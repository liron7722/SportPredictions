from Scripts.Analyzers.Handlers.Soccer.basic import Basic


class Team(Basic):
    def __init__(self, fixture, info, side, db=None, logger=None):
        super().__init__(fixture=fixture, info=info,  db=db, logger=logger)
        self.cls_type = 'Te'
        self.side = side
        self.name = self.fixture['Score Box'][f'{side} Team']['Name']
        self.log(f"Team Handler got: {self.name}", level=20)
        self.load()
