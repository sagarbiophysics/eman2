add_subdirectory(pmconfig)

if(WIN32)
	add_library(UTILS  STATIC "")
	add_library(UTILS1 STATIC "")
	add_library(EMDATA STATIC "")
	add_library(EM2    STATIC "")
else()
	add_library(UTILS  SHARED "")
	add_library(UTILS1 SHARED "")
	add_library(EMDATA SHARED "")
	add_library(EM2    SHARED "")
endif()

target_sources(UTILS PRIVATE
			   geometry.cpp
			   byteorder.cpp
			   interp.cpp
			   quaternion.cpp
			   )

target_sources(UTILS1 PRIVATE
			   exception.cpp
			   util.cpp
			   randnum.cpp
			   xydata.cpp
			   log.cpp
			   )
target_sources(EMDATA PRIVATE
			   emobject.cpp
			   emfft.cpp
			   imageio.cpp
			   emutil.cpp
			   transform.cpp
			   symmetry.cpp
			   mrcio.cpp
			   dm3io.cpp
			   dm4io.cpp
			   tifio.cpp
			   hdfio.cpp
			   hdfio2.cpp
			   jpegio.cpp
			   emdata.cpp
			   emdata_io.cpp
			   emdata_core.cpp
			   emdata_modular.cpp
			   emdata_metadata.cpp
			   emdata_transform.cpp
			   pifio.cpp
			   v4l2io.cpp
			   vtkio.cpp
			   spiderio.cpp
			   sspiderio.cpp
			   pgmio.cpp
			   fitsio.cpp
			   icosio.cpp
			   lstio.cpp
			   lstfastio.cpp
			   pngio.cpp
			   salio.cpp
			   amiraio.cpp
			   xplorio.cpp
			   gatan2io.cpp
			   emio.cpp
			   imagicio.cpp
			   imagicio2.cpp
			   df3io.cpp
			   omapio.cpp
			   situsio.cpp
			   serio.cpp
			   ctf.cpp
			   processor.cpp
			   aligner.cpp
			   projector.cpp
			   cmp.cpp
			   averager.cpp
			   reconstructor_tools.cpp
			   )

target_sources(EM2 PRIVATE
			   emcache.cpp
			   hdf_filecache.cpp
			   pdbreader.cpp
			   pointarray.cpp
			   polardata.cpp
			   boxingtools.cpp
			   emdata_cuda.cpp
			   reconstructor.cpp
			   testutil.cpp
			   analyzer.cpp
			   tomoseg.cpp
			   )

target_link_libraries(UTILS Boost::python)
target_link_libraries(UTILS1 UTILS GSL::gsl GSL::gslcblas)
target_link_libraries(EMDATA UTILS1)
target_link_libraries(EM2 EMDATA)

add_subdirectory(gorgon)
add_subdirectory(sparx)

if(WIN32)
	target_compile_definitions(EM2 PUBLIC _CRT_SECURE_NO_WARNINGS _SCL_SECURE_NO_WARNINGS)
endif()

install(TARGETS EM2 EMDATA UTILS1 UTILS
		DESTINATION ${SP_DIR}
		)

if(ENABLE_FFTW3)
	find_package(FFTW3 REQUIRED)
	
	if(ENABLE_NFFT2)
		find_package(NFFT2 REQUIRED)
		target_link_libraries(NFFT2 FFTW3D::FFTW3D)
	endif()
endif()

if(WIN32 OR ENABLE_FFTW3)
    target_link_libraries(EMDATA FFTW3::FFTW3)
endif()

find_package(GSL REQUIRED)
if(WIN32)
	set_target_properties(GSL::gsl
						  PROPERTIES
						  INTERFACE_COMPILE_DEFINITIONS GSL_DLL
						  )
endif()

target_link_libraries(EM2 GSL::gsl GSL::gslcblas)

option(ENABLE_TIFF "enable TIFF support" ON)
if(ENABLE_TIFF)
	include(${CMAKE_SOURCE_DIR}/cmake/TIFF.cmake)
    target_link_libraries(EMDATA TIFF::TIFF)
endif()

option(ENABLE_JPEG "enable JPEG support" ON)
if(ENABLE_JPEG)
	include(${CMAKE_SOURCE_DIR}/cmake/JPEG.cmake)
    target_link_libraries(EMDATA JPEG::JPEG)
endif()

include(${CMAKE_SOURCE_DIR}/cmake/HDF5.cmake)
target_link_libraries(EMDATA HDF5::HDF5)

option(ENABLE_PNG "enable PNG support" ON)
if(ENABLE_PNG)
	include(${CMAKE_SOURCE_DIR}/cmake/PNG.cmake)
    target_link_libraries(EMDATA PNG::PNG)
endif()

if(ENABLE_SPARX_CUDA)
    target_link_libraries(EM2 EM2SparxCuda FFTW3::FFTW3)
endif()

if(ENABLE_EMAN_CUDA)
    target_link_libraries(EM2 EM2Cuda FFTW3::FFTW3)
endif()

if(ENABLE_NFFT2)
	target_sources(EM2 PRIVATE pointarray.cpp)
	target_link_libraries(EM2 NFFT2::NFFT2 FFTW3D::FFTW3D)
endif()

option(ENABLE_DJBFFT "enable djbfft support" OFF)
mark_as_advanced(ENABLE_DJBFFT)
if(ENABLE_DJBFFT)
	option(ENABLE_NFFT2 "enable nfft2 support" OFF)
	
	find_package(DJBFFT REQUIRED)
	target_link_libraries(EM2 DJBFFT::DJBFFT)
endif()

option(ENABLE_OPTPP "enable Opt++ support" OFF)
if(ENABLE_OPTPP)
	find_package(OPTPP REQUIRED)
	target_link_libraries(EM2 OPTPP::OPTPP)
endif()

if(ENABLE_ACML_FFT)
	find_package(ACML REQUIRED)
	target_link_libraries(EM2 ACML::ACML)
endif()

option(ENABLE_OPENGL "enable EMAN2 OpenGL usage" ON)
if(ENABLE_OPENGL)
	include(${CMAKE_SOURCE_DIR}/cmake/OpenGL.cmake)

	option(ENABLE_STATIC_FTGL "If build EMAN with libftgl.a" OFF)
	mark_as_advanced(ENABLE_STATIC_FTGL)
	
	find_package(FTGL REQUIRED)
	
	add_subdirectory(fonts)
endif()
