#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import choice
import subprocess,datetime,os,sys,time,signal
import string
import re
from gevent import monkey;monkey.patch_all()
import gevent
from gevent import pool
import pexpect

#并发的控制
g = pool.Pool(5)

# gevent.monkey.patch_all()

#log文件的创建
def touchfile():
	os.system('[ -e log.txt ]||touch log.txt')
	os.system('rm -f neterror.txt;touch neterror.txt')
	os.system('rm -f authpass.txt;touch authpass.txt')
	os.system('rm -f autherror.txt;touch autherror.txt')
	os.system('rm -f tryauthpass.txt;touch tryauthpass.txt')
	os.system('mv passwordall.txt passwordall$(date +%F-%H-%M-%s).txt;touch passwordall.txt')
	os.system('mv password.txt password$(date +%F-%H-%M-%s).txt;touch password.txt')
	os.system('mv passworderror.txt passworderror$(date +%F-%H-%M-%s).txt;touch passworderror.txt')
	os.system('rm -f passwordexcept.txt;touch passwordexcept.txt')
	os.system('rm -f neterroragain.txt;touch neterroragain.txt')
	

#创建随机密码
def GenPassword(length=8,chars=string.ascii_letters+string.digits):
    zhi1=''.join([choice(chars) for i in range(length)])
    rzhi='%sA1'%zhi1
    return rzhi
#print(GenPassword(10))


def log(data):
	filelog=open('log.txt','a')
	timedata=time.strftime('%Y-%m-%d %H:%M %S',time.localtime(time.time()))
#	print a
	filedata='\n %s \n%s\n' %(timedata,data)
	filelog.write(filedata)
	filelog.close()

#遍历校验数据
def redata():
	ipmitxt = open('ipmi.txt','r')
	txtdata=ipmitxt.readlines()
	try:
    	     for x in txtdata:
    		b=x.split(' ')
    		ipaddr=b[0]
    		password=b[1]
    		info=' '.join(b[2:])
		username='admin'
    		g.spawn(letgo,ipaddr,username,password,info)
		g.join()
		print x
	except Exception, e:
		print e
	finally:
		print "有可能是list越界了"
		ipmitxt.close()
	

#遍历修改密码数据
def modifydata():
	ipmitxt = open('authpass.txt','r')
	txtdata=ipmitxt.readlines()
    	for x in txtdata:
    		b=x.split(' ')
    		ipaddr=b[0]
    		password=b[1]
    		info=' '.join(b[2:])
		username='admin'
    		modifypassword(ipaddr,username,password,info)
	ipmitxt.close()

#再次进行网络测试
def networkagain():
	print "第二轮 网络的测试"
	nettxt = open('neterror.txt','r')
        netdata=nettxt.readlines()
        for x in netdata:
                b=x.split(' ')
                ipaddr=b[0]
                password=b[1]
                info=' '.join(b[2:])
                username='admin'
		pingdata=os.popen('ping %s -c 1|grep "64 bytes"' % ipaddr).read()
		if pingdata:
			print "%s 再次测试为网络通" %ipaddr
			cmd="ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,password)
			result=timecontrol(cmd)
			rejieguo=re.search(r"IP Address", result)
			if rejieguo:
		                 print "%s is 通过了验证 " %ipaddr
                                 passlog=open('authpass.txt','a')
                                 passlogdata='%s %s %s' %(ipaddr,password,info)
                                 passlog.write(passlogdata)
                                 passlog.close()		
			else:
				 print "第二次还是没有通过验证"
		else:
			print "%s 网络还是不通" %ipaddr
		        netagainlog=open('neterroragain.txt','a')
                        netagainlogdata='%s %s %s' %(ipaddr,password,info)
                        netagainlog.write(netagainlogdata)
                        netagainlog.close()  
		
        nettxt.close()	


#密码自动推送推送
def expectcmd(ipaddr,username,password,num,newpassword):
	child = pexpect.spawn('ipmitool -I lanplus -H %s -U %s -P %s user set password %s' %(ipaddr,username,password,num))
        child.expect ('Password:')
	child.sendline (newpassword)
        child.expect ('Password:')
	child.sendline (newpassword)
	print child.before


