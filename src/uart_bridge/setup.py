from setuptools import find_packages, setup

package_name = 'uart_bridge'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial'],  # ← pyserial here too
    zip_safe=True,
    maintainer='zeyadcode',
    maintainer_email='zeyadshapan2004@gmail.com',
    description='UART bridge between ROS2 /cmd_vel and STM32',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'uart_bridge_node = uart_bridge.uart_bridge_node:main',
        ],
    },
)
