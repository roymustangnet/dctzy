#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :config.py
# @Time      :2020/2/21 20:10
# @Author    :supakito

import json
import os

class Config:
    __config_file = './conf.json'

    @staticmethod
    def obj2json(obj):
        pass
    @classmethod
    def json2obj(cls, json_data):
        return Profile(focused_fields =json_data['focused_fields'],
                       nlp_fields = json_data['nlp_fields'],
                       poses = json_data['poses'],
                       is_filter = json_data['is_filter'],
                       topK = json_data['topK'])

    @classmethod
    def store(cls, data):
        with open(cls.__config_file, 'w') as json_file:
            json_file.write(json.dumps(data, default = lambda obj: obj.__dict__, indent=4))

    @classmethod
    def load(cls):
        if not os.path.exists(cls.__config_file):
            cls.store(Profile(focused_fields = ['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE'],
                              nlp_fields = ['DIAG_DESC', 'ILLNESS_DESC'],
                              poses = ['n', 'a'],
                              is_filter = True,
                              topK = 20))
        with open(cls.__config_file) as json_file:
            try:
                profile = cls.json2obj(json.load(json_file))
            except:
                profile = Profile([],[])
            return profile

class Profile:
    def __init__(self,
                 focused_fields,
                 nlp_fields,
                 poses:list = ['n', 'a'],
                 is_filter = True,
                 topK = 20):
        # 需要保留的列名
        self.focused_fields = focused_fields
        # 能够进行NLP分析的列名
        self.nlp_fields = nlp_fields
        # 需要统计的词性
        self.poses = poses
        # 是否过滤取药、复诊的人员
        self.is_filter = is_filter
        # 选择最高的词
        self.topK = topK

if __name__ == '__main__':
    print(Config.load())