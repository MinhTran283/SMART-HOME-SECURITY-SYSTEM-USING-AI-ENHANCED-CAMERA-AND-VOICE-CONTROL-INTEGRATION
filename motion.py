import cv2


class MotionDetector:
    def __init__(self, threshold=25, min_area=1500, blur_size=(21, 21)):
        self.threshold = threshold
        self.min_area = min_area
        if blur_size[0] % 2 == 0 or blur_size[1] % 2 == 0:
            raise ValueError("Gaussian blur dimensions must be odd numbers")
        self.blur_size = blur_size
        self.previous_frame = None

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, self.blur_size, 0)

        motion_detected = False
        boxes = []

        if self.previous_frame is None:
            self.previous_frame = gray
            return motion_detected, boxes

        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            boxes.append((x, y, w, h))
            motion_detected = True

        self.previous_frame = gray
        return motion_detected, boxes
