"""shotlooter setup."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name="shotlooter",
                 version="1.0.0",
                 author="utkusen",
                 description=("Monitor and analyze lightshot images."),
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url="https://github.com/utkusen/shotlooter",
                 packages=setuptools.find_packages(),
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "Operating System :: OS Independent",
                 ],
                 python_requires='>=3.7',
                 install_requires=[
                     "requests", "beautifulsoup4", "Pillow", "pytesseract",
                     "numpy", "imutils", "opencv-python-headless", "colorama",
                     "termcolor", "lxml"
                 ],
                 entry_points={
                     'console_scripts':
                     ['shotlooter=shotlooter.shotlooter:main'],
                 })
