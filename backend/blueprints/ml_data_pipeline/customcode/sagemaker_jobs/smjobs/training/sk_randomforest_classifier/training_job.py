import argparse
import joblib
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics
from os import listdir
import time
import great_expectations as ge


# inference functions ---------------
def model_fn(model_dir):
    clf = joblib.load(os.path.join(model_dir, 'model.joblib'))
    return clf


if __name__ == '__main__':

    print('extracting arguments')
    parser = argparse.ArgumentParser()

    # hyperparameters sent by the client are passed as command-line arguments to the script.
    # to simplify the demo we don't use all sklearn RandomForest hyperparameters
    parser.add_argument('--n-estimators', type=int, default=10)
    parser.add_argument('--min-samples-leaf', type=int, default=3)
    parser.add_argument('--max-depth', type=int, default=10)
    parser.add_argument('--max-features', type=str, default='auto')
    parser.add_argument('--random-state', type=int, default=20)
    parser.add_argument('--multi-class', type=str, default='raise')

    # Data, model, and output directories
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--test', type=str, default=os.environ.get('SM_CHANNEL_TEST'))
    parser.add_argument('--train-file', type=str, default='training_data.csv')
    parser.add_argument('--test-file', type=str, default='validation_data.csv')

    args, _ = parser.parse_known_args()

    train_path = os.path.join(args.train, args.train_file)
    print('reading training data {}'.format(train_path))

    test_path = os.path.join(args.test, args.test_file)
    print('reading test data {}'.format(test_path))

    train_df = pd.read_csv(train_path, header=None).to_numpy()
    test_df = pd.read_csv(test_path, header=None).to_numpy()

    print('building training and testing datasets')
    X_train = train_df[:, 1:]
    X_test = test_df[:, 1:]

    y_train = train_df[:, 0]
    y_test = test_df[:, 0]

    print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

    # train
    print('training model')
    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        min_samples_leaf=args.min_samples_leaf,
        max_depth=args.max_depth,
        max_features=args.max_features,
        random_state=args.random_state,
        n_jobs=-1,
    )

    tic = time.perf_counter()
    model.fit(X_train, y_train)
    toc = time.perf_counter()

    # print abs error
    print('validating model')
    y_pred = model.predict(X_test)
    y_pred_prob = model.predict_proba(X_test)

    accuracy = metrics.accuracy_score(y_test, y_pred)
    print(f'Accuracy= {accuracy};')

    precision = metrics.precision_score(y_test, y_pred, average='macro')
    print(f'Precision= {precision};')

    recall = metrics.recall_score(y_test, y_pred, average='macro')
    print(f'Recall= {recall};')

    f1 = metrics.f1_score(y_test, y_pred, average='macro')
    print(f'F1= {f1};')

    roc_auc = metrics.roc_auc_score(y_test, y_pred_prob, multi_class=args.multi_class)
    print(f'ROC= {roc_auc};')

    print(f'Fit-time=  {toc - tic:0.4f};')

    # persist model
    path = os.path.join(args.model_dir, 'model.joblib')
    joblib.dump(model, path)
    print('model persisted at ' + path)
