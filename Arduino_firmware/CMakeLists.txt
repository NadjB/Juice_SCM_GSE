set(CMAKE_TOOLCHAIN_FILE cmake/Arduino-Toolchain.cmake)
cmake_minimum_required(VERSION 3.8.2)

project(JUICE_SCM_EGSE_FW C CXX ASM)

arduino_cmake_project(JUICE_SCM_EGSE_FW BOARD_NAME mega BOARD_CPU atmega2560)

add_arduino_executable(JUICE_SCM_EGSE_FW main.cpp)
set_target_upload_port(JUICE_SCM_EGSE_FW /dev/ttyACM0)

find_arduino_library(stl ArduinoSTL 3RD_PARTY)
link_arduino_library(JUICE_SCM_EGSE_FW stl)
find_arduino_library(ina INA2xx 3RD_PARTY)
link_platform_library(ina Wire)
link_platform_library(ina EEPROM)
link_arduino_library(JUICE_SCM_EGSE_FW ina)
link_platform_library(JUICE_SCM_EGSE_FW SPI)
