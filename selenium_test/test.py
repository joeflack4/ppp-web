"""Selenium tests"""
import os
import platform
import sys
import time
import selenium.webdriver.chrome.service as service
from selenium import webdriver

# noinspection PyProtectedMember
from diff_pdf_visually import pdfdiff
from selenium.common.exceptions import WebDriverException

PROJECT_ROOT_DIR = \
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT_DIR)

from selenium_test.static_methods import get_download_folder

# activity to choose two form files and submit the form, download file
DEFAULT_URLS = {
  'dev': 'http://localhost:8080',
  'production': 'http://ppp.pma2020.org/'
}

try:
    browser = webdriver.Chrome()
except WebDriverException:
    this_dir_path = os.path.abspath(os.path.dirname(__file__))
    driver_path_end = \
        os.path.join('win32', 'chromedriver.exe') \
        if platform.system() == 'Windows' \
        else os.path.join('mac64', 'chromedriver') \
        if platform.system() == 'Darwin' \
        else os.path.join('linux64', 'chromedriver') \
        if platform.system() == 'Linux' \
        else ''
    chromedriver_path = \
        os.path.join(this_dir_path, 'bin', 'chrome_driver', driver_path_end)
    service = service.Service(chromedriver_path)
    service.start()
    # capabilities = {'chrome.binary': '/path/to/custom/chrome'}  # ?
    # driver = webdriver.Remote(service.service_url, capabilities) # ?
    # example usage
    # driver.get('http://www.google.com/xhtml')
    # time.sleep(5)
    # driver.quit()
    browser = webdriver.Chrome()

browser.get(DEFAULT_URLS['production'])


def compare_files(ext, download_file_path, filename):
    """Compare files

    Args:
        ext (str): file extension
        download_file_path (str): Path to download file
        filename (str): file name

    Returns:
        bool: True if no errors
    """
    flag = False
    base_file_path = os.path.join(PROJECT_ROOT_DIR, 'docs', filename)

    if ext == 'pdf':
        statinfo_downloaded_file = os.stat(download_file_path)
        statinfo_base_file = os.stat(base_file_path)
        flag = statinfo_downloaded_file.st_size == statinfo_base_file.st_size
    else:
        with open(download_file_path) as f1:
            with open(base_file_path) as f2:
                if f1.read() == f2.read():
                    flag = True

    print(ext + ' ' + 'success' if flag else 'different' + '!')

    return True


def main_shot(btn_name: str, ext: str):
    """Main shot

        This function is repeatable cycle for 3 types of conversion - remove existing downloaded file, 
            uploading file, choosing type of conversion, submit button, downloading, comparing

    Args:
        btn_name (str): the element id for toggling button - type of conversion (doc, html, pdf)
        ext (str): file extension

    Returns:
        bool: True if no errors
    """

    filename_base = 'demo'
    filename = filename_base + '.' + ext

    download_file_path = os.path.join(get_download_folder(), filename)

    if os.path.exists(download_file_path):
        os.remove(download_file_path)

    btn_html_format = browser.find_element_by_id(btn_name)
    btn_html_format.click()

    xform_file = \
        os.path.join(PROJECT_ROOT_DIR, 'docs', filename_base + '.xlsx')

    file_uploader = browser.find_element_by_id('inFile')
    file_uploader.send_keys(xform_file)
    
    button_submit = browser.find_element_by_id('btnSubmit')
    button_submit.click()

    while not os.path.exists(download_file_path):
        time.sleep(1)

    return compare_files(ext, download_file_path, filename)


task1 = main_shot('btnDocFormat', 'doc')
while not task1:
    time.sleep(1)
time.sleep(2)

task2 = main_shot('btnHtmlFormat', 'html')
while not task2:
    time.sleep(1)
time.sleep(2)

task3 = main_shot('btnPdfFormat', 'pdf')
while not task3:
    time.sleep(1)
time.sleep(2)


browser.close()
