# -*- coding: utf-8 -*-
import os
import pandas as pd
import pickle
import warnings

REMOVED_WORDS = ['复查', '复诊', '取药', '开药', 'fuchsa', 'fuccha', '挂错号', '买药']
PAT = r'^(?:(?!代诊).)*(' + '|'.join(REMOVED_WORDS) + r')(?:(?!代诊).)*$'

def batch_read(cols:list=['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE'],
               is_filter:bool = True,
               filter_cols:list = ['ILLNESS_DESC'],
               filter_exps:list = [PAT]):
    '''
    批量读取数据
    :param cols: 需要读取的字段
    :param is_filter: 是否过滤数据，默认过滤
    :return:
    '''
    warnings.warn('This function is Expired. Please use OriginalData.batch_read')
    dump_file = './data/data.dmp'
    if not os.path.exists(dump_file):
        data_1 = read('./data/2016年心身科门诊数据.csv', cols = cols, is_filter= is_filter,
                      filter_cols = filter_cols, filter_exps = filter_exps)
        data_2 = read('data/2017年心身科门诊数据.csv', cols = cols, is_filter= is_filter,
                      filter_cols = filter_cols, filter_exps = filter_exps)
        data_3 = read('data/2018年心身科门诊数据.csv', cols = cols, is_filter= is_filter,
                      filter_cols = filter_cols, filter_exps = filter_exps)
        data = pd.concat([data_1, data_2, data_3], ignore_index=False)
        with open(dump_file, 'wb') as f:
            pickle.dump(data, f)
    else:
        with open(dump_file, 'rb') as f:
            data = pickle.load(f)
    return data


def read(file:str,
         cols:list=['PATIENT_ID', 'VISIT_DATE', 'SEX', 'DIAG_DESC', 'ILLNESS_DESC', 'AGE'],
         is_filter:bool = True,
         filter_cols:list = ['ILLNESS_DESC'],
         filter_exps:list = [PAT]):
    '''
    读取csv格式的文件
    :param file: csv文件名
    :param cols: 要保留的字段
    :param filter_cols: 需要过滤的字段
    :param filter_exps: 需要过滤字段的正则表达式
    :return: 读取的数据
    '''
    warnings.warn('This function is Expired. Please use OriginalData.read')
    try:
        data = pd.read_csv(file, encoding='utf-8')
        for c in cols:
            data[c].fillna('', inplace = True)
        if is_filter:
            for col, exp in zip(filter_cols, filter_exps):
                data = my_filter(data, col, exp)
        return data[cols]
    except Exception as e:
        print(e.message)


def my_filter(data:pd.DataFrame, col:str, kw_exp:str):
    '''
    :param data: 要过滤的数据，数据类型为DataFrame
    :param col: 要过滤的字段
    :param kw_exp: 匹配字符的正则表达式
    :return: 过滤后的数据
    '''
    warnings.warn('This function is Expired. Please use OriginalData.filter_data')
    return data[~data[col].str.contains(kw_exp)]


def get_outpatient_volume(data:pd.DataFrame):
    '''
    统计每天的门诊量
    :param data: 原始的门诊量访问数据
    :return: 每天的门诊量
    '''
    result = data.groupby(by='VISIT_DATE', as_index=False).size()
    return pd.DataFrame({'date':result.index,'volume':result.values})


def merage_file(folder, outputfile):
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

def format_print(result, title = ''):
    '''
    按照一定的格式输出想要查看的结果
    :param result: 单个权重的计算结果
    :return:
    '''
    if title:
        print(title)
    for i in result:
        print("{}:{}".format(i[0], i[1]))
    print('='*30)

def get_result_intersection(results):
    '''
    获得计算结果的交集
    :param results: 计算结果
    :return: 交集
    '''
    new_results = list()
    for r in results:
        new_set = set()
        for i in r:
            new_set.add(i[0])
        new_results.append(new_set)
    return set.intersection(*new_results)

def compute_term_rank(analyzer, topK, poses = ['n']):
    '''
    按照不同的及算法方法，对词的重要程度进行排序
    :param analyzer: 分析器
    :param topK: 截断值
    :param poses: 要选取的词性
    :return:
    '''
    print('Computing TF-IDF...')
    tf_idf_tag = analyzer.get_tf_idf_rank(poses, topK)
    print('Computing TextRank...')
    txtrank_tag = analyzer.get_textrank_rank(poses, topK)
    print('Computing Frequency...')
    freq_tag = analyzer.get_freq_rank(poses, topK)
    return [tf_idf_tag, txtrank_tag, freq_tag]

def display_term_rank_result(result, show_detail = False):
    '''
    展示词权重排序的结果
    :param result: 计算结果，其顺序分别为TF-IDF, TextRank, Frequency
    :param show_detail: 是否显示每种结果的详细计算结果
    :return:
    '''
    if show_detail:
        # 是否显示细节，即所有排序的结果
        format_print(result[0], 'TF-IDF results:')
        format_print(result[1], 'TextRank results:')
        format_print(result[2], 'Freqency results:')

    df_tfidf = pd.DataFrame([dict(result[0])]).T
    df_tfidf.columns = ['tfidf']
    df_txtrank = pd.DataFrame([dict(result[1])]).T
    df_txtrank.columns = ['textrank']
    df_freq = pd.DataFrame([dict(result[2])]).T
    df_freq.columns = ['freq']
    df = df_tfidf.join(df_txtrank).join(df_freq)
    intersection = get_result_intersection(result)
    print('top {} intersection are:'.format(len(result[0])))
    print(df.loc[intersection])
    # return df.loc[intersection]

