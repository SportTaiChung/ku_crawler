# -*- coding: utf-8 -*-
import time


def openWeb(base, globData):
    print(u"開啟新視窗")
    base.driver.get(globData['ku_url_start'])
    base.driver.delete_all_cookies()
    base.sleep(2)
    print(u"設定登入信息")
    for oCookies in globData['aCookies']:
        # print(oCookies)
        base.driver.add_cookie(oCookies)
    base.sleep(2)


def closeScroll(driver):
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
        print(u"等待兩秒檢查是否還有需要關閉")
        time.sleep(2)
        return closeScroll(driver)
    else:
        return True


def getGameTime(base, oldHtml):
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
            homeTeam = aGLInTBox_nameT[0].find('font').text
            awayTeam = aGLInTBox_nameT[1].find('font').text
            oGameData[homeTeam + "|" + awayTeam] = {
                # 'rel': rel,
                'date': st_span,
                'time': rt_font,
                'home': homeTeam,
                'away': awayTeam,
            }
    return oGameData
