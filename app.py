from flask import (Flask, render_template, flash, request, url_for, redirect,
                   make_response,Response,jsonify)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from Modules.SQL_module import SQL
from functools import wraps
import json, os, pymysql.cursors, boto3, dotenv,jwt,hashlib,redis,time
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
import socket
# Get Private Data From .env
dotenv.load_dotenv()
s3_key_id = os.getenv("aws_access_key_id")
s3_access_key = os.getenv("aws_secret_access_key")
s3_bucket_name = os.getenv("bucket_name")
s3_url = os.getenv("s3_url")
server_port = int(os.getenv("serve_port"))
sql_host = os.getenv("sql_host")
sql_user = os.getenv("sql_user")
sql_password = os.getenv("sql_password")
rds_host = os.getenv("rds_host")
rds_user = os.getenv("rds_user")
rds_password = os.getenv("rds_password")
# server init
app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='Template')
app.config['SECRET_KEY'] = 'mysecret'
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI']=f'mysql+pymysql://{rds_user}:{rds_password}@{rds_host}:3306/amazon'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')
class AmazonProduct(db.Model):
    __tablename__ = 'amazon_product'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255),nullable=False)
    img = db.Column(db.String(255),nullable=False)
    price = db.Column(db.String(255),nullable=False)
    tag = db.Column(db.String(255),nullable=False)

    def __init__(self, item_code, title, img, price, tag):
        self.item_code = item_code
        self.title = title
        self.img = img
        self.price = price
        self.tag = tag

class Similarity(db.Model):
    __tablename__ = 'item_similarity'
    id = db.Column(db.Integer, primary_key=True)
    item_1 = db.Column(db.String(255), nullable=False)
    item_2 = db.Column(db.String(255),nullable=False)
    cosine_similarity = db.Column(db.Float(),nullable=False)

    def __init__(self, item_1, item_2, cosine_similarity):
        self.item_1 = item_1
        self.item_2 = item_2
        self.cosine_similarity = cosine_similarity


# connect with AWS s3 Server
s3 = boto3.client('s3',
                  aws_access_key_id=s3_key_id,
                  aws_secret_access_key=s3_access_key)

# If you want ot upload img to S3 Server,please turn this var. into "upload"
version ="upload"
#######

stylist_db = SQL(host=rds_host,user=rds_user,password=rds_password,database="stylish")
# for table product
def create_json(sql_result):
    create_json_input = {}
    create_json_input['data'] = sql_result
    # tramsform images_list from str into list   
    sql_search_color = 'SELECT color_code as code, color_name as name from variant where product_id = %s'
    sql_search_size  = 'SELECT size from variant where product_id = %s group by size'
    sql_search_variants = 'SELECT color_code, size, stock from variant where product_id = %s '
    for index in range(len(create_json_input['data'])):
        colors = []
        for i in stylist_db.fetch_dict(sql_search_color, create_json_input['data'][index]['id']) :
            if i not in colors:
                colors.append(i)
        print(colors)        
        create_json_input['data'][index]['colors'] = colors


        images = create_json_input['data'][index]['images'].split(",")
        create_json_input['data'][index]['images'] = [i for i in images]
        create_json_input['data'][index]['description'] = json.loads(create_json_input['data'][index]['description'])
        
        create_json_input['data'][index]['variants'] = stylist_db.fetch_dict(sql_search_variants, create_json_input['data'][index]['id'])

        create_json_input['data'][index]['sizes'] = []
        size_sql_date = stylist_db.fetch_dict(sql_search_size, create_json_input['data'][index]['id'])
        for i in range(len(size_sql_date)):
            create_json_input['data'][index]['sizes'].append(size_sql_date[i]['size'])
    return create_json_input

# set the format allow to upload
allowed_extensions = set(['png', 'jpg', 'jpeg', 'gif']) 
# check if the uploading file follow the rule
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

redis = redis.Redis(host='localhost', port=6379, db=0)
def rate_limiter(fun):
    @wraps(fun)
    def decorated(*args,**kwargs):
        ip_address = request.remote_addr
        redis.set(ip_address,0,ex=60,nx=True)
        redis.incr(ip_address)
        print(redis.get(ip_address))
        if int(redis.get(ip_address)) >= 100 :
            return make_response('Your request has exceeded the allowed quantity', 429)
        return fun(*args,**kwargs)
    return decorated

