# -*- coding: utf-8 -*-
import re
import time
import traceback
from datetime import datetime
from pyquery import PyQuery as pq
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException, JavascriptException


class KuTools:

    def __init__(self, config):
        self._config = config

    @classmethod
    def is_working_time(cls, time_ranges):
        now = datetime.now().time()
        working = False
        for working_time_range in time_ranges:
            start, end = working_time_range.split('~')
            start_time = datetime.strptime(start, '%H:%M').time()
            end_time = datetime.strptime(end, '%H:%M').time()
            # 時段跨越凌晨00:00
            if end_time < start_time:
                if not (end_time <= now <= start_time):
                    working = True
            elif end_time >= now >= start_time:
                working = True
        return working

    def openWeb(self, base):
        for _ in range(3):
            try:
                print("刪除信息")
                base.driver.delete_all_cookies()
                print("跳轉KU網址")
                base.driver.get(self._config['ku_url_start'])
                base.sleep(5)
                if 'bbview' not in base.driver.current_url.lower():
                    print('跳轉KU失敗')
                    base.sleep(10)
                    continue
                print("複製登入cookie")
                for oCookies in self._config['cookies']:
                    base.driver.add_cookie(oCookies)
                break
            except (TimeoutException, UnexpectedAlertPresentException):
                print('進入賽事看板失敗')

    def closeScroll(self, driver, name=''):
        try:
            driver.execute_script('document.querySelectorAll(".btn_GLT > li.icon_gameList_list").forEach(e=>e.click())')
            time.sleep(0.5)
            driver.execute_script('document.querySelectorAll(".off > li.icon_gameList_list").forEach(e=>e.click())')
            driver.execute_script('document.querySelector(".gameListAll_scroll").scrollTo(0, 100000)')
            time.sleep(0.5)
            driver.execute_script('document.querySelector(".gameListAll_scroll").scrollTo(0, 0)')
            print(f'滾動列表 {name}')
        except (JavascriptException, UnexpectedAlertPresentException) as ex:
            print(name, ex.msg)
        except TimeoutException:
            print(name, '滾動賽事列表超時')
        except Exception:
            traceback.print_exc()

    def getGameTime(self, html):
        doc = pq(html)
        game_list = doc('div.gameList')
        event_time_mapping = {}
        for game in game_list:
            rows = game.cssselect('tr.GLInList')
            for row in rows:
                try:
                    event_id = row.attrib['rel']
                    date_part = row.cssselect('div.GLInTBox_row.st span')[0].text
                    time_part = row.cssselect('div.GLInTBox_row.rt font')[0].text
                    names = row.cssselect('div.GLInTBox_nameT')
                    home_team = pq(names[0]).text().strip()
                    away_team = pq(names[1]).text().strip()
                    if re.match(r'\d+-\d+', date_part) and re.match(r'\d+:\d+', time_part):
                        continue
                except (IndexError, TypeError):
                    pass
                event_time_mapping[event_id] = {
                    'id': event_id,
                    'home': home_team,
                    'away': away_team,
                    'game_time': f'{date_part} {time_part}'
                }
        return event_time_mapping

    def getGameOpen(self, base):
        oGameOpen = {}
        # noinspection PyBroadException
        try:
            ele_btnPagemode = base.waitBy("CSS", "#modeDS")
            ele_btnPagemode.click()
            base.sleep(1)
            sportListHtml = base.getHtml("div#sportList")
            soup = base.baseSoup(sportListHtml, "html.parser")
            aGameList = soup.find_all("div", class_="SM_list")
            for gameList in aGameList:
                if gameList['id'] in ['btnFV', 'btnCS', 'btnTV']:
                    continue
                gameId = gameList['id']
                liList = gameList.find_all("li")
                index = 0
                title = ""
                for li in liList:
                    if index == 0:
                        title = li.text
                    else:
                        subKey = "今日" + gameId + title + li['onclick']
                        oGameOpen[subKey] = '1'
                    index = index + 1

        except Exception:
            base.sleep(1)

        # noinspection PyBroadException
        try:
            ele_btnPagemode = base.waitBy("CSS", "#modeZD")
            ele_btnPagemode.click()
            base.sleep(1)
            sportListHtml = base.getHtml("div#sportList")
            soup = base.baseSoup(sportListHtml, "html.parser")
            aGameList = soup.find_all("div", class_="SM_list")
            for gameList in aGameList:
                if gameList['id'] in ['btnFV', 'btnCS', 'btnTV']:
                    continue
                gameId = gameList['id']
                liList = gameList.find_all("li")
                index = 0
                title = ""
                for li in liList:
                    if index == 0:
                        title = li.text
                    else:
                        subKey = "滾球" + gameId + title + li['onclick']
                        oGameOpen[subKey] = '1'
                    index = index + 1
        except Exception:
            base.sleep(1)

        try:
            ele_btnPagemode = base.waitBy("CSS", "#modeZP")
            ele_btnPagemode.click()
            base.sleep(1)
            sportListHtml = base.getHtml("div#sportList")
            soup = base.baseSoup(sportListHtml, "html.parser")
            aGameList = soup.find_all("div", class_="SM_list")
            for gameList in aGameList:
                if gameList['id'] in ['btnFV', 'btnCS', 'btnTV']:
                    continue
                gameId = gameList['id']
                liList = gameList.find_all("li")
                index = 0
                title = ""
                for li in liList:
                    if index == 0:
                        title = li.text
                    else:
                        subKey = "早盤" + gameId + title + li['onclick']
                        oGameOpen[subKey] = '1'
                    index = index + 1

        except Exception:
            base.sleep(1)

        return oGameOpen
