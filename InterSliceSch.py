"""This module contains the basic Inter Slice Scheduler class.
All possible inter slice schedulers should inherit from this."""
import math
import os
from Slice import *
import random

class InterSliceScheduler():
    """ Basic inter slice scheduler. It implements Round Robin algorithm."""
    def __init__(self,ba,fr,dm,tdd,gr):
        self.bw = ba
        self.FR = fr
        self.nRBtable = {'FR1':{'15kHz':{'5MHz':25,'10MHz':52,'15MHz':79,'20MHz':106,'25MHz':133,'30MHz':160,'40MHz':216,'50MHz':270},
        '30kHz':{'5MHz':11,'10MHz':24,'15MHz':38,'20MHz':51,'25MHz':65,'30MHz':78,'40MHz':106,'50MHz':133,'60MHz':162,'80MHz':217,'90MHz':245,'100MHz':273},
        '60kHz':{'10MHz':11,'15MHz':18,'20MHz':24,'25MHz':31,'30MHz':38,'40MHz':51,'50MHz':65,'60MHz':79,'80MHz':107,'90MHz':121,'100MHz':135}},
        'FR2':{'60kHz':{'50MHz':66,'100MHz':132,'200MHz':264},
        '120kHz':{'50MHz':32,'100MHz':66,'200MHz':132,'400MHz':264}}} # TS 38.101 table 5.3.2-1

        self.PRBs = 0
        for b in self.bw:
            if fr == 'FR1':
                self.PRBs = self.PRBs + self.nRBtable[fr]['15kHz'][str(b)+'MHz']
            else:
                self.PRBs = self.PRBs + self.nRBtable[fr]['60kHz'][str(b)+'MHz']
        self.slices = {}
        self.dm = dm
        if not os.path.exists('Logs'):
            os.mkdir('Logs')
        self.dbFile = open('Logs/AllSlices_dbFile.html','w')
        self.tdd = tdd
        self.granularity = gr

    def resAlloc(self,env): #PEM ------------------------------------------------
        """This method implements Round Robin PRB allocation between the different configured slices. This is a PEM method"""
        while True:
            self.dbFile.write('<h3> SUBFRAME NUMBER: '+str(env.now)+'</h3>')
            if len(list(self.slices.keys()))>0:
                if len(list(self.slices.keys()))>1:
                    for slice in list(self.slices.keys()):
                        self.slices[slice].updateConfig(int((self.PRBs/len(list(self.slices.keys())))/self.slices[slice].numRefFactor))
                        self.printSliceConfig(slice)
                else:
                    slice = self.slices[list(self.slices.keys())[0]]
                    prbs = 0
                    for b in self.bw:
                        prbs = prbs + self.nRBtable[self.FR][slice.scs][str(b)+'MHz']
                    slice.updateConfig(prbs)
                    #slice.updateConfig(1) # For 1PRB IoT test example! ################################################3
            self.dbFile.write('<hr>')
            yield env.timeout(self.granularity)

    def createSlice(self,dly,thDL,thUL,avl,cnxDL,cnxUL,ba,dm,mmd,ly,lbl,sch):
        """This method creates a slice and stores it in the slices dictionary."""
        self.slices[lbl] = Slice(dly,thDL,thUL,avl,cnxDL,cnxUL,ba,dm,mmd,ly,lbl,self.tdd,sch)


    def printSliceConfig(self,slice):
        """This method stores inter slice scheduling debugging information on the log file."""
        if slice == 'LTE':
            sliceCnx = len(list(self.slices[slice].schedulerDL.ues.keys()))
            sliceBrBuffSz = self.slices[slice].schedulerDL.updSumPcks()
            sliceRessources = self.slices[slice].schedulerDL.nrbUEmax
            self.dbFile.write('<h5> Slice '+self.slices[slice].label+' data:</h5>')
        else:
            sliceCnx = max(len(list(self.slices[slice].schedulerDL.ues.keys())),len(list(self.slices[slice].schedulerUL.ues.keys())))
            sliceBrBuffSz = max(self.slices[slice].schedulerDL.updSumPcks(),self.slices[slice].schedulerUL.updSumPcks())
            sliceRessources = max(self.slices[slice].schedulerDL.nrbUEmax,self.slices[slice].schedulerUL.nrbUEmax)
            self.dbFile.write('<h5> Slice '+self.slices[slice].label+' data:</h5>')
            self.dbFile.write('DL/UL symbols: '+str(self.slices[slice].schedulerDL.TDDsmb)+'/'+str(self.slices[slice].schedulerUL.TDDsmb)+'<br>')

        self.dbFile.write('Connections: '+str(sliceCnx)+'<br>')
        self.dbFile.write('Bearer Buffer Size (Packets): '+str(sliceBrBuffSz)+'<br>')
        self.dbFile.write('Resources (PRBs): '+str(sliceRessources)+'<br>')
