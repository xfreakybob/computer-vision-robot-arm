"""
Measuring physical distance between grippers when commanded to GRIPPER_OPEN and GRIPPER_CLOSED positions 

"""

from comm.serial_comm import ArmController

with ArmController() as arm:
    arm.home()
    arm.open_gripper()
    input("Measure jaw gap now, press Enter to continue...")
    arm.close_gripper()
    input("Measure jaw gap now, press Enter to continue...")