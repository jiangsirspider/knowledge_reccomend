# -*- coding: utf-8 -*-
# @Time : 2022/4/19 15:40
# @Author : @JiangSir

import os

import numpy as np
import torch
from entity_extract.utils import commonUtils, decodeUtils, trainUtils
import config
import bert_ner_model
from transformers import BertTokenizer
import pickle


args = config.Args().get_parser()
commonUtils.set_seed(args.seed)


class BertForNer:
    def __init__(self, args, idx2tag):
        self.args = args
        self.idx2tag = idx2tag

    def predict(self, raw_text, model,device):
        with torch.no_grad():
            tokenizer = BertTokenizer(
                os.path.join(self.args.bert_dir, 'vocab.txt'))
            tokens = commonUtils.fine_grade_tokenize(raw_text, tokenizer)
            encode_dict = tokenizer.encode_plus(text=tokens,
                                                max_length=self.args.max_seq_len,
                                                padding='max_length',
                                                truncation='longest_first',
                                                is_pretokenized=True,
                                                return_token_type_ids=True,
                                                return_attention_mask=True)
            token_ids = torch.from_numpy(np.array(encode_dict['input_ids'])).unsqueeze(0)
            attention_masks = torch.from_numpy(np.array(encode_dict['attention_mask'], dtype=np.uint8)).unsqueeze(0)
            token_type_ids = torch.from_numpy(np.array(encode_dict['token_type_ids'])).unsqueeze(0)
            logits = model(token_ids.to(device), attention_masks.to(device), token_type_ids.to(device), None)
            if self.args.use_crf == 'True':
                output = logits
            else:
                output = logits.detach().cpu().numpy()
                output = np.argmax(output, axis=2)
            pred_entities = decodeUtils.bioes_decode(output[0][1:1 + len(tokens)], "".join(tokens), self.idx2tag)
            print(pred_entities)
            return pred_entities


if __name__ == '__main__':
    args.bert_dir = '../data/bert-base-chinese'
    model_name = 'bert_bilstm_crf'  # 使用的model类型：bert_bilstm， bert_bilstm_crf， bert_crf， bert
    id2query = pickle.load(open('../data/id2query.pkl', 'rb'))
    ent2id_dict = pickle.load(open('../data/ent2id_dict.pkl', 'rb'))
    # print(id2query)
    args.num_tags = len(ent2id_dict)
    # print('args:', args)
    bertForNer = BertForNer(args, id2query)
    model_path = '../entity_extract/checkpoints/{}/model.pt'.format(model_name)
    model = bert_ner_model.BertNerModel(args)
    model, device = trainUtils.load_model_and_parallel(model, args.gpu_ids, model_path)
    model.eval()
    raw_text = " 汪主任您好，1月中旬常规体检发现TCT高度病变，HPV未查，2020年hpv和tct正常。已经在南京鼓楼医院做了活检，报告如下，诊断写的肿瘤，请问现在这个是不是癌呢？是不是很严重？因为娃太小很害怕，后续该怎么手术呢？十分迫切希望得到您的答复，不胜感激！ ".strip().replace(
        '(', '（').replace(')', '）').replace('+', '&')
    print(raw_text)
    bertForNer.predict(raw_text, model, device)


