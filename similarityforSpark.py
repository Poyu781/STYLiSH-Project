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

# from fake_useragent import UserAgent
# ua = UserAgent(verify_ssl=False)
# failure_item_list = []
# crawler_result = []
# def crawler_amazon(item_code):
#     url = f'https://www.amazon.com/dp/{item_code}'
#     headers = {
#             'user-agent': ua.random,
#             'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
#             }    
#     response = requests.get(url,headers = headers)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     fetch_list =[]
#     try:
#         title = soup.find("span",id="productTitle").text.replace("\n",'')
#         img_soup  = soup.find("div",id="imgTagWrapperId").img['data-a-dynamic-image']
#         images_list = list(json.loads(img_soup).keys())
#         image_url = images_list[0]
#         # if you need the image's base64
#         image_base64 = base64.b64encode(requests.get(image_url).content)
#         price = ""
#         try:
#             sale_price = soup.find("span",id= "priceblock_dealprice").text
#             price = sale_price
#         except :
#             try:
#                 origin_price = soup.find("span",id="priceblock_ourprice").text
#                 price = origin_price
#             except:
#                 price = "don't have price"

#         # set what's value need to insert
#         fetch_list.extend([item_code, title, image_url, price])
#         print(fetch_list)
#         crawler_result.append(fetch_list) 
#     except :
#         failure_item_list.append(item_code)
#         print("\n","Can't find this page", url)


# def thread_crawler(item_list):
#     threads =[]
#     start_time = time.time()
#     for i in range(len(item_list)):
#         # print(i,'\n',url)
#         threads.append(threading.Thread(target = crawler_amazon, args = (item_list[i],)))
#         time.sleep(1)
#         threads[i].start()
#     for i in range(len(item_list)):
#         # print(threads[i])
#         threads[i].join()
#     print(time.time() - start_time)
#     return crawler_result,failure_item_list




# def get_menu_list():
#     sql_output = amazon.fetch_list("""
#     select list.item_1 FROM (SELECT item_1,count(item_1) as num 
#     FROM `item_similarity` where  cosine_similarity >0.75 group by item_1) 
#     as list where list.num >= 3 """) # choose item cosine_similarity higher than 0.75 and match product more than three
#     menu_items = [i[0] for i in sql_output]

#     result,failure_item_list = thread_crawler(menu_items)
#     print(result)
#     amazon.bulk_execute("insert into amazon_product (item_code, title, img, price,tag) values(%s,%s,%s,%s,\'menu\') ",result)
#     # delete the item can not find on Amazon
#     for i in failure_item_list :
#         menu_items.remove(i)
#     return menu_items


# def get_similarity_items(menu_items):
#     similarity_items = []
#     for itemID in menu_items :
#         sql_output = amazon.fetch_list("select item_2 from item_similarity where item_1 = %s",itemID)
#         item_list = [i[0] for i in sql_output]
#         similarity_items.extend(item_list)

#     similarity_items = list(set(similarity_items))

#     result,failure_item_list = thread_crawler(similarity_items)
#     amazon.bulk_execute("insert IGNORE into amazon_product (item_code, title, img, price) values(%s,%s,%s,%s) ",result)
#     # choose_items_dict = {}
#     # for itemID in choose_items:
#     #     title = amazon.fetch_list("select title from amazon_product where item_code = %s",itemID)[0][0]
#     #     choose_items_dict[title] = itemID



# t1 = time.time()
# deal_with_similarity()
# print("total",time.time()-t1)

# t1 = time.time()
# menu_items = get_menu_list()
# print("down")
# t2 = time.time()

# get_similarity_items(menu_items)
# t3 = time.time()

# print(t2-t1,t3-t2)