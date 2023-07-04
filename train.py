from __future__ import annotations

import os
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
import torch
from matplotlib import pyplot as plt
from pytorch_tabnet.pretraining import TabNetPretrainer
from pytorch_tabnet.tab_model import TabNetClassifier
# from sklearn.metrics import roc_auc_score
# from sklearn.metrics import log_loss
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import KFold

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

    # 説明変数、目的変数、グループ変数の作成
    y = df_race_data_train['2着以内フラグ']
    X = df_race_data_train.drop(['1着フラグ', '2着フラグ', '2着以内フラグ'], axis=1)
    groups_train = df_race_data_train['グループID'].unique()
    groups_id = df_race_data_train['グループID']
    y_test = df_race_data_test['2着以内フラグ']
    X_test = df_race_data_test.drop(['1着フラグ', '2着フラグ', '2着以内フラグ'], axis=1)

    categorical_columns = list(categorical_dims.keys())
    cat_idxs = [i for i, f in enumerate(X) if f in categorical_columns]
    cat_dims = [categorical_dims[f] for f in X if f in categorical_columns]

    unsupervised_models: list[TabNetPretrainer] = []
    pred_models: list[TabNetClassifier] = []
    valid_scores: list[float] = []
    kf = KFold(n_splits=4, shuffle=True, random_state=0)
    for i, (tr_group_idx, va_group_idx) in enumerate(kf.split(groups_train)):
        # グループIDを訓練データ、バリデーションデータに分割
        tr_groups = groups_train[tr_group_idx]
        va_groups = groups_train[va_group_idx]

        is_tr = groups_id.isin(tr_groups)
        is_va = groups_id.isin(va_groups)
        X_train = X[is_tr].values
        y_train = y[is_tr].values
        X_valid = X[is_va].values
        y_valid = y[is_va].values

        # TabNetPretrainer
        unsupervised_model = TabNetPretrainer(
            cat_idxs=cat_idxs,
            cat_dims=cat_dims,
            cat_emb_dim=3,
            optimizer_fn=torch.optim.Adam,
            optimizer_params=dict(lr=2e-2),
            mask_type='entmax',  # "sparsemax",
            # n_shared_decoder=1, # nb shared glu for decoding
            # n_indep_decoder=1, # nb independent glu for decoding
        )

        max_epochs = 1000 if not os.getenv('CI', False) else 2
        # 環境変数 key が存在すればその値を返し、存在しなければ default を返します。
        # key、default、および返り値は文字列です。
        os.getenv('CI', False)

        unsupervised_model.fit(
            X_train=X_train,
            eval_set=[X_valid],
            max_epochs=max_epochs,
            patience=5,
            batch_size=2048,
            virtual_batch_size=128,
            num_workers=0,
            drop_last=False,
            pretraining_ratio=0.8,
        )

        unsupervised_models.append(unsupervised_model)

        clf = TabNetClassifier(
            optimizer_fn=torch.optim.Adam,
            optimizer_params=dict(lr=2e-2),
            scheduler_params={'step_size': 50,  # 学習率スケジューラの使用方法
                              'gamma': 0.9},
            scheduler_fn=torch.optim.lr_scheduler.StepLR,
            mask_type='sparsemax'  # 事前トレーニングモデルを使用している場合、これは上書きされます
        )

        clf.fit(
            X_train=X_train,
            y_train=y_train,
            eval_set=[(X_train, y_train), (X_valid, y_valid)],
            eval_name=['train', 'valid'],
            # eval_metric=['auc'],
            # eval_metric=['logloss'],
            eval_metric=['balanced_accuracy'],
            max_epochs=max_epochs,
            patience=20,
            batch_size=1024,
            virtual_batch_size=128,
            num_workers=0,
            weights=1,
            drop_last=False,
            from_unsupervised=unsupervised_model
        )

        y_valid_pred = clf.predict(X_valid)
        valid_scores.append(
            # roc_auc_score(y_valid, y_valid_pred)
            balanced_accuracy_score(y_valid, y_valid_pred)
        )
        pred_models.append(clf)

        fig = plt.figure()
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.set_title('loss')
        ax1.plot(clf.history['loss'])
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.set_title('train_balanced_accuracy&valid_balanced_accuracy')
        # ax2.plot(clf.history['train_auc'])
        # ax2.plot(clf.history['valid_auc'])
        # ax2.plot(clf.history['train_logloss'])
        # ax2.plot(clf.history['valid_logloss'])
        ax2.plot(clf.history['train_balanced_accuracy'])
        ax2.plot(clf.history['valid_balanced_accuracy'])
        plt.savefig('train' + str(i + 1) + '.png')

    best_idx = np.argmax(valid_scores)
    unsupervised_models[best_idx].save_model('./best_test_pretain_accuracy')
    pred_models[best_idx].save_model('./best_tabnet_model_accuracy')
