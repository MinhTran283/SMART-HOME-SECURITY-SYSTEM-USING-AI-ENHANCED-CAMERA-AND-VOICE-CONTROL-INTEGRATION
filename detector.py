import cv2
from pathlib import Path


class PersonDetector:
    def __init__(self, confidence_threshold=0.6, model_path=None, proto_path=None):
        self.confidence_threshold = confidence_threshold

        self.CLASSES = [
            "background", "aeroplane", "bicycle", "bird", "boat",
            "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
            "dog", "horse", "motorbike", "person", "pottedplant",
            "sheep", "sofa", "train", "tvmonitor"
        ]

        model_path = Path(model_path)
        proto_path = Path(proto_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not proto_path.exists():
            raise FileNotFoundError(f"Model prototxt not found: {proto_path}")

        print("Loading model from:", str(model_path))
        print("Loading proto from:", str(proto_path))

        self.net = cv2.dnn.readNetFromCaffe(str(proto_path), str(model_path))
        print("Person detector loaded successfully.")

    def detect_person(self, frame):
        (h, w) = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            scalefactor=0.007843,
            size=(300, 300),
            mean=127.5
        )

        self.net.setInput(blob)
        detections = self.net.forward()

        best_conf = 0.0
        best_bbox = None

        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])

            if confidence < self.confidence_threshold:
                continue

            idx = int(detections[0, 0, i, 1])

            if idx < 0 or idx >= len(self.CLASSES):
                continue

            label = self.CLASSES[idx]
            if label != "person":
                continue

            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            startX, startY, endX, endY = box.astype("int")

            startX = max(0, startX)
            startY = max(0, startY)
            endX = min(w - 1, endX)
            endY = min(h - 1, endY)

            bbox = [
                int(startX),
                int(startY),
                int(endX - startX),
                int(endY - startY),
            ]

            if confidence > best_conf:
                best_conf = confidence
                best_bbox = bbox

        return {
            "detected": best_bbox is not None,
            "confidence": round(best_conf, 3),
            "bbox": best_bbox,
            "label": "person",
        }
