import os
import sys
import simpy #from SimPy.Simulation import * (simpy2.2)
from collections import deque
import math
import random
from Slice import *

# Cell Class: cell description

class Cell():
    def __init__(self,i,b,fr,dm,mB,mBue,tdd):
        #Process.__init__(self)
        self.id = i
        self.bw = b
        self.inactTimer = 3000
        self.tUdQueue = 0.05
        self.maxBuff = mB
        self.maxBuffUE = mBue
        self.interSliceSched = interSliceScheduler(self.bw,fr,dm,tdd)
        self.slicesStsts = {}


    def controlAccess(self,u):
        return True

    def congestionControl(self,u):
        return True

    def updateStsts(self,env,interv,tSim): # ---------- PEM -------------
        for slice in list(self.interSliceSched.slices.keys()):
            self.slicesStsts[slice] = {}
            self.slicesStsts[slice]['DL'] = open('dlStsts'+'_'+slice+'.txt','w')
            self.slicesStsts[slice]['DL'].write('time ue sinr MCS BLER ResourceUse sntPackets lstPackets rcvdBytes sliceLabel'+'\n')
            self.slicesStsts[slice]['UL'] = open('ulStsts'+'_'+slice+'.txt','w')
            self.slicesStsts[slice]['UL'].write('time ue sinr MCS BLER ResourceUse sntPackets lstPackets rcvdBytes sliceLabel'+'\n')
        self.slicesStsts['InterSlice'] = {}
        self.slicesStsts['InterSlice']['DL'] = open('dlStsts_InterSlice.txt','w')
        self.slicesStsts['InterSlice']['DL'].write('time Slice Connections ResourceUse sntPackets lstPackets rcvdBytes'+'\n')
        self.slicesStsts['InterSlice']['UL'] = open('ulStsts_InterSlice.txt','w')
        self.slicesStsts['InterSlice']['UL'].write('time Slice Connections ResourceUse sntPackets lstPackets rcvdBytes'+'\n')

        while env.now<(tSim*0.83):
            yield env.timeout(interv) #yield hold, self, interv
            for slice in list(self.interSliceSched.slices.keys()):
                conn_UEs = list(self.interSliceSched.slices[slice].schedulerDL.ues.keys())
                res = self.interSliceSched.slices[slice].schedulerDL.nrbUEmax
                lostP = 0
                sentP = 0
                recByts = 0
                for ue in conn_UEs:
                    lP = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].lostPackets
                    sP = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].sentPackets
                    rB = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].rcvdBytes
                    sinr = self.interSliceSched.slices[slice].schedulerDL.ues[ue].radioLinks.linkQuality
                    mcs = self.interSliceSched.slices[slice].schedulerDL.ues[ue].MCS
                    bler = self.interSliceSched.slices[slice].schedulerDL.ues[ue].bler
                    resUse = self.interSliceSched.slices[slice].schedulerDL.ues[ue].resUse
                    lostP = lostP + lP
                    sentP = sentP + sP
                    recByts = recByts + rB
                    self.slicesStsts[slice]['DL'].write(str(env.now)+' '+ue+' '+str(sinr)+' '+str(mcs)+' '+str(bler)+' '+str(resUse)+' '+str(sP)+' '+str(lP)+' '+str(rB)+' '+slice+'\n')
                self.slicesStsts['InterSlice']['DL'].write(str(env.now)+' '+slice+' '+str(len(conn_UEs))+' '+str(res)+' '+ str(sentP)+' '+str(lostP)+' '+str(recByts)+'\n')
                conn_UEs = list(self.interSliceSched.slices[slice].schedulerUL.ues.keys())
                res = self.interSliceSched.slices[slice].schedulerUL.nrbUEmax
                lostP = 0
                sentP = 0
                recByts = 0
                for ue in list(self.interSliceSched.slices[slice].schedulerUL.ues.keys()):
                    lP = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].lostPackets
                    sP = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].sentPackets
                    rB = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].rcvdBytes
                    sinr = self.interSliceSched.slices[slice].schedulerUL.ues[ue].radioLinks.linkQuality
                    mcs = self.interSliceSched.slices[slice].schedulerUL.ues[ue].MCS
                    bler = self.interSliceSched.slices[slice].schedulerUL.ues[ue].bler
                    resUse = self.interSliceSched.slices[slice].schedulerUL.ues[ue].resUse
                    lostP = lostP + lP
                    sentP = sentP + sP
                    recByts = recByts + rB
                    self.slicesStsts[slice]['UL'].write(str(env.now)+' '+ue+' '+str(sinr)+' '+str(mcs)+' '+str(bler)+' '+str(resUse)+' '+str(sP)+' '+str(lP)+' '+str(rB)+' '+slice+'\n')
                self.slicesStsts['InterSlice']['UL'].write(str(env.now)+' '+slice+' '+str(len(conn_UEs))+' '+str(res)+' '+ str(sentP)+' '+str(lostP)+' '+str(recByts)+'\n')
            if env.now % (tSim/10) == 0:
                i=int(env.now/(tSim/10))
                print ("\r[%-10s] %d%%" % ('='*i, 10*i)+ 'complete simulation')



