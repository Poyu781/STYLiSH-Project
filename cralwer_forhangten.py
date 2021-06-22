from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import time,base64,threading,requests,json
from selenium import webdriver
from selenium.webdriver.common.by import By
from lxml import etree, html
from Modules.SQL_module import SQL
from app import rds_host,rds_password,rds_user
import re,json,random
from app import s3,s3_access_key,s3_bucket_name,s3_url
import requests,time,os
from werkzeug.utils import secure_filename
ua = UserAgent(verify_ssl=False)
stylish = SQL(host=rds_host,user=rds_user,password=rds_password,database="stylish")
crawler_result = []
image_model = "91"
def get_items_code(mainpage):
    driver = webdriver.Chrome("/usr/local/bin/chromedriver")
    driver.get(mainpage)
    driver.execute_script("window.scrollTo(0, 4000)") 
    time.sleep(2)
    driver.execute_script("window.scrollTo(4000, 8000)") 
    time.sleep(2)
    driver.execute_script("window.scrollTo(8000, 12000)") 
    time.sleep(2)
    driver.execute_script("window.scrollTo(12000,14000)") 
    time.sleep(1)
    r = driver.find_element(By.CLASS_NAME, "column-grid-container__content")
    p = r.get_attribute('innerHTML')
    result = re.findall(r'/SalePage/Index/.*?"',p)
    print(result)
    driver.quit()
    clean_man_list = []
    for i in result :
        item_code = re.search(r'\d+',i)[0]
        clean_man_list.append(item_code)
    return clean_man_list





def upload_s3(image_list):
    s3_image_list =[]
    s3_url = "https://stylishforjimmy.s3-ap-northeast-1.amazonaws.com/"
    for url in image_list:
        print(url)
        response = requests.get(url)
        filename = url[-32:].replace("/",".")   +".png"
        filename = secure_filename(filename)
        file = open(filename, "wb")
        file.write(response.content)
        file.close()

        s3.upload_file(Bucket=s3_bucket_name,
                    Filename=filename,
                    Key=filename,
                    ExtraArgs={'ContentType': 'image/png'})
        os.remove(filename)
        s3_image_list.append(s3_url+filename)
    return s3_image_list

crawler_result = []
def crawler_hangten(item,category):
    try:
        url = f'https://tw.shophangten.com/SalePage/Index/{item}'
        headers = {
                'user-agent': ua.random,
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,ja;q=0.5',
                }    
        response = requests.get(url,headers = headers)
        byte_data = response.content
        source_code = html.fromstring(byte_data)
        result = source_code.xpath("/html/body/script[8]")[0].text
        title = re.search(r'"Title":".*?"', result,flags=re.M)[0][9:-1]
        describe = re.search(r'<ul><li>.*?(</ul>)', result,flags=re.M)[0][8:-10].split("</li><li>")
        if describe[-1][0:4] == "商品貨號" :
            describe.pop()
        describe = json.dumps(describe,ensure_ascii=False)
        price = int(re.search(r'"Price":.*?,', result,flags=re.M)[0][8:-4])
        # item_code = re.search(r'"Id":.*?,', result,flags=re.M)[0][5:-1]
        pics = list(map(lambda x: "https://"+x[12:-1], re.findall(r'"PicUrl":"//.*?"',result)))
        if image_model == "s3":
            s3_urls = upload_s3(pics[0:min(len(pics),4)])
            main_image = s3_urls[0]
            images = ",".join(s3_urls[1:])
        else:
            main_image = pics[0]
            images = ",".join(pics[1:min(len(pics),4)])
        
        texture_list = ["棉質100%","聚酯纖維100%","羊毛100%","氰化物100%"]
        texture = texture_list[random.randint(0,3)]
        wash_list = ['手洗','腳洗','免洗',"給媽媽洗"]
        wash = wash_list[random.randint(0,3)]
        place_list = ['中國','台灣','越南','柬埔寨']
        place = place_list[random.randint(0,3)]
        note = "實品顏色依單品照為主"
        story  = "O.N.S is all about options, which is why we took our staple polo shirt and upgraded it with slubby linen jersey, making it even lighter for those who prefer their summer style extra-breezy."
        data_list = [category,title,describe,price,texture,wash,place,note,story,main_image,images]
        crawler_result.append(data_list)
        print("success put data into list")
    except:
        print("can't request:",url)
        return "wrong"

        

    # images = ",".join(pics[1:min(len(pics),4)])
    
    


    
    


#
def thread_crawler(item_list,category):
    threads =[]
    start_time = time.time()
    for i in range(len(item_list)):
        # print(i,'\n',url)
        threads.append(threading.Thread(target = crawler_hangten, args = (item_list[i],category,)))
        time.sleep(0.5)
        threads[i].start()
    for i in range(len(item_list)):
        # print(threads[i])
        threads[i].join()
    print(time.time() - start_time)
    return crawler_result



sql_insert = "INSERT IGNORE INTO `product` (`category`, `title`, `description`, `price`, `texture`, `wash`, `place`, `note`, `story`, `main_image`, `images`) VALUES (%s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s)"
    # stylish.execute(sql_s,category,title,describe,price,texture[0],wash_list[0],place_list[0],note,story,main_image,images)

if __name__ == "__main__":
    codes_list = get_items_code("https://tw.shophangten.com/v2/official/SalePageCategory/366940?sortMode=Sales")
    print(1)
    crawler_result = thread_crawler(codes_list,"women")
    if crawler_result :
        stylish.bulk_execute(sql_insert,crawler_result)
        print("success Update to SQL")
    else:
        print("somthing Wrong")

