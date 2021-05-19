
# 備份區、用於解析、目前無作用

def oddSC(_driver):
    print(u"足球")
    ele_btnSC = base.waitBy("CSS", "#btnSC")
    ele_btnSC.click()
    base.sleep(3)

    print(u"滾球")
    ele_btnSCmode = base.waitBy("CSS", "#modeZD")
    ele_btnSCmode.click()
    base.sleep(3)

    print(u"抓取")
    ele_scroll = base.waitBy("CSS", "div.gameListAll_scroll", wait)
    oldHtml = ele_scroll.get_attribute('innerHTML')
    oldNotice = base.json_encode({'data': oldHtml})
    # if oSC['is_decode'] == "1": # 是否解析(1:是,2:否)
    #     print(u"解析")
    #     soup = base.baseSoup(oldHtml, "html.parser")
    #     oGameData = sc.oddSCParsing(soup)
    #     oldNotice = base.json_encode(oGameData)
    print(u'設定基本資料')
    base.log('SC', 'setBase')
    base.log('SC', oldNotice)
    while True:
        print(base.getTime("Microseconds"))
        base.closeScroll()
        ele_scroll = base.waitBy("CSS", "div.gameListAll_scroll", wait)
        newNotice = ele_scroll.get_attribute('innerHTML')
        # if oSC['is_decode'] == "1":  # 是否解析(1:是,2:否)
        #     print(u"解析")
        #     soup = base.baseSoup(newHtml, "html.parser")
        #     oGameData = sc.oddSCParsing(soup)
        #     newNotice = base.json_encode(oGameData)
        if oldNotice != newNotice:
            oldNotice = newNotice
            print(u'資料異動')
            base.log('SC', 'change')
            newNotice = base.json_encode({'data': newNotice})
            base.log('SC', newNotice)
        base.sleep(0.1)

def oddSCParsing(soup):
    aGameList = soup.find_all("div", class_="gameList")
    oGameData = {}
    for gameList in aGameList:
        oTable = {}
        li = gameList.find("ul", class_="btn_GLT").find('li')
        GLT = (li.find_next_siblings("li")[0].getText())
        # print(GLT)
        oTable['GLT'] = GLT
        oTable['date'] = {}
        aGLInList = soup.find_all("tr", class_="GLInList")
        for GLInList in aGLInList:
            aGLINData = get_GLIn(GLInList)
            rel = aGLINData['rel']
            oTable['date'][rel] = aGLINData
        rel = gameList.attrs['rel']
        oGameData[rel] = oTable

    return oGameData

def get_GLIn(GLInList):
    global oSC
    aGLINData = {
        'ridx': GLInList.attrs['ridx'],
        'rel': GLInList.attrs['rel'],
        'st': GLInList.attrs['st']
    }
    aTd = GLInList.find_all("td")
    # 名稱 : 時間 li[0], 名稱 li[1]
    # aTd[0]
    aLi = aTd[0].find_all("li")
    # 時間 li[0]
    if aLi[0].attr:
        oSC['date'] = aLi[0].find_all("div")[0].getText()
        oSC['time'] = aLi[0].find_all("div")[1].getText()
    aGLINData['date'] = oSC['date']
    aGLINData['time'] = oSC['time']
    # 名稱 li[1]
    aGLINData['t1_name'] = aLi[1].find_all("div", class_="GLInTBox_nameT")[0].find('font').getText()
    aGLINData['t2_name'] = aLi[1].find_all("div", class_="GLInTBox_nameT")[1].find('font').getText()

    # print(u"全場讓球 qcrq")  # aTd[1]
    aData = get_SC_GLOdds(aTd[1].find_all("li"))
    aGLINData['t1_qcrq_L'] = aData[0]
    aGLINData['t1_qcrq_R'] = aData[1]
    aGLINData['t2_qcrq_L'] = aData[2]
    aGLINData['t2_qcrq_R'] = aData[3]
    aGLINData['t3_qcrq_L'] = aData[4]
    aGLINData['t3_qcrq_R'] = aData[5]

    # print(u"全場大小 qcdx")  # aTd[2]
    aData = get_SC_GLOdds(aTd[2].find_all("li"))
    aGLINData['t1_qcdx_L'] = aData[0]
    aGLINData['t1_qcdx_R'] = aData[1]
    aGLINData['t2_qcdx_L'] = aData[2]
    aGLINData['t2_qcdx_R'] = aData[3]
    aGLINData['t3_qcdx_L'] = aData[4]
    aGLINData['t3_qcdx_R'] = aData[5]

    # print(u"全場獨贏 qcdy")  # aTd[3]
    aLi = aTd[3].find_all("li")
    aGLINData['t1_qcdy'] = aLi[0].getText()
    aGLINData['t2_qcdy'] = aLi[1].getText()
    aGLINData['t3_qcdy'] = ''
    if len(aLi) > 2:
        aGLINData['t3_qcdy'] = aLi[2].getText()

    # print(u"上半讓球 sbrq")  # aTd[4]
    aData = get_SC_GLOdds(aTd[4].find_all("li"))
    aGLINData['t1_qcrq_L'] = aData[0]
    aGLINData['t1_qcrq_R'] = aData[1]
    aGLINData['t2_qcrq_L'] = aData[2]
    aGLINData['t2_qcrq_R'] = aData[3]
    aGLINData['t3_qcrq_L'] = aData[4]
    aGLINData['t3_qcrq_R'] = aData[5]

    # print(u"上半大小 sbdx")  # aTd[5]
    aData = get_SC_GLOdds(aTd[5].find_all("li"))
    aGLINData['t1_sbdx_L'] = aData[0]
    aGLINData['t1_sbdx_R'] = aData[1]
    aGLINData['t2_sbdx_L'] = aData[2]
    aGLINData['t2_sbdx_R'] = aData[3]
    aGLINData['t3_sbdx_L'] = aData[4]
    aGLINData['t3_sbdx_R'] = aData[5]

    # print(u"上半獨贏 sbdy")  # aTd[6]
    aLi = aTd[6].find_all("li")
    aGLINData['t1_sbdy'] = aLi[0].getText()
    aGLINData['t2_sbdy'] = aLi[1].getText()
    aGLINData['t3_sbdy'] = ''
    if len(aLi) > 2:
        aGLINData['t3_sbdy'] = aLi[2].getText()

    # print(u"更多 gd")  # aTd[7]

    return aGLINData


def get_SC_GLOdds(aLi):
    aData = [
        aLi[0].find("div", class_="GLOdds_L").getText(),
        aLi[0].find("div", class_="GLOdds_R").getText(),
        aLi[1].find("div", class_="GLOdds_L").getText(),
        aLi[1].find("div", class_="GLOdds_R").getText(),
        "",
        ""
    ]
    if len(aLi) > 2:
        aData[4] = aLi[2].find("div", class_="GLOdds_L").getText()
        aData[5] = aLi[2].find("div", class_="GLOdds_R").getText()
    return aData