class interSliceScheduler():
    def __init__(self,ba,fr,dm,tdd):
        self.bw = ba
        self.NRBtable = {'FR1':{'15kHz':{'5MHz':25,'10MHz':52,'15MHz':79,'20MHz':106,'25MHz':133,'30MHz':160,'40MHz':216,'50MHz':270},
        '30kHz':{'5MHz':11,'10MHz':24,'15MHz':38,'20MHz':51,'25MHz':65,'30MHz':78,'40MHz':106,'50MHz':133,'60MHz':162,'80MHz':217,'90MHz':245,'100MHz':273},
        '60kHz':{'10MHz':11,'15MHz':18,'20MHz':24,'25MHz':31,'30MHz':38,'40MHz':51,'50MHz':65,'60MHz':79,'80MHz':107,'90MHz':121,'100MHz':135}},
        'FR2':{'60kHz':{'50MHz':66,'100MHz':132,'200MHz':264},
        '120kHz':{'50MHz':32,'100MHz':66,'200MHz':132,'400MHz':264}}} # TS 38.101 table 5.3.2-1
        if fr == 'FR1':
            self.PRBs = self.NRBtable[fr]['15kHz'][str(self.bw)+'MHz']
        else:
            self.PRBs = self.NRBtable[fr]['60kHz'][str(self.bw)+'MHz']
        self.slices = {}
        self.dm = dm
        self.dbFile = open('AllSlices_dbFile.html','w')
        self.tdd = tdd

    def allocRes(self,env): #PEM ------------------------------------------------
        while True:
            self.dbFile.write('<h3> SUBFRAME NUMBER: '+str(env.now)+'</h3>')
            if len(list(self.slices.keys()))>0:
                for slice in list(self.slices.keys()):
                    self.printSliceConfig(slice)
                    self.slices[slice].updateConfig(int((self.PRBs/len(list(self.slices.keys())))/self.slices[slice].numRefFactor))
                    #print (str(self.slices[slice].PRBs)+'+++++++++++++++++++')
            self.dbFile.write('<hr>')
            yield env.timeout(1.0) #yield hold, self, 1.0

    def createSlice(self,dly,thDL,thUL,avl,cnxDL,cnxUL,ba,dm,mmd,ly,lbl,nCh,sch):
        self.slices[lbl] = Slice(dly,thDL,thUL,avl,cnxDL,cnxUL,ba,dm,mmd,ly,lbl,self.tdd,nCh,sch)


    def printSliceConfig(self,slice):
        sliceCnx = max(len(list(self.slices[slice].schedulerDL.ues.keys())),len(list(self.slices[slice].schedulerUL.ues.keys())))
        sliceBrBuffSz = max(self.slices[slice].schedulerDL.updSumPcks(),self.slices[slice].schedulerUL.updSumPcks())
        sliceRessources = max(self.slices[slice].schedulerDL.nrbUEmax,self.slices[slice].schedulerUL.nrbUEmax)
        self.dbFile.write('<h5> Slice '+self.slices[slice].label+' data:</h5>')
        self.dbFile.write('Connections: '+str(sliceCnx)+'<br>')
        self.dbFile.write('Bearer Buffer Size: '+str(sliceBrBuffSz)+'<br>')
        self.dbFile.write('Resources: '+str(sliceRessources)+'<br>')



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
