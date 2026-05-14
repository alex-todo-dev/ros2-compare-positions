import os
from setuptools import setup
from glob import glob

package_name = 'approach_a'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),       glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),       glob('config/*')),
        (os.path.join('share', package_name, 'urdf'),         glob('urdf/*')),
        (os.path.join('share', package_name, 'worlds'),       glob('worlds/*')),
        (os.path.join('share', package_name, 'models/cube'),  glob('models/cube/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='alexander',
    maintainer_email='alex.st.todorov@gmail.com',
    description='Pick-and-place using hardcoded joint angles — Approach A',
    license='BSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pick_place    = approach_a.pick_place:main',
            'set_home_pose = approach_a.set_home_pose:main',
        ],
    },
)