#这个是用来获取admin所在的id的

def adminnum(ipaddr,username,password,info):
	xxhao=re.search(r"Dell", info)
	cmd=''
	infonum=''
	print infonum
        if xxhao:
		infonum='1'
		print "if  %s"%infonum
		cmd='ipmitool -I lanplus -H %s -U %s -P %s user list %s'%(ipaddr,username,password,infonum)
	        ab=timecontrol(cmd)
#       print ab
	        xh=re.search(r"(.*admin.*)",ab)
        	if xh:
                	zhi=xh.group()
        	print zhi
	        forzhi=zhi.split(' ')
        	return forzhi[0]
		exit
	cmd='ipmitool -I lanplus -H %s -U %s -P %s user list 2'%(ipaddr,username,password)
	ab=timecontrol(cmd)
#	print ab
	xh=re.search(r"(.*admin.*)",ab)
	if xh:
     		zhi=xh.group()
	print zhi
	forzhi=zhi.split(' ')
	return forzhi[0]

#这个是用来修改密码
def  modifypassword(ipaddr,username,password,info):
	try:
        	print "正在获取 %s 的admin ID号码"%ipaddr 
		numzhi=adminnum(ipaddr,username,password,info)
        	print "正在修改 %s 的密码"%ipaddr 
	        newpassword=GenPassword(10)
#这个是把新旧的信息都放在一个日志里面的
		olddata='旧的\n%s %s %s'%(ipaddr,username,password)
		log(olddata)
		newdata='新的\n%s %s %s'%(ipaddr,username,newpassword)
		log(newdata)

		mocmd='ipmitool -I lanplus -H %s -U %s -P %s user set password %s %s' %(ipaddr,username,password,numzhi,newpassword)
	        moinfo=timecontrol2(mocmd)
#	xh=re.search(r"HP", info)
#	if xh:
#	        print "已经识别为HP"
#		numzhi=adminnum(ipaddr,username,password)
#		mocmd='ipmitool -I lanplus -H %s -U %s -P %s user set password %s %s' %(ipaddr,username,password,numzhi,newpassword)
#        	moinfo=timecontrol(mocmd)
        	os.system('[ -e password.txt ]||touch password.txt')
#检查是否修改成功,成功的话，写入到
		print "检测是否修改成功"
		cmd="ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,newpassword)
		result1=timecontrol(cmd)
		checkmopasswd=re.search(r"IP Address", result1)
		if checkmopasswd:
			print "%s 的密码修改为 %s" %(ipaddr,newpassword)
		        mpasswd=open('password.txt','a')
       		        mpasswddata='%s %s %s'%(ipaddr,newpassword,info)
        		mpasswd.write(mpasswddata)
       	        	mpasswd.close()
		else:
		        print "%s 修改密码失败" %(ipaddr)
#		trycmd='ipmitool -I lanplus -H %s -U %s -P %s user list 2|grep admin|head -n 1|cut -b 1" %(ipaddr,username,password)'
#		num=timecontrol(trycmd)
#		num=os.popen("ipmitool -I lanplus -H %s -U %s -P %s user list 2|grep admin|head -n 1|cut -b 1" %(ipaddr,username,password)).read()
#		checkmopasswd2=re.search(r"IP Address", result4)
#		if checkmopasswd2:		
#			print "%s 的密码修改为 %s" %(ipaddr,newpassword)
#                	mpasswd=open('password.txt','a')
#	                mpasswddata='%s %s %s'%(ipaddr,newpassword,info)
#        	        mpasswd.write(mpasswddata)
#                	mpasswd.close()
#		else:
#			mpasswd=open('passworderror.txt','a')
#                	mpasswddata='%s 修改密码错误\n'%(ipaddr)
#        	        mpasswd.write(mpasswddata)
#	                mpasswd.close()

               	        mpasswd=open('passworderror.txt','a')
			mpasswddata='%s %s %s'%(ipaddr,password,info)
        	        mpasswd.write(mpasswddata)
                	mpasswd.close()
	except Exception, e:
		mpasswd=open('passwordexcept.txt','a')
                mpasswddata='%s %s %s'%(ipaddr,password,info)
                mpasswd.write(mpasswddata)
                mpasswd.close()
	

