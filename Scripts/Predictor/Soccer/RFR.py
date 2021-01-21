from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report
from Scripts.Predictor.Soccer.basic import Basic


class RFR(Basic):
    def __init__(self, db, logger=None):
        self.model_type = 'RFR'
        super().__init__(db=db, logger=logger)
        self.load()
        self.clear()

    def add_model(self, comp_key, key):
        super().add_model(comp_key, key)
        x = self.x
        y = self.y[key]
        size = int(x.shape[0] * .8)
        x_train = x[:size]
        y_train = y[:size]
        x_test = x[size:]
        y_test = y[size:]

        x_train = x_train.fillna(-999)
        x_test = x_test.fillna(-999)

        rfr_model = RandomForestRegressor()
        parameters = {'n_estimators': [200],
                      'max_depth': [7],
                      'min_samples_split': [100],
                      'min_samples_leaf': [5]
                      }
        # Run the grid search
        grid_obj = GridSearchCV(rfr_model, parameters,
                                cv=7,
                                n_jobs=-1,
                                verbose=1)
        grid_obj = grid_obj.fit(x_train, y_train)

        # Set the clf to the best combination of parameters
        rfr_model = grid_obj.best_estimator_

        # Fit the best algorithm to the data.
        rfr_model.fit(x_train, y_train)

        # Evaluate
        y_predictions = rfr_model.predict(x_test)
        predictions = [int(value) for value in y_predictions]
        accuracy = accuracy_score(y_test, predictions)
        cr = classification_report(y_test, predictions, output_dict=True)

        # Save
        self.save_to_memory(comp_key, key, accuracy, cr, rfr_model)
        self.save_to_db(comp_key, key, accuracy, cr, rfr_model)
