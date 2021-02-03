from numpy import int64
from Scripts.Predictor.Soccer.basic import Basic
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report


class RFR(Basic):
    def __init__(self, db, logger=None):
        self.model_type = 'RFR'
        super().__init__(db=db, logger=logger)
        self.load()
        self.clear()

    @staticmethod
    def get_default_parameters():
        return {'bootstrap': [True, False],
                'max_depth': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, None],
                'max_features': ['auto', 'sqrt'],
                'min_samples_leaf': [1, 2, 4],
                'min_samples_split': [2, 5, 10],
                'n_estimators': [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]}

    def add_model(self, comp_key, key):
        # Avoid Model what already in the memory
        if comp_key == 'A-League':  # Todo Remove after fix in db
            return
        if comp_key in self.models.keys() and key in self.models[comp_key].keys():
            self.log(f'{self.model_type} Model for {key} already loaded')
            return
        super().add_model(comp_key, key)

        # Make a copy
        y = self.y[key]
        x = self.x.filter(items=y.index, axis=0)

        # reset index
        y = y.reset_index(drop=True)
        x = x.reset_index(drop=True)

        # split and null handling
        null_fill = -999
        size = int(x.shape[0] * .70)
        x_train = x[:size].fillna(null_fill)
        y_train = y[:size].fillna(null_fill).astype(int64)
        x_test = x[size:].fillna(null_fill)
        y_test = y[size:].fillna(null_fill).astype(int64)

        # model
        rfr_model = RandomForestRegressor()
        parameters = self.get_parameters(key)
        # Run the grid search
        grid_obj = RandomizedSearchCV(estimator=rfr_model,
                                      param_distributions=parameters,
                                      n_iter=100,
                                      cv=3,
                                      verbose=2,
                                      random_state=42,
                                      n_jobs=-1)
        # grid_obj = GridSearchCV(rfr_model, parameters,
        #                        cv=7,
        #                        n_jobs=-1,
        #                        verbose=0)
        grid_obj = grid_obj.fit(x_train, y_train)

        # Set the clf to the best combination of parameters
        rfr_model = grid_obj.best_estimator_

        # Fit the best algorithm to the data.
        rfr_model.fit(x_train, y_train)

        # Evaluate
        y_predictions = rfr_model.predict(x_test)
        predictions = [int(value) for value in y_predictions]  # round prediction down
        accuracy = accuracy_score(y_test, predictions)
        cr = classification_report(y_test, predictions, output_dict=True)

        # Save
        self.save_to_memory(comp_key, key, rfr_model, accuracy, cr)
        self.save_to_db(comp_key, key, rfr_model, accuracy, cr)
        self.save_parameters(key=key, parameters=parameters)
