import sys
import pandas as pd
import pickle
import numpy as np

sys.path.append('..')
from finder import *  # noqa: E402


def get_model(model_path):
    with open(model_path, 'rb') as file:
        model = pickle.load(file)
        return model


def predict(model, data, features):
    prediction = model.predict(data[features])
    return prediction


def inverser(x):
    negate = lambda v: 1-v
    negates = np.array([negate(xi) for xi in x])
    return negates


if __name__ == '__main__':
    model = get_model(os.path.join(DIR_REAPER, 'model', 'model_subset.pkl'))
    data = pd.read_csv(os.path.join(DIR_REAPER, 'data', 'results.csv'), index_col=False)
    prediction = inverser(predict(model, data, FEATURES_SUBSET))
    projects = data['repository'].to_list()
    res = pd.DataFrame({'repository': projects, 'engineered': prediction})
    res.to_csv(os.path.join(DIR_REAPER, 'data', 'class.csv'), index=False)
    eng = pd.DataFrame({'repository': res[res['engineered'] == 1]['repository']})
    eng.to_csv(PATH_REPOSITORIES_DATA['engineered_repos'], index=False)
