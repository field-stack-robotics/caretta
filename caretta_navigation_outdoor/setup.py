from glob import glob

from setuptools import find_packages, setup

package_name = 'caretta_navigation_outdoor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Oguzhan Gurbuz',
    maintainer_email='oguzhan@fieldstackrobotics.com',
    description='Caretta outdoor navigation: dual-antenna RTK GPS heading, GPS localization, Nav2 without a map',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'dual_gps_heading = caretta_navigation_outdoor.dual_gps_heading:main',
            'gps_waypoints = caretta_navigation_outdoor.gps_waypoints:main',
        ],
    },
)
