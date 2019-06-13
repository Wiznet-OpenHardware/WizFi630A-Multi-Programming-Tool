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
#daniel
mac_check_1_state = 22
mac_check_2_state = 23
mac_check_3_state = 24
mac_check_4_state = 25
mac_check_5_state = 26

flashVerified_state = 27

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
	# def __init__(self, id, dst_ip):
	def __init__(self, id, dst_ip, steps):
    		
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
		#daniel
		self.steps = steps
		self.readableMacaddr = []
		
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
							sys.stdout.write('[ComThread] got key pressed message ----------[%r] \r\n' % self.id)
							self.command = idle_msg
							self.client.working_state = check_sw_2_state
											
				elif self.client.working_state == check_sw_2_state:
					if(self.command == keyreleased_msg):
						# sys.stdout.write('[ComThread %r] got keyreleased message\r\n' % self.id)
						self.command = idle_msg
						self.client.working_state = ready_state

				elif self.client.working_state == ready_state:
					try:
						self.outputs.insert(0, [self.redled_port, LED_OFF, 'RED LED OFF'])
						self.outputs.insert(0, [self.blueled_port, LED_OFF, 'BLUE LED OFF'])
						self.outputs.insert(0, [self.power_port, POWER_ON, 'POWER ON']) #power
						self.outputs.insert(0, [self.redled_port, LED_ON, 'RED LED ON']) #reset pin
						self.outputs.insert(0, [self.redled_port, LED_OFF, 'RED LED OFF'])
						
							
						self.client.working_state = gout_1_state
						# sys.stdout.write('timer1 start\r\n')
						self.timer1 = threading.Timer(10.0, timeoutfunc)
						IsTimeout = 0
						self.timer1.start()
					except Exception as e:
						sys.stdout.write('%r\r\n' % e)
						# sys.stdout.write('timer1 stop\r\n')
						self.timer1.cancel()
						time.sleep(1)
			
				elif self.client.working_state == gout_1_state:
					if(len(self.outputs) == 0):
						self.client.working_state = mac_check_1_state
						self.timer1.cancel()
						# sys.stdout.write('\r\ninit_state\r\n')
					else:
						time.sleep(0.5)
					
					if IsTimeout is 1:
						# self.timer1.cancel()
						self.client.outputs.remove()
						self.client.working_state = idle_state
#start daniel
				elif self.client.working_state == mac_check_1_state:
					if( "MACCHECK" in self.steps):
						response = self.client.readline()
						# logger.debug("[mac_check_1_state] [%r] %r" % (len(response), response))
						if(response != ""):
							# sys.stdout.write(response)
							# sys.stdout.flush()
							if ("9: Load Boot Loader code then write to Flash via TFTP." in response) :
								self.client.write('4')

								self.timer1.cancel()
								self.client.working_state = mac_check_2_state

								# sys.stdout.write('\r\nmac_check_2_state\r\n')
								self.timer1 = threading.Timer(3.0, timeoutfunc)
								# sys.stdout.write('timer1 start in mac_check_1_state')
								self.timer1.start()
								IsTimeout = 0

						response = ""

						# if IsTimeout is 1:
						# 	sys.stdout.write("mac_check_1_state timeout")
						# 	self.client.working_state = fail_state
						# 	sys.stdout.write('\r\nfail_state\r\n')
					else:
						self.client.working_state = done_state

				elif self.client.working_state == mac_check_2_state:
					response = self.client.readline()
				
					if(response != ""):
						# sys.stdout.write(response)
						# sys.stdout.flush()

						if ("WizFi630A # " in response) :
							self.client.write("printenv ethaddr\r\n")
							self.client.working_state = mac_check_3_state
							self.timer1.cancel()
							# sys.stdout.write('timer1 cancel in if clause in mac_check_2_state')
							# sys.stdout.write('\r\mac_check_2_state\r\n')

							self.timer1 = threading.Timer(5.0, timeoutfunc)
							self.timer1.start()
							IsTimeout = 0
							# sys.stdout.write('timer1 start in if clause in mac_check_2_state')

						elif ("Starting kernel" in response):
							self.timer1.cancel()
							self.client.working_state = fail_state
							sys.stdout.write('\r\nfail_state\r\n')

   
						response = ""
			
					if IsTimeout is 1:
						sys.stdout.write("\r\nmac_check_2_state timeout\r\n")
						sys.stdout.write('\r\nfail_state\r\n')
						sys.stdout.flush()
						self.client.working_state = fail_state

				elif self.client.working_state == mac_check_3_state:
					response = self.client.readline()
					# sys.stdout.write(response)
					# sys.stdout.flush()
					if("ethaddr=" in response):
						# sys.stdout.write(response)
						# sys.stdout.flush()
						if("00:08:DC" in response):
							self.client.working_state = mac_check_4_state
							# sys.stdout.write(response)
							# sys.stdout.write("\r\nIt is correct WIZnet MAC address\r\n")
							# self.readableMacaddr.insert(0, [self.power_port, response.split('=')[1]])
							# print(type(response), str(response))

							# print(type(response.split('=')[1]), response.split('=')[1])
							self.readableMacaddr.append(str(response.split('=')[1].split('\n')[0]))

							self.timer1.cancel()
							self.timer1 = threading.Timer(3.0, timeoutfunc)
							IsTimeout = 0
							self.timer1.start()
						else:
							sys.stdout.write("\r\nIt is not WIZnet MAC address (%s)\r\n" % response )
							# sys.stdout.write("mac_check_2_state timeout")
							self.timer1.cancel()
							self.client.working_state = fail_state
							# sys.stdout.write('\r\nfail_state\r\n')
							
					response = ""

					if IsTimeout is 1:
						sys.stdout.write("\r\nIt is not WIZnet MAC address\r\n")
						# sys.stdout.write("mac_check_2_state timeout")
						self.timer1.cancel()
						self.client.working_state = fail_state
						sys.stdout.write('\r\nfail_state\r\n')

				elif self.client.working_state == mac_check_4_state:
					try:
						self.outputs.insert(0, [self.blueled_port, LED_ON, 'BLUE LED ON'])
						self.outputs.insert(0, [self.redled_port, LED_ON, 'RED LED ON'])
						self.outputs.insert(0, [self.power_port, POWER_OFF, 'POWER OFF'])
						

						self.client.working_state = gout_2_state
					except Exception as e:
						sys.stdout.write('%r\r\n' % e)
						sys.stdout.write('timer1 stop\r\n')

				elif self.client.working_state == fail_state:
					self.outputs.insert(0, [self.redled_port, LED_ON, 'RED LED ON'])
					self.outputs.insert(0, [self.power_port, POWER_OFF, 'POWER OFF'])
					self.client.working_state = gout_2_state
					# sys.stdout.write('\r\ngout_2_state\r\n')

				elif self.client.working_state == gout_2_state:
					if(len(self.outputs) == 0):
						sys.stdout.write("You can remove a module on bank%r now ------[%r]\r\n" % (self.id,self.id))
						self.client.working_state = idle_state
						# sys.stdout.write('\r\nidle_state\r\n')

		
		sys.stdout.write('[ComThread %r] Bye! \r\n' % self.id)
		self.client.close()
