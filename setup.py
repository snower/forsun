# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import os
from setuptools import find_packages, setup

version = "0.0.4"

if os.path.exists("README.rst"):
    with open("README.rst") as fp:
        long_description = fp.read()
else:
    long_description = ''

setup(
    name='forsun',
    version=version,
    url='https://github.com/snower/forsun',
    author='snower',
    author_email='sujian199@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        'tornado>=5.0',
        'thrift==0.11.0',
        'torthrift>=0.2.4',
        'tornadis>=0.8.0',
        'greenlet>=0.4.2',
        'msgpack>=0.5.1',
        'pytz>=2017.3',
        'tzlocal>=1.5.1',
    ],
    extras_require = {
        'mysql': ['tormysql>=0.3.7'],
        'beanstalk': ['beanstalkt>=0.7.0'],
    },
    package_data={
        '': ['README.md'],
    },
    entry_points={
        'console_scripts': [
            'forsun = forsun.scripts.forsun:main',
            'forsund = forsun.scripts.forsund:main',
        ],
    },
    description= 'High-performance high-precision timing scheduling service',
    long_description= long_description,
)
