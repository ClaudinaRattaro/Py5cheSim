""" This module contains the UE, Packet Flow, Packet, PcktQueue, Bearer and RadioLink clases.
This clases are oriented to describe UE traffic profile, and UE relative concepts
"""
import os
import sys
import random
import simpy
from collections import deque

# UE class: terminal description

class UE():
	""" This class is used to model UE behabiour and relative properties """
	def __init__(self, i,ue_sinr0,p,npM):
		self.id = i
		self.state = 'RRC-IDLE'
		self.packetFlows = []
		self.bearers = []
		self.radioLinks = RadioLink(1,ue_sinr0,self.id)
		self.TBid = 1
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
		self.TXedTB = 1
		self.lostTB = 0
		self.symb = 0

	def addPacketFlow(self,pckFl):
		self.packetFlows.append(pckFl)

	def addBearer(self,br):
		self.bearers.append(br)

	def receivePckt(self,env,c): # PEM -------------------------------------------
		"""This method takes packets on the application buffers and leave them on the bearer buffers. This is a PEM method."""
		while True:
			if len(self.packetFlows[0].appBuff.pckts)>0:
				if self.state == 'RRC-IDLE': # Not connected
					self.connect(c)
					nextPackTime = c.tUdQueue
					yield env.timeout(nextPackTime)
					if nextPackTime > c.inactTimer:
						self.releaseConnection(c)
				else: # Already connecter user
					self.queueDataPckt(c)
					nextPackTime = c.tUdQueue
					yield env.timeout(nextPackTime)
					if nextPackTime > c.inactTimer:
						self.releaseConnection(c)
			else:
				nextPackTime = c.tUdQueue
				yield env.timeout(nextPackTime)

	def connect(self,cl):
		"""This method creates bearers and bearers buffers."""
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
		"""This method queues the packets taken from the application buffer in the bearer buffers."""
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

# ------------------------------------------------
# PacketFlow class: PacketFlow description
class PacketFlow():
	""" This class is used to describe UE traffic profile for the simulation."""
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
		"""This method creates packets according to the packet flow traffic profile and stores them in the application buffer. """
		ueN = int(self.ue[2:]) # number of UEs in simulation
		self.tStart = (random.expovariate(1.0))
		yield env.timeout(self.tStart) 	 # each UE start transmission after tStart
		while env.now<(tSim*0.83):
			self.sentPackets = self.sentPackets + 1
			size = self.getPsize()
			pD = Packet(self.pId,size+self.header,self.qosFlowId,self.ue)
			self.pId = self.pId + 1
			pD.tIn = env.now
			self.appBuff.insertPckt(pD)
			nextPackTime = self.getParrRate()
			yield env.timeout(nextPackTime)

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
		"""This method calculates average PLR and throughput for the simulation."""
		self.meassuredKPI['PacketLossRate'] = float(100*self.lostPackets)/self.sentPackets
		if tsim>1000:
			self.meassuredKPI['Throughput'] = (float(self.rcvdBytes)*8000)/(0.83*tsim*1024*1024)
		else:
			self.meassuredKPI['Throughput'] = 0

class Packet:
	"""This class is used to model packets properties and behabiour."""
	def __init__(self,sn,s,qfi,u):
		self.secNum = sn
		self.size = s
		self.qosFlowId = qfi
		self.ue = u
		self.tIn = 0

	def printPacket(self):
		print (Format.CYELLOW + Format.CBOLD + self.ue+ '+packet '+str(self.secNum)+' arrives at t ='+str(now()) + Format.CEND)

class Bearer:
	"""This class is used to model Bearers properties and behabiour."""
	def __init__(self,i,q,tp):
		self.id = i
		self.qci = q
		self.type = tp
		self.buffer = PcktQueue()

class PcktQueue:
	"""This class is used to model application and bearer buffers."""
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
	"""This class is used to model radio link properties and behabiour."""
	def __init__(self,i,lq_0,u):
		self.id = i
		state = 'ON'
		self.linkQuality = lq_0
		self.ue = u
		self.totCount = 0
		self.maxVar = 0.1

	def updateLQ(self,env,udIntrv,tSim,fl,u,r):
		"""This method updates UE link quality in terms of SINR during the simulation. This is a PEM method.

		During the simulation it is assumed that UE SINR varies following a normal distribution with mean value equal to initial SINR value, and a small variance."""

		while env.now<(tSim*0.83):
			yield env.timeout(udIntrv)
			deltaSINR = random.normalvariate(0, self.maxVar)
			while deltaSINR > self.maxVar or deltaSINR<(0-self.maxVar):
				deltaSINR = random.normalvariate(0, self.maxVar)
			self.linkQuality = self.linkQuality + deltaSINR

class Format:
    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'
    CBLINK    = '\33[5m'
    CBLINK2   = '\33[6m'
    CSELECTED = '\33[7m'
    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'
    CGREENBG  = '\33[42m'
    CBLUEBG   = '\33[44m'
