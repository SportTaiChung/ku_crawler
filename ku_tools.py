# -*- coding: utf-8 -*-
import time


class KuTools:

    def __init__(self,_globData):
        time.sleep(0.01)
        self.globData = _globData

    def openWeb(self, base):
        print(u"開啟新視窗")
        base.driver.get(self.globData['ku_url_start'])
        base.sleep(2)
        print(u"刪除信息")
        base.driver.delete_all_cookies()
        base.sleep(2)
        print(u"設定登入信息")
        for oCookies in self.globData['aCookies']:
            # print(oCookies)
            base.driver.add_cookie(oCookies)
        base.sleep(2)

    def closeScroll(self, driver):
        gameList = driver.find_elements_by_xpath("//div[@class='gameList']/ul")
        index = 0
        isRe = False
        try:
            for gameListOne in gameList:
                className = gameListOne.get_attribute('class')
                rel = gameListOne.find_element_by_xpath('..').get_attribute('rel')
                index = index + 1
                if index == 1:
                    if className == 'btn_GLT off' or className == 'btn_GLT notBind off':
                        print(str(index) + " - " + className + " - " + rel + u' 開啟')
                        gameListOne.click()
                        time.sleep(0.1)
                        isRe = True
                    else:
                        time.sleep(0.01)
                else:
                    if className != 'btn_GLT off' and className != 'btn_GLT notBind off':
                        print(str(index) + " - " + className + " - " + rel + u' 關閉')
                        gameListOne.click()
                        time.sleep(0.1)
                        isRe = True
                    else:
                        time.sleep(0.01)
        except Exception as e:
            print(e)
            time.sleep(0.1)

        if isRe:
            print(u"等待一秒檢查是否還有需要關閉")
            time.sleep(1)
            return self.closeScroll(driver)
        else:
            return True

    def getGameTime(self, base, oldHtml):
        # oldHtml = base.getHtml("div.gameListAll_scroll")
        soup = base.baseSoup(oldHtml, "html.parser")
        aGameList = soup.find_all("div", class_="gameList")
        oGameData = {}
        for gameList in aGameList:
            aTr = gameList.find_all("tr", class_="GLInList")
            st_span = None
            rt_font = None
            for tr in aTr:
                rel = tr['rel']
                st = tr.find("div", class_="GLInTBox_row st")
                if st:
                    st_span = st.find('span').text
                rt = tr.find("div", class_="GLInTBox_row rt")
                if rt:
                    rt_font = rt.find('font').text
                GLInTBox_Name = tr.find("li", class_="GLInTBox_Name")
                aGLInTBox_nameT = GLInTBox_Name.find_all("div", class_="GLInTBox_nameT")
                homeTeam_names = aGLInTBox_nameT[0].find_all('font')
                homeTeam = '/'.join([n.text for n in homeTeam_names])
                awayTeam_names = aGLInTBox_nameT[1].find_all('font')
                awayTeam = '/'.join([n.text for n in awayTeam_names])
                oGameData[homeTeam + "|" + awayTeam] = {
                    # 'rel': rel,
                    'date': st_span,
                    'time': rt_font,
                    'home': homeTeam,
                    'away': awayTeam,
                }
        return oGameData

    def getGameOpen(self, base):
        oGameOpen = {}
        # noinspection PyBroadException
        try:
            print(u"全場")
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
                        print(subKey)
                        oGameOpen[subKey] = '1'
                    index = index + 1

        except Exception:
            base.sleep(1)

        # noinspection PyBroadException
        try:
            print(u"滾球")
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
                        print(subKey)
                        oGameOpen[subKey] = '1'
                    index = index + 1
        except Exception:
            base.sleep(1)

        try:
            print(u"早盤")
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
                        print(subKey)
                        oGameOpen[subKey] = '1'
                    index = index + 1

        except Exception:
            base.sleep(1)

        return oGameOpen
