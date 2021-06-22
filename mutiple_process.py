
import time


import csv
import pandas as pd
#Clothing_Shoes_and_Jewelry.csv
#Clothing_Shoes_and_Jewelry_sample.csv
#Clothing_Shoes_and_Jewelry_small.csv

# r = time.time()
# s3_obj = s3.get_object(Bucket=s3_bucket_name, Key='Clothing_Shoes_and_Jewelry_small.csv')
# s3_data = s3_obj['Body']
# print("s3",time.time()-r)
# print(s3_data)



# pool = Pool(8) # Pool() 不放參數則默認使用電腦核的數量
# pool.map(claw_a,args) 
# pool.close()  
# pool.join() 
# m = mp.Manager()
# queue = m.Queue()

from multiprocessing import Process,Queue


def group_by(q,df):
    r = time.time()
    result = df.groupby(['reviewerID'])['rating'].agg(sum=('sum'),count=("count"))
    q.put(result)
    print("function",time.time()-r)
# queue = queue.Queue()
if __name__ == '__main__':
    total = time.time()
    queue = Queue()
    rets = []
    procs = []
    chunk_data = pd.read_csv("~/Desktop/a.csv",chunksize=10000000)  
    print("createTextFile",time.time()-total)

    for df in chunk_data:
        t = time.time()
        proc = Process(target=group_by, args=(queue,df))
        procs.append(proc)
        proc.start()
        print("start process",time.time()-t)
    t = time.time()
    for proc in procs:
        ret = queue.get() # will block
        rets.append(ret)
    print("collect dataframe from process",time.time()-t)

    a = time.time()
    for proc in procs:
        proc.join()
    result = pd.concat(rets)
    print(time.time()-a)

    x = time.time()
    out = result.groupby(['reviewerID'])[['sum','count']].agg('sum')
    print("groupby again",time.time()-x)
    
    def div(a,b):
        return a/b
    
    avg = time.time()
    out["avg"]= div(out["sum"], out["count"])
    print("avg",time.time()-avg)

    store = time.time()
    out.to_csv('~/Desktop/v9.csv', index=True)
    print("store",time.time()-store)
    print("total",time.time()-total)
    print(out.shape)



# r = time.time()
# p = chunk_data.groupby(['reviewerID'])['rating'].agg(sum=('sum'),count=("count"))
# p.to_csv('~/Desktop/a.csv', index=True)
# print("avg",time.time()-r)
# print(r.to_dict())
# str_split_data = s3_data.split("\n")


# r = 0
# print(str_split_data[0:5])
# for i in str_split_data :
#     data = i.split(",")
#     print(data)
#     r += 1
#     if r >10:
#         break







# if __name__ == '__main__':  #必須放這段代碼，不然會Error
#     args = ["pr1","pr2","pr3","pr4","pr5","pr6","pr7","pr8"]#,"pr9","pr10"]
#     r = time.time()
#     # pool = Pool(8) # Pool() 不放參數則默認使用電腦核的數量
#     # pool.map(claw_a,args) 
#     # pool.close()  
#     # pool.join() 
#     ap = mp.Process(target=claw_a, args=("pr1",))
#     jk = mp.Process(target=claw_a, args=("pr2",))
#     p3 = mp.Process(target=claw_a, args=("pr3",))
#     p4 = mp.Process(target=claw_a, args=("pr4",))

#     # 開始加速執行
#     ap.start()
#     jk.start()
#     p3.start()
#     p4.start()

#     # 結束多進程
#     ap.join()
#     jk.join()
#     p3.join()
#     p4.join()

#     print("pro",time.time()-r)


# single-Process
    # queue = Queue()
    # rets = []
    # procs = []
    # r = time.time()
    # chunk_data = pd.read_csv("~/Desktop/Clothing_Shoes_and_Jewelry_sample.csv")#,chunksize=1500000000)  
    # print("pd",time.time()-r)

    # result =group_by("2",chunk_data)
    # out = result.groupby(['reviewerID'])[['sum','count']].agg('sum')
    # def div(a,b):
    #     return a/b
    # avg = time.time()
    # out["avg"]= div(out["sum"], out["count"])
    # print("avg",time.time()-avg)
    # # out.apply(lambda x: x['sum'] /x['count']).reset_index(name='avg')
    # store = time.time()
    # out.to_csv('~/Desktop/v9.csv', index=True)
    # print("store",time.time()-store)
    # print("s",time.time()-r)
    # print(out.shape)