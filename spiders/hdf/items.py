# -*- coding: utf-8 -*-
# Define here the models for your scraped items
#
# See documentation in:

import scrapy


class DoctorItem(scrapy.Item):
    # define the fields for your item here like:
    doctor_id = scrapy.Field()
    doctorName = scrapy.Field()
    hospitalName = scrapy.Field()
    disease = scrapy.Field()  #
    educate = scrapy.Field()
    articleCount = scrapy.Field()
    spaceRepliedCount = scrapy.Field()
    totaldiagnosis = scrapy.Field()
    openSpaceTime = scrapy.Field()
    patient_score = scrapy.Field()
    patient_online = scrapy.Field()
    hot_num = scrapy.Field()
    keshi = scrapy.Field()
    good_at = scrapy.Field()
    introduction = scrapy.Field()
    doctor_title = scrapy.Field()

class DiseaseItem(scrapy.Item):
    # define the fields for your item here like:
    doctor_id = scrapy.Field()
    disease = scrapy.Field()
    disease_info = scrapy.Field()
    disease_shichang = scrapy.Field()
    disease_byuser = scrapy.Field()
    disease_hope = scrapy.Field()
    disease_body = scrapy.Field()


class ErrorItem(scrapy.Item):
    # define the fields for your item here like:
    error_method = scrapy.Field()
    error_content = scrapy.Field()
    error_url = scrapy.Field()
    error_response = scrapy.Field()


