"""
Object Detector: detects coloured objects in camera frames using HSV Thresholding.

Returns detected objects with their colour, bounding box, and centroid pixel coordinates. Designed to work with any USB camera via OpenCV.
"""

import cv2
import numpy as np

# HSV colour ranges for detection.
# Red needs two ranges because a full 360 degree colour wheel is too big for OpenCV's 8-bit image capacity (only supports 255). So 
# they decided to divide it by 2 so it could fit, thus 0-179 inclusive. Red sits at the top of the colour wheel so it seeps into both ranges. 
# That's why red needs to be accounted for in both the lower and upper range! 
# These are starting defaults - will be tuned for specific lighting and objects using tuning script below
COLOR_RANGES = {
    'red' : [
        (np.array([0, 140, 76]), np.array([10,255,255])),    # lower range red
        (np.array([175, 111, 65]), np.array([179,255,255])) # upper range red        
    ],
    'green' : [
        (np.array([36, 80, 50]), np.array([86,255,255]))
    ],
    'blue' : [
        (np.array([109, 46, 52]), np.array([132,255,193]))
    ]
}

# Minimum contour area in pixels to count as a detection.
# Filters out noise and small reflections. Tuned based on how large objects appear in frame.
MIN_CONTOUR_AREA = 500

# Represents a single detected object in a frame
class DetectedObject:
    def __init__(self, colour, centroid, bbox, area):
        self.colour = colour        # string: 'red', 'green', 'blue
        self.centroid = centroid    # (px, py) pixel coordinates of center
        self.bbox = bbox            # (x, y, w, h) bounding box in pixels
        self.area = area            # contour area in pixels


class ObjectDetector:
    def __init__(self, color_ranges = None, min_area = MIN_CONTOUR_AREA):
        self.color_ranges = color_ranges or COLOR_RANGES
        self.min_area = min_area

    # raw frame (BGR) → HSV frame → raw masks (noisy) → clean masks → contours → real contours → DetectedObject instances
    def detect(self, frame):
        '''
        Detects coloured objects in a BGR camera frame.

        Returns list of DetectedObject instances, one per detected object. Returns empty list if nothing is detected.
        '''
        # HSV frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detected = []

        for colour_name, ranges in self.color_ranges.items():
            # raw masks (noisy)
            # Builds a combined mask for all ranges of this colour
            # Red needs two ranges explained near top of this file
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for (lower, upper) in ranges:
                mask |= cv2.inRange(hsv, lower, upper)

            # clean masks
            # Clean up mask: remove small noise, fill small holes
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # removes noise
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # fills holes

            # contours
            # RETR_EXTERNAL: only find outer boundaries, ignore holes inside blobs
            # CHAIN_APPROX_SIMPLE: compress the contour - only store corner points, not every pixel at a straight edge
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)     

            # real contours
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < self.min_area:
                    continue

                # Bounding box
                x, y, w, h = cv2.boundingRect(contour)

                # Centroid via image moments
                M = cv2.moments(contour)
                if M['m00'] == 0:
                    continue
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                # DetectedObject instances
                detected.append(DetectedObject(
                    colour=colour_name,
                    centroid=(cx, cy),
                    bbox=(x,y,w,h),
                    area=area
                ))

        return detected
    

    def draw(self, frame, detected_objects):
        """
        Draw bounding boxes, centroids, and labels on a frame.
        Returns an annotated copy of the frame (doesn't modify original)
        """
        # BGR colours for drawing (not same as HSV detection ranges)
        draw_colours = {
            'red':(0,0,255),
            'green':(0,255,0),
            'blue':(255,0,0)
        }
        annotated = frame.copy()

        for obj in detected_objects:
            colour = draw_colours.get(obj.colour, (255,255,255))
            x, y, w, h = obj.bbox
            cx, cy = obj.centroid

            # Bounding box
            cv2.rectangle(annotated, (x, y), (x+w, y+h), colour, 2)

            # Centroid dot
            cv2.circle(annotated, (cx, cy), 5, colour, -1)

            # Label: colour name + centroid coordinates
            label = f"{obj.colour} ({cx}, {cy})"
            cv2.putText(
                annotated, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2
            )
        return annotated