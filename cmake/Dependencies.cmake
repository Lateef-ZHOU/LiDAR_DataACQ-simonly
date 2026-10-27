include(FetchContent)
set(HANDLECORE_WITH_SIM_GIMBAL ON)
set(HANDLECORE_WITH_SIM_CARD ON)
set(TASKCORE_WITH_QML ON)
FetchContent_Declare(lidar_handle_core
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/HandleCore.git
    GIT_TAG 379401c85f0da11adde9a2f6fde8fe767fbae707
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/HandleCore")
FetchContent_Declare(lidar_algorithm
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/Algorithm.git
    GIT_TAG 00244abaf8fdabb6ad6bf2d2b875af4e60522a4f
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/Algorithm")
FetchContent_Declare(lidar_devicecore
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/DeviceCore.git
    GIT_TAG 5c63ec5c501d83a15daa65a41dca438ee4ff330f
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/DeviceCore")
FetchContent_Declare(lidar_uicore
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/UICore.git
    GIT_TAG bc9f330c8442169c4dd0fc10b5b7fbb5e7eeecb8
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/UICore")
FetchContent_Declare(lidar_chartcore
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/ChartCore.git
    GIT_TAG 223182769dcb51b6c591892edbe1655cf12219cd
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/ChartCore")
FetchContent_Declare(lidar_taskcore
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/TaskCore.git
    GIT_TAG 04b7279ba5d03396729f28aa9a717ff6785f7041
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/TaskCore")
FetchContent_Declare(lidar_simgimbaldevice
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/SimGimbalDevice.git
    GIT_TAG 8cad336a5bb0c31eb6423044c559950e33793ecb
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/SimGimbalDevice")
FetchContent_Declare(lidar_simcarddevice
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/SimCardDevice.git
    GIT_TAG ba016b9b6129abd1f747c506786015aa882c9cc3
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/SimCardDevice")
FetchContent_Declare(lidar_fixedtask
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/FixedTask.git
    GIT_TAG 705bafae11bb51efbac587012d4b8017e77cec36
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/FixedTask")
FetchContent_Declare(lidar_cycletask
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/CycleTask.git
    GIT_TAG a96dfa44ea56ce9e57cac86ab23b6665a83e6ded
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/CycleTask")
FetchContent_Declare(lidar_snaketask
    GIT_REPOSITORY https://github.com/Lateef-ZHOU/SnakeTask.git
    GIT_TAG 48d25657e69d693277d59fa44fa8395ae7857143
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/modules/SnakeTask")
FetchContent_MakeAvailable(lidar_handle_core lidar_algorithm lidar_devicecore lidar_uicore lidar_chartcore lidar_taskcore lidar_simgimbaldevice lidar_simcarddevice lidar_fixedtask lidar_cycletask lidar_snaketask)
set(sim_modules Lidar::UICore Lidar::ChartCore Lidar::TaskUI Lidar::SimGimbalDevice
    Lidar::SimCardDevice Lidar::FixedTask Lidar::CycleTask Lidar::SnakeTask)
set(sim_plugins LidarUICoreplugin LidarChartCoreplugin LidarTaskUIplugin LidarSimGimbalDeviceplugin
    LidarSimCardDeviceplugin LidarFixedTaskplugin LidarCycleTaskplugin LidarSnakeTaskplugin)
set(sim_uris Lidar.UI Lidar.Charts Lidar.TaskUI Lidar.SimGimbal Lidar.SimCard Lidar.FixedTask Lidar.CycleTask Lidar.SnakeTask)
set(sim_import_paths)
foreach(module IN LISTS sim_modules)
    get_target_property(output ${module} QT_QML_MODULE_OUTPUT_DIRECTORY)
    get_filename_component(import_root "${output}/../.." ABSOLUTE)
    list(APPEND sim_import_paths "${import_root}")
endforeach()
