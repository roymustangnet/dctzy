import os
from collections import Counter
import pandas as pd
import jieba
import jieba.posseg
import jieba.analyse
import utils


'''
停用词表来源：
https://github.com/goto456/stopwords
'''
class OutpatientDescriptionAnalyzer:
    '''
    从DataFrame的特定字段中
    统计所有词项的频率
    '''
    def __init__(self,
                 data:pd.DataFrame,
                 focused_fields:list=['DIAG_DESC'],
                 user_dict:str='./mydicts.txt',
                 stopwords_file:str ='./stopwords.txt'):
        '''
        :param data: 需要处理的门诊数据
        :param focused_fields: 需要处理的字段
        :param user_dict: 用户自定义的字典
        :param stopwords_file: 停用词文件
        '''
        self._data = data
        self._focused_fields = focused_fields
        self._stopwords = self.__get_stopwords(stopwords_file)
        self._c = Counter()
        jieba.load_userdict(user_dict)
        # jieba.analyse.load_userdict(user_dict)


    def get_freq_rank(self, poses:list=['n', 'a'], topK:int=20, clear=False):
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
        if clear or len(self._c) == 0:
            self._c.clear()
            for field in self._focused_fields:
                for row in self._data[field]:
                    self.__get_words(row, poses)
        return self._c.most_common(topK)

    def get_tf_idf_rank(self, poses:list=['n', 'a'], topK:int=20):
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
        sentence = self.__get_sentence()
        return jieba.analyse.extract_tags(sentence, topK=topK, withWeight=True, allowPOS=poses)


    def get_textrank_rank(self, poses:list=['n', 'a'], topK=20):
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
        sentence = self.__get_sentence()
        return jieba.analyse.textrank(sentence, topK=topK, withWeight=True, allowPOS=poses)

    def __get_words(self, txt, poses:list=['n', 'a']):
        '''
        对文档进行分词
        :param txt: 输入的文本
        :param poses: 需要保留的词性
        :return:
        '''
        words = jieba.posseg.cut(txt)
        for w in words:
            if w.word not in self._stopwords and (not poses or w.flag in poses):
                self._c[w.word] += 1

    def __get_stopwords(self, stopwords_file):
        '''
        获得停用词字典
        同时设置jieba分析器的停用词表
        :param stopwords_file:停用词表的文件
        :return:停用词字典
        '''
        if not(stopwords_file and os.path.exists(stopwords_file)):
            folder = './stopwords'
            stopwords_file = './stopwords.txt'
            utils.merage_file('./stopwords', stopwords_file)
            # 设置jieba的停用词
            jieba.analyse.set_stop_words(stopwords_file)
        return (line.strip() for line in open(stopwords_file, encoding='utf-8').readlines())

    def __get_sentence(self):
        '''
        将所有关心的字段中的文字合并在一起
        :return:
        '''
        sentence = ''
        for field in self._focused_fields:
            for row in self._data[field]:
                try:
                    if not row.endswith('.|。|，|,'):
                        row += '。'
                except Exception as e:
                    print(row)
                sentence += row
        return sentence




