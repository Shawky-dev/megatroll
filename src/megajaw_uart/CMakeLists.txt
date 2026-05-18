cmake_minimum_required(VERSION 3.8)
project(megajaw_uart)

find_package(ament_cmake REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)

add_library(megajaw_uart SHARED
  src/MotorDriver.cpp
  src/megajaw_uart_interface.cpp
)

target_include_directories(megajaw_uart PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(megajaw_uart
  hardware_interface
  pluginlib
  rclcpp
)

# No pigpio — pure POSIX serial only
pluginlib_export_plugin_description_file(hardware_interface megajaw_uart_plugin.xml)

install(TARGETS megajaw_uart
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY xacro/
  DESTINATION share/${PROJECT_NAME}/xacro
)

ament_package()
