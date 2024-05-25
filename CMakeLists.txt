cmake_minimum_required(VERSION 3.27)
project(NCD)

set(CMAKE_CXX_STANDARD 17)

add_executable(NCD src/main.cpp
        src/audio_processing.cpp
        src/compression.cpp)
