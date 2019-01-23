import os
import platform
import xlrd
import time
from selenium import webdriver
from pathlib import Path
from itertools import zip_longest
from static_methods import get_download_folder

# remove downloads/result.xlsx if exists
path_char = '\\' if platform.system() == 'Windows' else '/'
downloaded_doc_file_path = get_download_folder()+path_char+"demo.doc"
if os.path.exists(downloaded_doc_file_path):
    os.remove(downloaded_doc_file_path)
downloaded_html_file_path = get_download_folder()+path_char+"demo.html"
if os.path.exists(downloaded_html_file_path):
    os.remove(downloaded_html_file_path)
downloaded_pdf_file_path = get_download_folder()+path_char+"demo.pdf"
if os.path.exists(downloaded_pdf_file_path):
    os.remove(downloaded_pdf_file_path)

# activity to choose two form files and submit the form, download file
defaultUrls = {
  "dev": 'http://localhost:8080',
  "production": 'http://ppp.pma2020.org/'
}

browser = webdriver.Chrome()
browser.get(defaultUrls["production"])

xform_file = str(Path("docs/demo.xlsx").resolve())
if platform.system() == 'Windows':
    xform_file = xform_file.replace("\\", "\\\\")

file_uploader = browser.find_element_by_id("inFile")
file_uploader.send_keys(xform_file)
button_submit = browser.find_element_by_id("btnSubmit")
button_submit.click()

while not os.path.exists(downloaded_result_file_path):
    time.sleep(1)
browser.close()

# compare two files
flag = False
with open(downloaded_result_file_path) as f1:
   with open(Path("docs/demo.doc").resolve()) as f2:
      if f1.read() == f2.read():
          flag = True

if flag:
    print('success!')
else:
    print('different!')