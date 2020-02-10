#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :VolumeAnalyzer.py
# @Time      :2020/2/7 10:46
# @Author    :supakito
import pandas as pd
import numpy as np
import copy
import chinese_calendar as cc
import warnings

class Columns:
    Date = 'VISIT_DATE'
    Sex = 'SEX'
    Age = 'AGE'
    OutpatientVol = 'VOLUME'
    Year = 'YEAR'
    Month = 'MONTH'
    Day = 'DAY'
    Week = 'WEEK'
    Is_holiday = 'IS_HOLIDAY'
    Illness = 'ILLNESS'


class VolumeAnalyzer:
    # def __init__(self, data):
    #     self._data = data
    #     assert len(set(self._data.columns) & {'VISIT_DATE', 'SEX', 'AGE'}) == 3
        # self._volume = VolumeAnalyzer.get_outpatient_volume(data)
        # self._volume = VolumeAnalyzer.add_time_info(self._volume)
        # self._volume = VolumeAnalyzer.add_holiday_info(self._volume)

    # def get_volume(self):
    #     return self._volume

    # data必须具备的columns
    _ORIGINAL_DATA_MUST_HAVE_COLS = {'VISIT_DATE', 'SEX', 'AGE', 'DIAG_DESC'}



    @staticmethod
    def get_outpatient_volume(data:pd.DataFrame,
                              class_cols:list = ['VISIT_DATE', 'SEX'],
                              age_bins:list = [0, 6, 18, 24, 40, 50, 70, 130]):
        '''
        根据年龄、性别、来就诊时间等条件，统计每天的门诊量
        :param data: 原始的门诊量访问数据
        # :param bins: 年龄段的划分，可以写成cuts的形式e.g. pd.cut(result['AGE'], bins=age_bins, right=False)
        :return: 分类的统计门诊量
        '''

        assert len(set(data.columns) & VolumeAnalyzer._ORIGINAL_DATA_MUST_HAVE_COLS) == len(VolumeAnalyzer._ORIGINAL_DATA_MUST_HAVE_COLS)

        result = copy.deepcopy(data)

        # 添加各类信息
        result = VolumeAnalyzer.add_time_info(result)
        result = VolumeAnalyzer.add_holiday_info(result)

        # 分类
        result = result.groupby(by = class_cols, as_index=False).size()
        result = result.reset_index()
        result.rename(columns={0: Columns.OutpatientVol}, inplace=True)

        return result

    @staticmethod
    def add_time_info(input_vol, time_col=Columns.Date):
        '''
        为门诊量数据添加星期特征
        :param vol:门诊量数据
        :return: 添加了星期的门诊量数据
        '''
        vol = copy.deepcopy(input_vol)
        vol[Columns.Date] = pd.to_datetime(vol[time_col])
        vol[Columns.Week] = pd.to_datetime(vol[time_col]).dt.weekday + 1
        vol[Columns.Year] = pd.to_datetime(vol[time_col]).dt.year
        vol[Columns.Month] = pd.to_datetime(vol[time_col]).dt.month
        vol[Columns.Day] = pd.to_datetime(vol[time_col]).dt.day
        return vol

    @staticmethod
    def add_holiday_info(vol):
        '''
        为数据添加是否为节假日的信息
        :param vol: 原始的数据
        :return: 添加了'whether_holiday_filter'列，1表示这一天是节假日，为0则表示不是节假日
        '''
        vol = copy.deepcopy(vol)
        vol[Columns.Is_holiday] = pd.to_datetime(vol[Columns.Date]).apply(lambda t: {True:1,False:0}[cc.is_holiday(t)])
        return vol

    @staticmethod
    def get_grouped_result(vol_data: pd.DataFrame, grouped_col: str, staticmethod=np.mean):
        '''
        对数据进行分类统计
        :param vol_data: 门诊量数据
        :param grouped_col: 需要分类的列的名称
        :param staticmethod: 分类之后使用的统计方法
        @for example:
        get_grouped_result(vol_data: pd.DataFrame, grouped_col=Columns.Day, staticmethod=np.mean)
        :return:
        '''
        warnings.warn('This function has been')
        assert grouped_col in vol_data.columns
        grouped = vol_data.groupby(grouped_col)
        return grouped['volume'].agg(staticmethod)

    @staticmethod
    def process_outpatient_detail(data: pd.DataFrame):
        assert len(set(data.columns) & VolumeAnalyzer._ORIGINAL_DATA_MUST_HAVE_COLS) == len(VolumeAnalyzer._ORIGINAL_DATA_MUST_HAVE_COLS)
        result = copy.deepcopy(data)
        # result = VolumeAnalyzer.pod_clean_data(result)
        result = VolumeAnalyzer.pod_add_diagdesc(result)
        return result

    # @staticmethod
    # def pod_clean_data(data: pd.DataFrame):
    #     d = copy.deepcopy(data)
    #     d.drop(d[d['SEX'] == '1'].index, inplace=True)
    #     d.drop(d[d['SEX'] == '2'].index, inplace=True)
    #     d['SEX'] = d['SEX'].apply(lambda x: 'male' if x == '男' else 'female')
    #     assert len(d[d['SEX'] == '1'].index) == 0 and len(d[d['SEX'] == '2'].index) == 0
    #     return d

    @staticmethod
    def pod_add_diagdesc(data:pd.DataFrame):
        '''
        pod表示process Outpatient detail，是用于处理原始数据的
        该函数主要用于从原始的门诊量数据提取出疾病信息，目前仅处理四类疾病：
        - 抑郁症
        - 焦虑症
        - 精神分裂
        - 双相
        :param data:
        :return:
        '''
        def extract_first_ill(desc):
            index = [desc.find(x) if desc.find(x)>=0 else 10000 for x in ill_keywords]
            return ill_names[index.index(min(index))]
        result = copy.deepcopy(data)
        ill_keywords = ['抑郁', '焦虑', '精神分裂', '双相']
        ill_names = ['depression',
                     'anxiety',
                     'schizophrenia',
                     'bipolar_disorder']
        for k, name in zip(ill_keywords, ill_names):
            result['ILLNESS'] = result['DIAG_DESC'].apply(lambda x: name if k in x else '')
        result['ILLNESS'] = result['DIAG_DESC'].apply(extract_first_ill)
        return result




