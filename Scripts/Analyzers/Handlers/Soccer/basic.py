from Scripts.Utility.time import get_days_difference
from Scripts.Utility.re import get_prev_season_string, get_int_from_string


class Basic:
    ENV = 'Development'
    name = None
    side = None
    cls_type = None
    update_data = None

    info = None
    fixture = None
    logger = None
    db_client = None
    db_name = 'Data-Handling'

    def __init__(self, fixture, info, db=None, logger=None):
        self.add_db(db)
        self.add_logger(logger)
        self.add_info(info)
        self.add_fixture(fixture)
        self.stats = dict()

    def add_info(self, info):
        if self.info is None:
            self.info = info

    def add_fixture(self, fixture):
        if self.fixture is None:
            self.fixture = fixture

    def add_logger(self, logger):
        if self.logger is None:
            self.logger = logger

    def add_db(self, db):
        if self.db_client is None:
            self.db_client = db

    def get_stats_dict(self):
        return self.stats

    # Logger
    def log(self, message: str, level: int = 10):
        if self.logger is not None:
            if self.ENV == 'Development':
                level = 10
            elif self.ENV == 'Production':
                level = 20
            self.logger.log(level, message)

    # call get_stats with the right params
    def load(self):
        # DB Structure:
        # DB's is Comp name
        # Collections are Teams, Managers, Leagues
        # Each Document contain the next data: Competition: Many, Season: Many & All Time, Stats: dict
        self.log(f'Cmd: basic load')
        # Initialize
        cs = self.info['Season']
        ps = get_prev_season_string(cs)
        seasons = {'AT': 'All Time', 'CS': cs, 'PS': ps}  # All Time, Current Season, Past Season
        collection_name = 'Managers' if self.cls_type == 'Ma' else 'Teams'
        self.db_load(collection_name, seasons)

    def db_load(self, collection_name, seasons):
        competition = self.info['Competition']
        # Load
        if self.name is None:  # In case we don't get a name we create default data only
            collection = None
        else:
            db = self.db_client.get_db(name=self.db_name)
            collection = self.db_client.get_collection(name=collection_name, db=db)
        for key, season in seasons.items():
            self.get_stats(collection, competition, season, key)

    # Get stats from db or default
    def get_stats(self, collection, competition, season, key):
        self.log(f'Cmd: get_stats')
        fil = {'Competition': competition, 'Season': season, 'Name': self.name}
        data = [] if collection is None else \
            [item for item in collection.find(fil)]
        if len(data) == 1:
            if season == 'All Time':
                date = data[0].pop('Date')
                self.get_ltp(date)
            for unwanted_key in ['_id', 'Name', 'Competition', 'Season']:
                data[0].pop(unwanted_key)
            self.stats[key] = data[0]
        else:
            self.stats[key] = self.get_default_stats()

    @staticmethod
    def get_default_stats():
        res = dict()
        for side in ['H', 'A']:  # Home, Away
            res[f'{side}_Ga'] = 0  # Games
            for half in ['HT', 'FT', 'ET']:  # Half Time, Full Time, Extra Time
                for column in ['Wi', 'Dr', 'Lo']:  # Wins, Draws, Losses
                    res[f'{side}_{half}_{column}'] = 0

                for column in ['Go', 'Ye', 'Re', '2Ye']:  # Goals, Yellow, Red, 2nd Yellow
                    for j in ['F', 'A', '1st', 'E', 'L']:  # For, Against, First, Early(First 30 min), Late(Last 30 min)
                        res[f'{side}_{half}_{column}_{j}'] = list()

            for other in ['Att']:  # Attendance
                res[f'{side}_{other}'] = list()

            for j in ['F', 'A']:  # For, Against
                for column in ['PA', 'ST', 'Sa']:  # Passing Accuracy, Shots on Target, Saves
                    for typ in ['Su', 'To', 'Pe']:  # Successful, Total, Percent
                        res[f'{side}_{column}_{j}_{typ}'] = list()

                for column in ['Poss', 'Fo', 'Co', 'Cr', 'To', 'Ta', 'In', 'AW', 'Cl', 'Off', 'GK', 'TI', 'LB']:
                    # 'Possession', 'Fouls', 'Corners', 'Crosses', 'Touches', 'Tackles', 'Interceptions', 'Aerials Won',
                    # 'Clearances', 'Offsides', 'Goal Kicks', 'Throw Ins', 'Long Balls'
                    res[f'{side}_{column}_{j}'] = list()
        return res

    # Last Time Played
    def get_ltp(self, date=None):
        if date is None:
            self.stats[f'{self.cls_type}_LTP'] = None
        else:
            get_days_difference(date_one=date, date_two=self.fixture['Score Box']['DateTime']['Date'])

    # Read stats from fixture
    def read_and_save(self):
        self.log(f'Cmd: read_and_save')
        seasons = ['AT', 'CS']  # All Time, Current Season
        self.update_data = self.stats.copy()
        self.update_data.pop('PS')  # pop Past Season
        self.read_events(seasons, self.side[0])
        self.read_stats(seasons, self.side[0])
        self.read_extra_stats(seasons, self.side[0])

    def calc_events(self, half_key):
        event_index = {'goal': 'Go', 'yellow_card': 'Ye', 'red_card': 'Re', 'yellow_red_card': '2Ye'}
        events = self.fixture['Events']
        # Initialize
        side = 'F' if self.side is not None else 'H'

        # Goal, Yellow, Red, 2nd Yellow - For, Against, First, Early (Pre 30 minutes), Late(Last 30 minutes)
        temp = {'Go': {side: 0, 'A': 0, '1st': 0, 'E': 0, 'L': 0}, 'Ye': {side: 0, 'A': 0, '1st': 0, 'E': 0, 'L': 0},
                'Re': {side: 0, 'A': 0, '1st': 0, 'E': 0, 'L': 0}, '2Ye': {side: 0, 'A': 0, '1st': 0, 'E': 0, 'L': 0}}
        # Read
        for event in events[half_key]:
            if event['Event'] not in event_index.keys():  # Skipping events like substitute_in
                continue
            event_key = event_index[event['Event']]

            if self.side is not None:
                event_side = 'F' if event['Side'] == self.side else 'A'
            else:
                event_side = event['Side'][0]
            temp[event_key][event_side] += 1

            if temp[event_key][side] == temp[event_key]['A'] == 0:  # Calc First event
                temp[event_key]['1st'] = 1 if event_side != 'A' else -1
            minute = event['Minute'] if type(event['Minute']) is not dict else event['Minute']['Minute']
            if int(minute) <= 30:  # Calc Early event
                temp[event_key]['E'] += 1
            elif int(minute) >= 60:  # Calc Last event
                temp[event_key]['L'] += 1

        return temp

    def read_events(self, seasons, side):
        self.log(f'Cmd: read_events')
        half_index = {'First Half': 'HT', 'Half Time': 'FT', 'Full Time': 'ET'}  # Half Time, Full Time, Extra Time

        for half_key in half_index:
            temp = self.calc_events(half_key)
            # Save
            for season_key in seasons:
                self.update_data[season_key][f'{side}_Ga'] += 1  # Games

                # Win, Draw, Loss
                if temp['Go']['F'] > temp['Go']['A']:
                    wdl_key = 'Wi'
                elif temp['Go']['F'] == temp['Go']['A']:
                    wdl_key = 'Dr'
                else:
                    wdl_key = 'Lo'
                self.update_data[season_key][f'{side}_{half_index[half_key]}_{wdl_key}'] += 1

                # Goals, Yellows, Reds, 2nd Yellow
                for event_key, values in temp.items():
                    for j in values:
                        self.update_data[season_key][f'{side}_{half_index[half_key]}_{event_key}_{j}'].append(values[j])

    def read_poss(self, seasons, side):
        self.log(f'Cmd: read_poss')
        # Read
        if 'Possession' in self.fixture['Stats'][f'{self.side} Team'].keys():
            home_value = get_int_from_string(self.fixture['Stats'][f'{self.side} Team']['Possession'])  # Possession
        else:
            home_value = None
        away_value = 100 - home_value if home_value is not None else None
        # Save
        for season_key in seasons:
            self.update_data[season_key][f'{side}_Poss_F'].append(home_value)
            self.update_data[season_key][f'{side}_Poss_A'].append(away_value)

    def read_stats(self, seasons, side):
        self.log(f'Cmd: read_stats')
        stats_index = {'Passing Accuracy': 'PA', 'Shots on Target': 'ST', 'Saves': 'Sa'}
        type_index = {'Successful': 'Su', 'Total': 'To', 'Percent': 'Pe'}
        self.read_poss(seasons, side)  # Possession
        # Read
        for team in ['Home Team', 'Away Team']:
            temp = self.fixture['Stats'][team].copy()
            for key in ['Possession', 'Name', 'Cards']:
                if key in temp.keys():
                    temp.pop(key)
            j = 'F' if side == team[0] else 'A'  # _F = For, _A = Against
            # Save
            for season_key in seasons:
                for stat_key, inner_values in temp.items():
                    if type(inner_values) is not dict:
                        continue
                    for type_key, value in inner_values.items():
                        self.update_data[season_key][f'{side}_{stats_index[stat_key]}_{j}_{type_index[type_key]}'] \
                            .append(value)

    def read_extra_stats(self, seasons, side):
        self.log(f'Cmd: read_extra_stats')
        stats_index = {'Fouls': 'Fo', 'Corners': 'Co', 'Crosses': 'Cr', 'Touches': 'To', 'Tackles': 'Ta',
                       'Interceptions': 'In', 'Aerials Won': 'AW', 'Clearances': 'Cl', 'Offsides': 'Off',
                       'Goal Kicks': 'GK', 'Throw Ins': 'TI', 'Long Balls': 'LB'}
        # Read
        for team in ['Home Team', 'Away Team']:
            temp = self.fixture['Extra Stats'][f'{self.side} Team']
            j = 'F' if side == team[0] else 'A'  # _F = For, _A = Against
            # Save
            for season_key in seasons:
                for key, value in temp.items():
                    if key == 'Name':
                        continue
                    self.update_data[season_key][f'{side}_{stats_index[key]}_{j}'].append(value)

    # Update db
    def upload(self):
        self.log(f'Cmd: basic update')
        # Initialize
        competition = self.info['Competition']
        cs = self.info['Season']
        seasons = {'AT': 'All Time', 'CS': cs}  # All Time, Current Season, Past Season
        collection_name = 'Managers' if self.cls_type == 'Ma' else 'Teams'
        # Update
        db = self.db_client.get_db(name=self.db_name)
        collection = self.db_client.get_collection(name=collection_name, db=db)
        for season_key, season in seasons.items():
            self.update(competition, season, season_key, collection)

    def update(self, competition, season, season_key, collection):
        fil = {'Competition': competition, 'Season': season, 'Name': self.name}
        temp = self.update_data[season_key].copy()
        temp['Name'] = self.name
        temp['Competition'] = competition
        temp['Season'] = season
        temp['Date'] = self.fixture['Score Box']['DateTime']['Date']
        if self.db_client.is_document_exist(collection=collection, fil=fil):
            self.db_client.update_document(collection=collection, fil=fil, data=temp)
        else:
            self.db_client.insert_document(collection=collection, data=temp)

    def run(self):
        self.log(f'Cmd: basic run')
        if self.name is not None:
            self.read_and_save()
            self.upload()
