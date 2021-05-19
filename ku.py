# -*- coding: utf-8 -*-

import threading
import ku_sc
import tkLabel as tk

main_base = None
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
    begin()


def begin():
    # 多線程來執行各類運動
    # 收藏夾 btnFV
    # 即將開賽 btnCS
    # 轉播賽事 btnTV
    # 冠軍聯賽 btnCH
    # 棒球 btnBB
    # 網球 btnTN
    # 冰球 btnIH
    # 排球 btnVL
    # 手球 btnHB
    # 電子 btnES
    print(u"足球 btnSC")
    oBtnSC = {
        1: {'title': u"全　場", 'gameIndex': 1},
        2: {'title': u"角　球", 'gameIndex': 2},
        3: {'title': u"十五分", 'gameIndex': 7},
        4: {'title': u"波　膽", 'gameIndex': 4},
        5: {'title': u"入球數", 'gameIndex': 5},
        6: {'title': u"半全場", 'gameIndex': 6},
    }

    print(u"開啟流程框")
    tkLabel = tk.tkLabel(oBtnSC, globData)
    thread_tk = threading.Timer(1.0, tkLabel.start, args=[])
    thread_tk.start()
    main_base.sleep(1)

    for oBtnSCKey in oBtnSC:
        print(oBtnSC[oBtnSCKey]['title'])
        sc1 = ku_sc.KuSc(globData, tkLabel, oBtnSCKey, oBtnSC[oBtnSCKey]['gameIndex'])
        thread_sc1 = threading.Timer(1.0, sc1.start, args=[])
        thread_sc1.start()
        main_base.sleep(20)

    main_base.driver.quit()
