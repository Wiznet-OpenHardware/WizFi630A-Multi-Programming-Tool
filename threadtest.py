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

	if (len(sys.argv) < 3) or ((len(sys.argv) % 2) is 0):
		sys.stdout.write('Invalid syntax. Refer to below\r\n')
		sys.stdout.write('threadtest.py <web server ip 1> <WIZ145SR ip 1> [<web server ip 2> <WIZ145SR ip 1>...]\r\n)')
		sys.exit(0)

	webserver_ips = []
	dst_ips = []

	for i in range(1,len(sys.argv)):
		if (i % 2) == 1:
			webserver_ips.append(sys.argv[i])
		else:	
			dst_ips.append(sys.argv[i])
#		print(sys.argv[i])
	
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
		
	
#	for i in range(childnum*4):
#		com_threads[i].start()

		
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
		
					