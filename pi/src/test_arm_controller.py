'''
Smoke test for ArmController.
'''

from comm.serial_comm import ArmController, OutOfRangeError, FirmwareError
import time

def main():
    with ArmController() as arm:
        print("Connected to arm")

        print("Moving to home pose...")
        arm.home()
        time.sleep(2)

        print("Moving to compact pose...")
        arm.move_to(base=90, shoulder=45, elbow=135, gripper=90)
        time.sleep(3)

        print("Returning home...")
        arm.home()
        time.sleep(2)

        print("Testing out-of-range (Python-side)...")
        try:
            arm.move_to(base=200, shoulder=90, elbow=90, gripper=90)
        except OutOfRangeError as e:
            print(f"Caught expected error: {e}")
        print("All tests passed.")

if __name__ == "__main__":
    main()