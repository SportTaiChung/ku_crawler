# -*- coding: utf-8 -*-

import threading
import ku_game
import ku_game_open
import yaml
import tkLabel as tk
import base as main_base

globData = None


def start(_base, _globData):
    global globData, main_base
    main_base = _base
    globData = _globData

    main_base.driver.get(globData['ku_url'])
    main_base.sleep(3)
    aCookies = main_base.driver.get_cookies()
    globData['aCookies'] = aCookies

    current_url = main_base.driver.current_url
    pos = current_url.find('bbview')  # 從字串開頭往後找

    globData['ku_url_start'] = current_url[0:pos] + 'bbview'
    globData['ku_url_end'] = current_url[0:pos] + 'bbview/Games.aspx'
    begin(globData['yaml_name'])


def begin(yaml_name):
    # 多線程來執行各類運動
    oSportList = {}
    with open(yaml_name+'.yaml', 'r', encoding='utf8') as f:
        oSportList = yaml.load(f, Loader=yaml.FullLoader)

    oOpenList = {}
    oOpenList[0] = {'title': '監測場次開關','game': {'title': ''},}
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
    # print(oOpenList)
    print(u"開啟流程框")
    # tkLabel = tk.tkLabel(oOpenList, globData)
    # thread_tk = threading.Timer(1.0, tkLabel.start, args=[])
    # thread_tk.start()
    main_base.sleep(5)

    print(u"開啟比賽視窗")
    for oOpenKey in oOpenList:
        oOpen = oOpenList[oOpenKey]
        if oOpenKey == 0:  # 監測場次開啟關閉
            print(oOpen['title'])
            page = ku_game_open.kuGameOpen(globData, tkLabel, oOpenKey)
        else:
            print(oOpen['title'])
            page = ku_game.KuGame(globData, tkLabel, oOpenKey, oOpen['i_sport_type'], oOpen['i_oSport'], oOpen['title'],
                                  oOpen['btn'], oOpen['game'])
        thread1 = threading.Timer(1.0, page.start, args=[])
        thread1.start()
        main_base.sleep(20)

    main_base.driver.quit()
