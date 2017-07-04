#!/usr/bin/python


import sys
sys.path.append('./TCPClient/')
sys.path.append('./WIZ550WebClient/')
import getopt
import time
import socket
import threading
from TCPClient import TCPClient
from time import gmtime, strftime
from WIZ550WebClient import WIZ550WebClient
from comthread import comthread

SWITCH_DOWN = '0'
SWITCH_RELEASE = '1'

idle_msg = 0
start_msg = 1
end_msg = 2

class goutthread(threading.Thread):
	
	def __init__(self, webserver_ip):
		threading.Thread.__init__(self)
		self.id = 0
		self.neighbors = []
		self.alive = True
		self.webserver_ip = webserver_ip
		self.webclient = WIZ550WebClient(self.webserver_ip)
		self.channels = [4, 5, 7, 6]
		self.channelstates = [SWITCH_RELEASE, SWITCH_RELEASE, SWITCH_RELEASE, SWITCH_RELEASE]
	
	def stop(self):
		self.alive = False
		
	def run(self):			
		sys.stdout.write('[GOutThread %r] Hello\r\n' % self.id)
		
		while self.alive:
			if(len(self.neighbors) > 0):
				for i in range(4):
					outputs_len = len(self.neighbors[i].outputs)
					if outputs_len > 0:
						# get first item from list and its data is another list which consists of portnum and value
#						sys.stdout.write('len of outputs queue is %r\r\n' % outputs_len)
						item = self.neighbors[i].outputs.pop()
						sys.stdout.write('%r\r\n' % item)
						portnum = item[0]
						val = item[1]
						msg = item[2]
						sys.stdout.write("[%s]bank%d : %s\r\n" % (self.webserver_ip, i, msg))
						self.webclient.setGOUTvalue(portnum, val)

						time.sleep(0.5)

		sys.stdout.write('[GOutThread %r] Bye! \r\n' % self.id)
