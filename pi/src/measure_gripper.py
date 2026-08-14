from comm.serial_comm import ArmController

with ArmController() as arm:
    arm.home()
    arm.open_gripper()
    input("Measure jaw gap now, press Enter to continue...")
    arm.close_gripper()
    input("Measure jaw gap now, press Enter to continue...")