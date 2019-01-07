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

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

idle_msg = 0
keypressed_msg = 1
keyreleased_msg = 2
halt_msg = 3

POWER_ON = 1
POWER_OFF = 0
SWITCH_DOWN = '0'
SWITCH_RELEASE = '1'
LED_ON = 1
LED_OFF = 0

idle_state = 1
ready_state = 2
init_state = 3
menuselect_state = 4
flasherase_state = 5
localIP_state = 6
localIP2_state = 7
localIPDone_state = 8
serverIP_state = 9
serverIP2_state = 10
serverIPDone_state = 11
filename_state = 12
filenameDone_state = 13
done_state = 14
fail_state = 15
check_sw_1_state = 16
check_sw_2_state = 17
gout_1_state = 18
gout_2_state = 19
checkOrder_state = 20
tftpDone_state = 21
flashVerified_state = 22

SOCK_CLOSE_STATE = 1
SOCK_OPENTRY_STATE = 2
SOCK_OPEN_STATE = 3
SOCK_CONNECTTRY_STATE = 4
SOCK_CONNECT_STATE = 5

IsTimeout = 0

def timeoutfunc():
	global IsTimeout
	# sys.stdout.write('timer1 timeout\r\n')
	IsTimeout = 1

class comthread(threading.Thread):
	def __init__(self, id, dst_ip):
		threading.Thread.__init__(self)
		self.exitflag = False
		self.bank = 0
		self.id = id
		self.alive = True
		self.command = idle_msg
		self.dst_ip = dst_ip
		self.outputs = []
		self.is_request = False
		self.is_start = False
		self.timer1 = None
		
		if (id % 4) is 0:
			self.dst_port = 5001
			self.power_port = 0
			self.switch_port = 4
			self.redled_port = 8
			self.blueled_port = 9
		elif (id % 4) is 1:
			self.dst_port = 5002
			self.power_port = 1
			self.switch_port = 5
			self.redled_port = 10
			self.blueled_port = 11
		elif (id % 4) is 2:
			self.dst_port = 5003
			self.power_port = 3
			self.switch_port = 7
			self.redled_port = 14
			self.blueled_port = 15
		elif (id % 4) is 3:
			self.dst_port = 5004
			self.power_port = 2
			self.switch_port = 6
			self.redled_port = 12
			self.blueled_port = 13
			
		lastnumindex = dst_ip.rfind('.')
		lastnum = int(dst_ip[lastnumindex+1:len(dst_ip)])

		self.module_ip = dst_ip[:lastnumindex+1] + str(lastnum + id + 1) + "\r"
		# sys.stdout.write('module ip: %r\n' % self.module_ip)
		self.client = TCPClient(2, self.dst_ip, self.dst_port)
		
	def stop(self):
		sys.stdout.write('[ComThread %r] ' % self.id )
		sys.stdout.write('is shutdowning\r\n')
		if self.client is not None:
			self.client.close()

		if self.timer1 is not None:
			self.timer1.cancel()
		self.alive = False
		
	def run(self):
		sys.stdout.write('[ComThread %r] Hello\r\n' % self.id)
#		self.client.open()
		
		while self.alive:
			if self.client.state is SOCK_CLOSE_STATE:
				cur_state = self.client.state
				self.client.state = self.client.open()
#				if self.client.state != cur_state:
#					print(self.client.state) 
			
			elif self.client.state is SOCK_OPEN_STATE:
				cur_state = self.client.state
				self.client.state = self.client.connect()
#				if self.client.state != cur_state:
#					print(self.client.state) 
			
			elif self.client.state is SOCK_CONNECT_STATE:
				if self.client.working_state == idle_state:
					try:
						self.outputs.insert(0, [self.power_port, POWER_OFF, 'POWER OFF'])
