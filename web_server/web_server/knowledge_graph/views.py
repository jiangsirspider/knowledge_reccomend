import json

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.core.cache import cache
import os
from django.conf import settings
from django.core.paginator import Paginator
import pandas as pd

# http://127.0.0.1:8888/knowledge_graph/diagnosis/?raw_text=现在症状腹胀便秘，吃饭没有胃口，吃的很少，人变瘦了，持续20多天了。现在做了核磁共振和血液检查，下一步需要作超声活检吗？

# url反向解析
# 无参数：
# reverse('namespace名字:name名字')
# 如果有位置参数
# reverse('namespace名字:name名字', args = 位置参数元组)
# 如果有关键字参数
# reverse('namespace名字:name名字', kwargs=字典)
# /detail/商品的sku_id

# /get_entity?raw_text=xxx
class GetEntitylView(View):
    def get(self, request):
        # 获取源文本
        data = {"sucess": 0}
        result = []
        raw_text = [request.GET.get("raw_text")]
        model = settings.MODEL
        for i in raw_text:
            entities = settings.BERTFORNER.predict(i, model, settings.DEVICE)
            result.append(entities)
        data["data"] = result
        data["sucess"] = 1
        return JsonResponse(data)

# /diagnosis？raw_text=xxx
class DiagnosisView(View):
    def get(self, request):
        # 获取源文本
        raw_text = request.GET.get("raw_text")
        result, entity = settings.SEMANTIC(
        raw_text
        .strip().replace('(', '（').replace(')', '）').replace('+', '&'))
        context = {
            "entity": "; ".join(list(entity)),
            "result": result,
            "raw_text": raw_text,
        }
        return render(request, "services.html", context)
        # return JsonResponse(context)
# /
class IndexView(View):
    def get(self, request):

        return render(request, "index.html")

# /recommend？raw_text=xxx
class RecommendView(View):
    def get(self, request):
        data = {"sucess": 0}
        result = []
        raw_text = [request.GET.get("raw_text")]
        df_csv = settings.DFCSV
        # 建立参数
        # Number of Permutations
        permutations = 128
        forest = settings.GETFOREST(df_csv, permutations)
        # Number of Recommendations to return
        # 召回top—n数目
        num_recommendations = 100
        # 精确需要的医生id数
        num_doctors = 5
        # 输入测试文本
        raw_text = raw_text[0].strip().replace('(', '（').replace(')', '）').replace('+', '&')
        # 识别测试文本中的医疗实体
        model = settings.MODEL
        text_shiti = settings.PATHPRE(raw_text, settings.BERTFORNER, model, settings.DEVICE)
        result = settings.RECOMMEND(df_csv, text_shiti, settings.DF)
        print(result)
        context = {
            "result": result,
        }
        return render(request,  "news.html", context)

# /scores？chart=xxx&doctor_id=[xxx,xxx]
class ScoresView(View):
    def get(self, request, file):
        data = {"sucess": 0}
        doctor_id = request.GET.get("doctor_id")
        chart = request.GET.get("chart")
        # 建立参数
        if doctor_id:
            ids = [int(i) for i in json.loads(doctor_id)]
            df_csv = settings.DF
            search_df = df_csv.loc[df_csv.doctor_id.isin(ids)]
                # df_csv.loc[df_csv.doctor_id.isin(ids)]
            #
            search_df.doctorName = search_df.doctorName.apply(lambda x: x[0] + '*')
            doctors = search_df.to_dict(orient="records")
            cl_name = {'patient_score': '患者投票比', 'patient_online': '在线服务患者比', 'hot_num': '医师推荐热度比', 'articleCount': '总文章比', 'totaldiagnosis': '问诊后报到患者比', 'spaceRepliedCount': '总患者比'}
            search_df = search_df[['patient_score', 'patient_online', 'hot_num', 'articleCount', 'totaldiagnosis', 'spaceRepliedCount', 'doctorName', 'doctor_id']]
            search_df = search_df.dropna()
            doctor_ids = search_df.doctor_id.to_list()
            print(doctors)
            doctor_names = search_df.doctorName.to_list()
            # print(doctor_ids)
            # print(doctor_names)
            # print(doctors)
            search_df.drop(["doctorName"], axis=1, inplace=True)
            search_df.totaldiagnosis = search_df.totaldiagnosis.apply(lambda x: int(x[:-1]))
            search_df.articleCount = search_df.articleCount.apply(lambda x: int(x[:-1]))
            search_df.spaceRepliedCount = search_df.spaceRepliedCount.apply(lambda x: int(x[:-1]))
            # print(search_df)
            if chart == 'radar':
                # 转换为百分比，缩放数据
                search_df.patient_score = search_df.patient_score/sum(search_df.patient_score) * 100
                search_df.patient_online = search_df.patient_online/sum(search_df.patient_online) * 100
                search_df.hot_num = search_df.hot_num/sum(search_df.hot_num) * 100
                search_df.articleCount = search_df.articleCount/sum(search_df.articleCount) * 100
                search_df.totaldiagnosis = search_df.totaldiagnosis/sum(search_df.totaldiagnosis) * 100
                search_df.spaceRepliedCount = search_df.spaceRepliedCount/sum(search_df.spaceRepliedCount) * 100
            search_df = search_df.set_index('doctor_id')
            search_df = search_df.rename(columns=cl_name).T
            search_df = search_df.reset_index()
            new_cls = {'index': 'subject'}
            if chart == 'radar':
                new_cls.update({v: 'person{}'.format(i+1) for i, v in enumerate(doctor_ids)})
            else:
                new_cls.update({i: v for i, v in zip(doctor_ids, doctor_names)})
            print(new_cls)
            search_df = search_df.rename(columns=new_cls)
            search_df.to_csv('./static/data/{}'.format('data16.csv'), encoding='utf_8_sig', index=False)
            names = {
                "chart": chart,
                "doctors": doctors,
            }
            return render(request, "fifa16.html", names)
        if file:
            with open('./static/data/{}'.format(file), 'r') as f:
                return HttpResponse(f.read())


