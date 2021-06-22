import requests,json
from app import rds_host,rds_password,rds_user
from Modules.SQL_module import SQL

order_mid = SQL(host=rds_host,password=rds_password,user=rds_user,database="midterm")
data = requests.get("http://13.113.12.180:1234/api/1.0/order/data")
data = json.loads(data.text)
print(data[0])
r = 1/0
order_id_list = []
product_insert_list = []
order_id = 0

for order in data :
    total_num = order['total']
    order_id += 1
    print(total_num)
    order_id_list.append((order_id,total_num))
    product_list = order["list"]
    for product in product_list:
        # print(product)
        product_id = str(product["id"])
        product_price = product["price"]
        product_color_code = product["color"]['code']
        product_color_name = product["color"]['name']
        product_size = product["size"]
        product_qty = product["qty"]
        product_insert_list.append((order_id,product_id,product_price, product_color_code, product_color_name, product_size, product_qty))


order_mid.bulk_execute("INSERT INTO `order_id_list`(`order_id`, `total`) VALUES (%s, %s)",order_id_list)
order_mid.bulk_execute("INSERT INTO `order_product_list`(`order_id`, `product_id`, `price`, `color_code`, `color_name`, `size`, `qty`) VALUES (%s, %s, %s, %s, %s, %s, %s)",product_insert_list)
