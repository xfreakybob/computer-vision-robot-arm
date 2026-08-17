"""
Camera-to-arm calibration: builds a homography mapping camera pixel
coordinates to real-world (x, y) in the arm's frame (mm), using the
printed pick object as a physical fiducial.

Workflow: place the object at a handful of known (x, y) points on the
table (measured by tape measure from the base's rotation axis, same
convention/method used for the FK verification), and let the object
detector find its pixel centroid automatically at each point.

Before running:
  - Set OBJECT_COLOUR to whatever colour you printed
  - Adjust CALIBRATION_POINTS to real points within the arm's confirmed
    reach, spread across at least 2 rows/columns (not all in one line,
    a homography needs spread in both directions to solve well)

Run from pi/src/, needs a display for the confirmation window.
"""

import cv2
import numpy as np
import json
from vision.object_detector import ObjectDetector

OBJECT_COLOUR = 'green'   # TODO: set to colour printed

# (world_x_mm, world_y_mm), measured from the base's rotation axis.
# Placeholder values, replace with points that are actually reachable
# and visible to the camera on your setup.
CALIBRATION_POINTS = [
    (100, -100),
    (100, 0),
    (100, 100),
    (200, -100),
    (200, 0),
    (200, 100),
]

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    detector = ObjectDetector()
    pixel_points = []
    world_points = []

    for wx, wy in CALIBRATION_POINTS:
        input(f"\nPlace the object at world ({wx}, {wy}) mm, then press Enter...")
        ret, frame = cap.read()
        if not ret:
            print("  Camera read failed, skipping this point.")
            continue

        detected = [o for o in detector.detect(frame) if o.colour == OBJECT_COLOUR]
        if not detected:
            print("  No object detected here, skipping. Check lighting/position.")
            continue

        obj = max(detected, key=lambda o: o.area)  # largest match, in case of noise
        px, py = obj.centroid
        print(f"  Detected pixel centroid: ({px}, {py})")
        pixel_points.append([px, py])
        world_points.append([wx, wy])

    cap.release()

    if len(pixel_points) < 4:
        print(f"\nNeed at least 4 successful points for a homography, got {len(pixel_points)}.")
        return

    pixel_points = np.array(pixel_points, dtype=np.float32)
    world_points = np.array(world_points, dtype=np.float32)

    H, status = cv2.findHomography(pixel_points, world_points)
    print("\nHomography matrix:")
    print(H)

    with open('calibration.json', 'w') as f:
        json.dump({'homography': H.tolist()}, f, indent=2)
    print("\nSaved to calibration.json")

if __name__ == "__main__":
    main()