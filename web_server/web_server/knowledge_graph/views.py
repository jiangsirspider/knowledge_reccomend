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


