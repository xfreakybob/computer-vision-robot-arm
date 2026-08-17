import cv2
import numpy as np
import json
from vision.object_detector import ObjectDetector

OBJECT_COLOUR = 'green'

def apply_homography(H, px, py):
    """Map a pixel (px, py) through H to a world (wx, wy) in mm."""
    src = np.array([[[float(px), float(py)]]], dtype=np.float32)
    dst = cv2.perspectiveTransform(src, H)
    return float(dst[0, 0, 0]), float(dst[0, 0, 1])

def main():
    with open('calibration.json') as f:
        H = np.array(json.load(f)['homography'], dtype=np.float32)

    wx = float(input("True world X of the fresh test point (mm): "))
    wy = float(input("True world Y (mm): "))

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    detector = ObjectDetector()
    input(f"Object at ({wx}, {wy}) mm, then press Enter...")
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Camera read failed.")
        return

    detected = [o for o in detector.detect(frame) if o.colour == OBJECT_COLOUR]
    if not detected:
        print("No object detected. Check lighting/position.")
        return

    obj = max(detected, key=lambda o: o.area)
    px, py = obj.centroid
    pred_x, pred_y = apply_homography(H, px, py)
    err = ((pred_x - wx) ** 2 + (pred_y - wy) ** 2) ** 0.5

    print(f"\nDetected pixel: ({px}, {py})")
    print(f"Predicted world: ({pred_x:.1f}, {pred_y:.1f}) mm")
    print(f"True world:      ({wx:.1f}, {wy:.1f}) mm")
    print(f"Error: {err:.1f} mm")

if __name__ == "__main__":
    main()