# coding: utf-8

from datetime import datetime
import traceback
from pyquery import PyQuery as pq
from google.protobuf import text_format
import APHDC_pb2 as spec

def parse(html):
    data = spec.ApHdcArr()
    doc = pq(html)
    event_list_doc = doc('.gameList')
    for event_doc in event_list_doc:
        league_name = event_doc.cssselect('.btn_GLT li:nth-child(2)')[0].text
        rows = event_doc.cssselect('tr.GLInList')
        for row in rows:
            try:
                event_id = row.attrib['rel'] + row.attrib.get('st')
                cells = row.cssselect('td')
                if cells[0].cssselect('.st span'):
                    date = cells[0].cssselect('.st span')[0].text
                    date_time = cells[0].cssselect('.rt font')[0].text
                event_time = datetime.strptime(f'{date} {date_time}', '%m-%d %H:%M')
                home_team = cells[0].cssselect('li:nth-child(2) font')[0].text
                away_team = cells[0].cssselect('li:nth-child(2) font')[1].text
                event = spec.ApHdc(
                    source='TX',
                    game_class='soccer',
                    ip='ku_python',
                    event_time=event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    source_updatetime=datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S.%f')[:-3],
                    live='false',
                    information=spec.information(
                        league=league_name,
                        home=spec.infoHA(team_name=home_team),
                        away=spec.infoHA(team_name=away_team)
                    )
                )
                event_full = spec.ApHdc()
                event_1st = spec.ApHdc()
                event_full.CopyFrom(event)
                event_1st.CopyFrom(event)
                # 全場
                event_full.game_id = event_id
                event_full.game_type = 'full'
                # 全場讓分
                advanced_team = 'home' if cells[1].cssselect('ul > li:nth-child(1) > div.GLOdds_L') else 'away'
                zf_line = cells[1].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text or cells[1].cssselect('ul > li:nth-child(2) > div.GLOdds_L')[0].text
                zf_home_line = zf_line
                zf_away_line = zf_line
                if advanced_team == 'home':
                    zf_home_line = f'-{zf_line}'
                    zf_away_line = f'+{zf_line}'
                else:
                    zf_home_line = f'+{zf_line}'
                    zf_away_line = f'-{zf_line}'
                home_zf_odds = cells[1].cssselect('ul > li:nth-child(1) > div.GLOdds_R')[0].text
                away_zf_odds = cells[1].cssselect('ul > li:nth-child(2) > div.GLOdds_R')[0].text
                event_full.twZF.CopyFrom(
                    spec.twZF(homeZF=spec.typeZF(line=zf_home_line,
                                                odds=home_zf_odds),
                            awayZF=spec.typeZF(line=zf_away_line,
                                                odds=away_zf_odds)))
                # 全場大小
                ds_line = cells[2].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text
                ds_over_odds = cells[2].cssselect('ul > li:nth-child(1) > div.GLOdds_R')[0].text
                ds_under_odds = cells[2].cssselect('ul > li:nth-child(2) > div.GLOdds_R')[0].text
                event_full.twDS.CopyFrom(spec.typeDS(line=ds_line, over=ds_over_odds, under=ds_under_odds))
                # 全場獨贏
                de_home_odds = (cells[3].cssselect('ul > li:nth-child(1)')[0].text or '0').strip()
                de_away_odds = (cells[3].cssselect('ul > li:nth-child(2)')[0].text or '0').strip()
                if cells[3].cssselect('ul > li:nth-child(3)'):
                    de_draw_odds = (cells[3].cssselect('ul > li:nth-child(3)')[0].text or '0').strip()
                    event_full.draw = de_draw_odds
                event_full.de.CopyFrom(spec.onetwo(home=de_home_odds, away=de_away_odds))
                # 上半場
                event_1st.game_id = f'{event_id}1'
                event_1st.game_type = '1st half'
                # 上半場讓分
                advanced_team_1st = 'home' if cells[4].cssselect('ul > li:nth-child(1) > div.GLOdds_L') else 'away'
                zf_1st_line = cells[4].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text or cells[4].cssselect('ul > li:nth-child(2) > div.GLOdds_L')[0].text
                zf_1st_home_line = zf_1st_line
                zf_1st_away_line = zf_1st_line
                if advanced_team_1st == 'home':
                    zf_1st_home_line = f'-{zf_line}'
                    zf_1st_away_line = f'+{zf_line}'
                else:
                    zf_1st_home_line = f'+{zf_line}'
                    zf_1st_away_line = f'-{zf_line}'
                home_zf_1st_odds = cells[4].cssselect('ul > li:nth-child(1) > div.GLOdds_R')[0].text
                away_zf_1st_odds = cells[4].cssselect('ul > li:nth-child(2) > div.GLOdds_R')[0].text
                event_1st.twZF.CopyFrom(
                    spec.twZF(homeZF=spec.typeZF(line=zf_1st_home_line,
                                                odds=home_zf_1st_odds),
                            awayZF=spec.typeZF(line=zf_1st_away_line,
                                                odds=away_zf_1st_odds)))
                # 上半場大小
                ds_1st_line = cells[5].cssselect('ul > li:nth-child(1) > div.GLOdds_L')[0].text
                ds_1st_over_odds = cells[5].cssselect('ul > li:nth-child(1) > div.GLOdds_R')[0].text
                ds_1st_under_odds = cells[5].cssselect('ul > li:nth-child(2) > div.GLOdds_R')[0].text
                event_1st.twDS.CopyFrom(spec.typeDS(line=ds_1st_line, over=ds_1st_over_odds, under=ds_1st_under_odds))
                # 上半場獨贏
                de_1st_home_odds = cells[5].cssselect('ul > li:nth-child(1)')[0].text.strip()
                de_1st_away_odds = cells[5].cssselect('ul > li:nth-child(2)')[0].text.strip()
                if cells[5].cssselect('ul > li:nth-child(3)'):
                    de_1st_draw_odds = cells[5].cssselect('ul > li:nth-child(3)')[0].text.strip()
                    event_1st.draw = de_1st_draw_odds
                event_1st.de.CopyFrom(spec.onetwo(home=de_1st_home_odds, away=de_1st_away_odds))
                data.aphdc.extend([event_full, event_1st])
            except Exception as ex:
                traceback.print_exc()
    return data

if __name__ == '__main__':
    with open('test.html', encoding='utf-8') as f:
        result = parse(f.read())
        print(text_format.MessageToString(result, as_utf8=True))
