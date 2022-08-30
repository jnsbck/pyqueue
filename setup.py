# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

from setuptools import setup, find_packages 

with open("README.md") as fh:
    long_description = fh.read()

setup(
    name="pyqueue",
    version="0.01",
    author="Jonas Beck",
    author_email="jonas.beck@uni-tuebingen.de",
    description="A simple and lightweight task queue and job scheduler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jnsbck/pyqueue",
    # license="GPLv3", # TO BE DETERMINED
    packages=find_packages(where="pyqueue"),
    zip_safe=False,
    install_requires=["psutil", "black", "isort"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        'console_scripts': [
            'pyqueue=main:main',
        ],
    }
)
