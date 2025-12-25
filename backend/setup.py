from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "altsky_cpp",
        ["cpp_src/lore_parser.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=["-std=c++11"],
    ),
]

setup(
    name="altsky_cpp",
    version="0.1",
    ext_modules=ext_modules,
)
