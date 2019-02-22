#!/usr/bin/python

import time
import socket
import sys
import getopt
import threading
from time import gmtime, strftime
from comthread import comthread
from switchthread import switchthread
from goutthread import goutthread
from tftpthread import tftpthread

SWITCH_DOWN = '0'
SWITCH_RELEASE = '1'

idle_msg = 0
start_msg = 1
end_msg = 2

					
if __name__=='__main__':

	# if (len(sys.argv) < 3) or ((len(sys.argv) % 2) is 0):
	# 	sys.stdout.write('Invalid syntax. Refer to below\r\n')
	# 	sys.stdout.write('threadtest.py <web server ip 1> <WIZ145SR ip 1> [<web server ip 2> <WIZ145SR ip 1>...]\r\n)')
	# 	sys.exit(0)

	webserver_ips = []
	dst_ips = []

	file = open("config.txt", "r")
	str = file.readline()
	if "Number of Board" not in str:
		sys.stdout.write("'Number of Board' is missing\r\n")
		exit(1)
	param = str.split(":")
	sys.stdout.write("%s, %s\r\n" % (param[0], param[1]))

	for i in range(int(param[1].strip())):
		str = file.readline()
		if "WebServer IP" not in str:
			sys.stdout.write("'WebServer IP' is missing\r\n")
			exit(1)
		param = str.split(":")
		webserver_ips.append(param[1].strip())
		sys.stdout.write("%s, %s\r\n" % (param[0], param[1].strip()))
		
		str = file.readline()

		if "WIZ145SR IP" not in str:
			sys.stdout.write("'WIZ145SR IP' is missing\r\n")
			exit(1)
		param = str.split(":")
		dst_ips.append(param[1].strip())
		sys.stdout.write("%s, %s\r\n" % (param[0], param[1].strip()))

	str = file.readline()

	if "binary Filename" not in str:
		sys.stdout.write("'binary Filename' is missing\r\n")
		exit(1)
	param = str.split(":")
	sys.stdout.write("%s\r\n" % param[1].strip())

	str = file.readline()

	if "Finish Indicating String" not in str:
		sys.stdout.write("'Finish Indicating String' is missing\r\n")
		exit(1)
	param = str.split(":")
	sys.stdout.write("%s\r\n" % param[1].strip())

	# if (sys.version_info > (3, 0)):
	# 	num_bd = input("Number of Board: ")
	# 	for i in range(int(num_bd)):
	# 		webserver_ip = input("[%r]WebServer IP: " % i)
	# 		wiz145sr_ip = input("[%r]WIZ145SR IP: " % i)
	# 		webserver_ips.append(webserver_ip)
	# 		dst_ips.append(wiz145sr_ip)
	# else:
	# 	num_bd = raw_input("Number of Board: ")
	# 	for i in range(num_bd):
	# 		webserver_ip = raw_input("[%r]WebServer IP: " % i)
	# 		wiz145sr_ip = raw_input("[%r]WIZ145SR IP: " % i)
	# 		webserver_ips.append(webserver_ip)
	# 		dst_ips.append(wiz145sr_ip)

	sys.stdout.write("%r\r\n" % webserver_ips)
	sys.stdout.write("%r\r\n" % dst_ips)

	# for i in range(1,len(sys.argv)):
	# 	if (i % 2) == 1:
	# 		webserver_ips.append(sys.argv[i])
	# 	else:	
	# 		dst_ips.append(sys.argv[i])
	
	childnum = len(webserver_ips)	

	sw_threads = []
	gout_threads = []
	com_threads = []
	tftpth = tftpthread()
	
	for i in range(childnum):
		t = switchthread(webserver_ips[i])
		
		g = goutthread(webserver_ips[i])
		
		for j in range(4):
			c_th = comthread(4*i + j, dst_ips[i])
			t.neighbors.append(c_th)
			g.neighbors.append(c_th)
			tftpth.neighbors.append(c_th)
			c_th.start()

		t.start()
		sw_threads.append(t)	

		g.start()
		gout_threads.append(g)

	tftpth.start()
		
		
	while True:
		try:
			pass
			time.sleep(1)
		except KeyboardInterrupt:
			for i in range(childnum):
				
				for j in range(4):
					sw_threads[i].neighbors[j].stop()
					
				sw_threads[i].stop()
				gout_threads[i].stop()
			
			tftpth.stop()
			
			break
		
					