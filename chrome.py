# -*- coding: utf-8 -*-
from sys import path as sysPath
from os import path as osPath
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import gc
import time
import random
import os
import shutil
import json
import requests
import time
import urllib
import base64
import json
import os
import time
import csv
import io
from urllib3.exceptions import InsecureRequestWarning
import gc
import time, os, warnings
# import BeautifulSoup
import threading
# 初始化檔案
import base as base1
import tkListBox

# 警告修正
warnings.simplefilter('ignore', InsecureRequestWarning)

options = driver = wait = None
bank_url = 'https://tj777.net/index.aspx'
account = 'ININ520'
password = 'inin1129'


# # 開啟網頁
def _open():
    global options, driver
    options = webdriver.ChromeOptions()
    is_wap = False

    if is_wap:
        mobileEmulation = {"deviceName": "iPhone 6 Plus"}
        options.add_experimental_option('mobileEmulation', mobileEmulation)

    prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': 'c:\\LongPay\\data'}
    options.add_experimental_option('prefs', prefs)
    # driver = webdriver.Chrome(executable_path='D:\\chromedriver.exe', chrome_options=options)
    options.add_argument('--log-level=3')
    options.add_argument('–no-sandbox')
    # options.add_argument('incognito')
    # options.add_argument('disable-extensions')
    options.add_argument('auto-open-devtools-for-tabs')
    driver = webdriver.Chrome(chrome_options=options, executable_path='file\\chromedriver.exe')
    driver.implicitly_wait(3)
    driver.get(bank_url)
    driver.maximize_window()

    exit()


# 單元測試
def _uTest(index):
    global options, driver, wait
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", '127.0.0.1:' + str(index))
    driver = webdriver.Chrome(chrome_options=options, executable_path='file\\chromedriver.exe')
    wait = WebDriverWait(driver, 1)
    driver.switch_to.default_content()


# -----------------------------------


# _open()
# _uTest(61412)
_aData = {
    'driver': driver,
    'wait': wait,
};
base = base1.Base()
base.setValue(_aData)


# -----------------------------------
# -----------------------------------


def do():
    print(u"do")
    _min = int(base.getTime("%M"))
    print(_min)
    if _min < 20:
        print('111')
    elif 20 < _min < 40:
        print('222')
    else:
        print('333')


# 放要執行的東西

try:
    print('----- start')
    do()
    print('----- end')
except Exception as e:
    print(e)
