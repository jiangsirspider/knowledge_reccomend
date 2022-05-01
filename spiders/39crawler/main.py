from bs4 import BeautifulSoup
import xlwt
import requests
import re


def ask_url(url):
    head = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47"
        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36 Edg/86.0.622.63"
    }
    try:
        r = requests.get(url, headers=head, timeout=30)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        print(e)
        return ""


def get_data(base_url):
    data_list = []
    # 遍历每一页
    for i in range(85):  #16需要修改成对应的页数，在main主程序中找到对应的url的页数
        #https://jbk.39.net/bw/p/key=%e7%b3%96%e5%b0%bf%e7%97%85
        url = base_url + str(i+1)    #皮肤科 妇产科 儿科使用这个url
        # url = base_url.split('/key')[0]+str(i+1)+base_url.split('/p')[-1]
        html = ask_url(url)
        if html == "":
            continue
        soup = BeautifulSoup(html, 'html.parser')
        # 遍历每一种疾病
        for item in soup.find_all('div', class_="result_item"):
            data = {}
            #判断是否为疾病
            if item.div.p.span.string == "疾病":
                # diseaseName
                data['diseaseName'] = item.div.p.a.string
                # diseaseAlias
                # data.append(item.div.p.span.string.strip('（）'))
                # symptom
                symptoms = []
                p = item.find('p', class_='result_item_content_label')
                for symptom in p.find_all('a'):
                    symptoms.append(symptom.string + ';')
                # https://jbk.39.net/zs/
                sub_url = item.div.p.a.attrs["href"]
                sub_html = ask_url(sub_url)
                # print(sub_html)
                if sub_html == "":
                    continue
                sub_soup = BeautifulSoup(sub_html, 'html.parser')
                information_ul = sub_soup.find('ul', class_="information_ul")
                #遍历所有的元素
                for detail in information_ul.find_all('li'):
                    if detail.i.string == '别名：':
                        data['diseaseAlias'] = detail.span.string
                    elif detail.i.string == '发病部位：':
                        data['siteOfOnset'] = []
                        for site in detail.span.find_all('a'):
                            data['siteOfOnset'].append(site.string + ';')
                        # print()
                    elif detail.i.string == '传染性：':
                        data['infectivity'] = detail.span.string
                    elif detail.i.string == '多发人群：':
                        data['multiplePopulation'] = detail.span.string
                    elif detail.i.string == '并发症：':
                        data['complication'] = []
                        for complication in detail.span.find_all('a'):
                            data['complication'].append(complication.string + ';')
                    elif detail.i.string == '是否医保：':
                        # print(detail.span.string)
                        data['yibao'] = detail.span.string
                    elif detail.i.string == '挂号科室：':
                        data['registrationDepartment'] = []
                        for department in detail.span.find_all('a'):
                            data['registrationDepartment'].append(department.string + ';')
                    elif detail.i.string == '临床检查：':
                        data['clinicalExamination'] = []
                        for examination in detail.span.find_all('a'):
                            data['clinicalExamination'].append(examination.string + ';')
                    elif detail.i.string == '治疗费用：':
                        data['cost'] = detail.span.string
                    elif detail.i.string == '典型症状：':
                        for symptom in detail.span.find_all('a'):
                            symptoms.append(symptom.string + ';')
                        data['classicalSymptom'] = symptoms
                information_ul1 = sub_soup.find('ul', class_="information_ul information_ul_bottom")
                for detail in information_ul1.find_all('li'):
                    if detail.i.string == '常用药品：':
                        data['commonDrugs'] = []
                        for drug in detail.span.find_all('a'):
                            data['commonDrugs'].append(drug.string + ';')
                # 爬取详情页信息
                detail_information = sub_soup.find('div', class_="information_box")
                detail_href = detail_information.p.a.attrs["href"]
                detail_html = ask_url(detail_href)
                # print((detail_html))
                if detail_html == "":
                    continue
                detail_soup = BeautifulSoup(detail_html, 'html.parser')
                detail_introduction = detail_soup.find('p', class_="introduction")
                # a = detail_introduction.string
                data['introduction'] = detail_introduction.string
                data_list.append(data)
            else:
                continue

        print('第'+str(i+1)+'页爬取成功')
    return data_list

def save_data(data_list, save_path):
    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = book.add_sheet("冠心病数据集", cell_overwrite_ok=True)
    col = ["diseaseName", "diseaseAlias" , "siteOfOnset", "infectivity", "multiplePopulation", "earlySymptom",
           "advancedSymptom", "complication","yibao", "cost","classicalSymptom","registrationDepartment", "clinicalExamination", "commonDrugs","introduction"]
    length = len(data_list)
    for i in range(0, 15):
        sheet.write(0, i, col[i])
    for i in range(0, length):
        print("\r当前进度：{:.2f}%".format((i + 1) * 100 / length), end="")
        data = data_list[i]
        for j in range(0, 15):
            if col[j] in data:
                sheet.write(i + 1, j, data[col[j]])
    book.save(save_path)
    return ""



if __name__ == "__main__":
    base_url = "https://jbk.39.net/bw/fuchanke_p"  # 妇产科数据集
    save_path = ".\\妇产科数据集.xls"
    data_list = get_data(base_url)
    save_data(data_list, save_path)
