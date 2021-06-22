import time,base64,threading,requests,json
from Modules.SQL_module import SQL
import jieba
from app import rds_host,rds_password,rds_user
jieba.add_word("不對稱")
jieba.add_word("四季")
stylish = SQL(host=rds_host,user=rds_user,password=rds_password,database="stylish")
def get_product_descriptions(category):
    sql_data = stylish.fetch_list("select id, description, title from product where category = %s",category)
    index_to_id_dict = {}
    description_list =[]
    for i in range(len(sql_data)) :
        index_to_id_dict[i] = sql_data[i][0]
        description = ("".join(json.loads(sql_data[i][1])))+sql_data[i][2]
        description_list.append(" ".join(jieba.cut(description)))
    return description_list, index_to_id_dict

from sklearn.feature_extraction.text import CountVectorizer,TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
import math
with open("stop.txt", 'rb') as fp:
    stopword = fp.read().decode('utf-8')
stopword_list = stopword.splitlines()

def create_similarity(descriptions):
    corpus = descriptions
    vectorizer = CountVectorizer(stop_words = stopword_list)
    word_count_matrix = vectorizer.fit_transform(corpus)
    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(word_count_matrix)
    similarity_list =[]
    product_num = len(index_to_id_dict)
    for first in range(product_num) :
        item_ratio_list = []
        for second in range(product_num) :
            ratio = round(cosine_similarity(tfidf[first], tfidf[second])[0][0],4)
            if ratio > 0.00 and ratio != float("nan") and first != second:
                first_code = index_to_id_dict[first]
                second_code = index_to_id_dict[second]
                item_ratio_list.append((first_code,second_code,ratio))
        item_ratio_list = sorted(item_ratio_list, key = lambda x: x[2],reverse=True)
        similarity_list.extend(item_ratio_list)
    
    return similarity_list
# stylish.bulk_execute("INSERT INTO `item_similarity`( `item_1`, `item_2`, `similarity`) VALUES (%s,%s,%s)",create_similarity(description_list))
print("success")

import requests,time,os
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
def get_color_dict():
    ua = UserAgent(verify_ssl=False)
    url = "https://www.ebaomonthly.com/window/photo/lesson/colorList.htm"
    headers = {
            'user-agent': ua.random,
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,ja;q=0.5',
            }    
    response = requests.get(url,headers = headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    color_list  = soup.findAll("tr")
    del color_list[0]
    del color_list[0]
    color_dict = {}
    for x in color_list:
        # print(x)
        try :
            color_name = re.search(r'.*?[A-Za-z]',x.findAll("td")[1].text)[0][:-1]
            if "色" not in color_name :
                color_name = color_name + "色"
            color_code = x.td["bgcolor"][1:]
            color_dict[color_name] = color_code
        except:
            break

if __name__ == "__main__":
    description_list = get_product_descriptions('accessories')[0]
    index_to_id_dict = get_product_descriptions('accessories')[1]
    print(description_list[3])
    print(index_to_id_dict[3])

