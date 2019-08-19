# -*- coding: utf-8 -*-
# Created by Huo fei on 2019-08-09
# Copyright (c) 2019 Huo fei. All rights reserved.

import json
import warnings
import sys
import os

dir_path = os.path.abspath(__file__)
sys.path.append(dir_path)
warnings.filterwarnings("ignore")
import jieba
import pandas as pd
import numpy as np
import time
import pickle
from contextlib import contextmanager
from sqlalchemy import create_engine
import pymysql
from libact.base.dataset import Dataset
from libact.models import LogisticRegression
from libact.query_strategies import UncertaintySampling, RandomSampling
from libact.query_strategies.uncertainty_sampling_test import UncertaintySampling_test


@contextmanager
def timer(task_name="timer"):
    print("----{} started".format(task_name))
    t0 = time.time()
    yield
    print("----{} done in {:.0f} seconds".format(task_name, time.time() - t0))


class Query:
    def __init__(self, job_id, source="DataFrame"):
        """
        :param job_id: 待查询样本的任务编号
        :param source: source="DataFrame"：从pkl中获取,source="database",从数据库中获取

        """
        self.source = source
        self.conn = pymysql.connect(host="127.0.0.1",
                                    port=3306,
                                    user="root",
                                    password="r4998730",
                                    db="active",
                                    charset="utf8")
        if self.source == 'DataFrame':

            with open(
                    "/Users/huofei/PycharmProjects/django_ActiveLearning_ColdStart/step1_ColdStart/output_of_cold_start/job_{}.pkl".format(
                            job_id), "rb") as f:
                self.df = pickle.load(f)

        elif self.source == 'Database':
            pass
        else:
            pass
        self.qs = self.build_qs()
        self.job_id = job_id

    @staticmethod
    def parse_json_step_2(json_data):
        """
        查询阶段解析json数据
        :param json_data:
        :return: df:已经标注好的数据,is_init:是否为第一批
        """
        df = pd.DataFrame()
        dic = json.loads(json_data)
        uuid = []
        label = []
        jobid = dic["jobId"]

        uuid_label_kvs = dic["list"]
        for uuid_label_kv in uuid_label_kvs:
            uuid.append(uuid_label_kv["uuid"])
            label.append(uuid_label_kv["label"])

        is_init = dic["list"][0]["isActive"]
        df["uuid"] = uuid
        df["label"] = label
        df["jobId"] = [jobid] * df.shape[0]
        return df, is_init

    def get_pool_from_mysql(self):

        cur = self.conn.cursor()
        sql_get_all = "select * from active_test_1 "
        try:
            cur.execute(sql_get_all)
        except Exception as e:
            self.conn.rollback()
            print("获取全部数据失败")
        data = cur.fetchall()
        return data

    def update_database(self):
        pass

    def get_pool_from_df(self):
        """
        从内存中获取样本池
        :return:
        """
        assert self.df is not None
        X_tmp = []
        for item in self.df["content"]:
            X_tmp.append(item)
        X = np.array(X_tmp)

        y_tmp = []
        for item in self.df["label"]:
            y_tmp.append(item)
        y = np.array(y_tmp)

        pool = Dataset(X, y)
        # 建立索引与uuid的映射关系
        self.i2u_dic = {k: v for (k, v) in zip(range(self.df["uuid"].shape[0]), self.df["uuid"])}
        self.u2i_dic = {k: v for (k, v) in zip(self.df["uuid"], range(self.df["uuid"].shape[0]))}
        return pool

    def get_pool_from_database(self):
        """
        后续与数据库交互使用
        :return:
        """
        pass

    def build_qs(self):

        if self.source == "DataFrame":
            self.pool = self.get_pool_from_df()
        elif self.source == "database":
            self.pool = self.get_pool_from_database()
        else:
            print("未得到样本池，退出查询")
            return
        qs = UncertaintySampling_test(self.pool, method='lc', model=LogisticRegression())
        return qs

    def query(self, json_data):

        # 解析查询阶段传过来的已标注数据,并更新样本池
        query_df, _ = self.parse_json_step_2(json_data)
        lbs = query_df["label"].tolist()
        uuids = query_df["uuid"].tolist()
        ids = [self.u2i_dic[uuid] for uuid in uuids]

        for single_id, lb in zip(ids, lbs):
            self.pool.update(single_id, lb)

        # 返回查询id
        query_ids = self.qs.make_query(n_instances=10).tolist()
        res = []
        for sid in query_ids:
            res.append({"uuid": self.i2u_dic[sid]})
        return res


if __name__ == '__main__':
    q = Query("56")
    json_data_step_2 = """
    {
    	"jobId": "56",
    	"list": [{
    			"uuid": "865eb698826e4751005429bc536161b2",
    			"label": "A",
    			"isActive":true
    		},
    		{
    			"uuid": "a1ec7a459d0dc8de324a88d8aa589de3",
    			"label": "B",
    			"isActive":true
    		}
    	]
    }
    """
    print(q.query(json_data_step_2))
