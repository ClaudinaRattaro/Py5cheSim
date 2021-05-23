import math
from IntraSliceSch import IntraSliceScheduler
from collections import deque

class PF_Scheduler(IntraSliceScheduler): # PF Sched ---------
    def __init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch):
        IntraSliceScheduler.__init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch)
        self.promLen = 30
    def resAlloc(self,band):
        schd = self.schType[0:2]
        if schd=='PF' and len(list(self.ues.keys()))>0:
            exp_num = float(self.schType[2])
            exp_den = float(self.schType[3])
            self.setUEfactor(exp_num, exp_den)
            maxInd = self.findMaxFactor()
            for ue in list(self.ues.keys()):
                if ue == maxInd:
                    self.ues[ue].prbs = band
                else:
                    self.ues[ue].prbs = 0
                    if len(self.ues[ue].pastTbsz)>self.promLen:
                        self.ues[ue].pastTbsz.popleft()
                    self.ues[ue].pastTbsz.append(self.ues[ue].tbsz)
                    self.ues[ue].tbsz = 1
        # Print Resource Allocation
        self.printResAlloc()

    def setUEfactor(self, exp_n, exp_d):
        for ue in list(self.ues.keys()):
            sumTBS = 0
            for t in self.ues[ue].pastTbsz:
                sumTBS = sumTBS + t
            actual_den = sumTBS/len(self.ues[ue].pastTbsz)
            [tbs, mod, bi, mcs] = self.setMod(ue,self.nrbUEmax)
            self.ues[ue].pfFactor = math.pow(float(tbs), exp_n)/math.pow(actual_den,exp_d)
            self.ues[ue].lastDen = actual_den
            self.ues[ue].num = tbs

    def findMaxFactor(self):
        factorMax = 0
        factorMaxInd = ''
        for ue in list(self.ues.keys()):
            if len(self.ues[ue].bearers[0].buffer.pckts)>0 and self.ues[ue].pfFactor>factorMax:
                factorMax = self.ues[ue].pfFactor
                factorMaxInd = ue
        if factorMaxInd=='':
            ue = list(self.ues.keys())[self.ind_u]
            q = 0
            while len(self.ues[ue].bearers[0].buffer.pckts)==0 and q<len(self.ues):
                self.updIndUE()
                ue = list(self.ues.keys())[self.ind_u]
                q = q + 1
            factorMaxInd = ue

        return factorMaxInd

