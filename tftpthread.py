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

class tftpthread(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.neighbors = []
		self.alive = True
	
	def stop(self):
		self.alive = False
		
	def run(self):			
		sys.stdout.write('[TFTPThread] Hello\r\n')
		
		while self.alive:
			if(len(self.neighbors) > 0):
				for i in range(len(self.neighbors)):
					if(self.neighbors[i].is_request) :
						if(self.neighbors[i].is_start is False):
							self.neighbors[i].is_start = True
							sys.stdout.write('[%r] got a ticket\r\n' % i)
							while(self.neighbors[i].is_start):
								time.sleep(0.5)
				

		sys.stdout.write('[TFTPThread] Bye! \r\n')
