cmake_minimum_required(VERSION 3.16)
project(x5_gravity_reference LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(EIGEN_INCLUDE_DIR "${PROJECT_ROOT}/vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/include"
    CACHE PATH "Directory containing Eigen/Core; used only for native verification")
if(NOT EXISTS "${EIGEN_INCLUDE_DIR}/Eigen/Core")
  message(FATAL_ERROR "Set EIGEN_INCLUDE_DIR to an Eigen include directory")
endif()
set(KDL_SRC "${CMAKE_CURRENT_SOURCE_DIR}/../reference/orocos_kdl/src")
set(KDL_FILES chain.cpp chaindynparam.cpp chainidsolver_recursive_newton_euler.cpp
    frames.cpp joint.cpp segment.cpp rigidbodyinertia.cpp rotationalinertia.cpp
    articulatedbodyinertia.cpp jntarray.cpp jntspaceinertiamatrix.cpp utilities/utility.cxx)
list(TRANSFORM KDL_FILES PREPEND "${KDL_SRC}/")
add_library(gravity_kdl SHARED ${KDL_FILES})
set_target_properties(gravity_kdl PROPERTIES OUTPUT_NAME orocos-kdl)
target_include_directories(gravity_kdl PUBLIC "${KDL_SRC}" "${CMAKE_CURRENT_BINARY_DIR}")
target_include_directories(gravity_kdl SYSTEM PUBLIC "${EIGEN_INCLUDE_DIR}")

# Only satisfies the vendor ELF's DT_NEEDED entry for the isolated math probe.
# No parser or vendor controller constructor is ever called by that probe.
add_library(gravity_parser_placeholder SHARED parser_placeholder.cpp)
set_target_properties(gravity_parser_placeholder PROPERTIES OUTPUT_NAME kdl_parser)

add_executable(kdl_reference kdl_reference.cpp)
target_link_libraries(kdl_reference PRIVATE gravity_kdl ${CMAKE_DL_LIBS})
