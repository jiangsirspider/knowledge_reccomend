##推荐前n个问诊的方式
import sys
sys.path.append(r'D:\杂物\研究生\比赛竞赛\基于知识图谱的医生推荐系统\recommend')
import numpy as np
import re
import time
from datasketch import MinHash, MinHashLSHForest
import pandas as pd
import bert_ner_model
from predict import BertForNer
from entity_extract.utils import commonUtils, decodeUtils, trainUtils
import config
import pickle
args = config.Args().get_parser()
commonUtils.set_seed(args.seed)
from text_predict import path_pre
from doctor_find import find
#识别医疗实体

#Preprocess will split a string of text into individual tokens/shingles based on whitespace.
def preprocess(text):
    text = re.sub(r'[^\w\s]','',text)
    tokens = text.lower()
    tokens = tokens.split()
    return tokens
def get_forest(data, perms):
    start_time = time.time()
    minhash = []
    for text in data['text_type_result']:
        tokens = preprocess(text)
        m = MinHash(num_perm=perms)
        for s in tokens:
            m.update(s.encode('utf8'))
        minhash.append(m)
    forest = MinHashLSHForest(num_perm=perms)
    for i,m in enumerate(minhash):
        forest.add(i,m)
    forest.index()
    print('It took %s seconds to build forest.' %(time.time()-start_time))
    return forest
def predict(text, database, perms, num_results, forest,doctor):
    # print(num_results)
    doctor_id = []
    start_time = time.time()
    tokens = preprocess(text)
    m = MinHash(num_perm=perms)
    for s in tokens:
        m.update(s.encode('utf8'))
    idx_array = np.array(forest.query(m, num_results))
    print(len(idx_array))
    if len(idx_array) == 0:
        return None # if your query is empty, return none
    # result_text = str(database.iloc[idx_array]['text_type_result'])
    result_predict = database.iloc[idx_array]['docotor_id']
    # print(len(result_dotcor))
    for text_id in result_predict:
        if text_id not  in doctor_id:
            doctor_id.append(text_id)
        else:
            continue
        if len(doctor_id) >= doctor:
            break
    print('It took %s seconds to query forest.' %(time.time()-start_time))
    return doctor_id

def recommend(df_csv, text_shiti, df):
    #建立参数
    #Number of Permutations
    permutations = 128
    forest = get_forest(df_csv, permutations)
    #Number of Recommendations to return
    #召回top—n数目
    num_recommendations = 100
    #精确需要的医生id数
    num_doctors = 5
    #这里输出前5个医生的id
    result = predict(str(text_shiti),df_csv,permutations, num_recommendations, forest,num_doctors)
    result_ls = []
    for i in result:
        doctor_information = find(int(i), df=df)
        #这是输入医生的信息
        # print(doctor_information)
        result_ls += (doctor_information.to_dict(orient="records"))
    # print('\n Top Recommendation(s) is(are) \n\t', result)
    print(result_ls)
    return result_ls

if __name__ == "__main__":
    df_csv = pd.read_csv('./gaoxueya-1.csv')
    # 建立参数
    # Number of Permutations
    permutations = 128
    forest = get_forest(df_csv, permutations)
    # Number of Recommendations to return
    # 召回top—n数目
    num_recommendations = 100
    # 精确需要的医生id数
    num_doctors = 5
    # 输入测试文本
    raw_text = ' 一周前稍感胸闷，入院检查，心脏彩超，腹部彩超正常，心脏冠状动脉CT，显示狭窄 '
    raw_text = raw_text.strip().replace('(', '（').replace(')', '）').replace('+', '&')
    args.bert_dir = '../data/bert-base-chinese'
    model_name = 'bert_bilstm_crf'  # 使用的model类型：bert_bilstm， bert_bilstm_crf， bert_crf， bert
    id2query = pickle.load(open('../data/id2query.pkl', 'rb'))
    ent2id_dict = pickle.load(open('../data/ent2id_dict.pkl', 'rb'))
    args.num_tags = len(ent2id_dict)
    bertForNer = BertForNer(args, id2query)
    model_path = '../entity_extract/checkpoints/{}/model.pt'.format(model_name)
    model = bert_ner_model.BertNerModel(args)
    model, device = trainUtils.load_model_and_parallel(model, args.gpu_ids, model_path)
    model.eval()
    # 识别测试文本中的医疗实体
    text_shiti = path_pre(raw_text, bertForNer, model, device)
    df = pd.read_csv('./haodaifu/doctors_gaoxueya.csv')
    recommend(df_csv, text_shiti,df)
