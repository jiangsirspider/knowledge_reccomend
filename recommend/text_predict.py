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

def path_pre(raw_text, bertForNer, model, device):
    print(raw_text)
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
        # item['docotor_id'] = doctor_id
        # item['text_type_result'] = text_type_result
            # print(item)
        return text_type_result
    else:
            #无医疗实体可被识别
        return None

if __name__ == "__main__":
    raw_text = " 汪主任您好，1月中旬常规体检发现TCT高度病变，HPV未查，2020年hpv和tct正常。已经在南京鼓楼医院做了活检，报告如下，诊断写的肿瘤，请问现在这个是不是癌呢？是不是很严重？因为娃太小很害怕，后续该怎么手术呢？十分迫切希望得到您的答复，不胜感激！ ".strip().replace(
            '(', '（').replace(')', '）').replace('+', '&')
    path_pre(raw_text)

