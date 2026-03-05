cmake_minimum_required(VERSION 3.16)

project(gallery LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTORCC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets Svg)
qt_standard_project_setup()

qt_add_executable(gallery
    main.cpp
    app/common/config.cpp
    app/common/config.h
    app/view/main_window.cpp
    app/view/main_window.h
    resources/gallery.qrc
)

target_link_libraries(gallery PRIVATE
    qtfluentwidgets
    Qt6::Widgets
    Qt6::Svg
)

target_include_directories(gallery PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)
