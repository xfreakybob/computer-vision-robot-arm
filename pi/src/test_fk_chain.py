"""
Verifies arm_chain.py's forward kinematics against the real arm

Commands a few known poses and prints where the model thinks the gripper ended up. Will measure in real world with calipers.
Measured from the base's rotation axis, at the top of the base plate:
    z = straight up
    x = horizontal, in the direction the arm faces at base=90 (home)
    y = horizontal, sideways from that
"""

from comm.serial_comm import ArmController, GRIPPER_CLOSED
from kinematics.arm_chain import gripper_position
 
# Poses chosen to reach forward toward the table so a real cylinder can
# actually sit under the jaws for the measurement.
TEST_POSES = [
    {'base': 90, 'shoulder': 30, 'elbow': 150},
    {'base': 90, 'shoulder': 45, 'elbow': 135},
    {'base': 90, 'shoulder': 60, 'elbow': 120},
]
 
def main():
    with ArmController() as arm:
        arm.home()
        for pose in TEST_POSES:
            input(f"\nPlace the cylinder where the jaws will close on it "
                  f"for pose {pose}, then press Enter to command...")
            arm.move_to(gripper=GRIPPER_CLOSED, **pose)
            x, y, z = gripper_position(**pose)
            print(f"  Model predicts grip point at: x={x:.1f}mm  y={y:.1f}mm  z={z:.1f}mm")
            print(f"  (or {z + 30:.1f}mm above the tabletop)")
            input("  Measure where the cylinder actually is, then press Enter to continue...")
 
        print("\nDone. Returning home.")
        arm.home()
 
if __name__ == "__main__":
    main()