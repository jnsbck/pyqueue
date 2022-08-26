from setuptools import setup, find_packages 

with open("README.md") as fh:
    long_description = fh.read()

setup(
    name="pyqueue",
    version="0.1.1",
    author="Jonas Beck",
    author_email="jonas.beck@uni-tuebingen.de",
    description="A simple and lightweight task queue and job scheduler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jnsbck/pyqueue",
    license="GPLv3", # TO BE DETERMINED
    packages=find_packages("pyqueue"),
    package_dir = {"": "pyqueue"},
    zip_safe=False,
    install_requires=["psutil"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        'console_scripts': [
            'pyqueue=main.__main__:main',
        ],
    }
)