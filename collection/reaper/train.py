import sys
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

sys.path.append('..')
from finder import *  # noqa: E402


def train(train_path, model_path, features):
    train_data = pd.read_csv(train_path, index_col=False).fillna(value=0)
    train_data_class = pd.factorize(train_data['class'])[0]
    model = RandomForestClassifier(n_jobs=2, random_state=0)
    model.fit(train_data[features], train_data_class)
    with open(model_path, 'wb') as file:
        pickle.dump(model, file)


if __name__ == '__main__':
    train(os.path.join(DIR_REAPER, 'data', 'utility.csv'),
          os.path.join(DIR_REAPER, 'model', 'model_subset.pkl'),
          FEATURES_SUBSET)
    train(os.path.join(DIR_REAPER, 'data', 'utility.csv'),
          os.path.join(DIR_REAPER, 'model', 'model_full.pkl'),
          FEATURES_FULL)
