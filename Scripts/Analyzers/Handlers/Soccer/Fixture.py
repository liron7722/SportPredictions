from Scripts.Utility.re import get_int_from_string
from Scripts.Scraper.Soccer.MatchReport import MatchReport
from Scripts.Analyzers.Handlers.Soccer.basic import Basic
from Scripts.Analyzers.Handlers.Soccer.Team import Team
from Scripts.Analyzers.Handlers.Soccer.Manager import Manager
from Scripts.Analyzers.Handlers.Soccer.Referee import Referee


class Fixture(Basic):
    version = '1.0.0'

    def __init__(self, fixture, info, db=None, logger=None):
        super().__init__(fixture=fixture, info=info, db=db, logger=logger)
        self.info = info
        self.fixture = fixture
        fil = {'Competition': info['Competition'], 'Season': info['Season'],
               'Date': fixture['Score Box']['DateTime']['Date'], 'Home Team': fixture['Score Box']['Home Team']['Name'],
               'Away Team': fixture['Score Box']['Away Team']['Name']}
        self.calculated_flag = self.is_match_calculated(fil)
        if self.calculated_flag is False:
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

    def clean(self):
        self.home_team = None
        self.away_team = None
        self.home_manager = None
        self.away_manager = None
        self.referee = None
        self.calculated_stats = dict()

    def general(self):
        self.log(f'Cmd: Getting general info')
        self.stats['Competition'] = self.info['Competition']
        self.stats['Season'] = self.info['Season']
        self.stats['Date'] = self.fixture['Score Box']['DateTime']['Date']
        self.stats['Attendance'] = self.fixture['Score Box']['Attendance'] \
            if 'Attendance' in self.fixture['Score Box'].keys() else 0
        self.stats['Home Team'] = self.home_team.name
        self.stats['Away Team'] = self.away_team.name

    def copy_extra_data(self):
        self.log(f'Cmd: extra_data')
        index = {'Home Team': 'HT', 'Away Team': 'AT'}
        for key in index.keys():
            if 'score_xg' in self.fixture['Score Box'][key].keys():
                self.calculated_stats[f'{index[key]}_XG'] = self.fixture['Score Box'][key]['score_xg']  # score xg
            else:
                self.calculated_stats[f'{index[key]}_XG'] = None  # score xg

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
                else:
                    for inside_key in stats:
                        self.stats[f'{key}_{season}_{inside_key}'] = stats[inside_key]

    # Copy the columns we want to predict before calculation
    def copy_general_columns(self):
        general_list = ['Competition', 'Season', 'Date', 'Attendance', 'Home Team', 'Away Team']
        self.calculated_stats['Version'] = self.version
        for key in general_list:
            self.calculated_stats[key] = self.stats[key]

    # Copy the columns we want to predict before calculation
    def copy_predict_columns(self):
        predict_key = 'Pre'
        half_index = {'First Half': 'HT', 'Half Time': 'FT', 'Full Time': 'ET'}  # Half Time, Full Time, Extra Time
        for half, half_key in half_index.items():
            temp = self.calc_events(half)
            for column, inner_column in temp.items():
                for column_type, value in inner_column.items():
                    if column_type in ['H', 'A']:  # The rest are calc in avg and median
                        self.calculated_stats[f'{predict_key}_{half_key}_{column}_{column_type}'] = value
            self.calculated_stats[f'{predict_key}_{half_key}_Re'] = temp['Go']['H'] - temp['Go']['A']  # Result

        for team in ['Home Team', 'Away Team']:
            temp = self.fixture['Stats'][team].copy()
            for column, column_key in {'Passing Accuracy': 'PA', 'Shots on Target': 'ST'}.items():
                if column in temp:
                    for column_type, column_type_key in {'Successful': 'Su', 'Total': 'To'}.items():
                        if type(temp[column]) is dict:
                            self.calculated_stats[f'{predict_key}_{team[0]}_{column_key}_{column_type_key}'] = \
                                int(temp[column][column_type])

            temp = self.fixture['Extra Stats'][team].copy()
            for column, column_key in {'Fouls': 'Fo', 'Corners': 'Co', 'Offsides': 'Off', 'Tackles': 'Ta'}.items():
                if column in temp:
                    self.calculated_stats[f'{predict_key}_{team[0]}_{column_key}'] = int(temp[column])
                else:
                    self.calculated_stats[f'{predict_key}_{team[0]}_{column_key}'] = None

    # Calculate all the stats
    def calculate(self):
        # Inner Functions - For Calculations
        def avg(temp):
            if len(temp) == 0:
                return 0
            res = list(filter(None, temp))
            return sum(res) / len(temp)

        def median(temp):
            temp = list(filter(None, temp))
            if len(temp) == 0:
                return 0
            temp.sort()
            return temp[int(len(temp) / 2)]

        self.log(f'Cmd: calculate')
        # Copy and Calculate
        general_list = ['Competition', 'Season', 'Date', 'Attendance', 'Home Team', 'Away Team']
        for data_key, value in self.stats.items():
            if data_key in general_list:
                continue

            if type(value) is list:  # Calculate Average and Median
                values = get_int_from_string(value)
                self.calculated_stats[f'{data_key}_avg'] = avg(values)
                self.calculated_stats[f'{data_key}_med'] = median(values)
            else:  # Copy Games, Wins, Draw, Loss
                self.calculated_stats[f'{data_key}'] = value

    # Upload calculated fixture stats to the db
    def upload(self, db_name='Data-Handling'):
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

    def run(self):
        self.log(f'Cmd: Fixture Handler run')
        if self.calculated_flag is False or self.fixture['Version'] != MatchReport.version:
            # Create match stats before calculation
            self.general()
            self.save()
            # Calculate
            self.copy_general_columns()
            self.copy_predict_columns()
            self.copy_extra_data()
            self.calculate()
            self.upload()
            # Update stats in DB
            for item in [self.home_team, self.away_team, self.home_manager, self.away_manager, self.referee]:
                item.run()
            # Clean memory
            self.clean()
        self.log(f'Cmd: Fixture Handler finished')
