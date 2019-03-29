function(ADD_PYSTE_LIB libname libdep)
	add_library(${libname} SHARED lib${libname}.cpp)
	
	if(WIN32)
		set(suffix .pyd)
	else()
		set(suffix .so)
	endif()

	set_target_properties(${libname}
			PROPERTIES
			PREFIX lib
			SUFFIX ${suffix}
			)
	
	target_link_libraries(${libname} ${libdep} Boost::python)
	install(TARGETS ${libname} DESTINATION ${SP_DIR})
endfunction()

ADD_PYSTE_LIB(pyAligner2       EM2)
ADD_PYSTE_LIB(pyAverager2      EM2)
ADD_PYSTE_LIB(pyCmp2           EM2)
ADD_PYSTE_LIB(pyProcessor2     EM2)
ADD_PYSTE_LIB(pyReconstructor2 EM2) 
ADD_PYSTE_LIB(pyProjector2     EM2)
ADD_PYSTE_LIB(pyEMObject2      EM2) 
ADD_PYSTE_LIB(pyEMData2        EM2)
target_sources(pyEMData2 PRIVATE emdata_wrapitems.cpp)
ADD_PYSTE_LIB(pyGeometry2      EM2)
ADD_PYSTE_LIB(pyTransform2     EM2)
ADD_PYSTE_LIB(pyPointArray2    EM2)
ADD_PYSTE_LIB(pyUtils2         EM2)
ADD_PYSTE_LIB(pyBoxingTools2   EM2)
ADD_PYSTE_LIB(pyFundamentals2  EM2)
ADD_PYSTE_LIB(pyTypeConverter2 EM2)
target_sources(pyTypeConverter2 PRIVATE typeconverter.cpp)
ADD_PYSTE_LIB(pyPolarData2     EM2)
ADD_PYSTE_LIB(pyAnalyzer2      EM2)
ADD_PYSTE_LIB(pyPDBReader2     EM2)

if(NOT WIN32)
	ADD_PYSTE_LIB(pyTomoSeg2 EM2)
endif()

if(ENABLE_OPENGL)
	ADD_PYSTE_LIB(pyGLUtils2       EM2)
	ADD_PYSTE_LIB(pyMarchingCubes2 EM2)
	
	target_sources(pyMarchingCubes2 PRIVATE
				   marchingcubes.cpp
				   )
	target_sources(pyGLUtils2 PRIVATE
				   emftgl.cpp
				   glutil.cpp
				   )
	target_link_libraries(pyMarchingCubes2 OpenGL::OpenGL)
	target_link_libraries(pyGLUtils2       pyMarchingCubes2 FTGL::FTGL)
endif()

file(GLOB empythonlibs "${CMAKE_CURRENT_SOURCE_DIR}/*.py")
install(FILES ${empythonlibs}
		DESTINATION ${SP_DIR}
		COMPONENT PythonFiles
		)

add_subdirectory(qtgui)

target_link_libraries(pyUtils2         NumPy)
target_link_libraries(pyTypeConverter2 NumPy)
