#coding=utf-8

import requests
import re,sys,os
import json
import threading
import time

 
class spider:
    def __init__(self,sid,name):
      
        self.id = sid
        self.headers = { "Accept":"text/html,application/xhtml+xml,application/xml;",
            "Accept-Encoding":"gzip",
            "Accept-Language":"zh-CN,zh;q=0.8",
            "Referer":"http://www.taobao.com/",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
            }
 
        self.name=name
 
    def openurl(self,url):
         
        self.request = requests.get(url,headers = self.headers)        
        if self.request.ok:
            return self.request.text
  
    def matchs(self):
         
        tmall_exp = r"Setup\(([\s\S]+?)\);"### 匹配商品数据的正则
        detail= r"src=\"(https://img\S+?[jpgifn]+?)\""  ###匹配 商品详情图的正则
        html = self.openurl("https://detail.tmall.com/item.htm?id=%s"%self.id)
        print("扫描：https://detail.tmall.com/item.htm?id=%s"%self.id)
        data = re.findall(tmall_exp,html)
        data = json.loads(data[0])
        #final_json = json.dumps(data, sort_keys=True, indent=4)  #保存json
        #with open('%s.json'%self.id, 'w') as f:
        #    f.write(final_json)
 
        if 'propertyPics' in data.keys():
            color_data =data['valItemInfo']['skuList']  ### 这里获得商品的颜色信息列表   包括颜色编码  颜色名称,商品skuID
            main_img = data['propertyPics'] ## 这里包括了主图和颜色图的地址
            detail_html = self.openurl("http:"+data['api']["httpsDescUrl"]) #获取描述图地址
            detail_image = re.findall(detail,detail_html)
            self.newdata={"MAIN":main_img['default'],"DETAIL":detail_image,"id":self.id,}
            #print(main_img['default'])
            psvs = []
            self.newdata['COLOR']=[]
        
            for v in range(len(color_data)):
                if ";"in color_data[v]["pvs"]:
                    psv = color_data[v]['pvs'][color_data[v]['pvs'].find(";")+1:]
                else:
                    psv = color_data[v]['pvs']
                if psv in psvs:
                    continue
                psvs.append(psv)

                try:  #判断propertyPics中是否存在颜色图地址
                    color_img = main_img[";"+psv+";"]
                except:
                    #print(sys.exc_info())
                    return

                self.newdata['COLOR'].append({color_data[v]["names"]:main_img[";"+psv+";"]})

        else:
            main_img_exp = r"<ul id=\"J_UlThumb\"([\s\S]+?)</ul>"
            main_img1 = re.findall(main_img_exp,html)
            #print(main_img1)
            main_img = re.findall(r"src=\"(//img\S+?jpg)_60x60q90.jpg\"",main_img1[0])
            #print(main_img)
            
            detail_html = self.openurl("http:"+data['api']["httpsDescUrl"])
            detail_image = re.findall(detail,detail_html)
            self.newdata={"MAIN":main_img,"DETAIL":detail_image,"id":self.id,}


        return self.newdata

    def download(self):
        if len(self.newdata)>0:
            if 'MAIN' in self.newdata.keys():
                for x in range(len(self.newdata['MAIN'])):
                    threading.Thread(target=self.download_main,args=(self.newdata['MAIN'][x],x)).start()
            if 'COLOR' in self.newdata.keys():
                for x in self.newdata['COLOR']:
                    threading.Thread(target=self.download_color,args=(x,)).start()
            for x in range(len(self.newdata['DETAIL'])):
                threading.Thread(target=self.download_detail,args=(self.newdata['DETAIL'][x],x)).start()
        return
 
 
    def download_main(self,url,index):
        try:
            img = requests.get("http:"+url,stream=True,headers = self.headers,timeout=10)
        except:
            print(sys.exc_info())
            return
        if img.ok:
            if not os.path.exists(self.name+"/主图"):
                try:
                    os.makedirs(self.name+"/主图")
                except:
                    pass
            f = index + 1
            imgs = open(self.name+"/主图/%s.jpg"%f,"wb")
            imgs.write(img.content)
            imgs.close()
             
    def download_color(self,url):
          
        try:
            img = requests.get("http:"+url[list(url.keys())[0]][0],stream=True,headers = self.headers,timeout=10)
        except:
            print(sys.exc_info())
            return
        if img.ok:
            if not os.path.exists(self.name+"/颜色图"):
                try:
                    os.makedirs(self.name+"/颜色图")
                except:
                    pass
            if "/"in list(url.keys())[0]:
                color = list(url.keys())[0].replace("/","_")
            elif "\\" in list(url.keys())[0]:
                color = list(url.keys())[0].replace("\\","_")
            else:
                color = list(url.keys())[0]
            f = color + 1
            imgs = open(self.name+"/颜色图/%s.jpg"%f,"wb")
            imgs.write(img.content)
            imgs.close()
 
    def download_detail(self,url,index):

        try:
            img = requests.get(url,stream=True,headers = self.headers,timeout=10)
        except:
            print(sys.exc_info())
            return
        if img.ok:
            if not os.path.exists(self.name+"/描述图"):
                try:
                    os.makedirs(self.name+"/描述图")
                except:
                    pass

            x = re.findall(r"(jpg|gif|png)",url) #判断图片格式
            #print(x[0])
            f = index + 1
            if x[0] == 'jpg':
                imgs = open(self.name+"/描述图/%s.jpg"%f,"wb")
                imgs.write(img.content)
                imgs.close()
            elif x[0] == 'gif':
                imgs = open(self.name+"/描述图/%s.gif"%f,"wb")
                imgs.write(img.content)
                imgs.close()
            elif x[0] == 'png':
                imgs = open(self.name+"/描述图/%s.png"%f,"wb")
                imgs.write(img.content)
                imgs.close()

				
def txt_wrap_by(start_str, end, text):
    start = text.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = text.find(end, start)
        if end >= 0:
            return text[start:end].strip()

if __name__ =="__main__":
    hello = '''
		-----------------------------------------
		|   欢迎使用自动抓取天猫产品图片工具   	|
		|   Author：Sam.Wang   Ver：2018.10.10	|
		-----------------------------------------
	'''
    print(hello)
    today = time.strftime('%Y%m%d', time.localtime())
    #print(today)
	
	
    for line in open('url.txt','r',encoding='UTF-8'):
        #忽略#开头的行
        if '#' in line.strip():
            continue
        #如果id是以"?id"形式的
        elif '?id' in line.strip():
            sid = line.split('?id=')[-1].split('&')[0]
            #print(sid)
            taobao = spider(sid,"产品图片/"+today+'/'+sid)
            taobao.matchs()
            taobao.download()
        #如果id是以"&id"形式的
        elif '&id' in line.strip():
            sid = line.split('&id=')[-1].split('&')[0]
            #print(sid)
            taobao = spider(sid,"产品图片/"+today+'/'+sid)
            taobao.matchs()
            taobao.download()
			
			
    print("图片下载完成！")

	
	