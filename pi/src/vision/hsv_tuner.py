"""
Interactive HSV tuner. Shows the camera feed alongside the binary mask for a single colour. Use the trackbars
to find the right HSV range, then copy the values into COLOR_RANGES in object_detector.py

Usage:
python3 -c "
import sys; sys.path.insert(0, '.')
from vision.hsv_tuner import run_tuner
run_tuner()
"
"""

import cv2
import numpy as np

def run_tuner():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cv2.namedWindow("HSV Tuner")

    # Create trackbars for each HSV bound
    cv2.createTrackbar("H min", "HSV Tuner", 0, 179, lambda x: None)
    cv2.createTrackbar("H max", "HSV Tuner", 179, 179, lambda x: None)
    cv2.createTrackbar("S min", "HSV Tuner", 0, 255, lambda x: None)
    cv2.createTrackbar("S max", "HSV Tuner", 255, 255, lambda x: None)
    cv2.createTrackbar("V min", "HSV Tuner", 0, 255, lambda x: None)
    cv2.createTrackbar("V max", "HSV Tuner", 255, 255, lambda x: None)

    print("Adjust trackbars until the target colour shows white in the mask.")
    print("Press 'p' to print current values. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        h_min = cv2.getTrackbarPos("H min", "HSV Tuner")
        h_max = cv2.getTrackbarPos("H max", "HSV Tuner")
        s_min = cv2.getTrackbarPos("S min", "HSV Tuner")
        s_max = cv2.getTrackbarPos("S max", "HSV Tuner")
        v_min = cv2.getTrackbarPos("V min", "HSV Tuner")
        v_max = cv2.getTrackbarPos("V max", "HSV Tuner")

        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower, upper)

        # Show original and mask side by side
        mask_bgr =  cv2.cvtColor(mask, cv2.COLOR_COLOR_GRAY2BGR)
        combined = np.hstack([frame, mask_bgr])
        cv2.imshow("HSV Tuner", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            print(f"lower = np.array('[{h_min}, {s_min}, {v_min}])")
            print(f"upper = np.array('[{h_max}, {s_max}, {v_max}])")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_tuner()
