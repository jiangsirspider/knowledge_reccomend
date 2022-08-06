import sys
import pandas as pd
from predict import BertForNer
from entity_extract.utils import commonUtils, decodeUtils, trainUtils
import config
import pickle
import bert_ner_model
args = config.Args().get_parser()
commonUtils.set_seed(args.seed)
from multiprocessing import Pool


class pre(object):
    def path_pre(self,raw_text,doctor_id):
        args.bert_dir = '../data/bert-base-chinese'
        model_name = 'bert_bilstm_crf'  # 使用的model类型：bert_bilstm， bert_bilstm_crf， bert_crf， bert
        id2query = pickle.load(open('../data/id2query.pkl', 'rb'))
        ent2id_dict = pickle.load(open('../data/ent2id_dict.pkl', 'rb'))
        # print(id2query)
        args.num_tags = len(ent2id_dict)
        # print('args:', args)
        bertForNer = BertForNer(args, id2query)
        model_path = '../entity_extract/checkpoints/{}/model.pt'.format(model_name)
        item = {}
        model = bert_ner_model.BertNerModel(args)
        model, device = trainUtils.load_model_and_parallel(model, args.gpu_ids, model_path)
        model.eval()
        # print(raw_text)
        predict_result = bertForNer.predict(raw_text, model,device)
        # print(111)
        if list(predict_result.values()):
            len_result = len(list(predict_result.values())[0])
            text_type_result = ''
            # df1 = pd.DataFrame()
            for i in range(len_result):
                b = str(list(predict_result.values())[0][i-1][0])
                # print(b)
                text_type_result=text_type_result+b+' '
            item['docotor_id'] = doctor_id
            item['text_type_result'] = text_type_result
            # print(item)
            return item
        else:
            #无医疗实体可被识别
            return {}
if __name__ == '__main__':
    pool = Pool(processes=10)
    # 进程池
    task_ls = []  # 任务列表
    shili = pre()
    path_list = ['./haodaifu/disease_gaoxueya.csv',
                 './haodaifu/disease_tangniaobing.csv',
                 './haodaifu/disease_guanxinbing.csv',
                 './haodaifu/disease_pifuke.csv',
                 './haodaifu/disease_erke.csv',
                 './haodaifu/disease_fuchanke.csv',]
    path = path_list[0]#修改索引，下标为0
    df1 = pd.read_csv('./gaoxueya-30992.csv')
    df = pd.read_csv(path)
    doctor_id_list = df.doctor_id.values.tolist()
    raw_text_list = df.disease_info.values.tolist()
    for range_i in range(60149,60150):
        try:
            doctor_id = doctor_id_list[range_i]
            raw_text = raw_text_list[range_i].strip().replace('(', '（').replace(')', '）').replace('+', '&')
        except:
            continue
        if len(raw_text) == 0:
            print(range_i,'空')
            continue
        # print(range_i,doctor_id,raw_text)
        # task = t.submit(shili.path_pre,raw_text,doctor_id)
        task = pool.apply_async(shili.path_pre,args=(raw_text,doctor_id,))
        # print('类型',type(task))
        task_ls.append(task)
        if len(task_ls) >= 10:
                # print('task_ls',task_ls)
            for res in task_ls:
                    # print('res类型',type(res))
                item = res.get()
                if item:
                    df1 = df1.append([item])  # 转换结果写入数据库
                    # print(item)
            task_ls.clear()
        if (range_i + 1) % 10 == 0:
            print(range_i)
            df1.to_csv('./gaoxueya-30992.csv', encoding='utf-8-sig')
    # print("最后task",len(task_ls))
    for res in task_ls:
        # print('jinru')
        item = res.get()
        if item:
            df1 = df1.append([item])  # 转换结果写入数据库
                    # print(item)
    print(df1)
    df1.to_csv('./gaoxueya-30992.csv', encoding='utf-8-sig')
    # print("跳出循环")
    pool.close()