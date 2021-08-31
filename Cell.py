""" This module contains the Cell class.
"""
import os
import sys
import simpy #from SimPy.Simulation import * (simpy2.2)
from collections import deque
import math
import random
from Slice import *
from Scheds_Inter import *

# Cell Class: cell description

class Cell():
    """Cell class has cell relative parameters and collect kpi ststistics. """
    def __init__(self,i,b,fr,dm,mBue,tdd,gr,schInter):
        """This method creates a cell instance.

        It initialices cell parameters and interSliceScheduler according to the algorithm specified on the sch attribute."""
        self.id = i
        self.bw = b
        self.inactTimer = 3000
        self.tUdQueue = 0.05
        self.maxBuffUE = mBue
        """Maximum bearer buffer size by UE, in bytes"""
        self.sch = schInter
        if schInter[0:3] == 'RRp':
            self.interSliceSched = RRplus_Scheduler(self.bw,fr,dm,tdd,gr)
        elif schInter[0:2] == 'PF':
            self.interSliceSched = PF_Scheduler(self.bw,fr,dm,tdd,gr,schInter)
        elif schInter[0:2] == 'DT':
            self.interSliceSched = dynTDD_Scheduler(self.bw,fr,dm,tdd,gr)
        else:
            self.interSliceSched = InterSliceScheduler(self.bw,fr,dm,tdd,gr)
            self.sch = 'RR'
        self.slicesStsts = {}

    def updateStsts(self,env,interv,tSim): # ---------- PEM -------------
        """This method manages the statistics collection. This is a PEM Method.

        This method creates statistics files and stores counter values to calculate later the main kpi considered. \n
        Inter Slice statistics are stored in the dlStsts_InterSlice.txt file for DL and ulStsts_InterSlice.txt file for UL. \n
        Intra Slice statistics are stored in the dlStsts_<Slicename>Slice.txt file for DL and ulStsts_<Slicename>Slice.txt file for UL."""
        if not os.path.exists('Statistics'):
            os.mkdir('Statistics')
        for slice in list(self.interSliceSched.slices.keys()):
            self.slicesStsts[slice] = {}
            self.slicesStsts[slice]['DL'] = open('Statistics/dlStsts'+'_'+slice+'.txt','w')
            self.slicesStsts[slice]['DL'].write('time ue sinr MCS BLER ResourceUse sntPackets lstPackets rcvdBytes sliceLabel'+'\n')
            self.slicesStsts[slice]['UL'] = open('Statistics/ulStsts'+'_'+slice+'.txt','w')
            self.slicesStsts[slice]['UL'].write('time ue sinr MCS BLER ResourceUse sntPackets lstPackets rcvdBytes sliceLabel'+'\n')
        self.slicesStsts['InterSlice'] = {}
        self.slicesStsts['InterSlice']['DL'] = open('Statistics/dlStsts_InterSlice.txt','w')
        self.slicesStsts['InterSlice']['DL'].write('time Slice Connections ResourceUse sntPackets lstPackets rcvdBytes bufferSize'+'\n')
        self.slicesStsts['InterSlice']['UL'] = open('Statistics/ulStsts_InterSlice.txt','w')
        self.slicesStsts['InterSlice']['UL'].write('time Slice Connections ResourceUse sntPackets lstPackets rcvdBytes bufferSize'+'\n')

        while env.now<(tSim*0.83):
            yield env.timeout(interv)
            for slice in list(self.interSliceSched.slices.keys()):
                conn_UEs = list(self.interSliceSched.slices[slice].schedulerDL.ues.keys())
                res = self.interSliceSched.slices[slice].schedulerDL.nrbUEmax
                lostP = 0
                sentP = 0
                recByts = 0
                sliceRcvdBytes = 0 # interSlice PF scheduler
                buf = 0
                for ue in conn_UEs:
                    lP = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].lostPackets
                    sP = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].sentPackets
                    rB = self.interSliceSched.slices[slice].schedulerDL.ues[ue].packetFlows[0].rcvdBytes
                    sinr = self.interSliceSched.slices[slice].schedulerDL.ues[ue].radioLinks.linkQuality
                    mcs = self.interSliceSched.slices[slice].schedulerDL.ues[ue].MCS
                    bler = self.interSliceSched.slices[slice].schedulerDL.ues[ue].bler
                    resUse = self.interSliceSched.slices[slice].schedulerDL.ues[ue].resUse
                    buf = self.interSliceSched.slices[slice].schedulerDL.updSumPcks()
                    lostP = lostP + lP
                    sentP = sentP + sP
                    recByts = recByts + rB
                    self.slicesStsts[slice]['DL'].write(str(env.now)+' '+ue+' '+str(sinr)+' '+str(mcs)+' '+str(bler)+' '+str(resUse)+' '+str(sP)+' '+str(lP)+' '+str(rB)+' '+slice+'\n')
                sliceRcvdBytes = sliceRcvdBytes + recByts # interSlice PF scheduler
                pfSliceMetric = self.interSliceSched.slices[slice].metric
                self.slicesStsts['InterSlice']['DL'].write(str(env.now)+' '+slice+' '+str(len(conn_UEs))+' '+str(res)+' '+ str(sentP)+' '+str(lostP)+' '+str(recByts)+' '+str(buf)+' '+str(pfSliceMetric)+'\n')

                if slice != 'LTE':
                    conn_UEs = list(self.interSliceSched.slices[slice].schedulerUL.ues.keys())
                    res = self.interSliceSched.slices[slice].schedulerUL.nrbUEmax
                    lostP = 0
                    sentP = 0
                    recByts = 0
                    buf = 0
                    for ue in list(self.interSliceSched.slices[slice].schedulerUL.ues.keys()):
                        lP = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].lostPackets
                        sP = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].sentPackets
                        rB = self.interSliceSched.slices[slice].schedulerUL.ues[ue].packetFlows[0].rcvdBytes
                        sinr = self.interSliceSched.slices[slice].schedulerUL.ues[ue].radioLinks.linkQuality
                        mcs = self.interSliceSched.slices[slice].schedulerUL.ues[ue].MCS
                        bler = self.interSliceSched.slices[slice].schedulerUL.ues[ue].bler
                        resUse = self.interSliceSched.slices[slice].schedulerUL.ues[ue].resUse
                        buf = self.interSliceSched.slices[slice].schedulerUL.updSumPcks()
                        lostP = lostP + lP
                        sentP = sentP + sP
                        recByts = recByts + rB
                        self.slicesStsts[slice]['UL'].write(str(env.now)+' '+ue+' '+str(sinr)+' '+str(mcs)+' '+str(bler)+' '+str(resUse)+' '+str(sP)+' '+str(lP)+' '+str(rB)+' '+slice+'\n')
                    sliceRcvdBytes = sliceRcvdBytes + recByts # interSlice PF scheduler
                    self.slicesStsts['InterSlice']['UL'].write(str(env.now)+' '+slice+' '+str(len(conn_UEs))+' '+str(res)+' '+ str(sentP)+' '+str(lostP)+' '+str(recByts)+' '+str(buf)+' '+str(pfSliceMetric)+'\n')
                    if self.sch[0:2] == 'PF' and len(self.interSliceSched.slices[slice].rcvdBytes) >= self.interSliceSched.rcvdBytesLen:
                        self.interSliceSched.slices[slice].rcvdBytes.popleft()
                    self.interSliceSched.slices[slice].rcvdBytes.append(sliceRcvdBytes) # to consider the received bytes during the meassurement interval

            if env.now % (tSim/10) == 0:
                i=int(env.now/(tSim/10))
                print ("\r[%-10s] %d%%" % ('='*i, 10*i)+ ' complete simulation')
