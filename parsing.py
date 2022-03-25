# coding: utf-8

import os
from time import perf_counter
import re
from datetime import datetime, timedelta
import json
from json.decoder import JSONDecodeError
from itertools import product
import traceback
import requests
from pyquery import PyQuery as pq
from google.protobuf import text_format
import APHDC_pb2 as spec
from constants import Ku, GameType, Period, EXCLUDED_LEAGUES


def parse(dom, parser_config, ignore_team_hash=None, tha_event_map=None):
    machine_id = parser_config['machine_id']
    sport_id = parser_config['sport_id']
    game_type_id = parser_config['game_type_id']
    live = parser_config['live']
    sport_type_name = Ku.Mapping.sport_game_class.get(sport_id, 'other')
    sport_type = GameType[sport_type_name]
    mapping = tha_event_map if (live and tha_event_map) else {}
    data = spec.ApHdcArr()
    if not dom('div:first'):
        return data
    event_list_doc = dom('.gameList')
    event_rel_id = ''
    date = ''
    date_time = ''
    home_score = '0'
    away_score = '0'
    olympic = (sport_id == '53')
    event_time_map = {}
    if not ignore_team_hash:
        ignore_team_hash = set()
    for event_doc in event_list_doc:
        league_name = re.sub(r'\s', '', event_doc.cssselect('.btn_GLT li:nth-child(2)')[0].text)
        if sport_id in ('11', '51', '52') and live and EXCLUDED_LEAGUES.search(league_name):
            continue
        if olympic:
            if '排球' in league_name:
                sport_id = '16'
                sport_type = GameType.otherbasketball
            elif '足球' in league_name:
                sport_id = '53'
                sport_type = GameType.soccer
            elif '羽毛球' in league_name:
                sport_id = '17'
                sport_type = GameType.otherbasketball
            elif '乒乓球' in league_name:
                sport_id = '21'
                sport_type = GameType.otherbasketball
            elif '網球' in league_name:
                sport_id = '14'
                sport_type = GameType.tennis
            else:
                sport_id = '12'
                sport_type = GameType.otherbasketball
        rows = event_doc.cssselect('tr.GLInList')
        home_red, away_red = '0', '0'
        for row in rows:
            try:
                cells = row.cssselect('td')
                header = None
                if (sport_type is GameType.soccer and game_type_id == 4) or (sport_type is GameType.eSport and game_type_id == 2) or (sport_type is GameType.basketball and game_type_id == 4):
                    odds_table = event_doc.cssselect('table')[0]
                    new_event_rel_id = event_id = odds_table.attrib['rel'] + odds_table.attrib.get('st')
                    header = event_doc.cssselect('th.GLInBoxT')[0]
                    teams = header.cssselect('font[rel]')
                    home_team = re.sub(r'\s', '', teams[0].text)
                    if sport_type is GameType.basketball and game_type_id == 4:
                        away_element = event_doc.cssselect('table:nth-child(2) th.GLInBoxT:nth-child(1) font[rel]')
                        away_team = re.sub(r'\s', '', get_value(away_element, ''))
                    else:
                        away_team = re.sub(r'\s', '', re.sub(r'\s', '', teams[1].text))
                    if live:
                        date = header.cssselect('span.GLInBoxT_time > span')[0].text
                        date_time = header.cssselect('span.GLInBoxT_time > font')[0].text
                        live_time = f'{date} {date_time or ""}'.replace("'", '').replace('半場', '').replace('LIVE', '上 0').strip()
                    home_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(1)')
                    home_score = home_score_element[0].text.strip() if home_score_element else '0'
                    away_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(2)')
                    # away_score_element = cells[0].cssselect('span.GLInTBox_Score > span:nth-child(3)')
                    away_score = away_score_element[0].text.strip() if away_score_element else '0'
                else:
                    new_event_rel_id = row.attrib['rel']
                    event_id = row.attrib['rel'] + row.attrib.get('st')
                    if len(cells[0].cssselect('div.GLInTBox_nameT[rel] font')) >= 2:
                        if len(cells[0].cssselect('div.GLInTBox_nameT[rel] font')) == 2:
                            home_team = re.sub(r'\s', '', cells[0].cssselect('div.GLInTBox_nameT[rel] font')[0].text)
                            away_team = re.sub(r'\s', '', cells[0].cssselect('div.GLInTBox_nameT[rel] font')[1].text)
                            if live and cells[0].cssselect('div.GLInTBox_redCard'):
                                home_red = get_value(cells[0].cssselect('div.GLInTBox_redCard'), '0')
                                away_red = get_value(cells[0].cssselect('div.GLInTBox_redCard'), '0', index=1)
                        else:
                            home_team = re.sub(r'\s', '', f'{cells[0].cssselect("div.GLInTBox_nameT[rel] font")[0].text}/{cells[0].cssselect("div.GLInTBox_nameT[rel] font")[1].text}')
                            away_team = re.sub(r'\s', '', f'{cells[0].cssselect("div.GLInTBox_nameT[rel] font")[2].text}/{cells[0].cssselect("div.GLInTBox_nameT[rel] font")[3].text}')
                    elif (sport_type is GameType.basketball and game_type_id == 4) or (sport_type is GameType.baseball and game_type_id == 5):
                        home_team = away_team = re.sub(r'\s', '', cells[0].cssselect('div.GLInTBox_nameT > font')[0].text)
                    else:
                        home_team = re.sub(r'\s', '', cells[0].cssselect('li:nth-child(2) font')[0].text)
                        away_team = re.sub(r'\s', '', cells[0].cssselect('li:nth-child(2) font')[1].text)

                if live:
                    event_info = mapping.get(row.attrib['rel'])
                # 多盤口
                if new_event_rel_id != event_rel_id:
                    if header and not live:
                        date_str, time_str = event_doc.cssselect('span.GLInBoxT_time')[0].text.split(' ')
                        event_info = {
                            'id': row.attrib['rel'],
                            'home': home_team,
                            'away': away_team,
                            'game_time': f'{date_str} {time_str}'
                        }
                        live_time = ''
                    elif not live:
                        event_info = {
                            'id': row.attrib['rel'],
                            'home': home_team,
                            'away': away_team,
                            'game_time': f'{row.cssselect("div.GLInTBox_row.st > span")[0].text} {row.cssselect("div.GLInTBox_row.rt > font")[0].text}'
                        }
                        live_time = ''
                    if not header and live:
                        if cells[0].cssselect('.st span'):
                            date = cells[0].cssselect('.st span')[0].text
                            date_time = cells[0].cssselect('.rt font')[0].text
                        live_time = f'{date} {date_time or ""}'.replace("'", '').replace('半場', '').replace('LIVE', '上 0').strip()
                        home_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(1)')
                        home_score = (home_score_element[0].text or '').strip() if home_score_element else '0'
                        away_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(2)')
                        away_score = (away_score_element[0].text or '').strip() if away_score_element else '0'
                    event_rel_id = new_event_rel_id

                if not event_info:
                    # if row.attrib['rel'] in ignore_team_hash:
                    #     continue
                    sport_type_id = Ku.Mapping.get_sport_type_id(sport_id, league_name)
                    event_time = None
                    if sport_id in event_time_map:
                        event_map = event_time_map[sport_id]
                        event_time = search_event_time(home_team, away_team, event_map)
                    else:
                        event_datacenter = query_sport_event_time(sport_type_id)
                        event_time_map[sport_id] = event_datacenter
                        event_time = search_event_time(home_team, away_team, event_datacenter)
                    if event_time:
                        date_str = event_time.split(' ')[0]
                        sport_name = Ku.Mapping.sport_id_name.get(sport_id)
                        event_info = {
                            'id': row.attrib['rel'],
                            'home': home_team,
                            'away': away_team,
                            'game_time': f'{date_str[5:]} {event_time[11:16]}'
                        }
                        with open(f'mapping/{sport_name}_gameTime_{date_str.replace("-", "")}.txt', encoding='utf-8', mode='a') as game_time_data:
                            json.dump(event_info,
                                      game_time_data,
                                      ensure_ascii=False)
                            game_time_data.write('\n')
                    else:
                        # ignore_team_hash.add(row.attrib['rel'])
                        # print('找不到相關開賽時間:', f'{event_id}={home_team}|{away_team}')
                        sport_name = Ku.Mapping.sport_id_name.get(sport_id)
                        event_info = {
                            'id': row.attrib['rel'],
                            'home': home_team,
                            'away': away_team,
                            'game_time': f'{datetime.now():%m-%d %H:00}'
                        }
                        with open(f'mapping/{sport_name}_gameTime_{datetime.now():%Y%m%d}.txt', encoding='utf-8', mode='a') as game_time_data:
                            json.dump(event_info,
                                      game_time_data,
                                      ensure_ascii=False)
                            game_time_data.write('\n')

                today = datetime.today()
                year = today.year
                if today.month == 12 and today.month != int(event_info["game_time"].split('-')[0]):
                    year += 1
                event_time = f'{year}-{event_info["game_time"]}:00'
                game_class = game_class_convert(sport_type, league_name)
                # live_time = re.sub(r'第\d節', '?q' live_time)
                event = spec.ApHdc(source='KU',
                                    game_class=game_class,
                                    ip=f'ku_python-{machine_id}',
                                    event_time=event_time,
                                    source_updatetime=datetime.now().strftime(
                                        '%Y-%m-%d %H:%M:%S.%f')[:-3],
                                    live='true' if live else 'false',
                                    live_time=live_time,
                                    information=spec.information(
                                        league=league_name,
                                        home=spec.infoHA(team_name=home_team),
                                        away=spec.infoHA(team_name=away_team)),
                                    score=spec.score(home=home_score, away=away_score),
                                    redcard=spec.redcard(home=home_red, away=away_red)
                                )
                if game_type_id in (0, 1, 99):
                    event_full = spec.ApHdc()
                    event_1st = spec.ApHdc()
                    event_full.CopyFrom(event)
                    event_1st.CopyFrom(event)
                    # 全場
                    event_full.game_id = event_id
                    event_full.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                    # 全場讓分
                    advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                    zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text
                    zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                    if zf_line:
                        home_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        away_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                    else:
                        home_zf_odds = '0'
                        away_zf_odds = '0'
                    event_full.twZF.CopyFrom(
                        spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                    odds=home_zf_odds),
                                awayZF=spec.typeZF(line=zf_away_line,
                                                    odds=away_zf_odds)))
                    # 全場大小
                    if not olympic or (olympic and sport_id not in ('17', '21')):
                        ds_line = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_full.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                    if sport_type is GameType.soccer or (sport_type is GameType.baseball and not live):
                        # 全場獨贏
                        de_home_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[3].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_full.draw = de_draw_odds
                        event_full.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                    elif sport_type is GameType.basketball:
                        # 全場單雙
                        odd_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_full.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                    elif sport_type is GameType.hockey:
                        # 全場單雙
                        odd_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_full.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                    elif sport_type is GameType.tennis:
                        event_full.information.league += '-局數獲勝者'
                    elif sport_type is GameType.otherbasketball and sport_id in ('16', '21'):
                        event_full.information.league += '-局數獲勝者'
                        de_home_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[3].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_full.draw = de_draw_odds
                        event_full.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                    elif sport_type is GameType.otherbasketball and sport_id in ('17', '21'):
                        event_full.information.league += '-局數獲勝者'
                        de_home_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[2].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_full.draw = de_draw_odds
                        event_full.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))

                    # 上半場
                    event_1st.game_id = f'{event_id}1'
                    event_1st.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, half=True, live=live).value
                    if sport_type is GameType.tennis:
                        # 上半場獨贏
                        de_1st_home_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_1st_away_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[3].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_1st_draw_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_1st.draw = de_1st_draw_odds
                        event_1st.de.CopyFrom(spec.onetwo(home=de_1st_home_odds, away=de_1st_away_odds))
                        # 上半場讓分
                        advanced_team_1st = 'home' if get_value(cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_1st_line = cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[4].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_1st_home_line, zf_1st_away_line = compute_zf_line(zf_1st_line, advanced_team_1st)
                        if zf_1st_line:
                            home_zf_1st_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_1st_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_1st_odds = '0'
                            away_zf_1st_odds = '0'
                        event_1st.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_1st_home_line,
                                                        odds=home_zf_1st_odds),
                                    awayZF=spec.typeZF(line=zf_1st_away_line,
                                                        odds=away_zf_1st_odds)))
                    elif sport_type is not GameType.eSport and sport_type is not GameType.hockey and len(cells) > 5:
                        # 上半場讓分
                        if sport_type == GameType.baseball and live:
                            advanced_team_1st = 'home' if get_value(cells[3].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                            zf_1st_line = cells[3].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[3].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                            zf_1st_home_line, zf_1st_away_line = compute_zf_line(zf_1st_line, advanced_team_1st)
                            if zf_1st_line:
                                home_zf_1st_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                                away_zf_1st_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                            else:
                                home_zf_1st_odds = '0'
                                away_zf_1st_odds = '0'
                        else:
                            advanced_team_1st = 'home' if get_value(cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                            zf_1st_line = cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[4].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                            zf_1st_home_line, zf_1st_away_line = compute_zf_line(zf_1st_line, advanced_team_1st)
                            if zf_1st_line:
                                home_zf_1st_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                                away_zf_1st_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                            else:
                                home_zf_1st_odds = '0'
                                away_zf_1st_odds = '0'
                        if sport_id not in ('16', '17', '21'):
                            event_1st.twZF.CopyFrom(
                                spec.twZF(homeZF=spec.typeZF(line=zf_1st_home_line,
                                                            odds=home_zf_1st_odds),
                                        awayZF=spec.typeZF(line=zf_1st_away_line,
                                                            odds=away_zf_1st_odds)))
                        # 上半場大小
                        if sport_type == GameType.baseball and live or (olympic and sport_id == '16'):
                            ds_1st_line = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '0')
                            ds_1st_over_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            ds_1st_under_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        elif olympic and sport_id in ('17', '21'):
                            ds_1st_line = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '0')
                            ds_1st_over_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            ds_1st_under_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            ds_1st_line = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '0')
                            ds_1st_over_odds = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            ds_1st_under_odds = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_1st_line:
                            ds_1st_line = '0'
                            ds_1st_over_odds = '0'
                            ds_1st_under_odds = '0'
                        if not re.search(r'[+./-]', ds_1st_line):
                            ds_1st_line += '+0'
                        event_1st.twDS.CopyFrom(spec.typeDS(line=ds_1st_line, over=ds_1st_over_odds, under=ds_1st_under_odds))
                    if sport_type is GameType.soccer or (sport_type is GameType.baseball and not live):
                        # 上半場獨贏
                        de_1st_home_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_1st_away_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[6].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_1st_draw_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_1st.draw = de_1st_draw_odds
                        event_1st.de.CopyFrom(spec.onetwo(home=de_1st_home_odds, away=de_1st_away_odds))
                    elif sport_type is GameType.basketball:
                        # 全場單雙
                        odd_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_1st.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                    elif sport_type is GameType.tennis:
                        event_1st.information.league += '-盤數獲勝者'
                        event_1st.game_type = Period.LIVE_FULL.value if game_type_id not in (0, 99) else Period.FULL.value
                        event_1st.de.CopyFrom(spec.onetwo(home='0', away='0'))
                    elif sport_type is GameType.otherbasketball and sport_id in ('16', '17', '21'):
                        event_1st.information.league += '-總分獲勝者'
                        # 上半場單雙
                        odd_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_1st.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))


                    if sport_type is not GameType.eSport and sport_type is not GameType.hockey:
                        if sport_type is GameType.baseball:
                            data.aphdc.extend([reverseTeam(event_full), reverseTeam(event_1st)])
                        else:
                            data.aphdc.extend([event_full, event_1st])
                    else:
                        data.aphdc.append(event_full)
                elif game_type_id == 2:
                    # 角球
                    if sport_type is GameType.soccer:
                        event_full_corner = spec.ApHdc()
                        event_full_corner.CopyFrom(event)
                        event_full_corner.game_id = f'{event_id}20'
                        event_full_corner.information.league += '-角球'
                        event_full_corner.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_full_corner.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_full_corner.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 全場獨贏
                        de_home_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[3].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_full_corner.draw = de_draw_odds
                        event_full_corner.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                        # 全場單雙
                        odd_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_full_corner.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                        data.aphdc.append(event_full_corner)
                    elif sport_type is GameType.basketball:
                        event_bk_set = spec.ApHdc()
                        event_bk_set.CopyFrom(event)
                        event_bk_set.information.league += '-單節'
                        event_bk_set.game_id = f'{event_id}10'
                        event_bk_set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_bk_set.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_bk_set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 全場單雙
                        odd_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_bk_set.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                        data.aphdc.append(event_bk_set)
                    elif sport_type is GameType.baseball:
                        event_13set = spec.ApHdc()
                        event_13set.CopyFrom(event)
                        event_13set.information.league += '(1~3局)投注'
                        event_13set.game_id = f'{event_id}13'
                        event_13set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_13set.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_13set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 一輸
                        advanced_team = 'home' if get_value(cells[3].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        home_zf_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        away_zf_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_13set.esre.CopyFrom(
                            spec.Esre(let=spec.whichTeam.home if advanced_team
                                      else spec.whichTeam.away,
                                      home=home_zf_odds,
                                      away=away_zf_odds))
                        # 全場單雙
                        odd_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        even_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        event_13set.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                        data.aphdc.append(reverseTeam(event_13set))
                    elif sport_type is GameType.tennis:
                        event_tennis_set = spec.ApHdc()
                        event_tennis_set.CopyFrom(event)
                        event_tennis_set.game_id = event_id
                        event_tennis_set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        # advanced_team = 'home' if get_value(cells[1].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_tennis_set.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_tennis_set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 全場獨贏
                        de_home_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[1].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_tennis_set.draw = de_draw_odds
                        event_tennis_set.information.league += f'-{cells[1].cssselect("div:nth-child(1)")[0].text or ""}'
                        data.aphdc.append(event_tennis_set)
                    elif sport_type is GameType.hockey:
                        event_hk_set = spec.ApHdc()
                        event_hk_set.CopyFrom(event)
                        event_hk_set.game_id = f'{event_id}10'
                        event_hk_set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_hk_set.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_hk_set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))

                        # 全場獨贏
                        de_home_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[1].cssselect('ul:nth-child(3) > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(3)'), '0')
                            event_hk_set.draw = de_draw_odds
                        event_hk_set.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                        event_hk_set.information.league += f'-{cells[1].cssselect("div:nth-child(1)")[0].text or ""}'
                        data.aphdc.append(event_hk_set)
                    elif sport_type is GameType.eSport:
                        event_esport_set = spec.ApHdc()
                        event_esport_set.CopyFrom(event)
                        event_esport_set.game_id = event_id
                        event_esport_set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        for game in cells[0].cssselect('div.show'):
                            event_esport_game = spec.ApHdc()
                            event_esport_game.CopyFrom(event_esport_set)
                            postfix = game.cssselect('div.GLOddsPcgame_T')[0].text
                            event_esport_game.information.league += f'-{postfix}'
                            event_esport_game.game_id = game.attrib['rel'].replace('_', '') + str(sum(ord(c) for c in postfix) % 1000)
                            esport_game_type = game.cssselect('ul:nth-child(1)')[0].attrib['pktype']
                            if esport_game_type == '100008':
                                # 全場讓分
                                advanced_team = 'home' if get_value(cells[0].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                                zf_line = '0'
                                zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                                if zf_line:
                                    home_zf_odds = get_value(cells[0].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                                    away_zf_odds = get_value(cells[0].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                                else:
                                    home_zf_odds = '0'
                                    away_zf_odds = '0'
                                event_esport_set.twZF.CopyFrom(
                                    spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                                odds=home_zf_odds),
                                            awayZF=spec.typeZF(line=zf_away_line,
                                                                odds=away_zf_odds)))
                                data.aphdc.append(event_esport_game)
                            elif esport_game_type == '100009':
                                # 全場大小
                                ds_line = get_value(cells[0].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '').replace('大 ', '')
                                ds_over_odds = get_value(cells[0].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                                ds_under_odds = get_value(cells[0].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                                if not ds_line:
                                    ds_line = '0'
                                    ds_over_odds = '0'
                                    ds_under_odds = '0'
                                if not re.search(r'[+./-]', ds_line):
                                    ds_line += '+0'
                                event_esport_set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                                data.aphdc.append(event_esport_game)

                elif game_type_id == 3:
                    if sport_type is GameType.basketball:
                        event_full_15min = spec.ApHdc()
                        event_full_15min.CopyFrom(event)
                        event_full_15min.game_id = f'{event_id}{33}'
                        event_full_15min.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        time_range = cells[1].cssselect('div:nth-child(1)')[0].text
                        event_full_15min.information.league += f'-({time_range})'
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul:nth-child(1) > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_full_15min.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[1].cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_full_15min.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 全場獨贏
                        de_home_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[1].cssselect('ul:nth-child(3) > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[1].cssselect('ul:nth-child(3) > li.btn_GLOdds:nth-child(3)'), '0')
                            event_full_15min.draw = de_draw_odds
                        event_full_15min.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                        data.aphdc.append(event_full_15min)
                    elif sport_type is GameType.baseball:
                        event_17set = spec.ApHdc()
                        event_17set.CopyFrom(event)
                        event_17set.information.league += '(1~7局)投注'
                        event_17set.game_id = f'{event_id}17'
                        event_17set.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_17set.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 全場大小
                        ds_line = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_17set.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 一輸
                        # advanced_team = 'home' if get_value(cells[3].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        # home_zf_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        # away_zf_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        # event_17set.esre.CopyFrom(
                        #     spec.Esre(let=spec.whichTeam.home if advanced_team
                        #               else spec.whichTeam.away,
                        #               home=home_zf_odds,
                        #               away=away_zf_odds))
                        # 全場單雙
                        # odd_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        # even_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        # event_17set.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                        data.aphdc.append(reverseTeam(event_17set))
                elif game_type_id == 4:
                    # 波膽
                    if sport_type is GameType.soccer:
                        event_correct_score = spec.ApHdc()
                        event_correct_score.CopyFrom(event)
                        event_correct_score.game_id = event_id
                        event_correct_score.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 全場波膽
                        correct_score = {f'{home}-{away}': '0' for home, away in product([0, 1, 2, 3, 4], repeat=2)}
                        correct_score['other'] = '0'
                        for odds_pair in event_doc.cssselect('li.btn_GLOdds, td.btn_GLOdds'):
                            game_score = odds_pair.cssselect('div.GLOdds_T')[0].text.replace(' ', '')
                            if '-' not in game_score:
                                game_score = 'other'
                            game_odds = get_value(odds_pair.cssselect('div.GLOdds_B'), '0')
                            correct_score[game_score] = game_odds
                        event_correct_score.multi = json.dumps(correct_score)
                        data.aphdc.append(event_correct_score)
                    elif sport_type is GameType.basketball:
                        event_total_goal = spec.ApHdc()
                        event_total_goal.CopyFrom(event)
                        radix = re.sub(r'[a-z]', '', row.attrib['ridx'])
                        event_total_goal.game_id = f'{event_id}{radix}'
                        event_total_goal.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 總得分
                        odds_rows = cells[1].getchildren()
                        for i in range(len(odds_rows) // 2):
                            title = odds_rows[i * 2].text
                            odds = odds_rows[i * 2 + 1]
                            # 全場大小
                            ds_line = get_value(odds.cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '').replace('大 ', '')
                            ds_over_odds = get_value(odds.cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            ds_under_odds = get_value(odds.cssselect('ul:nth-child(1) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                            if not ds_line:
                                ds_line = '0'
                                ds_over_odds = '0'
                                ds_under_odds = '0'
                            if not re.search(r'[+./-]', ds_line):
                                ds_line += '+0'
                            event_total_goal.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                            # 全場單雙
                            odd_odds = get_value(odds.cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            even_odds = get_value(odds.cssselect('ul:nth-child(2) > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                            event_total_goal.sd.CopyFrom(spec.onetwo(home=odd_odds, away=even_odds))
                            event_total_period = spec.ApHdc()
                            event_total_period.CopyFrom(event_total_goal)
                            event_total_period.game_id = f'{event_id}01{i}'
                            event_total_period.information.league += f'-{title}-團隊總得分'
                            data.aphdc.append(event_total_period)
                    elif sport_type is GameType.baseball:
                        event_first_set_goal = spec.ApHdc()
                        event_first_set_goal.CopyFrom(event)
                        radix = re.sub(r'[a-z]', '', row.attrib['ridx'])
                        event_first_set_goal.game_id = f'{event_id}{radix}11'
                        event_first_set_goal.information.league += '-第一局-得分'
                        event_first_set_goal.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        # 第一局
                        # 得分讓分
                        advanced_team = 'home' if get_value(cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[1].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_first_set_goal.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 得分大小
                        ds_line = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[2].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_first_set_goal.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 得分獨贏
                        de_home_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[3].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[3].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_first_set_goal.draw = de_draw_odds
                        event_first_set_goal.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                        data.aphdc.append(reverseTeam(event_first_set_goal))

                        event_first_set_hit = spec.ApHdc()
                        event_first_set_hit.CopyFrom(event)
                        event_first_set_hit.game_id = f'{event_id}{radix}12'
                        event_first_set_hit.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        event_first_set_hit.information.league += '-第一局-安打'
                        # 安打讓分
                        advanced_team = 'home' if get_value(cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                        zf_line = cells[4].cssselect('ul.GLOdds > li:nth-child(1) > div.GLOdds_L')[0].text or cells[4].cssselect('ul.GLOdds > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                        zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                        if zf_line:
                            home_zf_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                            away_zf_odds = get_value(cells[4].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        else:
                            home_zf_odds = '0'
                            away_zf_odds = '0'
                        event_first_set_hit.twZF.CopyFrom(
                            spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                        odds=home_zf_odds),
                                    awayZF=spec.typeZF(line=zf_away_line,
                                                        odds=away_zf_odds)))
                        # 安打大小
                        ds_line = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[5].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_first_set_hit.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        # 安打獨贏
                        de_home_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1)'), '0')
                        de_away_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2)'), '0')
                        if cells[6].cssselect('ul.GLOdds > li:nth-child(3)'):
                            de_draw_odds = get_value(cells[6].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(3)'), '0')
                            event_first_set_hit.draw = de_draw_odds
                        event_first_set_hit.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                        data.aphdc.append(reverseTeam(event_first_set_hit))

                elif game_type_id == 5:
                    # 入球數
                    if sport_type is GameType.soccer:
                        event_score_sum = spec.ApHdc()
                        event_score_sum.CopyFrom(event)
                        event_score_sum.game_id = event_id
                        event_score_sum.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        score_sum = {
                            '0-1': '0',
                            '2-3': '0',
                            '4-6': '0',
                            '7+': '0',
                        }
                        odds = row.cssselect('td[id]')[:4]
                        score_sum['0-1'] = odds[0].text or '0'
                        score_sum['2-3'] = odds[1].text or '0'
                        score_sum['4-6'] = odds[2].text or '0'
                        score_sum['7+'] = odds[3].text or '0'
                        score_sum_1st_half = {
                            '0': '0',
                            '1': '0',
                            '2': '0',
                            '3+': '0',
                        }
                        score_sum['0'] = odds[4].text or '0'
                        score_sum['1'] = odds[5].text or '0'
                        score_sum['2'] = odds[6].text or '0'
                        score_sum['3+'] = odds[7].text or '0'
                        event_score_sum_1st_half = spec.ApHdc()
                        event_score_sum_1st_half.CopyFrom(event_score_sum)
                        event_score_sum_1st_half.game_id = f'{event_id}1'
                        event_score_sum.game_type = Period.FIRST_HALF.value
                        event_score_sum.multi = json.dumps(score_sum)
                        event_score_sum_1st_half.multi = json.dumps(score_sum_1st_half)
                        data.aphdc.append(event_score_sum)
                        data.aphdc.append(event_score_sum_1st_half)
                    elif sport_type is GameType.baseball:
                        event_total_goal = spec.ApHdc()
                        event_total_goal.CopyFrom(event)
                        event_total_goal.game_id = event_id + str(sum(ord(c) for c in event.information.home.team_name) % 1000)
                        event_total_goal.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        event_total_goal.information.league += f'-團隊總得分'
                        # 總得分
                        # 大小
                        ds_line = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                        ds_over_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                        ds_under_odds = get_value(cells[1].cssselect('ul.GLOdds > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                        if not ds_line:
                            ds_line = '0'
                            ds_over_odds = '0'
                            ds_under_odds = '0'
                        if not re.search(r'[+./-]', ds_line):
                            ds_line += '+0'
                        event_total_goal.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                        data.aphdc.append(reverseTeam(event_total_goal))

                elif game_type_id == 6:
                    # 半全場
                    if sport_type is GameType.soccer:
                        event_half_full = spec.ApHdc()
                        event_half_full.CopyFrom(event)
                        event_half_full.game_id = event_id
                        event_half_full.game_type = Ku.Mapping.get_game_type(sport_type, game_type_id, live=live).value
                        half_full_score = {f'{first}{full}': '0' for first, full in product(['H', 'D', 'A'], repeat=2)}
                        odds = row.cssselect('td[id]')
                        half_full_score['HH'] = odds[0].text
                        half_full_score['HD'] = odds[1].text
                        half_full_score['HA'] = odds[2].text
                        half_full_score['DH'] = odds[3].text
                        half_full_score['DD'] = odds[4].text
                        half_full_score['DA'] = odds[5].text
                        half_full_score['AH'] = odds[6].text
                        half_full_score['AD'] = odds[7].text
                        half_full_score['AA'] = odds[8].text
                        event_half_full.multi = json.dumps(half_full_score)
                        data.aphdc.append(event_half_full)

            except Exception:
                with open(f'logs/{sport_type.value}_{game_type_id}_解析錯誤.log', 'a+', encoding='utf-8') as log:
                    log.write(datetime.now().isoformat())
                    log.write(traceback.format_exc())
                    log.write('\n')
    return data

def compute_zf_line(line, advanced_team):
    if not line:
        line = '0'
    if line and line[-2:] == '0.5' and '/' not in line:
        line = f'{line[:-2]}-100'
    elif not re.search(r'[+./-]', line):
        line += '+0'
    if advanced_team == 'home':
        zf_home_line = f'-{line}'
        zf_away_line = f'+{line}'
    else:
        zf_home_line = f'+{line}'
        zf_away_line = f'-{line}'
    return zf_home_line, zf_away_line

def get_value(element, default, index=0):
    try:
        if element:
            return (element[index].text or default).strip()
    except (IndexError, TypeError):
        pass
    return default

def reverseTeam(event):
    event.information.home.team_name, event.information.home.cn_name, event.information.home.en_name, event.information.away.team_name, event.information.away.cn_name, event.information.away.en_name = event.information.away.team_name, event.information.away.cn_name, event.information.away.en_name, event.information.home.team_name, event.information.home.cn_name, event.information.home.en_name
    if event.HasField('twZF'):
        event.twZF.homeZF.line, event.twZF.homeZF.odds, event.twZF.awayZF.line, event.twZF.awayZF.odds = event.twZF.awayZF.line, event.twZF.awayZF.odds, event.twZF.homeZF.line, event.twZF.homeZF.odds
    if event.HasField('de'):
        event.de.home, event.de.away = event.de.away, event.de.home
    if event.HasField('esre'):
        if event.esre.let == spec.whichTeam.home:
            event.esre.let = spec.whichTeam.away
        else:
            event.esre.let = spec.whichTeam.home
        event.esre.home, event.esre.away = event.esre.away, event.esre.home
    return event

def read_mapping(sport_id):
    mapping = {}
    sport_name = Ku.Mapping.sport_id_name.get(sport_id)
    if sport_name:
        today = datetime.now()
        date_str = today.strftime('%Y%m%d')
        yesterday_date_str = (today - timedelta(days=1)).strftime('%Y%m%d')
        if os.path.exists(f'mapping/{sport_name}_gameTime_{yesterday_date_str}.txt') and today.hour < 8:
            with open(f'mapping/{sport_name}_gameTime_{yesterday_date_str}.txt', encoding='utf-8') as game_time_data:
                for line in game_time_data:
                    if line:
                        try:
                            data = json.loads(line)
                            mapping[data['id']] = data
                        except JSONDecodeError:
                            print('mapping parsing error:', line)
        if os.path.exists(f'mapping/{sport_name}_gameTime_{date_str}.txt'):
            with open(f'mapping/{sport_name}_gameTime_{date_str}.txt', encoding='utf-8') as game_time_data:
                for line in game_time_data:
                    if line:
                        try:
                            data = json.loads(line)
                            mapping[data['id']] = data
                        except JSONDecodeError:
                            print('mapping parsing error:', line)
        return mapping

def game_class_convert(game_type, league):
    """Specify game class based on game type and league name"""
    game_class = None
    if game_type is GameType.baseball:
        if '美國職棒' in league or 'MLB' in league:
            game_class = GameType.mlb
        elif '日本職業棒球' in league or 'NPB' in league:
            game_class = GameType.npb
        elif 'CPBL' in league:
            game_class = GameType.cpbl
        else:
            game_class = GameType.kbo
    elif game_type == GameType.basketball:
        if ('美國職業籃球' in league or 'NBA' in league) and ('WNBA' not in league and 'Summer League' not in league):
            game_class = GameType.basketball
        else:
            game_class = GameType.otherbasketball
    elif game_type is GameType.hockey:
        game_class = GameType.hockey
    elif game_type is GameType.football:
        game_class = GameType.football
    elif game_type is GameType.tennis:
        game_class = GameType.tennis
    elif game_type is GameType.eSport:
        game_class = GameType.eSport
    elif re.search(r'(歐洲冠軍|歐足聯歐洲聯賽|歐洲盃|美洲國家盃\(在巴西\)|亞足聯冠軍)', league) and '外圍賽' not in league:
        game_class = GameType.UCL
    elif game_type is GameType.soccer:
        game_class = GameType.soccer
    else:
        game_class = GameType.other
    return game_class.value


def query_sport_event_time(sport_type_id):
    try:
        resp = requests.post('http://52.198.102.230:56786/multiSourceKanban',
                          data={
                              'date': datetime.now().strftime('%Y-%m-%d'),
                              'category': sport_type_id,
                              'type': '7'
                          }, timeout=5)
        if resp.ok:
            event_info = resp.json()
            event_time_map = {}
            for event in event_info.values():
                home_team_datacenter = re.sub(r'\s', '', event['hTeamName'])
                away_team_datacenter = re.sub(r'\s', '', event['aTeamName'])
                event_time_map[f'{home_team_datacenter}{away_team_datacenter}'] = event
            return event_time_map
    except Exception:
        traceback.print_exc()
    return {}


def search_event_time(home_team, away_team, event_map):
    home_team = re.sub(r'-女\b', '(女)', home_team)
    away_team = re.sub(r'-女\b', '(女)', away_team)
    event_info = event_map.get(f'{home_team}{away_team}') or event_map.get(f'{away_team}{home_team}') or {}
    return event_info.get('gameTime')


if __name__ == '__main__':
    start_time = perf_counter()
    with open('ku_sc_full.html', encoding='utf-8') as f:
        result = parse(f.read(), '11', 0, live=False)
        end_time = perf_counter()
        print(len(result.aphdc), end_time - start_time)
        print(text_format.MessageToString(result, as_utf8=True))
        with open('test.log', 'w', encoding='utf-8') as log:
            log.write(text_format.MessageToString(result, as_utf8=True))
