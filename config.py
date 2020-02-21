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
        return Profile(json_data['_focused_fields'])

    @classmethod
    def store(cls, data):
        with open(cls.__config_file, 'w') as json_file:
            json_file.write(json.dumps(data, default = lambda obj: obj.__dict__, indent=4))

    @classmethod
    def load(cls):
        if not os.path.exists(cls.__config_file):
            cls.store(Profile(['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE']))
        with open(cls.__config_file) as json_file:
            try:
                profile = json.load(json_file)
            except:
                profile = Profile([])
            return profile

class Profile:
    def __init__(self, focused_fields):
        self._focused_fields = focused_fields

if __name__ == '__main__':
    p = Profile(['a','b','c'])
    print(Config.load())