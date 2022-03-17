# coding: utf-8
from enum import Enum
import re


EXCLUDED_LEAGUES = re.compile(r'([丙丁戊][級組]|U20|U1|特定15分鐘|夢幻對壘|預備|後備|沙灘|室內|友誼賽|土庫曼青年聯賽|蒲隆地共和國超級聯賽|保加利亞乙|烏克蘭聯賽U21|印度果阿超級聯賽|愛沙尼亞乙|烏茲別克|哈薩克|澳洲西方超級聯賽- 女子|馬拉威 TNM 超級聯賽|津巴布韋超級聯賽|立陶宛乙|中華台北甲|總入球|特別投注|角球|罰牌|分鐘)')


class Source(Enum):
    TX = 'TX'
    KU = 'KU'


class Site(Enum):
    THA = 'tha'
    LEO = 'leo'


class GameType(Enum):
    # baseball not used in protobuf game class
    baseball = 'baseball'
    mlb = 'mlb'    # 美棒
    npb = 'npb'    # 日棒
    cpbl = 'cpbl'  # 台棒
    kbo = 'kbo'    # 韓棒和其他
    basketball = 'basketball'  # NBA
    otherbasketball = 'otherbasketball'  # 其他非NBA籃球
    tennis = 'tennis'
    hockey = 'hockey'
    football = 'football'
    eSport = 'eSport'
    soccer = 'soccer'
    UCL = 'UCL'  # 歐洲冠軍足球
    pingpong = 'other'
    volleyball = 'other'
    other = 'other'


class GameCategory(Enum):
    ZF = 'zf'  # spread 讓分
    DS = 'ds'  # total 大小
    DE = 'de'  # money line 獨贏
    ESRE = 'esre'  # 一輸二贏
    SD = 'sd'  # parity 單雙數


class PlayType(Enum):
    TODAY = 'today'
    EARLY = 'early'
    TEAM_TOTAL = 'team totals'
    LIVE = 'live'
    TEAM_TOTAL_LIVE = 'team totals live'


class Period(Enum):
    FULL = 'full'
    FIRST_HALF = '1st half'
    SECOND_HALF = '2nd half'
    LIVE = 'live'
    LIVE_FULL = 'live full'
    LIVE_FIRST_HALF = 'live 1st half'
    # 波膽
    CORRECT_SCORE = 'pd full'
    CORRECT_SCORE_1ST_HALF = 'pd 1st half'
    CORRECT_SCORE_2ND_HALF = 'pd 2nd half'
    CORRECT_SCORE_LIVE = 'pd live full'
    CORRECT_SCORE_LIVE_1ST_HALF = 'pd live 1st half'
    CORRECT_SCORE_LIVE_2ND_HALF = 'pd live 2nd half'
    # 半全場
    HALF_FULL_SCORE = 'hf full'
    HALF_FULL_SCORE_LIVE = 'hf live full'
    # 入球數
    SCORE_SUM = 'tg full'
    SCORE_SUM_1ST_HALF = 'tg 1st half'
    SCORE_SUM_LIVE = 'tg live full'
    SCORE_SUM_LIVE_1ST_HALF = 'tg live 1st half'
    # 多玩法
    MULTI = 'multi'


