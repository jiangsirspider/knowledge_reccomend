# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from hdf.items import DoctorItem, DiseaseItem, ErrorItem
import pandas as pd


class DoctorPipeline:
    def __init__(self):
        pass

    def process_item(self, item, spider):
        if isinstance(item, DoctorItem):
            new_line = pd.DataFrame([dict(item)])
            self.collection = self.collection.append(new_line)

            print(dict(item))
            pass
        return item

    def open_spider(self, spider):
        self.collection = pd.DataFrame()

    def close_spider(self, spider):
        self.collection.to_csv('./doctors_{}.csv'.format(spider.name), encoding='utf-8-sig')


class AllPipeline:
    def __init__(self):
        pass

    def process_item(self, item, spider):

        if isinstance(item, DiseaseItem):
            new_line = pd.DataFrame([dict(item)])
            self.collection = self.collection.append(new_line)
            print(dict(item))
            pass
        return item

    def open_spider(self, spider):
        self.collection = pd.DataFrame()

    def close_spider(self, spider):
        self.collection.to_csv('./disease_{}.csv'.format(spider.name), encoding='utf-8-sig')

        pass


class ErrorPipeline:
    def __init__(self):
        pass

    def process_item(self, item, spider):
        if isinstance(item, ErrorItem):
            new_line = pd.DataFrame([dict(item)])
            self.collection = self.collection.append(new_line)

            print(dict(item))
            pass
        return item

    def open_spider(self, spider):
        self.collection = pd.DataFrame()

    def close_spider(self, spider):
        self.collection.to_csv('./errors_{}.csv'.format(spider.name), encoding='utf-8-sig')

        pass


