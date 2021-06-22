from email.mime.multipart import MIMEMultipart
import dotenv,os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
dotenv.load_dotenv()
gmail_password = os.getenv("gmail_password")
# with open('/Users/poyuchiu/Desktop/rd.log','r') as outFile:
#     r = outFile.readlines()[-3:]
#     p = "".join(r)
# print(p)
content = MIMEMultipart()  #建立MIMEMultipart物件
content["subject"] = "Emergency !"  #郵件標題
content["from"] = "v3708599@gmail.com"  #寄件者
content["to"] = "poyu850122@gmail.com" #收件者
content.attach(MIMEText("阿伯，出事了！"))  #郵件內容



with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:  # 設定SMTP伺服器
    try:
        smtp.ehlo()  # 驗證SMTP伺服器
        smtp.starttls()  # 建立加密傳輸
        smtp.login("v3708599@gmail.com", gmail_password)  # 登入寄件者gmail
        smtp.send_message(content)  # 寄送郵件
        print("Complete!")
    except Exception as e:
        print("Error message: ", e)