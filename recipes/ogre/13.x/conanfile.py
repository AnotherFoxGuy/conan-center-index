import os
from conans import CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration, ConanException
import conan.tools.files
import textwrap, shutil
import functools


class ogrecmakeconan(ConanFile):
    name = "ogre"
    license = "MIT"
    homepage = "https://github.com/OGRECave/ogre"
    url = "https://github.com/conan-io/conan-center-index"
    description = "A scene-oriented, flexible 3D engine written in C++ "
    topics = ("graphics", "rendering", "engine", "c++")

    settings = "os", "compiler", "build_type", "arch"

    generators = "cmake", "cmake_find_package"
    exports_sources = "CMakeLists.txt", "patches/**"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cp_bin_dir": "ANY",
        "cp_media_dir": "ANY",
        "disable_plugins": [True, False],
        # Enable Ogre asserts. Possible values:
        # 0 - Standard asserts in debug builds, nothing in release builds.
        # 1 - Standard asserts in debug builds, exceptions in release builds.
        # 2 - Exceptions in debug & release builds.
        "assert_mode": [0, 1, 2],
        "build_component_bites": [True, False],
        "build_component_hlms": [True, False],
        "build_component_meshlodgenerator": [True, False],
        "build_component_overlay": [True, False],
        "build_component_paging": [True, False],
        "build_component_property": [True, False],
        "build_component_python": [True, False],
        "build_component_rtshadersystem": [True, False],
        "build_component_terrain": [True, False],
        "build_component_volume": [True, False],
        "build_plugin_bsp": [True, False],
        "build_plugin_octree": [True, False],
        "build_plugin_pcz": [True, False],
        "build_plugin_pfx": [True, False],
        "build_plugin_freeimage": [True, False],
        "build_plugin_exrcodec": [True, False],
        "build_rendersystem_d3d11": [True, False],
        "build_rendersystem_gl": [True, False],
        "build_rendersystem_gl3plus": [True, False],
        "build_samples": [True, False],
        "build_tests": [True, False],
        "build_tools": [True, False],
        "config_enable_quad_buffer_stereo": [True, False],
        "config_filesystem_unicode": [True, False],
        # Enable Ogre thread safety support for multithreading. Possible values:
        # 0 - no thread safety. DefaultWorkQueue is not threaded.
        # 1 - background resource preparation and loading is thread safe. Threaded DefaultWorkQueue. [DEPRECATED]
        # 2 - only background resource preparation is thread safe. Threaded DefaultWorkQueue. [DEPRECATED]
        # 3 - no thread safety. Threaded DefaultWorkQueue.
        "config_threads": [0, 1, 2, 3],
        "config_enable_freeimage": [True, False],
        "install_pdb": [True, False],
        "install_samples": [True, False],
        "install_tools": [True, False],
        "install_vsprops": [True, False],
        # Make ResourceManager strict for faster operation. Possible values:
        # 0 - OFF search in all groups twice - for case sensitive and insensitive lookup [DEPRECATED]
        # 1 - PEDANTIC require an explicit resource group. Case sensitive lookup.
        # 2 - STRICT search in default group if not specified otherwise. Case sensitive lookup.
        "resourcemanager_strict": [0, 1, 2],
        "set_double": [True, False],
        "glsupport_use_egl": [True, False],
        "nodeless_positioning": [True, False],
    }

    default_options = {
        "shared": False,
        "fPIC": True,
        "cp_bin_dir": "bin",
        "cp_media_dir": "Media",
        "disable_plugins": False,
        "assert_mode": 2,
        "build_component_bites": True,
        "build_component_hlms": True,
        "build_component_meshlodgenerator": True,
        "build_component_overlay": True,
        "build_component_paging": True,
        "build_component_property": True,
        "build_component_python": False,
        "build_component_rtshadersystem": True,
        "build_component_terrain": True,
        "build_component_volume": True,
        "build_plugin_bsp": True,
        "build_plugin_octree": True,
        "build_plugin_pcz": True,
        "build_plugin_pfx": True,
        "build_plugin_freeimage": True,
        "build_plugin_exrcodec": True,
        "build_rendersystem_d3d11": True,
        "build_rendersystem_gl": True,
        "build_rendersystem_gl3plus": True,
        "build_samples": False,
        "build_tests": False,
        "build_tools": True,
        "config_enable_quad_buffer_stereo": False,
        "config_filesystem_unicode": True,
        "config_threads": 3,
        "config_enable_freeimage": True,
        "install_pdb": False,
        "install_samples": False,
        "install_tools": True,
        "install_vsprops": False,
        "resourcemanager_strict": 2,
        "set_double": False,
        "glsupport_use_egl": True,
        "nodeless_positioning": False,
    }
    exports_sources = "CMakeLists.txt", "patches/**"

    def requirements(self):
        # Required dependencies
        self.requires("zlib/1.2.12")
        self.requires("zziplib/0.13.71")
        self.requires("pugixml/1.12.1")
        self.requires("sdl/2.0.20")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("xorg/system")
            self.requires("glu/system")
        if self.options.glsupport_use_egl and self.settings.os in ["Linux", "FreeBSD"]:
            self.requires("egl/system")
        else:
            self.requires("libglvnd/1.4.0")

        # Optional dependencies
        if self.options.build_tests:
            self.requires("gtest/1.12.1")
        if self.options.build_plugin_freeimage:
            self.requires("freeimage/3.18.0")
        if self.options.build_plugin_freeimage:
            self.requires("freetype/2.11.1")
        if self.options.build_plugin_exrcodec:
            self.requires("openexr/2.5.7")

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        self.options.install_tools = self.options.build_tools
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    @property
    def _required_boost_components(self):
        return ["date_time", "thread"]

    @functools.lru_cache(1)
    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["OGRE_STATIC"] = not self.options.shared
        cmake.definitions["OGRE_CONFIG_DOUBLE"] = self.options.set_double
        cmake.definitions["OGRE_CONFIG_NODE_INHERIT_TRANSFORM"] = False
        cmake.definitions["OGRE_GLSUPPORT_USE_EGL"] = self.options.glsupport_use_egl
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, 11)
        else:
            # INFO: OpenEXR requires C++11
            cmake.definitions["CMAKE_CXX_STANDARD"] = 11
        cmake.definitions["OGRE_BUILD_TESTS"] = self.options.build_tests
        cmake.definitions["OGRE_ASSERT_MODE"] = self.options.assert_mode
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_BITES"
        ] = self.options.build_component_bites
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_HLMS"
        ] = self.options.build_component_hlms
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_MESHLODGENERATOR"
        ] = self.options.build_component_meshlodgenerator
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_OVERLAY"
        ] = self.options.build_component_overlay
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_PAGING"
        ] = self.options.build_component_paging
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_PROPERTY"
        ] = self.options.build_component_property
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_PYTHON"
        ] = self.options.build_component_python
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_RTSHADERSYSTEM"
        ] = self.options.build_component_rtshadersystem
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_TERRAIN"
        ] = self.options.build_component_terrain
        cmake.definitions[
            "OGRE_BUILD_COMPONENT_VOLUME"
        ] = self.options.build_component_volume
        cmake.definitions["OGRE_BUILD_DEPENDENCIES"] = False # Never let ogre build its own dependencies, this will cause linking errors
        cmake.definitions["OGRE_BUILD_PLUGIN_BSP"] = self.options.build_plugin_bsp
        cmake.definitions["OGRE_BUILD_PLUGIN_OCTREE"] = self.options.build_plugin_octree
        cmake.definitions["OGRE_BUILD_PLUGIN_PCZ"] = self.options.build_plugin_pcz
        cmake.definitions["OGRE_BUILD_PLUGIN_PFX"] = self.options.build_plugin_pfx
        cmake.definitions[
            "OGRE_BUILD_RENDERSYSTEM_D3D11"
        ] = self.options.build_rendersystem_d3d11
        cmake.definitions[
            "OGRE_BUILD_RENDERSYSTEM_GL"
        ] = self.options.build_rendersystem_gl
        cmake.definitions[
            "OGRE_BUILD_RENDERSYSTEM_GL3PLUS"
        ] = self.options.build_rendersystem_gl3plus
        cmake.definitions["OGRE_BUILD_SAMPLES"] = self.options.build_samples
        cmake.definitions["OGRE_BUILD_TOOLS"] = self.options.build_tools
        cmake.definitions[
            "OGRE_CONFIG_ENABLE_QUAD_BUFFER_STEREO"
        ] = self.options.config_enable_quad_buffer_stereo
        cmake.definitions[
            "OGRE_CONFIG_FILESYSTEM_UNICODE"
        ] = self.options.config_filesystem_unicode
        cmake.definitions["OGRE_CONFIG_THREADS"] = self.options.config_threads
        cmake.definitions[
            "OGRE_CONFIG_ENABLE_FREEIMAGE"
        ] = self.options.config_enable_freeimage
        cmake.definitions["OGRE_INSTALL_PDB"] = self.options.install_pdb
        cmake.definitions["OGRE_INSTALL_SAMPLES"] = self.options.install_samples
        cmake.definitions["OGRE_INSTALL_TOOLS"] = self.options.install_tools
        cmake.definitions[
            "OGRE_RESOURCEMANAGER_STRICT"
        ] = self.options.resourcemanager_strict
        cmake.definitions[
            "OGRE_NODELESS_POSITIONING"
        ] = self.options.nodeless_positioning
        if self.settings.os == "Windows":
            cmake.definitions["OGRE_INSTALL_VSPROPS"] = self.options.install_vsprops
        cmake.configure()
        return cmake

    def source(self):
        tools.get(
            **self.conan_data["sources"][self.version],
            destination=self._source_subfolder,
            strip_root=True,
        )


    @staticmethod
    def _gen_findpkg_shim(findpkg_file, org_pkg, shim_pkg):
        content = textwrap.dedent(
            """\
            include(Find{org})

            set({shim}_FOUND "${{{org}_FOUND}}" CACHE BOOL "Conan patch for {shim}" FORCE)
            set({shim}_LIBRARIES "${{{org}_LIBRARIES}}" CACHE STRING "Conan patch for {shim}" FORCE)
            set({shim}_INCLUDE_DIR "${{{org}_INCLUDE_DIR}}" CACHE STRING "Conan patch for {shim}" FORCE)
        """.format(
                org=org_pkg, shim=shim_pkg
            )
        )
        tools.save(findpkg_file, content)


    def _patch_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        ogre_pkg_modules = [
            "AMDQBS",
            "Cg",
            "HLSL2GLSL",
            "GLSLOptimizer",
            "OpenGLES",
            "OpenGLES2",
            "OpenGLES3",
            "SDL2",
            "Softimage",
            "Wix",
        ]
        ogre_pkg_module_path = os.path.join(
            self.build_folder, self._source_subfolder, "CMake", "Packages"
        )
        for pkg_module in ogre_pkg_modules:
            pkg_path = os.path.join(self.build_folder, f"Find{pkg_module}.cmake")
            if os.path.isfile(pkg_path):
                shutil.copy(pkg_path, ogre_pkg_module_path)
            else:
                raise ConanException(
                    f"The file Find{pkg_module}.cmake is not present in f{self.build_folder}!"
                )
        # Generate fake Findfreeimage to fix issues with ogre not finding freeimage
        self._gen_findpkg_shim(os.path.join(ogre_pkg_module_path, f"FindConanFreeImage.cmake"), "freeimage", "ConanFreeImage")

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy(
            pattern="License.md",
            dst="licenses",
            src=os.path.join(self._source_subfolder, "Docs"),
        )
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "share"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "OGRE", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "share"))
        self._create_cmake_module_variables(
            os.path.join(self.package_folder, self._module_file_rel_path),
            tools.Version(self.version),
        )

    @staticmethod
    def _create_cmake_module_variables(module_file, version):
        content = textwrap.dedent(
            """\
            set(OGRE_PREFIX_DIR ${{CMAKE_CURRENT_LIST_DIR}}/../..)
            set(OGRE{major}_VERSION_MAJOR {major})
            set(OGRE{major}_VERSION_MINOR {minor})
            set(OGRE{major}_VERSION_PATCH {patch})
            set(OGRE{major}_VERSION_STRING "{major}.{minor}.{patch}")

            set(OGRE_MEDIA_DIR "${{OGRE_PREFIX_DIR}}/share/OGRE/Media")
            set(OGRE_PLUGIN_DIR "${{OGRE_PREFIX_DIR}}/lib/OGRE")
            set(OGRE_CONFIG_DIR "${{OGRE_PREFIX_DIR}}/share/OGRE") 
        """.format(
                major=version.major, minor=version.minor, patch=version.patch
            )
        )
        tools.save(module_file, content)

    @property
    def _components(self):
        include_prefix = os.path.join("include", "OGRE")
        plugin_lib_dir = os.path.join("lib", "OGRE")
        components = {
            "OgreMain": {
                "requires": [
                    "boost::boost",
                    "cppunit::cppunit",
                    "freeimage::freeimage",
                    "openexr::openexr",
                    "freetype::freetype",
                    "sdl::sdl",
                    "tbb::tbb",
                    "xorg::xorg",
                    "zlib::zlib",
                    "zziplib::zziplib",
                    "poco::poco",
                    "glu::glu",
                    "egl::egl",
                ],
                "libs": ["OgreMain"],
                "include": [include_prefix],
                "libdirs": ["lib"],
            },
            "Bites": {
                "requires": ["OgreMain", "Overlay"],
                "libs": ["OgreBites"],
                "include": ["include", include_prefix, f"{include_prefix}/Bites"],
                "libdirs": ["lib"],
            },
            "HLMS": {
                "requires": ["OgreMain"],
                "libs": ["OgreHLMS"],
                "include": ["include", include_prefix, f"{include_prefix}/HLMS"],
                "libdirs": ["lib"],
            },
            "MeshLodGenerator": {
                "requires": ["OgreMain"],
                "libs": ["OgreMeshLodGenerator"],
                "include": [
                    "include",
                    include_prefix,
                    f"{include_prefix}/MeshLodGenerator",
                ],
                "libdirs": ["lib"],
            },
            "Overlay": {
                "requires": ["OgreMain"],
                "libs": ["OgreOverlay"],
                "include": ["include", include_prefix, f"{include_prefix}/Overlay"],
                "libdirs": ["lib"],
            },
            "Paging": {
                "requires": ["OgreMain"],
                "libs": ["OgrePaging"],
                "include": ["include", include_prefix, f"{include_prefix}/Paging"],
                "libdirs": ["lib"],
            },
            "Property": {
                "requires": ["OgreMain"],
                "libs": ["OgreProperty"],
                "include": ["include", include_prefix, f"{include_prefix}/Property"],
                "libdirs": ["lib"],
            },
            "RTShaderSystem": {
                "requires": ["OgreMain"],
                "libs": ["OgreRTShaderSystem"],
                "include": [
                    "include",
                    include_prefix,
                    f"{include_prefix}/RTShaderSystem",
                ],
                "libdirs": ["lib"],
            },
            "Terrain": {
                "requires": ["OgreMain"],
                "libs": ["OgreTerrain"],
                "include": ["include", include_prefix, f"{include_prefix}/Terrain"],
                "libdirs": ["lib"],
            },
            "Volume": {
                "requires": ["OgreMain"],
                "libs": ["OgreVolume"],
                "include": ["include", include_prefix, f"{include_prefix}/Volume"],
                "libdirs": ["lib"],
            },
        }

        if self.options.build_component_python:
            components["Python"] = {
                "requires": ["OgreMain"],
                "libs": ["OgrePython"],
                "include": ["include", include_prefix, f"{include_prefix}/Python"],
            }

        if self.options.build_plugin_bsp:
            components["BSPSceneManager"] = {
                "requires": ["OgreMain"],
                "libs": ["Plugin_BSPSceneManager"],
                "libdirs": ["lib", plugin_lib_dir],
                "include": [
                    "include",
                    include_prefix,
                    os.path.join(include_prefix, "Plugins", "BSPSceneManager"),
                ],
            }

        if self.options.build_plugin_octree:
            components["OctreeSceneManager"] = {
                "requires": ["OgreMain"],
                "libs": ["Plugin_OctreeSceneManager"],
                "libdirs": ["lib", plugin_lib_dir],
                "include": [
                    "include",
                    include_prefix,
                    os.path.join(include_prefix, "Plugins", "OctreeSceneManager"),
                ],
            }

        if self.options.build_plugin_pfx:
            components["ParticleFX"] = {
                "requires": ["OgreMain"],
                "libs": ["Plugin_ParticleFX"],
                "libdirs": ["lib", plugin_lib_dir],
                "include": [
                    "include",
                    include_prefix,
                    os.path.join(include_prefix, "Plugins", "ParticleFX"),
                ],
            }

        if self.options.build_plugin_pcz:
            components["PCZSceneManager"] = {
                "requires": ["OgreMain"],
                "libs": ["Plugin_PCZSceneManager"],
                "libdirs": ["lib", plugin_lib_dir],
                "include": [
                    "include",
                    include_prefix,
                    os.path.join(include_prefix, "Plugins", "PCZSceneManager"),
                ],
            }

            components["OctreeZone"] = {
                "requires": ["OgreMain", "PCZSceneManager"],
                "libs": ["Plugin_OctreeZone"],
                "libdirs": ["lib", plugin_lib_dir],
                "include": [
                    "include",
                    include_prefix,
                    os.path.join(include_prefix, "Plugins", "OctreeZone"),
                ],
            }

        if not self.options.shared:
            for _, values in components.items():
                libs = [lib + "Static" for lib in values.get("libs")]
                values["libs"] = libs

        if self.options.build_tests:
            components["OgreMain"]["requires"].append("cppunit::cppunit")

        if self.settings.build_type == "Debug":
            for _, values in components.items():
                libs = [lib + "_d" for lib in values.get("libs")]
                values["libs"] = libs

        return components

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "OGRE")
        self.cpp_info.names["cmake_find_package"] = "OGRE"
        self.cpp_info.names["cmake_find_package_multi"] = "OGRE"

        for comp, values in self._components.items():
            self.cpp_info.components[comp].names["cmake_find_package"] = comp
            self.cpp_info.components[comp].names["cmake_find_package_multi"] = comp
            self.cpp_info.components[comp].names["cmake_paths"] = comp
            self.cpp_info.components[comp].libs = values.get("libs")
            self.cpp_info.components[comp].libdirs = values.get("libdirs")
            self.cpp_info.components[comp].requires = values.get("requires")
            self.cpp_info.components[comp].set_property(
                "cmake_target_name", f"OGRE::{comp}"
            )
            self.cpp_info.components[comp].includedirs = values.get("include")

            self.cpp_info.components[comp].builddirs.append(self._module_file_rel_dir)
            self.cpp_info.components[comp].build_modules["cmake_find_package"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components[comp].build_modules["cmake_find_package_multi"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components[comp].build_modules["cmake_paths"] = [
                self._module_file_rel_path
            ]
            self.cpp_info.components[comp].builddirs.append(self._module_file_rel_path)
            if self.settings.os == "Linux":
                self.cpp_info.components[comp].system_libs.append("pthread")

        if self.options.install_tools:
            self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))

    @property
    def _module_file_rel_dir(self):
        return os.path.join("lib", "cmake")

    @property
    def _module_file_rel_path(self):
        return os.path.join(
            self._module_file_rel_dir, f"conan-official-{self.name}-variables.cmake"
        )