class Ku:
    class Selector:
        # sport category
        FAVORITE = 'btnFV'
        COMINGSOON = 'btnCS'
        TV_LIVING = 'btnTV'
        # EUROPE_FIVE_LEAGUES = 'btnEU' ## 冠軍聯賽
        CHAMPION = 'btnCH' ## 冠軍聯賽
        OLYMPIC = 'btnOP'
        SOCCER = 'btnSC'
        BASKETBALL = 'btnBK'
        BASEBALL = 'btnBB'
        TENNIS = 'btnTN'
        ICE_HOCKEY = 'btnIH'
        VOLLEYBALL = 'btnVL'
        BADMINTON = 'btnBM'
        ESPORT = 'btnES'
        FOOTBALL = 'btnAF'
        TABLE_TENNIS = 'btnTT'
        PINBALL = 'btnPB'
        HANDBALL = 'btnHB'
        WATERBALL = 'btnWB'

    class Value:
        pass

    class Mapping:
        sport_id_name = {
            '11': '足球',
            '51': '冠軍聯賽',
            '52': '五大聯賽',
            '53': '奧運會',
            '12': '籃球',
            '13': '棒球',
            '14': '網球',
            '15': '冰球',
            '16': '排球',
            '17': '羽毛球',
            '18': '電子競技',
            '19': '美足',
            '20': '撞球',
            '21': '乒乓球',
            '22': '手球',
            '23': '水球'
        }
        sport_game_class = {
            '11': 'soccer',
            '51': 'soccer',
            '52': 'soccer',
            '53': 'soccer',
            '12': 'basketball',
            '13': 'baseball',
            '14': 'tennis',
            '15': 'hockey',
            '16': 'volleyball',
            '17': '羽毛球',
            '18': 'eSport',
            '19': 'football',
            '20': '撞球',
            '21': 'pingpong',
            '22': '手球',
            '23': '水球'
        }

        @classmethod
        def get_sport_category_parameter(cls, sport_type_id):
            # sport category parameter
            FAVORITE = ('fv', 99)
            COMINGSOON = ('cs', 100)
            TV_LIVING = ('tv', 54)
            CHAMPION = ('ch', 51) ## 冠軍聯賽
            # EUROPE_FIVE_LEAGUES = ('eu', 52) ## 冠軍聯賽
            OLYMPIC = ('op', 53)
            SOCCER = ('sc', 11)
            BASKETBALL = ('bk', 12)
            BASEBALL = ('bb', 13)
            TENNIS = ('tn', 14)
            ICE_HOCKEY = ('ih', 15)
            VOLLEYBALL = ('vl', 16)
            BADMINTON = ('bm', 17)
            ESPORT = ('es', 18)
            FOOTBALL = ('af', 19)
            PINBALL = ('pb', 20)
            TABLE_TENNIS = ('tt', 21)
            HANDBALL = ('hb', 22)
            WATERBALL = ('hb', 23)

            sport_type_id_parameter_mapping = {
                '51': CHAMPION,
                # '52': cls.Value.EUROPE_FIVE_LEAGUES,
                '53': OLYMPIC,
                '11': SOCCER,
                '12': BASKETBALL,
                '13': BASEBALL,
                '14': TENNIS,
                '15': ICE_HOCKEY,
                '16': VOLLEYBALL,
                '17': BADMINTON,
                '18': ESPORT,
                '19': FOOTBALL,
                '20': PINBALL,
                '21': TABLE_TENNIS,
                '22': HANDBALL,
                '23': WATERBALL
            }
            return sport_type_id_parameter_mapping.get(sport_type_id, ('', 0))

        @staticmethod
        def get_exchange_name(sport_type_id):
            sport_type_id_exchange_mapping = {
                '11': 'KU_SC',
                '51': 'KU_SC',
                '52': 'KU_SC',
                '53': 'KU_SC',
                '12': 'KU_BK',
                '13': 'KU_BS',
                '14': 'KU_TN',
                '15': 'KU_HC',
                '16': 'KU_BK',
                '17': 'KU_BK',
                '18': 'KU_ES',
                '19': 'KU_FB',
                '20': 'KU_BK',
                '21': 'KU_BK',
                '22': 'KU_BK',
                '23': 'KU_BK'
            }
            return sport_type_id_exchange_mapping.get(sport_type_id, 'KU_BK')
        
        @staticmethod
        def get_sport_type_id(sport_id, league_name):
            if sport_id in ('11', '51', '52'):
                if re.search(r'(歐洲冠軍|歐足聯歐洲聯賽|歐洲盃|美洲國家盃\(在巴西\)|亞足聯冠軍)', league_name) and '外圍賽' not in league_name:
                    return '20'
                return '10'
            if sport_id == '12':
                if 'NBA' in league_name or '美國職業' in league_name:
                    return '6'
            elif sport_id == '13':
                if '美國' in league_name or 'MLB' in league_name:
                    return '1'
                elif '日本' in league_name or 'NPB' in league_name:
                    return '2'
                elif '中華' in league_name or 'CPBL' in league_name:
                    return '3'
                else:
                    return '4'
            return '14'

        @staticmethod
        def get_game_type(sport_type, game_type_id, half=False, live=False):
            game_type = Period.FULL if not live else Period.LIVE_FULL
            if sport_type is GameType.soccer:
                if game_type_id in (0, 99, -1):
                    game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 1:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 2:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 3:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 4:
                    if live:
                        game_type = Period.CORRECT_SCORE_LIVE if not half else Period.CORRECT_SCORE_1ST_HALF
                    else:
                        game_type = Period.CORRECT_SCORE if not half else Period.CORRECT_SCORE_1ST_HALF
                elif game_type_id == 5:
                    if live:
                        game_type = Period.SCORE_SUM_LIVE if not half else Period.SCORE_SUM_LIVE_1ST_HALF
                    else:
                        game_type = Period.SCORE_SUM if not half else Period.SCORE_SUM_1ST_HALF
                elif game_type_id == 6:
                    if live:
                        game_type = Period.HALF_FULL_SCORE_LIVE
                    else:
                        game_type = Period.HALF_FULL_SCORE
            elif sport_type is GameType.basketball:
                if game_type_id in (0, 99, -1):
                    game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 1:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 2:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 4:
                    game_type = Period.SECOND_HALF
            elif sport_type is GameType.baseball:
                if game_type_id == 0:
                    game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 1:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 2:
                    if live:
                        game_type = Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FIRST_HALF
                elif game_type_id == 3:
                    if live:
                        game_type = Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FIRST_HALF
                elif game_type_id == 4:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 5:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
            elif sport_type is GameType.tennis:
                if game_type_id == 0:
                        game_type = Period.FULL
                elif game_type_id == 1:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 2:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 3:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
            elif sport_type is GameType.hockey:
                if game_type_id == 0:
                        game_type = Period.FULL
                elif game_type_id == 1:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 2:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
                elif game_type_id == 3:
                    if live:
                        game_type = Period.LIVE_FULL if not half else Period.LIVE_FIRST_HALF
                    else:
                        game_type = Period.FULL if not half else Period.FIRST_HALF
            return game_type
