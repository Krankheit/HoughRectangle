# Hough Rectangle Detection - Python Examples

This directory contains example scripts demonstrating how to use the `hough_rectangle` Python library.

## Prerequisites

Install the library first:

```bash
cd ..
pip install .
```

## Examples

### 1. simple_example.py

Basic usage examples showing:
- How to create and configure the detector
- Basic Hough transform operations
- Configuration options
- Utility functions

Run it:
```bash
python simple_example.py
```

### 2. edge_detection_example.py

Complete pipeline example showing:
- Image preprocessing with edge detection (requires OpenCV)
- Rectangle detection on real images
- Visualization of results

This example requires OpenCV:
```bash
pip install opencv-python
```

Run it:
```bash
python edge_detection_example.py <input_image.png>
```

Example:
```bash
# Download a test image first or use your own
python edge_detection_example.py my_image.png
```

## Output Files

The examples may create the following files:
- `edge_detected.png` - Edge-detected version of input image
- `detected_rectangles.txt` - Detected rectangle coordinates
- `output_with_rectangles.png` - Visualization with rectangles drawn

## Rectangle Format

Rectangles are saved in the format:
```
x1,y1,x2,y2,x3,y3,x4,y4
```

Where (x1,y1), (x2,y2), (x3,y3), (x4,y4) are the four corners of the rectangle.

## Tips

1. **Input Images**: The library works best with edge-detected binary images
2. **Window Size**: Adjust `L_window` to be larger than your expected rectangles
3. **Thresholds**: Tune the threshold parameters based on your specific images
4. **Performance**: Use larger step sizes in the sliding window for faster processing

## Need Help?

See the main documentation in `../README_PYTHON.md` for detailed API reference and more examples.
