#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :main.py
# @Time      :2020/2/9 23:16
# @Author    :supakito

from utils import *
from Analyzer.VolumeAnalyzer import VolumeAnalyzer
from Analyzer.VolumeAnalyzer import Columns
import OriginalData
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from MainGUI import Main_GUI


if __name__ == "__main__":
    window = Main_GUI()
    window.run()
    # data = OriginalData.OriginalData.batch_read()
    # data = VolumeAnalyzer.process_outpatient_detail(data)
    #
    # # age_bins = [0, 6, 18, 24, 40, 50, 70, 200]
    # age_bins = list(range(30, 100, 10))
    # age_cuts = pd.cut(data['AGE'], bins=age_bins, right=False)
    # class_cols = [Columns.Date, Columns.Sex, age_cuts]
    #
    # vol = VolumeAnalyzer.get_outpatient_volume(data, class_cols)
    # vol = vol.drop(vol[vol[Columns.OutpatientVol]==0].index)
    # print(vol.columns)
    #
    # myfont = FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf', size=14)
    # sns.set(font=myfont.get_name(), style='white')
    #
    # g = sns.boxplot(xname=Columns.Age,
    #                 y=Columns.OutpatientVol,
    #                 hue=Columns.Sex,
    #                 data=vol,
    #                 )
    # plt.xticks(rotation=45)
    # plt.show()
    # g.get_figure().savefig('boxplot_volumn_age_sex.png', dpi=600, bbox_inches='tight')
    #
    # g = sns.violinplot(xname=Columns.Age,
    #                    y=Columns.OutpatientVol,
    #                    hue=Columns.Sex,
    #                    data=vol,
    #                    split=True)
    #
    # plt.xticks(rotation=45)
    # plt.show()
    # g.get_figure().savefig('violinplot_volumn_age_sex.png', dpi=600, bbox_inches='tight')









