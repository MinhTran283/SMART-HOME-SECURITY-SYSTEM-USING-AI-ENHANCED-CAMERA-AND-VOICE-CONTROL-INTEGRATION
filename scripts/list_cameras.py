import argparse
from pathlib import Path

import cv2


def probe_camera(index: int, output_dir: Path | None = None) -> dict:
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    opened = cap.isOpened()

    result = {
        "index": index,
        "opened": opened,
        "width": None,
        "height": None,
        "snapshot": None,
    }

    if opened:
        ok, frame = cap.read()
        if ok and frame is not None:
            height, width = frame.shape[:2]
            result["width"] = width
            result["height"] = height

            if output_dir is not None:
                output_dir.mkdir(parents=True, exist_ok=True)
                snapshot_path = output_dir / f"camera_{index}_probe.jpg"
                cv2.imwrite(str(snapshot_path), frame)
                result["snapshot"] = str(snapshot_path)

    cap.release()
    return result


def main():
    parser = argparse.ArgumentParser(description="List available OpenCV camera indexes.")
    parser.add_argument("--max-index", type=int, default=5)
    parser.add_argument("--save-snapshots", action="store_true")
    args = parser.parse_args()

    output_dir = Path("logs") if args.save_snapshots else None
    found = []

    for index in range(args.max_index + 1):
        result = probe_camera(index, output_dir)
        if result["opened"]:
            found.append(result)
            size = f"{result['width']}x{result['height']}" if result["width"] else "no frame"
            suffix = f" snapshot={result['snapshot']}" if result["snapshot"] else ""
            print(f"CAMERA index={index} opened=true frame={size}{suffix}")
        else:
            print(f"CAMERA index={index} opened=false")

    if not found:
        raise SystemExit("No camera indexes opened. Check USB connection and camera privacy settings.")


if __name__ == "__main__":
    main()
