cmake_minimum_required(VERSION 3.10)

# THIS IS THE NEW LINE: It tells CMake exactly where to find our vcpkg libraries
set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake" CACHE STRING "Vcpkg toolchain file")

project(ANPR_System)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find the vcpkg libraries
find_package(OpenCV REQUIRED)
find_package(Tesseract REQUIRED)

# Create our main software executable
add_executable(ANPR_App main.cpp)

# Link the libraries to our software
target_link_libraries(ANPR_App PRIVATE ${OpenCV_LIBS} Tesseract::libtesseract)