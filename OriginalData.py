#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :OriginalData.py
# @Time      :2020/2/10 23:44
# @Author    :supakito
import pandas as pd
import pickle
import os
import copy


class OriginalData():
    _REMOVED_WORDS = ['复查', '复诊', '取药', '开药', 'fuchsa', 'fuccha', '挂错号', '买药']
    _PAT = r'^(?:(?!代诊).)*(' + '|'.join(_REMOVED_WORDS) + r')(?:(?!代诊).)*$'
    @staticmethod
    def batch_read(cols: list = ['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE'],
                   is_filter: bool = True,
                   filter_cols: list = ['ILLNESS_DESC'],
                   filter_exps: list = [_PAT],
                   dump_file: str = './data/data.dmp'):
        '''
        批量读取数据
        :param cols: 需要读取的字段
        :param is_filter: 是否过滤数据，默认过滤
        :return:
        '''

        if not os.path.exists(dump_file):
            data_1 = OriginalData.read('./data/2016年心身科门诊数据.csv', cols=cols, is_filter=is_filter,
                          filter_cols=filter_cols, filter_exps=filter_exps)
            data_2 = OriginalData.read('data/2017年心身科门诊数据.csv', cols=cols, is_filter=is_filter,
                          filter_cols=filter_cols, filter_exps=filter_exps)
            data_3 = OriginalData.read('data/2018年心身科门诊数据.csv', cols=cols, is_filter=is_filter,
                          filter_cols=filter_cols, filter_exps=filter_exps)
            data = pd.concat([data_1, data_2, data_3], ignore_index=False)
            with open(dump_file, 'wb') as f:
                pickle.dump(data, f)
        else:
            with open(dump_file, 'rb') as f:
                data = pickle.load(f)
        return data

    @staticmethod
    def read(file: str,
             cols: list = ['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE'],
             is_filter: bool = True,
             filter_cols: list = ['ILLNESS_DESC'],
             filter_exps: list = [_PAT]):
        '''
        读取csv格式的文件
        :param file: csv文件名
        :param cols: 要保留的字段
        :param filter_cols: 需要过滤的字段
        :param filter_exps: 需要过滤字段的正则表达式
        :return: 读取的数据
        '''
        try:
            data = pd.read_csv(file, encoding='utf-8')
            for c in cols:
                data[c].fillna('', inplace=True)
            if is_filter:
                for col, exp in zip(filter_cols, filter_exps):
                    data = OriginalData.filter_data(data, col, exp)
            data = OriginalData.clean_data(data)
            return data[cols]
        except Exception as e:
            print(e.message)

    @staticmethod
    def filter_data(data: pd.DataFrame,
                    col: str,
                    kw_exp: str):
        '''
        :param data: 要过滤的数据，数据类型为DataFrame
        :param col: 要过滤的字段
        :param kw_exp: 匹配字符的正则表达式
        :return: 过滤后的数据
        '''
        return data[~data[col].str.contains(kw_exp)]

    @staticmethod
    def clean_data(data:pd.DataFrame):
        '''
        数据清洗
        :param data: 需要清洗的数据
        :return: 清洗后的数据
        '''
        d = copy.deepcopy(data)
        d.drop(d[d['SEX'] == '1'].index, inplace=True)
        d.drop(d[d['SEX'] == '2'].index, inplace=True)
        d['SEX'] = d['SEX'].apply(lambda x: 'Male' if x == '男' else 'Female')
        assert len(d[d['SEX'] == '1'].index) == 0 and len(d[d['SEX'] == '2'].index) == 0
        return d

if __name__ == '__main__':
    print(len(OriginalData.batch_read()))
