#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :main.py
# @Time      :2020/2/9 23:16
# @Author    :supakito

from utils import *
from Analyzer.VolumeAnalyzer import VolumeAnalyzer
import copy
from Analyzer.VolumeAnalyzer import Columns
import OriginalData
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


if __name__ == "__main__":
    data = OriginalData.OriginalData.batch_read()
    data = VolumeAnalyzer.process_outpatient_detail(data)

    age_bins = [0, 6, 18, 24, 40, 50, 70, 200]
    age_bins = list(range(0, 120, 10))
    age_cuts = pd.cut(data['AGE'], bins=age_bins, right=False)
    class_cols = [Columns.Date, Columns.Sex, age_cuts]

    vol = VolumeAnalyzer.get_outpatient_volume(data, class_cols)

    print(vol.columns)
    sns.boxplot(x=Columns.Age,
                y=Columns.OutpatientVol,
                hue=Columns.Sex,
                data=vol)
    plt.show()







