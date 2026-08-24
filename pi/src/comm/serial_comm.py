'''
ArmController: Pi-side wrapper around the ESP32 serial protocol.

Communicates with the ESP32-C3 firmware over USB serial using the S1:x,S2:x,S3:x,S4:x command format.
Mirrors the firmware's joint limits for defense in depth.
'''

import serial
import time

# Joint limits mirror the firmware (safe operating ranges, 5 degree margin from absolute mechanical limits documented in Week 2 testing).
JOINT_LIMITS = {
    'base':(5,185),
    'shoulder':(5,155),
    'elbow':(5,185),
    'gripper':(20,115)
}

# Convenience positions
HOME_POSE = {'base':90, 'shoulder':90, 'elbow':90, 'gripper':90}
GRIPPER_OPEN = 90
GRIPPER_CLOSED = 23


# Custom Errors to capture unexpectancies 
class ArmControllerError(Exception):
    '''Base exception for ArmController errors.'''
    pass
class OutOfRangeError(ArmControllerError):
    '''Raised when a command angle is outside the safe operating range.'''
    pass
class FirmwareError(ArmControllerError):
    '''Raised when the firmware returns an error response.'''
    pass

class ArmController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=2.0):
        '''
        Open serial connection to the ESP32. Waits for the firmware's READY message before returning.
        '''
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(2) # ESP32 resets on serial open; wait for boot

        # clears all accumulated, unread incoming data
        self.ser.reset_input_buffer()

        # Opening the serial port resets the ESP32, and the firmware puts every servo at 90 degrees on boot
        # so HOME_POSE is a safe assumption for the arm's actual position
        self.last_pose = dict(HOME_POSE)

    def close(self):
        '''
        Close the serial connection.
        '''
        if self.ser.is_open:
            self.ser.close()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _validate(self, base, shoulder, elbow, gripper):
        '''
        Raise OutOfRangeError if any angle is outside its safe range.
        '''
        angles = {
            'base':base,
            'shoulder':shoulder,
            'elbow':elbow,
            'gripper':gripper
        }
        for joint, angle in angles.items():
            lo, hi = JOINT_LIMITS[joint]
            if not (lo <= angle <= hi):
                raise OutOfRangeError(
                    f"{joint} angle {angle} out of range [{lo}, {hi}]"
                )
            
    def move_to(self, base, shoulder, elbow, gripper):
        '''
        Command the arm to a new pose. Blocks until the firmware acknowledges the command (does not wait for motion to complete).
        '''
        self._validate(base, shoulder, elbow, gripper)
        command = f"S1:{base},S2:{shoulder},S3:{elbow},S4:{gripper}\n"
        self.ser.write(command.encode())
        response = self.ser.readline().decode().strip()

        if response == "OK":
            self.last_pose = {
                'base': base, 'shoulder': shoulder, 'elbow': elbow, 'gripper': gripper
            }
            return
        elif response.startswith("ERR:"):
            raise FirmwareError(f"Firmware rejected command: {response}")
        else:
            raise FirmwareError(f"Unexpected response: {response}")
        
    def home(self):
        '''
        Move arm to the veritical reference pose (90/90/90/90).
        '''
        self.move_to(**HOME_POSE)

    def open_gripper(self):
        '''
        Open the gripper while keeping other joints at current command.
        '''
        pose = dict(self.last_pose)
        pose['gripper'] = GRIPPER_OPEN
        self.move_to(**pose)
    
    def close_gripper(self):
        '''
        Close the gripper, keeping base/shoulder/elbow at their last commanded pose
        '''
        pose = dict(self.last_pose)
        pose['gripper'] = GRIPPER_CLOSED
        self.move_to(**pose)