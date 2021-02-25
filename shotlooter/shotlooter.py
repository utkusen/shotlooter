'''
        ___
    .-``   ``-.
  .'           '.
 /               |   Utku Sen's
|      __ __      |   .-. .        .  .             .
'      /|_/|      '  (   )|       _|_ |            _|_
 |  ___|O_O/___  /    `-. |--. .-. |  |    .-.  .-. |  .-. .--.
  |/    ___    |/    (   )|  |(   )|  |   (   )(   )| (.-' |
  (    (___)    )     `-' '  `-`-' `-''---'`-'  `-' `-'`--''
   |   /|_/|   /             utkusen.com / twitter.com/utkusen
    |  |._.|  /
     | |   | /
      |/   |/
'''

import requests
from bs4 import BeautifulSoup
import string
import argparse as parser
from PIL import Image
import pytesseract
import re
import math
import os
import io
from signal import signal, SIGINT
import sys
import unicodedata
import numpy as np
import imutils
import cv2
import argparse
from os import listdir
from os.path import isfile, join
from colorama import init
from termcolor import colored


def handler(signal_received, frame):
    sys.exit(0)


headers = {
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    'accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'
}

code_chars = list(string.ascii_lowercase) + [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
]
base = len(code_chars)


# searches for a template(small image) in a image, returns True if found, False if not found
def template_match(fname_template, fname_image):
    template0 = cv2.imread(fname_template)
    template = cv2.cvtColor(template0, cv2.COLOR_BGR2GRAY)
    template = cv2.Canny(template, 50, 200)
    (tH, tW) = template.shape[:2]
    image = cv2.imread(fname_image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    found = None
    isFound = False
    for scale in np.linspace(0.2, 1.0, 20)[::-1]:
        resized = imutils.resize(gray, width=int(gray.shape[1] * scale))
        r = gray.shape[1] / float(resized.shape[1])
        if resized.shape[0] < tH or resized.shape[1] < tW:
            break
        edged = cv2.Canny(resized, 50, 200)
        result = cv2.matchTemplate(edged, template, cv2.TM_CCORR_NORMED)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
        if found is None or maxVal > found[0]:
            found0 = (maxVal, maxLoc, r)
            result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF_NORMED)
            (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
            (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
            (endX, endY) = (int((maxLoc[0] + tW) * r), int(
                (maxLoc[1] + tH) * r))
            img = image[startY:endY, startX:endX]
            height, width = template.shape[:2]
            img = cv2.resize(img, (width, height))
            img1, img2 = img, template0
            result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)
            if maxVal >= 0.48:
                found = (maxVal, maxLoc, r)
                isFound = True
                found = found0
    return isFound


# prnt.sc parser codes mostly borrowed from https://github.com/mitchelljy/Prntsc_Scraper
def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)


def str_base(number, base):
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)


def next_code(curr_code):
    curr_code_num = int(curr_code, base)
    return str_base(curr_code_num + 1, base)


def get_img(code):
    html = requests.get(f"https://prnt.sc/{code}", headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    img_url = soup.find_all('img',
                            {'class': 'no-click screenshot-image'})[0]['src']
    response = requests.get(img_url)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))


#https://github.com/joshleeb/creditcard/blob/master/creditcard/luhn.py
def get_check_digit(unchecked):
    digits = digits_of(unchecked)
    checksum = sum(even_digits(unchecked)) + sum(
        [sum(digits_of(2 * d)) for d in odd_digits(unchecked)])
    return 9 * checksum % 10


def is_valid_cc(number):
    if len(number) != 16:
        return False
    n = str(number)
    if not n.isdigit():
        return False
    return int(n[-1]) == get_check_digit(n[:-1])


def digits_of(number):
    return [int(d) for d in str(number)]


def even_digits(number):
    return list(map(int, str(number)[-2::-2]))


def odd_digits(number):
    return list(map(int, str(number)[-1::-2]))


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


