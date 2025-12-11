#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/eigen.h>
#include <pybind11/numpy.h>

#include "process_image.hpp"
#include "rectangle_detection.hpp"
#include "rectangle_utils.hpp"
#include "eigen_utils.hpp"
#include "io.hpp"
#include "config.hpp"
#include "recursive_hough_transform.hpp"

namespace py = pybind11;

// Helper function to convert NumPy array to Eigen matrix
Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> 
numpy_to_eigen(py::array_t<float> input) {
    py::buffer_info buf = input.request();
    
    if (buf.ndim != 2) {
        throw std::runtime_error("Input must be a 2D array");
    }
    
    int rows = buf.shape[0];
    int cols = buf.shape[1];
    
    Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> mat(rows, cols);
    
    float* ptr = static_cast<float*>(buf.ptr);
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            mat(i, j) = ptr[i * cols + j];
        }
    }
    
    return mat;
}

// Helper function to convert Eigen matrix to NumPy array
py::array_t<float> eigen_to_numpy(
    const Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>& mat) {
    int rows = mat.rows();
    int cols = mat.cols();
    
    py::array_t<float> result({rows, cols});
    py::buffer_info buf = result.request();
    float* ptr = static_cast<float*>(buf.ptr);
    
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            ptr[i * cols + j] = mat(i, j);
        }
    }
    
    return result;
}

