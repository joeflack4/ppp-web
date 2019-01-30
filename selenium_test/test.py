import os
import platform
import xlrd
import time
from selenium import webdriver
from pathlib import Path
from itertools import zip_longest
from static_methods import get_download_folder
from diff_pdf_visually import pdfdiff
import sys

# activity to choose two form files and submit the form, download file
defaultUrls = {
  "dev": 'http://localhost:8080',
  "production": 'http://ppp.pma2020.org/'
}

browser = webdriver.Chrome()
browser.get(defaultUrls["production"])

def mainShot(btnName, ext):
    global browser
    path_char = '\\' if platform.system() == 'Windows' else '/'
    download_file_path = get_download_folder()+path_char+"demo."+ext
    if os.path.exists(download_file_path):
        os.remove(download_file_path)

    btnHtmlFormat = browser.find_element_by_id(btnName)
    btnHtmlFormat.click()

    xform_file = str(Path("docs/demo.xlsx").resolve())
    if platform.system() == 'Windows':
        xform_file = xform_file.replace("\\", "\\\\")

    file_uploader = browser.find_element_by_id("inFile")
    file_uploader.send_keys(xform_file)
    
    button_submit = browser.find_element_by_id("btnSubmit")
    button_submit.click()

    while not os.path.exists(download_file_path):
        time.sleep(1)

    # compare two files
    flag = False
    if ext == "pdf":
        print(download_file_path)
        print(Path("docs/demo."+ext).resolve())

        flag = pdfdiff(download_file_path, Path("docs/demo."+ext).resolve())
    else:
        with open(download_file_path) as f1:
            with open(Path("docs/demo."+ext).resolve()) as f2:
                if f1.read() == f2.read():
                    flag = True
    if flag:
        print(ext + ' success!')
    else:
        print(ext + ' different!')

    return True


task1 = mainShot("btnDocFormat", "doc")
while not task1:
    time.sleep(1)
time.sleep(2)

task2 = mainShot("btnHtmlFormat", "html")
while not task2:
    time.sleep(1)
time.sleep(2)

task3 = mainShot("btnPdfFormat", "pdf")
while not task3:
    time.sleep(1)
time.sleep(2)


browser.close()