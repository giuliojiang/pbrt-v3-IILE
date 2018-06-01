cmake_minimum_required(VERSION 2.8)

project(cpfm)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-Ofast -flto")

# Useful CMake options for Qt projects
set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_AUTOMOC ON)

set(project_sources
   main.cpp
   filereader.cpp
)

add_executable(${PROJECT_NAME}
  ${project_sources}
)
