# Hough Rectangle Detection - Python Library

[中文文档](#中文文档) | [English Documentation](#english-documentation)

---

## 中文文档

这是一个基于 Hough 变换的矩形检测算法的 Python 库，从 C++ 代码转换而来。该库使用 pybind11 提供高性能的 Python 接口。

### 安装

#### 前置要求

- Python >= 3.6
- CMake >= 3.5
- C++ 编译器 (支持 C++14)
- NumPy >= 1.19.0

#### 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/Krankheit/HoughRectangle.git
cd HoughRectangle

# 安装
pip install .
```

如果您想在开发模式下安装（可编辑安装）：

```bash
pip install -e .
```

### 快速开始

#### 基本用法

```python
import hough_rectangle
import numpy as np
from PIL import Image

# 1. 加载边缘检测后的图像（必须是二值图像）
# 注意：输入图像应该是边缘检测后的结果
img = Image.open('edge_detected_image.png').convert('L')
img_array = np.array(img, dtype=np.float32)

# 2. 创建配置对象
config = hough_rectangle.Config()
config.thetaBins = 256          # 角度bins数量
config.rhoBins = 256            # rho bins数量
config.thetaMin = -90          # 最小角度
config.thetaMax = 90           # 最大角度
config.h = 5                   # 增强Hough变换的邻域高度
config.w = 5                   # 增强Hough变换的邻域宽度
config.L_window = 100          # 窗口大小（应大于矩形的最大尺寸）
config.r_min = 20              # 窗口Hough变换的内半径
config.r_max = 80              # 窗口Hough变换的外半径
config.min_side_length = 10    # 矩形的最小边长
config.T_theta = 5.0           # 角度差异阈值
config.T_rho = 5.0             # rho差异阈值
config.T_l = 10.0              # T_l参数
config.T_alpha = 10.0          # 角点差异阈值

# 3. 创建 HoughRectangle 对象
ht = hough_rectangle.HoughRectangle(
    config.L_window,
    config.thetaBins,
    config.rhoBins,
    config.thetaMin,
    config.thetaMax
)

# 4. 执行 Hough 变换
hough_img = ht.hough_transform(img_array)
print(f"Hough transform shape: {hough_img.shape}")

# 5. 应用增强 Hough 变换
enhanced = ht.enhance_hough(hough_img, config.h, config.w)

# 6. 检测峰值并查找矩形
# 这是一个简化的示例，完整的检测需要遍历图像的不同窗口
```

#### 完整的矩形检测示例

```python
import hough_rectangle
import numpy as np

def detect_rectangles(image_path, config):
    """
    在图像中检测矩形
    
    Args:
        image_path: 边缘检测后的图像路径（PNG格式）
        config: hough_rectangle.Config 对象
    
    Returns:
        检测到的矩形列表
    """
    # 读取图像
    gray = hough_rectangle.read_image(image_path)
    
    # 创建 HoughRectangle 对象
    ht = hough_rectangle.HoughRectangle(
        config.L_window,
        config.thetaBins,
        config.rhoBins,
        config.thetaMin,
        config.thetaMax
    )
    
    rectangles = []
    rows = gray.rows()
    cols = gray.cols()
    
    # 在图像上滑动窗口
    for i in range(0, rows - config.L_window, 10):  # 步长为10加快速度
        print(f"处理行 {i}/{rows}")
        for j in range(0, cols - config.L_window, 10):
            # 提取窗口
            window = gray[i:i+config.L_window, j:j+config.L_window]
            
            # 执行 Hough 变换
            hough_img = ht.hough_transform(window)
            
            # 检测峰值
            indexes = hough_rectangle.find_local_maximum(
                hough_img,
                config.min_side_length
            )
            
            if len(indexes) == 0:
                continue
            
            # 转换为 rho 和 theta 值
            rho_maxs, theta_maxs = ht.index_rho_theta(indexes)
            
            # 查找配对
            pairs = hough_rectangle.find_pairs(
                rho_maxs,
                theta_maxs,
                config.T_rho,
                config.T_theta,
                config.T_l
            )
            
            if len(pairs) == 0:
                continue
            
            # 将配对匹配成矩形
            rectangles_tmp = hough_rectangle.match_pairs_into_rectangle(
                pairs,
                config.T_alpha
            )
            
            if len(rectangles_tmp) == 0:
                continue
            
            # 移除重复
            detected_rectangle = hough_rectangle.remove_duplicates_float(
                rectangles_tmp,
                1.0,
                4.0
            )
            
            # 转换为角点格式
            rect_corners = hough_rectangle.convert_all_rects_2_corner_format_single(
                detected_rectangle,
                config.L_window,
                config.L_window
            )
            
            # 修正偏移
            hough_rectangle.correct_offset_rectangle(rect_corners, j, i)
            rectangles.append(rect_corners)
    
    return rectangles


# 使用示例
config = hough_rectangle.Config()
config.thetaBins = 256
config.rhoBins = 256
config.thetaMin = -90
config.thetaMax = 90
config.h = 5
config.w = 5
config.L_window = 100
config.r_min = 20
config.r_max = 80
config.min_side_length = 10
config.T_theta = 5.0
config.T_rho = 5.0
config.T_l = 10.0
config.T_alpha = 10.0

# 检测矩形
rectangles = detect_rectangles("edge_detected_image.png", config)

# 保存结果
if rectangles:
    hough_rectangle.save_rectangle_multi("output_rectangles.txt", rectangles)
    print(f"检测到 {len(rectangles)} 个矩形")
else:
    print("未检测到矩形")
```

### 边缘检测预处理

该库需要边缘检测后的图像作为输入。您可以使用 OpenCV 进行边缘检测：

```python
import cv2

# 读取原始图像
img = cv2.imread('input_image.png', cv2.IMREAD_GRAYSCALE)

# 应用高斯模糊
blurred = cv2.GaussianBlur(img, (5, 5), 0)

# Canny 边缘检测
edges = cv2.Canny(blurred, 50, 150)

# 保存边缘图像
cv2.imwrite('edge_detected_image.png', edges)
```

### API 参考

#### Config 类

配置参数对象：

- `thetaBins`: 角度bins的数量
- `rhoBins`: rho bins的数量
- `thetaMin`: 最小角度（通常为 -90）
- `thetaMax`: 最大角度（通常为 90）
- `h`: 增强Hough变换的邻域高度
- `w`: 增强Hough变换的邻域宽度
- `L_window`: 窗口大小（应大于矩形）
- `r_min`: 内环半径
- `r_max`: 外环半径
- `min_side_length`: 最小边长
- `T_theta`: 角度差异阈值
- `T_rho`: rho差异阈值
- `T_l`: T_l参数
- `T_alpha`: 角点差异阈值

#### HoughRectangle 类

主要方法：

- `hough_transform(img)`: 对图像应用经典 Hough 变换
- `windowed_hough(img, r_min, r_max)`: 执行窗口 Hough 变换
- `enhance_hough(hough, h, w)`: 计算增强 Hough 变换
- `ring(img, r_min, r_max)`: 在矩阵上应用环形遮罩
- `index_rho_theta(indexes)`: 将索引转换为 rho 和 theta 位置

#### 函数

- `find_pairs(rho_maxs, theta_maxs, T_rho, T_t, T_L)`: 将检测到的峰值匹配成配对
- `match_pairs_into_rectangle(pairs, T_alpha)`: 将配对匹配成矩形
- `remove_duplicates_float(rectangles, a, b)`: 移除重复的矩形
- `find_local_maximum(img, threshold)`: 在图像中查找局部最大值
- `convert_all_rects_2_corner_format_single(rectangle, x_size, y_size)`: 转换为角点格式
- `correct_offset_rectangle(rectangle, x_bias, y_bias)`: 修正矩形偏移
- `read_image(filename)`: 加载PNG图像
- `save_rectangle_multi(filename, rectangles)`: 保存矩形到文本文件

### 输出格式

矩形以以下格式保存在文本文件中（每行一个矩形）：
```
x1,y1,x2,y2,x3,y3,x4,y4
```

其中 (x1,y1), (x2,y2), (x3,y3), (x4,y4) 是矩形的四个角点。

### 性能提示

1. 使用适当的窗口大小（`L_window`）- 应大于要检测的最大矩形
2. 调整步长以平衡速度和精度
3. 根据图像调整阈值参数
4. 考虑使用多处理来并行处理不同的图像区域

---

## English Documentation

This is a Python library for rectangle detection using Hough transform, converted from C++ code. The library uses pybind11 to provide a high-performance Python interface.

### Installation

#### Prerequisites

- Python >= 3.6
- CMake >= 3.5
- C++ compiler (with C++14 support)
- NumPy >= 1.19.0

#### Install from Source

```bash
# Clone the repository
git clone https://github.com/Krankheit/HoughRectangle.git
cd HoughRectangle

# Install
pip install .
```

For development (editable install):

```bash
pip install -e .
```

### Quick Start

#### Basic Usage

```python
import hough_rectangle
import numpy as np
from PIL import Image

# 1. Load edge-detected image (must be binary)
# Note: Input image should be the result of edge detection
img = Image.open('edge_detected_image.png').convert('L')
img_array = np.array(img, dtype=np.float32)

# 2. Create configuration object
config = hough_rectangle.Config()
config.thetaBins = 256          # Number of angle bins
config.rhoBins = 256            # Number of rho bins
config.thetaMin = -90          # Minimum angle
config.thetaMax = 90           # Maximum angle
config.h = 5                   # Height of neighborhood for enhanced Hough
config.w = 5                   # Width of neighborhood for enhanced Hough
config.L_window = 100          # Window size (should be larger than max rectangle)
config.r_min = 20              # Inner radius of windowed Hough
config.r_max = 80              # Outer radius of windowed Hough
config.min_side_length = 10    # Minimum side length of rectangle
config.T_theta = 5.0           # Angle difference threshold
config.T_rho = 5.0             # Rho difference threshold
config.T_l = 10.0              # T_l parameter
config.T_alpha = 10.0          # Corner difference threshold

# 3. Create HoughRectangle object
ht = hough_rectangle.HoughRectangle(
    config.L_window,
    config.thetaBins,
    config.rhoBins,
    config.thetaMin,
    config.thetaMax
)

# 4. Apply Hough transform
hough_img = ht.hough_transform(img_array)
print(f"Hough transform shape: {hough_img.shape}")

# 5. Apply enhanced Hough transform
enhanced = ht.enhance_hough(hough_img, config.h, config.w)

# 6. Detect peaks and find rectangles
# This is a simplified example; full detection requires sliding windows
```

#### Complete Rectangle Detection Example

```python
import hough_rectangle
import numpy as np

def detect_rectangles(image_path, config):
    """
    Detect rectangles in an image
    
    Args:
        image_path: Path to edge-detected image (PNG format)
        config: hough_rectangle.Config object
    
    Returns:
        List of detected rectangles
    """
    # Read image
    gray = hough_rectangle.read_image(image_path)
    
    # Create HoughRectangle object
    ht = hough_rectangle.HoughRectangle(
        config.L_window,
        config.thetaBins,
        config.rhoBins,
        config.thetaMin,
        config.thetaMax
    )
    
    rectangles = []
    rows = gray.rows()
    cols = gray.cols()
    
    # Slide window across image
    for i in range(0, rows - config.L_window, 10):  # stride of 10 for speed
        print(f"Processing row {i}/{rows}")
        for j in range(0, cols - config.L_window, 10):
            # Extract window
            window = gray[i:i+config.L_window, j:j+config.L_window]
            
            # Apply Hough transform
            hough_img = ht.hough_transform(window)
            
            # Detect peaks
            indexes = hough_rectangle.find_local_maximum(
                hough_img,
                config.min_side_length
            )
            
            if len(indexes) == 0:
                continue
            
            # Convert to rho and theta values
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
            
            # Match pairs into rectangles
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
    
    return rectangles


# Usage example
config = hough_rectangle.Config()
config.thetaBins = 256
config.rhoBins = 256
config.thetaMin = -90
config.thetaMax = 90
config.h = 5
config.w = 5
config.L_window = 100
config.r_min = 20
config.r_max = 80
config.min_side_length = 10
config.T_theta = 5.0
config.T_rho = 5.0
config.T_l = 10.0
config.T_alpha = 10.0

# Detect rectangles
rectangles = detect_rectangles("edge_detected_image.png", config)

# Save results
if rectangles:
    hough_rectangle.save_rectangle_multi("output_rectangles.txt", rectangles)
    print(f"Detected {len(rectangles)} rectangles")
else:
    print("No rectangles detected")
```

### Edge Detection Preprocessing

This library requires edge-detected images as input. You can use OpenCV for edge detection:

```python
import cv2

# Read original image
img = cv2.imread('input_image.png', cv2.IMREAD_GRAYSCALE)

# Apply Gaussian blur
blurred = cv2.GaussianBlur(img, (5, 5), 0)

# Canny edge detection
edges = cv2.Canny(blurred, 50, 150)

# Save edge image
cv2.imwrite('edge_detected_image.png', edges)
```

### API Reference

#### Config Class

Configuration parameters object:

- `thetaBins`: Number of angle bins
- `rhoBins`: Number of rho bins
- `thetaMin`: Minimum angle (typically -90)
- `thetaMax`: Maximum angle (typically 90)
- `h`: Height of neighborhood for enhanced Hough
- `w`: Width of neighborhood for enhanced Hough
- `L_window`: Window size (should be larger than rectangles)
- `r_min`: Inner ring radius
- `r_max`: Outer ring radius
- `min_side_length`: Minimum side length
- `T_theta`: Angle difference threshold
- `T_rho`: Rho difference threshold
- `T_l`: T_l parameter
- `T_alpha`: Corner difference threshold

#### HoughRectangle Class

Main methods:

- `hough_transform(img)`: Apply classic Hough transform on image
- `windowed_hough(img, r_min, r_max)`: Perform windowed Hough transform
- `enhance_hough(hough, h, w)`: Compute enhanced Hough transform
- `ring(img, r_min, r_max)`: Apply ring mask on matrix
- `index_rho_theta(indexes)`: Convert indexes to rho and theta positions

#### Functions

- `find_pairs(rho_maxs, theta_maxs, T_rho, T_t, T_L)`: Match detected peaks into pairs
- `match_pairs_into_rectangle(pairs, T_alpha)`: Match pairs into rectangles
- `remove_duplicates_float(rectangles, a, b)`: Remove duplicate rectangles
- `find_local_maximum(img, threshold)`: Find local maxima in image
- `convert_all_rects_2_corner_format_single(rectangle, x_size, y_size)`: Convert to corner format
- `correct_offset_rectangle(rectangle, x_bias, y_bias)`: Correct rectangle offset
- `read_image(filename)`: Load PNG image
- `save_rectangle_multi(filename, rectangles)`: Save rectangles to text file

### Output Format

Rectangles are saved in text files with the following format (one rectangle per line):
```
x1,y1,x2,y2,x3,y3,x4,y4
```

Where (x1,y1), (x2,y2), (x3,y3), (x4,y4) are the four corners of the rectangle.

### Performance Tips

1. Use appropriate window size (`L_window`) - should be larger than the largest rectangle to detect
2. Adjust stride to balance speed and accuracy
3. Tune threshold parameters based on your images
4. Consider using multiprocessing to parallelize processing of different image regions

### Troubleshooting

#### Build Issues

If you encounter build issues:

1. Make sure CMake >= 3.5 is installed
2. Ensure you have a C++14 compatible compiler
3. Check that Eigen3 is available on your system
4. Try cleaning build artifacts: `rm -rf build/ *.egg-info/`

#### Runtime Issues

1. **Import Error**: Make sure the module is properly installed
2. **Image Format Error**: Ensure input images are edge-detected binary images
3. **No Rectangles Detected**: Try adjusting threshold parameters or window size

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

This project follows the original C++ project's license.

### Acknowledgments

This Python binding is based on the C++ implementation of the Hough rectangle detection algorithm from the paper:
"Rectangle Detection based on a Windowed Hough Transform" by C.Jung and R.Schramm.
