import pandas as pd
import sys
sys.path.append(r'D:\杂物\研究生\比赛竞赛\基于知识图谱的医生推荐系统\recommend')
def find(id, df):
    # df =pd.read_csv('./haodaifu/doctors_gaoxueya.csv')
    doctor_infomation = df[df['doctor_id'] == id]
    return doctor_infomation
if __name__ == '__main__':
    doctor_id = 221603
    df = pd.read_csv('./haodaifu/doctors_gaoxueya.csv')

    doctor_infomation = find(doctor_id, df)
    print(doctor_infomation)
    print(doctor_infomation.columns)
    print(doctor_infomation.to_dict(orient="records"))