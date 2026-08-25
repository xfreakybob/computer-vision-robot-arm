# Overview
The Raspberry Pi 5 4GB is the brains of the operation. It handles everything the ESP32 doesn't: capturing camera frames, detecting coloured objects, converting pixel coordinates to real-world positions, solving the joint angles needed to reach them, and orchestrating the full pick-and-place sequence. Thes ESP32 only ever receives the finished joint-angle commands over serial and moves the servos, everthing upstream of that happens here.

The Pi can run headless (no monitor) through SSH (secure shell) and receives updates through Git via git pull origin main. Everything is developed on personal laptop then pushed to Github repo.

Table of Contents
- [Software Stack](#software-stack)
- [Architecture](#architecture)
- [Setup](#setup)
- [Running the Pipeline](#running-the-pipeline)
- [OpenCV & NumPy](#opencv--numpy)
- [Kinematics](#kinematics)
- [Other important info](#other-important-information)


## Software Stack
| Layer | Library | Role |
|-------|---------|------|
| Vision | OpenCV + NumPy | Detect coloured objects, find their pixel centroids |
| Calibration | OpenCV (homography) | Map camera pixels to real-world table coordinates |
| Kinematics | ikpy | Solve joint angles for a target 3D position |
| Comms | pyserial | Send joint-angle commands to the ESP32 |
 
Exact versions are pinned in [`requirements.txt`](requirements.txt).

## Architecture
The Pi code follows a layered design: each module depends only on the below it, and `main.py` sits on top as the orchestrator. This is what makes the system easy to reason about and to swap parts out (for eg, refactoring serial comms to Wifi/MQTT touches only one file).
```
                        main.py
              (end-to-end pick-and-place loop)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
     vision/          kinematics/           comm/
  object_detector    arm_chain.py       serial_comm.py
  (detect objects)  (solve IK / FK)   (talk to ESP32)
        │                                     │
     camera                              ESP32-C3
```
- **`comm/serial_comm.py`** — `ArmController`, the *only* file that touches the serial port. Wraps the ESP32 protocol behind a clean `move_to(base, shoulder, elbow, gripper)` API, mirrors the firmware's joint limits (defence in depth), and raises typed exceptions on failure.
- **`vision/object_detector.py`** — `ObjectDetector` / `DetectedObject`. HSV-based colour detection returning each object's colour, bounding box, and centroid.
- **`vision/hsv_tuner.py`** — interactive tool to find HSV ranges for your lighting before committing them to the detector.
- **`kinematics/arm_chain.py`** — the ikpy chain, forward kinematics, and the IK solver with reachability checking.
- **`calibrate_camera.py`** / **`validate_calibration.py`** — build and sanity-check the pixel→world homography.
- **`test_*.py`** — per-module smoke/live tests, runnable in isolation.

## Setup
 
### Prerequisites
- Raspberry Pi 5 (4GB) running Raspberry Pi OS
- A USB webcam (project uses a Microsoft LifeCam HD-3000)
- Python 3.11+ (ships with current Raspberry Pi OS)
### Install
```
bash
cd pi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
 
### Wiring
The Pi connects to the ESP32-C3 over USB (Pi USB-A → ESP32 USB-C). The ESP32 enumerates as `/dev/ttyUSB0`, which is the default port in `ArmController`. See the [ESP32 README](../esp32/README.md) for the firmware side.
 
> **Note:** the ESP32 needs its 18650 battery physically inserted before it will enumerate over USB. If `/dev/ttyUSB0` doesn't appear, check the battery first.

## Running the Pipeline
 
The full pick-and-place demo assumes the arm and camera are physically fixed in the same relative pose used for calibration, and that `calibration.json` exists.
 
```
bash
cd pi/src
 
# 1. Tune HSV ranges for your lighting (optional but recommended)
python3 -c "import sys; sys.path.insert(0,'.'); from vision.hsv_tuner import run_tuner; run_tuner()"
 
# 2. Calibrate camera → arm (produces calibration.json)
python3 calibrate_camera.py
python3 validate_calibration.py     # check the error is acceptable
 
# 3. Run the full loop
python3 main.py
```
 
The pick sequence for each object is: **hover → descend → close gripper → lift → traverse to drop zone → release → home.**

## OpenCV & NumPy
Open Source Computer Vision Library (**OpenCV**), is an open-source software library designed specifically for real-time computer vision, image processing, and machine learning.\
Numerical Python (**NumPy**), is the foundational open-source library for scientific and numerical computing in Python.

When OpenCV reads a frame from the camera, it gives you a NumPy array — a grid of numbers.
For a 640x480 colour image, that array has shape (480, 640, 3):
- 480 rows (height)
- 640 columns (width)
- 3 values per pixel (colour channels)

Each pixel is represented by three numbers. By default, OpenCV uses **BGR oder** (Blue, Green, Red). All values range from 0-255.

<details>
<summary>HSV vs. BGR</summary>

## Why HSV and not BGR?

BGR can vary greatly under lighting changes. Under bright light, a red block may have BGR values [30, 20, 200]. Under dim light, the same block might look like [15, 10, 100]. If you try to write "detec red = R channel between 150 and 255", your detection breaks in lighting variance — or you risk losing colour detection accuracy if your range is too large.
The reason: in BGR/RGB, brightness and colour are mixed together in all three channels simultaneously.

With HSV, mostly V changes (brightness) when lighting changes and slightly S (Saturation). H stays roughly the same. So a red block under bright vs. dim light has nearly the same H value, just different V. This lets you write a detector saying "find pixels where H is between 0 and 10 regardless of V" and it will work across lighting conditions. 
| HSV | Description |
|-|-------------|
| Hue | The *pure* colour — what we normally call 'red', 'green', 'blue', etc. Represented as an angle on colour wheel. In OpenCV hue goes from 0-179. |
| Saturation | The intensity or *vividness* of a colour. High saturation = vivid, pure colour. Low saturation = washed out, closer to grey. Range 0-255 in OpenCV. |
| Value | How *bright* the colour is. High value = bright. Low value = dark. Range 0-255 in OpenCV. |


![HSV is represented here in cylindrical coordinates](threshold_inrange_hsv_colorspace.jpg)\
**Figure 1: Cylindrical representation of HSV**

Converting BGR to HSV in python only takes one line!\
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
</details>

<details>
<summary>Frame Pipeline</summary>

## Frame Pipeline — How does each frame get processed?

**Raw frame (BGR)**

↓ cv2.cvtColor(image, color conversion) — converts BGR to HSV

**HSV frame**

↓ cv2.inRange(src, lower bound, upper bound) — performs thresholding to see if colour is in range (returns binary image in black and white)

**Raw masks (noisy)**

↓ morphologyEx OPEN → erode then dillate (removes small isolated noise pixels)\
↓ morphologyEx CLOSE → dillate then erode (fills small holes inside deteced regions)

**Clean masks** 

↓ cv2.findContours → list of contour boundaries (boundaries of objects in a binary image)

**Contours**

↓ filter by cv2.contourArea < MIN_CONTOUR_AREA (min contour area is arbitrary and should be tested)

**Real contours** 

↓ cv2.boundingRect → (x, y, w, h)\
↓ cv2.moments → (cx, cy) (centroid, expand later)

**DetectedObject instances**

↓ draw() → annotated frame

**Display**

</details>

## Kinematics - IKPy
Kinematics in robotics is the study of motion for a robot's links and joints without looking at the forces or torques causing the movement.

Forward kinematics: *where* the robot's hand will be based on the joint angles\
Inverse kinematics: *what* joint angles are needed to put that hand in a specific spot

<details>
<summary>About the ikpy library</summary>

IKPy (Inverse Kinematics Python) is a pure-Python library designed to calculate the forward and inverse kinematics of robotic chains.

There are **2 main classes** used for functionality:

|   Class   |    Description    | Parameters |
|----------|--------------|----------|
| **Chain**     | core class used to represent a robot's kinematic structure. Acts as mathematical engine. |- links[] (required)= list of `Link` objects defining the physical layout and segments of the robot from base to tip<br> - active_links_mask (optional) = list of booleans matching length of `links[]` list. True means joint can move, False locks the joint at specific angle <br> - name (optional) = string label to identify kinematic chain |
| **Link** | represents a single component in a robot's kinematic chain. A robot is essentially a list of `Link` objects passed into a `Chain` |- name (required) = A label for the link <br> - length (required) = physical length of the segment along its primary axis <br> - bounds (optional) = a min/max tuple in rads defining how far this joint can move |
| URDFLink | subclass of Link, stands for Unified Robot Description Format. Used if you want to manually build a robot using URDF-style parameters instead of raw lengths |- name (required) = label name matching your URDF config. mapping <br> - origin_translation (required) = 3D translation vector (xyz attribute of the joint origin) <br> - origin_orientation (required) = 3D orientation vector (roll pitch yaw attribute of the joint origin) <br> - rotation (optional) = joint rotation axis vector (xys of the joint axis) <br> - bounds (optional) = min and max limits for joint movements |

</details>

## Other important information

<details>
<summary>How this arm is modelled</summary>

The arm is modelled as four links: base (yaw), shoulder (pitch), elbow (pitch), and a fixed offset out to the gripper's grasp point. The gripper's open/close servo isn't a positioning joint, so it's left out of the chain entirely.
 
A few hard-won details baked into the model:
- **Coordinate frame:** origin at the base's rotation axis on top of the base plate, +Z up, +X the direction the arm faces at base = 90°. The tabletop sits at z = −30 mm (the base axis is 30 mm above the table).
- **Angle convention:** ikpy works in radians measured from a zero reference, so every servo angle is converted as `radians(servo_deg − 90)` before use, and back again for `move_to()`.
- **Elbow sign is inverted** relative to the shoulder on the real hardware — confirmed by testing, not assumed.
- **Link lengths are from the kit diagram.** The forearm length in particular (`ELBOW_TO_GRIPPER`) is measured to the actual grip contact point, not the pivot screw.

</details>
<details>
<summary>Homography</summary>

The detector gives you an object's location in *pixels*. The arm needs it in *millimetres from the base*. A **homography** is the translator between those two: a 3×3 matrix that maps any point on one flat plane to a point on another flat plane.
 
It works because both planes are flat and the camera is fixed:
- the camera's image sensor is one plane,
- the tabletop the objects sit on is the other.
To build it (`calibrate_camera.py`), you place the object at a handful of known (x, y) points measured with a ruler from the base axis, let the detector find each pixel centroid, and hand both sets to `cv2.findHomography`. The points need spread in *both* directions (not all in a line) for the solve to be well-conditioned. The result is saved to `calibration.json`; `validate_calibration.py` then checks the error against a fresh test point.

</details>
<details>
<summary>Testing</summary>

Each module has a standalone test you can run from `pi/src/` without the full pipeline:
 
| Script | What it exercises |
|--------|-------------------|
| `test_arm_controller.py` | Serial comms, home/compact poses, out-of-range rejection, cleanup |
| `test_object_detector.py` | Live annotated camera feed (`q` to quit, `s` to print detections) |
| `test_fk_chain.py` | Commands known poses and prints where the model predicts the gripper landed, to check against calipers |
| `measure_gripper.py` | Reports the jaw gap at open/closed, for sizing pick objects |
 
Testing bottom-up (comms first, then vision, then kinematics, then integration) is the fastest way to localise a fault when "nothing happens" — a lesson the journal has more than one story about.

</details>

[Back to top](#overview)