def passwordall():
#	os.system("cat neterroragain.txt>>password.txt")
#	os.system("cat passworderror.txt >>password.txt")
	w = open('passworderror.txt','r')
	wread = w.read()
	aa=open('passwordall.txt','a')
	aa.write(wread)
	aa.close()
	w.close( )


#试图猜测默认密码
def  tryagain(ipaddr,username,password,info,tryfor):

#已经给出默认的用户-密码 不用遍历里面的list
	if tryfor=='no':
		tryusername=['root','admin','administrator','Administrator']
		print "%s 试图猜测默认密码" %ipaddr

                cmd="ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,password)
                result=timecontrol(cmd)
		

		retry=re.search(r"IP Address", result)
		if retry:
		        passlog=open('authpass.txt','a')
	                passlogdata='%s %s %s' %(ipaddr,password,info)
        	        passlog.write(passlogdata)
                        passlog.close()
			
			print "猜测成功,通过验证"
		  	tryagainlog=open('tryauthpass.txt','a')
	          	trydata='%s %s %s' %(ipaddr,password,info)
		  	tryagainlog.write(trydata)
		        tryagainlog.close()
        
		else:
	    	#	return "false"
			print " %s 猜测密码失败 " %ipaddr

#进行尝试里面的所有密码

	elif tryfor=='yes':
		print "尝试密码破解" 
		trypd=['oaksadmin','admin','root','calvin','duduadmin','123456']
		for i in trypd:
			print "尝试密码 %s"%i
                	cmd="ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,i)
	                result=timecontrol(cmd)
			retry=re.search(r"IP Address", result)
			if retry:
				passlog=open('authpass.txt','a')
				passlogdata='%s %s %s' %(ipaddr,password,info)
				passlog.write(passlogdata)
				passlog.close()

				tryagainlog=open('tryauthpass.txt','a')
				trydata='%s %s %s' %(ipaddr,password,info)
				tryagainlog.write(trydata)
				tryagainlog.close()
			else:
				authlog=open('autherror.txt','a')
				authlogdata='%s %s %s' %(ipaddr,password,info)
				authlog.write(authlogdata)
				authlog.close()

			
	else:
		print "没有给tyrfor的参数,问题可能出在匹配正则的上"			


def timecontrol(command):  
      timeout='0.5'
      cmd = command.split(" ")
      print cmd
      start = datetime.datetime.now()
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      while process.poll() is None:
          time.sleep(0.2)
          now = datetime.datetime.now()
          if (now - start).seconds> timeout:
              os.kill(process.pid, signal.SIGKILL)
              os.waitpid(-1, os.WNOHANG)
              return None
      return process.stdout.read()

def timecontrol2(command):  
      timeout='0.9'
      cmd = command.split(" ")
      print cmd
      start = datetime.datetime.now()
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      while process.poll() is None:
          time.sleep(0.2)
          now = datetime.datetime.now()
          if (now - start).seconds> timeout:
              os.kill(process.pid, signal.SIGKILL)
              os.waitpid(-1, os.WNOHANG)
              return None
      return process.stdout.read()

    

