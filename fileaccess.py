#!/usr/bin/python


import sys
import time
sys.path.append('./TCPClient/')
sys.path.append('./WIZ550WebClient/')
import threading
import csv
from comthread import comthread

SWITCH_DOWN = '0'
SWITCH_RELEASE = '1'

idle_msg = 0
start_msg = 1
end_msg = 2

filename = "WizFi630A_MACADDRESS.csv"
today = ''.join(time.strftime("%Y-%m-%d"))


class fileAccess(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.neighbors = []
        self.readableMacaddr = []
        self.MacAddrList = {}
        self.alive = True

    def readFile(self):
        with open(filename, "a+") as inFile:
            reader = csv.reader(inFile, delimiter='\t')
            for row in reader:
                # self.MacAddrList.append(row)
                self.MacAddrList.update({row[0] : row[1:]})
        sys.stdout.write('[File Access Thread] File Read done\r\n')
        sys.stdout.write("[File Access Thread] Read (%d) MACs in the (%s)\r\n" % (len(self.MacAddrList), filename))


    def writeFile(self):
        if(len(self.MacAddrList)>0):
            with open(filename, "w+") as inFile:
                writer = csv.writer(inFile, delimiter='\t', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

                for key in self.MacAddrList.keys():
                    list_to_str = ', '.join(self.MacAddrList[key])
                    listedMacaddr = []
                    listedMacaddr.extend([key, list_to_str])
                    writer.writerow(listedMacaddr)
  

        sys.stdout.write('[File Access Thread] File Write done\r\n')
        sys.stdout.write("[File Access Thread] Write (%d) MACs in the (%s)\r\n" % (len(self.MacAddrList), filename))

    def checkDuplicated(self, mac):

        if mac in self.MacAddrList.keys():
            return True
        else:
            return False

    def stop(self):
        self.writeFile()
        self.alive = False

    def run(self):
        sys.stdout.write('[File Access Thread] Hello\r\n')

        self.readFile()

        while self.alive:
            if (len(self.neighbors) > 0):
                for i in range(len(self.neighbors)):
                    outputs_len = len(self.neighbors[i].readableMacaddr)
                    if outputs_len > 0:
                        mac = self.neighbors[i].readableMacaddr.pop()
                        
                        if self.checkDuplicated(mac) == False:
                            # self.MacAddrList[mac] = today
                            self.MacAddrList.update({mac: [today]})
                            sys.stdout.write("[File Access Thread] Add MAC (%s) to the (%s)\r\n" % (mac, filename))
                        else:
                            saved_ts = []
                            saved_ts.extend(self.MacAddrList[mac])
                            saved_ts.append(today)
                            self.MacAddrList.update({mac: saved_ts})
                            sys.stdout.write("[File Access Thread] Duplicated MAC (%s) in the (%s) <--- Duplicated!!\r\n" % (mac, filename))

        # self.writeFile()

        # for test
        # while self.alive:
        # # for i in range(len(self.readableMacaddr)):
        #     if(len(self.readableMacaddr) > 0):
        #         mac = self.readableMacaddr.pop()
        #
        #         if self.checkDuplicated(mac) == False:
        #             self.MacAddrList.update({mac : [today]})
        #             sys.stdout.write("[File Access Thread] Add MAC (%s) to the (%s)\r\n" % (mac, filename))
        #         else:
        #             saved_ts = []
        #             saved_ts.extend(self.MacAddrList[mac])
        #             saved_ts.append(today)
        #             self.MacAddrList.update({mac: saved_ts})
        #             sys.stdout.write("[File Access Thread] Duplicated MAC (%s) in the (%s)\r\n" % (mac, filename))


        sys.stdout.write('[File Access Thread] Bye!\r\n')
