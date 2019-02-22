#!/usr/bin/python


import sys
sys.path.append('./TCPClient/')
sys.path.append('./WIZ550WebClient/')
import time
import socket
import getopt
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

class switchthread(threading.Thread):
	
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
		sys.stdout.write('[KeyInCheckThread %r] Hello\r\n' % self.id)
		
		while self.alive:
			value = self.webclient.getGINstateall()
			for i in range(4):
				if(self.webclient.inputs[self.channels[i]] == SWITCH_DOWN):
					if(self.channelstates[i] == SWITCH_RELEASE):
						sys.stdout.write('Switch[%r] pressed down\r\n' % self.channels[i])
						self.channelstates[i] = SWITCH_DOWN
						self.neighbors[i].command = start_msg
				else:			
					if(self.channelstates[i] == SWITCH_DOWN):
						sys.stdout.write('Switch[%r] released up\r\n' % self.channels[i])
						self.channelstates[i] = SWITCH_RELEASE
						self.neighbors[i].command = end_msg
			time.sleep(0.5)
			

		sys.stdout.write('[KeyInCheckThread %r] Bye! \r\n' % self.id)