PYBIND11_MODULE(hough_rectangle, m) {
    m.doc() = "Hough Rectangle Detection Library - Python bindings for C++ implementation";

    // Bind Config struct
    py::class_<Config>(m, "Config")
        .def(py::init<>())
        .def_readwrite("thetaBins", &Config::thetaBins, "Number of angle bins")
        .def_readwrite("rhoBins", &Config::rhoBins, "Number of bins for the normal length")
        .def_readwrite("thetaMin", &Config::thetaMin, "Minimum angle")
        .def_readwrite("thetaMax", &Config::thetaMax, "Maximum angle")
        .def_readwrite("h", &Config::h, "Height of neighborhood for enhanced Hough")
        .def_readwrite("w", &Config::w, "Width of neighborhood for enhanced Hough")
        .def_readwrite("L_window", &Config::L_window, "Size of the window")
        .def_readwrite("r_min", &Config::r_min, "Inner radius of windowed Hough")
        .def_readwrite("r_max", &Config::r_max, "Outer radius of windowed Hough")
        .def_readwrite("min_side_length", &Config::min_side_length, "Minimum side length")
        .def_readwrite("T_theta", &Config::T_theta, "Minimum angle difference threshold")
        .def_readwrite("T_rho", &Config::T_rho, "Minimum normal length difference threshold")
        .def_readwrite("T_l", &Config::T_l, "T_l parameter")
        .def_readwrite("T_alpha", &Config::T_alpha, "Minimum corner difference threshold");

    // Bind HoughRectangle class with Python-friendly interface
    py::class_<HoughRectangle>(m, "HoughRectangle")
        .def(py::init<>())
        .def(py::init<int, int, int, float, float>(),
             py::arg("L_window"),
             py::arg("thetaBins"),
             py::arg("rhoBins"),
             py::arg("thetaMin"),
             py::arg("thetaMax"),
             "Initialize HoughRectangle with parameters")
        .def("hough_transform", 
             [](HoughRectangle& self, py::array_t<float> img) {
                 auto eigen_img = numpy_to_eigen(img);
                 auto result = self.hough_transform(eigen_img);
                 return eigen_to_numpy(result);
             },
             py::arg("img"),
             "Apply classic Hough transform on the image")
        .def("windowed_hough",
             [](HoughRectangle& self, py::array_t<float> img, int r_min, int r_max) {
                 auto eigen_img = numpy_to_eigen(img);
                 auto result = self.windowed_hough(eigen_img, r_min, r_max);
                 return eigen_to_numpy(result);
             },
             py::arg("img"),
             py::arg("r_min"),
             py::arg("r_max"),
             "Perform windowed Hough transform on a single patch")
        .def("enhance_hough",
             [](HoughRectangle& self, py::array_t<float> hough, int h, int w) {
                 auto eigen_hough = numpy_to_eigen(hough);
                 auto result = self.enhance_hough(eigen_hough, h, w);
                 return eigen_to_numpy(result);
             },
             py::arg("hough"),
             py::arg("h"),
             py::arg("w"),
             "Compute enhanced Hough transform")
        .def("ring",
             [](HoughRectangle& self, py::array_t<float> img, int r_min, int r_max) {
                 auto eigen_img = numpy_to_eigen(img);
                 auto result = self.ring(eigen_img, r_min, r_max);
                 return eigen_to_numpy(result);
             },
             py::arg("img"),
             py::arg("r_min"),
             py::arg("r_max"),
             "Apply a ring mask on the input matrix")
        .def("index_rho_theta",
             &HoughRectangle::index_rho_theta,
             py::arg("indexes"),
             "Convert indexes to theta and rho positions");

    // Bind RecursiveHoughTransform class
    py::class_<RecursiveHoughTransform, HoughRectangle>(m, "RecursiveHoughTransform")
        .def(py::init<>())
        .def(py::init<int, int, int, float, float>(),
             py::arg("L_window"),
             py::arg("thetaBins"),
             py::arg("rhoBins"),
             py::arg("thetaMin"),
             py::arg("thetaMax"));

    // Bind rectangle detection functions
    m.def("find_pairs",
          &rectangle_detect::find_pairs,
          py::arg("rho_maxs"),
          py::arg("theta_maxs"),
          py::arg("T_rho"),
          py::arg("T_t"),
          py::arg("T_L"),
          "Match detected peaks into pairs");

    m.def("match_pairs_into_rectangle",
          &rectangle_detect::match_pairs_into_rectangle,
          py::arg("pairs"),
          py::arg("T_alpha"),
          "Match detected peaks into rectangles");

    m.def("remove_duplicates_int",
          py::overload_cast<std::vector<std::array<int, 8>>, float, float>(
              &rectangle_detect::remove_duplicates),
          py::arg("rectangles"),
          py::arg("a"),
          py::arg("b"),
          "Remove duplicate rectangles (int version)");

    m.def("remove_duplicates_float",
          py::overload_cast<std::vector<std::array<float, 8>>, float, float>(
              &rectangle_detect::remove_duplicates),
          py::arg("rectangles"),
          py::arg("a"),
          py::arg("b"),
          "Remove duplicate rectangles (float version)");

    // Bind utility functions
    m.def("find_local_maximum",
          &find_local_maximum,
          py::arg("img"),
          py::arg("threshold"),
          "Find local maxima in the image");

    m.def("normalise_img",
          &normalise_img,
          py::arg("img"),
          "Normalize image to binary 0 and 255");

    // Bind rectangle utility functions
    m.def("convert_normal2cartesian",
          &convert_normal2cartesian,
          py::arg("angle"),
          py::arg("rho"),
          "Convert normal coordinates to cartesian coordinates");

    m.def("correct_offset_rectangle",
          &correct_offset_rectangle,
          py::arg("rectangle"),
          py::arg("x_bias"),
          py::arg("y_bias"),
          "Correct rectangle position given window offset");

    m.def("convert_normal_rect2_corners_rect",
          &convert_normal_rect2_corners_rect,
          py::arg("in_rectangle"),
          py::arg("x_size"),
          py::arg("y_size"),
          "Convert normal rectangle to corner rectangle");

    m.def("convert_all_rects_2_corner_format_single",
          py::overload_cast<const rectangle_T<float>&, const int&, const int&>(
              &convert_all_rects_2_corner_format),
          py::arg("rectangle"),
          py::arg("x_size"),
          py::arg("y_size"),
          "Convert single rectangle to corner format");

    m.def("convert_all_rects_2_corner_format_multi",
          py::overload_cast<const rectangles_T<float>&, const int&, const int&>(
              &convert_all_rects_2_corner_format),
          py::arg("rectangles"),
          py::arg("x_size"),
          py::arg("y_size"),
          "Convert multiple rectangles to corner format");

    // Bind IO functions
    m.def("read_image",
          &eigen_io::read_image,
          py::arg("filename"),
          "Load PNG image to Eigen matrix");

    m.def("save_rectangle_single",
          py::overload_cast<const std::string&, const std::array<int, 8>&>(
              &eigen_io::save_rectangle),
          py::arg("filename"),
          py::arg("rectangles"),
          "Save single detected rectangle to text file");

    m.def("save_rectangle_multi",
          py::overload_cast<const std::string&, const std::vector<std::array<int, 8>>&>(
              &eigen_io::save_rectangle),
          py::arg("filename"),
          py::arg("indexes"),
          "Save multiple detected rectangles to text file");

    m.def("save_pairs",
          &eigen_io::save_pairs,
          py::arg("filename"),
          py::arg("pairs"),
          "Save detected pairs to text file");

    m.def("save_maximum",
          &eigen_io::save_maximum,
          py::arg("filename"),
          py::arg("maximums"),
          "Save detected maximums to text file");

    // Add version info
    m.attr("__version__") = "1.0.0";
}
