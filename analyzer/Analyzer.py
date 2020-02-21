#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :Analyzer.py
# @Time      :2020/2/21 18:44
# @Author    :supakito
import warnings
import datetime
import os
import copy
import collections

import pandas as pd
import numpy as np
import chinese_calendar as cc
import jieba
import jieba.posseg
import jieba.analyse


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

        remove_age_cuts_cls_cols = [col for col in class_cols if type(col) == str]
        # 添加各类信息
        if len(set(remove_age_cuts_cls_cols) & {Columns.Week,
                                  Columns.Is_holiday,
                                  Columns.Year,
                                  Columns.Month,
                                  Columns.Day,
                                  }) > 0:
            result = cls.add_time_info(result)
            result = cls.add_holiday_info(result)

        if len(set(remove_age_cuts_cls_cols) & {Columns.Len_after_hld,
                                  Columns.Len_pre_hld,
                                  Columns.Dist_pre_hld,
                                  Columns.Dist_after_hld}) >0:
            result = cls.add_holiday_ext_info(result)

        # 分类
        result = result.groupby(by = class_cols, as_index=False).size()
        result = result.reset_index()
        result.rename(columns={0: Columns.OutpatientVol}, inplace=True)

        return result

    @classmethod
    def add_time_info(cls,
                      input_vol:pd.DataFrame,
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

    @classmethod
    def add_holiday_info(cls, vol:pd.DataFrame):
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
    #     d['SEX'] = d['SEX'].apply(lambda xname: 'male' if xname == '男' else 'female')
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


class OutpatientDescriptionAnalyzer:
    '''
    从DataFrame的特定字段中
    统计所有词项的频率
    '''
    # 用户词典的位置，用于分词，不过好像没有什么效果
    __user_dict = './mydicts.txt'
    # 停用词表的位置，来源于https://github.com/goto456/stopwords
    __stopwords_file = './stopwords.txt'

    @classmethod
    def get_freq_rank(cls,
                      data:pd.DataFrame,
                      focused_fields:list,
                      poses:list=['n', 'a'],
                      topK:int=20, clear=False):
        '''
        获得词频最高的词项
        :param topK: 前n项的数量
        :param poses: 词性，可选择的包括
        n	普通名词	f	方位名词	s	处所名词	t	时间
        nr	人名	ns	地名	nt	机构名	nw	作品名
        nz	其他专名	v	普通动词	vd	动副词	vn	名动词
        a	形容词	ad	副形词	an	名形词	d	副词
        m	数量词	q	量词	r	代词	p	介词
        c	连词	u	助词	xc	其他虚词	w	标点符号
        PER	人名	LOC	地名	ORG	机构名	TIME	时间
        :return: 词频排名靠前的前N个词项
        '''
        stopwords = cls.__get_stopwords(cls.__stopwords_file)
        c = collections.Counter()
        for field in focused_fields:
            for row in data[field]:
                cls.__get_words(row, c, poses, stopwords)
        return c.most_common(topK)
        # if clear or len(self._c) == 0:
        #     self._c.clear()
        #     for field in self._focused_fields:
        #         for row in self._data[field]:
        #             self.__get_words(row, poses)
        # return self._c.most_common(topK)

    @classmethod
    def get_tf_idf_rank(cls,
                        data:pd.DataFrame,
                        focused_fields:list,
                        poses:list=['n', 'a'],
                        topK:int=20):
        '''
        获得TF-IDF的排名靠前的词项
        :param topK: 前n项的数量
        :param poses: 词性，可选择的包括
        n	普通名词	f	方位名词	s	处所名词	t	时间
        nr	人名	ns	地名	nt	机构名	nw	作品名
        nz	其他专名	v	普通动词	vd	动副词	vn	名动词
        a	形容词	ad	副形词	an	名形词	d	副词
        m	数量词	q	量词	r	代词	p	介词
        c	连词	u	助词	xc	其他虚词	w	标点符号
        PER	人名	LOC	地名	ORG	机构名	TIME	时间
        :return: TF-IDF排名靠前的前N个词项
        '''
        sentence = cls.__get_sentence(data, focused_fields)
        return jieba.analyse.extract_tags(sentence, topK=topK, withWeight=True, allowPOS=poses)

    @classmethod
    def get_textrank_rank(cls, poses:list=['n', 'a'], topK=20):
        '''
        获得TextRank最高的词项
        :param topK: 前n项的数量
        :param poses: 词性，可选择的包括
        n	普通名词	f	方位名词	s	处所名词	t	时间
        nr	人名	ns	地名	nt	机构名	nw	作品名
        nz	其他专名	v	普通动词	vd	动副词	vn	名动词
        a	形容词	ad	副形词	an	名形词	d	副词
        m	数量词	q	量词	r	代词	p	介词
        c	连词	u	助词	xc	其他虚词	w	标点符号
        PER	人名	LOC	地名	ORG	机构名	TIME	时间
        :return: TextRank排名靠前的前N个词项
        '''
        sentence = cls.__get_sentence()
        return jieba.analyse.textrank(sentence, topK=topK, withWeight=True, allowPOS=poses)

    @staticmethod
    def __get_sentence(data, focused_fields):
        '''
        将所有关心的字段中的文字合并在一起
        :return:
        '''
        sentence = ''
        for field in focused_fields:
            for row in data[field]:
                try:
                    if not row.endswith('.|。|，|,'):
                        row += '。'
                except Exception as e:
                    print(row)
                sentence += row
        return sentence

    @staticmethod
    def __merage_file(folder, outputfile):
        '''
        合并文件
        :param folder:原始文件所在的文件夹
        :param outputfile:需要输出的文件的位置
        :return:
        '''
        with open(outputfile, 'w', encoding='utf-8') as newfile:
            for f in os.listdir(folder):
                with open(os.path.join(folder, f), 'r',encoding='utf-8') as readfile:
                    newfile.write(readfile.read())

    @classmethod
    def __get_stopwords(cls, stopwords_file):
        '''
        获得停用词字典
        同时设置jieba分析器的停用词表
        :param stopwords_file:停用词表的文件
        :return:停用词字典
        '''
        if not(stopwords_file and os.path.exists(stopwords_file)):
            folder = './stopwords'
            stopwords_file = './stopwords.txt'
            cls.__merage_file('./stopwords', stopwords_file)
            # 设置jieba的停用词
            jieba.analyse.set_stop_words(stopwords_file)
        return (line.strip() for line in open(stopwords_file, encoding='utf-8').readlines())

    @classmethod
    def __get_words(cls,
                    txt,
                    counter:collections.Counter,
                    poses:list=['n', 'a'],
                    stopwords:list=[]):
        '''
        对文档进行分词
        :param txt: 输入的文本
        :param poses: 需要保留的词性
        :param stopwords: 停用词
        :return:
        '''
        words = jieba.posseg.cut(txt)
        for w in words:
            if w.word not in stopwords and (not poses or w.flag in poses):
                counter[w.word] += 1
