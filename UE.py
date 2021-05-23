# UE Module: classes related to the terminal

import os
import sys
import random
import simpy #from SimPy.Simulation import * (Simpy2.2)
from cell import Format
from collections import deque

# UE class: terminal description

class UE():
	def __init__(self, i,ue_sinr0,p,npM):
		self.id = i
		self.state = 'RRC-IDLE'
		self.packetFlows = []
		self.bearers = []
		self.radioLinks = RadioLink(1,ue_sinr0,self.id)
		self.TBid = 1
		# self.accessRetry = 0
		# self.accessFailMax = 2
		self.pendingPckts = {}
		self.prbs = p
		self.resUse = 0
		self.pendingTB = []
		self.bler = 0
		self.tbsz = 1
		self.MCS = 0
		self.pfFactor = 1 # PF Scheduler
		self.pastTbsz = deque([1]) # PF Scheduler
		self.lastDen = 0.001 # PF Scheduler
		self.num = 0 # PF Scheduler
		self.BWPs = npM
		self.TXedTB = 0
		self.lostTB = 0
		self.symb = 0

#------------------------------------------------ lists mng

	def addPacketFlow(self,pckFl):
		self.packetFlows.append(pckFl)

	def addBearer(self,br):
		self.bearers.append(br)

#-----------------------------------------------

	def receivePckt(self,env,c): # PEM -------------------------------------------

		while True:

			if len(self.packetFlows[0].appBuff.pckts)>0:
				if self.state == 'RRC-IDLE': # Not connected
					if c.controlAccess(self): # cell can give resources
						self.connect(c)
						nextPackTime = c.tUdQueue
						yield env.timeout(nextPackTime) #yield hold, self, nextPackTime (Simpy2.2)
						if nextPackTime > c.inactTimer:
							self.releaseConnection(c)
					else: # cell can't give resources
						self.connRej()
						yield env.timeout(10) #yield hold, self, 10  (Simpy2.2) # Should be 10, for RACH
				else: # Already connecter user
					if c.congestionControl(self):
						self.queueDataPckt(c)
						nextPackTime = c.tUdQueue
						yield env.timeout(nextPackTime) #yield hold, self, nextPackTime (Simpy2.2)
						if nextPackTime > c.inactTimer:
							self.releaseConnection(c)
					else:
						self.connRej()
						self.releaseConnection(c)
						nextPackTime = c.tUdQueue
						yield env.timeout(nextPackTime) #yield hold, self, nextPackTime (Simpy2.2)
			else:
				nextPackTime = c.tUdQueue
				yield env.timeout(nextPackTime) #yield hold, self, nextPackTime (Simpy2.2)

	def connRej(self):
		print (str(self.id)+ ' Connection rejected')
		pD = self.packetFlows[0].appBuff.removePckt()
		if (now()-pD.tIn) > 30:
			pcktN = pD.secNum
			print (str(self.id)+'packet '+str(pcktN)+' lost .....'+str(pD.twait))
			self.packetFlows[0].lostPackets = self.packetFlows[0].lostPackets + 1
		else:
			self.packetFlows[0].appBuff.insertPcktLeft(pD)


	def connect(self,cl):
		bD = Bearer(1,9,self.packetFlows[0].type)
		self.addBearer(bD)
		self.queueDataPckt(cl)
		if self.packetFlows[0].type == 'DL':
			if (list(cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues.keys()).count(self.id))<1:
				cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues[self.id] = self
		else:
			if (list(cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues.keys()).count(self.id))<1:
				cl.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues[self.id] = self
		self.state = 'RRC-CONNECTED'


	def queueDataPckt(self,cell):
		pD = self.packetFlows[0].appBuff.removePckt()
		buffSizeAllUEs = 0
		buffSizeThisUE = 0
		if self.packetFlows[0].type == 'DL':
			for ue in list(cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues.keys()):
				buffSizeUE = 0
				for p in cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.ues[ue].bearers[0].buffer.pckts:
					buffSizeUE = buffSizeUE + p.size
				if self.id == ue:
					buffSizeThisUE = buffSizeUE
				buffSizeAllUEs = buffSizeAllUEs + buffSizeUE
		else:
			for ue in list(cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues.keys()):
				buffSizeUE = 0
				for p in cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.ues[ue].bearers[0].buffer.pckts:
					buffSizeUE = buffSizeUE + p.size
				if self.id == ue:
					buffSizeThisUE = buffSizeUE
				buffSizeAllUEs = buffSizeAllUEs + buffSizeUE

		if buffSizeThisUE<cell.maxBuffUE:#len(self.bearers[1].buffer.pckts)<cell.maxBuffUE:
			self.bearers[0].buffer.insertPckt(pD)
		else:
			pcktN = pD.secNum
			#print (Format.CRED+Format.CBOLD+self.id,'packet ',pcktN,' lost .....',str(pD.tIn)+Format.CEND)
			if self.packetFlows[0].type == 'DL':
				cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerDL.printDebDataDM('<p style="color:red"><b>'+str(self.id)+' packet '+str(pcktN)+' lost .....'+str(pD.tIn)+'</b></p>')
			else:
				cell.interSliceSched.slices[self.packetFlows[0].sliceName].schedulerUL.printDebDataDM('<p style="color:red"><b>'+str(self.id)+' packet '+str(pcktN)+' lost .....'+str(pD.tIn)+'</b></p>')
			self.packetFlows[0].lostPackets = self.packetFlows[0].lostPackets + 1

	def releaseConnection(self,cl):
		self.state = 'RRC-IDLE'
		self.bearers = []
		# Cleaning actions?

