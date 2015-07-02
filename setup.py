# -*- coding: utf-8 -*-
# 15/6/10
# create by: snower

import os
from setuptools import find_packages, setup


# Dynamically calculate the version based on django.VERSION.
version = __import__('forsun').version

if os.path.exists("README.md"):
    with open("README.md") as fp:
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
        'tornado>=4.1',
        'tornadoredis',
        'greenlet>=0.4.2',
    ],
    package_data={
    '': ['README.md'],
    },
    description= 'A high-level timing service',
    long_description= long_description,
)
