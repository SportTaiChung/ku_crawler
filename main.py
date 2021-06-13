# -*- coding: utf-8 -*-
import yaml
import multiprocessing as mp
import base as base
import ku as game  # 開始遊戲流程 - 目前只有一個不做選項、直接調用
import tkLabel as tk
import ku_game_open
import ku_game
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
    'yaml_name': "sport_run",
}
oOpenList = {}
processList = []


# 設定帳號相關信息
def defaultData():
    global globData

    with open(config_name, 'r') as f:
        content_list = f.read().splitlines()

    for tContent in content_list:
        # print(tContent)
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
        elif tContentArr[0] == "sport_type":
            globData['sport_type'] = tContentArr[1]
        elif tContentArr[0] == "yaml_name":
            globData['yaml_name'] = tContentArr[1]
    globData['a_sport_type'] = globData['sport_type'].split(',')
    globData['timestamp_start'] = int(float(main_base.getTime('Ticks')))
    globData['timestamp_end'] = globData['timestamp_start'] + int(globData['time_close'])


# 登入
def doLogin():
    global globData
    print(globData)
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

    main_base.driver.get(globData['ku_url'])
    main_base.sleep(3)
    aCookies = main_base.driver.get_cookies()
    globData['aCookies'] = aCookies

    current_url = main_base.driver.current_url
    pos = current_url.find('bbview')  # 從字串開頭往後找

    globData['ku_url_start'] = current_url[0:pos] + 'bbview'
    globData['ku_url_end'] = current_url[0:pos] + 'bbview/Games.aspx'


# 設定場次資料
def setGame():
    global oOpenList
    with open(globData['yaml_name'] + '.yaml', 'r', encoding='utf8') as f:
        oSportList = yaml.load(f, Loader=yaml.FullLoader)

    oOpenList = {}
    oOpenList[0] = {'title': '監測場次開關', 'game': {'title': ''}, }
    tk_index = 1
    for i_sport_type in globData['a_sport_type']:
        if i_sport_type in oSportList:
            for i_oSport in oSportList[i_sport_type]['list']:
                tk_index = tk_index + 1
                oOpenList[tk_index] = {
                    'i_sport_type': i_sport_type,
                    'i_oSport': i_oSport,
                    'title': oSportList[i_sport_type]['title'],
                    'btn': oSportList[i_sport_type]['btn'],
                    'game': oSportList[i_sport_type]['list'][i_oSport],
                }


def startGame():
    global processList
    # 設定流程框
    # print(u"開啟流程框")
    tkLabel = None
   # if (globData['is_test'] == "TRUE"):
    #    tkLabel = tk.tkLabel(oOpenList, globData)
   #     p_tkLabel = mp.Process(target=tkLabel.start)
    #    processList.append(p_tkLabel)


    print(u"開啟比賽視窗")
    for oOpenKey in oOpenList:
        print(oOpenKey)
        oOpen = oOpenList[oOpenKey]
        print(oOpen)
        if oOpenKey == 0:  # 監測場次開啟關閉
            print(oOpen['title'])
            page = ku_game_open.kuGameOpen(globData, tkLabel, oOpenKey)
        else:
            print(oOpen['title'])
            page = ku_game.KuGame(globData, tkLabel, oOpenKey, oOpen['i_sport_type'], oOpen['i_oSport'], oOpen['title'],
                                  oOpen['btn'], oOpen['game'])
        p = mp.Process(target=page.start)
        processList.append(p)



# ------------------------
if __name__ == '__main__':
    main_base = base.Base()
    defaultData()
    doLogin()
    setGame()
    startGame()
    print(u'開始抓吧')
    print(len(processList))
    # 開始工作
    for p in processList:
        p.start()
        main_base.sleep(5)
    # main_base.driver.quit()
