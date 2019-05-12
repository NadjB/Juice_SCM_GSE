set(CMAKE_TOOLCHAIN_FILE cmake/Arduino-Toolchain.cmake)
cmake_minimum_required(VERSION 3.8.2)

project(JUICE_SCM_EGSE_FW C CXX ASM)

arduino_cmake_project(JUICE_SCM_EGSE_FW BOARD_NAME mega BOARD_CPU atmega2560)

add_arduino_executable(JUICE_SCM_EGSE_FW main.cpp)
set_target_upload_port(JUICE_SCM_EGSE_FW /dev/ttyACM1)

find_arduino_library(stl ArduinoSTL 3RD_PARTY)
link_arduino_library(JUICE_SCM_EGSE_FW stl)
link_platform_library(JUICE_SCM_EGSE_FW Wire)
link_platform_library(JUICE_SCM_EGSE_FW SPI)

add_arduino_executable(test_ltc2983 test_ltc2983.cpp)
set_target_upload_port(test_ltc2983 /dev/ttyACM0)
find_arduino_library(lhc298X LTC298X 3RD_PARTY)
link_arduino_library(test_ltc2983 stl)
link_arduino_library(test_ltc2983 lhc298X)
link_platform_library(test_ltc2983 SPI)
