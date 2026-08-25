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

# --- Setup constants ---
TARGET_COLOUR = 'green'
DROP_XY = (120, 0)          # (x, y) mm in the arm's frame, where picked objects go
                            # (straight forward from base, well inside reach envelope)

# Half-width of the world-space exclusion zone around DROP_XY. Any detected
# object whose world coords fall within this square of DROP_XY is treated as
# "already in the container" and ignored, so the arm never re-picks its own
# successful drops. Bigger than the container's footprint gives margin for
# calibration drift and drop landing spread.
DROP_ZONE_EXCLUSION = 50    # mm

# --- Geometry constants tied to the calibrated setup (all in mm) ---
TABLE_Z = -30               # tabletop in model coords, base rotation axis is 30mm above table
CYLINDER_HEIGHT = 22
PICK_Z = TABLE_Z + CYLINDER_HEIGHT // 2   # mid-cylinder, solid grasp point
HOVER_Z = 30                # comfortably above any object on the table
LIFT_Z = 90                 # clear height after grasp, high enough that the whole
                            # arm (not just the grip point) stays well above any
                            # cylinder-height object during traverse

# --- Timing (seconds), tuned to let easing complete before sending the next command ---
# The shoulder eases at 30 deg/sec with EASE_QUARTIC_IN_OUT (chosen back in Week 2
# to suppress resonance in the acrylic frame), which dominates every move's total
# time. 1.5s is enough for even large angular swings to finish before we override.
SETTLE = 1.5
GRIPPER_TIME = 0.6


def apply_homography(H, px, py):
    """Map pixel (px, py) to world (wx, wy) in mm."""
    src = np.array([[[float(px), float(py)]]], dtype=np.float32)
    dst = cv2.perspectiveTransform(src, H)
    return float(dst[0, 0, 0]), float(dst[0, 0, 1])


def detect_targets(cap, detector):
    """Grab a fresh frame, return all objects of TARGET_COLOUR (may be empty)."""
    # Drain the driver's frame buffer, otherwise cap.read() returns a stale frame
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    if not ret:
        return []
    return [o for o in detector.detect(frame) if o.colour == TARGET_COLOUR]


def move_with_gripper(arm, xyz, gripper_angle):
    """Solve IK for xyz and command the arm to it, holding the given gripper angle."""
    x, y, z = xyz
    angles = solve_ik(x, y, z)
    print(f"  -> ({x:.0f}, {y:.0f}, {z}) mm  ->  "
          f"base={angles['base']}, shoulder={angles['shoulder']}, elbow={angles['elbow']}")
    arm.move_to(gripper=gripper_angle, **angles)
    time.sleep(SETTLE)


MAX_PICKS = 20              # safety cap: stop even if detector keeps seeing objects


def main():
    """
    This is where everything comes together.
    
    Load calibrated homography -> initiate video capture and object detection class -> initiate arm controller class ->
    while loop -> detects object outside of drop zone exclusion and finds its real world coords -> pick object closest to base first ->
    pick all objects -> bring arm back to home popse and release camera
    """
    with open('calibration.json') as f:
        H = np.array(json.load(f)['homography'], dtype=np.float32)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    detector = ObjectDetector()

    try:
        with ArmController() as arm:
            print("Homing...")
            arm.home()
            time.sleep(SETTLE)

            picks_done = 0
            while picks_done < MAX_PICKS:
                print(f"\n--- Cycle {picks_done + 1}: searching for {TARGET_COLOUR} objects ---")
                targets = detect_targets(cap, detector)
                if not targets:
                    print(f"No {TARGET_COLOUR} objects visible, stopping.")
                    break

                # Convert each target's pixel centroid to world coords, then filter
                # out anything inside the drop-zone exclusion square (that's a
                # cylinder already in the container, not a new pick target)
                targets_world = []
                for t in targets:
                    px, py = t.centroid
                    wx, wy = apply_homography(H, px, py)
                    if (abs(wx - DROP_XY[0]) < DROP_ZONE_EXCLUSION and
                            abs(wy - DROP_XY[1]) < DROP_ZONE_EXCLUSION):
                        continue
                    targets_world.append((wx, wy, t))

                if not targets_world:
                    print(f"Only {TARGET_COLOUR} objects in the drop zone remain, stopping.")
                    break

                # Pick the one closest to the base rotation axis (shortest reach =
                # highest accuracy, given the error-with-extension pattern from FK)
                targets_world.sort(key=lambda tw: tw[0] ** 2 + tw[1] ** 2)
                wx, wy, target = targets_world[0]

                print(f"{len(targets_world)} pickable object(s), picking closest at world "
                      f"({wx:.1f}, {wy:.1f}) mm")

                # Distance-proportional offset: servo error compounds along the chain
                # in extended poses, so real picks land short of the model's prediction.
                REACH_GAIN = 1.02
                pick_x = wx * REACH_GAIN
                pick_y = wy * REACH_GAIN
                print(f"Pick target (with reach compensation): ({pick_x:.1f}, {pick_y:.1f}) mm")

                print("Hover above pick point...")
                move_with_gripper(arm, (pick_x, pick_y, HOVER_Z), GRIPPER_OPEN)

                print("Descend to pick point...")
                move_with_gripper(arm, (pick_x, pick_y, PICK_Z), GRIPPER_OPEN)

                print("Close gripper...")
                arm.close_gripper()
                time.sleep(GRIPPER_TIME)

                print("Lift...")
                move_with_gripper(arm, (pick_x, pick_y, LIFT_Z), GRIPPER_CLOSED)

                print(f"Traverse to drop zone {DROP_XY}...")
                move_with_gripper(arm, (DROP_XY[0], DROP_XY[1], LIFT_Z), GRIPPER_CLOSED)

                print("Release...")
                arm.open_gripper()
                time.sleep(GRIPPER_TIME)

                picks_done += 1

            print(f"\nDone. {picks_done} object(s) picked.")
            arm.home()
            time.sleep(SETTLE)

    finally:
        cap.release()


if __name__ == "__main__":
    main()