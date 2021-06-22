
import io
import os
import requests,base64
from google.cloud import vision
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "mykey.json"
categories = [
    "Baptism","Communion Dres","Baseball Uniform","Basketball Uniform","Bicycle Bib","Bicycle Jersey","Bicycle Short","Brief","Bicycle Skinsuit","Bicycle Tight","Bra Strap Pad","Bra Strap","Extender","Breast Enhancing Insert","Breast Petal","Concealer","Cheerleading Uniform","Chef's Hat","Chef's Jacket","Chef's Pant","Cricket Uniform","Football Uniform","Garter Belt","Garter","Ghillie Suit","Hockey Uniform","Hunting","Fishing Vest","Hunting","Tactical Pant","Martial Arts Uniform","Motorcycle Jacket","Motorcycle Pant","Motorcycle Suit","Officiating Uniform","Soccer Uniform","Softball Uniform","Wrestling Uniform","Baby","Toddler Bottom","Baby","Toddler Diaper Cover","Baby","Toddler Dress","Baby","Toddler Outerwear","Baby","Toddler Outfit","Baby","Toddler Sleepwear","Baby","Toddler Socks","Tight","Baby","Toddler Swimwear","Baby","Toddler Top","Baby One-Piece","Bicycle Activewear","Boxing Short","Bra Accessorie","Bra","Bridal Party Dress","Chap","Coats","Jacket","Contractor Pants","Coverall","Dance Dress, Skirts",
    "Costume","Dirndl","Flight Suit","Food Service Uniform","Football Pant","Hakama Trouser","Hosiery","Hunting Clothing","Japanese Black Formal Wear","Jock Strap","Jumpsuits","Romper","Kimono Outerwear","Kimono","Leotards","Unitard","Lingerie","Lingerie Accessorie","Long John","Loungewear","Martial Arts Short","Military Uniform","Motorcycle Protective Clothing","Nightgown","Overall","Paintball Clothing","Pajama","Pant Suit","Petticoats","Pettipant","Rain Pant","Rain Suit","Religious Ceremonial Clothing","Robe","Saris","Lehenga","School Uniform","Security Uniform","Shapewear","Skirt Suit","Snow Pants","Suit","Sock","Sports Uniform","Toddler Underwear","Traditional Leather Pant","Tuxedo","Undershirt","Underwear","Underwear Slip","Vest","Wedding Dress","White Coat","Yukata","Activewear","Baby","Toddler Clothing","Dress","One-Piece","Outerwear","Outfit Set","Pant","Shirt","Top","Shirt","Dress Shirt","Short","Skirt","Skort","Sleepwear","Loungewear","Suit","Swimwear","Traditional","Ceremonial Clothing","Underwear","Sock","Uniform","Trousers",'Jeans','T-shirt',"Coat","Overcoat",'Gown','One-piece garment','Formal wear','Day dress', 'Collar','Dress shirt',"Trench coat",'Active pants', 'Denim', 'Khaki pants', 'Linens', 'Shorts', 'Sportswear'
]
# Imports the Google Cloud client library
def get_tags_colors(photo_path):
    client = vision.ImageAnnotatorClient()
    file_name = os.path.abspath(photo_path)
    # Loads the image into memory
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

#### Performs label detection on the image file
    response = client.label_detection(image=image)
    labels = response.label_annotations
    tags_list = []
    for label in labels:
        print(label.description)
        if label.description in categories:
            tags_list.append(label.description)

    response = client.image_properties(image=image)
    props = response.image_properties_annotation
    color_list = []
    for color in props.dominant_colors.colors:
        color_list.append([color.pixel_fraction,int(color.color.red),int(color.color.green),int(color.color.blue)])
    color_list = sorted(color_list,key = lambda x : x[0],reverse=True)
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    return tags_list,color_list



from Modules.SQL_module import SQL
from app import rds_host,rds_password,rds_user
stylish = SQL(host=rds_host,user=rds_user,password=rds_password,database="stylish")
# sql_output = stylish.fetch_list("SELECT main_image FROM `product` WHERE category = 'men' ")

upload_sql_list =[]
# image_list = [i[0] for i in sql_output]
image_list = ["https://s.yimg.com/zp/MerchandiseImages/5E8FC930CC-SP-6959172.jpg"]
item_code = [0]
for url in image_list:
    print(url)
    # item_code = re.search(r'SalePage/.*?/', url)[0][9:-1]
    remove_backgroud(url)
    tags_list,colors_list = get_tags_colors(output_path)
    os.remove('input.png')
    os.remove('out.png')
    # print(tags_list)
    # print(colors_list)
    if len(tags_list) == 0 :
        print("\n",item_code,"\n")
        tags_list = ["Neck","Elbow"]
    for tag in tags_list :
        if colors_list[0][0]> 0.77 and colors_list[1][0]< 0.06:
            upload_sql_list.append((item_code,tag,colors_list[0][1],colors_list[0][2],colors_list[0][3]))
        else:
            upload_sql_list.append((item_code,tag,colors_list[1][1],colors_list[1][2],colors_list[1][3]))
    print(colors_list[0:3])
# stylish.bulk_execute("INSERT INTO `colors`(`product_id`, `tag`,`red`, `green`, `blue`) VALUES (%s,%s,%s,%s,%s)",upload_sql_list)
print(upload_sql_list)



import requests,io
from PIL import Image
from PIL import ImageFile
import numpy as np
from rembg.bg import remove
def remove_backgroud(url):
    data = requests.get(url)
    with open("input.png", "wb") as f:
        f.write(data.content)
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    input_path = "input.png"
    output_path = 'out.png'

    file_rm = np.fromfile(input_path)
    rm_result = remove(file_rm)
    img = Image.open(io.BytesIO(rm_result)).convert("RGBA")
    img.save(output_path)
    return output_path