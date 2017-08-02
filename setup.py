from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='discordbot.py',
    version='0.2.3.a3',
    description='A wrapper for discord.py with advanced functionality',
    long_description=long_description,
    url='https://github.com/rauenzi/discordbot.py',
    author='Zack Rauen',
    author_email='rauenzi@outlook.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    keywords='discord framework development',
    packages=find_packages(),
    install_requires=['discord.py', 'psutil'],
    python_requires=">=3.5",
    extras_require={
        'voice': ['discord.py[voice]']
    }
)
