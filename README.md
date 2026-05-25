# Desktop Video Frame Extractor

A Python desktop app to open MP4 videos, preview frames, select a start/end range, and export selected frames as 100% quality JPEGs.

## Setup

1. Create a Python virtual environment (recommended).
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Usage

1. Click `Open Video` and select an MP4 file.
2. Use the preview slider to seek frames.
3. Set the `Start frame` and `End frame` range.
4. Click `Export Selected Frames`.
5. Choose a folder and export all selected frames as high-quality JPEGs.

## Notes

- JPEG export uses `cv2.IMWRITE_JPEG_QUALITY=100`.
- The preview uses the selected frame index from the preview slider.
