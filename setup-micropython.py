"""pypi compatible setup module.

This setup is based on:
https://packaging.python.org/tutorials/distributing-packages/
and
http://docs.micropython.org/en/latest/wipy/reference/packages.html
"""
from setuptools import setup
from codecs import open
from os import path
import sdist_upip

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ev3devlight',
    version='0.1.2',
    description='Lightweight ev3dev Micropython and Python library.',
    long_description=long_description,
    url='https://github.com/laurensvalk/ev3devlight',
    author='Laurens Valk',
    author_email='laurensvalk@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='lego mindstorms ev3 micropython',
    cmdclass={'sdist': sdist_upip.sdist},
    packages=['ev3devlight'],
    project_urls={
        'Bug Reports': 'https://github.com/laurensvalk/ev3devlight/issues',
        'Questions': 'https://github.com/laurensvalk/ev3devlight/issues',
        'Examples': 'https://github.com/laurensvalk/ev3devlight-examples',
        'Source': 'https://github.com/laurensvalk/ev3devlight',
    }
    )
