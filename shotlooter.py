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
import argparse
from PIL import Image
import pytesseract
import re
import math
import os
import sys
import unicodedata
import numpy as np
import imutils
import cv2
from os import listdir
from os.path import isfile, join
from colorama import init
from termcolor import colored
from signal import signal, SIGINT
import time
import random

init()

def handler(signal_received, frame):
    sys.exit(0)


# Create a session object to maintain cookies
session = requests.Session()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Cache-Control': 'max-age=0',
}


code_chars = list(string.ascii_lowercase) + ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
base = len(code_chars)


# searches for a template(small image) in a image, returns True if found, False if not found
def template_match(fname_template: str, fname_image: str) -> bool:
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
            (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
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
def digit_to_char(digit: int) -> str:
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number: int, base: int) -> str:
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)

def next_code(curr_code: str) -> str:
    curr_code_num = int(curr_code, base)
    return str_base(curr_code_num + 1, base)

def get_img_url(code: str) -> str:
    # Add a small random delay before each request
    time.sleep(random.uniform(1, 3))
    
    url = f"https://prnt.sc/{code}"
    try:
        # Use session instead of requests directly
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'lxml')
        img_url = soup.find_all('img', {'class': 'no-click screenshot-image'})
        if not img_url:
            print(f"No image found for code: {code}")
            return None
            
        url = img_url[0]['src']
        if url.startswith('//'):
            url = 'https:' + url
        return url
    except Exception as e:
        print(f"Error getting image URL: {e}")
        return None

def get_img(url: str, path: str) -> bool:
    if not url:
        return False
        
    try:
        # Use session for image download too
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(f"{path}.png", 'wb') as f:
                f.write(response.content)
            return True
        return False
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return False

#https://github.com/joshleeb/creditcard/blob/master/creditcard/luhn.py
def get_check_digit(unchecked):
    digits = digits_of(unchecked)
    checksum = sum(even_digits(unchecked)) + sum([
        sum(digits_of(2 * d)) for d in odd_digits(unchecked)])
    return 9 * checksum % 10

def is_valid_cc(number: str) -> bool:
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

def hasNumbers(inputString: str) -> bool:
    return any(char.isdigit() for char in inputString)

def entropy(string: str) -> float:
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
    return entropy


def action(
    code: str,
    imagedir: str | None,
    no_entropy: bool,
    no_cc: bool,
    no_keyword: bool,
    delay: float
) -> None:
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create findings.csv in the output directory if it doesn't exist
    findings_file = os.path.join(output_dir, "findings.csv")
    if not os.path.exists(findings_file):
        with open(findings_file, "w") as f:
            f.write("type,value,code\n")
    
    numbers = re.compile(r'\d+(?:\.\d+)?')
    
    # Use context manager for file operations
    with open("keywords.txt", "r", encoding='utf-8') as f:
        keywords = [line.rstrip().lower() for line in f if line.rstrip()]
    
    while True:
        code = next_code(code)
        try:
            flag = False
            img_path = os.path.join(output_dir, code)
            url = get_img_url(code)
            print("Extracted URL:", url)
            success = get_img(url, img_path)
            
            if not success:
                print(f"Failed to download image for code: {code}")
                
                if delay > 0:
                    print(f"Waiting {delay} seconds before next request...")
                    time.sleep(delay)
                continue
                
            print(f"Analyzing: {code}")
            
            # Check if image file exists before processing
            img_file = f"{img_path}.png"
            if not os.path.exists(img_file):
                print(f"Failed to download image for code: {code}")
                continue
                
            image_text = pytesseract.image_to_string(Image.open(img_file))
            if no_keyword is None:
                for word in keywords:
                    if word.lower() in image_text.lower():
                        print(colored(f"Keyword Match: {word}", "green"))
                        with open(findings_file, "a") as f:
                            f.write(f"keyword,{word},{code}\n")
                        flag = True
            
            image_words = image_text.split()
            for word in image_words:
                if no_cc is None:
                    if hasNumbers(word):
                        number = numbers.findall(word)
                        if number and is_valid_cc(number[0]):
                            print(colored(f"Credit Card Detected: {number[0]}", "yellow"))
                            with open(findings_file, "a") as f:
                                f.write(f"credit_card,{number[0]},{code}\n")
                            flag = True
                if no_entropy is None:
                    if entropy(unicodedata.normalize('NFKD', word).encode('ascii','ignore').decode('utf-8')) >= 4.5 and "http" not in word and "/" not in word and len(word) < 65:
                        print(colored(f"High Entropy Detected: {word}", "magenta"))
                        with open(findings_file, "a") as f:
                            f.write(f"entropy,{word},{code}\n")
                        flag = True
            
            if not flag:
                if os.path.exists(img_file):
                    os.remove(img_file)
        except Exception as e:
            print(e)

signal(SIGINT, handler)

parser = argparse.ArgumentParser()
parser.add_argument('--code', action='store', dest='code', help='Start code for prnt.sc', required=True)
parser.add_argument('--imagedir', action='store', dest='imagedir', help='Image directory for logo search', default=None)
parser.add_argument('--no-entropy', action='store_true', dest='no_entropy', help="Don't search for high entropy", default=None)
parser.add_argument('--no-cc', action='store_true', dest='no_cc', help="Don't search for credit card", default=None)
parser.add_argument('--no-keyword', action='store_true', dest='no_keyword', help="Don't search for keywords", default=None)
parser.add_argument('--delay', action='store', dest='delay', help='Delay between requests in seconds', type=float, default=10.0)
argv = parser.parse_args()

if argv.no_entropy:
    argv.no_entropy = True
if argv.no_cc:
    argv.no_cc = True
if argv.no_keyword:
    argv.no_keyword = True

action(argv.code, argv.imagedir, argv.no_entropy, argv.no_cc, argv.no_keyword, argv.delay)
