# -*- coding:utf-8 -*-
import os
from return_answer.config import semantic_slot
import re
import json
import requests
import random
from py2neo import Graph
import pandas as pd
from config import *

graph = Graph(host="127.0.0.1",
              http_port=7474,
              user="neo4j",
              password="jiangsir")


def slot_recognizer(text):
    # url = 'http://127.0.0.1:60061/service/api/medical_ner'
    # data = {"text_list": [text]}
    # headers = {'Content-Type': 'application/json;charset=utf8'}
    # reponse = requests.get(url, data=json.dumps(data), headers=headers)
    # if reponse.status_code == 200:
    #     reponse = json.loads(reponse.text)
    #     return reponse['data']
    # else:
    #     return -1

    url = 'http://127.0.0.1:8888/knowledge_graph/get_entity'
    data = {"raw_text": text}
    headers = {'Content-Type': 'application/json;charset=utf8'}
    reponse = requests.get(url, params=data, headers=headers)
    if reponse.status_code == 200:
        reponse = json.loads(reponse.text)
        return reponse['data']
    else:
        return -1


def neo4j_searcher(cql_list):
    ress = ""
    # print(cql_list)
    if isinstance(cql_list, list):
        for cql in cql_list:
            rst = []
            data = graph.run(cql).data()
            if not data:
                continue
            for d in data:
                d = list(d.values())
                if isinstance(d[0], list):
                    rst.extend(d[0])
                else:
                    rst.extend(d)

            data = ",".join([str(i) for i in rst])
            ress += data + "\n"
    else:
        data = graph.run(cql_list).data()
        if not data:
            return ress
        rst = []
        for d in data:
            d = list(d.values())
            if isinstance(d[0], list):
                rst.extend(d[0])
            else:
                rst.extend(d)

        data = ",".join([str(i) for i in rst])
        ress += data
    return ress


def semantic_parser(text):
    """
    对文本进行解析
    intent = {"name":str,"confidence":float}
    """
    # intent_rst = intent_classifier(text)
    slot_rst = slot_recognizer(text)
    print(slot_rst)
    cql = []
    entity = set()
    ls = set()
    for it in slot_rst:
        for key, val in it.items():
            if key == 'disease':
                # print(val)
                for v in val:
                    entity.add(v[0])
                    ls.add((v[0], 1))
            slot_info = semantic_slot.get(key)
            cql_template = slot_info['cql_template']
            for v in val:
                entity.add(v[0])
                if isinstance(cql_template, list):
                    for s in cql_template:
                        cql.append(s.format(**{key: v[0]}))
                else:
                    cql.append(cql_template.format(**{key: v[0]}))
    # print(cql)
    answer = neo4j_searcher(cql)
    topk = 10 - len(ls)
    recommend = pd.Series(answer.split(',')).value_counts()
    recommend = recommend / recommend[:topk].sum()
    # print(result.to_dict())
    # print(ls)
    recommend_ordered = sorted(recommend.to_dict().items(), key=lambda item: item[1], reverse=True)[:topk]
    # print(recommend_ordered)
    result = list(ls) + recommend_ordered
    # print(result)
    # 加入疾病描述
    r_ls = []
    for i in result:
        d = i[0].strip()
        p = round(i[1], 2)
        c1 = 'MATCH(p:疾病) WHERE p.name="{}" RETURN p.desc'.format(d)
        c2 = 'MATCH(p:疾病) WHERE p.name="{}" RETURN p.cure_department'.format(d)
        c3 = 'MATCH(p:疾病) WHERE p.name="{}" RETURN p.easy_get'.format(d)
        c4 = 'MATCH(p:疾病) WHERE p.name="{}" RETURN p.cured_prob'.format(d)
        x = neo4j_searcher([c1,c2,c3,c4])
        # print("x: ",x.split('\n'))
        try:
            i1, i2, i3, i4 = x.split('\n')[:-1]
            r_ls.append((d, p, i1, i2, i3, i4))
        except:
            print('不存在实体')
    # print(result)
    # print(entity)
    print(r_ls)
    return r_ls, entity


if __name__ == "__main__":
    semantic_parser(
        '你好，我母亲多年以前就偶尔会有胸闷胸痛的症状，劳累后心悸。胸骨后疼痛，时常感到乏力、心慌。检查了心电图，当时没有做b超检查，症状不是很重，就没有治疗，前几天带她去体检，做了个心脏彩超，发现问题比较重，医生说需要做心脏瓣膜置换。'
        .strip().replace('(', '（').replace(')', '）').replace('+', '&'))
