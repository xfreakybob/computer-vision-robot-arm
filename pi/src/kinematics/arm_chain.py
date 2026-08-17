'''
Kinematic chain for 3 of the arm's positioning joints (base, shoulder, elbow).
The gripper servo only controls open/close so it will be ignored in this chain

Link lengths are straight from kit's diagram:
    BASE_TO_SHOULDER = 46.5 mm (base plate to shoulder pivot)
    SHOULDER_TO_ELBOW = 58 mm (upper arm)
    ELBOW_TO_GRIPPER = 75 mm (forearm, elbow pivot to gripper grasp point)

z=0 in the model sits at the base rotation axis and tabletop is z=-30mm (height from table to base)
    
Assumption in this model: all joints at default 90 degrees (vertical line up with gripper horizontal)

Angle convention: ikpy works in radians measured from zero at the reference (in this case, HOME_POSE), so
every servo angle gets converted as radians(servo_deg - 90) before use

Coordinate frame: origin at base's rotation axis, at the top of the base plate. +Z is up. +X is horizontal reach direction when base = 90 (away from esp32).
+Y is sideways from that. Units are mm.

'''

import numpy as np
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
 
BASE_TO_SHOULDER = 46.5
SHOULDER_TO_ELBOW = 58
ELBOW_TO_GRIPPER = 115
 
 
def _bounds(servo_lo, servo_hi):
    """Convert a safe servo range (degrees) to the chain's zero-at-90 radians."""
    return (np.radians(servo_lo - 90), np.radians(servo_hi - 90))
 
 
arm_chain = Chain(name='arm', active_links_mask=[False, True, True, True, False], links=[
    OriginLink(),
    URDFLink(
        name="base",
        origin_translation=[0, 0, 0],
        origin_orientation=[0, 0, 0],
        rotation=[0, 0, 1],            # yaw, about Z
        bounds=_bounds(5, 185),        # matches JOINT_LIMITS['base']
    ),
    URDFLink(
        name="shoulder",
        origin_translation=[0, 0, BASE_TO_SHOULDER],
        origin_orientation=[0, 0, 0],
        rotation=[0, -1, 0],           # pitch, about Y (flipped: away-from-board = +X)
        bounds=_bounds(5, 155),        # matches JOINT_LIMITS['shoulder']
    ),
    URDFLink(
        name="elbow",
        origin_translation=[0, 0, SHOULDER_TO_ELBOW],
        origin_orientation=[0, 0, 0],
        rotation=[0, 1, 0],            # pitch, inverted sense vs. shoulder (confirmed on real arm)
        bounds=_bounds(5, 185),        # matches JOINT_LIMITS['elbow']
    ),
    URDFLink(
        name="gripper_point",
        origin_translation=[0, 0, ELBOW_TO_GRIPPER],
        origin_orientation=[0, 0, 0],
        joint_type='fixed',            # not an actuated joint, just an offset
    ),
])
 
 
def servo_to_chain_angles(base, shoulder, elbow):
    """Convert move_to()-style servo degrees to the chain's radian convention."""
    return [
        0,                          # OriginLink placeholder
        np.radians(base - 90),
        np.radians(shoulder - 90),
        np.radians(elbow - 90),
        0,                          # fixed gripper_point link
    ]
 
 
def chain_to_servo_angles(chain_angles):
    """Convert solved chain radians back to servo degrees for move_to()."""
    base_rad, shoulder_rad, elbow_rad = chain_angles[1], chain_angles[2], chain_angles[3]
    return {
        'base': round(np.degrees(base_rad) + 90),
        'shoulder': round(np.degrees(shoulder_rad) + 90),
        'elbow': round(np.degrees(elbow_rad) + 90),
    }
 
 
def gripper_position(base, shoulder, elbow):
    """Returns the (x, y, z) mm position of the gripper's grasp point for given servo angles."""
    angles = servo_to_chain_angles(base, shoulder, elbow)
    matrix = arm_chain.forward_kinematics(angles)
    return matrix[:3, 3]
 
 
def solve_ik(x, y, z, initial_servo_pose=(90, 90, 90)):
    """
    Solve for the (base, shoulder, elbow) servo angles that place the
    gripper at the given (x, y, z) mm position. Position only, no
    orientation control (this arm's gripper has none).
    """
    initial = servo_to_chain_angles(*initial_servo_pose)
    result = arm_chain.inverse_kinematics(
        target_position=[x, y, z],
        initial_position=initial,
    )
    return chain_to_servo_angles(result)