
import random, string, re, time,dotenv , os
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime


dotenv.load_dotenv()
mongo_server = os.getenv("mongo_server")
mongo_user = os.getenv("mongo_user")
mongo_password = os.getenv("mongo_password")
client = MongoClient(mongo_server,
                     username=mongo_user,
                     password=mongo_password,
                     authSource='91data',
                     authMechanism='SCRAM-SHA-1')
db = client['91data']
collection = db.tracking_raw_realtime


def create_url(cid):
    random_num = random.uniform(0, 1)
    if random_num <= 0.22:
        event_type = "view_item"
        event_urlvalue = f"evtn={event_type}&"
        item_id = ''.join(random.choice(string.digits) for x in range(8))
        item_urlvalue = f"item_id&evtvs2={item_id}&"
        require_url = 'https://fake.data/v1/?' + cid + event_urlvalue + item_urlvalue

    elif random_num <= 0.3:
        event_type = "add_to_cart"
        event_urlvalue = f"evtn={event_type}&"
        require_url = 'https://fake.data/v1/?' + cid + event_urlvalue

    elif random_num <= 0.47:
        event_type = "checkout_progress"
        event_urlvalue = f"evtn={event_type}&"
        step = random.choice([1, 2, 3])
        checkout_urlvalue = f"step&evtvi1={step}&"
        require_url = 'https://fake.data/v1/?' + cid + event_urlvalue + checkout_urlvalue

    return require_url


def insert_Mongo():
    insert_list = []
    insert_dict = {}
    if random.uniform(0, 1) <= 0.94:
        id_code = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for x in range(32))
        client_id = id_code[0:8] + "-" + id_code[8:12] + "-" + id_code[
            12:16] + "-" + id_code[16:20] + "-" + id_code[20:]
    else:
        cursor = collection.aggregate([{"$sample": {"size": 1}}])
        for i in cursor:  # only one
            client_id = re.search(r'cid=.*?&', i["request_url"],
                                  flags=re.M)[0][4:-1]
    cid = f"cid={client_id}&"

    if random.uniform(0, 1) <= 0.95:
        event_type = "view"
        event_urlvalue = f"evtn={event_type}&"
        require_url = 'https://fake.data/v1/?' + cid + event_urlvalue
        insert_dict["request_url"] = require_url
        insert_dict["created_at"] = datetime.utcnow().strftime(
            '%Y-%m-%d %H:%M:%S')
        insert_list.append(insert_dict)
        insert_dict = {}
        try:
            url = create_url(cid)
            print(url)
            insert_dict["request_url"] = url
            insert_dict["created_at"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            insert_list.append(insert_dict)
        except:
            print(1)
    else:
        url = 'https://fake.data/v1/?' + cid + "evtn=hover&"
        insert_dict["request_url"] = url
        insert_dict["created_at"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        insert_list.append(insert_dict)
    collection.insert_many(insert_list)


while True:
    insert_Mongo()
    print("s")
    time.sleep(random.uniform(1, 3) * random.uniform(1, 2))
