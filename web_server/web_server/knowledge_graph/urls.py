# -*- coding: utf-8 -*-
# @Time : 2022/4/23 12:30
# @Author : @JiangSir

from django.urls import re_path
from knowledge_graph import views
urlpatterns = [
    re_path(r"^$", views.IndexView.as_view(), name="index"),
    re_path(r"^get_entity/", views.GetEntitylView.as_view(), name="get_entity"),
    re_path(r"^diagnosis/", views.DiagnosisView.as_view(), name="diagnosis"),
    re_path(r"^recommend/$", views.RecommendView.as_view(), name="recommend"),
    re_path(r"^scores/(.*?)$", views.ScoresView.as_view(), name="scores"),
    # re_path(r"^list/([\d]+)/([\d]+)$", views.ListView.as_view(), name="list"),
]