def entropy(string):
    prob = [
        float(string.count(c)) / len(string)
        for c in dict.fromkeys(list(string))
    ]
    entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy


def keywords_analysis(keywords, image_text, code):
    match = False
    for word in keywords:
        # Append findings
        if word.lower() in image_text.lower():
            print(colored("Keyword Match: " + word, "green"))
            append_findings("keyword", word, code)
            match = True
    return match


def credit_card_analysis(image_words, code):
    numbers = re.compile('\d+(?:\.\d+)?')
    match = False
    for word in image_words:
        if hasNumbers(word):
            number = numbers.findall(word)
            if is_valid_cc(number[0]):
                print(colored("Credit Card Detected: " + number[0], "yellow"))
                append_findings("credit_card", number[0], code)
                match = True
    return match


def entropy_analysis(image_words, code):
    for word in image_words:
        if entropy(
                unicodedata.normalize('NFKD', word).encode(
                    'ascii', 'ignore').decode('utf-8')
        ) >= 4.5 and "http" not in word and "/" not in word and len(word) < 65:
            print(colored("High Entropy Detected: " + word, "magenta"))
            append_findings("entropy", word, code)
            return True
    return False


def image_analysis(imagedir, code):
    match = False
    files = [f for f in listdir(imagedir) if isfile(join(imagedir, f))]
    for file in files:
        if ".png" in file or ".jpg" in file:
            is_found = template_match(imagedir + "/" + file,
                                      os.getcwd() + "/output/" + code + ".png")
        if is_found:
            print(colored("Image Match Detected: " + file, 'cyan'))
            append_findings("image", file, code)
            match = True
    return match


def parse_args() -> argparse.Namespace:
    """Parse the CLI arguments of the program."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--code',
                        action='store',
                        dest='code',
                        help='Start code for prnt.sc.',
                        required=True)
    parser.add_argument('--imagedir',
                        action='store',
                        dest='imagedir',
                        help='Image directory for logo search.',
                        default=None)
    parser.add_argument('--no-entropy',
                        action='store_true',
                        dest='no_entropy',
                        help="Don't search for high entropy.",
                        default=False)
    parser.add_argument('--no-cc',
                        action='store_true',
                        dest='no_cc',
                        help="Don't search for credit card.",
                        default=False)
    parser.add_argument('--no-keyword',
                        action='store_true',
                        dest='no_keyword',
                        help="Don't search for keywords.",
                        default=False)
    parser.add_argument('--keywords_path',
                        action='store',
                        dest='keywords_path',
                        help='Keywords text file path.',
                        required=True)
    return parser.parse_args()


def append_findings(style: str, match: str, code: str):
    with open("findings.csv", "a+") as f:
        f.write(f"{style},{match},{code}")
        f.write("\n")


def action(code, imagedir, no_entropy, no_cc, no_keyword, keywords_path):
    with open(keywords_path, "r") as f:
        keywords = [
            keyword.lower()
            for keyword in open(keywords_path, "r").read().splitlines()
        ]
    while True:
        code = next_code(code)
        try:
            match = False
            image = get_img(code)
            print("Analyzing: " + code)
            image_text = pytesseract.image_to_string(image)
            image_words = image_text.split()

            # Keywords Analysis
            if not no_keyword:
                match = keywords_analysis(keywords, image_text, code)

            # Credit Cards Analysis
            if not no_cc:
                match = credit_card_analysis(image_words, code)
                if not no_entropy:
                    match = entropy_analysis(image_words, code)

            # Logo Analysis
            if imagedir is not None:
                match = image_analysis(imagedir, code)

            if match:
                image.save(os.getcwd() + "/output/" + code + ".png")
        except Exception as e:
            print(e)


def main():
    args = parse_args()
    action(args.code, args.imagedir, args.no_entropy, args.no_cc,
           args.no_keyword, args.keywords_path)
