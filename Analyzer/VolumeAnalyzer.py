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
import datetime


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
    Len_pre_hld = 'LEN_PRE_HOLIDAY'
    Len_after_hld = 'LEN_AFTER_HOLIDAY'
    Dist_pre_hld = 'DIST_PRE_HOLIDAY'
    Dist_after_hld = 'DIST_AFTER_HOLIDAY'


class VolumeAnalyzer:

    # data必须具备的columns
    __ORIGINAL_DATA_MUST_HAVE_COLS = {'VISIT_DATE', 'SEX', 'AGE', 'DIAG_DESC'}
    __ill_keywords = ['抑郁', '焦虑', '精神分裂', '双相']
    __ill_names = ['depression',
                 'anxiety',
                 'schizophrenia',
                 'bipolar_disorder']
    @property
    def ill_names(cls):
        return cls.__ill_names

    @classmethod
    def get_outpatient_volume(cls,
                              data:pd.DataFrame,
                              class_cols:list = ['VISIT_DATE'],
                              ):
        '''
        根据年龄、性别、来就诊时间等条件，统计每天的门诊量
        :param data: 原始的门诊量访问数据
        # :param bins: 年龄段的划分，可以写成cuts的形式e.g. pd.cut(result['AGE'], bins=age_bins, right=False)
        :return: 分类的统计门诊量
        '''

        assert len(set(data.columns) & cls.__ORIGINAL_DATA_MUST_HAVE_COLS) == len(cls.__ORIGINAL_DATA_MUST_HAVE_COLS)
        result = copy.deepcopy(data)

        # 添加各类信息
        if len(set(class_cols) & {Columns.Week,
                                  Columns.Is_holiday,
                                  Columns.Year,
                                  Columns.Month,
                                  Columns.Day,
                                  }) > 0:
            result = cls.add_time_info(result)
            result = cls.add_holiday_info(result)

        if len(set(class_cols) & {Columns.Len_after_hld,
                                  Columns.Len_pre_hld,
                                  Columns.Dist_pre_hld,
                                  Columns.Dist_after_hld}) >0:
            result = cls.add_holiday_ext_info(result)

        # 分类
        result = result.groupby(by = class_cols, as_index=False).size()
        result = result.reset_index()
        result.rename(columns={0: Columns.OutpatientVol}, inplace=True)

        return result

    @staticmethod
    def add_time_info(input_vol:pd.DataFrame,
                      time_col=Columns.Date):
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

    @classmethod
    def add_holiday_ext_info(cls, data: pd.DataFrame):
        # assert Columns.Is_holiday in data.columns
        tmp_data = copy.deepcopy(data)
        tmp_data[Columns.Date] = pd.to_datetime(tmp_data[Columns.Date])
        df = pd.DataFrame({Columns.Date:tmp_data[Columns.Date].drop_duplicates()})
        df = cls.__supplementary_days(df)
        df[Columns.Dist_pre_hld] = 0
        df[Columns.Dist_after_hld] = 0
        df[Columns.Len_pre_hld] = 0
        df[Columns.Len_after_hld] = 0
        # 前一个假期的长度
        pre_h_length = 0
        #距离前一个假期的时间，也可以看作是记录工作日的长度
        dist_pre_h = 0
        recorded_workday_indexes = list()
        # 一个阶跃信号，表示当前处于假期，还是处于工作日
        flag_up_step = True
        for index, row in df.iterrows():
            if row[Columns.Is_holiday] == 1:
                if not flag_up_step:
                    # 从工作日切换到了休息日
                    flag_up_step = True
                    pre_h_length = 0
                    # 更新前面工作日的距离
                    df.loc[recorded_workday_indexes, Columns.Dist_after_hld] = \
                        dist_pre_h + 1 - df.loc[recorded_workday_indexes, Columns.Dist_pre_hld]
                pre_h_length += 1
            else:
                if flag_up_step:
                    # 从休息日切换到了工作日
                    flag_up_step = False
                    dist_pre_h = 0
                    # 更新记录的工作日后面假期的长度
                    df.loc[recorded_workday_indexes, Columns.Len_after_hld] = pre_h_length
                    recorded_workday_indexes.clear()
                dist_pre_h += 1
                df.loc[index, Columns.Len_pre_hld] = pre_h_length
                df.loc[index, Columns.Dist_pre_hld] = dist_pre_h
                recorded_workday_indexes.append(index)
        result = pd.merge(tmp_data, df, how='left', on=[Columns.Date])
        return result

    @classmethod
    def __supplementary_days(cls, data: pd.DataFrame):
        '''补充时间，使得数据中的时间以完整的假期开始，以完整的假期结束'''
        # 对数据按照时间进行排序
        df = copy.deepcopy(data)
        df.index = pd.to_datetime(df[Columns.Date])
        del df[Columns.Date]
        df.sort_index(inplace=True)
        df.reset_index(inplace=True)
        upday = cls.__get_datetime_range(df.iloc[0][Columns.Date], -1)
        lowerday = cls.__get_datetime_range(df.iloc[-1][Columns.Date], 1)
        newdf = pd.DataFrame({Columns.Date:pd.date_range(upday, lowerday)})
        result = pd.merge(newdf, df, how='left', on=[Columns.Date])
        result[Columns.Is_holiday] = pd.to_datetime(result[Columns.Date])\
            .apply(lambda t: {True:int(1),False:int(0)}[cc.is_holiday(t)])
        if Columns.OutpatientVol in result.columns:
            result[Columns.OutpatientVol].fillna(0, inplace=True)
        return result

    @classmethod
    def __get_datetime_range(cls, current, offset):
        '''
        获得时间的上下限，目标是找到一个日期，该日期是有休息日变成工作日的界限
        offset为负数时，则反过来
        :param current:当前日期
        :param offset:偏移量
        :return:
        '''
        while True:
            another_day = cls.__get_offset_date(current, offset)
            current_is_holiday = cc.is_holiday(current)
            another_day_is_holiday = cc.is_holiday(another_day)
            if not another_day_is_holiday and current_is_holiday:
                return current
            else:
                current = another_day
                before_day = cls.__get_offset_date(current, offset)

    @classmethod
    def __get_offset_date(cls, current, offset):
        '''
        获得时间的偏移量
        :param current: 当前日期
        :param offset: 时间偏移的距离，单位为天
        :return:
        '''
        offset = datetime.timedelta(days=offset)
        re_date = current + offset
        return re_date

    @classmethod
    def add_dist_pre_holiday(cls, data: pd.DataFrame):
        '''
        当天之前假日的距离
        :param data:
        :return:
        '''
        result = copy.deepcopy(data)
        result[Columns.Dist_pre_hld] = 0
        result['Shift'] = result[Columns.is_holiday].shift(1)
        return result


    @classmethod
    def add_dist_after_holiday(cls, data: pd.DataFrame):
        '''
        当天之后假日的距离
        :param data:
        :return:
        '''
        result = copy.deepcopy(data)
        return result

    @classmethod
    def add_len_of_recent_pre_holiday(cls, data: pd.DataFrame):
        '''
        当天之前假期的长度
        :param data:
        :return:
        '''
        result = copy.deepcopy(data)
        return result

    @classmethod
    def add_len_of_recent_after_holiday(cls, data: pd.DataFrame):
        '''
        当天之后假期的长度
        :param data:
        :return:
        '''
        result = copy.deepcopy(data)
        return result

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

    @classmethod
    def process_outpatient_detail(cls, data: pd.DataFrame):
        assert len(set(data.columns) & cls.__ORIGINAL_DATA_MUST_HAVE_COLS) == len(cls.__ORIGINAL_DATA_MUST_HAVE_COLS)
        result = copy.deepcopy(data)
        # result = cls.pod_clean_data(result)
        result = cls.pod_add_diagdesc(result)
        return result

    # @staticmethod
    # def pod_clean_data(data: pd.DataFrame):
    #     d = copy.deepcopy(data)
    #     d.drop(d[d['SEX'] == '1'].index, inplace=True)
    #     d.drop(d[d['SEX'] == '2'].index, inplace=True)
    #     d['SEX'] = d['SEX'].apply(lambda x: 'male' if x == '男' else 'female')
    #     assert len(d[d['SEX'] == '1'].index) == 0 and len(d[d['SEX'] == '2'].index) == 0
    #     return d

    @classmethod
    def pod_add_diagdesc(cls, data:pd.DataFrame):
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
            index = [desc.find(x) if desc.find(x)>=0 else 10000 for x in cls.__ill_keywords]
            return cls.__ill_names[index.index(min(index))]
        result = copy.deepcopy(data)
        for k, name in zip(cls.__ill_keywords, cls.__ill_names):
            result[name] = result['DIAG_DESC'].apply(lambda x: '1' if k in x else '0')
        result['ILLNESS'] = result['DIAG_DESC'].apply(extract_first_ill)
        return result
#
# if __name__ == '__main__':
#     import OriginalData
#     data = OriginalData.OriginalData.batch_read()
#     data = VolumeAnalyzer.process_outpatient_detail(data)
#     vol = VolumeAnalyzer.get_outpatient_volume(data)
#     print(vol.head())

