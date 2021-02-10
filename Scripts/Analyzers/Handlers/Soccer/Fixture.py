from Scripts.Utility.re import get_int_from_string
from Scripts.Scraper.Soccer.MatchReport import MatchReport
from Scripts.Analyzers.Handlers.Soccer.basic import Basic
from Scripts.Analyzers.Handlers.Soccer.Team import Team
from Scripts.Analyzers.Handlers.Soccer.Manager import Manager
from Scripts.Analyzers.Handlers.Soccer.Referee import Referee


class Fixture(Basic):
    version = '1.1.4'

    def __init__(self, fixture, info, db=None, logger=None):
        super().__init__(fixture=fixture, info=info, db=db, logger=logger)
        self.info = info
        self.fixture = fixture
        fil = {'Competition': info['Competition'], 'Season': info['Season'],
               'Date': fixture['Score Box']['DateTime']['Date'],
               'Home Team': fixture['Score Box']['Home Team']['Name'],
               'Away Team': fixture['Score Box']['Away Team']['Name']}
        self.calculated_flag = self.is_match_calculated(fil)
        if self.calculated_flag is False or self.fixture['Version'] != MatchReport.version:
            self.log(f"Fixture Handler got fixture: Competition: {info['Competition']}\tSeason: {info['Season']}\t"
                     f"Date: {fixture['Score Box']['DateTime']['Date']}\t"
                     f"Home Team: {fixture['Score Box']['Home Team']['Name']}\t"
                     f"Away Team: {fixture['Score Box']['Away Team']['Name']}", level=20)
            self.home_team = Team(fixture=fixture, info=info,  side='Home', db=self.db_client, logger=self.logger)
            self.away_team = Team(fixture=fixture, info=info,  side='Away', db=self.db_client, logger=self.logger)
            self.home_manager = Manager(fixture=fixture, info=info,  side='Home', db=self.db_client, logger=self.logger)
            self.away_manager = Manager(fixture=fixture, info=info,  side='Away', db=self.db_client, logger=self.logger)
            self.referee = Referee(fixture=fixture, info=info, db=self.db_client, logger=self.logger)
            self.calculated_stats = dict()

    # Utility function
    def clean(self):
        self.home_team = None
        self.away_team = None
        self.home_manager = None
        self.away_manager = None
        self.referee = None
        self.calculated_stats = dict()

    # For Calculations
    @staticmethod
    def avg(temp):
        if len(temp) == 0:
            return 0
        res = list(filter(None, temp))
        return sum(res) / len(temp)

    @staticmethod
    def median(temp):
        temp = list(filter(None, temp))
        if len(temp) == 0:
            return 0
        temp.sort()
        return temp[int(len(temp) / 2)]

    def general(self):
        self.log(f'Cmd: Getting general info')
        self.stats['Competition'] = self.info['Competition']
        self.stats['Season'] = self.info['Season']
        self.stats['Date'] = self.fixture['Score Box']['DateTime']['Date']
        self.stats['Attendance'] = self.fixture['Score Box']['Attendance'] \
            if 'Attendance' in self.fixture['Score Box'].keys() else 0
        self.stats['Home Team'] = self.home_team.name
        self.stats['Home Manager'] = self.home_manager.name
        self.stats['Away Team'] = self.away_team.name
        self.stats['Away Manager'] = self.away_manager.name
        self.stats['Referee'] = self.referee.name

    # Save all the stats in one dict before calculation
    def save(self):
        self.log(f'Cmd: basic save')
        index = {'HT': self.home_team, 'AT': self.away_team, 'HTM': self.home_manager, 'ATM': self.away_manager,
                 'Ref': self.referee}
        for key, item in index.items():
            data = item.get_stats_dict()
            for season, stats in data.items():
                if type(stats) is not dict:
                    self.stats[f'{key}_{season}'] = stats  # Last time played
                elif season != 'AT' or key == 'Ref':  # Disable All time for teams and managers
                    for inside_key in stats:
                        self.stats[f'{key}_{season}_{inside_key}'] = stats[inside_key]

    def create_general_columns(self):
        res = dict()
        general_list = ['Competition', 'Season', 'Date', 'Attendance', 'Home Team', 'Home Manager', 'Away Team',
                        'Away Manager', 'Referee']
        res['Version'] = self.version
        for key in general_list:
            res[key] = self.stats[key]
        return res

    def create_predict_columns(self):
        res = dict()
        predict_key = 'Pre'
        # Half Time, Full Time, Extra Time
        half_index = {'First Half': 'HT', 'Half Time': 'FT'}  # , 'Full Time': 'ET'}
        for half, half_key in half_index.items():
            temp = self.calc_events(half)
            res[f'{predict_key}_{half_key}_Res'] = temp['Go']['H'] - temp['Go']['A']  # Result
            for column, inner_column in temp.items():
                for column_type, value in inner_column.items():
                    if column_type in ['H', 'A']:  # The rest are calc in avg and median
                        res[f'{predict_key}_{half_key}_{column}_{column_type}'] = value

        for team in ['Home Team', 'Away Team']:
            temp = self.fixture['Stats'][team].copy()
            for column, column_key in {'Passing Accuracy': 'PA', 'Shots on Target': 'ST'}.items():
                if column in temp:
                    for column_type, column_type_key in {'Successful': 'Su', 'Total': 'To'}.items():
                        if type(temp[column]) is dict:
                            res[f'{predict_key}_{team[0]}_{column_key}_{column_type_key}'] = \
                                int(temp[column][column_type])

            temp = self.fixture['Extra Stats'][team].copy()
            for column, column_key in {'Fouls': 'Fo', 'Corners': 'Co', 'Offsides': 'Off', 'Tackles': 'Ta'}.items():
                if column in temp:
                    res[f'{predict_key}_{team[0]}_{column_key}'] = int(temp[column])
                else:
                    res[f'{predict_key}_{team[0]}_{column_key}'] = None

        temp = self.fixture['Events'].copy()
        res = self.prep_event_prediction(temp)
        for key, item in res.items():
            if type(item) is int:
                res[f'{predict_key}_{key}'] = item
            elif type(item) is dict:
                side = item['side'][0]
                other_side = 'H' if side == 'A' else 'A'
                if 'min' in item.keys():
                    res[f'{predict_key}_{key}_{side}'] = item['min']
                    res[f'{predict_key}_{key}_{other_side}'] = -1  # wasn't first or last
                else:
                    res[f'{predict_key}_{key}_{side}'] = 1  # was first or last
                    res[f'{predict_key}_{key}_{other_side}'] = 0  # wasn't first or last
            elif type(item) is None:
                for side in ['H', 'A']:
                    res[f'{predict_key}_{key}_{side}'] = None
        return res

    # Copy the columns we want to predict before calculation
    def copy_general_and_prediction_columns(self):
        for res in [self.create_general_columns(), self.create_predict_columns()]:
            for key, value in res.items():
                self.calculated_stats[key] = value

    @staticmethod
    def prep_event_prediction(events):
        res = {}
        for event in ['G', 'C']:  # Goal, Card
            for key in ['E', 'Le']:  # Early, Late
                res[f'{key}_{event}'] = 0
            for key in ['F', 'La', 'TF']:  # First, Last, Time of First
                res[f'{key}_{event}'] = None
        for half, item in events.items():
            for event in item:
                if event['Event'] in ['goal', 'own_goal', 'penalty_goal']:
                    event_key = 'G'
                elif event['Event'] in ['yellow_card', 'red_card', 'yellow_red_card']:
                    event_key = 'C'
                else:
                    continue
                if res[f'F_{event_key}'] is None:
                    res[f'F_{event_key}'] = {'side': event['Side']}  # First Card
                    res[f'TF_{event_key}'] = {'side': event['Side'], 'min': event['Minute']}  # Time of First Card
                minute = event['Minute'] if type(event['Minute']) is str else event['Minute']['Minute']
                if int(minute) < 30:  # Early Card
                    res[f'E_{event_key}'] += 1
                elif int(minute) > 70:  # Late Card
                    res[f'Le_{event_key}'] += 1
                res[f'La_{event_key}'] = {'side': event['Side']}  # Last Card
        return res

    def copy_extra_data(self):
        self.log(f'Cmd: extra_data')
        index = {'Home Team': 'HT', 'Away Team': 'AT'}
        for key in index.keys():
            if 'score_xg' in self.fixture['Score Box'][key].keys():
                self.calculated_stats[f'{index[key]}_XG'] = self.fixture['Score Box'][key]['score_xg']  # score xg
            else:
                self.calculated_stats[f'{index[key]}_XG'] = None  # score xg

    def calculate_h2h(self, db_name='Data-Handling', n_games=7):
        def sum_avg_med(games, additional_key='RT'):
            temp = {}
            res = {}
            # SUM
            for game in games:
                for col_key, col_value in game.items():
                    if 'Pre' in col_key:
                        temp[col_key] = list() if col_key not in temp.keys() else temp[col_key]
                        temp[col_key].append(col_value)
            # Avg & Med
            for col_key, values in temp.items():
                data_key = col_key.replace('Pre_', 'H2H_')
                res[f'{data_key}_{additional_key}_avg'] = self.avg(values)
                res[f'{data_key}_{additional_key}_med'] = self.median(values)
            return res

        documents = list()
        db = self.db_client.get_db(name=db_name)
        collection_name = self.stats['Competition']
        collection = self.db_client.get_collection(name=collection_name, db=db)
        sort_key = "Score Box.DateTime.Date"  # sort by date
        # RT = Regular Team (On the same side of current match)
        # BT = Both Team sides (Last games where team can be on both sides)
        team_filters = {'RT': {"Score Box.Home Team.Name": self.home_team.name,
                               "Score Box.Away Team.Name": self.away_team.name},
                        'BT': {'$or': [{"Score Box.Home Team.Name": self.home_team.name,
                                        "Score Box.Away Team.Name": self.away_team.name},
                                       {"Score Box.Home Team.Name": self.away_team.name,
                                        "Score Box.Away Team.Name": self.home_team.name}]}}
        for key, fil in team_filters.items():
            # get data
            documents.extend(self.db_client.get_documents_list(collection=collection, fil=fil, sort=sort_key,
                                                               ascending=-1, limit=n_games))
            # calculate
            calculations = sum_avg_med(documents, additional_key=key)
            # save
            for col, value in calculations.items():
                self.calculated_stats[col] = value

    # Calculate all the stats
    def calculate(self):
        self.log(f'Cmd: calculate')
        # Copy and Calculate
        general_list = ['Competition', 'Season', 'Date', 'Attendance', 'Home Team', 'Away Team']
        for data_key, value in self.stats.items():
            if data_key in general_list or 'AT_' in data_key:
                continue

            if type(value) is list:  # Calculate Average and Median
                values = get_int_from_string(value)
                self.calculated_stats[f'{data_key}_avg'] = self.avg(values)
                self.calculated_stats[f'{data_key}_med'] = self.median(values)
            else:  # Copy Games, Wins, Draw, Loss
                self.calculated_stats[f'{data_key}'] = value

    # Upload calculated fixture stats to the db
    def update_all(self, db_name='Data-Handling'):
        self.log(f'Cmd: upload')
        fil = {'Competition': self.calculated_stats['Competition'], 'Season': self.calculated_stats['Season'],
               'Date': self.calculated_stats['Date'], 'Home Team': self.calculated_stats['Home Team'],
               'Away Team': self.calculated_stats['Away Team']}
        db = self.db_client.get_db(name=db_name)
        collection_name = self.stats['Competition']
        collection = self.db_client.get_collection(name=collection_name, db=db)
        if self.db_client.is_document_exist(collection=collection, fil=fil):
            self.db_client.update_document(collection=collection, fil=fil, data=self.calculated_stats)
        else:
            self.db_client.insert_document(collection=collection, data=self.calculated_stats)

    def is_match_calculated(self, fil, db_name='Data-Handling'):
        db = self.db_client.get_db(name=db_name)
        collection_name = self.info['Competition']
        collection = self.db_client.get_collection(name=collection_name, db=db)
        document = self.db_client.get_documents_list(collection=collection, fil=fil)
        return len(document) > 0 and document[0]['Version'] == self.version

    def update_for_prediction_site(self):
        data = self.create_general_columns()  # get a copy
        comp = data.pop('Competition')  # get comp
        data['Time'] = self.fixture['Score Box']['DateTime']['Time']  # add time
        data['Results'] = self.create_predict_columns()  # get results copy
        
        if self.db_client is not None:  # save data to db
            db = self.db_client.get_db(name='Prediction-Site')
            collection = self.db_client.get_collection(name=comp, db=db)
            fil = {'Season': data['Season'], 'Date': data['Date'],
                   'Home Team': data['Home Team'], 'Away Team': data['Away Team']}
            self.upload_to_db(collection=collection, data=data, fil=fil)

    def run(self):
        self.log(f'Cmd: Fixture Handler run')
        if self.calculated_flag is False or self.fixture['Version'] != MatchReport.version:
            # Update Fixture info on prediction site db
            self.update_for_prediction_site()
            # Create match stats before calculation
            self.general()
            self.save()
            # Calculate
            self.copy_general_and_prediction_columns()
            self.copy_extra_data()
            self.calculate_h2h()
            self.calculate()
            self.update_all()
            # Update stats in DB
            for item in [self.home_team, self.away_team, self.home_manager, self.away_manager, self.referee]:
                item.run()
            # Clean memory
            self.clean()
        self.log(f'Cmd: Fixture Handler finished')

    def get_stats_for_prediction(self):
        self.log(f'Cmd: Getting fixture data for prediction')
        self.save()
        self.copy_extra_data()
        self.calculate_h2h()
        self.calculate()
        result = self.calculated_stats.copy()
        self.clean()
        return result
