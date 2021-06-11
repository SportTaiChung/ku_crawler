# -*- coding: utf-8 -*-
import time
import json
import os
import winreg
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


# -*- coding: utf-8 -*-
class Base:
    # 建構式
    def __init__(self):
        self.driver = None
        self.wait = None
        self.page_load_timeout = "30"
        self.keyWinreg = r'Software\Being\LEO'

    # 設定公用變數
    def setValue(self, _aData):
        # noinspection PyBroadException
        try:
            for key in _aData:
                if key == "driver":
                    self.driver = _aData['driver']
                if key == "wait":
                    self.wait = _aData['wait']
                if key == "page_load_timeout":
                    self.page_load_timeout = _aData['page_load_timeout']
        except Exception:
            time.sleep(0.1)

    # 等待(秒)
    def sleep(self, sec):
        time.sleep(sec)

    # 等待元素出現
    def waitBy(self, _type, css, _fromWait=None):
        _wait = self.wait
        if _fromWait is not None:
            _wait = _fromWait
        by = By.CSS_SELECTOR
        if _type == "XPATH":
            by = By.XPATH
        elif _type == "ID":
            by = By.ID
        elif _type == "LINK_TEXT":
            by = By.LINK_TEXT
        return _wait.until(
            EC.presence_of_element_located((by, css))
        )

    # 送出鍵盤動作(非驅動輸入)
    def sendKey(self, browser, key):
        # noinspection PyBroadException
        try:
            actions = ActionChains(browser)
            if key == "TAB":
                actions.send_keys(Keys.TAB * 1)
            elif key == "ENTER":  # sendKey(dricer,"ENTER")
                actions.send_keys(Keys.ENTER)
            elif key == "RETURN":
                actions.send_keys(Keys.RETURN)
            elif key == "DOWN":
                actions.send_keys(Keys.DOWN)

            actions.perform()
        except Exception:
            time.sleep(0.1)

    # 回傳時間格式
    def getTime(self, _type, _time=None):
        # noinspection PyBroadException
        try:
            if _type == 'Ticks':
                return str(time.time())
            elif _type == 'Microseconds':
                return datetime.now().strftime("%H:%M:%S.%f")
            elif _type == 'localtime':
                return time.localtime(_time)  # 轉成時間元組
            # "%Y-%m-%d %H:%M:%S"
            # "%M:%S"
            # "%Y-%m-%d"
            return time.strftime(_type, time.localtime())
        except Exception:
            return False

    def json_decode(self, string):
        # noinspection PyBroadException
        try:
            return json.loads(string)
        except Exception:
            return False

    def json_encode(self, obj):
        # noinspection PyBroadException
        try:
            return json.dumps(obj)
        except Exception:
            return False

    def defaultDriverBase(self):
        # noinspection PyBroadException
        try:
            print(u'初始化瀏覽器')
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument('--log-level=3')
            options.add_argument('–no-sandbox')
            # options.add_argument('auto-open-devtools-for-tabs')

            self.driver = webdriver.Chrome(chrome_options=options, executable_path='file/chromedriver.exe')
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    })
                """
            })
            _sec = int(self.page_load_timeout)
            self.driver.implicitly_wait(_sec)
            self.driver.set_page_load_timeout(_sec)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, _sec)
        except Exception as e:
            print(u'初始化瀏覽器失敗')
            print(e)
            return False

    def defaultNewDriverBase(self, _driver):
        # noinspection PyBroadException
        try:
            print(_driver.capabilities['goog:chromeOptions']['debuggerAddress'])
            options = webdriver.ChromeOptions()
            options.add_experimental_option("debuggerAddress",
                                            _driver.capabilities['goog:chromeOptions']['debuggerAddress'])
            self.driver = webdriver.Chrome(chrome_options=options, executable_path='file/chromedriver.exe')
            _sec = int(self.page_load_timeout)
            self.wait = WebDriverWait(self.driver, _sec)
            return True
        except Exception:
            return False

    def log(self, file_name, _type, text, log_type):

        # noinspection PyBroadException
        try:
            if log_type == 'logs':
                return True
                path = 'logs'
                self.checkPath(path)
                _min = int(self.getTime("%M"))
                _log_min = '_40_60'
                print(_min)
                if _min < 20:
                    _log_min = '_00_20'
                elif 20 < _min < 40:
                    _log_min = '_20_40'
                txt_url = path + "\\" + file_name + "_" + self.getTime("%Y%m%d_%H") + _log_min + '.txt'
                f = open(txt_url, "a+")
                f.write(self.getTime("Microseconds") + '\n')
            elif log_type == 'mapping':
                path = 'mapping'
                self.checkPath(path)
                txt_url = path + "\\" + file_name + "_" + self.getTime("%Y%m%d") + '.txt'
                f = open(txt_url, "a+")
            elif log_type == 'switch':
                path = 'logs'
                self.checkPath(path)
                txt_url = path + "\\" + file_name + "_" + self.getTime("%Y%m%d") + '.txt'
                f = open(txt_url, "a+")
                f.write(self.getTime("Microseconds") + '\n')
            elif log_type == 'gameOpen':
                path = 'logs'
                self.checkPath(path)
                txt_url = path + "\\" + file_name + '.txt'
                f = open(txt_url, "w")

            if _type != '':
                f.write(_type + '\n')

            f.write(text + '\n')
            f.close()
        except Exception as e:
            print(e)
            time.sleep(0.1)

    def checkPath(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)

    def baseSoup(self, _html, _type):
        return BeautifulSoup(_html, _type)

    def getHtml(self, _css):
        ele_scroll = self.waitBy("CSS", _css)
        return ele_scroll.get_attribute('innerHTML')

    def setWinregKey(self, subKey, value):
        # noinspection PyBroadException
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyWinreg, 0, winreg.KEY_ALL_ACCESS)
        except Exception:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.keyWinreg)
        winreg.SetValueEx(key, subKey, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)

    def getWinregKey(self, subKey):

        return self.getWinregKeyByFile(subKey)
        # noinspection PyBroadException
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyWinreg, 0, winreg.KEY_ALL_ACCESS)
            value, _type = winreg.QueryValueEx(key, subKey)
        except Exception:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.keyWinreg)
            value = ""
        return str(value)

    def getWinregKeyByFile(self, subKey):
        _value = ""
        # noinspection PyBroadException
        try:
            txt_url = 'logs\\gameOpen.txt'
            f = open(txt_url, 'r')
            sGameOpen = f.read()
            f.close()
            oGameOpen = self.json_decode(sGameOpen)
            if subKey in oGameOpen['data']:
                _value = str(oGameOpen['data'][subKey])
        except Exception:
            time.sleep(0.01)
        return _value

    def resetWinregKeyValue(self):
        # noinspection PyBroadException
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.keyWinreg, 0, winreg.KEY_ALL_ACCESS)
            for key in range(3000):
                print(key)
                try:
                    show_sub_keys = winreg.EnumValue(reg_key, key)
                    winreg.SetValueEx(reg_key, show_sub_keys[0], 0, winreg.REG_SZ, '0')
                except Exception:
                    break
        except Exception:
            return False
        return True
