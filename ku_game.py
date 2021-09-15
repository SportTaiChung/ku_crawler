# -*- coding: utf-8 -*-

import os
import json
import csv
import traceback
import time
import ku_tools as tools
from time import perf_counter
from google.protobuf import text_format
from upload import init_session, upload_data
from parsing import parse


class KuGame:
    # 建構式
    # globData, tkLabel, i_sport_type, title, btn, game
    def __init__(self, _globData, _tkBox, _tk_index, _i_sport_type, _i_oSport, _title, _btn, _game):
        print([_tk_index, _i_sport_type, _i_oSport, _title, _btn, _game])
        import base as base
        self.base = base.Base()
        self.tools = tools.KuTools(_globData)
        self.globData = _globData  #
        self.tkBox = _tkBox  #
        self.tkIndex = _tk_index  #
        self.i_sport_type = str(_i_sport_type)  # 運動類型 足球 11 , 籃球 12 ... 參考 sport_type 說明
        self.i_oSport = _i_oSport  # list 裡面的index 0: 全場、1:滾球A
        self.title = _title  # 足球 , 籃球 ...
        self.btn = _btn  # 足球 btnSC , 籃球 btnBK ...
        self.game = _game  # {'title': u"今日-全場", 'gameIndex': 1}
        self.gameTitle = str(_game['title'])
        self.gameType = self.gameTitle.split("-")[0]
        self.gameIndex = str(_game['gameIndex'])

        self.connection = None
        self.channel = None
        self._upload_status = True

    def test(self):
        print(self.title + " : test")

    # globData['is_test']
    def start(self):
        if self.globData['is_test'] != "TRUE":
            self.connection, self.channel = init_session('amqp://program:0d597e7dc7c6fa0064dbcbc2a6239fe59c31e06c784d989b1dc75665711c6436@35.73.114.219:5672/%2F?heartbeat=60&connection_attempts=3&retry_delay=3&socket_timeout=3')
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):

            # noinspection PyBroadException
            try:
                print(self.title + "_" + str(self.i_oSport) + "_start")
                if self.base.driver == None:
                    self.updateGameLabel(u'開啟視窗 ' + self.base.getTime("Microseconds"))
                    self.base.defaultDriverBase()
                    self.tools.openWeb(self.base)
                    self.updateGameLabel(u'導至遊戲 : ' + self.base.getTime("Microseconds"))
                    self.base.driver.get(self.globData['ku_url_end'])
                    self.base.sleep(3)
                self.odd()
            except Exception as e:
                print(self.title + "_" + str(self.i_oSport) + "_" + u'發生錯誤1')
                self.updateGameLabel(u'發生錯誤1 : ' + self.base.getTime("Microseconds"))
                # newNotice = self.base.json_encode({'data': e})
                # self.base.log('error1', '-----', newNotice, 'logs')
                self.base.sleep(0.1)
            self.base.sleep(5)
            self.base.driver.implicitly_wait(1)
            try:
                self.base.driver.find_element_by_xpath('//li[@id="modeDS"]')
                self.base.sleep(0.1)
                self.base.driver.find_element_by_xpath('//li[@id="modeZD"]')
                self.base.sleep(0.1)
                self.base.driver.implicitly_wait(30)
            except Exception:
                self.updateGameLabel(u'關閉視窗 ' + self.base.getTime("Microseconds"))
                try:
                    self.base.driver.quit()
                except Exception:
                    self.base.sleep(0.1)
                import base as base
                self.base = base.Base()
            self.base.sleep(5)
        self.updateGameLabel(u'腳本已終止 ' + self.base.getTime("Microseconds"))

    def odd(self):
        try:
            self.updateGameLabel(u'選擇mode' + self.base.getTime("Microseconds"))
            if u'今日' in self.gameTitle:
                print(u"今日")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeDS")
            elif u'早盤' in self.gameTitle:
                print(u"早盤")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeZP")
            else:
                print(u"滾球")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeZD")

            self.updateGameLabel(u'導入' + self.base.getTime("Microseconds"))
            ele_btnPagemode.click()
            self.base.sleep(1)

            print(self.title)
            # if not self.checkBtnExist():
            #     return True

            print(u"類型")
            self.updateGameLabel(u'類型' + self.base.getTime("Microseconds"))
            if (self.gameIndex == "-1"):
                btn = self.btn.replace('btn', ' ')
                btn = btn.lower()
                self.base.driver.execute_script("Menu.ChangeSport(this, '" + btn + "', " + self.i_sport_type + ")")
            else:
                self.base.driver.execute_script(
                    "Menu.ChangeKGroup(this, '" + self.i_sport_type + "', " + self.gameIndex + ");")
            self.base.sleep(1)

            print(u"檢查有無資料")
            self.updateGameLabel(u'檢查有無資料' + self.base.getTime("Microseconds"))
            if not self.checkNoDate():
                return True

            print(u"抓取")
            self.updateGameLabel(u'抓取' + self.base.getTime("Microseconds"))
            oldHtml = self.base.getHtml("div.gameListAll_scroll")

            if self.i_oSport == 0 or self.i_oSport == 99:
                self.gameTime(oldHtml)
            else:
                self.gameOdds(oldHtml)
        except Exception as e:
            print(self.title + "_" + str(self.i_oSport) + "_" + u'發生錯誤2')
            print(e)
            traceback.print_exc()
            self.updateGameLabel(u'發生錯誤2 : ' + self.base.getTime("Microseconds"))
            with open(f'logs/{self.title}_{self.gameTitle}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                log.write(traceback.format_exc())
                log.write('\n')
            # newNotice = self.base.json_encode({'data': e})
            # self.base.log('error2', '-----', newNotice, 'logs')
        return True

    def gameTime(self, oldHtml):
        oGameData = self.tools.getGameTime(self.base, oldHtml)
        print(u'寫入比賽場次')
        self.updateGameLabel(u'寫入比賽場次 : ' + self.base.getTime("Microseconds"))

        for oGameKey in oGameData:
            print(oGameKey)
            self.base.log(self.title + "_gameTime", '',
                          oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), 'mapping')
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            # print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds"))
            try:
                self.updateGameLabel(u'點選我的最愛 : ' + self.base.getTime("Microseconds"))
                self.base.driver.find_element_by_xpath('//div[@id="btnFV"]').click()
                self.base.sleep(5)
                self.updateGameLabel(u'點回遊戲 : ' + self.base.getTime("Microseconds"))
                self.base.driver.find_element_by_xpath('//div[@id="' + self.btn + '"]').click()
                self.base.sleep(5)
                self.base.driver.execute_script(
                    "Menu.ChangeKGroup(this, '" + self.i_sport_type + "', " + self.gameIndex + ");")
                self.base.sleep(60)
            except Exception:
                self.base.sleep(60)
            self.base.driver.execute_script("Outer.ChangeSort(Args.SortTime)")
            self.tools.closeScroll(self.base.driver)

            # if not self.checkBtnExist():
            #     return True

            newHtml = self.base.getHtml("div.gameListAll_scroll")
            oNewGameData = self.tools.getGameTime(self.base, newHtml)
            data = parse(newHtml, self.i_sport_type, self.i_oSport, live=('滾球' in self.gameTitle))
            if self.globData['is_test'] != "TRUE":
                if self.connection.is_closed or self.channel.is_closed or not self._upload_status:
                    if self.connection.is_open:
                        self.connection.close()
                    self.connection, self.channel = init_session('amqp://program:0d597e7dc7c6fa0064dbcbc2a6239fe59c31e06c784d989b1dc75665711c6436@35.73.114.219:5672/%2F?heartbeat=60&connection_attempts=3&retry_delay=3&socket_timeout=3')
                if data:
                    self._upload_status = upload_data(self.channel, data, self.i_sport_type)
            iChange = 0
            for oGameKey in oNewGameData:
                if oGameKey not in oGameData:
                    print(oGameKey)
                    iChange = iChange + 1
                    oGameData[oGameKey] = oNewGameData[oGameKey]
                    self.base.log(self.title + "_gameTime", '',
                                  oGameKey + "=>" + self.base.json_encode(oGameData[oGameKey]), 'mapping')
            if iChange > 0:
                msg = u'新增場次(' + str(iChange) + ') : '
                self.updateGameLabel(msg + self.base.getTime("Microseconds"))
            else:
                print(u'無新增場次')
                self.updateGameLabel(u'無新增場次 : ' + self.base.getTime("Microseconds"))

            self.base.sleep(0.1)

    def gameOdds(self, oldHtml):
        print(u'設定基本資料')
        self.updateGameLabel(u'設定基本資料 : ' + self.base.getTime("Microseconds"))
        oldNotice = self.base.json_encode({'data': oldHtml})
        # self.base.log(self.title + "_" + self.gameTitle, 'setBase', oldNotice, 'logs')

        file_existed = os.path.exists(f'stats/{self.gameTitle}.csv')
        with open(f'stats/{self.gameTitle}.csv', 'a+', encoding='utf-8', newline='') as stat_file:
            stat = {}
            writer = csv.DictWriter(stat_file, fieldnames=['休眠間隔', '摺疊賽事', '檢查按鈕', '取得資料', '檢查資料', '解析耗時', '更新面板', '上傳耗時', '執行耗時'])
            if not file_existed:
                writer.writeheader()
            end_upload = perf_counter()
            while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
                start_time = perf_counter()
                stat['休眠間隔'] = round(start_time - end_upload, 3)
                # print(self.title + "_" + self.gameIndex + " - " + self.base.getTime("Microseconds"))
                self.base.driver.execute_script("Outer.ChangeSort(Args.SortTime)")
                self.tools.closeScroll(self.base.driver)
                end_close_scroll = perf_counter()
                stat['摺疊賽事'] = round(end_close_scroll - start_time, 3)

                # if not self.checkBtnExist():
                #     return True
                end_check_btn = perf_counter()
                stat['檢查按鈕'] = round(end_check_btn - end_close_scroll, 3)

                newHtml = self.base.getHtml("div.gameListAll_scroll")
                end_get_html = perf_counter()
                stat['取得資料'] = round(end_get_html - end_check_btn, 3)

                if newHtml == "":
                    print(u"檢查有無資料")
                    if not self.checkNoDate():
                        return True
                    continue
                end_check_data = perf_counter()
                stat['檢查資料'] = round(end_check_data - end_get_html, 3)

                data = parse(newHtml, self.i_sport_type, self.i_oSport, live=('滾球' in self.gameTitle))
                end_parsing = perf_counter()
                stat['解析耗時'] = round(end_parsing - end_check_data, 3)
                if oldHtml != newHtml:
                    oldHtml = newHtml
                    self.updateGameLabel(u'資料異動 : ' + self.base.getTime("Microseconds"))
                    # newNotice = self.base.json_encode({'data': newHtml})
                    # self.base.log(self.title + "_" + self.gameTitle, 'change', newNotice, 'logs')
                else:
                    self.updateGameLabel(u'無變更 : ' + self.base.getTime("Microseconds"))
                    pass
                end_update_gui = perf_counter()
                stat['更新面板'] = round(end_update_gui - end_parsing, 3)

                if self.globData['is_test'] != "TRUE":
                    if self.connection.is_closed or self.channel.is_closed or not self._upload_status:
                        if self.connection.is_open:
                            self.connection.close()
                        self.connection, self.channel = init_session('amqp://program:0d597e7dc7c6fa0064dbcbc2a6239fe59c31e06c784d989b1dc75665711c6436@35.73.114.219:5672/%2F?heartbeat=60&connection_attempts=3&retry_delay=3&socket_timeout=3')
                    if data:
                        self._upload_status = upload_data(self.channel, data, self.i_sport_type)
                with open(f'{self.title}_{self.gameTitle}.log', 'w', encoding='utf-8') as dump:
                    dump.write(text_format.MessageToString(data, as_utf8=True))
                end_upload = perf_counter()
                stat['上傳耗時'] = round(end_upload - end_update_gui, 3)

                self.base.sleep(0.1)
                stat['執行耗時'] = round(perf_counter() - start_time, 3)
                writer.writerow(stat)

    def checkNoDate(self):
        self.base.driver.implicitly_wait(1)
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            # noinspection PyBroadException
            try:

                # if not self.checkBtnExist():
                #     return False

                self.base.driver.find_element_by_xpath('//div[@class="gameList"]')
                self.base.sleep(0.1)
                self.base.driver.implicitly_wait(30)

                return True
            except Exception:
                self.updateGameLabel(u'無資料、等待一秒後重試 : ' + self.base.getTime("Microseconds"))
                print(self.gameIndex + " - " + self.base.getTime("Microseconds") + u" - 無資料、等待一秒後重試")
                self.base.sleep(1)
                try:
                    self.updateGameLabel(u'點選我的最愛 : ' + self.base.getTime("Microseconds"))
                    self.base.driver.find_element_by_xpath('//div[@id="btnFV"]').click()
                    self.base.sleep(10)
                    self.updateGameLabel(u'點回遊戲 : ' + self.base.getTime("Microseconds"))
                    self.base.driver.find_element_by_xpath('//div[@id="' + self.btn + '"]').click()
                    self.base.sleep(10)
                    if self.i_sport_type != '53':
                        self.base.driver.execute_script(
                            "Menu.ChangeKGroup(this, '" + self.i_sport_type + "', " + self.gameIndex + ");")
                    self.base.sleep(1)
                except Exception:
                    self.base.driver.execute_script("location.reload();")
                    self.base.sleep(1)
                    return False

    def checkBtnExist(self):
        # print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds") + u" - 檢查項目是否存在")
        # 全場btnSC足球Menu.ChangeKGroup(this, '11', 1)
        if self.gameIndex == '-1':
            return True
        isExist = True
        key = self.gameType + self.btn + self.title + "Menu.ChangeKGroup(this, '" + self.i_sport_type + "', " + self.gameIndex + ")"
        isOpen = self.base.getWinregKey(key)
        self.updateGameLabel(u'無列表選項、等待十秒後重試 : ' + self.base.getTime("Microseconds"))
        print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds") + u" - 無列表選項、等待十秒後重試")
        self.base.sleep(10)
        isOpen = self.base.getWinregKey(key)
        isExist = False
        if not isExist:
            print(u'列表開啟、重新導入')
            self.updateGameLabel(u'列表開啟、重新導入 : ' + self.base.getTime("Microseconds"))
        return isExist
        # self.base.driver.implicitly_wait(1)
        # isExist = True
        # index = 0
        # max_index = 19  # 每三分鐘、就回去重新導入網頁
        # if type == 2:  # 2 只執行一次、就回去重新導入網頁
        #     index = max_index - 1
        # while index < max_index:
        #     index = index + 1
        #     # noinspection PyBroadException
        #     try:
        #         self.base.driver.find_element_by_xpath('//div[@id="' + self.btn + '"]')
        #         self.base.driver.implicitly_wait(30)
        #         ele_btnPage = self.base.waitBy("CSS", "#" + self.btn)
        #         ele_btnPage.click()
        #         self.base.sleep(1)
        #         break
        #     except Exception:
        #         self.updateGameLabel( u'無列表選項、等待十秒後重試 : ' + self.base.getTime("Microseconds"))
        #         print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds") + u" - 無列表選項、等待十秒後重試")
        #         self.base.sleep(10)
        #         isExist = False
        # return isExist

    def updateGameLabel(self, _msg):
        if self.tkBox != None:
            self.tkBox.updateLabel(self.tkIndex, _msg)
