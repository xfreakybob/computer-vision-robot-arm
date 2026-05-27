"""
Live test for Object Detector.

Opens the camera, runs detection on every frame, and displays the annotated feed in a window. Press 'q' to quit,
's' to print detected object details to the console. 
"""

import cv2
from vision.object_detector import ObjectDetector

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return
    
    detector = ObjectDetector()
    print("Camera open. Press 'q' to quit, 's' to print detections to console.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: failed to read frame")
            break

        detected = detector.detect(frame)
        annotated = detector.draw(frame, detected)

        cv2.imshow("Object Detector", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            if detected:
                for obj in detected:
                    print(
                        f"  {obj.colour}: centroid={obj.centroid}, "
                        f"bbox={obj.bbox}, area={obj.area:.0f}px"
                    )
            else:
                print("  No objects detected.")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
