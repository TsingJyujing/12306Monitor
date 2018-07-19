# -*- coding: utf-8 -*-
"""
Created on Fri Sep 02 23:36:42 2016
@author: 袁逸凡
功能：获取指定日期和出发结束地点的硬卧，一旦有票就邮件通知
"""

import ssl
import json
import urllib
import winsound
import time
import datetime
import smtplib
import traceback
from email.mime.text import MIMEText

def get_traininfo_raw(train_date,from_code,to_code):
	"""
	2016-09-30
	XAY 西安
	BJP 北京
	WXH 无锡
	"""
	while(True):
		try:
			rawdata = "No data."
			time.sleep(1)
			url_mdl = "https://kyfw.12306.cn/otn/leftTicket/queryT?"+\
				"leftTicketDTO.train_date=%s&"+\
				"leftTicketDTO.from_station=%s&"+\
				"leftTicketDTO.to_station=%s&"+\
				"purpose_codes=ADULT"
			url = url_mdl % (train_date,from_code,to_code)
			#print url
			context = ssl._create_unverified_context()
			req = urllib.urlopen(url, context=context)
			rawdata = req.read()
			return json.loads(rawdata)
			#BREAK
		except:
			print "Error while analysising returns, retrying..."
	
def check_validation(struct_train_info,care_info):
	try:
		botton_text = struct_train_info['buttonTextInfo']
		struct_train_info = struct_train_info["queryLeftNewDTO"]
		
		# 仅仅关注硬卧
		rest_info = '';
		for type in care_info:
			yp_num = struct_train_info[type]
			rest_info += "Type:%s Rest:%s" % (type,yp_num)
			if yp_num==u'\u65e0' or yp_num==u'--' or yp_num==u'*':
				pass
			else:
				yp_valid = True

		start_time = struct_train_info["start_time"]
		
		if time.strptime(start_time,"%H:%M")>time.strptime("12:00","%H:%M"):
			#时间有效
			time_valid = True
		else:
			time_valid = False
			
		time_valid = True
		
		if botton_text==u'\u9884\u8ba2':
			checkin_valid = True
		else:
			checkin_valid = False
			
		if time_valid and yp_valid and checkin_valid:
			train_code = struct_train_info["station_train_code"]
			return "Valid Train:%s Start:%s Restnum:%s\n" % (train_code,start_time,rest_info),True
		else:
			return "Invalid",False
	except:
		return "Error",False

def beep_alert(repeat_times):
	for i in range(repeat_times):
		winsound.Beep(1000,200)
		time.sleep(0.1)
		winsound.Beep(1000,800)
		time.sleep(0.2)

def mail_alert(sub,content,to_list):
	#to_list=['373207102@qq.com','tsingjyujing@163.com'] 
	mail_host="smtp.qq.com"  #设置服务器
	mail_user="yuanyifan1993"    #用户名
	mail_pass="给出你的密码"   #口令 
	mail_postfix="qq.com"  #发件箱的后缀
	me="TrainAlerter"+"<"+mail_user+"@"+mail_postfix+">"  
	msg = MIMEText(content,_subtype='plain',_charset='gb2312')  
	msg['Subject'] = sub  
	msg['From'] = me  
	msg['To'] = ";".join(to_list)  
	try:
		server = smtplib.SMTP()
		server.connect(mail_host)
		server.login(mail_user,mail_pass)
		server.sendmail(me, to_list, msg.as_string())  
		server.close()
		return True  
	except Exception, e:
		print "Sending mail error: ",e
		return False
		
def get_valid_info(search_field_info):
	DateUse = search_field_info[0]
	FromLocation = search_field_info[1]
	ToLocation = search_field_info[2]
	care_info = search_field_info[3]
	raw_struct = get_traininfo_raw(DateUse,FromLocation,ToLocation)
	datalist = raw_struct['data']
	sum_valid = 0;
	info_cluster = "Date:%s \n Route: %s -> %s \n" % (DateUse,FromLocation,ToLocation);
	for data in datalist:
		info,valid = check_validation(data,care_info)
		if valid:
			print 'Valid info get:'
			print info
			info_cluster = info_cluster + "\n\n" + info
			sum_valid += 1
	if sum_valid>0:
		return info_cluster,True
	else:
		return "No valid data",False
		
if __name__=="__main__":
	tasks = []
	
	tasks.append(['2016-09-30','XAY','WXH',['yw_num','yz_num']])

	mailbox_info = ['yuanyifan@deewinfl.com','tsingjyujing@163.com']
	
	resent_count = 20
	
	print "System started, monitoring..."
	while(True):
		# 检测12306是否是能购票的阶段，否则通知了也没用啊
		hr = datetime.datetime.now().hour
		if hr<7 or hr>=23:
			#print 'System closed, sleeping...'
			time.sleep(60)
			continue
		try:
			mail_text = '';
			valid_exist = False
			del_items = []
			for task in tasks:
				info_text,valid = get_valid_info(task)
				if valid:
					valid_exist = True
					mail_text += info_text
					mail_text += "\n"
					del_items.append(task)
					
			for del_task in del_items:
				tasks.remove(del_task)
				print "Task ",del_task," has deleted, attach sucessfully."
				
			if valid_exist:
				for i in range(resent_count):
					mail_valid = mail_alert('Train ticket is valid',mail_text,mailbox_info)
					#mail_valid = True
					if mail_valid:
						print "Mail sent successfully."
						break
					else:
						print "Mail sent failed, retrying."
			#else:
			#	print "Can't find valid infomation."
		except Exception,e:
			print "Error while itering: "
			print "Error info:",e
			print "Trace back info: "
			traceback.print_exc()
		time.sleep(5)
		
