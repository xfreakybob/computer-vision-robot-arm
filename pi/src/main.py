"""
End-to-end pick-and-place: detect object, compute its world position via
the saved homography, solve IK for the pick pose, and run the arm through
hover -> descend -> close -> lift -> move to drop -> open -> home.

Run from pi/src/ with the arm and camera in the same physical setup used
for calibration. Requires calibration.json (from calibrate_camera.py).

Expected total run: ~15-20 seconds for one full cycle. Sleep durations
below are pauses to let the arm mechanically settle at each pose,
move_to() returns as soon as the firmware acknowledges the command, it
does NOT wait for the motion itself to complete.
"""

import cv2
import numpy as np
import json
import time

from comm.serial_comm import ArmController, HOME_POSE, GRIPPER_OPEN, GRIPPER_CLOSED
from vision.object_detector import ObjectDetector
from kinematics.arm_chain import solve_ik

# --- Setup constants, change these if your physical setup shifts ---
TARGET_COLOUR = 'green'
DROP_XY = (80, -80)         # (x, y) mm in the arm's frame, where picked objects go
                            # (chosen inside the reach envelope, IK solves cleanly here)

# --- Geometry constants tied to the calibrated setup ---
TABLE_Z = -30               # tabletop in model coords, base rotation axis is 30mm above table
CYLINDER_HEIGHT = 22
PICK_Z = TABLE_Z + CYLINDER_HEIGHT // 2   # mid-cylinder, solid grasp point
HOVER_Z = 30                # comfortably above any object on the table
LIFT_Z = 90                 # clear height after grasp, high enough that the whole
                            # arm (not just the grip point) stays well above any
                            # cylinder-height object during traverse

# --- Timing (seconds), tuned to let easing complete before sending the next command ---
SETTLE_LONG = 1.5           # after a big move (traverse across the workspace)
SETTLE_SHORT = 0.8          # after a short move (descend, lift)
GRIPPER_TIME = 0.6          # gripper close/open


def apply_homography(H, px, py):
    """Map pixel (px, py) to world (wx, wy) in mm."""
    src = np.array([[[float(px), float(py)]]], dtype=np.float32)
    dst = cv2.perspectiveTransform(src, H)
    return float(dst[0, 0, 0]), float(dst[0, 0, 1])


def detect_target(cap, detector):
    """Grab a fresh frame, return the largest object of TARGET_COLOUR, or None."""
    # Drain the driver's frame buffer, otherwise cap.read() returns a stale frame
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    if not ret:
        return None
    matches = [o for o in detector.detect(frame) if o.colour == TARGET_COLOUR]
    return max(matches, key=lambda o: o.area) if matches else None


def move_with_gripper(arm, xyz, gripper_angle, settle=SETTLE_LONG):
    """Solve IK for xyz and command the arm to it, holding the given gripper angle."""
    x, y, z = xyz
    angles = solve_ik(x, y, z)
    print(f"  -> ({x:.0f}, {y:.0f}, {z}) mm  ->  "
          f"base={angles['base']}, shoulder={angles['shoulder']}, elbow={angles['elbow']}")
    arm.move_to(gripper=gripper_angle, **angles)
    time.sleep(settle)


def main():
    with open('calibration.json') as f:
        H = np.array(json.load(f)['homography'], dtype=np.float32)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    detector = ObjectDetector()

    try:
        with ArmController() as arm:
            print("Homing...")
            arm.home()
            time.sleep(SETTLE_LONG)

            print(f"\nSearching for {TARGET_COLOUR} object...")
            target = detect_target(cap, detector)
            if not target:
                print(f"No {TARGET_COLOUR} object detected. Aborting.")
                return

            px, py = target.centroid
            wx, wy = apply_homography(H, px, py)
            print(f"Detected at pixel ({px}, {py}) -> world ({wx:.1f}, {wy:.1f}) mm")

            # Distance-proportional offset: servo error compounds along the chain
            # in extended poses, so real picks land short of the model's prediction.
            # Empirically, ~4% correction scales with reach without over-correcting
            # close targets (where accuracy was already good).
            REACH_GAIN = 1.04
            pick_x = wx * REACH_GAIN
            pick_y = wy * REACH_GAIN
            print(f"Pick target (with reach compensation): ({pick_x:.1f}, {pick_y:.1f}) mm")

            print("\nHover above pick point...")
            move_with_gripper(arm, (pick_x, pick_y, HOVER_Z), GRIPPER_OPEN)

            print("Descend to pick point...")
            move_with_gripper(arm, (pick_x, pick_y, PICK_Z), GRIPPER_OPEN, settle=SETTLE_SHORT)

            print("Close gripper...")
            arm.close_gripper()
            time.sleep(GRIPPER_TIME)

            print("Lift...")
            move_with_gripper(arm, (pick_x, pick_y, LIFT_Z), GRIPPER_CLOSED, settle=SETTLE_SHORT)

            print(f"Traverse to drop zone {DROP_XY}...")
            move_with_gripper(arm, (DROP_XY[0], DROP_XY[1], LIFT_Z), GRIPPER_CLOSED)

            print("Release...")
            arm.open_gripper()
            time.sleep(GRIPPER_TIME)

            print("Homing.")
            arm.home()
            time.sleep(SETTLE_LONG)

    finally:
        cap.release()


if __name__ == "__main__":
    main()