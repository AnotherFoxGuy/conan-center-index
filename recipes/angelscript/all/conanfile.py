import os
from conan import ConanFile
from conan.tools.files import get, load, save, rmdir,copy
from conan.tools.cmake import CMakeToolchain, CMake,  cmake_layout

required_conan_version = ">=1.52.0"


class AngelScriptConan(ConanFile):
    name = "angelscript"
    license = "Zlib"
    homepage = "http://www.angelcode.com/angelscript"
    url = "https://github.com/conan-io/conan-center-index"
    description = (
        "An extremely flexible cross-platform scripting library designed to "
        "allow applications to extend their functionality through external scripts."
    )
    topics = ("angelcode", "embedded", "scripting", "language", "compiler", "interpreter")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [False, True],
        "fPIC": [False, True],
        "no_exceptions": [False, True],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "no_exceptions": False,
    }

    short_paths = True

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)

    def layout(self):
        cmake_layout(self)

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def source(self):
        # Website blocks default user agent string.
        get(self,
            **self.conan_data["sources"][self.version],
            destination=self.source_folder,
            headers={"User-Agent": "ConanCenter"},
            strip_root=True,
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["AS_NO_EXCEPTIONS"] = self.options.no_exceptions
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def _extract_license(self):
        header = load(self, os.path.join(self.package_folder, "include", "angelscript.h"))
        save(self, "LICENSE", header[header.find("/*", 1) + 3 : header.find("*/", 1)])

    def package(self):
        cmake = CMake(self)
        cmake.install()
        self._extract_license()
        copy(self, "LICENSE", self.build_folder, os.path.join(self.package_folder, "licenses"), keep_path=False)
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Angelscript")
        self.cpp_info.set_property("cmake_target_name", "Angelscript::angelscript")
        postfix = "d" if self._is_msvc and self.settings.build_type == "Debug" else ""
        # TODO: back to global scope in conan v2 once cmake_find_package* generators removed
        self.cpp_info.components["_angelscript"].libs = ["angelscript" + postfix]
        if self.settings.os in ("Linux", "FreeBSD", "SunOS"):
            self.cpp_info.components["_angelscript"].system_libs.append("pthread")

        # TODO: to remove in conan v2 once cmake_find_package* generators removed
        self.cpp_info.names["cmake_find_package"] = "Angelscript"
        self.cpp_info.names["cmake_find_package_multi"] = "Angelscript"
        self.cpp_info.components["_angelscript"].names["cmake_find_package"] = "angelscript"
        self.cpp_info.components["_angelscript"].names["cmake_find_package_multi"] = "angelscript"
        self.cpp_info.components["_angelscript"].set_property("cmake_target_name", "Angelscript::angelscript")
