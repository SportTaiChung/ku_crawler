# -*- coding: utf-8 -*-

import os
import json
from google.protobuf import text_format
from upload import init_session, upload_data
from parsing import parse


class KuGame:
    # 建構式
    # globData, tkLabel, i_sport_type, title, btn, game
    def __init__(self, _globData, _tkBox, _tk_index, _i_sport_type, _i_oSport, _title, _btn, _game):
        print([_tk_index, _i_sport_type, _i_oSport, _title, _btn, _game])
        import base as base
        import ku_tools as tools
        self.base = base.Base()
        self.tools = tools
        self.globData = _globData  #
        self.tkBox = _tkBox  #
        self.tkIndex = _tk_index  #
        self.i_sport_type = str(_i_sport_type)  # 運動類型 足球 11 , 籃球 12 ... 參考 sport_type 說明
        self.i_oSport = _i_oSport  # list 裡面的index 0: 全場、1:滾球A
        self.title = _title  # 足球 , 籃球 ...
        self.btn = _btn  # 足球 btnSC , 籃球 btnBK ...
        self.game = _game  # {'title': u"今日-全場", 'gameIndex': 1}
        self.gameIndex = str(_game['gameIndex'])

        [connection, channel] = ["", ""]
        if self.globData['is_test'] != "TRUE":
            connection, channel = init_session('amqp://GTR:565p@rmq.nba1688.net:5673/')

        self.connection = connection
        self.channel = channel

    # globData['is_test']
    def start(self):
        # noinspection PyBroadException
        try:
            print(self.title + "_" + str(self.i_oSport) + "_start")
            self.base.defaultDriverBase()
            self.tools.openWeb(self.base, self.globData)
            self.odd()
        except Exception as e:
            print(self.title + "_" + str(self.i_oSport) + "_" + u'發生錯誤1')
            self.tkBox.updateLabel(self.tkIndex, u'發生錯誤1 : ' + self.base.getTime("Microseconds"))
            newNotice = self.base.json_encode({'data': e})
            self.base.log('error1', '-----', newNotice)
            self.base.sleep(0.1)
        self.base.sleep(5)
        self.base.driver.quit()
        self.base.sleep(5)
        if int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            self.start()
        else:
            self.tkBox.updateLabel(self.tkIndex, u'腳本已終止 ' + self.base.getTime("Microseconds"))

    def odd(self):
        try:
            print(u"導至遊戲")
            self.tkBox.updateLabel(self.tkIndex, u'導至遊戲 : ' + self.base.getTime("Microseconds"))
            self.base.driver.get(self.globData['ku_url_end'])
            self.base.sleep(3)

            if self.i_oSport == 0:
                print(u"全場")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeDS")
            else:
                print(u"滾球")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeZD")

            ele_btnPagemode.click()
            self.base.sleep(1)

            print(self.title)
            self.base.driver.implicitly_wait(1)
            while True:
                # noinspection PyBroadException
                try:
                    self.base.driver.find_element_by_xpath('//div[@id="' + self.btn + '"]')
                    self.base.driver.implicitly_wait(30)
                    ele_btnPage = self.base.waitBy("CSS", "#" + self.btn)
                    ele_btnPage.click()
                    self.base.sleep(1)
                    break
                except Exception:
                    self.tkBox.updateLabel(self.tkIndex, u'無列表選項、等待十秒後重試 : ' + self.base.getTime("Microseconds"))
                    print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds") + u" - 無列表選項、等待十秒後重試")
                    self.base.sleep(10)

            print(u"類型")
            self.base.driver.execute_script(
                "Menu.ChangeKGroup(this, '" + self.i_sport_type + "', " + self.gameIndex + ");")
            self.base.sleep(1)

            print(u"檢查有無資料")
            self.checkNoDate()

            print(u"抓取")
            oldHtml = self.base.getHtml("div.gameListAll_scroll")

            if self.i_oSport == 0:
                self.gameTime(oldHtml)
            else:
                self.gameOdds(oldHtml)
        except Exception as e:
            print(self.title + "_" + str(self.i_oSport) + "_" + u'發生錯誤2')
            self.tkBox.updateLabel(self.tkIndex, u'發生錯誤2 : ' + self.base.getTime("Microseconds"))
            newNotice = self.base.json_encode({'data': e})
            self.base.log('error2', '-----', newNotice)

    def gameTime(self, oldHtml):
        print(u'寫入比賽場次')
        if self.globData['is_test'] != "TRUE":
            data = {}
            if os.path.exists('event_time.json'):
                with open('event_time.json', encoding='utf-8') as f:
                    data = json.load(f)
            self.tkBox.updateLabel(self.loopIndex, u'寫入比賽場次 : ' + self.base.getTime("Microseconds"))
        oGameData = self.tools.getGameTime(self.base, oldHtml)

        if self.globData['is_test'] != "TRUE" and data:
            oGameData.update(data)
        for oGameKey in oGameData:
            print(oGameKey)
            self.base.log(self.title + "_gameTime", '',
                          oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), False)
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds"))
            self.tools.closeScroll(self.base.driver)
            newHtml = self.base.getHtml("div.gameListAll_scroll")
            oNewGameData = self.tools.getGameTime(self.base, newHtml)
            iChange = 0
            for oGameKey in oNewGameData:
                if oGameKey not in oGameData:
                    print(oGameKey)
                    iChange = iChange + 1
                    oGameData[oGameKey] = oNewGameData[oGameKey]
                    self.base.log(self.title + "_gameTime", '',
                                  oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), False)
            if iChange > 0:
                msg = u'新增場次(' + str(iChange) + ') : '
                self.tkBox.updateLabel(self.tkIndex, msg + self.base.getTime("Microseconds"))
            else:
                self.tkBox.updateLabel(self.tkIndex, u'無新增場次 : ' + self.base.getTime("Microseconds"))
            if self.globData['is_test'] != "TRUE":
                with open('event_time.json', mode='w', encoding='utf-8') as f:
                    json.dump(oGameData, f, ensure_ascii=False)

            self.base.sleep(0.1)

    def gameOdds(self, oldHtml):
        print(u'設定基本資料')
        self.tkBox.updateLabel(self.tkIndex, u'設定基本資料 : ' + self.base.getTime("Microseconds"))
        oldNotice = self.base.json_encode({'data': oldHtml})
        self.base.log(self.title + "_" + self.gameIndex, 'setBase', oldNotice)

        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            print(self.title + "_" + self.gameIndex + " - " + self.base.getTime("Microseconds"))
            self.tools.closeScroll(self.base.driver)
            newHtml = self.base.getHtml("div.gameListAll_scroll")

            if newHtml == "":
                self.checkNoDate()
                continue

            if oldHtml != newHtml:
                oldHtml = newHtml
                print(self.title + "_" + self.gameIndex + "_" + u'資料異動')
                self.tkBox.updateLabel(self.tkIndex, u'資料異動 : ' + self.base.getTime("Microseconds"))
                newNotice = self.base.json_encode({'data': newHtml})
                self.base.log(self.title + "_" + self.gameIndex, 'change', newNotice)
            else:
                self.tkBox.updateLabel(self.tkIndex, u'無變更 : ' + self.base.getTime("Microseconds"))

            if self.globData['is_test'] != "TRUE":
                data = parse(newHtml)
                upload_data(self.channel, data)
                print(text_format.MessageToString(data, as_utf8=True))
                # self.channel.close()
                # self.connection.close()

            self.base.sleep(0.1)

    def checkNoDate(self):
        self.base.driver.implicitly_wait(1)
        while True:
            # noinspection PyBroadException
            try:
                self.base.driver.find_element_by_xpath('//div[@class="gameList"]')
                self.base.sleep(0.1)
                self.base.driver.implicitly_wait(30)
                break
            except Exception:
                self.tkBox.updateLabel(self.tkIndex, u'無資料、等待一秒後重試 : ' + self.base.getTime("Microseconds"))
                print(self.gameIndex + " - " + self.base.getTime("Microseconds") + u" - 無資料、等待一秒後重試")
                self.base.sleep(1)
