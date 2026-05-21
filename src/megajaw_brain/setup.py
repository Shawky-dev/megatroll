from setuptools import find_packages, setup
from glob import glob
import os

package_name = "megajaw_brain"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "static", "best_ncnn_model"), glob("static/best_ncnn_model/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zeyadcode",
    maintainer_email="zeyadshapan2004@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "to_target_controller_node = megajaw_brain.to_target_controller_node:main",
            "detector_node = megajaw_brain.detector_node:main",
        ],
    },
)
