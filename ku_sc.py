# -*- coding: utf-8 -*-
import os
import traceback
import json
from google.protobuf import text_format
from upload import init_session, upload_data
from parsing import parse
class KuSc:
    # 建構式
    def __init__(self, _globData, _tkBox, _loopIndex, _gameIndex):
        import base as base
        import ku_tools as tools
        self.base = base.Base()
        self.tools = tools
        self.gameName = "SC"
        self.globData = _globData
        self.tkBox = _tkBox
        self.loopIndex = _loopIndex
        self.gameIndex = str(_gameIndex)
        connection, channel = init_session('amqp://GTR:565p@rmq.nba1688.net:5673/')
        self.connection = connection
        self.channel = channel

    def start(self):
        # noinspection PyBroadException
        try:
            self.base.defaultDriverBase()
            self.tools.openWeb(self.base, self.globData)
            self.odd()
        except Exception as e:
            print(self.gameName + "_" + u'發生錯誤1')
            self.tkBox.updateLabel(self.loopIndex, u'發生錯誤1 : ' + self.base.getTime("Microseconds"))
            newNotice = self.base.json_encode({'data': e})
            self.base.log('error1', '-----', newNotice)
            self.base.sleep(0.1)
        self.base.sleep(5)
        self.base.driver.quit()
        self.base.sleep(5)
        if int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            self.start()
        else:
            self.tkBox.updateLabel(self.loopIndex, u'腳本已終止 ' + self.base.getTime("Microseconds"))

    def odd(self):
        try:
            print(u"導至遊戲")
            self.tkBox.updateLabel(self.loopIndex, u'導至遊戲 : ' + self.base.getTime("Microseconds"))
            self.base.driver.get(self.globData['ku_url_end'])
            self.base.sleep(3)

            if self.loopIndex == 0:
                print(u"全場")
                ele_btnSCmode = self.base.waitBy("CSS", "#modeDS")
            else:
                print(u"滾球")
                ele_btnSCmode = self.base.waitBy("CSS", "#modeZD")

            ele_btnSCmode.click()
            self.base.sleep(1)

            print(u"足球")
            ele_btnSC = self.base.waitBy("CSS", "#btnSC")
            ele_btnSC.click()
            self.base.sleep(1)

            print(u"類型")
            self.base.driver.execute_script("Menu.ChangeKGroup(this, '11', " + self.gameIndex + ");")
            self.base.sleep(1)

            print(u"檢查有無資料")
            self.checkNoDate()

            print(u"抓取")
            oldHtml = self.base.getHtml("div.gameListAll_scroll")

            if self.loopIndex == 0:
                self.gameTime(oldHtml)
            else:
                self.gameOdds(oldHtml)
            print(u'設定基本資料')
            self.tkBox.updateLabel(self.loopIndex, u'設定基本資料 : ' + self.base.getTime("Microseconds"))
            oldNotice = self.base.json_encode({'data': oldHtml})
            self.base.log(self.gameName + "_" + self.gameIndex, 'setBase', oldNotice)

            while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
                print(self.gameIndex + " - " + self.base.getTime("Microseconds"))
                self.tools.closeScroll(self.base.driver)
                newHtml = self.base.getHtml("div.gameListAll_scroll")

                if newHtml == "":
                    self.checkNoDate()
                    continue

                if oldHtml != newHtml:
                    oldHtml = newHtml
                    print(self.gameName + "_" + self.gameIndex + "_" + u'資料異動')
                    self.tkBox.updateLabel(self.loopIndex, u'資料異動 : ' + self.base.getTime("Microseconds"))
                    newNotice = self.base.json_encode({'data': newHtml})
                    self.base.log(self.gameName + "_" + self.gameIndex, 'change', newNotice)
                else:
                    self.tkBox.updateLabel(self.loopIndex, u'無變更 : ' + self.base.getTime("Microseconds"))
                self.base.sleep(0.1)
        except Exception as e:
            print(self.gameName + "_" + u'發生錯誤2')
            traceback.print_exc()
            self.tkBox.updateLabel(self.loopIndex, u'發生錯誤2 : ' + self.base.getTime("Microseconds"))
            newNotice = self.base.json_encode({'data': e})
            self.base.log('error2', '-----', newNotice)

    def gameTime(self, oldHtml):
        print(u'寫入比賽場次')
        data = {}
        if os.path.exists('event_time.json'):
            with open('event_time.json', encoding='utf-8') as f:
                data = json.load(f)
        self.tkBox.updateLabel(self.loopIndex, u'寫入比賽場次 : ' + self.base.getTime("Microseconds"))
        oGameData = self.tools.getGameTime(self.base, oldHtml)
        if data:
            oGameData.update(data)
        for oGameKey in oGameData:
            print(oGameKey)
            self.base.log(self.gameName + "_gameTime", '',
                          oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), False)
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            print(self.gameIndex + " - " + self.base.getTime("Microseconds"))
            self.tools.closeScroll(self.base.driver)
            newHtml = self.base.getHtml("div.gameListAll_scroll")
            oNewGameData = self.tools.getGameTime(self.base, newHtml)
            iChange = 0
            for oGameKey in oNewGameData:
                if oGameKey not in oGameData:
                    print(oGameKey)
                    iChange = iChange + 1
                    oGameData[oGameKey] = oNewGameData[oGameKey]
                    self.base.log(self.gameName + "_gameTime", '',
                                  oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), False)
            if iChange > 0:
                msg = u'新增場次(' + str(iChange) + ') : '
                self.tkBox.updateLabel(self.loopIndex, msg + self.base.getTime("Microseconds"))
            else:
                self.tkBox.updateLabel(self.loopIndex, u'無新增場次 : ' + self.base.getTime("Microseconds"))
            with open('event_time.json', mode='w', encoding='utf-8') as f:
                json.dump(oGameData, f, ensure_ascii=False)
            self.base.sleep(0.1)

    def gameOdds(self, oldHtml):
        print(u'設定基本資料')
        self.tkBox.updateLabel(self.loopIndex, u'設定基本資料 : ' + self.base.getTime("Microseconds"))
        oldNotice = self.base.json_encode({'data': oldHtml})
        self.base.log(self.gameName + "_" + self.gameIndex, 'setBase', oldNotice)

        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            print(self.gameIndex + " - " + self.base.getTime("Microseconds"))
            self.tools.closeScroll(self.base.driver)
            newHtml = self.base.getHtml("div.gameListAll_scroll")

            if newHtml == "":
                self.checkNoDate()
                continue

            if oldHtml != newHtml:
                oldHtml = newHtml
                print(self.gameName + "_" + self.gameIndex + "_" + u'資料異動')
                self.tkBox.updateLabel(self.loopIndex, u'資料異動 : ' + self.base.getTime("Microseconds"))
                newNotice = self.base.json_encode({'data': newHtml})
                self.base.log(self.gameName + "_" + self.gameIndex, 'change', newNotice)
            else:
                self.tkBox.updateLabel(self.loopIndex, u'無變更 : ' + self.base.getTime("Microseconds"))
            data = parse(newHtml)
            status = upload_data(self.channel, data)
            if status is None:
                self.connection, self.channel = init_session('amqp://GTR:565p@rmq.nba1688.net:5673/')
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
                self.tkBox.updateLabel(self.loopIndex, u'無資料、等待一秒後重試 : ' + self.base.getTime("Microseconds"))
                print(self.gameIndex + " - " + self.base.getTime("Microseconds") + u" - 無資料、等待一秒後重試")
                self.base.sleep(1)
