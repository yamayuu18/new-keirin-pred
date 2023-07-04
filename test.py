from __future__ import annotations

import pickle
from datetime import datetime

import pandas as pd
from pytorch_tabnet.tab_model import TabNetClassifier
from sklearn.metrics import balanced_accuracy_score
# from sklearn.metrics import roc_auc_score

if __name__ == '__main__':
    # pickleファイルの読み込み
    df_race_data = pd.read_pickle('df_race_data.pkl')
    with open('categorical_dims.pkl', 'rb') as f:
        categorical_dims = pickle.load(f)

    # 訓練データとテストデータの分割
    test_date = datetime(2021, 8, 1)
    df_race_data_test = df_race_data.query('開催日時 >= @test_date').copy()
    df_race_data_train = df_race_data.query('開催日時 < @test_date').copy()
    df_race_data_test['開催日時'] = df_race_data_test['開催日時'].apply(
        lambda x: x.timestamp())
    df_race_data_train['開催日時'] = df_race_data_train['開催日時'].apply(
        lambda x: x.timestamp())
    y_test = df_race_data_test['2着以内フラグ'].values
    X_test = df_race_data_test.drop(
        ['1着フラグ', '2着フラグ', '2着以内フラグ'], axis=1).values

    best_clf = TabNetClassifier()
    # best_clf.load_model('./best_tabnet_model.zip')
    best_clf.load_model('./best_tabnet_model_accuracy.zip')

    y_test_pred = best_clf.predict(X_test)
    print(balanced_accuracy_score(y_test, y_test_pred))

    df_race_data_test['予測結果'] = y_test_pred
    df_race_data_test.to_pickle('df_race_data_test.pkl')
