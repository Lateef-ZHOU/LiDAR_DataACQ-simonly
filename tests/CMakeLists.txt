foreach(name SimGimbalDevice SimCardDevice FixedTask CycleTask SnakeTask)
    string(TOLOWER "${name}" lower)
    add_subdirectory("${lidar_${lower}_SOURCE_DIR}/tests" "${CMAKE_CURRENT_BINARY_DIR}/${name}")
endforeach()

find_package(Qt6 REQUIRED COMPONENTS Test)
qt_add_executable(simonly_probe probe.cpp ${headers} "${PROJECT_SOURCE_DIR}/src/ImportModules.cpp")
set(probe_views)
foreach(view IN LISTS views)
    list(APPEND probe_views "${PROJECT_SOURCE_DIR}/${view}")
    get_filename_component(name "${view}" NAME)
    set_source_files_properties("${PROJECT_SOURCE_DIR}/${view}" PROPERTIES QT_RESOURCE_ALIAS "${name}")
endforeach()
qt_add_qml_module(simonly_probe URI Lidar.SimOnly VERSION 1.0 RESOURCE_PREFIX /qt/qml NO_CACHEGEN
    OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/Lidar/SimOnly"
    DEPENDENCIES ${sim_uris} IMPORT_PATH ${sim_import_paths} QML_FILES ${probe_views})
qt_add_resources(simonly_probe config PREFIX / BASE "${PROJECT_SOURCE_DIR}/config"
    FILES "${PROJECT_SOURCE_DIR}/config/simulation.example.json")
qt_add_resources(simonly_probe controls PREFIX / BASE "${PROJECT_BINARY_DIR}"
    FILES "${PROJECT_BINARY_DIR}/qtquickcontrols2.conf")
target_include_directories(simonly_probe PRIVATE "${PROJECT_SOURCE_DIR}/include" "${PROJECT_SOURCE_DIR}/include/Simulation")
target_link_libraries(simonly_probe PRIVATE ${sim_modules} ${sim_plugins} Qt6::Test)
target_compile_definitions(simonly_probe PRIVATE QT_NO_KEYWORDS)
if(MSVC)
    target_compile_options(simonly_probe PRIVATE /W4 /WX)
else()
    target_compile_options(simonly_probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()
add_test(NAME simonly_runtime COMMAND simonly_probe "${CMAKE_CURRENT_BINARY_DIR}/runtime-results")
set_tests_properties(simonly_runtime PROPERTIES TIMEOUT 90
    ENVIRONMENT "QT_QPA_PLATFORM=offscreen;QSG_RHI_BACKEND=null"
    ENVIRONMENT_MODIFICATION "PATH=path_list_prepend:$<TARGET_FILE_DIR:Qt6::Core>")
