# -*- coding: utf-8 -*-
import argparse
import subprocess
import os
import platform
import multiprocessing as mp
import signal
from time import time, sleep
import traceback
import yaml
import base
import ku_game
from ku_tools import KuTools


# 設定帳號相關信息
def load_config(args):
    print('載入設定檔')
    with open(args.config, encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)
    config['sport_config'] = args.sport_config
    config['debug'] = config['debug'] or args.debug
    return config


def main_login(config):
    main_base.defaultDriverBase()
    print(f'開啟KU首頁: {config["home_url"]}')
    main_base.driver.get(config['home_url'])
    main_base.sleep(3)
    print("帳號:" + config['account'])
    print(f'登入帳號: {config["account"]}，密碼: {config["password"]}')
    ele_account = main_base.waitBy("CSS", "#txtUser")
    ele_password = main_base.waitBy("CSS", "#txtPassword")
    ele_account.send_keys(config['account'])
    ele_password.send_keys(config['password'])
    main_base.driver.execute_script("UserPassIsEmpty();")
    main_base.sleep(5)
    print(f'跳轉進入KU賽事頁面: {config["ku_redirect_url"]}')
    main_base.driver.get(config['ku_redirect_url'])
    main_base.sleep(3)
    cookies = main_base.driver.get_cookies()
    config['cookies'] = cookies
    print(f'取得登入cookie: {cookies}')
    current_url = main_base.driver.current_url
    pos = current_url.find('bbview')  # 從字串開頭往後找
    config['ku_url_start'] = f'{current_url[0:pos]}bbview'
    config['ku_url_end'] = f'{current_url[0:pos]}bbview/Games.aspx'


def setup_crawlers(config):
    crawler_configs = []
    print('解析球種設定與初始化')
    with open(config['sport_config'], encoding='utf8') as sport_config_file:
        sport_config = yaml.safe_load(sport_config_file)

    for sport_id in config['crawl_sport_ids']:
        if sport_id in sport_config:
            for game_type_id in sport_config[sport_id]['list']:
                crawler_configs.append({
                    'i_sport_type': sport_id,
                    'i_oSport': game_type_id,
                    'title': sport_config[sport_id]['title'],
                    'btn': sport_config[sport_id]['btn'],
                    'game': sport_config[sport_id]['list'][game_type_id],
                })
    return crawler_configs


def init_crawlers(config, crawler_configs, shared_dict):
    print('初始化爬蟲')
    crawlers = []
    for crawler_id, crawler_config in enumerate(crawler_configs, start=1):
        task = ku_game.KuGame(config, crawler_id,
                              crawler_config['i_sport_type'],
                              crawler_config['i_oSport'],
                              crawler_config['title'], crawler_config['btn'],
                              crawler_config['game'], shared_dict)
        crawlers.append(task)
    return crawlers


def parse_args():
    parser = argparse.ArgumentParser('KU盤口爬蟲')
    parser.add_argument('-c', '--config', default='config.yml', help='設定檔路徑')
    parser.add_argument('-s',
                        '--sport-config',
                        default='sport.yml',
                        help='爬蟲設定檔路徑')
    parser.add_argument('-d', '--debug', action='store_true', help='除錯模式')
    return parser.parse_args()


if __name__ == '__main__':
    mp.freeze_support()
    args = parse_args()
    main_base = base.Base()
    config = load_config(args)
    manager = mp.Manager()
    shared_dict = manager.dict()
    main_login(config)
    crawler_configs = setup_crawlers(config)
    crawlers = init_crawlers(config, crawler_configs, shared_dict)
    print(f'啟動KU個球種玩法盤口爬蟲({len(crawlers)})')
    for crawler in crawlers:
        crawler.start()
        main_base.sleep(config.get('crawler_init_interval') + 5)

    print('已完成所有爬蟲啟動')
    main_base.driver.quit()
    while KuTools.is_working_time(config['crawler_uptime_ranges']):
        try:
            output = subprocess.run(['powershell.exe', '-Command', '(Get-Process -Name Chrome | measure-object -Line).Lines'], capture_output=True, check=True)
            chrome_process_num = int((output.stdout or '0').strip())
            if chrome_process_num > 150:
                os.system('taskkill.exe /IM chrome.exe /F')
                os.system('taskkill.exe /IM chromedriver.exe /F')
                os.system('taskkill.exe /IM leo_main.exe /F')
        except Exception:
            traceback.print_exc()
        for crawler_id, crawler in enumerate(crawlers, start=1):
            if time() - shared_dict[crawler_id]['update_timestamp'] > 300:
                for pid in shared_dict[crawler_id]['pids']:
                    if platform.system() == 'Windows':
                        os.system(f'taskkill.exe /F /pid {pid}')
                    else:
                        os.kill(pid, signal.SIGKILL)
                new_crawler = ku_game.KuGame(config, crawler_id, crawler.i_sport_type,
                        crawler.i_oSport, crawler.title, crawler.btn,
                        crawler.game, shared_dict)
                crawlers[crawler_id - 1] = new_crawler
                new_crawler.start()
        sleep(30)
    manager.shutdown()
