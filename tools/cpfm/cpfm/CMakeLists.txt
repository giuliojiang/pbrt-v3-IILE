cmake_minimum_required(VERSION 2.8)

project(cpfm)

# Useful CMake options for Qt projects
set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_AUTOMOC ON)

set(project_sources
   main.cpp
   filereader.cpp
   lodepng.cpp
)

add_executable(${PROJECT_NAME}
  ${project_sources}
)
