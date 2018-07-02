import pandas as pd
import os
import numpy as np
from setting import DAT_DIR


class DataPrep():
    '''
    Data preprocessing object
    '''

    def __init__(self):
        pass

    def add_derived_feats(self, data_all):
        print('Add derived features...')
        data_all['age_in_year'] = data_all['YrSold'] - data_all['YearBuilt']
        data_all['years_from_remodel'] = data_all['YrSold'] - data_all['YearRemodAdd']
        return data_all

    def choose_features(self, X, cat_feats=None, quant_feats=None):
        '''
        Choose features to be used as predictors from:
        + numerical feats
        + categorical feats
        :param quant_feats:
        :param cat_feats:
        :param X:
        :return:
        '''
        numerical_feats = ['LotArea', 'OverallQual', 'OverallCond', 'YearBuilt', 'YearRemodAdd',
                           'age_in_year', 'years_from_remodel',
                           ]
        area_feats = ['TotalBsmtSF',
                      '1stFlrSF',
                      '2ndFlrSF', ]
        features = numerical_feats + area_feats

        if cat_feats:
            for cf in cat_feats:
                features += get_onehot_features(cf, X)

        if quant_feats:
            print('Adding quantitative features')
            features += to_score_feats(quant_feats)

        print('features used for training models: {}'.format(features))
        return features


def get_onehot_features(cat_feat, df):
    '''
    Include the given categorical feature
    :param df:
    :param cat_feat: given categorical feature
    :return:
    '''

    print('include categorical feature {}'.format(cat_feat))
    onehot_features = [ff for ff in df.columns if '{}_'.format(cat_feat) in ff]
    return onehot_features


def to_score_feats(quant_feats):
    return [qf + '_score' for qf in quant_feats]


def join(train, test, response):
    test[response] = np.nan
    return pd.concat([train, test])


def onehot_encode(feat, df):
    print('Onehot encode feature {}'.format(feat))
    encoded = pd.get_dummies(df[feat], prefix=feat)
    res = pd.concat([df.drop(feat, axis=1), encoded], axis='columns')
    return res


def to_full(abbv_feat, df, full_form):
    # convert an abbreviated feature in data into its full form via given full forms
    full_feat = 'full_' + abbv_feat
    df[abbv_feat] = df[abbv_feat].fillna("NA")
    df[full_feat] = df[abbv_feat].apply(lambda x: full_form[x])
    return df


def load_full_form(fname):
    tmp = pd.read_csv(os.path.join(DAT_DIR, fname), keep_default_na=False)
    full_form = dict(zip(tmp['abbr'], tmp['full']))

    # debug
    # print('full forms: {}'.format(full_form))
    return full_form


def to_quantitative(text_feat, df, scoring):
    '''
    Given a feature stored in data as text but actually a quantitative feat, convert it to numerical values
    via given encoding
    :param scoring:
    :param text_feat:
    :return:
    '''
    print('\t {}'.format(text_feat))

    res = df.copy()
    n_na = sum(df[text_feat].isnull())
    print('\t Column {0} has {1} NAs, they will be filled by 0'.format(text_feat, n_na))
    res[text_feat].fillna("NA", inplace=True)

    # print('\t Column {} has {} NAs, they will be filled by forward filling'.format(text_feat, n_na))
    # res[text_feat].fillna(method='ffill', inplace=True)
    res['{}'.format(text_feat) + '_score'] = res[text_feat].apply(lambda form: scoring[form])
    return res


if __name__ == '__main__':
    train = pd.read_csv(os.path.join(DAT_DIR, 'train.csv'))
    test = pd.read_csv(os.path.join(DAT_DIR, 'test.csv'))

    ## Preprocesses
    response = 'SalePrice'
    data_all = join(train, test, response)

    print('\n Onehot encoding categorical feats...')
    data_all = onehot_encode('Neighborhood', data_all)
    # zone_full = load_full_form('zones.csv')
    # data_all = to_full('MSZoning', data_all, zone_full)
    data_all = onehot_encode('MSZoning', data_all)

    print('\n Encoding quantitative text features...')
    score_dict = {
        "Utilities": {"AllPub": 4, "NoSewr": 3, "NoSeWa": 2, "ELO": 1, "NA": 0},
        "ExterQual": {"Ex": 5, "Gd": 4, "TA": 3, "Fa": 2, "Po": 1, "NA": 0},
        "ExterCond": {"Ex": 5, "Gd": 4, "TA": 3, "Fa": 2, "Po": 1, "NA": 0},
        "HeatingQC": {"Ex": 5, "Gd": 4, "TA": 3, "Fa": 2, "Po": 1, "NA": 0},
        "BsmtQual": {"Ex": 5, "Gd": 4, "TA": 3, "Fa": 2, "Po": 1, "NA": 0},
        "BsmtCond": {"Ex": 5, "Gd": 4, "TA": 3, "Fa": 2, "Po": 1, "NA": 0},
        "BsmtExposure": {"Gd": 4, "Av": 3, "Mn": 2, "No": 1, "NA": 0},
        "BsmtFinType1": {"GLQ": 6, "ALQ": 5, "BLQ": 4, "Rec": 3, "LwQ": 2, "Unf": 1, "NA": 0},
    }

    for tf in score_dict.keys():
        data_all = to_quantitative(text_feat=tf, df=data_all, scoring=score_dict[tf])

    dp = DataPrep()
    features = dp.choose_features(data_all,
                                  cat_feats=['Neighborhood', 'full_MSZoning'],
                                  quant_feats=['Utilities', 'ExterQual', 'ExterCond', 'HeatingQC'])

    # fill NA in both train and test
    print('Fill NAs in features by 0')
    data_all[features].fillna(0, inplace=True)

    ## End of preprocesses ==================
    print('Shape of data_all after all preprocessing: {}'.format(data_all.shape))
    score_feats = [cc for cc in data_all.columns if '_score' in cc]
    print('Sample of features with score:')
    print(data_all[score_feats].head())

    fname = os.path.join(DAT_DIR, 'data_all.csv')
    data_all.to_csv(fname, index=False)
    print('Save processed data to file {}'.format(fname))
