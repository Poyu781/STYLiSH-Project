import time,base64,threading,requests,json
from app import s3,s3_bucket_name,rds_host,rds_password,rds_user
from bs4 import BeautifulSoup
from Modules.SQL_module import SQL
from statistics import mean, pstdev
from itertools import combinations
amazon = SQL(host= rds_host,user=rds_user,password=rds_password,database="amazon")


def cosine_similarity(vec_a,vec_b):
        dot = sum(a*b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a*a for a in vec_a) ** 0.5
        norm_b = sum(b*b for b in vec_b) ** 0.5
        cos_sim = dot / (norm_a*norm_b)
        return cos_sim


def deal_with_similarity():
    remove_list = ["helpful",'reviewText', 'reviewTime','summary' ]
    review_list = []
    user_dict = {}
    item_dict ={}
    user_index = -1
    item_index = -1
    t1 = time.time()
    # get data from s3
    s3_obj = s3.get_object(Bucket=s3_bucket_name, Key='data.json')
    s3_data = s3_obj['Body'].read().decode("utf-8")
    str_split_data = s3_data.split("\n")

    print("S3",time.time()-t1)
    for line in str_split_data :
        review = json.loads(line)
        for remove in remove_list :
            del review[remove]
        try:
            del review["reviewerName"]
        except:
            pass

        # build index for reviewer
        if review['reviewerID'] in user_dict.keys():
            review['reviewerID'] = user_dict[review['reviewerID']]
        else:
            user_index += 1  
            user_dict[review['reviewerID']] = user_index
            review['reviewerID'] = user_index
        
            
        # build index for item
        if review['asin'] in item_dict.keys():
            review['asin'] = item_dict[review['asin']]
        else :
            item_index += 1
            item_dict[review['asin']] = item_index
            review['asin'] = item_index
        review_list.append(review)


    user_to_items = {} # {user: []}
    for review in review_list:
        user = review['reviewerID']
        if (user not in user_to_items):
            user_to_items[user] = {}
        user_to_items[user][review["asin"]] = review["overall"]
    

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

    item_to_users = {}
    # user_to_items = {3:{13:4,27:2}}
    for user in user_to_items :
        for item in user_to_items[user].keys():
            if (item not in item_to_users):
                item_to_users[item] = {}
            item_to_users[item][user] = user_to_items[user][item]

    # find item pairs
    item_packages_list = []
    t1 = time.time()
    for user in user_to_items:
        item_packages_list.extend(combinations(list(user_to_items[user].keys()),2))
    print("pair",time.time()-t1)


    item_index = dict(map(reversed, item_dict.items()))
    similarity_list = []
    # get the similarity
    for item_package in item_packages_list:
        item1_reviews_dict = item_to_users[item_package[0]]
        item2_reviews_dict = item_to_users[item_package[1]]
        item1_users = item1_reviews_dict.keys()
        item2_users = item2_reviews_dict.keys()
        user_set = (set(item1_users) & set(item2_users))
        if len(user_set) > 2 :
            vec_item1 = []
            vec_item2 = []
            for user in list(user_set):
                vec_item1.append(item1_reviews_dict[user]) # get rating
                vec_item2.append(item2_reviews_dict[user])
            similarity = cosine_similarity(vec_item1,vec_item2)

            similarity_pair = (item_index[item_package[0]],item_index[item_package[1]],similarity)
            if similarity_pair not in similarity_list:
                similarity_list.append(similarity_pair)
    print("successful")
    # put similarity_list into database
    amazon.bulk_execute("INSERT INTO `item_similarity` (`item_1`, `item_2`, `cosine_similarity`) VALUES (%s, %s, %s)",similarity_list)



from fake_useragent import UserAgent
ua = UserAgent(verify_ssl=False)
failure_item_list = []
crawler_result = []
def crawler_amazon(item_code):
    url = f'https://www.amazon.com/dp/{item_code}'
    headers = {
            'user-agent': ua.random,
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            }    
    response = requests.get(url,headers = headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    fetch_list =[]
    try:
        title = soup.find("span",id="productTitle").text.replace("\n",'')
        img_soup  = soup.find("div",id="imgTagWrapperId").img['data-a-dynamic-image']
        images_list = list(json.loads(img_soup).keys())
        image_url = images_list[0]
        # if you need the image's base64
        image_base64 = base64.b64encode(requests.get(image_url).content)
        price = ""
        try:
            sale_price = soup.find("span",id= "priceblock_dealprice").text
            price = sale_price
        except :
            try:
                origin_price = soup.find("span",id="priceblock_ourprice").text
                price = origin_price
            except:
                price = "don't have price"

        # set what's value need to insert
        fetch_list.extend([item_code, title, image_url, price])
        print(fetch_list)
        crawler_result.append(fetch_list) 
    except :
        failure_item_list.append(item_code)
        print("\n","Can't find this page", url)


def thread_crawler(item_list):
    threads =[]
    start_time = time.time()
    for i in range(len(item_list)):
        # print(i,'\n',url)
        threads.append(threading.Thread(target = crawler_amazon, args = (item_list[i],)))
        time.sleep(1)
        threads[i].start()
    for i in range(len(item_list)):
        # print(threads[i])
        threads[i].join()
    print(time.time() - start_time)
    return crawler_result,failure_item_list




def get_menu_list():
    sql_output = amazon.fetch_list("""
    select list.item_1 FROM (SELECT item_1,count(item_1) as num 
    FROM `item_similarity` where  cosine_similarity >0.75 group by item_1) 
    as list where list.num >= 3 """) # choose item cosine_similarity higher than 0.75 and match product more than three
    menu_items = [i[0] for i in sql_output]

    result,failure_item_list = thread_crawler(menu_items)
    print(result)
    amazon.bulk_execute("insert into amazon_product (item_code, title, img, price,tag) values(%s,%s,%s,%s,\'menu\') ",result)
    # delete the item can not find on Amazon
    for i in failure_item_list :
        menu_items.remove(i)
    return menu_items


def get_similarity_items(menu_items):
    similarity_items = []
    for asin in menu_items :
        sql_output = amazon.fetch_list("select item_2 from item_similarity where item_1 = %s",asin)
        item_list = [i[0] for i in sql_output]
        similarity_items.extend(item_list)

    similarity_items = list(set(similarity_items))

    result,failure_item_list = thread_crawler(similarity_items)
    amazon.bulk_execute("insert IGNORE into amazon_product (item_code, title, img, price) values(%s,%s,%s,%s) ",result)
    # choose_items_dict = {}
    # for asin in choose_items:
    #     title = amazon.fetch_list("select title from amazon_product where item_code = %s",asin)[0][0]
    #     choose_items_dict[title] = asin



t1 = time.time()
deal_with_similarity()
print("total",time.time()-t1)

t1 = time.time()
menu_items = get_menu_list()
print("down")
t2 = time.time()

get_similarity_items(menu_items)
t3 = time.time()

print(t2-t1,t3-t2)