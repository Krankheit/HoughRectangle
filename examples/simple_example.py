"""
Simple example demonstrating basic usage of the hough_rectangle library.

This example shows how to:
1. Load an edge-detected image
2. Configure the Hough rectangle detector
3. Perform Hough transform
4. Detect rectangles in the image
5. Save the results
"""

import hough_rectangle
import numpy as np


def basic_hough_example():
    """Basic example showing Hough transform usage."""
    print("=" * 60)
    print("Basic Hough Transform Example")
    print("=" * 60)
    
    # Create a simple test image (100x100 with a rectangle)
    img = np.zeros((100, 100), dtype=np.float32)
    # Draw a rectangle edge
    img[20:80, 20:21] = 255  # Left edge
    img[20:80, 79:80] = 255  # Right edge
    img[20:21, 20:80] = 255  # Top edge
    img[79:80, 20:80] = 255  # Bottom edge
    
    print(f"Created test image of shape: {img.shape}")
    
    # Create HoughRectangle object
    ht = hough_rectangle.HoughRectangle(
        100,   # L_window
        180,   # thetaBins
        200,   # rhoBins
        -90,   # thetaMin
        90     # thetaMax
    )
    
    print("Initialized HoughRectangle detector")
    
    # Apply Hough transform
    hough_result = ht.hough_transform(img)
    print(f"Hough transform result shape: {hough_result.shape}")
    print(f"Max value in Hough space: {np.max(hough_result)}")
    
    # Apply enhanced Hough transform
    enhanced = ht.enhance_hough(hough_result, 5, 5)
    print(f"Enhanced Hough transform shape: {enhanced.shape}")
    
    print("\n✓ Basic Hough transform completed successfully!\n")


def config_example():
    """Example showing how to use Config object."""
    print("=" * 60)
    print("Configuration Example")
    print("=" * 60)
    
    # Create and configure a Config object
    config = hough_rectangle.Config()
    
    # Set Hough transform parameters
    config.thetaBins = 256
    config.rhoBins = 256
    config.thetaMin = -90
    config.thetaMax = 90
    
    # Set enhanced Hough parameters
    config.h = 5
    config.w = 5
    
    # Set windowed Hough parameters
    config.L_window = 100
    config.r_min = 20
    config.r_max = 80
    
    # Set rectangle detection parameters
    config.min_side_length = 10
    config.T_theta = 5.0
    config.T_rho = 5.0
    config.T_l = 10.0
    config.T_alpha = 10.0
    
    print("Configuration created:")
    print(f"  Theta bins: {config.thetaBins}")
    print(f"  Rho bins: {config.rhoBins}")
    print(f"  Window size: {config.L_window}")
    print(f"  Min side length: {config.min_side_length}")
    
    # Create HoughRectangle with config parameters
    ht = hough_rectangle.HoughRectangle(
        config.L_window,
        config.thetaBins,
        config.rhoBins,
        config.thetaMin,
        config.thetaMax
    )
    
    print("\n✓ Configuration example completed successfully!\n")


def rectangle_detection_example():
    """Example showing full rectangle detection pipeline."""
    print("=" * 60)
    print("Rectangle Detection Example")
    print("=" * 60)
    
    # Create test image with a clear rectangle
    img = np.zeros((150, 150), dtype=np.float32)
    # Draw rectangle edges (thicker for better detection)
    img[30:100, 30:33] = 255    # Left edge
    img[30:100, 97:100] = 255   # Right edge
    img[30:33, 30:100] = 255    # Top edge
    img[97:100, 30:100] = 255   # Bottom edge
    
    print(f"Created test image with rectangle: {img.shape}")
    
    # Setup configuration
    config = hough_rectangle.Config()
    config.L_window = 150
    config.thetaBins = 180
    config.rhoBins = 200
    config.thetaMin = -90
    config.thetaMax = 90
    config.min_side_length = 5
    config.T_theta = 10.0
    config.T_rho = 10.0
    config.T_l = 15.0
    config.T_alpha = 15.0
    config.h = 5
    config.w = 5
    
    # Create detector
    ht = hough_rectangle.HoughRectangle(
        config.L_window,
        config.thetaBins,
        config.rhoBins,
        config.thetaMin,
        config.thetaMax
    )
    
    # Apply Hough transform
    hough_img = ht.hough_transform(img)
    print(f"Hough transform computed: {hough_img.shape}")
    
    # Find local maxima
    indexes = hough_rectangle.find_local_maximum(hough_img, config.min_side_length)
    print(f"Found {len(indexes)} local maxima")
    
    if len(indexes) > 0:
        # Convert indexes to rho and theta
        rho_maxs, theta_maxs = ht.index_rho_theta(indexes)
        print(f"Converted to {len(rho_maxs)} rho values and {len(theta_maxs)} theta values")
        
        # Find pairs
        pairs = hough_rectangle.find_pairs(
            rho_maxs,
            theta_maxs,
            config.T_rho,
            config.T_theta,
            config.T_l
        )
        print(f"Found {len(pairs)} pairs")
        
        if len(pairs) > 0:
            # Match into rectangles
            rectangles = hough_rectangle.match_pairs_into_rectangle(
                pairs,
                config.T_alpha
            )
            print(f"Detected {len(rectangles)} potential rectangles")
            
            if len(rectangles) > 0:
                # Remove duplicates
                best_rect = hough_rectangle.remove_duplicates_float(
                    rectangles,
                    1.0,
                    4.0
                )
                print(f"Best rectangle found: {best_rect}")
                
                # Convert to corner format
                rect_corners = hough_rectangle.convert_all_rects_2_corner_format_single(
                    best_rect,
                    config.L_window,
                    config.L_window
                )
                print(f"Rectangle corners: {rect_corners}")
    
    print("\n✓ Rectangle detection example completed!\n")


def utility_functions_example():
    """Example showing utility functions."""
    print("=" * 60)
    print("Utility Functions Example")
    print("=" * 60)
    
    # Test coordinate conversion
    angle = 45.0  # degrees
    rho = 100.0   # pixels
    
    cartesian = hough_rectangle.convert_normal2cartesian(angle, rho)
    print(f"Normal coordinates (angle={angle}°, rho={rho})")
    print(f"  → Cartesian: {cartesian}")
    
    # Test rectangle offset correction
    rectangle = [10, 10, 50, 10, 50, 50, 10, 50]  # x1,y1,x2,y2,x3,y3,x4,y4
    print(f"\nOriginal rectangle: {rectangle}")
    
    hough_rectangle.correct_offset_rectangle(rectangle, 20, 30)
    print(f"After offset correction (x=20, y=30): {rectangle}")
    
    print("\n✓ Utility functions example completed!\n")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Hough Rectangle Detection - Python Examples")
    print("="*60 + "\n")
    
    try:
        basic_hough_example()
        config_example()
        rectangle_detection_example()
        utility_functions_example()
        
        print("="*60)
        print("All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
