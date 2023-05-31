from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("GIRR.py"),
    name="GIRR"
)
"""
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
ext_modules = [
    Extension("GIRR",  ["GIRR.py"]),
]

setup(
    name = 'My Program',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)
"""