# ------------------------------------------------

# PacketFlow class: PacketFlow description

class PacketFlow():
	def __init__(self,i,pckSize,pckArrRate,u,tp,slc):
		self.id = i
		self.tMed = 0
		self.sMed = 0
		self.type = tp
		self.sliceName = slc
		self.pckArrivalRate = pckArrRate
		self.qosFlowId = 0
		self.packetSize = pckSize
		self.ue = u
		self.sMax = (float(self.packetSize)/350)*600
		self.tMax = (float(self.pckArrivalRate)/6)*12.5
		self.tStart = 0
		self.appBuff = PcktQueue()
		self.lostPackets = 0
		self.sentPackets = 0
		self.rcvdBytes = 0
		self.pId = 1
		self.header = 30
		self.meassuredKPI = {'Throughput':0,'Delay':0,'PacketLossRate':0}


	def setQosFId(self,q):
		qosFlowId = q

	def queueAppPckt(self,env,tSim): # --- PEM -----
		#i = 1
		ueN = int(self.ue[2:]) # number of UEs in simulation
		self.tStart = (random.expovariate(1.0))
		yield env.timeout(self.tStart) 	#yield hold, self, self.tStart (Simpy2.2)  # each UE start transmission after tStart
		while env.now<(tSim*0.83):
			self.sentPackets = self.sentPackets + 1
			size = self.getPsize()
			pD = Packet(self.pId,size+self.header,self.qosFlowId,self.ue)
			self.pId = self.pId + 1
			pD.tIn = env.now
			self.appBuff.insertPckt(pD)
			nextPackTime = self.getParrRate()
			yield env.timeout(nextPackTime) #yield hold, self, nextPackTime (Simpy2.2)

	def getPsize(self):
		pSize = random.paretovariate(1.2)*(self.packetSize*(0.2/1.2))
		while pSize > self.sMax:
			pSize = random.paretovariate(1.2)*(self.packetSize*(0.2/1.2))
		self.sMed = self.sMed + pSize
		return pSize

	def getParrRate(self):
		pArrRate = random.paretovariate(1.2)*(self.pckArrivalRate*(0.2/1.2))
		while pArrRate > self.tMax:
			pArrRate = random.paretovariate(1.2)*(self.pckArrivalRate*(0.2/1.2))
		self.tMed = self.tMed + pArrRate
		return pArrRate

	def setMeassures(self,tsim):
		#print Format.CBLUE+'Lost packets: '+str(self.lostPackets),'Sent packets: '+str(self.sentPackets) + Format.CEND
		self.meassuredKPI['PacketLossRate'] = float(100*self.lostPackets)/self.sentPackets
		if tsim>1000:
			self.meassuredKPI['Throughput'] = (float(self.rcvdBytes)*8000)/(0.83*tsim*1024*1024)
		else:
			self.meassuredKPI['Throughput'] = 0

class Packet:
	def __init__(self,sn,s,qfi,u):
		self.secNum = sn
		self.size = s
		self.qosFlowId = qfi
		self.ue = u
		self.tIn = 0

	def printPacket(self):
		print (Format.CYELLOW + Format.CBOLD + self.ue+ '+packet '+str(self.secNum)+' arrives at t ='+str(now()) + Format.CEND)

class Bearer:
	def __init__(self,i,q,tp):
		self.id = i
		self.qci = q
		self.type = tp
		self.buffer = PcktQueue()

class PcktQueue:
    def __init__(self):
        self.pckts = deque([])

    def insertPckt(self,p):
        self.pckts.append(p)

    def insertPcktLeft(self,p):
        self.pckts.appendleft(p)

    def removePckt(self):
        if len(self.pckts)>0:
            return self.pckts.popleft()

class RadioLink():
	def __init__(self,i,lq_0,u):
		self.id = i
		state = 'ON'
		self.linkQuality = lq_0
		self.ue = u
		self.lqAv = 0
		self.totCount = 0
		self.maxVar = 0.1

	def updateLQ(self,env,udIntrv,tSim,fl,u,r):
		if fl: # load SINR from lena DlRsrpSinrStats.txt ststs file
			sizeFile = int(u*float(tSim)/udIntrv)
			with open(r+'DlRsrpSinrStats.txt') as s:
				lines = s.readlines()
				line_i = 1
				time = 0
				while time*1000<tSim:
					lqMed = 0
					count = 0
					short_time = 0
					ref_time = time
					while short_time*1000<udIntrv and line_i<len(lines):
						columns = lines[line_i].split("\t",7)
						time = float(columns[0])
						imsi = columns[2]
						line_i = line_i + 1
						short_time = time - ref_time
						if imsi==self.ue[2:]:
							lqMed = lqMed + float(columns[5])
							self.lqAv = self.lqAv + float(columns[5])
							count = count + 1
							self.totCount = self.totCount + 1
					if count>0:
						self.linkQuality = float(lqMed)/(count)
					yield env.timeout(udIntrv) #yield hold, self, udIntrv (Simpy2.2)

		else: # vary SINR with normal distribution
			while env.now<(tSim*0.83): #while now()<(tSim*0.83): (Simpy2.2)
				yield env.timeout(udIntrv) #yield hold, self, udIntrv (Simpy2.2)
				deltaSINR = random.normalvariate(0, self.maxVar)
				while deltaSINR > self.maxVar or deltaSINR<(0-self.maxVar):
					deltaSINR = random.normalvariate(0, self.maxVar)
				self.linkQuality = self.linkQuality + deltaSINR
