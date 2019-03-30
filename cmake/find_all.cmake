find_package(Python REQUIRED)
find_package(NumPy  REQUIRED)

find_package(Nosetests)

# Find Boost
include(cmake/Boost.cmake)

find_package(GSL REQUIRED)
include(${CMAKE_SOURCE_DIR}/cmake/HDF5.cmake)
