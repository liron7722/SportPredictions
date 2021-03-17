from Scripts.Analyzers.Handlers.Soccer.basic import Basic


class Manager(Basic):
    def __init__(self, fixture, info,  side, db=None, logger=None):
        super().__init__(fixture=fixture, info=info,  db=db, logger=logger)
        self.cls_type = 'Ma'
        self.side = side
        score_box = self.fixture['Score Box'][f'{side} Team']
        if 'Manager' in score_box.keys():
            self.name = score_box['Manager']
            self.logger.log(f"Manager Handler got: {self.name}", level=20)

        else:
            self.name = None
        self.load()
