#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :test.py
# @Time      :2020/2/23 21:42
# @Author    :supakito

from analyzer.Analyzer import VolumeAnalyzer
from analyzer.Analyzer import Columns
from OriginalData import OriginalData
from config import Config
import pandas as pd

if __name__ == "__main__":
    path = './data/data.dmp'
    profile = Config.load()
    data = OriginalData.read_dump_file(file = path,
                                       cols = profile.focused_fields)
    class_cols = [Columns.Date, Columns.Week]
    age_cuts = pd.cut(data['AGE'],
                      bins=[10, 20, 30, 40, 50, 60, 70, 80, 90], right=False)
    class_cols.append(age_cuts)
    vol = VolumeAnalyzer.get_outpatient_volume(data, class_cols)