#						sys.stdout.write('>')
						time.sleep(0.1)
						# check input switch value
						self.client.working_state = check_sw_1_state
						# logger.debug("Waiting SW%r input\r\n" % (switch_port -4))
					except :
						time.sleep(1)
		
				elif self.client.working_state == check_sw_1_state:
						if(self.command == keypressed_msg):
							sys.stdout.write('[ComThread %r] got key pressed message\r\n' % self.id)
							self.command = idle_msg
							self.client.working_state = check_sw_2_state
											
				elif self.client.working_state == check_sw_2_state:
					if(self.command == keyreleased_msg):
						sys.stdout.write('[ComThread %r] got keyreleased message\r\n' % self.id)
						self.command = idle_msg
						self.client.working_state = ready_state

				elif self.client.working_state == ready_state:
					try:
						self.outputs.insert(0, [self.redled_port, LED_OFF, 'RED LED OFF'])
						self.outputs.insert(0, [self.blueled_port, LED_OFF, 'BLUE LED OFF'])
						self.outputs.insert(0, [self.power_port, POWER_ON, 'POWER ON'])
						self.outputs.insert(0, [self.redled_port, LED_ON, 'RED LED ON'])
						self.outputs.insert(0, [self.redled_port, LED_OFF, 'RED LED OFF'])
						
							
						self.client.working_state = gout_1_state
						sys.stdout.write('timer1 start\r\n')
						self.timer1 = threading.Timer(10.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
					except Exception as e:
						sys.stdout.write('%r\r\n' % e)
						sys.stdout.write('timer1 stop\r\n')
						self.timer1.cancel()
						time.sleep(1)
			
				elif self.client.working_state == gout_1_state:
					if(len(self.outputs) == 0):
						self.client.working_state = init_state
						sys.stdout.write('\r\ninit_state\r\n')
					else:
						time.sleep(0.5)
					
					if IsTimeout is 1:
						# self.timer1.cancel()
						self.client.outputs.remove()
						self.client.working_state = idle_state
							
				elif self.client.working_state == init_state:					
					response = self.client.readline()
					# logger.debug("[init_state] [%r] %r" % (len(response), response))
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						if ("9: Load Boot Loader code then write to Flash via TFTP." in response) :
							self.client.write("2")
							# print 'timer1 stop'
							self.timer1.cancel()
							self.client.working_state = menuselect_state

							sys.stdout.write('\r\nmenuselect_state\r\n')
							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()
					response = ""
				
					if IsTimeout is 1:
						sys.stdout.write("init_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == menuselect_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						if ("Warning!! Erase Linux in Flash then burn new one. Are you sure?(Y/N)" in response) :
							self.client.write("Y")

							self.timer1.cancel()
							self.client.working_state = flasherase_state
							# sys.stdout.write('\r\nflasherase_state\r\n')

							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()
						elif ("3: System Boot system code via Flash" in response):
							self.timer1.cancel()
							self.client.working_state = fail_state
							sys.stdout.write('\r\nfail_state\r\n')

							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()

					response = ""
				
					if IsTimeout is 1:
						sys.stdout.write("menuselect_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == flasherase_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						if ("Input device IP (10.10.10.123)" in response) :
							for i in range(12):
								self.client.write("\b \b")
								time.sleep(0.1)
							self.timer1.cancel()
							self.client.working_state = localIP_state				
							# sys.stdout.write('\r\nlocalIP_state\r\n')
							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()
						response = ""
			
					if IsTimeout is 1:
						sys.stdout.write("flasherase_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == localIP_state:
	
					response = self.client.readline()
					if (response != "") :
						sys.stdout.write(response)
						# sys.stdout.flush()
						response = ""
						self.timer1.cancel()
						self.client.write(self.module_ip)
						self.client.working_state = localIP2_state
						# sys.stdout.write('\r\nlocalIP2_state\r\n')
					
						self.timer1 = threading.Timer(3.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
						response = ""
				
					if IsTimeout is 1:
						sys.stdout.write("localIP_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == localIP2_state:
	
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
					
						self.timer1.cancel()
						self.client.working_state = localIPDone_state
						# sys.stdout.write('\r\nlocalIPDone_state\r\n')
						self.timer1 = threading.Timer(3.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
				
						response = ""

					if IsTimeout is 1:
						sys.stdout.write("localIP2_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == localIPDone_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						if ("Input server IP (10.10.10.3)" in response) :
							for i in range(10):
								self.client.write("\b \b")
								time.sleep(0.1)
						
							self.timer1.cancel()
							self.client.working_state = serverIP_state
							# sys.stdout.write('\r\nserverIP_state\r\n')
							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()
					
						response = ""
	
					if IsTimeout is 1:
						sys.stdout.write("localIPDone_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == serverIP_state:
			
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()

						self.client.write("192.168.10.212\r")
						# self.client.write("192.168.10.235\r")
						self.timer1.cancel()
						self.client.working_state = serverIP2_state
						# sys.stdout.write('\r\nserverIP2_state\r\n')
						self.timer1 = threading.Timer(3.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
						response = ""

					if IsTimeout is 1:
						sys.stdout.write("serverIP_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')
					
				elif self.client.working_state == serverIP2_state:
			
					response = self.client.readline()

					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						self.timer1.cancel()
						self.client.working_state = checkOrder_state
						sys.stdout.write('\r\ncheckOrder_state\r\n')
						self.timer1 = threading.Timer(30.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
						
						response = ""

					if IsTimeout is 1:
						sys.stdout.write("serverIP2_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						# sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == checkOrder_state:
					if self.is_request is False:
						self.is_request = True
					else :
						if self.is_start is True:
							self.timer1.cancel()
							self.client.working_state = serverIPDone_state
							# sys.stdout.write('\r\nserverIPDone_state\r\n')

					if IsTimeout is 1:
						sys.stdout.write("checkOrder_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						self.is_request = False
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == serverIPDone_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						if ("Input Linux Kernel filename ()" in response) :
							self.client.write("std.bin\r")
							self.client.working_state = filename_state
							# sys.stdout.write('\r\nfilename_state\r\n')

						response = ""
			
				elif self.client.working_state == filename_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						# sys.stdout.flush()
						# self.timer1.cancel()
						self.client.working_state = filenameDone_state	
						# sys.stdout.write('\r\nfilenameDone_state\r\n')
						# self.timer1 = threading.Timer(30.0, timeoutfunc)
						# IsTimeout = 0
						# self.timer1.start()
					response = ""
	
					# if IsTimeout is 1:
					# 	sys.stdout.write("filename_state timeout")
					# 	self.timer1.cancel()
					# 	self.client.working_state = fail_state
					# 	sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == filenameDone_state:
					ch = self.client.read()
					if(ch != ''):
						self.client.str_list.append(ch)
						sys.stdout.write("%c" % ch)
						# sys.stdout.flush()
			
						if(ch == '\r'):
							response = ''.join(self.client.str_list)
							# sys.stdout.write('[%r-%r]' % (self.bank, self.id))
							del self.client.str_list[:]
							if("done" in response):
								# self.timer1.cancel()
								self.client.working_state = tftpDone_state
								# sys.stdout.write('\r\ntftpDone_state\r\n')
								self.is_request = False
								self.is_start = False
								# self.timer1 = threading.Timer(30.0, timeoutfunc)
								# IsTimeout = 0
								# self.timer1.start()
							elif ("Retry count exceeded; starting again" in response) :
								self.client.retrycount += 1
								# logger.debug("retrycount: %r\r\n" % self.client.retrycount)
								if(self.client.retrycount >= 10):
									self.client.retrycount = 0
									self.client.working_state = fail_state
									sys.stdout.write('\r\nfail_state\r\n')

							response = ""
					# if IsTimeout is 1:
					# 	sys.stdout.write("filenameDone_state timeout")
					# 	self.timer1.cancel()
					# 	self.client.working_state = fail_state
					# 	sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == tftpDone_state:
					ch = self.client.read()
					if(ch != ''):
						self.client.str_list.append(ch)
						# if(ch is '#'):
						# 	sys.stdout.write("%c" % ch)
						# 	sys.stdout.flush()
			
						if(ch == '\r'):
							response = ''.join(self.client.str_list)
							# sys.stdout.write(response)
							sys.stdout.write('%r' % self.id)
							del self.client.str_list[:]
							if ("Verifying Checksum ... Bad Data CRC" in response) :
								# self.timer1.cancel()
								sys.stdout.write('Flashing Failed. Bad CRC\r\n')
								self.client.write("\r\n\r\n")
								self.client.working_state = fail_state
								sys.stdout.write('\r\fail_state\r\n')
								# self.is_start = False
								# self.is_request = False
								# self.timer1 = threading.Timer(10.0, timeoutfunc)
								# IsTimeout = 0
								# self.timer1.start()
							elif ("Verifying Checksum ... OK" in response) :
								self.client.working_state = flashVerified_state
								sys.stdout.write('\r\nflashverified_state\r\n')
							
							response = ""

				elif self.client.working_state == flashVerified_state:
					ch = self.client.read()
					if(ch != ''):
						self.client.str_list.append(ch)
						# if(ch is '#'):
						# 	sys.stdout.write("%c" % ch)
						# 	sys.stdout.flush()
			
						if(ch == '\r'):
							response = ''.join(self.client.str_list)
							# sys.stdout.write(response)
							sys.stdout.write('%r' % self.id)
							del self.client.str_list[:]
							if ("Please press Enter to activate this console." in response) :
								# self.timer1.cancel()
								sys.stdout.write('enter CRLF \r\n')
								self.client.write("\r\n\r\n")
								self.client.working_state = done_state
								sys.stdout.write('\r\done_state\r\n')
								# self.is_start = False
								# self.is_request = False
								# self.timer1 = threading.Timer(10.0, timeoutfunc)
								# IsTimeout = 0
								# self.timer1.start()
							elif ("failsafe button BTN_1 was pressed" in response) :
								self.client.working_state = done_state
								sys.stdout.write('\r\ndone_state\r\n')
							
							response = ""
			
				elif self.client.working_state == done_state:
					response = self.client.readline()
					if(response != ""):
						sys.stdout.write(response)
						if ("root@" in response) : #Standard
						# if ("IPS-231-0000 login:" in response) : #SOS intelliport
							sys.stdout.write(response)
							sys.stdout.write("\r\n")
							sys.stdout.flush()
							self.client.write("\r")
							sys.stdout.write("===============================================\n")
							sys.stdout.write(" Bank %r, ID %r Firmware Update Succeeded!!!\n" % (self.bank, self.id))
							sys.stdout.write("===============================================\n")
							sys.stdout.flush()
							# BLUELED ON (HIGH)
							
							# self.timer1.cancel()
							self.outputs.insert(0, [self.blueled_port, LED_ON, 'BLUE LED ON'])
							self.outputs.insert(0, [self.power_port, POWER_OFF, 'POWER OFF'])
									
							self.client.working_state = gout_2_state
							sys.stdout.write('\r\ngout_2_state\r\n')
						elif ("Please press Enter to activate this console." in response) :
							self.client.write("\r\n\r\n")
						else:
							self.client.write("\r\n")
                                                
                                                        
						response = ""
							
					# if IsTimeout is 1:
					# 	sys.stdout.write("done_state timeout")
					# 	self.timer1.cancel()
					# 	self.client.working_state = fail_state
					# 	sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == fail_state:
					self.outputs.insert(0, [self.redled_port, LED_ON, 'RED LED ON'])
					self.outputs.insert(0, [self.power_port, POWER_OFF, 'POWER OFF'])
					self.client.working_state = gout_2_state
					sys.stdout.write('\r\ngout_2_state\r\n')
			
				elif self.client.working_state == gout_2_state:
					if(len(self.outputs) == 0):
						logger.debug("You can remove a module on bank%r now\r\n" % self.id)						
						self.client.working_state = idle_state
						sys.stdout.write('\r\nidle_state\r\n')

		
		sys.stdout.write('[ComThread %r] Bye! \r\n' % self.id)
		self.client.close()