#异步后Timeout 超时的处理
def letgo(ipaddr,username,password,info):
	try:
	    with gevent.Timeout(3, False) as timeout:
			print "正在进行 %s "%ipaddr
	    		ifdata=''
	    		#测试网络是否通
			pingdata=os.popen('ping %s -c 1|grep "64 bytes"' % ipaddr).read()
			#如果网络通的话
			if pingdata:
				print "%s 网络通" %ipaddr
				cmd="ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,password)
				result=timecontrol(cmd)
			#	result=os.popen("ipmitool -I lanplus -H %s -U %s -P %s lan print" %(ipaddr,username,password)).read()
				rejieguo=re.search(r"IP Address", result)
				if rejieguo:
					print "%s is 通过了验证 " %ipaddr
					passlog=open('authpass.txt','a')
		                        passlogdata='%s %s %s' %(ipaddr,password,info)
		                        passlog.write(passlogdata)
		              	        passlog.close()
		            	else:
				#没有通过验证，再次尝试密码碰撞
					trypd=['oaksadmin','admin','root','calvin','duduadmin','123456']
					dl3xxg5=re.search(r"HP.*DL3.*G[0-5]", info)
					if dl3xxg5:
						print "无需尝试,不支持ipmi协议"

					dl1xx=re.search(r"HP.*DL1..", info)
					if dl1xx:
					#默认用户名admin，默认密码admin
						print "admin admin"
						tryfor='no'
						tryagain(ipaddr,'admin','admin',dl1xx.group(),tryfor)
					dl2000=re.search(r"HP.*DL2000", info)
					if dl2000:
						print "admin admin"
						tryfor='no'
						tryagain(ipaddr,'admin','admin',dl2000.group(),tryfor)
							
					dl3xxg7=re.search(r"HP.*DL3.*G[7-9]", info)
					if dl3xxg7:
						print "administrator"
						tryfor='yes'
						tryagain(ipaddr,'administrator','password',dl3xxg7.group(),tryfor)
					hpse1220=re.search(r"HP.*SE1220",info)
					if hpse1220:
						print "Administrator"
						tryfor='yes'
						tryagain(ipaddr,'Administrator','password',hpse1220.group(),tryfor)

					dell=re.search(r'Dell',info)
					if dell:
						print "root"
						tryfor='yes'
						tryagain(ipaddr,'root','password',dell.group(),tryfor)
							
					ifdata="网络是通的 但是验证不了"
					print "%s  %s"%(ipaddr,ifdata)
					authlog1=open('autherror.txt','a')
					authlogdata='%s %s %s' %(ipaddr,password,info)
					authlog1.write(authlogdata)
					authlog1.close()
					print "55555"

			#如果不通的话
			else:
				ifdata='网络是不通的'
				pinglog=open('neterror.txt','a')
				pinglogdata='%s %s %s' %(ipaddr,password,info)
				pinglog.write(pinglogdata)
				pinglog.close()
					
				ifserverinfo=re.search(r"DL160", info)	
				if ifserverinfo:
					ncdata=os.popen('nc -v -z -w2 %s 23' %ipaddr).read()
					renc=re.search(r"succeeded", ncdata)
					if renc:
					    	print "23 端口是通的"
					    	pinglog=open('neterror.txt','a')
						pinglogdata='%s %s 23端口是通的\n' %(ipaddr,ifdata)
						pinglog.write(pinglogdata)
						pinglog.close()

					else:
			 		 	print "23 端口是不通的"

#			print "%s  is bad 原因是 咱们太快了" %ipaddr
#			try:
#				filelog=open('log.txt','a')
#				filedata='%s 莫名的错误 \n' % ipaddr
#				filelog.write(filedata)
#			except Exception, e:
#				print "妹的，写入有问题"
#			finally:
#				filelog.close()
	except Exception, e:
		print "gevent io 出现问题"
	finally:
		pass
			
# 从接口获取数据

# jobs = [gevent.spawn(letgo,ipaddr,username,password) for i in range(10)]

if __name__ == '__main__':
	print '\n'
	os.system('echo -e "\033[32m \033[05m 把服务器信息放在 ipmi.txt 文件内  流程是  先检测，后改密码 检测完成后把结果放到authpass.txt里面，修改密码会调取authpass文件进行改密码\033[0m"')
	print '\n\n'

	print " authpass.txt            认证通过的\n autherror.txt           认证没通过的 \n tryauthpass.txt         试图猜测密码成功的，这个信息也会写到authpass.txt里面 \n neterror.txt            网络不通的"	
	os.system('echo -e "\033[15m \033[36m 你打算做什么  \n 校验认证 \n 请输入: checkipmi    \n 修改密码  \n 请输入: modifypwd  \033[0m"')
	
	n=raw_input("\n :")
	if n=="checkipmi":
		touchfile()
		redata()
		networkagain()
	elif n=='modifypwd':
		print "正在进行改密码  "
	        os.system('mv password.txt password$(date +%F-%H-%M-%s).txt;touch password.txt')
        	os.system('rm -f passworderror.txt;touch passworderror.txt')
		modifydata()
		print "修改完了，信息放到了 password.txt 里面"
		print "修改密码失败的放在 passworderror.txt 里面"
		
	else:
		"输入错误，退出来了"
		exit
	
