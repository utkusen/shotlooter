## Introduction

Shotlooter tool is developed to find sensitive data inside the screenshots which are uploaded to https://prnt.sc/ (via the LightShot software) by applying OCR and image processing methods.

```
                                                              +-------------------+
    IMAGE FILE                                                |#!/usr/bin/python  |
+--------------------+                                        |                   +----->SENSITIVE
|prnt.sc/sjgmm5      |                                        |Search for:        |
+--------------------+                                        |                   |
|      _             |      CONVERTS          STRING          |sensitive keywords |
|  .-.-.=\-          |      +-------+     +------------+      |                   |
|  (_)=='(_)         |      |       |     |            |      |high entropy       |
|              .._\  +----->+  OCR  +---->+ TEXTTEXTT  +----->+                   |
|             (o)(o) |      |       |     |            |      |credit card pattern+----->NOT SENSITIVE
|   TEXTTEXTTEX      |      +-------+     +------------+      |                   |
|                    |                                        +-------------------+
+--------------+------+
               |                 +-----------------------+
               v                 |#!/usr/bin/python      |
SMALLER         IMAGES           |                       +------>SENSITIVE
+-------------+ +------------+   |Image processing:      |
|    _        | |    .._\    |   |                       |
| .-.-.=\-    | |   (o)(o)   +-->+ Does it contain:      |
| (_)=='(_)   | |            |   |   ~~O                 |
+-------------+ +------------+   |    /\,                |
                                 |   -|~(*)              +------>NOT SENSITIVE
                                 |  (*)                  |
                                 +-----------------------+

```

## How it Works?

1) Starting from given image id, Shotlooter iterates through images (yes, image ids are not random) and downloads them locally.
2) Converts the text inside the image by using tesseract OCR library.
3) Searches for predefined keywords on the image
4) Searches strings with high entropy (API keys usually have high entropy)
5) Searches small images (e.g Lastpass logo) inside the downloaded image (Template Matching) with OpenCV.
6) Saves the results to a CSV file
7) Saves images that contain sensitive data to the `output` folder

## Installation

Shotlooter requires Python3, pip3 to work and tested on macOS and Debian based Linux systems. 

**Installing Dependencies for macOS:** `brew install tesseract`

**Installing Dependencies for Debian Based Linux:** `sudo apt install libsm6 libxext6 libxrender-dev tesseract-ocr -y`

Clone the repository:

`git clone https://github.com/utkusen/shotlooter.git`

Go inside the folder

`cd shotlooter`

Install required libraries

`pip3 install -r requirements.txt`

## Usage

**Basic Usage:** `python3 shotlooter.py --code PRNT.SC_ID` 

It searches for matching keywords (located in `keywords.txt`), high entropy strings and credit card numbers. You can find an id by uploading an image to https://prnt.sc/ . For example `python3 shotlooter.py --code sjgmm5` 

It will check the ids by incrementing them one by one:

```
sjgmm6
sjgmm7
sjgmm8
sjgmm9
sjgmma
sjgmmb
...
```

**Image Search:** `python3 shotlooter.py --code sjgmm5 --imagedir IMAGE_FOLDER_PATH` 

It will search for the items covered in basic usage + will search for provided small images in the bigger screenshots. If you are planning to use this feature, put your small images inside the `img` folder.

**Exclude Search:** You can exclude any search type by providing related argument: `--no-cc`, `--no-entropy`, `--no-keyword` 

For example: `python3 shotlooter.py --code sjgmm5 --no-entropy`. Shotlooter will skip high entropy string checking.

### A Note For The False Positives

Shotlooter has high false-positive rates for high entropy string and credit card matching. Actually, they are not false positives but may not be the items that you are looking for. It detects high entropy strings to catch API keys, private keys etc. However, any non-sensitive random string will have a high entropy too and Shotlooter will detect them. The same goes for the credit card. 

If you don't want to deal with false positives, exclude entropy and credit card searches.
