from flask import Flask, jsonify, request, render_template
from Scripts.Analyzers.Handlers.Soccer.DataHandler import DataHandler
from Scripts.Predictor.Soccer.PredictorHandler import PredictorHandler

ENV = 'Development'

# Init app
app = Flask(__name__)

# Init data handlers
data_handler = DataHandler()

# Init predictors
predictor_handler = PredictorHandler()


@app.route('/predict', methods=['POST'])
def predict():
    comp_key = request.form['competition'].replace(' ', '-')
    fixture_info = {
        'Home Team': {'Name': request.form['home_team_name'], 'Manager': request.form['home_team_manager']},
        'Away Team': {'Name': request.form['away_team_name'], 'Manager': request.form['away_team_manager']},
        'Officials': [{'Name': request.form['ref']}]
    }
    fixture = {'Score Box': fixture_info}
    data = data_handler.get_fixture_data(info={'Competition': comp_key}, fixture=fixture)
    return jsonify({'Info': fixture_info,
                    'Prediction': predictor_handler.predict(comp_key=comp_key, data=data)})


@app.route('/predict-info', methods=['GET'])
def info():
    return jsonify(predictor_handler.info())


@app.route('/', methods=['GET'])
def get():
    return render_template('home.html')


def run():
    debug = True if ENV == 'Development' else False
    app.run(debug=debug)


# Run Server
if __name__ == '__main__':
    run()
