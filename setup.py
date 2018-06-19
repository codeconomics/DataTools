from setuptools import setup, find_packages

setup(
    name='padar_extra',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    description='Extension scripts to process and visualize accelerometer data for padar package',
    long_description=open('README.md').read(),
    install_requires=[
        "pandas",
        "numpy",
        "plotly"
    ],
)