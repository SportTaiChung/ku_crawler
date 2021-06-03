# -*- coding: utf-8 -*-

import os
import json
from google.protobuf import text_format

import ku_tools
from upload import init_session, upload_data
from parsing import parse


class kuGameOpen:
    # 建構式
    # globData, tkLabel, i_sport_type, title, btn, game
    def __init__(self, _globData, _tkBox, _tk_index):
        import base as base
        import ku_tools as tools
        self.base = base.Base()
        self.tools = tools
        self.globData = _globData  #
        self.tkBox = _tkBox  #
        self.tkIndex = _tk_index  #
        self.title = "檢查賽事開關"

    # globData['is_test']
    def start(self):
        while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
            # noinspection PyBroadException
            try:
                print(self.title + "_start")
                if self.base.driver == None:
                    self.base.defaultDriverBase()
                    self.tools.openWeb(self.base, self.globData)
                    print(u"導至遊戲")
                    self.tkBox.updateLabel(self.tkIndex, u'導至遊戲 : ' + self.base.getTime("Microseconds"))
                    self.base.driver.get(self.globData['ku_url_end'])
                    self.base.sleep(3)
                self.odd()
            except Exception as e:
                print(self.title + "_" + u'發生錯誤1')
                self.tkBox.updateLabel(self.tkIndex, u'發生錯誤1 : ' + self.base.getTime("Microseconds"))
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
                self.tkBox.updateLabel(self.tkIndex, u'關閉視窗 ' + self.base.getTime("Microseconds"))
                try:
                    self.base.driver.quit()
                except Exception:
                    self.base.sleep(0.1)
            self.base.sleep(5)
        self.tkBox.updateLabel(self.tkIndex, u'腳本已終止 ' + self.base.getTime("Microseconds"))

    def odd(self):
        try:
            print(u"初始化註冊檔")
            self.tkBox.updateLabel(self.tkIndex, u'初始化註冊檔 : ' + self.base.getTime("Microseconds"))
            self.base.resetWinregKeyValue()

            print(u"初始化資料")
            self.tkBox.updateLabel(self.tkIndex, u'初始化資料 : ' + self.base.getTime("Microseconds"))
            oOldGameOpenList = ku_tools.getGameOpen(self.base)
            index_def = 0
            for oOldGameOpenOne in oOldGameOpenList:
                index_def = index_def + 1
                self.base.setWinregKey(oOldGameOpenOne, '1')
                self.base.log('檢查賽事開關', '', oOldGameOpenOne + u" - 開啟", 'switch')
            self.tkBox.updateLabel(self.tkIndex, u"開啟 - " + str(index_def))

            while int(float(self.base.getTime('Ticks'))) <= int(float(self.globData['timestamp_end'])):
                print(str(self.tkIndex) + " - " + self.base.getTime("Microseconds"))
                self.tkBox.updateLabel(self.tkIndex, "監測中 - " + self.base.getTime("Microseconds"))
                oNewGameOpenList = ku_tools.getGameOpen(self.base)

                # 先檢查舊的是否還有在 新的裡面、 沒有就是關閉了
                index_close = 0
                for oOldGameOpenOne in oOldGameOpenList:
                    if oOldGameOpenOne not in oNewGameOpenList:
                        index_close = index_close + 1
                        # print('關閉')
                        # print(oOldGameOpenOne)
                        self.base.setWinregKey(oOldGameOpenOne, '0')
                        self.base.log('檢查賽事開關', '', oOldGameOpenOne + u" - 關閉", 'switch')
                # 再檢查新的是否有在 舊的裡面、 沒有就是新開啟的
                index_open = 0
                for oNewGameOpenOne in oNewGameOpenList:
                    if oNewGameOpenOne not in oOldGameOpenList:
                        index_open = index_open + 1
                        # print('開啟')
                        # print(oNewGameOpenOne)
                        self.base.setWinregKey(oNewGameOpenOne, '1')
                        self.base.log('檢查賽事開關', '', oNewGameOpenOne + u" - 開啟", 'switch')
                oOldGameOpenList = oNewGameOpenList

                self.tkBox.updateLabel(self.tkIndex, u"此次開啟" + str(index_open) + u"關閉" + str(index_close)+
                                       u'、等待十秒後重試')
                self.base.sleep(10)

        except Exception as e:
            print(self.title + "_" + u'發生錯誤2')
            self.tkBox.updateLabel(self.tkIndex, u'發生錯誤2 : ' + self.base.getTime("Microseconds"))
            newNotice = self.base.json_encode({'data': e})
            self.base.log('error2', '-----', newNotice, 'logs')
