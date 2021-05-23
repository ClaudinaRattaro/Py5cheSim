from IntraSliceSch import IntraSliceScheduler
from Scheds_Intra import *

class Slice:
    def __init__(self,dly,thDL,thUL,avl,cnxDL,cnxUL,ba,dm,mmd,ly,lbl,tdd,nCh,sch):
        self.reqDelay = dly
        self.reqThroughputDL = thDL
        self.reqThroughputUL = thUL
        self.reqAvailability = avl
        self.reqDLconnections = cnxDL
        self.reqULconnections = cnxUL

        self.band = ba
        #self.bw = bw
        self.nCh = nCh
        self.PRBs = 0
        self.signLoad = 0.000001
        self.scs = '15kHz'
        self.ttiBms = 1
        self.robustMCS = False
        self.mimoMd = mmd
        self.layers = ly
        self.tddSymb = 14 # In TDD always 2 symbols for ctrl
        self.schType = sch
        self.label = lbl
        self.tdd = tdd
        self.dm = dm
        self.setInitialConfig()
        self.schedulerDL = self.createSliceSched('DL',self.tddSymb)
        self.schedulerUL = self.createSliceSched('UL',14-self.tddSymb)

    def createSliceSched(self,dir,tddSymb):
        if self.tdd:
            if self.schType[0:2] == 'PF':
                scheduler = PF_Scheduler(self.band,self.PRBs,self.dm,self.signLoad,self.ttiBms,self.mimoMd,self.layers,dir,tddSymb,self.robustMCS,self.label,self.schType)
                print('PF_TDD')
            else:
                scheduler = TDD_Scheduler(self.band,self.PRBs,self.dm,self.signLoad,self.ttiBms,self.mimoMd,self.layers,dir,tddSymb,self.robustMCS,self.label,self.schType)
                print('RR_TDD')
        else: # FDD Schedulers
            if self.schType[0:2] == 'PF':
                scheduler = PF_Scheduler(self.band,self.PRBs,self.dm,self.signLoad,self.ttiBms,self.mimoMd,self.layers,dir,14,self.robustMCS,self.label,self.schType)
                print('PF_FDD')
            else: # RR Scheduler by default
                scheduler = IntraSliceScheduler(self.band,self.PRBs,self.dm,self.signLoad,self.ttiBms,self.mimoMd,self.layers,dir,14,self.robustMCS,self.label,self.schType)
                print('RR_FDD')
        return scheduler

    def setInitialConfig(self):
        self.dly2scs(self.reqDelay)
        if self.band == 'n257' or self.band == 'n258' or self.band == 'n260' or self.band == 'n261':
            self.tdd = True
            numReftable = {'60kHz':1,'120kHz':2}
            self.numRefFactor = numReftable[self.scs]
        else:
            #self.tdd = False
            self.numRefFactor = self.ttiBms
        # if self.tdd:
        #     DLfactor = float(self.reqDLconnections*self.reqThroughputDL)/(self.reqDLconnections*self.reqThroughputDL+self.reqULconnections*self.reqThroughputUL)
        #     self.tddSymb = int(14*DLfactor)
        #     print(self.tddSymb)

        if self.reqAvailability == 'high':
            self.robustMCS = True

        if self.label == 'mMTC':
            self.signLoad = 0.003

    def dly2scs(self,delay):
        if self.band == 'n257' or self.band == 'n258' or self.band == 'n260' or self.band == 'n261': #FR2
            if delay<=2.5:
                self.scs = '120kHz'
                self.ttiBms = 8
            else:
                self.scs = '60kHz'
                self.ttiBms = 4
        else: # FR1
            if delay<=2.5:
                self.scs = '120kHz'
                self.ttiBms = 8
            elif delay<=5:
                self.scs = '60kHz'
                self.ttiBms = 4
            elif delay<=10:
                self.scs = '30kHz'
                self.ttiBms = 2
            else:
                self.scs = '15kHz'
                self.ttiBms = 1

    def updateConfig(self,n):
        self.PRBs = n
        self.schedulerDL.nrbUEmax = self.PRBs
        self.schedulerUL.nrbUEmax = self.PRBs
        if self.mimoMd == 'MU':
            self.schedulerDL.queue.updateSize(self.PRBs*self.layers)
            self.schedulerUL.queue.updateSize(self.PRBs*self.layers)
        else:
            self.schedulerDL.queue.updateSize(self.PRBs)
            self.schedulerUL.queue.updateSize(self.PRBs)
