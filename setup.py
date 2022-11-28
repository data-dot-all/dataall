import setuptools

__pkg_name__ = 'data.all-core'
__version__ = '0.0.1'
__author__ = 'AWS Professional Services'

setuptools.setup(
    name=__pkg_name__,
    version=__version__,
    description='data.all common functions package',
    author=__author__,
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
)
