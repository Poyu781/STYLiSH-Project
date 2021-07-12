#############Spark
from pyspark.sql import SparkSession
import time
start = time.time()
print(2)
spark = SparkSession \
    .builder \
    .appName("qiuboyude-MacBook-Pro.local") \
    .master("local[4]") \
    .getOrCreate()
print(1)

df = spark.read.csv("/Users/poyuchiu/Desktop/Clothing_Shoes_and_Jewelry_sample.csv",header=True).rdd
result = df.map(lambda x: (x["reviewerID"],(x["itemID"],x["rating"])))
groupby_user = result.groupByKey()

from statistics import mean, pstdev
def normalization(arr):
    rating_list = []
    return_list = []
    for item_tuple in arr[1]:
        rating_list.append(float(item_tuple[1]))
    mean_value = mean(rating_list)
    standard_dv = pstdev(rating_list)
    if standard_dv == 0:
        return (return_list,)
    for item_tuple in arr[1]:
        rate = round((float(item_tuple[1]) - mean_value) / standard_dv,3)
        append_tuple = (item_tuple[0],rate)
        return_list.append(append_tuple)
        
    return (return_list)
nor = groupby_user.map(normalization).filter(lambda x:len(x[0])>1)

def combination(arr):
    item_pair_list = []
    for i in arr :
        for p in arr:
            if i != p :
                item_pair = (i[0],p[0])
                rating_pair = (i[1],p[1])
                item_pair_list.append((item_pair,rating_pair))
    return item_pair_list
combine = nor.flatMap(combination)
groupby_combine = combine.groupByKey().filter(lambda x : len(x[1])>1)
def cosine_similarity(vec_a,vec_b):
    dot = sum(a*b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a*a for a in vec_a) ** 0.5
    norm_b = sum(b*b for b in vec_b) ** 0.5
    if (norm_a*norm_b) == 0:
        return "null"
    cos_sim = dot / (norm_a*norm_b)
    return cos_sim
def run(arr):
    vec_a =[]
    vec_b = []
    for i in arr[1]:
        vec_a.append(i[0])
        vec_b.append(i[1])
    cos_sim = cosine_similarity(vec_a,vec_b)
    return arr[0],cos_sim
last = groupby_combine.map(run)
print(last.count())
print(time.time()-start)






# Original way
import time,base64,threading,requests,json
from app import s3,s3_bucket_name,rds_host,rds_password,rds_user
from bs4 import BeautifulSoup
from Modules.SQL_module import SQL
from statistics import mean, pstdev
from itertools import combinations
# amazon = SQL(host= rds_host,user=rds_user,password=rds_password,database="amazon")


def cosine_similarity(vec_a,vec_b):
        dot = sum(a*b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a*a for a in vec_a) ** 0.5
        norm_b = sum(b*b for b in vec_b) ** 0.5
        if (norm_a*norm_b) == 0:
            return "null"
        cos_sim = dot / (norm_a*norm_b)
        return cos_sim


def deal_with_similarity():

    review_list = []
    user_dict = {}
    item_dict ={}
    user_index = -1
    item_index = -1
    t1 = time.time()
    # get data from s3
    csv = time.time()
    with open("/Users/poyuchiu/Desktop/Clothing_Shoes_and_Jewelry_sample.csv","r") as infp:
        x = []
        for i in infp.readlines():
            # print(i)
            i = i[:-1]
            i = i.split(",")
            r ={"reviewerID":i[0],"itemID":i[1],"rating":i[2]}
            x.append(r)
        x.pop(0)
    print(time.time()-csv)
    re = time.time()
    for review in x :
        # build index for reviewer
        if review['reviewerID'] in user_dict.keys():
            review['reviewerID'] = user_dict[review['reviewerID']]
        else:
            user_index += 1  
            user_dict[review['reviewerID']] = user_index
            review['reviewerID'] = user_index
        
            
        # build index for item
        if review['itemID'] in item_dict.keys():
            review['itemID'] = item_dict[review['itemID']]
        else :
            item_index += 1
            item_dict[review['itemID']] = item_index
            review['itemID'] = item_index
        review_list.append(review)
    print("trans",time.time()-re)


    use = time.time()
    user_to_items = {} # {user: []}
    for review in review_list:
        user = review['reviewerID']
        if (user not in user_to_items):
            user_to_items[user] = {}
        user_to_items[user][review["itemID"]] = int(float(review["rating"]))
    print("usertoitem",time.time()-use)

    nor = time.time()
    # Normalization
    # user_to_items = {3:{13:4,27:2}}
    for user in list(user_to_items.keys()):
        rating_list = user_to_items[user].values()
        mean_value = mean(rating_list)
        standard_dv = pstdev(rating_list)
        if standard_dv != 0:
            for item_key in user_to_items[user].keys():
                user_to_items[user][item_key] = round((user_to_items[user][item_key] - mean_value) / standard_dv,3)
        else:
            del user_to_items[user]
    print("nor",time.time()-nor)

    itemXX = time.time()
    item_to_users = {}
    # user_to_items = {3:{13:4,27:2}}
    for user in user_to_items :
        for item in user_to_items[user].keys():
            if (item not in item_to_users):
                item_to_users[item] = {}
            item_to_users[item][user] = user_to_items[user][item]
    print("item",time.time()-itemXX)
    # find item pairs
    item_packages_dict = {}
    t1 = time.time()
    for user in user_to_items:
        for i in user_to_items[user]:
            for j in user_to_items[user]:
                if i != j:
                    try:
                        item_packages_dict[(i,j)].append((user_to_items[user][i],user_to_items[user][j]))
                        # print(item_packages_dict[(i,j)])
                    except:
                        item_packages_dict[(i,j)] = [(user_to_items[user][i],user_to_items[user][j])]
        # item_packages_list.extend(combinations(list(user_to_items[user].keys()),2))
    print("pair",time.time()-t1)
    # print(item_packages_dict)
    # r =1/0
    item_index = dict(map(reversed, item_dict.items()))
    similarity_list = []
    def run(pair):
        vec_a =[]
        vec_b = []
        for i in item_packages_dict[pair]:
            vec_a.append(i[0])
            vec_b.append(i[1])
        cos_sim = cosine_similarity(vec_a,vec_b)
        return [item_index[pair[0]],item_index[pair[1]],str(cos_sim)]
    # get the similarity  {item1:{user1:4,user2:5},item2:{user1:4,user2:5}}
    sim = time.time()

    for item_package in item_packages_dict:
        if len(item_packages_dict[item_package]) >=2 : 
            similarity_pair = run(item_package)
            similarity_list.append(similarity_pair)
    print(time.time()-sim)
    print("successful")
    return similarity_list

    # put similarity_list into database
    # amazon.bulk_execute("INSERT INTO `item_similarity` (`item_1`, `item_2`, `cosine_similarity`) VALUES (%s, %s, %s)",similarity_list)

x = time.time()
similarity_list = deal_with_similarity()
print(time.time()-x)
with open("/Users/poyuchiu/Desktop/result.csv","w") as infp:
    for i in similarity_list :
        # print(i)
        infp.writelines(",".join(i)+'\n')

