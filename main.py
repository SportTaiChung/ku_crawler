# -*- coding: utf-8 -*-
import base as base
# 警告修正
from warnings import simplefilter
from urllib3.exceptions import InsecureRequestWarning

simplefilter('ignore', InsecureRequestWarning)
config_name = "config.ini"
globData = {
    'url': "",
    'ku_url': "",
    'account': "",
    'password': "",
    'page_index': '',
    'time_close': 8 * 60 * 60,  # 秒(8H)
    'is_test': 'False',
}


# 設定帳號相關信息
def defaultData():
    global globData

    with open(config_name, 'r') as f:
        content_list = f.read().splitlines()

    for tContent in content_list:
        tContentArr = tContent.split('|')
        if tContentArr[0] == "account":
            globData['account'] = tContentArr[1]
        elif tContentArr[0] == "password":
            globData['password'] = tContentArr[1]
        elif tContentArr[0] == "url":
            globData['url'] = tContentArr[1]
        elif tContentArr[0] == "ku_url":
            globData['ku_url'] = tContentArr[1]
        elif tContentArr[0] == "time_close":
            globData['time_close'] = tContentArr[1]
        elif tContentArr[0] == "is_test":
            globData['is_test'] = tContentArr[1]

    # account = input(u'login account: ')
    # password = input(u'login password: ')
    # page_index = input(u'page_index: ')

    # python 2 要用 raw_input
    # account = "KIEY093001"
    # password = "Qq123456"


defaultData()
main_base = base.Base()
main_base.defaultDriverBase()
print(u"網址:" + globData['url'])
main_base.driver.get(globData['url'])
main_base.sleep(3)

print(u"帳號:" + globData['account'])
ele_account = main_base.waitBy("CSS", "#txtUser")
ele_account.send_keys(globData['account'])
main_base.sleep(0.5)

print(u"密碼:" + globData['password'])
ele_password = main_base.waitBy("CSS", "#txtPassword")
ele_password.send_keys(globData['password'])
main_base.sleep(0.5)

print(u"登入")
main_base.driver.execute_script("UserPassIsEmpty();")
main_base.sleep(5)

# 開始遊戲流程 - 目前只有一個不做選項、直接調用

import ku as game

globData['timestamp_start'] = int(float(main_base.getTime('Ticks')))
globData['timestamp_end'] = globData['timestamp_start'] + int(globData['time_close'])
game.start(main_base, globData)
