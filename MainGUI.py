#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :MainGUI.py
# @Time      :2020/2/17 11:34
# @Author    :supakito
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter import Toplevel
from tkinter import Label
from OriginalData import OriginalData
from Analyzer.VolumeAnalyzer import Columns
from Analyzer.VolumeAnalyzer import VolumeAnalyzer
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


class Main_GUI():
    def __init__(self):
        self.top = tk.Tk()
        self.top.title('Outpatient Volume Analysis Tools')
        self.top.geometry('500x300')
        # 原始的门诊信息
        self.__original_data = pd.DataFrame()
        # 根据门诊量统计出的门诊量信息
        self.__vol_data = pd.DataFrame()
        self.__init_menu()
        self.__init_table()

    def run(self):
        self.top.mainloop()

    def __init_table(self):
        self.scrollbar = tk.Scrollbar(self.top, )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.table = ttk.Treeview(self.top,
                                  yscrollcommand=self.scrollbar.set,
                                  show='headings')

    def __init_menu(self):
        menubar = tk.Menu(self.top)
        file_menu = tk.Menu(self.top)
        for item, func in zip(['打开CSV', '打开序列化文件', '另存为...'],
                              (self.__open_csv_files, self.__open_dump_file, self.__save_file)):
            file_menu.add_command(label=item, command=func)
        menubar.add_cascade(label="文件", menu=file_menu)

        process_menu = tk.Menu(self.top)
        for item, func in zip(['分组统计'], [self.__statistic]):
            process_menu.add_command(label=item, command=func)
        menubar.add_cascade(label="数据处理", menu=process_menu)
        self.top['menu'] = menubar

    def __statistic(self):
        if len(self.__original_data) == 0:
            messagebox.showinfo('提示信息','尚未读取数据，请加载原始的门诊量数据')
            return
        self.__init_stat_config_window()

    def __init_stat_config_window(self):
        '''
        初始化门诊量统计的配置窗口
        :return:
        '''
        def stat_config_dropdown_list_selected(event):
            col1 = self._comvalue_1.get()
            col2 = self._comvalue_2.get()
            if col1 == Columns.Age:
                age_edit_box1.grid(column=2, row=0, )
            else:
                age_edit_box1.grid_forget()
            if col2 == Columns.Age:
                age_edit_box2.grid(column=2, row=1, )
            else:
                age_edit_box2.grid_forget()

        def confirm_button_click():
            col1 = self._comvalue_1.get()
            col2 = self._comvalue_2.get()
            if not col1:
                messagebox.showinfo('Error', '请选择一列进行统计')
                return
            if col1==col2==Columns.Age:
                messagebox.showinfo('Error', '两列不能都为AGE')
                return

            if col1 == Columns.Age:
                age_bins = age_edit_box1.get()
            elif col1 == Columns.Age:
                age_bins = age_edit_box2.get()
            else:
                age_bins = list()
            stat_conf_window.destroy()
            self.__plot(col1, col2, age_bins)


        stat_conf_window = Toplevel()
        stat_conf_window.title('分组统计配置')
        stat_conf_window.geometry('550x100')
        stat_conf_window.resizable(0, 0)
        selectable_items = [
            # Columns.Date,
            Columns.Year,
            Columns.Month,
            Columns.Day,
            Columns.Week,
            Columns.Is_holiday,
            Columns.Sex,
            Columns.Age,
            Columns.Len_pre_hld,
            Columns.Len_after_hld,
            Columns.Dist_pre_hld,
            Columns.Dist_after_hld
        ]

        lb1 = Label(stat_conf_window, text="分组统计参数1（x轴）：")
        lb1.grid(column=0, row=0, padx=8, pady=4)
        lb1 = Label(stat_conf_window, text="分组统计参数2（分组，可不选）：")
        lb1.grid(column=0, row=1, padx=8, pady=4)

        self._comvalue_1 = tk.StringVar()
        dropdownlist_1 = ttk.Combobox(stat_conf_window, textvariable=self._comvalue_1, state='readonly')  # 初始化
        dropdownlist_1["values"] = selectable_items
        dropdownlist_1.grid(column=1, row=0, padx=8, pady=4)
        dropdownlist_1.bind("<<ComboboxSelected>>", stat_config_dropdown_list_selected)

        self._comvalue_2 = tk.StringVar()
        dropdownlist_2 = ttk.Combobox(stat_conf_window, textvariable=self._comvalue_2, state='readonly')  # 初始化
        dropdownlist_2["values"] = selectable_items
        dropdownlist_2.grid(column=1, row=1, padx=8, pady=4)
        dropdownlist_2.bind("<<ComboboxSelected>>", stat_config_dropdown_list_selected)

        age_edit_box1 = tk.Entry(stat_conf_window)
        age_edit_box1.insert(0, '10, 20, 30, 40, 50, 60, 70, 80, 90')
        age_edit_box2 = tk.Entry(stat_conf_window)
        age_edit_box2.insert(0, '10, 20, 30, 40, 50, 60, 70, 80, 90')

        confirm_button = tk.Button(stat_conf_window, text="开始绘图", command=confirm_button_click)
        confirm_button.grid(column=1, row=2, padx=8, pady=4)

    def __save_file(self):
        if len(self.__original_data) == 0:
            messagebox.showinfo('','尚未加载数据')
            return
        file_path = filedialog.asksaveasfilename(title=u'保存文件',
                                                 filetypes=[('dump','dmp'), ("csv", ".csv")],
                                                 defaultextension='.dmp')
        if file_path.endswith('.csv'):
            OriginalData.save_csv_file(self.__original_data, file_path)
        elif file_path.endswith('.dmp'):
            OriginalData.save_dump_file(self.__original_data, file_path)
        else:
            return
    def __open_csv_files(self):
        '''
        读取多个csv文件
        :return:
        '''
        files = filedialog.askopenfilenames(title='读取数据文件',
                                            filetypes=[('csv', '*.csv')])
        if files and len(files) > 0:
            self.__original_data = OriginalData.read_csv_files(files)
            self.__show_data(self.__original_data)

    def __open_dump_file(self):
        '''
        读取序列化的文件
        :return:
        '''
        file = filedialog.askopenfilename(title='读取序列化的数据文件',
                                          filetypes=[('dump',('*.dump', '*.dmp'))])
        if file:
            self.__original_data = OriginalData.read_dump_file(file)
            self.__show_data(self.__original_data)

    def __show_data(self,
                    data:pd.DataFrame,
                    col_length = [90, 90, 70, 180, 180, 40]):
        '''
        展示加载的数据
        :param data:需要显示的数据
        :param col_length: 每一列的长度
        :return:
        '''
        self.table['columns'] = data.columns.to_list()
        for c, w in zip(data.columns, col_length):
            self.table.column(c, width=w, anchor='center')
            self.table.heading(c, text=c)

        for i in self.table.get_children():
            # 清空原有的数据内容
            self.table.delete(i)
        for index, row in data.iterrows():
            self.table.insert('', 'end', values=row.to_list())
            if index>100:
                break

        self.scrollbar.config(command=self.table.yview)
        self.table.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

    def __plot(self, xname, group, agebins=[]):
        class_cols = [Columns.Date]
        if xname != Columns.Age:
            class_cols.append(xname)
        else:
            age_cuts = pd.cut(self.__original_data['AGE'],
                              bins=[int(a) for a in agebins.split(',')], right=False)
            class_cols.append(age_cuts)

        if group != Columns.Age:
            class_cols.append(group)
        else:
            age_cuts = pd.cut(self.__original_data['AGE'],
                              bins=[int(a) for a in agebins.split(',')], right=False)
            class_cols.append(age_cuts)

        vol = VolumeAnalyzer.get_outpatient_volume(self.__original_data, class_cols)
        myfont = FontProperties(fname=r'C:\Windows\Fonts\simhei.ttf', size=14)
        sns.set(font=myfont.get_name(), style='white')

        g = sns.boxplot(x=xname,
                        y=Columns.OutpatientVol,
                        hue=group,
                        data=vol,
                        )
        plt.xticks(rotation=45)
        plt.show()


