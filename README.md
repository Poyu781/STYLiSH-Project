This is Assignment 1  
My name is Jimmy  
＝＝＝＝＝＝＝＝  
Ｔhis is Week_0_Part_2  
My Url : http://18.177.185.177/    
  
1. Create a aws ec2 server  
ref. : https://ithelp.ithome.com.tw/articles/10236617  
2. Set Elastic IPs and Security Group (Follow by aw instruction) 
3. log in Server with .pem  
4. Install miniconda for virtual Env.  
ref. : https://wszhan.github.io/2018/04/09/installing-anaconda-on-ec2.html  
5. Create Env. and install python and flask to run app.py  
6. Install Nginx for setting reverse proxy to port = 80  
ref. : https://gist.github.com/soheilhy/8b94347ff8336d971ad0  
7. Install npm ,then install pm2 to run Web Server in the background  
ref. : https://docs.aws.amazon.com/zh_tw/sdk-for-javascript/v2/developer-guide/setting-up-node-on-ec2-instance.html  
ref. : https://gokhang1327.medium.com/deploying-flask-app-with-pm2-on-ubuntu-server-18-04-992dfd808079  


## week_2_part_5
#### How to update data pipeline automatically:
##### Setting crontab 
Type `crontab -e` and add
 `0 0 */3 * * sh ~/Data-Engineering-Class-Batch13/students/Jimmy/pipeline_script.sh >> status.log`

The Script will run once every three days to update the data !
It will be make more sense that you invoke the script by AWS CloudWatch to detect whether raw data have increased . 



