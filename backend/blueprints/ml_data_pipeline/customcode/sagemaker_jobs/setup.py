from setuptools import find_packages, setup

install_requires = [
    'boto3>=1.13.24',
    'botocore',
    'numpy',
    'pandas',
    'scikit-learn',
    'matplotlib',
    'hyperopt',
]

dev_requires = [
    'autopep8',
    'pytest',
    'pytest-cov',
    'pytest-mock',
    'pytest-timeout',
    'twine',
    'coverage-badge',
    'semver',
    'flake8',
    'pylint',
    'moto',
]
setup(
    name='sagemaker_jobs',
    version='0.1.0',
    description='SageMaker Jobs Package',
    author='Author',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    include_package_data=True,
    extras_require={'dev': dev_requires},
)
