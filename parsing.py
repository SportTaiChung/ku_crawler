# coding: utf-8

from datetime import datetime
import json
from json.decoder import JSONDecodeError
import traceback
from pyquery import PyQuery as pq
from google.protobuf import text_format
import APHDC_pb2 as spec

def parse(html):
    try:
        with open('event_time.json', encoding='utf-8') as f:
            event_time_table = json.load(f)
    except JSONDecodeError:
        event_time_table = {}
    data = spec.ApHdcArr()
    doc = pq(html)
    event_list_doc = doc('.gameList')
    event_rel_id = ''
    date = ''
    date_time = ''
    home_score = '0'
    away_score = '0'
    for event_doc in event_list_doc:
        league_name = event_doc.cssselect('.btn_GLT li:nth-child(2)')[0].text
        rows = event_doc.cssselect('tr.GLInList')
        for row in rows:
            try:
                new_event_rel_id = row.attrib['rel']
                event_id = row.attrib['rel'] + row.attrib.get('st')
                cells = row.cssselect('td')
                # event_time = datetime.strptime(f'{date} {date_time}', '%m-%d %H:%M')
                home_team = cells[0].cssselect('li:nth-child(2) font')[0].text
                away_team = cells[0].cssselect('li:nth-child(2) font')[1].text
                event_info = event_time_table.get(f'{home_team}|{away_team}')
                if not event_info:
                    continue
                event_time = f'2021-{event_info["date"]} {event_info["time"]}:00'
                if new_event_rel_id != event_rel_id:
                    if cells[0].cssselect('.st span'):
                        date = cells[0].cssselect('.st span')[0].text
                        date_time = cells[0].cssselect('.rt font')[0].text
                    live_time = f'{date} {date_time or ""}'.replace("'", '').replace('半場', '').replace('休息', '')
                    home_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(1)')
                    home_score = home_score_element[0].text if home_score_element else '0'
                    away_score_element = cells[0].cssselect('.GLInTBox_Score > div:nth-child(2)')
                    away_score = away_score_element[0].text if away_score_element else '0'
                    event_rel_id = new_event_rel_id
                event = spec.ApHdc(
                    source='TX',
                    game_class='soccer',
                    ip='ku_python',
                    # event_time=event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    event_time=event_time,
                    source_updatetime=datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S.%f')[:-3],
                    live='true',
                    live_time=live_time,
                    information=spec.information(
                        league=league_name,
                        home=spec.infoHA(team_name=home_team),
                        away=spec.infoHA(team_name=away_team)
                    ),
                    score=spec.score(home=home_score, away=away_score)
                )
                event_full = spec.ApHdc()
                event_1st = spec.ApHdc()
                event_full.CopyFrom(event)
                event_1st.CopyFrom(event)
                # 全場
                event_full.game_id = event_id
                event_full.game_type = 'live full'
                # 全場讓分
                advanced_team = 'home' if get_value(cells[1].cssselect('ul > li:nth-child(1) > div.GLOdds_L'), '') else 'away'
                zf_line = cells[1].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                zf_home_line, zf_away_line = compute_zf_line(zf_line, advanced_team)
                home_zf_odds = get_value(cells[1].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                away_zf_odds = get_value(cells[1].cssselect('ul > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                event_full.twZF.CopyFrom(
                    spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                odds=home_zf_odds),
                            awayZF=spec.typeZF(line=zf_away_line,
                                                odds=away_zf_odds)))
                # 全場大小
                ds_line = get_value(cells[2].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '')
                ds_over_odds = get_value(cells[2].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0')
                ds_under_odds = get_value(cells[2].cssselect('ul > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0')
                if not ds_line:
                    ds_line = '0'
                    ds_over_odds = '0'
                    ds_under_odds = '0'
                if '.5' not in ds_line and '/' not in ds_line:
                    ds_line += '+0'
                event_full.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                # 全場獨贏
                de_home_odds = get_value(cells[3].cssselect('ul > li.btn_GLOdds:nth-child(1)'), '0').strip()
                de_away_odds = get_value(cells[3].cssselect('ul > li.btn_GLOdds:nth-child(2)'), '0').strip()
                if cells[3].cssselect('ul > li:nth-child(3)'):
                    de_draw_odds = get_value(cells[3].cssselect('ul > li.btn_GLOdds:nth-child(3)'), '0').strip()
                    event_full.draw = de_draw_odds
                event_full.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                # 上半場
                event_1st.game_id = f'{event_id}1'
                event_1st.game_type = 'live 1st half'
                # 上半場讓分
                advanced_team_1st = 'home' if cells[4].cssselect('ul > li:nth-child(1) > div.GLOdds_L') else 'away'
                zf_1st_line = cells[4].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text or cells[4].cssselect('ul > li:nth-child(2) > div.GLOdds_L')[0].text or '0'
                zf_1st_home_line, zf_1st_away_line = compute_zf_line(zf_1st_line, advanced_team_1st)
                home_zf_1st_odds = get_value(cells[4].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0').strip()
                away_zf_1st_odds = get_value(cells[4].cssselect('ul > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0').strip()
                event_1st.twZF.CopyFrom(
                    spec.twZF(homeZF=spec.typeZF(line=zf_1st_home_line,
                                                odds=home_zf_1st_odds),
                            awayZF=spec.typeZF(line=zf_1st_away_line,
                                                odds=away_zf_1st_odds)))
                # 上半場大小
                ds_1st_line = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_L'), '0').strip()
                ds_1st_over_odds = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(1) > div.GLOdds_R'), '0').strip()
                ds_1st_under_odds = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(2) > div.GLOdds_R'), '0').strip()
                if not ds_1st_line:
                    ds_1st_line = '0'
                    ds_1st_over_odds = '0'
                    ds_1st_under_odds = '0'
                if '.5' not in ds_1st_line and '/' not in ds_1st_line:
                    ds_1st_line += '+0'
                event_1st.twDS.CopyFrom(spec.typeDS(line=ds_1st_line, over=ds_1st_over_odds, under=ds_1st_under_odds))
                # 上半場獨贏
                de_1st_home_odds = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(1)'), '0').strip()
                de_1st_away_odds = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(2)'), '0').strip()
                if cells[5].cssselect('ul > li:nth-child(3)'):
                    de_1st_draw_odds = get_value(cells[5].cssselect('ul > li.btn_GLOdds:nth-child(3)'), '0').strip()
                    event_1st.draw = de_1st_draw_odds
                event_1st.de.CopyFrom(spec.onetwo(home=de_1st_home_odds, away=de_1st_away_odds))
                data.aphdc.extend([event_full, event_1st])
            except Exception as ex:
                traceback.print_exc()
    return data

def compute_zf_line(line, advanced_team):
    if line and line[-2:] == '0.5' and '/' not in line:
        line = f'{line[:-2]}-100'
    elif '.' not in line and '/' not in line:
        line += '+0'
    if advanced_team == 'home':
        zf_home_line = f'-{line}'
        zf_away_line = f'+{line}'
    else:
        zf_home_line = f'+{line}'
        zf_away_line = f'-{line}'
    return zf_home_line, zf_away_line

def get_value(element, default):
    if element:
        return element[0].text or default
    return default

if __name__ == '__main__':
    with open('test.html', encoding='utf-8') as f:
        result = parse(f.read())
        print(text_format.MessageToString(result, as_utf8=True))
