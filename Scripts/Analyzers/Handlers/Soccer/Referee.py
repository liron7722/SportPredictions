from Scripts.Analyzers.Handlers.Soccer.basic import Basic


class Referee(Basic):
    def __init__(self, fixture, info,  db=None, logger=None):
        super().__init__(fixture=fixture, info=info,  db=db, logger=logger)
        self.cls_type = 'Re'
        if len(self.fixture['Score Box']['Officials']) > 0:
            self.name = self.fixture['Score Box']['Officials'][0]['Name']
            self.log(f"Referee Handler got: {self.name}", level=20)
        else:
            self.name = None
        self.load()

    # call get_stats with the right params
    def load(self):
        self.log(f'Cmd: basic load')
        # Initialize
        seasons = {'AT': 'All Time'}  # All Time
        collection_name = 'Referees'
        self.db_load(collection_name, seasons)

    # Read stats from fixture
    def read_and_save(self):
        self.log(f'Cmd: read_and_save')
        seasons = ['AT']  # All Time
        self.update_data = self.stats.copy()
        self.read_events(seasons, None)
        self.read_extra_stats(seasons, None)

    def read_events(self, seasons, _):
        self.log(f'Cmd: read_events')
        half_index = {'First Half': 'HT', 'Half Time': 'FT', 'Full Time': 'ET'}  # Half Time, Full Time, Extra Time
        event_index = {'yellow_card': 'Ye', 'red_card': 'Re', 'yellow_red_card': '2Ye'}
        # Read and Save
        for season_key in seasons:
            self.update_data[season_key][f'Ga'] += 1  # Games
            for half, half_key in half_index.items():
                # Amount, Early, Late
                temp = {'Ye': {'Am': 0, 'E': 0, 'L': 0},
                        'Re': {'Am': 0, 'E': 0, 'L': 0},
                        '2Ye': {'Am': 0, 'E': 0, 'L': 0}}
                events = self.fixture['Events'][half]
                # Goals, Yellows, Reds, 2nd Yellow
                for event in events:
                    if event['Event'] in event_index.keys():
                        event_key = event_index[event["Event"]]
                        temp[event_key]['Am'] += 1

                        minute = event['Minute'] if type(event['Minute']) is not dict else event['Minute']['Minute']
                        if int(minute) <= 30:  # Calc Early event
                            temp[event_key]['E'] += 1
                        elif int(minute) >= 60:  # Calc Last event
                            temp[event_key]['L'] += 1

                for event_key, event_type in temp.items():
                    for type_key, value in event_type.items():
                        self.update_data[season_key][f'{half_key}_{event_key}_{type_key}'].append(value)

    def read_extra_stats(self, seasons, _):
        self.log(f'Cmd: read_extra_stats')
        stats_index = {'Fouls': 'Fo'}
        temp = {'Fo': 0}  # Fouls

        # Read
        for team in ['Home Team', 'Away Team']:
            data = self.fixture['Extra Stats'][team]
            for key, value in data.items():
                if key in stats_index:
                    temp[stats_index[key]] += int(value)

        # Save
        for season_key in seasons:
            for stat_key, value in temp.items():
                self.update_data[season_key][f'{stat_key}'].append(value)

    # Update db
    def upload(self):
        self.log(f'Cmd: basic update')
        # Initialize
        competition = self.info['Competition']
        seasons = {'AT': 'All Time'}  # All Time
        collection_name = 'Referees'
        # Update
        db = self.db_client.get_db(name=self.db_name)
        collection = self.db_client.get_collection(name=collection_name, db=db)
        for season_key, season in seasons.items():
            self.update(competition, season, season_key, collection)

    @staticmethod
    def get_default_stats():
        res = dict()
        for column in ['Ga']:  # Games
            res[f'{column}'] = 0

        for half in ['HT', 'FT', 'ET']:  # Half Time, Full Time, Extra Time
            for column in ['Ye', 'Re', '2Ye']:  # Yellow, Red, 2nd Yellow
                for inner_column in ['Am', 'E', 'L']:  # Amount, Early, Late
                    res[f'{half}_{column}_{inner_column}'] = list()

        for column in ['Fo']:  # Fouls
            res[f'{column}'] = list()

        return res
