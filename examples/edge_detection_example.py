"""
Example demonstrating edge detection preprocessing for Hough rectangle detection.

This script shows how to:
1. Load a regular image
2. Apply edge detection (Canny)
3. Use the hough_rectangle library to detect rectangles
4. Visualize and save results

Note: This example requires OpenCV (cv2) to be installed:
    pip install opencv-python
"""

import sys

try:
    import cv2
    import numpy as np
    import hough_rectangle
except ImportError as e:
    print(f"Error: {e}")
    print("\nPlease install required packages:")
    print("  pip install opencv-python numpy")
    print("  pip install .")
    sys.exit(1)


def preprocess_image(image_path, display=False):
    """
    Apply edge detection to an input image.
    
    Args:
        image_path: Path to input image
        display: If True, display intermediate results
    
    Returns:
        Edge-detected image as numpy array
    """
    print(f"Loading image: {image_path}")
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"  Image shape: {gray.shape}")
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    print("  Applied Gaussian blur")
    
    # Apply Canny edge detection
    edges = cv2.Canny(blurred, 50, 150)
    print("  Applied Canny edge detection")
    
    # Optional: Apply morphological operations to clean up edges
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    print("  Applied morphological closing")
    
    if display:
        try:
            cv2.imshow('Original', gray)
            cv2.imshow('Edges', edges)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except:
            print("  (Display not available in headless environment)")
    
    return edges.astype(np.float32)


def detect_rectangles_in_image(edge_image, config):
    """
    Detect rectangles in an edge-detected image.
    
    Args:
        edge_image: Edge-detected image (numpy array)
        config: hough_rectangle.Config object
    
    Returns:
        List of detected rectangles
    """
    print("\nDetecting rectangles...")
    
    # Create HoughRectangle detector
    ht = hough_rectangle.HoughRectangle(
        config.L_window,
        config.thetaBins,
        config.rhoBins,
        config.thetaMin,
        config.thetaMax
    )
    
    rectangles = []
    rows, cols = edge_image.shape
    
    # Slide window across image
    step = max(10, config.L_window // 4)  # Adaptive step size
    total_windows = ((rows - config.L_window) // step) * ((cols - config.L_window) // step)
    processed = 0
    
    for i in range(0, rows - config.L_window, step):
        for j in range(0, cols - config.L_window, step):
            processed += 1
            if processed % 100 == 0:
                print(f"  Progress: {processed}/{total_windows} windows")
            
            # Extract window
            window = edge_image[i:i+config.L_window, j:j+config.L_window]
            
            # Skip if window is mostly empty
            if np.sum(window > 0) < 10:
                continue
            
            # Apply Hough transform
            hough_img = ht.hough_transform(window)
            
            # Detect peaks
            indexes = hough_rectangle.find_local_maximum(hough_img, config.min_side_length)
            
            if len(indexes) == 0:
                continue
            
            # Convert to rho and theta
            rho_maxs, theta_maxs = ht.index_rho_theta(indexes)
            
            # Find pairs
            pairs = hough_rectangle.find_pairs(
                rho_maxs,
                theta_maxs,
                config.T_rho,
                config.T_theta,
                config.T_l
            )
            
            if len(pairs) == 0:
                continue
            
            # Match into rectangles
            rectangles_tmp = hough_rectangle.match_pairs_into_rectangle(
                pairs,
                config.T_alpha
            )
            
            if len(rectangles_tmp) == 0:
                continue
            
            # Remove duplicates
            detected_rectangle = hough_rectangle.remove_duplicates_float(
                rectangles_tmp,
                1.0,
                4.0
            )
            
            # Convert to corner format
            rect_corners = hough_rectangle.convert_all_rects_2_corner_format_single(
                detected_rectangle,
                config.L_window,
                config.L_window
            )
            
            # Correct offset
            hough_rectangle.correct_offset_rectangle(rect_corners, j, i)
            rectangles.append(rect_corners)
    
    print(f"\n  Detected {len(rectangles)} rectangles")
    return rectangles


def visualize_results(original_image_path, rectangles, output_path="output_with_rectangles.png"):
    """
    Visualize detected rectangles on the original image.
    
    Args:
        original_image_path: Path to original image
        rectangles: List of detected rectangles
        output_path: Path to save output image
    """
    print(f"\nVisualizing results...")
    
    # Load original image
    img = cv2.imread(original_image_path)
    if img is None:
        print("  Could not load original image for visualization")
        return
    
    # Draw rectangles
    for rect in rectangles:
        # rect format: x1,y1,x2,y2,x3,y3,x4,y4
        points = np.array([
            [rect[0], rect[1]],
            [rect[2], rect[3]],
            [rect[4], rect[5]],
            [rect[6], rect[7]]
        ], np.int32)
        
        # Draw polygon
        cv2.polylines(img, [points], True, (0, 255, 0), 2)
    
    # Save result
    cv2.imwrite(output_path, img)
    print(f"  Saved visualization to: {output_path}")
    
    return img


def main():
    """Main function to run the complete pipeline."""
    print("="*70)
    print("Hough Rectangle Detection - Complete Pipeline Example")
    print("="*70)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage: python edge_detection_example.py <input_image_path>")
        print("\nExample:")
        print("  python edge_detection_example.py input.png")
        print("\nNote: This will create edge_detected.png and output_with_rectangles.png")
        return
    
    input_image = sys.argv[1]
    
    try:
        # Step 1: Edge detection
        print("\n" + "-"*70)
        print("Step 1: Edge Detection")
        print("-"*70)
        edges = preprocess_image(input_image)
        
        # Save edge image
        edge_path = "edge_detected.png"
        cv2.imwrite(edge_path, edges)
        print(f"\nSaved edge-detected image to: {edge_path}")
        
        # Step 2: Configure detector
        print("\n" + "-"*70)
        print("Step 2: Configure Detector")
        print("-"*70)
        config = hough_rectangle.Config()
        config.thetaBins = 180
        config.rhoBins = 200
        config.thetaMin = -90
        config.thetaMax = 90
        config.h = 5
        config.w = 5
        config.L_window = 100
        config.r_min = 20
        config.r_max = 80
        config.min_side_length = 10
        config.T_theta = 8.0
        config.T_rho = 8.0
        config.T_l = 15.0
        config.T_alpha = 15.0
        
        print(f"  Window size: {config.L_window}x{config.L_window}")
        print(f"  Theta bins: {config.thetaBins}")
        print(f"  Rho bins: {config.rhoBins}")
        
        # Step 3: Detect rectangles
        print("\n" + "-"*70)
        print("Step 3: Rectangle Detection")
        print("-"*70)
        rectangles = detect_rectangles_in_image(edges, config)
        
        # Step 4: Save results
        print("\n" + "-"*70)
        print("Step 4: Save Results")
        print("-"*70)
        
        if rectangles:
            # Save to text file
            output_txt = "detected_rectangles.txt"
            hough_rectangle.save_rectangle_multi(output_txt, rectangles)
            print(f"  Saved rectangles to: {output_txt}")
            
            # Visualize
            visualize_results(input_image, rectangles)
        else:
            print("  No rectangles detected")
        
        print("\n" + "="*70)
        print("Pipeline completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
