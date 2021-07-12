from pymongo import MongoClient
import re, pymysql.cursors , dotenv , os
from bson.objectid import ObjectId
import time
from Modules.SQL_module import SQL
from datetime import datetime,timedelta
dotenv.load_dotenv()
rds_host = os.getenv("rds_host")
rds_user = os.getenv("rds_user")
rds_password = os.getenv("rds_password")
mongo_server = os.getenv("mongo_server")
mongo_user = os.getenv("mongo_user")
mongo_password = os.getenv("mongo_password")

# MongoDB
# client = MongoClient(mongo_server,
#                      username=mongo_user,
#                      password=mongo_password,
#                      authSource='91data',
#                      authMechanism='SCRAM-SHA-1')
# db = client['91data']
# collection = db.tracking_raw_realtime
# RDS MySQL
database = SQL(host=rds_host,user=rds_user,password=rds_password,database="91app_data")
# data_get =[]
# def clean_data(mongo_cursor,data_get):
#     for data in mongo_cursor:
#         # print(data["created_at"])
#         put_list = []
#         data_url = data["request_url"]
#         ## get user id
#         put_list.append(re.search(r'cid=.*?&', data_url, flags=re.M)[0][4:-1])
#         # get create time
#         put_list.append(str(data['_id']))
#         put_list.append(data["created_at"])
#         # get event-type
#         put_list.append(re.search(r'evtn=.*?&', data_url, flags=re.M)[0][5:-1])

#         if put_list[3] == "view":
#             try:
#                 view_detail = re.search(r'view_detail.*', data_url, flags=re.M)[0][19:]
#                 put_list.extend([view_detail, " ", " "])
#             except:
#                 # print function is for me to debug

#                 put_list.extend([" ", ' ', " "])


#         elif put_list[3] == "view_item":
#             try:
#                 item_id = re.search(r'item_id&.*?&', data_url, flags=re.M)[0][15:-1]
#                 put_list.extend([" ", item_id, " "])
#             except:

#                 break

#         elif put_list[3] == "checkout_progress":
#             try:
#                 checkout_step = re.search(r'step&evtvi...', data_url, flags=re.M)[0][-1]
#                 put_list.extend([" ", " ", checkout_step])
#             except:

#                 break
#         else:
#             put_list.extend([" ", ' ', " "])
#         data_get.append(put_list)
#     return data_get



# def clean_Mongodata():
    
#     sql_select_newest_data = "select create_time, mongo_id from user_event order by id desc"
#     newest_data = database.fetch_dict(sql_select_newest_data,fetch_method="one")

#     cursor = collection.find({"created_at": {"$gte":newest_data['create_time']} , 
#                             "_id": {"$ne" : ObjectId(newest_data['mongo_id'])}
#                         })
#     insert_data = clean_data(cursor,[])

#     database.bulk_execute("INSERT INTO `user_event` (`client_id`, `mongo_id`, `create_time`, `event_type`, `view_detail`, `item_id`, `checkout_step`) VALUES ( %s, %s, %s, %s,%s,%s,%s)",insert_data)

total_user_count,active_user,new_user, return_user,view_user,view_item_user,add_to_cart_user,checkout_user = 0,0,0,0,0,0,0,0
import random
def insert_statistic_table():
    global total_user_count,active_user,new_user, return_user,view_user,view_item_user,add_to_cart_user,checkout_user
    today_xx = datetime.utcnow()
    today = today_xx.strftime('%Y-%m-%d')
    before_day = (today_xx-timedelta(days=1)).strftime('%Y-%m-%d')
    check_value = database.fetch_list("select id from `statistical_data` where date = %s",today,fetch_method="one")

    if check_value != None :
        value = random.randint(1,3)
        active_user += value
        new_user = (active_user*0.96)//1
        return_user = active_user - new_user
        total_user_count += value

        
        view_user = (active_user*0.95)//1
        view_item_user = (view_user*0.24)//1
        add_to_cart_user = (view_item_user*0.33)//1
        checkout_user =  (add_to_cart_user*0.42)//1
        sql_syntax = '''UPDATE `statistical_data` SET `all_user_count`=%s,
        `active_user_count`=%s,`new_user_count`=%s,`return_user_count`=%s,`view_count`=%s,
        `view_item_count`=%s,`add_to_cart_count`=%s,`checkout_count`=%s WHERE date = %s'''
        database.execute(sql_syntax,total_user_count,active_user,new_user,return_user,view_user,view_item_user,add_to_cart_user,checkout_user,today)

    else:
        total_user_count = database.fetch_list("select all_user_count from `statistical_data` where date = %s",before_day,fetch_method="one")[0]
        active_user,new_user, return_user,view_user,view_item_user,add_to_cart_user,checkout_user = 0,0,0,0,0,0,0
        # if previous data not updated yet , it will automatically update data into database
        sql_insert = "INSERT INTO `statistical_data` (`date`, `all_user_count`, `active_user_count`, `new_user_count`, `return_user_count`, `view_count`, `view_item_count`, `add_to_cart_count`, `checkout_count`) VALUES (%s ,%s,%s,%s,%s,%s,%s,%s,%s)"
        database.execute(sql_insert,today,0,0,0,0,0,0,0,0)


if __name__ == "__main__":
    total_user_count,active_user,new_user, return_user,view_user,view_item_user,add_to_cart_user,checkout_user = 0,0,0,0,0,0,0,0
    while True :
        time.sleep(7)
        insert_statistic_table()

