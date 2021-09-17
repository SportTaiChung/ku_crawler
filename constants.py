# coding: utf-8
from enum import Enum


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
                if league_name == '歐洲足協 - 冠軍聯賽':
                    return '20'
                return '10'
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
