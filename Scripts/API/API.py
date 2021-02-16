from os import environ
from flask import Flask, jsonify, request, render_template, json
from Scripts.Analyzers.Handlers.Soccer.DataHandler import DataHandler
from Scripts.Predictor.Soccer.PredictorHandler import PredictorHandler

ENV = 'Development' if environ.get('ENV') != 'Production' else 'Production'

# Init app
app = Flask(__name__)

# Init data handlers
data_handler = DataHandler()

# Init predictors
predictor_handler = PredictorHandler()
ph_info = predictor_handler.info()


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
    res = {'Home_Team': request.form['home_team_name'], 'Home_Team_Manager': request.form['home_team_manager'],
           'Away_Team': request.form['away_team_name'], 'Away_Team_Manager': request.form['away_team_manager'],
           'Referee': request.form['ref'], 'Competition': comp_key,
           'Prediction': predictor_handler.predict(comp_key=comp_key, data=data)}
    response = app.response_class(
        response=json.dumps(res),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/predict-info', methods=['GET'])
def info():
    return jsonify(ph_info)


@app.route('/manual', methods=['GET'])
def manual():
    return render_template('home.html', data=ph_info)


@app.route('/', methods=['GET'])
def get():
    return jsonify({'msg': 'Welcome to Soccer Prediction API',
                    'documentation': 'https://www.lironrevah.tech/projects/sports-prediction-api/soccer'})


def run():
    debug = True if ENV == 'Development' else False
    app.run(debug=debug, port=5005)


# Run Server
if __name__ == '__main__':
    run()
