import sys
import pandas as pd
import pickle
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

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


def validate(model_path, data_path, features):
    data = pd.read_csv(data_path, index_col=False)
    model = get_model(model_path)
    prediction = inverser(predict(model, data, features))
    truth = inverser(pd.factorize(data['class'])[0])
    _acc = accuracy_score(truth, prediction)
    tn, fp, fn, tp = confusion_matrix(truth, prediction).ravel()
    fpr = round(fp / (fp + tn), 2)
    fnr = round(fn / (fn + tp), 2)
    precision = round(tp / (tp + fp), 2)
    recall = round(tp / (tp + fn), 2)
    f1 = round((2 * precision * recall) / (precision + recall), 2)
    acc = round(_acc, 2)
    return fpr, fnr, precision, recall, f1, acc


if __name__ == '__main__':
    result_full = validate(os.path.join(DIR_REAPER, 'model', 'model_full.pkl'),
                           os.path.join(DIR_REAPER, 'data', 'validation.csv'),
                           FEATURES_FULL)
    result_subset = validate(os.path.join(DIR_REAPER, 'model', 'model_subset.pkl'),
                             os.path.join(DIR_REAPER, 'data', 'validation.csv'),
                             FEATURES_SUBSET)
    headers = ['fpr', 'fnr', 'precision', 'recall', 'f1-measure', 'accuracy']
    results = [result_full, result_subset]
    df_results = pd.DataFrame(columns=headers, data=results)
    df_results['setting'] = pd.Series(['full', 'subset'])
    df_results.set_index('setting', inplace=True)
    df_results.to_csv(os.path.join(DIR_REAPER, 'data', 'performance.csv'), index=True)
