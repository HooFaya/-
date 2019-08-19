# -*- coding: utf-8 -*-
# Created by Huo fei on 2019-08-08
# Copyright (c) 2019 Huo fei. All rights reserved.
import json
import warnings

warnings.filterwarnings("ignore")
import jieba
import pandas as pd
import numpy as np
import time
from contextlib import contextmanager
from sqlalchemy import create_engine
import pickle
import os


@contextmanager
def timer(task_name="timer"):
    print("----{} started".format(task_name))
    t0 = time.time()
    yield
    print("----{} done in {:.0f} seconds".format(task_name, time.time() - t0))


class ColdStart:
    def __init__(self, json_data_cold_start):
        """
        加载全量W2V向量与词典
        """
        dir_path = os.path.dirname(os.path.abspath(__file__))
        self.dir_path = dir_path
        full_matrix_path = os.sep.join([dir_path, "Financial_w2v", "w2v_full_matrix.pkl"])
        full_vocabulary_path = os.sep.join([dir_path, "Financial_w2v", "w2v_full_vocabulary.pkl"])

        if not os.path.exists(full_vocabulary_path): raise FileNotFoundError("full_vocabulary_path is not found")
        if not os.path.exists(full_matrix_path): raise FileNotFoundError("full_matrix_path is not found")

        with open(full_matrix_path, "rb") as f:
            self.full_matrix = pickle.load(f)

        with open(full_vocabulary_path, "rb") as f:
            self.full_vocabulary = pickle.load(f)

        self.data_df = self.parse_json_step_1(json_data_cold_start)

    @staticmethod
    def parse_json_step_1(json_data):
        """
        冷启动阶段解析json数据
        :param json_data:Json格式的数据
        :return:包含jobId,uuid,content字段的DataFrame
        """
        dic = json.loads(json_data)
        df = pd.DataFrame()
        jobId = dic["jobId"]
        uuid, content = [], []
        content_uuid_kvs = dic["list"]
        for content_uuid_kv in content_uuid_kvs:
            uuid.append(content_uuid_kv["uuid"])
            content.append(content_uuid_kv["content"])
        df["jobId"] = [jobId] * len(uuid)
        df["uuid"] = uuid
        df["content"] = content
        return df

    @staticmethod
    def jieba_cut(texts):
        res = []
        for text in texts:
            text_cut = jieba.cut(text)
            # res.append(" ".join(text_cut))
            res.append(text_cut)
        return res

    @staticmethod
    def get_vector(cut_words, full_matrix, full_vocabulary):
        vector_list = [full_matrix[full_vocabulary[word]] for word in cut_words if word in full_vocabulary]
        # 当语料库中没有任何该句子中的词时，用0填充,这种情况很少，3万条数据只有一条是这样的,长这样：'新年好'，这居然切成个词。。
        if not vector_list:
            vector_list = [[0] * 300]
        vector_df = pd.DataFrame(vector_list)
        cutWord_vector = vector_df.mean(axis=0).values.tolist()
        return cutWord_vector

    def get_custom_matrix(self, full_matrix, full_vocabulary, df):
        cut_words_list = self.jieba_cut(df["content"])
        custom_matrix = []
        for cut_words in cut_words_list:
            custom_matrix.append(self.get_vector(cut_words, full_matrix, full_vocabulary))
        custom_matrix = [item for item in custom_matrix if len(item) == 300]
        res = np.array(custom_matrix)
        return res

    def start(self, to_mysql=False):
        """
        :param :
        :param to_mysql: 如果为True,则把转换好的数据表(DataFrame)存在MySql里，否则直接返回数据表
        :return:
        """
        df = self.data_df
        matrix = self.get_custom_matrix(self.full_matrix, self.full_vocabulary, self.data_df)
        df["content"] = [item.tolist() for item in matrix]
        df["label"] = [None] * df.shape[0]
        self_job_id = df["jobId"][0]
        if to_mysql:
            df["content"] = df["content"].astype(np.str)
            df["label"] = [None] * df.shape[0]
            engine = create_engine('mysql+pymysql://root:r4998730@localhost:3306/active')
            try:
                df.to_sql('active_test_1', engine, index=None, if_exists="replace")
                return
            except:
                print("冷启动存入数据库失败")
        try:

            with open("{0}/output_of_cold_start/job_{1}.pkl".format(self.dir_path, self_job_id), "wb") as f:
                pickle.dump(df, f)
            msg = "Cold start JOB_{} successfully".format(self_job_id)
            return msg
        except:
            return "Fail to save output_of_cold_start_job_{}.pkl".format(self_job_id)


if __name__ == '__main__':
    json_data_for_cold_start = """
{
	"jobId": 1234,
	"list": [{
		"uuid": "865eb698826e4751005429bc536161b2",
		"content": "【比亚迪：预计在2022年前后把电池业务分拆独立上市】 比亚迪8月7日在互动平台上回答投资者提问时表示，目前公司动力电池业务分拆上市在稳步推进中，预计在2022年前后会把电池整个分拆出去独立上市。"
	}, {
		"uuid": "a1ec7a459d0dc8de324a88d8aa589de3",
		"content": "印度SENSEX和NIFTY指数一度跌0.5%，先前印度央行罕见地降息35个基点以刺激经济。"
	}, {
		"uuid": "3ac537f2ab95217a9deb4e457133f7c1",
		"content": "韩国KOSPI指数收盘下跌0.41%，报1909.70点。"
	}, {
		"uuid": "7748eafa0e365ef181663083f24ef5a3",
		"content": "【江苏：全面实行养老机构登记备案制】7日从江苏省民政厅获悉，为深化养老服务领域“放管服”改革，优化养老服务营商环境，江苏省民政厅、省市场监管局日前联合印发通知，部署全面开展养老机构登记备案管理工作。（新华社）"
	}],
	"questions": [{
		"title": "发金刚楠",
		"options ": [{
			"name": "A 与中金所有关"
		}, {
			"name": "B 与中金所无关"

		}, {
			"name": "C 不知道"
		}]
	}, {
		"title": "测试用例",
		"options ": [{
			"name": "A 与期货有关"
		}, {
			"name": "B 与期货无关"

		}, {
			"name": "C 不知道"
		}]
	}]
}
"""
    with timer("__cold_start__"):
        cs = ColdStart(json_data_for_cold_start)
        msg = cs.start()
        # print((df.iloc[0,:]))
        print(msg)
