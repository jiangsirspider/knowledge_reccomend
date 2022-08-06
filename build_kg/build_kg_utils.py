#encoding:utf8
import os
import re
import json
import codecs
import threading
from py2neo import Graph
import pandas as pd 
import numpy as np 
from tqdm import tqdm 

def print_data_info(data_path):
    triples = []
    i = 0
    with open(data_path,'r',encoding='utf8') as f:
        for line in f.readlines():
            data = json.loads(line)
            print(json.dumps(data, sort_keys=True, indent=4, separators=(', ', ': '),ensure_ascii=False))
            i += 1
            if i >=5:
                break
    return triples

class MedicalExtractor(object):
    def __init__(self):
        super(MedicalExtractor, self).__init__()
        self.graph = Graph('http://localhost:7474', auth=('', ''))

        # 共8类节点
        self.drugs = [] # 药品
        self.checks = [] # 检查
        self.departments = [] #科室
        self.diseases = [] #疾病
        self.symptoms = []#症状
        self.body = []#身体
        self.alias = []#别名
        self.disease_infos = []#疾病信息

        # 构建节点实体关系
        self.rels_department = [] #　科室－科室关系
        self.rels_commonddrug = [] # 疾病－通用药品关系
        self.rels_check = [] # 疾病－检查关系
        self.rels_symptom = [] #疾病症状关系
        self.rels_acompany = [] # 疾病并发关系
        self.rels_category = [] #　疾病与科室之间的关系
        self.rels_body = [] #　疾病与身体之间的关系
        self.rels_alias = [] #　疾病与别名之间的关系

    def extract_triples(self, path):
        print("从xlsx文件中转换抽取三元组")
        graph_data = pd.read_excel(path)
        for idx, line in tqdm(graph_data.iterrows(), total=len(graph_data)):
            data_json = line.to_dict()
            disease_dict = {}
            disease = line['diseaseName']
            disease_dict['name'] = disease
            self.diseases.append(disease)
            disease_dict['desc'] = ''
            disease_dict['prevent'] = ''
            disease_dict['cause'] = ''
            disease_dict['easy_get'] = ''
            disease_dict['cure_department'] = ''
            disease_dict['cure_way'] = ''
            disease_dict['cure_lasttime'] = ''
            disease_dict['symptom'] = ''
            disease_dict['cured_prob'] = ''

            if 'classicalSymptom' in data_json:
                try:
                    self.symptoms += data_json['classicalSymptom'].split(';')[:-1]
                    for symptom in data_json['classicalSymptom'].split(';')[:-1]:
                        self.rels_symptom.append([disease, 'has_symptom', symptom])
                except:
                    pass

            if 'complication' in data_json:
                try:
                    for acompany in data_json['complication'].split(';')[:-1]:
                        self.rels_acompany.append([disease, 'acompany_with', acompany])
                        self.diseases.append(acompany)
                except:
                    pass

            if 'diseaseAlias' in data_json:
                try:
                    for alias in data_json['diseaseAlias'].split(',')[:-1]:
                        self.rels_alias.append([disease, 'has_alias', alias])
                        self.diseases.append(alias)
                        self.alias.append(alias)
                except:
                    pass

            if 'siteOfOnset' in data_json:
                try:
                    for body in data_json['siteOfOnset'].split(';')[:-1]:
                        self.rels_body.append([disease, 'in_body', body])
                        self.body.append(body)
                except:
                    pass

            if 'introduction' in data_json:
                disease_dict['desc'] = data_json['introduction']

            if 'prevent' in data_json:
                disease_dict['prevent'] = data_json['prevent']

            if 'cause' in data_json:
                disease_dict['cause'] = data_json['cause']

            if 'get_prob' in data_json:
                disease_dict['get_prob'] = data_json['get_prob']

            if 'multiplePopulation' in data_json:
                disease_dict['easy_get'] = data_json['multiplePopulation']

            if 'registrationDepartment' in data_json:
                try:
                    cure_department = data_json['registrationDepartment'].split(';')[:-1]
                    for department in cure_department:
                        self.rels_category.append([disease, 'cure_department', department])
                    disease_dict['cure_department'] = cure_department
                    self.departments += cure_department
                except:
                    pass

            if 'cure_way' in data_json:
                disease_dict['cure_way'] = data_json['cure_way']

            if 'cure_lasttime' in data_json:
                disease_dict['cure_lasttime'] = data_json['cure_lasttime']

            if 'cured_prob' in data_json:
                disease_dict['cured_prob'] = data_json['cured_prob']

            if 'commonDrugs' in data_json:
                try:
                    common_drug = data_json['commonDrugs'].split(';')[:-1]
                    for drug in common_drug:
                        self.rels_commonddrug.append([disease, 'has_common_drug', drug])
                    self.drugs += common_drug
                except:
                    pass


            if 'clinicalExamination' in data_json:
                try:
                    check = data_json['clinicalExamination'].split(';')[:-1]
                    for _check in check:
                        self.rels_check.append([disease, 'need_check', _check])
                    self.checks += check
                except:
                    pass

            self.disease_infos.append(disease_dict)

    def write_nodes(self,entitys,entity_type):
        print("写入 {0} 实体".format(entity_type))
        for node in tqdm(set(entitys),ncols=80):
            cql = """MERGE(n:{label}{{name:'{entity_name}'}})""".format(
                label=entity_type,entity_name=node.replace("'",""))
            try:
                self.graph.run(cql)
            except Exception as e:
                print(e)
                print(cql)
        
    def write_edges(self,triples,head_type,tail_type):
        print("写入 {0} 关系".format(triples[0][1]))
        for head,relation,tail in tqdm(triples,ncols=80):
            cql = """MATCH(p:{head_type}),(q:{tail_type})
                    WHERE p.name='{head}' AND q.name='{tail}'
                    MERGE (p)-[r:{relation}]->(q)""".format(
                        head_type=head_type,tail_type=tail_type,head=head.replace("'",""),
                        tail=tail.replace("'",""),relation=relation)
            try:
                self.graph.run(cql)
            except Exception as e:
                print(e)
                print(cql)

    def set_attributes(self,entity_infos,etype):
        print("写入 {0} 实体的属性".format(etype))
        for e_dict in tqdm(entity_infos,ncols=80):
            name = e_dict['name']
            del e_dict['name']
            for k,v in e_dict.items():
                if k in ['cure_department','cure_way'] and v:
                    cql = """MATCH (n:{label})
                        WHERE n.name='{name}'
                        set n.{k}={v}""".format(label=etype,name=name.replace("'",""),k=k,v=v)
                else:
                    try:
                        cql = """MATCH (n:{label})
                            WHERE n.name='{name}'
                            set n.{k}='{v}'""".format(label=etype,name=name.replace("'",""),k=k,v=v.replace("'","").replace("\n",""))
                    except:
                        print(name, k, v)
                try:
                    self.graph.run(cql)
                except Exception as e:
                    print(e)
                    print(cql)


    def create_entitys(self):
        self.write_nodes(self.drugs,'药品')
        self.write_nodes(self.checks,'检查')
        self.write_nodes(self.departments,'科室')
        self.write_nodes(self.diseases,'疾病')
        self.write_nodes(self.symptoms,'症状')
        self.write_nodes(self.body,'身体')
        self.write_nodes(self.alias,'别名')

    def create_relations(self):
        self.write_edges(self.rels_commonddrug,'疾病','药品')
        self.write_edges(self.rels_check,'疾病','检查')
        self.write_edges(self.rels_symptom,'疾病','症状')
        self.write_edges(self.rels_acompany,'疾病','疾病')
        self.write_edges(self.rels_category,'疾病','科室')
        self.write_edges(self.rels_body,'疾病','身体')
        self.write_edges(self.rels_alias,'疾病','别名')

    def create_relations2(self):
        self.write_edges(self.rels_commonddrug,'药品','疾病')
        self.write_edges(self.rels_check,'检查','疾病')
        self.write_edges(self.rels_symptom,'症状','疾病')
        self.write_edges(self.rels_category,'科室','疾病')

    def set_diseases_attributes(self):
        t=threading.Thread(target=self.set_attributes,args=(self.disease_infos,"疾病"))
        t.setDaemon(False)
        t.start()


    def export_data(self,data,path):
        if isinstance(data[0],str):
            data = sorted([d.strip("...") for d in set(data)])
        with codecs.open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_entitys_relations(self):
        self.export_data(self.drugs,'./graph_data/drugs.json')
        self.export_data(self.checks,'./graph_data/checks.json')
        self.export_data(self.departments,'./graph_data/departments.json')
        self.export_data(self.diseases,'./graph_data/diseases.json')
        self.export_data(self.symptoms,'./graph_data/symptoms.json')
        # self.export_data(self.rels_department,'./graph_data/rels_department.json')
        self.export_data(self.rels_commonddrug,'./graph_data/rels_commonddrug.json')
        self.export_data(self.rels_check,'./graph_data/rels_check.json')
        self.export_data(self.rels_symptom,'./graph_data/rels_symptom.json')
        self.export_data(self.rels_acompany,'./graph_data/rels_acompany.json')
        self.export_data(self.rels_category,'./graph_data/rels_category.json')





if __name__ == '__main__':
    path = "./graph_data/皮肤科数据集.xls"  # 冠心病，糖尿病，高血压， 儿科, 皮肤科
    extractor = MedicalExtractor()
    extractor.extract_triples(path)
    # extractor.create_entitys()
    # extractor.create_relations()
    # extractor.create_relations2()
    # extractor.set_diseases_attributes()
    extractor.export_entitys_relations()
