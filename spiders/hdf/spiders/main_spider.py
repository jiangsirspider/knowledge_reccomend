# -*- coding: utf-8 -*-
import requests
import scrapy
import re
import json
from lxml import etree
from hdf.items import DoctorItem, DiseaseItem, ErrorItem

class HdfSpiderSpider(scrapy.Spider):
    with open('disease.txt', 'r') as f:
        name = [i.strip() for i in f.readlines()][0]
    allowed_domains = ['www.haodf.com', 'jiankanghao.haodf.com', 'm.haodf.com']

    def errback_http(self, failure):
        print("error", failure)
        all_item = failure.request.meta.get('all_item')
        if all_item:
            all_item['sale'] = ''
            all_item['like_num'] = ''
            all_item['buy_price'] = ''
            all_item['online_num'] = ''
            all_item['hot_num'] = ''
            yield all_item
        doctor_item = failure.request.meta.get('doctor_item')
        if doctor_item:
            doctor_item['hospital_lever'] = ''
            yield doctor_item
        request = failure.request
        error_item = ErrorItem()
        error_item['error_method'] = 'errback_http'
        error_item['error_content'] = '{}'.format(failure)
        error_item['error_url'] = '{}'.format(request.url)
        error_item['error_response'] = ''
        yield error_item


    def start_requests(self):
        disease_ls = [self.name]
        if 'ke' in self.name:
            for disease in disease_ls:
                headers = {
                    'Host': 'www.haodf.com',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache',
                    # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                    'sec-ch-ua-mobile': '?0',
                    # 'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1',
                    'Sec-Fetch-Dest': 'document',
                    # 'Referer': 'https://www.haodf.com/',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                }

                url = 'https://www.haodf.com/doctor/list-all-{}.html?p=1'.format(disease)

                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers=headers,
                    errback=self.errback_http,
                    meta={'disease': disease}
                )
        else:
            for disease in disease_ls:
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Host': 'www.haodf.com',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                }

                url = 'https://www.haodf.com/citiao/jibing-{}/tuijian-doctor.html'.format(disease)

                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    headers=headers,
                    errback=self.errback_http,
                    meta={'disease': disease}
                )


    def parse(self, response):
        disease = response.meta.get('disease')

        try:
            if 'ke' in disease:
                try:
                    html = response.body.decode('gb2312')
                except:
                    print(response.request.url)
                    html = response.body.decode('gbk')
                html = etree.HTML(html)
                doc_list = html.xpath('//div[@class="d-doc-list"]/ul/li')

                for li in doc_list:
                    doctor_name = li.xpath('.//span[@class="doc-name"]/a/text()')[0].strip()
                    # print(doctor_name)
                    doctor_id = re.search(r'/(\d+)\.html$', li.xpath('.//span[@class="doc-name"]/a/@href')[0].strip()).group(1)

                    print('获取->{}<-医生:'.format(self.name), doctor_id, doctor_name)

                    url2 = 'https://www.haodf.com/ndoctor/ajaxGetSrvDocInfo?doctorId={}'.format(doctor_id)

                    headers2 = {
                        'accept': 'application/json, text/plain, */*',
                        'accept-encoding': 'gzip, deflate, br',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'if-none-match': 'W/"1ce-lpqDXO1HihbefSgpyc5PYA"',
                        'referer': 'https://www.haodf.com/doctor/{}/fuwu-wenzhen.html'.format(doctor_id),
                        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': "Windows",
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-origin',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
                    }
                    yield scrapy.Request(
                        url=url2,
                        callback=self.parse_item,
                        errback=self.errback_http,
                        headers=headers2,
                        meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name}
                    )

                next_page = response.xpath('//div[@class="page_turn"]/a[contains(string(), "下一页")]/@href').extract_first()

                if next_page:
                    page_num = int(re.search(r'\d+', next_page).group())

                    if page_num > 100:
                        return

                    url2 = 'https://www.haodf.com' + next_page

                    headers2 = {
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Host': 'www.haodf.com',
                        # 'Referer': 'https://www.haodf.com/citiao/jibing-{}/tuijian-doctor.html?p={}'.format(disease, i-1),
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                        'X-Requested-With': 'XMLHttpRequest',
                        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                        'sec-ch-ua-mobile': '?0',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                        # 'Cookie': '__jsluid_s=e9de4106b3ad37ddef0d7335a9533810; g=66247_1626181968043; CNZZDATA-FE=CNZZDATA-FE; g=HDF.183.60ed91502cd78; Hm_lvt_dfa5478034171cc641b1639b2a5b717d=1638847995; Hm_lpvt_dfa5478034171cc641b1639b2a5b717d=1638849256'
                    }

                    yield scrapy.Request(
                        url2,
                        callback=self.parse,
                        errback=self.errback_http,
                        headers=headers2,
                        meta={'disease': disease}
                    )
            else:
                html = response.body.decode()
                termid = re.search(r'"termId":(\d+)', html).group(1)
                placeId = re.search(r'"placeId":(\d+)', html).group(1)
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Host': 'www.haodf.com',
                    'Referer': 'https://www.haodf.com/citiao/jibing-{}/tuijian-doctor.html?p={}'.format(disease, 1),
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                    # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                    'sec-ch-ua-mobile': '?0',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    # 'Cookie': '__jsluid_s=e9de4106b3ad37ddef0d7335a9533810; g=66247_1626181968043; CNZZDATA-FE=CNZZDATA-FE; g=HDF.183.60ed91502cd78; Hm_lvt_dfa5478034171cc641b1639b2a5b717d=1638847995; Hm_lpvt_dfa5478034171cc641b1639b2a5b717d=1638849256'
                }
                data = {
                    'nowPage': '{}'.format(1),
                    'pageSize': '15',
                    'placeId': '{}'.format(placeId),
                    'termId': '{}'.format(termid),
                }

                url = 'https://www.haodf.com/ndisease/ajaxLoadMoreDoctor/'

                yield scrapy.FormRequest(
                    url,
                    callback=self.parse_doctor_list,
                    headers=headers,
                    errback=self.errback_http,
                    formdata=data,
                    meta={'disease': disease, 'termid': termid, 'placeId': placeId}
                )

        except Exception as e:
            error_item = ErrorItem()
            error_item['error_method'] = 'parse_doctor_list'
            error_item['error_content'] = '{}'.format(e)
            error_item['error_url'] = '{}'.format(response.request.url)
            error_item['error_response'] = '{}'.format(response.body.decode())
            yield error_item

    def parse_doctor_list(self, response):
        disease = response.meta.get('disease')
        termid = response.meta.get('termid')
        placeId = response.meta.get('placeId')

        try:

            data = json.loads(response.body.decode()).get('data')

            data_list = data.get('list')

            totalPage = int(data.get('pageInfo').get('totalPage'))

            nowPage = int(data.get('pageInfo').get('page'))

            html = etree.HTML(data_list)

            li_items = html.xpath('//li[@class="item"]')

            for li in li_items:
                # print(li.xpath('./a/@href'))
                doctor_id = re.search(r'/(\d+)\.html$', li.xpath('./a/@href')[0]).group(1)
                doctor_name = li.xpath('.//div[@class="info"]//span[@class="name"]/text()')[0]
                print('获取->{}<-医生:'.format(self.name), doctor_id, doctor_name)

                url2 = 'https://www.haodf.com/ndoctor/ajaxGetSrvDocInfo?doctorId={}'.format(doctor_id)

                headers2 = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-encoding': 'gzip, deflate, br',
                    'accept-language': 'zh-CN,zh;q=0.9',
                    'if-none-match': 'W/"1ce-lpqDXO1HihbefSgpyc5PYA"',
                    'referer': 'https://www.haodf.com/doctor/{}/fuwu-wenzhen.html'.format(doctor_id),
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': "Windows",
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
                }
                yield scrapy.Request(
                    url=url2,
                    callback=self.parse_item,
                    errback=self.errback_http,
                    headers=headers2,
                    meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name}
                )

            if nowPage == 1:
                end = totalPage

                if totalPage >= 100:
                    end = 100

                for i in range(2, end + 1):
                    # break
                    headers2 = {
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Host': 'www.haodf.com',
                        'Referer': 'https://www.haodf.com/citiao/jibing-{}/tuijian-doctor.html?p={}'.format(disease, i-1),
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                        'X-Requested-With': 'XMLHttpRequest',
                        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                        'sec-ch-ua-mobile': '?0',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                        # 'Cookie': '__jsluid_s=e9de4106b3ad37ddef0d7335a9533810; g=66247_1626181968043; CNZZDATA-FE=CNZZDATA-FE; g=HDF.183.60ed91502cd78; Hm_lvt_dfa5478034171cc641b1639b2a5b717d=1638847995; Hm_lpvt_dfa5478034171cc641b1639b2a5b717d=1638849256'
                    }

                    data = {
                        'nowPage': '{}'.format(i),
                        'pageSize': '15',
                        'placeId': '{}'.format(placeId),
                        'termId': '{}'.format(termid),
                    }

                    url2 = 'https://www.haodf.com/ndisease/ajaxLoadMoreDoctor/'

                    yield scrapy.FormRequest(
                        url2,
                        callback=self.parse_doctor_list,
                        errback=self.errback_http,
                        headers=headers2,
                        formdata=data,
                        meta={'disease': disease, 'termid': termid, 'placeId': placeId}
                    )

        except Exception as e:
            error_item = ErrorItem()
            error_item['error_method'] = 'parse_doctor_list'
            error_item['error_content'] = '{}'.format(e)
            error_item['error_url'] = '{}'.format(response.request.url)
            error_item['error_response'] = '{}'.format(response.body.decode())
            yield error_item


    def parse_item(self, response):
        disease = response.meta.get('disease')
        doctor_id = response.meta.get('doctor_id')
        doctor_name = response.meta.get('doctor_name')
        data_dict = {}
        data = response.body.decode()
        data = json.loads(data)['data']
        try:
            patient_score = data['commentCntIn2Years']
            patient_online = data['patientCnt']
            data_dict['patient_score'] = patient_score
            data_dict['patient_online'] = patient_online
            url1 = 'https://www.haodf.com/doctor/{}.html'.format(doctor_id)
            headers1 = {
                'Host': 'www.haodf.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                # 'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                # 'Referer': 'https://www.haodf.com/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',

            }

            yield scrapy.Request(
                url=url1,
                callback=self.parse_home,
                errback=self.errback_http,
                headers=headers1,
                meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name, 'data_dict': data_dict}
            )


        except Exception as e:
            error_item = ErrorItem()
            error_item['error_method'] = 'parse_item'
            error_item['error_content'] = '{}'.format(e)
            error_item['error_url'] = '{}'.format(response.request.url)
            error_item['error_response'] = '{}'.format(response.body.decode())
            yield error_item

    def parse_home(self, response):
        disease = response.meta.get('disease')
        doctor_id = response.meta.get('doctor_id')
        doctor_name = response.meta.get('doctor_name')
        data_dict = response.meta.get('data_dict')
        try:
            educate = response.xpath('//span[@class="doctor-educate-title"]/text()').extract_first()
            articleCount = response.xpath('//span[@class="per-sta-data js-articleCount"]/text()').extract_first()
            spaceRepliedCount = response.xpath('//span[@class="per-sta-data js-spaceRepliedCount"]/text()').extract_first()
            totaldiagnosis = response.xpath('//span[@class="per-sta-data js-totaldiagnosis-report"]/text()').extract_first()
            openSpaceTime = response.xpath('//span[@class="per-sta-data js-openSpaceTime"]/text()').extract_first()
            hot_num = ''.join(response.xpath('//ul[@class="profile-statistic"]/li[1]/span[@class="value"]//text()').extract())
            hospital = ''.join(response.xpath('//li[@class="doctor-faculty"]/a[1]//text()').extract())
            keshi = ''.join(response.xpath('//li[@class="doctor-faculty"]/a[2]//text()').extract())
            good_at = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//div[@class="brief-container"]/div[1]/div/p//text()').extract()])
            introduction = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//div[@class="brief-container"]/div[2]/div//p[@class="init-content"]//text()').extract()])
            doctor_title = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//span[@class="doctor-title"]/text()').extract()])

            data_dict['educate'] = educate
            data_dict['articleCount'] = articleCount
            data_dict['spaceRepliedCount'] = spaceRepliedCount
            data_dict['totaldiagnosis'] = totaldiagnosis
            data_dict['openSpaceTime'] = openSpaceTime
            data_dict['hot_num'] = hot_num
            data_dict['hospitalName'] = hospital
            data_dict['keshi'] = keshi
            data_dict['good_at'] = good_at
            data_dict['introduction'] = introduction
            data_dict['doctor_title'] = doctor_title

            item = DoctorItem()

            for key in data_dict:
                item[key] = data_dict[key]
            item['doctor_id'] = doctor_id
            item['doctorName'] = doctor_name
            item['disease'] = disease


            yield item

            url = 'https://www.haodf.com/doctor/{}/bingcheng.html?p_type=all&p=1'.format(doctor_id)
            headers1 = {
                'Host': 'www.haodf.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                # 'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                # 'Referer': 'https://www.haodf.com/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_wenzhen_list,
                errback=self.errback_http,
                headers=headers1,
                meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name}
            )


        except Exception as e:
            error_item = ErrorItem()
            error_item['error_method'] = 'parse_home'
            error_item['error_content'] = '{}'.format(e)
            error_item['error_url'] = '{}'.format(response.request.url)
            error_item['error_response'] = '{}'.format(response.body.decode())
            yield error_item

    def parse_wenzhen_list(self, response):
        disease = response.meta.get('disease')
        doctor_name = response.meta.get('doctor_name')
        doctor_id = response.meta.get('doctor_id')
        trs = response.xpath('//div[@class="zixun_list"]//tr')


        for tr in trs:
            service_type = tr.xpath('./td[3]/text()').extract_first()
            # print(service_type)
            if service_type in ['图文问诊']:
                url = tr.xpath('./td[2]//a/@href').extract_first()
                # print(url)
                headers = {
                'Host': 'www.haodf.com',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                # 'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                # 'Referer': 'https://www.haodf.com/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                }
                yield scrapy.FormRequest(
                    url,
                    callback=self.parse_wenzhen,
                    errback=self.errback_http,
                    headers=headers,
                    meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name}
                )



        next_page = response.xpath('//div[@class="p_bar"]/a[contains(string(), "下一页")]/@href').extract_first()

        if next_page:

            page_num = int(re.search(r'\d+', next_page).group())

            if page_num > 100:
                return


            url2 = 'https://www.haodf.com/doctor/{}/bingcheng.html'.format(doctor_id) + next_page

            headers2 = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Host': 'www.haodf.com',
                # 'Referer': 'https://www.haodf.com/citiao/jibing-{}/tuijian-doctor.html?p={}'.format(disease, i - 1),
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'sec-ch-ua-mobile': '?0',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                # 'Cookie': '__jsluid_s=e9de4106b3ad37ddef0d7335a9533810; g=66247_1626181968043; CNZZDATA-FE=CNZZDATA-FE; g=HDF.183.60ed91502cd78; Hm_lvt_dfa5478034171cc641b1639b2a5b717d=1638847995; Hm_lpvt_dfa5478034171cc641b1639b2a5b717d=1638849256'
            }



            yield scrapy.FormRequest(
                url2,
                callback=self.parse_wenzhen_list,
                errback=self.errback_http,
                headers=headers2,
                meta={'disease': disease, 'doctor_id': doctor_id, 'doctor_name': doctor_name, 'page_num': page_num}
            )

    def parse_wenzhen(self, response):
        disease = response.meta.get('disease')
        doctor_name = response.meta.get('doctor_name')
        doctor_id = response.meta.get('doctor_id')
        disease_info = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//div[contains(text(), "疾病描述")]/following-sibling::div[1]//text()').extract()])
        disease_byuser = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//section[@class="diseaseinfo"]//div[text()="疾病："]/following-sibling::div[1]//text()').extract()])
        disease_shichang = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//section[@class="diseaseinfo"]//div[contains(text(), "患病时长")]/following-sibling::div[1]//text()').extract()])
        disease_hope = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//section[@class="diseaseinfo"]//div[contains(text(), "希望得到的帮助")]/following-sibling::div[1]//text()').extract()])
        disease_body = ' '.join([i.replace('\n', '').replace(' ', '').replace('\t', '').strip('') for i in response.xpath('//section[@class="diseaseinfo"]//div[contains(text(), "身高体重")]/following-sibling::div[1]//text()').extract()])

        item = DiseaseItem()

        item['doctor_id'] = doctor_id
        item['disease'] = disease
        item['disease_info'] = disease_info
        item['disease_byuser'] = disease_byuser
        item['disease_shichang'] = disease_shichang
        item['disease_hope'] = disease_hope
        item['disease_body'] = disease_body

        yield item

