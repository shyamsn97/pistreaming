from setuptools import setup, find_packages

setup(
    name="pistreaming",
    package_data = {
        "static": ["*"]
    },
    entry_points={
        "console_scripts": ["yolov3 = yolov3.__main__:main"]
    },
)
