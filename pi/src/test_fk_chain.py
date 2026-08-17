"""
Verifies arm_chain.py's forward kinematics against the real arm

Commands a few known poses and prints where the model thinks the gripper ended up. Will measure in real world with calipers.
Measured from the base's rotation axis, at the top of the base plate:
    z = straight up
    x = horizontal, in the direction the arm faces at base=90 (home)
    y = horizontal, sideways from that
"""

from comm.serial_comm import ArmController, HOME_POSE
from kinematics.arm_chain import gripper_position

TEST_POSES = [
    {'base':90, 'shoulder':90, 'elbow':90},  # home, should be x=0, y=0, z=209.5
    {'base':90, 'shoulder':60, 'elbow':90},
    {'base':90, 'shoulder':90, 'elbow':60},

    {'base':60, 'shoulder':60, 'elbow':60},
    {'base':110, 'shoulder':70, 'elbow':60}
]

def main():
    with ArmController() as arm:
        for pose in TEST_POSES:
            arm.move_to(gripper=HOME_POSE['gripper'], **pose)
            x, y, z = gripper_position(**pose)
            print(f"\nPose: {pose}")
            print(f"Model predicts: x={x:.1f}mm, y={y:.1f}mm, z={z:.1f}mm")
            input("Measure real arm and press Enter for next pose...")
        print("\nDone. Returning home")
        arm.home()

if __name__ == "__main__":
    main()