class TDD_Scheduler(IntraSliceScheduler): # TDD Sched ---------
    # Allocates the entire band to each UE by TTI
    def __init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch):
        IntraSliceScheduler.__init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch)
        self.symMax = Smb
        self.queue = TBqueueTDD(self.symMax)

    def resAlloc(self,band):
        if len(list(self.ues.keys()))>0:
            for ue in list(self.ues.keys()):
                self.ues[ue].prbs = band
                self.ues[ue].symb = 1
                #self.ues[ue].symb = max(1,round(12.0/len(list(self.ues.keys()))))
        # Print Resource Allocation
        self.printResAlloc()

    def queueUpdate(self):
        # Make Resource allocation and Insert generated TBs into Scheduler queue,for 1 TTI
        packts = 1
        self.ueLst = list(self.ues.keys())
        self.resAlloc(self.nrbUEmax)
        sym = 0
        if self.mimomd == 'MU':
            self.rb_lim = self.nrbUEmax*self.nlayers # max allocated RB/TTI
        else:
            self.sm_lim = self.symMax

        while len(self.ueLst)>0 and packts>0 and sym < self.sm_lim:
            #rb = rb + self.rrcBrcstSigIn() # To add Broadcast signalling (MIB and SIB)
            ue = self.ueLst[self.ind_u]
            self.printDebDataDM('---------------- '+ue+' ------------------<br>') # print more info in debbug mode
            if self.ues[ue].symb>0:
                if len(self.ues[ue].bearers)>0 and sym < self.sm_lim:
                    if len(self.ues[ue].pendingTB)==0: # No TB to reTX
                        sym = sym + self.rrcUncstSigIn(ue)
                        if  len(self.ues[ue].bearers[0].buffer.pckts)>0 and sym < self.sm_lim:
                            sym = sym + self.dataPtoTB(ue)
                    else: # There are TB to reTX
                        self.printPendTB()
                        sym = sym + self.retransmitTB(ue)
                    if self.dbMd:
                        self.printQtb() # Print TB queue in debbug mode
            # else:
            #     self.printDebDataDM( ue+' has not resources in this subframe')
            self.updIndUE()
            packts = self.updSumPcks()

    def rrcUncstSigIn(self,u):
        ueN = int(self.ues[u].id[2:])
        sfSig = int(float(1)/self.sLoad)
        rrcUESigCond = (self.sbFrNum-ueN)%sfSig == 0
        if rrcUESigCond:
            p_l = []
            p_l.append(self.ues[u].packetFlows[0].pId)
            self.ues[u].packetFlows[0].pId = self.ues[u].packetFlows[0].pId + 1
            ins = self.insertTB(self.ues[u].TBid,'4-QAM',u,'Sig',p_l,self.ues[u].prbs,19)
            r = self.symMax
        else:
            r = 0
        return r

    def retransmitTB(self,u):
        pendingTbl = self.ues[u].pendingTB[0]
        if pendingTbl.reTxNum < 3000:# or pendingTbl.type == 'Sig': # TB retransmission
            intd = self.queue.insertTB(pendingTbl)
            self.ues[u].pendingTB.pop(0)
            pendingTbl.reTxNum = pendingTbl.reTxNum + 1
            r = self.symMax
        else:
            self.ues[u].pendingTB.pop(0) # Drop!!!
            r = 0
        return r

    def dataPtoTB(self,u):
        n = self.ues[u].prbs
        [tbSbits,mod,bits,mcs__] = self.setMod(u,n)
        if self.schType[0:2]=='PF':
            if len(self.ues[u].pastTbsz)>self.promLen:
                self.ues[u].pastTbsz.popleft()
            self.ues[u].pastTbsz.append(self.ues[u].tbsz)

        self.ues[u].tbsz = tbSbits
        self.ues[u].MCS = mcs__
        self.setBLER(u)
        tbSize = int(float(tbSbits)/8) # TB size in bytes
        self.printDebDataDM('TBs: '+str(tbSize)+' nrb: '+str(n)+' FreeSp: '+str(self.queue.getFreeSpace())+'<br>')
        pks_s = 0
        list_p = []
        while pks_s<tbSize and len(self.ues[u].bearers[0].buffer.pckts)>0:
            pacD = self.ues[u].bearers[0].buffer.removePckt()
            pks_s = pks_s + pacD.size# + 2
            list_p.append(pacD.secNum)
            #print u,' -> ',str(list_p[0].secNum)
        #print u,'pack: ',str(pacD.secNum),'TBsize: ',str(tbSize),'TB: ',str(self.ues[u].TBid),'n:',str(nn), str(self.ues[u].prbs),' +++++++++++++'
        insrt = self.insertTB(self.ues[u].TBid,mod,u,'data',list_p,n,min(int(pks_s),tbSize))
        if (pks_s - tbSize)>0:
            pacD.size = pks_s - tbSize
            self.ues[u].bearers[0].buffer.insertPcktLeft(pacD)
        return self.ues[u].symb

    def setTBS(self,r,qm,uldl,u_,fr,nprb): # TS 38.214 procedure
        OHtable = {'DL':{'FR1':0.08,'FR2':0.10},'UL':{'FR1':0.08,'FR2':0.11}}
        OH = OHtable[uldl][fr]
        Nre__ = min(156,math.floor(12*self.ues[u_].symb*(1-OH)))
        if self.mimomd == 'SU':
            # Ninfo = Nre__*self.ues[u_].prbs*r*qm*self.nlayers
            Ninfo = Nre__*nprb*r*qm*self.nlayers
        else:
            # Ninfo = Nre__*self.ues[u_].prbs*r*qm
            Ninfo = Nre__*nprb*r*qm
            tbs = Ninfo
            #print(str(self.TDDsmb)+'-----------------> '+str(Nre__)+' ----- '+str(qm)+' '+str(r)+' '+str(nprb)+'=========> '+str(Ninfo))

        return tbs

class TBqueueTDD: # TB queue!!!
    def __init__(self,symb):
        self.res = deque([])
        self.numRes = symb

    def getFreeSpace(self):
        freeSpace = self.numRes
        if len(self.res)>0:
            for tbl in self.res:
                freeSpace = freeSpace - 1
        return freeSpace

    def insertTB(self,tb):
        succ = False
        freeSpace = self.getFreeSpace()
        if freeSpace>=1:
            self.res.append(tb) # The TB fits the free space
            succ = True
        else:
            succ = False
            print (Format.CRED+'No dentraaaaaaaaaa: '+str(freeSpace)+'/'+str(tb.numRB)+Format.CEND)
        return succ

    def removeTB(self):
        if len(self.res)>0:
            return self.res.popleft()

    def updateSize(self,newSize):
        self.numRes = newSize
