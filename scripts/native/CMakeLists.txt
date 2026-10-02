cmake_minimum_required(VERSION 3.18)
project(arx_comtest_bindings LANGUAGES CXX)

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)
if(NOT DEFINED ARX_SDK_SOURCE)
    message(FATAL_ERROR "ARX_SDK_SOURCE must point to the pinned vendor Python SDK")
endif()

set(ARX_BIMANUAL "${ARX_SDK_SOURCE}/bimanual")
set(ARX_CORE "${ARX_BIMANUAL}/lib/arx_x5_src/libarx_x5_src.so")
set(ARX_SOLVER "${ARX_BIMANUAL}/lib/libx5_kinematic_solver.so")
pybind11_add_module(arx_x5_python "${ARX_BIMANUAL}/src/single_arm_interface.cpp")
pybind11_add_module(kinematic_solver "${ARX_BIMANUAL}/src/kinematic_solver.cpp")
foreach(target arx_x5_python kinematic_solver)
    target_compile_features(${target} PRIVATE cxx_std_17)
    target_include_directories(${target} PRIVATE
        "${ARX_BIMANUAL}/lib" "${ARX_BIMANUAL}/lib/arx_x5_src/include"
        "${ARX_BIMANUAL}/lib/arx_hardware_interface/include")
    # Relative paths permit moving the generated SDK along with this project.
    set_target_properties(${target} PROPERTIES INSTALL_RPATH "$ORIGIN/../arx_x5_src;$ORIGIN/..")
endforeach()
target_link_libraries(arx_x5_python PRIVATE "${ARX_CORE}")
target_link_libraries(kinematic_solver PRIVATE "${ARX_SOLVER}")
install(TARGETS arx_x5_python kinematic_solver LIBRARY DESTINATION bimanual/api/arx_x5_python)
install(FILES "${ARX_CORE}" DESTINATION bimanual/api/arx_x5_src)
install(FILES "${ARX_SOLVER}" DESTINATION bimanual/api)
install(FILES "${ARX_BIMANUAL}/__init__.py" DESTINATION bimanual)
install(DIRECTORY "${ARX_BIMANUAL}/script/" DESTINATION bimanual/script
        FILES_MATCHING PATTERN "*.py" PATTERN "*.urdf")
