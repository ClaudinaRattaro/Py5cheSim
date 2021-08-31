"""This module contains different implemented inter slice schedulers.
New schedulers should be implemented here following the current structure."""
import math
from InterSliceSch import InterSliceScheduler
from Slice import *
import random

class RRplus_Scheduler(InterSliceScheduler):
    """This class implements Round Robin Plus inter slice scheduling algorithm."""
    def __init__(self,ba,fr,dm,tdd,gr):
        InterSliceScheduler.__init__(self,ba,fr,dm,tdd,gr)

    def resAlloc(self,env): #PEM ------------------------------------------------
        """This method implements Round Robin Plus PRB allocation between the different configured slices.
        This PEM method overwrites the resAlloc method from InterSliceScheduler class.

        Round Robin Plus scheduler allocates the same amount of resources to each slice with packets in buffer. """
        while True:
            self.dbFile.write('<h3> SUBFRAME NUMBER: '+str(env.now)+'</h3>')
            if len(list(self.slices.keys()))>0:
                if len(list(self.slices.keys()))>1:
                    slicesWithPacks = 0
                    for slice in list(self.slices.keys()):
                        sliceHasPackets = self.slices[slice].schedulerDL.updSumPcks()>0 or self.slices[slice].schedulerUL.updSumPcks()>0
                        if sliceHasPackets:
                            slicesWithPacks = slicesWithPacks + 1
                    if slicesWithPacks == 0:
                        for slice in list(self.slices.keys()):
                            self.slices[slice].updateConfig(int((self.PRBs/len(list(self.slices.keys())))/self.slices[slice].numRefFactor))
                            self.printSliceConfig(slice)
                    else:
                        for slice in list(self.slices.keys()):
                            sliceHasPackets = self.slices[slice].schedulerDL.updSumPcks()>0 or self.slices[slice].schedulerUL.updSumPcks()>0
                            if not sliceHasPackets:
                                self.slices[slice].updateConfig(0)
                            else:
                                self.slices[slice].updateConfig(int((self.PRBs/slicesWithPacks)/self.slices[slice].numRefFactor))
                            self.printSliceConfig(slice)
                else:
                    slice = self.slices[list(self.slices.keys())[0]]
                    prbs = 0
                    for b in self.bw:
                        prbs = prbs + self.nRBtable[self.FR][slice.scs][str(b)+'MHz']
                    slice.updateConfig(prbs)
            self.dbFile.write('<hr>')
            yield env.timeout(self.granularity)


class PF_Scheduler(InterSliceScheduler):
    """This class implements Proportional Fair inter slice scheduling algorithm."""
    def __init__(self,ba,fr,dm,tdd,gr,sch):
        InterSliceScheduler.__init__(self,ba,fr,dm,tdd,gr)
        self.sch = sch
        """String formatted as PFXY, with X=numerator exponent for metric formula, and Y=denominator exponent. """
        self.rcvdBytesLen = 10
        """rcvdBytes list length in Slice instance. No more that rcvdBytesLen values are stored."""

    def resAlloc(self,env): #PEM ------------------------------------------------
        """This method implements Proportional Fair resource allocation between the different configured slices.
        This PEM method overwrites the resAlloc method from InterSliceScheduler class.

        Proportional Fair scheduler allocates all PRBs in the cell to the slice with the biggest metric.
        Metric for each slice is calculated as PossibleAverageUEtbs/ReceivedBytes."""
        while True:
            self.dbFile.write('<h3> SUBFRAME NUMBER: '+str(env.now)+'</h3>')
            if len(list(self.slices.keys()))>0:
                if len(list(self.slices.keys()))>1:
                    if env.now>0:
                        self.setMetric(float(self.sch[2]),float(self.sch[3]))
                        maxMetSlice = self.findMaxMetSlice()
                        self.assign2aSlice(maxMetSlice)
                        self.printSliceConfig(maxMetSlice)
                    else:
                        initialSlice = random.choice(list(self.slices.keys()))
                        self.assign2aSlice(initialSlice)
                        self.printSliceConfig(initialSlice)
                else:
                    slice = self.slices[list(self.slices.keys())[0]]
                    prbs = 0
                    for b in self.bw:
                        prbs = prbs + self.nRBtable[self.FR][slice.scs][str(b)+'MHz']
                    slice.updateConfig(prbs)
                    self.printSliceConfig(slice.label)
            self.dbFile.write('<hr>')
            yield env.timeout(self.granularity)

    def setMetric(self,exp_n,exp_d):
        """This method sets the PF metric for each slice"""
        if len(list(self.slices.keys()))>0:
            for slice in list(self.slices.keys()):
                rcvdBt_end = self.slices[slice].rcvdBytes[len(self.slices[slice].rcvdBytes)-1]
                rcvdBt_in = self.slices[slice].rcvdBytes[0]
                if rcvdBt_end - rcvdBt_in == 0:
                    den = 1
                else:
                    den = rcvdBt_end - rcvdBt_in
                num = 0
                for ue in list(self.slices[slice].schedulerDL.ues.keys()):
                    [tbs, mod, bi, mcs] = self.slices[slice].schedulerDL.setMod(ue,self.PRBs)
                    num = num + tbs
                for ue in list(self.slices[slice].schedulerUL.ues.keys()):
                    [tbs, mod, bi, mcs] = self.slices[slice].schedulerUL.setMod(ue,self.PRBs)
                    num = num + tbs
                num = num/(len(list(self.slices[slice].schedulerDL.ues.keys()))+len(list(self.slices[slice].schedulerUL.ues.keys())))
                self.slices[slice].metric = math.pow(float(num), exp_n)/math.pow(den,exp_d)

    def findMaxMetSlice(self):
        """This method finds and returns the Slice with the highest metric"""
        metric = 0
        for slice in list(self.slices.keys()):
            if self.slices[slice].metric > metric:
                metric = self.slices[slice].metric
                maxSliceM = slice
            if self.slices[slice].metric == metric:
                slicesMlist = [maxSliceM,slice]
                maxSliceM = random.choice(slicesMlist)
        return maxSliceM

    def assign2aSlice(self,slice):
        """This method allocates cell's PRBs to the indicated slice"""
        for sl in list(self.slices.keys()):
            if sl == slice:
                self.slices[sl].updateConfig(int(self.PRBs/self.slices[sl].numRefFactor))
            else:
                self.slices[sl].updateConfig(0)

    def printSliceConfig(self,slice):
        """This method stores inter slice scheduling debugging information on the log file, adding PF metric values."""
        super().printSliceConfig(slice)
        for s in list(self.slices.keys()):
            self.dbFile.write('Slice: '+str(s)+' -> PF Metric: '+str(self.slices[s].metric)+'<br>')
