"""
Verifies arm_chain.py's forward kinematics against the real arm

Commands a few known poses and prints where the model thinks the gripper ended up. Will measure in real world with calipers.
Measured from the base's rotation axis, at the top of the base plate:
    z = straight up
    x = horizontal, in the direction the arm faces at base=90 (home), away from esp32 board
    y = horizontal, sideways from that
"""

import time
from comm.serial_comm import ArmController, GRIPPER_OPEN, GRIPPER_CLOSED
from kinematics.arm_chain import gripper_position
 
# Poses to verify: forward-reaching, spanning a useful vertical range.
TEST_POSES = [
    {'base': 90, 'shoulder': 30, 'elbow': 150},   # low, near table
    {'base': 90, 'shoulder': 45, 'elbow': 135},   # mid
    {'base': 90, 'shoulder': 60, 'elbow': 120},   # high
]
 
# Safe intermediate pose: arm reaching out but comfortably above the
# table, used as a waypoint between home and every target so the arm
# never interpolates through the table on the way down.
TRANSIT_POSE = {'base': 90, 'shoulder': 45, 'elbow': 90}
 
SETTLE = 1.5   # seconds between commanded poses
 
def main():
    with ArmController() as arm:
        arm.home()
        time.sleep(SETTLE)
 
        for pose in TEST_POSES:
            input(f"\nPlace the cylinder where the closed jaws will land for "
                  f"pose {pose}, then press Enter to move...")
 
            # Transit above the table with jaws open, then descend to target,
            # then close on the cylinder. Never close during motion.
            arm.move_to(gripper=GRIPPER_OPEN, **TRANSIT_POSE)
            time.sleep(SETTLE)
            arm.move_to(gripper=GRIPPER_OPEN, **pose)
            time.sleep(SETTLE)
            arm.close_gripper()
            time.sleep(0.6)
 
            x, y, z = gripper_position(**pose)
            print(f"  Model predicts grip point at: x={x:.1f}mm  y={y:.1f}mm  z={z:.1f}mm")
            print(f"  (or {z + 30:.1f}mm above the tabletop)")
            input("  Measure where the cylinder actually is, then press Enter to continue...")
 
            # Release and lift back to transit before the next pose.
            arm.open_gripper()
            time.sleep(0.6)
            arm.move_to(gripper=GRIPPER_OPEN, **TRANSIT_POSE)
            time.sleep(SETTLE)
 
        print("\nDone. Returning home.")
        arm.home()
 
if __name__ == "__main__":
    main()