@app.route("/")
def home():
    return render_template("main_page.html")


# @app.errorhandler(404)
# def not_found_error(error):
#     return Response(response="Wrong Request", status= 400)

# upload file into AWS s3 server
@app.route("/upload_image", methods=["POST"])
def upload_image():
    img_dict_stored = {}
    img_dict_stored['images'] =[]
    for i in range(len(request.files)):
        img = request.files[f"image{i}"]
        if img and allowed_file(img.filename) :
            filename = secure_filename(img.filename)
            if version == "upload":
                # upload S3 (if I want to develope some new funcion without uploading date into S3)
                img.save(filename)
                s3.upload_file(Bucket=s3_bucket_name,
                            Filename=filename,
                            Key=filename,
                            ExtraArgs={'ContentType': 'image/png'})
                os.remove(filename)
            if i == 0:
                img_dict_stored['main_image'] = s3_url + filename
            else :
                img_dict_stored['images'].append(s3_url + filename)
                print(s3_url + filename)  
                print(type(s3_url + filename))              
        else :
            return {"message": "Upload Image Failed , Please check the file are .img , .png , .jpg or .gif format"}
    return img_dict_stored


#Put data into SQL 
@app.route("/store_data", methods=["POST"])
def store_data():
    get_data = request.get_json()
    print(get_data)
    sql_insert_product = """INSERT INTO `product` (`title`,`category`, `description`, `price`, `texture`,
                `wash`, `place`, `note`, `story`, `main_image`, `images`)
                VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    sql_insert_color = "INSERT INTO `color` (`color_name`, `color_code`, `product_id`) VALUES (%s,%s, %s)"

    sql_insert_stock = "INSERT INTO `stock` (`color_code`,`size`, `stock`, `product_id`) VALUES (%s, %s, %s, %s)"

    try :
        stylist_db.execute(sql_insert_product,get_data['title'], get_data['category'],get_data['description'],
                    int(get_data['price']), get_data['texture'], get_data['wash'],
                    get_data['place'], get_data['note'], get_data['story'],
                    get_data['images']['main_image'],
                    str(get_data['images']['images']))
        print("1 su")
        product_id = stylist_db.fetch_dict("select id from product where title = %s", get_data['title'],fetch_method="one")["id"]
        print(product_id)
        for i in range(0,3):
            print(f"loop{i}")
            stylist_db.execute(sql_insert_color, get_data['variants'][i]['color_name'], get_data['variants'][i]['color_code'][1:], int(product_id))
            sizes = ["s", "m", "l"]
            for size in sizes:
                stylist_db.execute(sql_insert_stock, get_data['variants'][i]['color_code'][1:], size.upper() ,int(get_data['variants'][i][f'sizes_{size}']), int(product_id))
                print(f"success{i}")
        return {"message": "Successful update"}
    except:
        return {"message": "Failed"}




@app.route('/api/1.0/products/<string:page_name>/')
def get_product(page_name,paging = 0):
    paging_number = int(request.args.get('paging',paging))
    search_condition = f"id >=(SELECT id FROM product  WHERE category = '{page_name}' ORDER BY id limit  {(paging_number)*6}, 1)"
    
    if page_name == "all" :
        sql_search_all = 'select count(id) as count_num from product'
        sql_count_output = stylist_db.fetch_dict(sql_search_all,fetch_method="one")
        sql_search_product = f"""SELECT * FROM `product` WHERE  id >=(SELECT id FROM product ORDER BY id limit  {(paging_number)*6}, 1) order by id limit 6 """          
    elif page_name == "women" or page_name == "men" or page_name == "accessories" :
        print(page_name)
        sql_search_count ='select count(id) as count_num from product where category = %s'
        sql_count_output = stylist_db.fetch_dict(sql_search_count,page_name,fetch_method="one")
        sql_search_product = f"""SELECT * FROM `product`
                WHERE category = '{page_name}'  and {search_condition} order by id limit 6 """ 
    else :
        return Response(response="Please choose the category you want to search ", status=400)

    
    count_num = sql_count_output["count_num"]
    output_for_json = create_json(stylist_db.fetch_dict(sql_search_product))
    # print(stylist_db.fetch_dict(sql_search_product))
    if count_num - paging_number*6 >6:
        output_for_json["next_paging"] = paging_number+1    
    return jsonify(output_for_json),200

@app.route('/api/1.0/products/search/')
def search_product(keyword = None,paging = 0):
    product_keyword = "%" + request.args.get('keyword',keyword) +"%"
    paging_number = int(request.args.get('paging',paging))


    sql_search_count ="select count(id) as count_num from product where title like %s"
    sql_count_output = stylist_db.fetch_dict(sql_search_count,product_keyword,fetch_method="one")
    count_num = sql_count_output["count_num"]
    sql_search_product ="select * from product where title like %s and id >=(SELECT id FROM product ORDER BY id limit %s, 1) order by id limit 6"
    output_for_json = create_json(stylist_db.fetch_dict(sql_search_product,product_keyword,paging_number))

    if output_for_json :
        if count_num - paging_number*6 >6:
            output_for_json["next_paging"] = paging_number+1    
        return jsonify(output_for_json),200
    return Response(response="Wrong Message", status=400)


@app.route('/api/1.0/products/details/')
def search_product_detail(id = None,paging = 0):
    product_id = request.args.get('id',id)
    paging_number = int(request.args.get('paging',paging))

    sql_search_product ="select * from product where id = %s"
    output_for_json = create_json(stylist_db.fetch_dict(sql_search_product,product_id))
    # print(output_for_json)
    if product_id == None:
        return Response(response="Please add ID behind detail", status=400)
    try:
        # output_for_json['data'] = output_for_json['data'][0]  
        return jsonify(output_for_json),200
    except:
        return Response(response="not found in database", status=404)

# ###################################### login part

def password_secure_process(password):
    secure_hash = hashlib.md5()
    secure_hash.update(password.encode())
    password_decrypted = secure_hash.hexdigest()
    return password_decrypted

picture = "https://stylishforjimmy.s3-ap-northeast-1.amazonaws.com/ScreenShot_2021-02-01_2.55.35.png"


@app.route('/api/1.0/user/signup', methods =["POST"])
def sign_up():
    try:
        provider = 'native'
        get_data = request.get_json()
        name, email, password = get_data['name'], get_data['email'], get_data['password']
        sql_check_email = 'select email from user where email = %s'
        if stylist_db.fetch_list(sql_check_email,email,fetch_method="one") != None:
            return Response(response="Email Already Exists" , status=403)
        ### create secure password

        password = password_secure_process(password)
        sql_insert_user = "INSERT INTO `user` ( `provider`, `name`, `email`, `password`,`picture`) VALUES (%s, %s ,  %s, %s, %s)"
        stylist_db.execute(sql_insert_user, provider, name, email, password, picture)


        user_data = {"provider":provider, "name": name , "email": email, "picture": picture}
        payload = {"data": user_data,"exp":datetime.utcnow() + timedelta(seconds=3000) }
        access_token = jwt.encode(payload, "secret", algorithm='HS256')

        sql_get_id = 'select id from user where email = %s'
        id = stylist_db.fetch_dict(sql_get_id,email,fetch_method="one")["id"]
        user_data['id'] = id
        response_json = {}
        user_data = {"provider":provider, "name": name , "email": email, "picture": picture}
        response_json['data'] = {"access_token":access_token, "access_expired": payload["exp"], "user":user_data}
        return jsonify(response_json) 
    except Exception as e:
        return jsonify({"message":e}) 


@app.route('/api/1.0/user/signin', methods =["POST"])
def sign_in():
    get_data = request.get_json()
    provider = get_data["provider"]
    if provider == "facebook":
        access_toke = get_data['access_toke']
        ## do something
    else :
        email, password = get_data['email'], get_data['password']
        try:
            password = password_secure_process(password)
            sql_check_login = 'select password from user where email = %s'
            password_decrypted = stylist_db.fetch_dict(sql_check_login,email,fetch_method="one")["password"]

            if password_decrypted == password :
                get_id_name = stylist_db.fetch_dict("select id, name, picture from user where email = %s",email,fetch_method="one")
                id, name, picture = get_id_name["id"], get_id_name["name"], get_id_name["picture"]
                user_data = {"provider":provider, "name": name , "email": email, "picture": picture}

                payload = {"data": user_data,"exp":datetime.utcnow() + timedelta(seconds=3600) }
                access_token = jwt.encode(payload, "secret", algorithm='HS256')
                
                user_data["id"] =id
                response_json = {}
                response_json['data'] = {"access_token":access_token, "access_expired": payload["exp"], "user":user_data}
                print(response_json)
                return jsonify(response_json)
            else:
                return Response(response="SingIn Failed" , status=403)

        except:
            return Response(response="SingIn Failed" , status=403)

@app.route('/api/1.0/user/profile', methods =["GET"])
def get_access_into_profile():
    try :
        token_get = request.headers['authorization'].split(" ")[1]
        if token_get != "":
            try :
                user_data = jwt.decode(token_get, "secret", algorithms="HS256")
                response_json = {}
                response_json['data'] = user_data['data']
                return jsonify(response_json)
            except jwt.ExpiredSignatureError:
                return Response(response="Signature has expired",status=403)
        return Response(response="no token",status=401)
    except:
        return Response(response="Wrong Format",status=401)

################ dashboard
@app.route("/dashboard")
def dashboard():    
    return render_template("dashboard.html")
    
@app.route("/api/1.0/91data",methods=["POST"])
def data_return():
    database = SQL(host=rds_host,user=rds_user,password=rds_password,database="91app_data")
    chosen_day = datetime.strptime(request.get_json()['date'],'%Y-%m-%d').date()
    interval_date = chosen_day + timedelta(days=1)  ## 未來要開發時間區段，可以使用 
    
    response_json_data ={}
    user_statistic = []
    user_behavior_funnel = []    
    try:
        sql_get_dict = database.fetch_dict("select * from `statistical_data` where date = %s",chosen_day)[0]
        total_user_count, active_user , new_user, return_user = sql_get_dict['all_user_count'],sql_get_dict['active_user_count'],sql_get_dict['new_user_count'],sql_get_dict['return_user_count']
        user_statistic.extend([active_user,new_user,return_user])
        # deal with tunnel data
        view_user ,view_item_user,add_to_cart_user,checkout_user = sql_get_dict['view_count'],sql_get_dict['view_item_count'],sql_get_dict['add_to_cart_count'],sql_get_dict['checkout_count']
        user_behavior_funnel.extend([view_user,view_item_user,add_to_cart_user,checkout_user])
        response_json_data["total_user_count"] = total_user_count
        response_json_data["user_statistic"] = user_statistic
        response_json_data["user_behavior_funnel"] = user_behavior_funnel
    except:
        response_json_data["total_user_count"] = 0
        response_json_data["user_statistic"] = [0,0,0]
        response_json_data["user_behavior_funnel"] = [0,0,0,0]        
    return response_json_data



################ week_2_part_4

@app.route("/stylish/main_page")
def show_stylish_mainpage():
    return render_template("stylish_main.html")

@app.route("/recommend_list")
def show_recommend():
    return render_template("recommend.html")

@app.route("/api/1.0/amazon_similarity")
@rate_limiter
def show_similarity_data(item = None):
    item_code = request.args.get("item",item)
    amazon = SQL(user=rds_user,password=rds_password, host= rds_host,database="amazon")
    menu_dict = AmazonProduct.query.filter_by(tag='menu').all()
    choose_items_dict ={}
    for item_info in menu_dict:
        choose_items_dict[item_info.title] = item_info.item_code
    if item_code == None: 
        return ({"data":choose_items_dict})
    # check if redis have stored the recommend product
    if redis.get(item_code) :
        redis_output =redis.get(item_code)
        print("redis")
        return({"data":json.loads(redis_output)})
    else:
        # sql_output = amazon.fetch_list("select distinct(item_2) from `item_similarity` where item_1 = %s and cosine_similarity > 0.8",item_code)
        # similarity_list = [i[0] for i in sql_output]
        sql_output = Similarity.query.filter(Similarity.item_1 == item_code, Similarity.cosine_similarity > 0.8).distinct().all()
        similarity_list = [i.item_2 for i in sql_output]
        similarity_list.insert(0,item_code)
        products_detail =[]
        print(similarity_list)
        for item_code in similarity_list:
            try :
                r = AmazonProduct.query.filter_by(item_code = item_code).distinct().first()
                sql_output = r.__dict__
                del sql_output['_sa_instance_state']
                # print(sql_output)
            except:
                continue
            # sql_output = amazon.fetch_dict("SELECT distinct(title),img,price FROM `amazon_product` WHERE item_code = %s",item_code)
            products_detail.extend([sql_output])
        print(products_detail)
        redis.set(item_code,json.dumps(products_detail),ex=300)
        return({"data":products_detail})


############ midterm_dashboard
order_database = SQL(host=rds_host,password=rds_password,user=rds_user,database="midterm")
@app.route("/api/1.0/midterm_data",methods=["GET"])
@rate_limiter
def data_show():
    return_json = {}
    if redis.get('data_json') :
        redis_output =redis.get('data_json')
        print("redis")
        return redis_output
    
    total_revenue = int(order_database.fetch_list("select sum(total) as total_revenue FROM order_id_list",fetch_method="one")[0])
    products_divided_by_color = order_database.fetch_dict("SELECT color_code,color_name,FORMAT(sum(qty),0)as `count` FROM `order_product_list` GROUP by color_code")
    products_count_by_price = order_database.fetch_dict("SELECT price, sum(qty) as`count` FROM `order_product_list` GROUP by price")
    products_price_num_array = []
    for price_count in products_count_by_price:
        product_list = [price_count["price"] for i in range(int(price_count["count"]))]
        products_price_num_array.extend(product_list)
    products_divided_by_size = order_database.fetch_dict("SELECT product_id,size,sum(qty)as `count` FROM `order_product_list` WHERE product_id IN (select filter.product_id from (SELECT product_id FROM order_product_list GROUP by product_id order by sum(qty) desc LIMIT 5)as filter) GROUP by product_id,size")
    # print(products_divided_by_size)
    products_total_count = {}
    x = time.time()
    for i in products_divided_by_size:
        try :
            products_total_count[i["product_id"]] += int(i["count"])
        except:
            products_total_count[i["product_id"]] = int(i["count"])
    sort_product_list = sorted(products_total_count.items(), key=lambda d: d[1],reverse=True)
    sort_product_list = [i[0] for i in sort_product_list]
    # print(sort_product_list)
    print(time.time()-x)
    size_list = []
    index = 0
    for size in (["S","M","L"]):
        size_list.append({})
        size_list[index]["size"] = size
        size_list[index]["ids"] = sort_product_list
        size_list[index]["count"] = []
        for product in sort_product_list:
            for product_size_pair in products_divided_by_size:
                if product_size_pair['product_id'] == product and product_size_pair['size'] == size:
                    size_list[index]["count"].append(int(product_size_pair['count']))
        index += 1
    # print(size_list)
    
    return_json["total_revenue"] = total_revenue
    return_json["products_divided_by_color"] = products_divided_by_color
    return_json["products_count_by_price"] = products_price_num_array
    return_json["products_count_by_size"] = size_list
    
    redis.set('data_json',json.dumps(return_json),ex=300)
    # print(return_json)
    return json.dumps(return_json)

@app.route("/socket.test")
def test_socket():
    return render_template("socket_order.html")

@socketio.on('message')
def connect_check(msg):
    print(msg)

@socketio.on('send_data')
def receive_data(data):
    print("s",data)
    data_list = json.loads(data)['data']
    price = 1002
    order_database.execute("INSERT INTO `order_id_list`(`total`) VALUES ( %s)",price * int(data_list[2]))
    order_id = order_database.fetch_list("select order_id from order_id_list order by order_id desc limit 1")[0][0]
    order_database.execute("""
    INSERT INTO `order_product_list`(`order_id`, `product_id`, `price`, `color_code`, `color_name`, `size`, `qty`)
    VALUES (%s, %s, %s, %s, %s, %s, %s)""",order_id, int(data_list[0]), price , "#0000EE","Blue" ,data_list[1],int(data_list[2]))
    if redis.get('data_json') :
        redis.delete('data_json')
    return_json = data_show()
    
    emit("send_data",return_json, broadcast=True)

if __name__ == "__main__":
    socketio.run(app,debug=True, port=server_port)