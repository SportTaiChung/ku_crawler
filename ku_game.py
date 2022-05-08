# -*- coding: utf-8 -*-

import json
from math import ceil
from multiprocessing import Process
import time
from time import perf_counter
from datetime import datetime
import traceback
from google.protobuf import text_format
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException, UnexpectedAlertPresentException, NoSuchElementException, WebDriverException
import psutil
from telegram import Bot
import base
import ku_tools as tools
from upload import init_session, upload_data
from parsing import parse, read_mapping
from constants import Ku


class KuGame(Process):
    # globData, tkLabel, i_sport_type, title, btn, game
    def __init__(self, config, crawler_id, _i_sport_type, _i_oSport, _title, _btn, _game, shared_dict):
        super().__init__()
        self.base = base.Base()
        self.tools = tools.KuTools(config)
        self._pids = []
        self._config = config  #
        self._crawler_id = crawler_id  #
        self.i_sport_type = str(_i_sport_type)  # 運動類型 足球 11 , 籃球 12 ... 參考 sport_type 說明
        self.i_oSport = _i_oSport  # list 裡面的index 0: 全場、1:滾球A
        self.title = _title  # 足球 , 籃球 ...
        self.btn = _btn  # 足球 btnSC , 籃球 btnBK ...
        self.game = _game  # {'title': "今日-全場", 'gameIndex': 1}
        self.gameTitle = str(_game['title'])
        self.gameType = self.gameTitle.split("-")[0]
        self.gameIndex = str(_game['gameIndex'])
        self.name = f'{self.title}_{self.gameTitle}'
        self.parser_config = {
            'machine_id': self._config['machine_id'],
            'sport_id': self.i_sport_type,
            'game_type_id': self.i_oSport,
            'live': '滾球' in self.gameTitle
        }
        self._shared_dict = shared_dict

        self.connection = None
        self.channel = None
        self._upload_status = True
        self._bot = None

    def run(self):
        self._bot = Bot(self._config['telegram_token'])
        if not self._config['debug']:
            self.connection, self.channel = init_session(self._config['mq_url'])
        while self.tools.is_working_time(self._config['crawler_uptime_ranges']):
            try:
                if self.base.driver == None:
                    # 開啟視窗
                    self.base.defaultDriverBase()
                    self.tools.openWeb(self.base)
                    # 跳轉到指定遊戲
                    self.base.driver.get(self._config['ku_url_end'])
                    self.base.sleep(5)
                    self.base.driver.execute_script(f'document.title = "{self.name}";')
                    driver_pid = self.base.driver.service.process.pid
                    self._pids = [child.pid for child in psutil.Process(driver_pid).children(recursive=True)]
                    self._pids.append(driver_pid)
                    self.heartbeat()
                print(f'{self.name} 開始抓取盤口')
                self.odd()
            except WebDriverException as ex:
                print(f'{self.name} 發生selenium錯誤: {ex}')
                with open(f'{self.name}-selenium-error.log', 'a', encoding='utf-8') as error_file:
                    error_file.write(f'{datetime.now()}\n')
                    error_file.write(traceback.format_exc())
                    error_file.write('\n')
                self.base.driver.refresh()
                self.base.sleep(0.5)
                self.base.driver.execute_script(f'document.title = "{self.name}";')
            except Exception as e:
                print(f'{self.name} 發生未知錯誤: {e}')
                # 發生未知錯誤
                traceback.print_exc()
                self.base.driver.refresh()
                self.base.sleep(0.5)
                self.base.driver.execute_script(f'document.title = "{self.name}";')
        print('爬蟲已終止')

    def odd(self):
        try:
            self.switch_label_refresh()
            self.base.sleep(1)
            self.check_and_wait_for_events()
            print('抓取')
            old_dom = self.base.get_dom("div.gameListAll_scroll")
            self.inject_scroll_updater()
            self.heartbeat()
            if self.i_oSport == 0 or self.i_oSport == 99:
                self.gameTime(old_dom)
            else:
                self.gameOdds()
        except (JavascriptException, UnexpectedAlertPresentException, NoSuchElementException) as ex:
            print(f'{self.name}: 盤口處理發生錯誤: {ex}')
            traceback.print_exc()
            # 盤口解析錯誤
            with open(f'logs/{self.name}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                log.write(datetime.now().isoformat())
                log.write(traceback.format_exc())
                log.write('\n')
            self.refresh_page(force=True)

    def gameTime(self, old_dom):
        oGameData = self.tools.getGameTime(old_dom)
        print('寫入比賽場次')
        for event_info in oGameData.values():
            self.base.log(f'{self.title}_gameTime', '', self.base.json_encode(event_info), 'mapping')
        last_refresh_time = time.time()
        while self.tools.is_working_time(self._config['crawler_uptime_ranges']):
            self.heartbeat()
            if time.time() - last_refresh_time > 1800:
                self.refresh_page(force=True)
                last_refresh_time = time.time()
            # if not self.check_websocket_alive():
            #     time.sleep(10)
            #     continue
            self.check_and_click_messagebox()
            if not self.check_active_menu_item():
                print('無法存取目標球種玩法，暫停更新')
                self.base.sleep(30)
                continue

            match_event_number = self.check_event_number_match_list()
            need_refresh = time.time() - last_refresh_time > 300
            if need_refresh:
                if not match_event_number:
                    print(f'{self.name} 賽事數量與顯示不同')
                self.refresh_page()
                last_refresh_time = time.time()

            dom = self.base.get_dom("div.gameListAll_scroll")
            oNewGameData = self.tools.getGameTime(dom)

            data = parse(dom, self.parser_config)
            if not self._config['debug']:
                if self.connection.is_closed or self.channel.is_closed or not self._upload_status:
                    if self.connection.is_open:
                        self.connection.close()
                    self.connection, self.channel = init_session(self._config['mq_url'])
                if data:
                    self._upload_status = upload_data(self.channel, data, self.i_sport_type)
            for event_id, event_info in oNewGameData.items():
                if event_id not in oGameData:
                    oGameData[event_id] = event_info
                    self.base.log(f'{self.title}_gameTime', '',
                                  json.dumps(event_info, ensure_ascii=False),
                                  'mapping')
            with open(f'{self.name}.log', 'w', encoding='utf-8') as dump:
                dump.write(text_format.MessageToString(data, as_utf8=True))
            self.base.sleep(1)

    def gameOdds(self):
        print('開始抓取賽事盤口')
        stat = {}
        end_upload = perf_counter()
        last_refresh_time = time.time()
        last_refresh_mapping_time = time.time()
        ignore_team_hash = set()
        mapping = {}
        while self.tools.is_working_time(self._config['crawler_uptime_ranges']):
            self.heartbeat()
            start_time = perf_counter()
            if time.time() - last_refresh_time > 1800:
                self.refresh_page(force=True)
                last_refresh_time = time.time()
            if time.time() - last_refresh_mapping_time > 120:
                mapping = read_mapping(self.i_sport_type)
                sport_name = Ku.Mapping.sport_id_name[self.i_sport_type]
                with open(f'mapping/{sport_name}_gameTime_{datetime.now():%Y%m%d}.txt', encoding='utf-8') as event_data:
                    unique_lines = set([line for line in event_data.readlines() if line[0] == '{' and line[-2] == '}'])
                with open(f'mapping/{sport_name}_gameTime_{datetime.now():%Y%m%d}.txt', 'w', encoding='utf-8') as event_data:
                    if unique_lines:
                        for line in unique_lines:
                            event_data.write(line)
                last_refresh_mapping_time = time.time()
            # if not self.check_websocket_alive():
            #     time.sleep(10)
            #     continue
            stat['休眠間隔'] = round(start_time - end_upload, 3)
            end_close_scroll = perf_counter()
            stat['摺疊賽事'] = round(end_close_scroll - start_time, 3)

            self.check_and_click_messagebox()
            if not self.check_active_menu_item():
                print('無法存取目標球種玩法，暫停更新')
                self.base.sleep(30)
                continue
            match_event_number = self.check_event_number_match_list()
            need_refresh = time.time() - last_refresh_time > 60
            if need_refresh:
                if not match_event_number:
                    print(f'{self.name} 賽事數量與顯示不同')
                self.refresh_page()
                last_refresh_time = time.time()
                ignore_team_hash.clear()
            end_check_btn = perf_counter()
            stat['檢查按鈕'] = round(end_check_btn - end_close_scroll, 3)

            dom = self.base.get_dom("div.gameListAll_scroll")
            end_get_html = perf_counter()
            stat['取得資料'] = round(end_get_html - end_check_btn, 3)

            if not dom.css_first('div'):
                self.check_and_wait_for_events()
                continue
            end_check_data = perf_counter()
            stat['檢查資料'] = round(end_check_data - end_get_html, 3)
            data = parse(dom, self.parser_config, ignore_team_hash=ignore_team_hash, tha_event_map=mapping)
            end_parsing = perf_counter()
            stat['解析耗時'] = round(end_parsing - end_check_data, 3)
            if not self._config['debug']:
                if self.connection.is_closed or self.channel.is_closed or not self._upload_status:
                    if self.connection.is_open:
                        self.connection.close()
                    self.connection, self.channel = init_session(self._config['mq_url'])
                if data:
                    self._upload_status = upload_data(self.channel, data, self.i_sport_type)
            with open(f'{self.name}.log', 'w', encoding='utf-8') as dump:
                dump.write(text_format.MessageToString(data, as_utf8=True))
            end_upload = perf_counter()
            stat['上傳耗時'] = round(end_upload - end_parsing, 3)

            self.base.sleep(0.1)
            stat['執行耗時'] = round(perf_counter() - start_time, 3)
            print(
                f'{self.name}, 狀態檢查={round(end_check_btn - start_time, 3)} 取得資料={stat["取得資料"]} 解析耗時={stat["解析耗時"]}，上傳耗時={stat["上傳耗時"]} 爬取時間={stat["執行耗時"]}秒'
            )

    def split_tasks(self, dom):
        leagues = dom.css('div.gameList')
        if leagues:
            data_bulks = []
            for index in range(ceil(len(leagues) / 5)):
                league_data_bulk = b''.join(league_row.raw_html for league_row in leagues[index:(index + 1) * 5])
                data_bulks.append((league_data_bulk, self.parser_config))
        return data_bulks

    def check_and_wait_for_events(self):
        while self.tools.is_working_time(self._config['crawler_uptime_ranges']):
            try:
                self.heartbeat()
                if self.i_sport_type != '53':
                    self.base.driver.execute_script(f'Menu.ChangeKGroup(this, "{self.i_sport_type}", "{self.gameIndex}");')
                self.base.sleep(30)
                self.switch_label_refresh()
                self.base.sleep(30)
                self.base.driver.find_element(By.CSS_SELECTOR, 'div.gameList')
                break
            except (NoSuchElementException, JavascriptException, UnexpectedAlertPresentException):
                print('無資料、等待五秒後重試')
                self.base.sleep(5)
                try:
                    print(f'{self.name} 點選我的最愛')
                    self.base.driver.find_element(By.CSS_SELECTOR, 'div#btnFV').click()
                    self.base.sleep(5)
                    print(f'{self.name} 點回遊戲')
                    self.base.driver.find_element(By.CSS_SELECTOR, f'div#{self.btn}').click()
                    self.base.sleep(5)
                    if self.i_sport_type != '53':
                        self.base.driver.execute_script(f'Menu.ChangeKGroup(this, "{self.i_sport_type}", "{self.gameIndex}");')
                    self.base.sleep(10)
                except NoSuchElementException:
                    self.base.sleep(5)
                except JavascriptException as ex:
                    print(self.name, ex.msg)
                except UnexpectedAlertPresentException:
                    self.base.sleep(300)
                except Exception:
                    traceback.print_exc()
                    self.refresh_page(force=True)
            print(self.name, '等待賽事資料出現')
            self.base.sleep(60)

    def check_active_menu_item(self):
        if self.gameIndex == '-1':
            return True
        try:
            active_time_type_id = self.base.driver.execute_script('return document.querySelector("#modeOption li.on").id;')
            if ('今日' in self.gameTitle and active_time_type_id != 'modeDS'
                ) or ('早盤' in self.gameTitle and active_time_type_id !=
                      'modeZP') or ('滾球' in self.gameTitle
                                    and active_time_type_id != 'modeZD'):
                try:
                    self.switch_label_refresh()
                except Exception:
                    traceback.print_exc()
                    print(self.name, '無法切換球種時間類型')
                    return False

            match_menu_items = self.base.driver.execute_script(r'return ((document.querySelector(".SM_list li.on") || window).onclick || "").toString().match(/\d+/g) || [];')
            if not match_menu_items or len(match_menu_items) != 2:
                match_menu_items = (self.i_sport_type, self.gameIndex)
                print(self.name, '無法抓取到目前球種玩法')
            sport_id, game_type_id = match_menu_items
            if self.i_sport_type != sport_id or self.gameIndex != game_type_id:
                print(f'當前爬取非指定頁面，當前: ({sport_id}, {game_type_id})，目標: {self.name}_{self.i_sport_type}_{self.i_oSport} ({self.i_sport_type}, {self.gameIndex})')
                items = self.get_menu_list()
                if f'{self.i_sport_type}_{self.gameIndex}' not in items:
                    print(f'目前沒有目標球種玩法選項，當前: ({sport_id}, {game_type_id})，目標: ({self.i_sport_type}, {self.gameIndex})')
                    return False
                self.base.driver.execute_script(f"Menu.ChangeKGroup(this, '{self.i_sport_type}', {self.gameIndex})")
                match_menu_items = self.base.driver.execute_script(r'return ((document.querySelector(".SM_list li.on") || window).onclick || "").toString().match(/\d+/g) || [];')
                if not match_menu_items or len(match_menu_items) != 2:
                    match_menu_items = (self.i_sport_type, self.gameIndex)
                    print(self.name, '無法抓取到目前球種玩法')
                sport_id, game_type_id = match_menu_items
                if self.i_sport_type != sport_id or self.gameIndex != game_type_id:
                    print(f'無法切換到指定球種玩法，當前: ({sport_id}, {game_type_id})，目標: ({self.i_sport_type}, {self.gameIndex})')
                    return False
                print(f'{self.name} 成功切換到指定球種玩法，當前: ({sport_id}, {game_type_id})')
        except JavascriptException as ex:
            print(self.name, ex.msg)
            with open(f'logs/{self.name}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                log.write(datetime.now().isoformat())
                log.write(traceback.format_exc())
                log.write('\n')
                log.write(self.base.getHtml("div.sportMenu_in"))
                log.write('\n')
            return False
        return True

    def get_menu_list(self):
        menu_items = self.base.driver.execute_script(r'var items = []; document.querySelectorAll(".SM_list li[rel]").forEach(e => {items.push(e.onclick.toString().match(/\d+/g));}, items); return items;')
        item_keys = set([f'{item[0]}_{item[1]}' for item in menu_items])
        return item_keys

    def check_event_number_match_list(self):
        try:
            self.base.driver.execute_script('UnMask();')
            try:
                is_sport_exist = self.base.driver.execute_script(f'return document.querySelector("div#{self.btn}") !== null')
                if is_sport_exist:
                    event_counter = self.base.driver.execute_script(f'return document.querySelector(".SM_list li.on div.SM_listIn_counter").textContent')
                else:
                    event_counter = 0
            except JavascriptException:
                self.base.driver.execute_script(f'document.querySelector("div#{self.btn} div.btn_SM_listT").click()')
                self.base.sleep(3)
                event_counter = self.base.driver.execute_script(f'return document.querySelector(".SM_list li.on div.SM_listIn_counter").textContent')
            unique_event_number = self.base.driver.execute_script(r'var events = new Set(); document.querySelectorAll("tr.GLInList").forEach(e => events.add(e.getAttribute("rel")), events); return events.size;')
        except JavascriptException as ex:
            print(f'{self.name} 確認盤口數量一致性發生錯誤: {ex.msg}')
            with open(f'logs/{self.name}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                log.write(datetime.now().isoformat())
                log.write(traceback.format_exc())
                log.write('\n')
                log.write(self.base.getHtml("div.sportMenu_in"))
                log.write('\n')
            return False
        if event_counter is not None and unique_event_number is not None and int(event_counter) <  unique_event_number:
            return False
        return True

    def check_and_click_messagebox(self):
        try:
            has_alert, message = self.base.driver.execute_script('return [Alert.Status, Alert.Msg];')
            if has_alert:
                self.base.driver.execute_script('Alert.Confirm();')
                self._bot.send_message(self._config['telegram_chat_id'], f'{self.name} KU網站跳出訊息: {message}，自動點擊確認')
        except (JavascriptException, UnexpectedAlertPresentException):
            pass

    def refresh_page(self, force=False):
        if force:
            print(f'{self.name} {datetime.now().isoformat(sep=" ")} 強制刷新頁面')
            self.base.driver.refresh()
            self.base.sleep(3)
            try:
                self.switch_label_refresh()
                self.base.sleep(1)
            except Exception:
                traceback.print_exc()
                print('無法切換球種時間類型')

            change_menu_timeout = time.time() + 60
            current_menu_item = ''
            while current_menu_item != f'{self.i_sport_type}_{self.gameIndex}':
                self.heartbeat()
                self.base.sleep(15)
                try:
                    sport_code, default_game_type_id = Ku.Mapping.get_sport_category_parameter(self.i_sport_type)
                    if sport_code and default_game_type_id:
                        print(f'切換主球種按鈕: {sport_code}, {default_game_type_id}')
                        self.base.driver.execute_script(f"Menu.ChangeKGroup(this, '{sport_code}', {default_game_type_id});")
                        self.base.sleep(2)
                    self.base.driver.execute_script(f"Menu.ChangeKGroup(this, '{self.i_sport_type}', {self.gameIndex});")
                    self.base.sleep(1)
                    self.base.driver.execute_script("Outer.ChangeSort(Args.SortTime)")
                    match_menu_items = self.base.driver.execute_script(r'return ((document.querySelector(".SM_list li.on") || window).onclick || "").toString().match(/\d+/g) || [];')
                    if not match_menu_items or len(match_menu_items) != 2:
                        match_menu_items = (self.i_sport_type, self.gameIndex)
                        print('無法抓取到目前球種玩法')
                    sport_id, game_type_id = match_menu_items
                    current_menu_item = f'{sport_id}_{game_type_id}'
                except JavascriptException as ex:
                    print(self.name, ex.msg)
                    with open(f'logs/{self.name}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                        log.write(datetime.now().isoformat())
                        log.write(traceback.format_exc())
                        log.write('\n')
                        log.write(self.base.getHtml("div.sportMenu_in"))
                        log.write('\n')
                if time.time() > change_menu_timeout:
                    print('刷新頁面後無法切回原球種玩法')
                    break
        else:
            print(f'{self.name} {datetime.now().isoformat(sep=" ")} 切換球種刷新頁面')
            self.base.driver.execute_script("Menu.ChangeKGroup(this, 'fv', 99);")
            current_menu_item = 'fv_99'
            change_menu_timeout = time.time() + 60
            while current_menu_item != f'{self.i_sport_type}_{self.gameIndex}':
                self.heartbeat()
                self.base.sleep(5)
                try:
                    sport_code, default_game_type_id = Ku.Mapping.get_sport_category_parameter(self.i_sport_type)
                    if sport_code and default_game_type_id:
                        print(f'切換主球種按鈕: {sport_code}, {default_game_type_id}')
                        self.base.driver.execute_script(f"Menu.ChangeKGroup(this, '{sport_code}', {default_game_type_id});")
                        self.base.sleep(1)

                    self.base.driver.execute_script(f"Menu.ChangeKGroup(this, '{self.i_sport_type}', {self.gameIndex});")
                    match_menu_items = self.base.driver.execute_script('return ((document.querySelector(".SM_list li.on") || window).onclick || "").toString().match(/\d+/g) || [];')
                    if not match_menu_items or len(match_menu_items) != 2:
                        match_menu_items = (self.i_sport_type, self.gameIndex)
                        print('無法抓取到目前球種玩法')
                    sport_id, game_type_id = match_menu_items
                    current_menu_item = f'{sport_id}_{game_type_id}'
                except JavascriptException as ex:
                    print(self.name, ex.msg)
                    with open(f'logs/{self.name}_{self.i_sport_type}_{self.i_oSport}_error.log', 'a+', encoding='utf-8') as log:
                        log.write(datetime.now().isoformat())
                        log.write(traceback.format_exc())
                        log.write('\n')
                        log.write(self.base.getHtml("div.sportMenu_in"))
                        log.write('\n')
                if time.time() > change_menu_timeout:
                    print('刷新頁面後無法切回原球種玩法')
                    break
        self.base.driver.execute_script(f'document.title = "{self.name}";')
        self.inject_scroll_updater()

    def switch_label_refresh(self):
        # 切換盤口時間羽球種刷新資料
        try:
            print(self.name, '選擇爬取時間範圍')
            if '今日' in self.gameTitle:
                print("今日")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeDS")
            elif '早盤' in self.gameTitle:
                print("早盤")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeZP")
            else:
                print("滾球")
                ele_btnPagemode = self.base.waitBy("CSS", "#modeZD")

            print(self.name, '跳轉到時段標籤')
            try:
                ele_btnPagemode.click()
                self.base.sleep(0.5)
            except Exception:
                traceback.print_exc()
                print(self.name, '無法切換球種時間類型')
            print(self.name, '切到收藏夾')
            self.base.driver.execute_script("Menu.ChangeSport(this, 'fv', 99);")
            self.base.sleep(0.5)
            print(self.name, '切換玩法類型')
            if (self.gameIndex == "-1"):
                btn = self.btn.replace('btn', ' ')
                btn = btn.lower()
                self.base.driver.execute_script(f'Menu.ChangeSport(this, "{btn}", "{self.i_sport_type}");')
            else:
                self.base.driver.execute_script(f'Menu.ChangeKGroup(this, "{self.i_sport_type}", "{self.gameIndex}");')
        except (JavascriptException, NoSuchElementException, UnexpectedAlertPresentException) as ex:
            print(self.name, ex.msg)


    def check_websocket_alive(self):
        alive = False
        try:
            alive = self.base.driver.execute_script('return self.mainSocket.isAllDown;')
        except JavascriptException:
            print('網路中斷')
        return alive

    def inject_scroll_updater(self):
        # 注入JS滾動賽事卷軸
        try:
            if not self.base.driver.execute_script('return window.scrollTimer;'):
                self.base.driver.execute_script("""
                    window.scrollList = function() {
                        document.querySelectorAll(".btn_GLT > li.icon_gameList_list").forEach(e=>e.click());
                        setTimeout(()=>document.querySelectorAll(".off > li.icon_gameList_list").forEach(e=>e.click()), 500);
                        setTimeout(()=>document.querySelector(".gameListAll_scroll").scrollTo(0, 100000), 800);
                        setTimeout(()=>document.querySelector(".gameListAll_scroll").scrollTo(0, 0), 1000);
                    }
                    window.scrollTimer = setInterval(window.scrollList, 120000);
                """)
        except JavascriptException as ex:
            print(f'注入滾動賽事卷軸JS失敗: {ex.msg}')

    def heartbeat(self):
        if 'bbview/Games.aspx' in self.base.driver.current_url:
            self._shared_dict[self._crawler_id] = {
                'pids': self._pids,
                'update_timestamp': time.time()
            }
