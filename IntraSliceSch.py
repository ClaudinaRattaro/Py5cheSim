"""This module contains the basic Intra Slice Scheduler class.
All possible intra slice schedulers should inherit from this."""
import os
import sys
import simpy
from collections import deque
import math
import random

class IntraSliceScheduler():
    """ Basic intra slice scheduler. It implements Round Robin algorithm."""
    def __init__(self,ba,n,debMd,sLod,ttiByms,mmd_,ly_,dir,Smb,robustMCS,slcLbl,sch):
        self.band = ba
        self.PRBs = n
        if mmd_ == 'MU':
            prbsMaxQueue = ly_*n # 5G
        else:
            prbsMaxQueue = n
        self.schType = sch
        self.queue = TBqueue(prbsMaxQueue)
        self.ues = {}
        self.modTable = []
        self.sinrModTable = [] # 5G
        self.ind_u = 0
        self.nrbUEmax = n
        self.sbFrNum = 0
        self.dbMd = debMd
        self.rets = 0
        self.sLoad = sLod
        self.ueLst = []
        self.ttiByms = ttiByms # 5G
        self.mimomd = mmd_ # 5G
        self.nlayers = ly_ # 5G
        self.direction = dir # 5G
        self.TDDsmb = Smb # 5G
        self.robustMCS = robustMCS # 5G
        self.tdd = self.band == 'n257' or self.band == 'n258' or self.band == 'n260' or self.band == 'n261'
        self.loadModTable()
        self.loadSINR_MCStable() # 5G
        self.sliceLabel = slcLbl # 5G
        if not os.path.exists('Logs'):
            os.mkdir('Logs')
        self.dbFile = open('Logs/'+self.sliceLabel+dir+'dbFile.html','w') # 5G

    def loadModTable(self):
        """MCS table 2 (5.1.3.1-2) from 3GPP TS 38.214"""
        self.modTable.append({'spctEff':0.2344, 'bitsPerSymb':2,'codeRate':0.1171875,'mcsi':0,'mod':'BPSK'})
        self.modTable.append({'spctEff':0.377, 'bitsPerSymb':2,'codeRate':0.1884765625,'mcsi':1,'mod':'BPSK'})
        self.modTable.append({'spctEff':0.6016, 'bitsPerSymb':2,'codeRate':0.30078125,'mcsi':2,'mod':'BPSK'})
        self.modTable.append({'spctEff':0.877, 'bitsPerSymb':2,'codeRate':0.4384765625,'mcsi':3,'mod':'BPSK'})
        self.modTable.append({'spctEff':1.1758, 'bitsPerSymb':2,'codeRate':0.587890625,'mcsi':4,'mod':'BPSK'})
        self.modTable.append({'spctEff':1.4766, 'bitsPerSymb':4,'codeRate':0.369140625,'mcsi':5,'mod':'QPSK'})
        self.modTable.append({'spctEff':1.6953, 'bitsPerSymb':4,'codeRate':0.423828125,'mcsi':6,'mod':'QPSK'})
        self.modTable.append({'spctEff':1.9141, 'bitsPerSymb':4,'codeRate':0.478515625,'mcsi':7,'mod':'QPSK'})
        self.modTable.append({'spctEff':2.1602, 'bitsPerSymb':4,'codeRate':0.5400390625,'mcsi':8,'mod':'QPSK'})
        self.modTable.append({'spctEff':2.4063, 'bitsPerSymb':4,'codeRate':0.6015625,'mcsi':9,'mod':'QPSK'})
        self.modTable.append({'spctEff':2.5703, 'bitsPerSymb':4,'codeRate':0.642578125,'mcsi':10,'mod':'QPSK'})
        self.modTable.append({'spctEff':2.7305, 'bitsPerSymb':6,'codeRate':0.455078125,'mcsi':11,'mod':'64QAM'})
        self.modTable.append({'spctEff':3.0293, 'bitsPerSymb':6,'codeRate':0.5048828125,'mcsi':12,'mod':'64QAM'})
        self.modTable.append({'spctEff':3.3223, 'bitsPerSymb':6,'codeRate':0.5537109375,'mcsi':13,'mod':'64QAM'})
        self.modTable.append({'spctEff':3.6094, 'bitsPerSymb':6,'codeRate':0.6015625,'mcsi':14,'mod':'64QAM'})
        self.modTable.append({'spctEff':3.9023, 'bitsPerSymb':6,'codeRate':0.650390625,'mcsi':15,'mod':'64QAM'})
        self.modTable.append({'spctEff':4.2129, 'bitsPerSymb':6,'codeRate':0.7021484375,'mcsi':16,'mod':'64QAM'})
        self.modTable.append({'spctEff':4.5234, 'bitsPerSymb':6,'codeRate':0.75390625,'mcsi':17,'mod':'64QAM'})
        self.modTable.append({'spctEff':4.8164, 'bitsPerSymb':6,'codeRate':0.802734375,'mcsi':18,'mod':'64QAM'})
        self.modTable.append({'spctEff':5.1152, 'bitsPerSymb':6,'codeRate':0.8525390625,'mcsi':19,'mod':'64QAM'})
        self.modTable.append({'spctEff':5.332, 'bitsPerSymb':8,'codeRate':0.66650390625,'mcsi':20,'mod':'256QAM'})
        self.modTable.append({'spctEff':5.5547, 'bitsPerSymb':8,'codeRate':0.6943359375,'mcsi':21,'mod':'256QAM'})
        self.modTable.append({'spctEff':5.8906, 'bitsPerSymb':8,'codeRate':0.736328125,'mcsi':22,'mod':'256QAM'})
        self.modTable.append({'spctEff':6.2266, 'bitsPerSymb':8,'codeRate':0.7783203125,'mcsi':23,'mod':'256QAM'})
        self.modTable.append({'spctEff':6.5703, 'bitsPerSymb':8,'codeRate':0.8212890625,'mcsi':24,'mod':'256QAM'})
        self.modTable.append({'spctEff':6.9141, 'bitsPerSymb':8,'codeRate':0.8642578125,'mcsi':25,'mod':'256QAM'})
        self.modTable.append({'spctEff':7.1602, 'bitsPerSymb':8,'codeRate':0.89501953125,'mcsi':26,'mod':'256QAM'})
        self.modTable.append({'spctEff':7.4063, 'bitsPerSymb':8,'codeRate':0.92578125,'mcsi':27,'mod':'256QAM'})

    def loadSINR_MCStable(self):
        """MCS-SINR allocation table"""

        if self.tdd:
            ############### TDD #########################
            self.sinrModTable.append(1.2) # MCS 0
            self.sinrModTable.append(3.9) # MCS 1
            self.sinrModTable.append(4.9) # MCS 2
            self.sinrModTable.append(7.1) # MCS 3
            self.sinrModTable.append(7.8) # MCS 4
            self.sinrModTable.append(9.05) # MCS 5
            self.sinrModTable.append(10.0) # MCS 6
            self.sinrModTable.append(11.1) # MCS 7
            self.sinrModTable.append(12.0) # MCS 8
            self.sinrModTable.append(13.2) # MCS 9
            self.sinrModTable.append(14.0) # MCS 10
            self.sinrModTable.append(15.2) # MCS 11
            self.sinrModTable.append(16.1) # MCS 12
            self.sinrModTable.append(17.2) # MCS 13
            self.sinrModTable.append(18.0) # MCS 14
            self.sinrModTable.append(19.2) # MCS 15
            self.sinrModTable.append(20.0) # MCS 16
            self.sinrModTable.append(21.8) # MCS 17
            self.sinrModTable.append(22.0) # MCS 18
            self.sinrModTable.append(22.5) # MCS 19
            self.sinrModTable.append(22.9) # MCS 20
            self.sinrModTable.append(24.2) # MCS 21
            self.sinrModTable.append(25.0) # MCS 22
            self.sinrModTable.append(27.2) # MCS 23
            self.sinrModTable.append(28.0) # MCS 24
            self.sinrModTable.append(29.2) # MCS 25
            self.sinrModTable.append(30.0) # MCS 26
            self.sinrModTable.append(100.00) # MCS 27

        else:
            ############## FDD #########################
            self.sinrModTable.append(0.0) # MCS 0
            self.sinrModTable.append(3.0) # MCS 1
            self.sinrModTable.append(5.0) # MCS 2
            self.sinrModTable.append(7.0) # MCS 3
            self.sinrModTable.append(8.1) # MCS 4
            self.sinrModTable.append(9.3) # MCS 5
            self.sinrModTable.append(10.5) # MCS 6
            self.sinrModTable.append(11.9) # MCS 7
            self.sinrModTable.append(12.7) # MCS 8
            self.sinrModTable.append(13.4) # MCS 9
            self.sinrModTable.append(14.0) # MCS 10
            self.sinrModTable.append(15.8) # MCS 11
            self.sinrModTable.append(16.8) # MCS 12
            self.sinrModTable.append(17.8) # MCS 13
            self.sinrModTable.append(18.4) # MCS 14
            self.sinrModTable.append(20.1) # MCS 15
            self.sinrModTable.append(21.1) # MCS 16
            self.sinrModTable.append(22.7) # MCS 17
            self.sinrModTable.append(23.6) # MCS 18
            self.sinrModTable.append(24.2) # MCS 19
            self.sinrModTable.append(24.5) # MCS 20
            self.sinrModTable.append(25.6) # MCS 21
            self.sinrModTable.append(26.3) # MCS 22
            self.sinrModTable.append(28.3) # MCS 23
            self.sinrModTable.append(29.3) # MCS 24
            self.sinrModTable.append(31.7) # MCS 25
            self.sinrModTable.append(35.0) # MCS 26
            self.sinrModTable.append(100.00) # MCS 27

    def queuesOut(self,env): # ---------- PEM -------------
        """This method manages the scheduler TB queue. This is a PEM method.

        At each TTI it first updates the scheduler TB queue and then takes each TB  and sends it through the air interface.
        TB are queued to retransmit with a BLER probability. """
        while True:
            if self.dbMd:
                self.printQstate(env)
            self.queueUpdate() # RESOURCE ALLOCATION
            yield env.timeout(1.0/self.ttiByms)
            self.printDebDataDM('<h4>Transport Blocks served at time = '+ str(env.now)+'</h4>')
            if len(self.queue.res)>0:
                for i in range (len(self.queue.res)):#[0])):
                    tbl = self.queue.removeTB()
                    ue = tbl.ue
                    self.ues[ue].resUse = self.ues[ue].resUse + 1
                    if random.random()<=(1.0-self.ues[ue].bler) or (tbl.reTxNum>0): # not sending again retransmitted TB
                        self.printDebDataDM('<p style="color:green">'+ue+' TB '+str(tbl.id)+ ' Served '+' ---------'+'</p>')
                        self.ues[ue].packetFlows[0].rcvdBytes = self.ues[ue].packetFlows[0].rcvdBytes + tbl.size
                        self.ues[ue].TXedTB = self.ues[ue].TXedTB + 1
                        for pckt in tbl.pckt_l:
                            self.ues[tbl.ue].pendingPckts[pckt] = self.ues[tbl.ue].pendingPckts[pckt] - 1
                            if self.ues[tbl.ue].pendingPckts[pckt] == 0:
                                if not (self.findPackBeQ(tbl.ue,pckt)): # Check if there is a piece of this packet in bearer buffer
                                    self.printDebDataDM('<p style="color:green"><b>'+tbl.ue+ ' Packet '+str(pckt)+ ' Served ---------'+ '</b></p>')
                                    del self.ues[tbl.ue].pendingPckts[pckt]
                    else: # Lost TB -> queue in pendingTB
                        self.printDebDataDM('<p style="color:red">'+ue+' TB '+str(tbl.id)+' Lost '+'!!!'+'</p>')
                        self.rets = self.rets + 1
                        self.ues[tbl.ue].pendingTB.append(tbl)
                        self.ues[ue].lostTB = self.ues[ue].lostTB + 1
            else:
                self.printDebDataDM('<p style="color:green">'+'no more TBs in queue'+'</p>')
            self.sbFrNum = self.sbFrNum + 1

# --------------------------------------------------------

    def findPackBeQ(self,uee,p):
        # Finds packet p in data bearer buffer
        findP = False
        k = 0
        while (not findP) and k<len(self.ues[uee].bearers[0].buffer.pckts):
            findP = findP or p == self.ues[uee].bearers[0].buffer.pckts[k].secNum
            k = k + 1

        return findP

    def queueUpdate(self):
        """This method fills scheduler TB queue at each TTI with TBs built with UE data/signalling bytes.

        It makes Resource allocation and insert generated TBs into Scheduler queue in a TTI."""
        packts = 1
        self.ueLst = list(self.ues.keys())
        self.resAlloc(self.nrbUEmax)
        rb = 0
        if self.mimomd == 'MU':
            self.rb_lim = self.nrbUEmax*self.nlayers # max allocated RB/TTI
        else:
            self.rb_lim = self.nrbUEmax

        while len(self.ueLst)>0 and packts>0 and self.rb_lim > 0 and (rb + self.ues[self.ueLst[self.ind_u]].prbs) <= self.rb_lim:
            ue = self.ueLst[self.ind_u]
            self.printDebDataDM('---------------- '+ue+' ------------------<br>') # print more info in debbug mode
            if self.ues[ue].prbs>0:
                if len(self.ues[ue].bearers)>0 and rb < self.rb_lim:
                    if len(self.ues[ue].pendingTB)==0: # No TB to reTX
                        rb = rb + self.rrcUncstSigIn(ue)
                        if  rb < self.rb_lim:
                            rb = rb + self.dataPtoTB(ue)
                    else: # There are TB to reTX
                        rb = rb + self.retransmitTB(ue)
                    if self.dbMd:
                        self.printQtb() # Print TB queue in debbug mode
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
            r = self.nrbUEmax
        else:
            r = 0
        return r

    def updIndUE(self): # Update ind_u in ues list in circular way.
        if self.ind_u<len(self.ueLst)-1:
            self.ind_u = self.ind_u + 1
        else:
            self.ind_u = 0

    def updSumPcks(self): # Update packts variable (sum all packets in bearer buffers)
        packets = 0
        for uue in list(self.ues.keys()):
            packets = packets + len(self.ues[uue].bearers[0].buffer.pckts)# + len(self.ues[uue].bearers[1].buffer.pckts)
        return packets

    def dataPtoTB(self,u):
        """This method takes UE data bytes, builds TB and puts them in the scheduler TB queue."""
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

        insrt = self.insertTB(self.ues[u].TBid,mod,u,'data',list_p,n,min(int(pks_s),tbSize))
        if (pks_s - tbSize)>0:
            pacD.size = pks_s - tbSize
            self.ues[u].bearers[0].buffer.insertPcktLeft(pacD)
        return n

    def retransmitTB(self,u):
        pendingTbl = self.ues[u].pendingTB[0]
        if pendingTbl.reTxNum < 3000: # TB retransmission
            intd = self.queue.insertTB(pendingTbl)
            self.ues[u].pendingTB.pop(0)
            pendingTbl.reTxNum = pendingTbl.reTxNum + 1
            r = self.ues[u].prbs
        else:
            self.ues[u].pendingTB.pop(0) # Drop!!!
            r = 0
        return r

    def resAlloc(self,Nrb):
        """This method allocates cell PRBs to the different connected UEs."""
        if len(list(self.ues.keys()))>0:
            for ue in list(self.ues.keys()): # TS 38.214 table 5.1.2.2.1-1  RBG size for configuration 2
                if self.ues[ue].BWPs<37:
                    self.ues[ue].prbs = 4
                elif self.ues[ue].BWPs<73:
                    self.ues[ue].prbs = 8
                else:
                    self.ues[ue].prbs = 16
                # self.ues[ue].prbs = Nrb # To compare with lena-5G
        # Print Resource Allocation
        self.printResAlloc()

    def setMod(self,u,nprb): # AMC
        """This method sets the MCS and TBS for each TB."""
        sinr = self.ues[u].radioLinks.linkQuality
        mcs_ = self.findMCS(sinr)
        if self.robustMCS and mcs_>2:
            mcs_ = mcs_-2
        mo = self.modTable[mcs_]['mod']
        mcsi = self.modTable[mcs_]['mcsi']
        Qm = self.modTable[mcs_]['bitsPerSymb']
        R = self.modTable[mcs_]['codeRate']
        # Find TBsize
        if self.band == 'n257' or self.band == 'n258' or self.band == 'n260' or self.band == 'n261':
            fr = 'FR2'
        else:
            fr = 'FR1'
        if nprb>0:
            tbls = self.setTBS(R,Qm,self.direction,u,fr,nprb) # bits
        else:
            tbls = 0 # PF Scheduler
        return [tbls, mo, Qm, mcsi]

    def findMCS(self,s):
        mcs = -1
        findSINR = False
        while mcs<27 and not(findSINR): # By SINR
            mcs = mcs + 1
            if mcs < 27:
                findSINR = s<float(self.sinrModTable[mcs])
            else:
                findSINR = True
        return mcs

    def setTBS(self,r,qm,uldl,u_,fr,nprb): # TS 38.214 procedure
        OHtable = {'DL':{'FR1':0.14,'FR2':0.18},'UL':{'FR1':0.08,'FR2':0.10}}
        OH = OHtable[uldl][fr]
        Nre__ = min(156,math.floor(12*self.TDDsmb*(1-OH)))
        if self.mimomd == 'SU':
            Ninfo = Nre__*nprb*r*qm*self.nlayers
            tbs = Ninfo
        else:
            Ninfo = Nre__*nprb*r*qm
            tbs = Ninfo
        return tbs

    def setBLER(self,u): # BLER calculation
        self.ues[u].bler = 0.0

    def insertTB(self,id,m,uu,type,pack_lst,n,s):
        tb = TransportBlock(id,m,uu,type,pack_lst,n,s)
        succ = self.queue.insertTB(tb)
        if not(uu=='Broadcast'):
            self.ues[uu].TBid = self.ues[uu].TBid + 1 # Only if can insert the TB
            for pack in pack_lst:
                if list(self.ues[uu].pendingPckts.keys()).count(pack)>0:
                    self.ues[uu].pendingPckts[pack] = self.ues[uu].pendingPckts[pack] + 1
                else:
                    self.ues[uu].pendingPckts[pack] = 1
        return succ

# Print methods -----------------------------------------

    def printQstate(self,env):
        if self.dbMd:
            self.printDebData('<hr>')
            self.printDebData('<h3>SUBFRAME NUMBER: '+ str(self.sbFrNum)+'</h3>')
            self.printDebData('<p style="color:blue">'+'Queues status at time = '+ str(env.now)+'</p>')
            self.printQue()
            for ue in list(self.ues.keys()):
                self.ues[ue].packetFlows[0].setMeassures(env.now)
            self.printDebData('<hr>')

    def printQue(self):
        self.printDebData('UEs Bearers queues:')
        if len(list(self.ues.keys()))>0:
            for ue in list(self.ues.keys()):
                self.printDebData('<p style="color:blue">'+ue+' DRB queue:'+'</p>')
                if len(self.ues[ue].bearers)>0 and len(self.ues[ue].bearers[0].buffer.pckts)>0:
                    for p in self.ues[ue].bearers[0].buffer.pckts:
                        self.printDebData(p.ue+ ' packet '+str(p.secNum)+'<br>')
                else:
                    self.printDebData('void DRB queue'+'<br>')
        else:
            self.printDebData('<br>')

    def printQtb(self):
        if self.dbMd:
            self.printDebData('<b>'+'TBs queue:'+'</b>'+'<br>')
            if len(self.queue.res)>0:
                for tb in self.queue.res:
                    self.printDebData('Sbframe n: '+str(self.sbFrNum)+' '+tb.ue+ ' TB '+str(tb.id)+' '+ tb.type+'<br>')
            else:
                self.printDebData( 'void queue'+'<br>')

    def printPendTB(self):
        if self.dbMd:
            self.printDebData( '<b>'+'Pending TBs: '+'</b>'+'<br>')
            for tb in self.ues[ue].pendingTB:
                self.printDebData( 'TB: '+str(tb.id)+'<br>')

    def printDebData(self,debData):
        self.dbFile.write(debData)

    def printDebDataDM(self,debData):
        if self.dbMd:
            self.dbFile.write(debData)

    def printResAlloc(self):
        if self.dbMd:
            self.printDebData('+++++++++++ Res Alloc +++++++++++++'+'<br>')
            self.printDebData('PRBs: '+str(self.nrbUEmax)+'<br>')
            resAllocMsg = ''
            for ue in list(self.ues.keys()):
                resAllocMsg = resAllocMsg + ue +': '+ str(self.ues[ue].prbs)+' PRBs'+'<br>'
            self.printDebData(resAllocMsg)
            self.printDebData('+++++++++++++++++++++++++++++++++++'+'<br>')

#--------------------------------------------------------------

class LTE_scheduler(IntraSliceScheduler):
    """ Basic intra slice LTE scheduler. It implements Round Robin algorithm for scheduling in a LTE Slice."""
    def __init__(self,ba,n,debMd,sLod,mmd_,ly_,dir):
        IntraSliceScheduler.__init__(self,ba,n,debMd,sLod,1,mmd_,ly_,dir,14,False,'LTE','RR')
        self.BER = 0.01
        self.modTable = []
        self.tbsTable = []
        self.cqiTable = []
        self.blerTable = {}
        self.loadModTable()
        self.loadTbsTable()
        self.loadCqiTable()
        self.loadBlerTable()

    def loadModTable(self):
        """3GPP TS 36.213 7.1.7.1-1 merged with MCS table presented in R1-081483."""
        self.modTable.append({})
        self.modTable.append({'spctEff':0.15234375	, 'bitsPerSymb':2	,'codeRate':0.076171875     ,'tbsi':1, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.193359375	, 'bitsPerSymb':2	,'codeRate':0.0966796875    ,'tbsi':2, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.234375  	, 'bitsPerSymb':2	,'codeRate':0.1171875       ,'tbsi':3, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.3056640625, 'bitsPerSymb':2   ,'codeRate':0.1528320313    ,'tbsi':4, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.376953125	, 'bitsPerSymb':2	,'codeRate':0.1884765625	,'tbsi':5, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.4892578125, 'bitsPerSymb':2	,'codeRate':0.2446289063    ,'tbsi':6, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.6015625	, 'bitsPerSymb':2	,'codeRate':0.30078125	    ,'tbsi':7, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.7392578125, 'bitsPerSymb':2	,'codeRate':0.3696289063    ,'tbsi':8, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':0.876953125	, 'bitsPerSymb':2	,'codeRate':0.4384765625	,'tbsi':9, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':1.026367188	, 'bitsPerSymb':2	,'codeRate':0.5131835938	,'tbsi':9, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':1.17578125	, 'bitsPerSymb':2	,'codeRate':0.587890625	    ,'tbsi':10, 'mod': '4-QAM' })
        self.modTable.append({'spctEff':1.326171875	, 'bitsPerSymb':4	,'codeRate':0.3315429688	,'tbsi':11, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':1.4765625	, 'bitsPerSymb':4	,'codeRate':0.369140625	    ,'tbsi':12, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':1.6953125   , 'bitsPerSymb':4	,'codeRate':0.423828125	    ,'tbsi':13, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':1.9140625	, 'bitsPerSymb':4	,'codeRate':0.478515625	    ,'tbsi':14, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':2.16015625	, 'bitsPerSymb':4	,'codeRate':0.5400390625	,'tbsi':15, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':2.40625	    , 'bitsPerSymb':4	,'codeRate':0.6015625   	,'tbsi':15, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':2.568359375	, 'bitsPerSymb':4	,'codeRate':0.6420898438	,'tbsi':16, 'mod': '16-QAM' })
        self.modTable.append({'spctEff':2.73046875	, 'bitsPerSymb':6	,'codeRate':0.455078125	    ,'tbsi':17, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':3.026367188	, 'bitsPerSymb':6	,'codeRate':0.5043945313	,'tbsi':18, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':3.322265625	, 'bitsPerSymb':6	,'codeRate':0.5537109375	,'tbsi':19, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':3.612304688	, 'bitsPerSymb':6	,'codeRate':0.6020507813	,'tbsi':20, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':3.90234375	, 'bitsPerSymb':6	,'codeRate':0.650390625	    ,'tbsi':21, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':4.212890625	, 'bitsPerSymb':6	,'codeRate':0.7021484375	,'tbsi':22, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':4.5234375   , 'bitsPerSymb':6	,'codeRate':0.75390625   	,'tbsi':23, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':4.819335938	, 'bitsPerSymb':6	,'codeRate':0.8032226563	,'tbsi':24, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':5.115234375	, 'bitsPerSymb':6	,'codeRate':0.8525390625	,'tbsi':25, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':5.334960938	, 'bitsPerSymb':6	,'codeRate':0.8891601563	,'tbsi':26, 'mod': '64-QAM' })
        self.modTable.append({'spctEff':5.5546875	, 'bitsPerSymb':6	,'codeRate':0.92578125  	,'tbsi':26, 'mod': '64-QAM' })

    def loadTbsTable(self):
        """TBS table 7.1.7.2.1-1 from 3GPP TS 36.213"""
        self.tbsTable.append({})
        self.tbsTable.append({	'0' : 16,	'1' : 24,	'2' : 32,	'3' : 40,	'4' : 56,	'5' : 72,	'6' : 328,	'7' : 104,	'8' : 120,	'9' : 136,	'10' : 144,	'11' : 176,	'12' : 208,	'13' : 224,	'14' : 256,	'15' : 280,	'16' : 328,	'17' : 336,	'18' : 376,	'19' : 408,	'20' : 440,	'21' : 488,	'22' : 520,	'23' : 552,	'24' : 584,	'25' : 616,	'26' : 712})
        self.tbsTable.append({	'0' : 32,	'1' : 56,	'2' : 72,	'3' : 104,	'4' : 120,	'5' : 144,	'6' : 176,	'7' : 224,	'8' : 256,	'9' : 296,	'10' : 328,	'11' : 376,	'12' : 440,	'13' : 488,	'14' : 552,	'15' : 600,	'16' : 632,	'17' : 696,	'18' : 776,	'19' : 840,	'20' : 904,	'21' : 1000,	'22' : 1064,	'23' : 1128,	'24' : 1192,	'25' : 1256,	'26' : 1480})
        self.tbsTable.append({	'0' : 56,	'1' : 88,	'2' : 144,	'3' : 176,	'4' : 208,	'5' : 224,	'6' : 256,	'7' : 328,	'8' : 392,	'9' : 456,	'10' : 504,	'11' : 584,	'12' : 680,	'13' : 744,	'14' : 840,	'15' : 904,	'16' : 968,	'17' : 1064,	'18' : 1160,	'19' : 1288,	'20' : 1384,	'21' : 1480,	'22' : 1608,	'23' : 1736,	'24' : 1800,	'25' : 1864,	'26' : 2216})
        self.tbsTable.append({	'0' : 88,	'1' : 144,	'2' : 176,	'3' : 208,	'4' : 256,	'5' : 328,	'6' : 392,	'7' : 472,	'8' : 536,	'9' : 616,	'10' : 680,	'11' : 776,	'12' : 904,	'13' : 1000,	'14' : 1128,	'15' : 1224,	'16' : 1288,	'17' : 1416,	'18' : 1544,	'19' : 1736,	'20' : 1864,	'21' : 1992,	'22' : 2152,	'23' : 2280,	'24' : 2408,	'25' : 2536,	'26' : 2984})
        self.tbsTable.append({	'0' : 120,	'1' : 176,	'2' : 208,	'3' : 256,	'4' : 328,	'5' : 424,	'6' : 504,	'7' : 584,	'8' : 680,	'9' : 776,	'10' : 872,	'11' : 1000,	'12' : 1128,	'13' : 1256,	'14' : 1416,	'15' : 1544,	'16' : 1608,	'17' : 1800,	'18' : 1992,	'19' : 2152,	'20' : 2344,	'21' : 2472,	'22' : 2664,	'23' : 2856,	'24' : 2984,	'25' : 3112,	'26' : 3752})
        self.tbsTable.append({	'0' : 152,	'1' : 208,	'2' : 256,	'3' : 328,	'4' : 408,	'5' : 504,	'6' : 600,	'7' : 712,	'8' : 808,	'9' : 936,	'10' : 1032,	'11' : 1192,	'12' : 1352,	'13' : 1544,	'14' : 1736,	'15' : 1800,	'16' : 1928,	'17' : 2152,	'18' : 2344,	'19' : 2600,	'20' : 2792,	'21' : 2984,	'22' : 3240,	'23' : 3496,	'24' : 3624,	'25' : 3752,	'26' : 4392})
        self.tbsTable.append({	'0' : 176,	'1' : 224,	'2' : 296,	'3' : 392,	'4' : 488,	'5' : 600,	'6' : 712,	'7' : 840,	'8' : 968,	'9' : 1096,	'10' : 1224,	'11' : 1384,	'12' : 1608,	'13' : 1800,	'14' : 1992,	'15' : 2152,	'16' : 2280,	'17' : 2536,	'18' : 2792,	'19' : 2984,	'20' : 3240,	'21' : 3496,	'22' : 3752,	'23' : 4008,	'24' : 4264,	'25' : 4392,	'26' : 5160})
        self.tbsTable.append({	'0' : 208,	'1' : 256,	'2' : 328,	'3' : 440,	'4' : 552,	'5' : 680,	'6' : 808,	'7' : 968,	'8' : 1096,	'9' : 1256,	'10' : 1384,	'11' : 1608,	'12' : 1800,	'13' : 2024,	'14' : 2280,	'15' : 2472,	'16' : 2600,	'17' : 2856,	'18' : 3112,	'19' : 3496,	'20' : 3752,	'21' : 4008,	'22' : 4264,	'23' : 4584,	'24' : 4968,	'25' : 5160,	'26' : 5992})
        self.tbsTable.append({	'0' : 224,	'1' : 328,	'2' : 376,	'3' : 504,	'4' : 632,	'5' : 776,	'6' : 936,	'7' : 1096,	'8' : 1256,	'9' : 1416,	'10' : 1544,	'11' : 1800,	'12' : 2024,	'13' : 2280,	'14' : 2600,	'15' : 2728,	'16' : 2984,	'17' : 3240,	'18' : 3624,	'19' : 3880,	'20' : 4136,	'21' : 4584,	'22' : 4776,	'23' : 5160,	'24' : 5544,	'25' : 5736,	'26' : 6712})
        self.tbsTable.append({	'0' : 256,	'1' : 344,	'2' : 424,	'3' : 568,	'4' : 696,	'5' : 872,	'6' : 1032,	'7' : 1224,	'8' : 1384,	'9' : 1544,	'10' : 1736,	'11' : 2024,	'12' : 2280,	'13' : 2536,	'14' : 2856,	'15' : 3112,	'16' : 3240,	'17' : 3624,	'18' : 4008,	'19' : 4264,	'20' : 4584,	'21' : 4968,	'22' : 5352,	'23' : 5736,	'24' : 5992,	'25' : 6200,	'26' : 7480})
        self.tbsTable.append({	'0' : 288,	'1' : 376,	'2' : 472,	'3' : 616,	'4' : 776,	'5' : 968,	'6' : 1128,	'7' : 1320,	'8' : 1544,	'9' : 1736,	'10' : 1928,	'11' : 2216,	'12' : 2472,	'13' : 2856,	'14' : 3112,	'15' : 3368,	'16' : 3624,	'17' : 4008,	'18' : 4392,	'19' : 4776,	'20' : 5160,	'21' : 5544,	'22' : 5992,	'23' : 6200,	'24' : 6712,	'25' : 6968,	'26' : 8248})
        self.tbsTable.append({	'0' : 328,	'1' : 424,	'2' : 520,	'3' : 680,	'4' : 840,	'5' : 1032,	'6' : 1224,	'7' : 1480,	'8' : 1672,	'9' : 1864,	'10' : 2088,	'11' : 2408,	'12' : 2728,	'13' : 3112,	'14' : 3496,	'15' : 3624,	'16' : 3880,	'17' : 4392,	'18' : 4776,	'19' : 5160,	'20' : 5544,	'21' : 5992,	'22' : 6456,	'23' : 6968,	'24' : 7224,	'25' : 7480,	'26' : 8760})
        self.tbsTable.append({	'0' : 344,	'1' : 456,	'2' : 568,	'3' : 744,	'4' : 904,	'5' : 1128,	'6' : 1352,	'7' : 1608,	'8' : 1800,	'9' : 2024,	'10' : 2280,	'11' : 2600,	'12' : 2984,	'13' : 3368,	'14' : 3752,	'15' : 4008,	'16' : 4264,	'17' : 4776,	'18' : 5160,	'19' : 5544,	'20' : 5992,	'21' : 6456,	'22' : 6968,	'23' : 7480,	'24' : 7992,	'25' : 8248,	'26' : 9528})
        self.tbsTable.append({	'0' : 376,	'1' : 488,	'2' : 616,	'3' : 808,	'4' : 1000,	'5' : 1224,	'6' : 1480,	'7' : 1672,	'8' : 1928,	'9' : 2216,	'10' : 2472,	'11' : 2792,	'12' : 3240,	'13' : 3624,	'14' : 4008,	'15' : 4264,	'16' : 4584,	'17' : 5160,	'18' : 5544,	'19' : 5992,	'20' : 6456,	'21' : 6968,	'22' : 7480,	'23' : 7992,	'24' : 8504,	'25' : 8760,	'26' : 10296})
        self.tbsTable.append({	'0' : 392,	'1' : 520,	'2' : 648,	'3' : 872,	'4' : 1064,	'5' : 1320,	'6' : 1544,	'7' : 1800,	'8' : 2088,	'9' : 2344,	'10' : 2664,	'11' : 2984,	'12' : 3368,	'13' : 3880,	'14' : 4264,	'15' : 4584,	'16' : 4968,	'17' : 5352,	'18' : 5992,	'19' : 6456,	'20' : 6968,	'21' : 7480,	'22' : 7992,	'23' : 8504,	'24' : 9144,	'25' : 9528,	'26' : 11064})
        self.tbsTable.append({	'0' : 424,	'1' : 568,	'2' : 696,	'3' : 904,	'4' : 1128,	'5' : 1384,	'6' : 1672,	'7' : 1928,	'8' : 2216,	'9' : 2536,	'10' : 2792,	'11' : 3240,	'12' : 3624,	'13' : 4136,	'14' : 4584,	'15' : 4968,	'16' : 5160,	'17' : 5736,	'18' : 6200,	'19' : 6968,	'20' : 7480,	'21' : 7992,	'22' : 8504,	'23' : 9144,	'24' : 9912,	'25' : 10296,	'26' : 11832})
        self.tbsTable.append({	'0' : 456,	'1' : 600,	'2' : 744,	'3' : 968,	'4' : 1192,	'5' : 1480,	'6' : 1736,	'7' : 2088,	'8' : 2344,	'9' : 2664,	'10' : 2984,	'11' : 3496,	'12' : 3880,	'13' : 4392,	'14' : 4968,	'15' : 5160,	'16' : 5544,	'17' : 6200,	'18' : 6712,	'19' : 7224,	'20' : 7992,	'21' : 8504,	'22' : 9144,	'23' : 9912,	'24' : 10296,	'25' : 10680,	'26' : 12576})
        self.tbsTable.append({	'0' : 488,	'1' : 632,	'2' : 776,	'3' : 1032,	'4' : 1288,	'5' : 1544,	'6' : 1864,	'7' : 2216,	'8' : 2536,	'9' : 2856,	'10' : 3112,	'11' : 3624,	'12' : 4136,	'13' : 4584,	'14' : 5160,	'15' : 5544,	'16' : 5992,	'17' : 6456,	'18' : 7224,	'19' : 7736,	'20' : 8248,	'21' : 9144,	'22' : 9528,	'23' : 10296,	'24' : 11064,	'25' : 11448,	'26' : 13536})
        self.tbsTable.append({	'0' : 504,	'1' : 680,	'2' : 840,	'3' : 1096,	'4' : 1352,	'5' : 1672,	'6' : 1992,	'7' : 2344,	'8' : 2664,	'9' : 2984,	'10' : 3368,	'11' : 3880,	'12' : 4392,	'13' : 4968,	'14' : 5544,	'15' : 5736,	'16' : 6200,	'17' : 6712,	'18' : 7480,	'19' : 8248,	'20' : 8760,	'21' : 9528,	'22' : 10296,	'23' : 11064,	'24' : 11448,	'25' : 12216,	'26' : 14112})
        self.tbsTable.append({	'0' : 536,	'1' : 712,	'2' : 872,	'3' : 1160,	'4' : 1416,	'5' : 1736,	'6' : 2088,	'7' : 2472,	'8' : 2792,	'9' : 3112,	'10' : 3496,	'11' : 4008,	'12' : 4584,	'13' : 5160,	'14' : 5736,	'15' : 6200,	'16' : 6456,	'17' : 7224,	'18' : 7992,	'19' : 8504,	'20' : 9144,	'21' : 9912,	'22' : 10680,	'23' : 11448,	'24' : 12216,	'25' : 12576,	'26' : 14688})
        self.tbsTable.append({	'0' : 568,	'1' : 744,	'2' : 936,	'3' : 1224,	'4' : 1480,	'5' : 1864,	'6' : 2216,	'7' : 2536,	'8' : 2984,	'9' : 3368,	'10' : 3752,	'11' : 4264,	'12' : 4776,	'13' : 5352,	'14' : 5992,	'15' : 6456,	'16' : 6712,	'17' : 7480,	'18' : 8248,	'19' : 9144,	'20' : 9912,	'21' : 10680,	'22' : 11448,	'23' : 12216,	'24' : 12960,	'25' : 13536,	'26' : 15264})
        self.tbsTable.append({	'0' : 600,	'1' : 776,	'2' : 968,	'3' : 1256,	'4' : 1544,	'5' : 1928,	'6' : 2280,	'7' : 2664,	'8' : 3112,	'9' : 3496,	'10' : 3880,	'11' : 4392,	'12' : 4968,	'13' : 5736,	'14' : 6200,	'15' : 6712,	'16' : 7224,	'17' : 7992,	'18' : 8760,	'19' : 9528,	'20' : 10296,	'21' : 11064,	'22' : 11832,	'23' : 12576,	'24' : 13536,	'25' : 14112,	'26' : 16416})
        self.tbsTable.append({	'0' : 616,	'1' : 808,	'2' : 1000,	'3' : 1320,	'4' : 1608,	'5' : 2024,	'6' : 2408,	'7' : 2792,	'8' : 3240,	'9' : 3624,	'10' : 4008,	'11' : 4584,	'12' : 5352,	'13' : 5992,	'14' : 6456,	'15' : 6968,	'16' : 7480,	'17' : 8248,	'18' : 9144,	'19' : 9912,	'20' : 10680,	'21' : 11448,	'22' : 12576,	'23' : 12960,	'24' : 14112,	'25' : 14688,	'26' : 16992})
        self.tbsTable.append({	'0' : 648,	'1' : 872,	'2' : 1064,	'3' : 1384,	'4' : 1736,	'5' : 2088,	'6' : 2472,	'7' : 2984,	'8' : 3368,	'9' : 3752,	'10' : 4264,	'11' : 4776,	'12' : 5544,	'13' : 6200,	'14' : 6968,	'15' : 7224,	'16' : 7736,	'17' : 8760,	'18' : 9528,	'19' : 10296,	'20' : 11064,	'21' : 12216,	'22' : 12960,	'23' : 13536,	'24' : 14688,	'25' : 15264,	'26' : 17568})
        self.tbsTable.append({	'0' : 680,	'1' : 904,	'2' : 1096,	'3' : 1416,	'4' : 1800,	'5' : 2216,	'6' : 2600,	'7' : 3112,	'8' : 3496,	'9' : 4008,	'10' : 4392,	'11' : 4968,	'12' : 5736,	'13' : 6456,	'14' : 7224,	'15' : 7736,	'16' : 7992,	'17' : 9144,	'18' : 9912,	'19' : 10680,	'20' : 11448,	'21' : 12576,	'22' : 13536,	'23' : 14112,	'24' : 15264,	'25' : 15840,	'26' : 18336})
        self.tbsTable.append({	'0' : 712,	'1' : 936,	'2' : 1160,	'3' : 1480,	'4' : 1864,	'5' : 2280,	'6' : 2728,	'7' : 3240,	'8' : 3624,	'9' : 4136,	'10' : 4584,	'11' : 5352,	'12' : 5992,	'13' : 6712,	'14' : 7480,	'15' : 7992,	'16' : 8504,	'17' : 9528,	'18' : 10296,	'19' : 11064,	'20' : 12216,	'21' : 12960,	'22' : 14112,	'23' : 14688,	'24' : 15840,	'25' : 16416,	'26' : 19080})
        self.tbsTable.append({	'0' : 744,	'1' : 968,	'2' : 1192,	'3' : 1544,	'4' : 1928,	'5' : 2344,	'6' : 2792,	'7' : 3368,	'8' : 3752,	'9' : 4264,	'10' : 4776,	'11' : 5544,	'12' : 6200,	'13' : 6968,	'14' : 7736,	'15' : 8248,	'16' : 8760,	'17' : 9912,	'18' : 10680,	'19' : 11448,	'20' : 12576,	'21' : 13536,	'22' : 14688,	'23' : 15264,	'24' : 16416,	'25' : 16992,	'26' : 19848})
        self.tbsTable.append({	'0' : 776,	'1' : 1000,	'2' : 1256,	'3' : 1608,	'4' : 1992,	'5' : 2472,	'6' : 2984,	'7' : 3368,	'8' : 3880,	'9' : 4392,	'10' : 4968,	'11' : 5736,	'12' : 6456,	'13' : 7224,	'14' : 7992,	'15' : 8504,	'16' : 9144,	'17' : 10296,	'18' : 11064,	'19' : 12216,	'20' : 12960,	'21' : 14112,	'22' : 15264,	'23' : 15840,	'24' : 16992,	'25' : 17568,	'26' : 20616})
        self.tbsTable.append({	'0' : 776,	'1' : 1032,	'2' : 1288,	'3' : 1672,	'4' : 2088,	'5' : 2536,	'6' : 2984,	'7' : 3496,	'8' : 4008,	'9' : 4584,	'10' : 5160,	'11' : 5992,	'12' : 6712,	'13' : 7480,	'14' : 8248,	'15' : 8760,	'16' : 9528,	'17' : 10296,	'18' : 11448,	'19' : 12576,	'20' : 13536,	'21' : 14688,	'22' : 15840,	'23' : 16416,	'24' : 17568,	'25' : 18336,	'26' : 21384})
        self.tbsTable.append({	'0' : 808,	'1' : 1064,	'2' : 1320,	'3' : 1736,	'4' : 2152,	'5' : 2664,	'6' : 3112,	'7' : 3624,	'8' : 4264,	'9' : 4776,	'10' : 5352,	'11' : 5992,	'12' : 6712,	'13' : 7736,	'14' : 8504,	'15' : 9144,	'16' : 9912,	'17' : 10680,	'18' : 11832,	'19' : 12960,	'20' : 14112,	'21' : 15264,	'22' : 16416,	'23' : 16992,	'24' : 18336,	'25' : 19080,	'26' : 22152})
        self.tbsTable.append({	'0' : 840,	'1' : 1128,	'2' : 1384,	'3' : 1800,	'4' : 2216,	'5' : 2728,	'6' : 3240,	'7' : 3752,	'8' : 4392,	'9' : 4968,	'10' : 5544,	'11' : 6200,	'12' : 6968,	'13' : 7992,	'14' : 8760,	'15' : 9528,	'16' : 9912,	'17' : 11064,	'18' : 12216,	'19' : 13536,	'20' : 14688,	'21' : 15840,	'22' : 16992,	'23' : 17568,	'24' : 19080,	'25' : 19848,	'26' : 22920})
        self.tbsTable.append({	'0' : 872,	'1' : 1160,	'2' : 1416,	'3' : 1864,	'4' : 2280,	'5' : 2792,	'6' : 3368,	'7' : 3880,	'8' : 4584,	'9' : 5160,	'10' : 5736,	'11' : 6456,	'12' : 7224,	'13' : 8248,	'14' : 9144,	'15' : 9912,	'16' : 10296,	'17' : 11448,	'18' : 12576,	'19' : 13536,	'20' : 14688,	'21' : 15840,	'22' : 16992,	'23' : 18336,	'24' : 19848,	'25' : 20616,	'26' : 23688})
        self.tbsTable.append({	'0' : 904,	'1' : 1192,	'2' : 1480,	'3' : 1928,	'4' : 2344,	'5' : 2856,	'6' : 3496,	'7' : 4008,	'8' : 4584,	'9' : 5160,	'10' : 5736,	'11' : 6712,	'12' : 7480,	'13' : 8504,	'14' : 9528,	'15' : 10296,	'16' : 10680,	'17' : 11832,	'18' : 12960,	'19' : 14112,	'20' : 15264,	'21' : 16416,	'22' : 17568,	'23' : 19080,	'24' : 19848,	'25' : 20616,	'26' : 24496})
        self.tbsTable.append({	'0' : 936,	'1' : 1224,	'2' : 1544,	'3' : 1992,	'4' : 2408,	'5' : 2984,	'6' : 3496,	'7' : 4136,	'8' : 4776,	'9' : 5352,	'10' : 5992,	'11' : 6968,	'12' : 7736,	'13' : 8760,	'14' : 9912,	'15' : 10296,	'16' : 11064,	'17' : 12216,	'18' : 13536,	'19' : 14688,	'20' : 15840,	'21' : 16992,	'22' : 18336,	'23' : 19848,	'24' : 20616,	'25' : 21384,	'26' : 25456})
        self.tbsTable.append({	'0' : 968,	'1' : 1256,	'2' : 1544,	'3' : 2024,	'4' : 2472,	'5' : 3112,	'6' : 3624,	'7' : 4264,	'8' : 4968,	'9' : 5544,	'10' : 6200,	'11' : 6968,	'12' : 7992,	'13' : 9144,	'14' : 9912,	'15' : 10680,	'16' : 11448,	'17' : 12576,	'18' : 14112,	'19' : 15264,	'20' : 16416,	'21' : 17568,	'22' : 19080,	'23' : 19848,	'24' : 21384,	'25' : 22152,	'26' : 25456})
        self.tbsTable.append({	'0' : 1000,	'1' : 1288,	'2' : 1608,	'3' : 2088,	'4' : 2600,	'5' : 3112,	'6' : 3752,	'7' : 4392,	'8' : 4968,	'9' : 5736,	'10' : 6200,	'11' : 7224,	'12' : 8248,	'13' : 9144,	'14' : 10296,	'15' : 11064,	'16' : 11832,	'17' : 12960,	'18' : 14112,	'19' : 15264,	'20' : 16992,	'21' : 18336,	'22' : 19080,	'23' : 20616,	'24' : 22152,	'25' : 22920,	'26' : 26416})
        self.tbsTable.append({	'0' : 1032,	'1' : 1352,	'2' : 1672,	'3' : 2152,	'4' : 2664,	'5' : 3240,	'6' : 3880,	'7' : 4584,	'8' : 5160,	'9' : 5736,	'10' : 6456,	'11' : 7480,	'12' : 8504,	'13' : 9528,	'14' : 10680,	'15' : 11448,	'16' : 12216,	'17' : 13536,	'18' : 14688,	'19' : 15840,	'20' : 16992,	'21' : 18336,	'22' : 19848,	'23' : 21384,	'24' : 22920,	'25' : 23688,	'26' : 27376})
        self.tbsTable.append({	'0' : 1032,	'1' : 1384,	'2' : 1672,	'3' : 2216,	'4' : 2728,	'5' : 3368,	'6' : 4008,	'7' : 4584,	'8' : 5352,	'9' : 5992,	'10' : 6712,	'11' : 7736,	'12' : 8760,	'13' : 9912,	'14' : 11064,	'15' : 11832,	'16' : 12216,	'17' : 13536,	'18' : 15264,	'19' : 16416,	'20' : 17568,	'21' : 19080,	'22' : 20616,	'23' : 22152,	'24' : 22920,	'25' : 24496,	'26' : 28336})
        self.tbsTable.append({	'0' : 1064,	'1' : 1416,	'2' : 1736,	'3' : 2280,	'4' : 2792,	'5' : 3496,	'6' : 4136,	'7' : 4776,	'8' : 5544,	'9' : 6200,	'10' : 6712,	'11' : 7736,	'12' : 8760,	'13' : 9912,	'14' : 11064,	'15' : 11832,	'16' : 12576,	'17' : 14112,	'18' : 15264,	'19' : 16992,	'20' : 18336,	'21' : 19848,	'22' : 21384,	'23' : 22152,	'24' : 23688,	'25' : 24496,	'26' : 29296})
        self.tbsTable.append({	'0' : 1096,	'1' : 1416,	'2' : 1800,	'3' : 2344,	'4' : 2856,	'5' : 3496,	'6' : 4136,	'7' : 4968,	'8' : 5544,	'9' : 6200,	'10' : 6968,	'11' : 7992,	'12' : 9144,	'13' : 10296,	'14' : 11448,	'15' : 12216,	'16' : 12960,	'17' : 14688,	'18' : 15840,	'19' : 16992,	'20' : 18336,	'21' : 19848,	'22' : 21384,	'23' : 22920,	'24' : 24496,	'25' : 25456,	'26' : 29296})
        self.tbsTable.append({	'0' : 1128,	'1' : 1480,	'2' : 1800,	'3' : 2408,	'4' : 2984,	'5' : 3624,	'6' : 4264,	'7' : 4968,	'8' : 5736,	'9' : 6456,	'10' : 7224,	'11' : 8248,	'12' : 9528,	'13' : 10680,	'14' : 11832,	'15' : 12576,	'16' : 13536,	'17' : 14688,	'18' : 16416,	'19' : 17568,	'20' : 19080,	'21' : 20616,	'22' : 22152,	'23' : 23688,	'24' : 25456,	'25' : 26416,	'26' : 30576})
        self.tbsTable.append({	'0' : 1160,	'1' : 1544,	'2' : 1864,	'3' : 2472,	'4' : 2984,	'5' : 3752,	'6' : 4392,	'7' : 5160,	'8' : 5992,	'9' : 6712,	'10' : 7480,	'11' : 8504,	'12' : 9528,	'13' : 10680,	'14' : 12216,	'15' : 12960,	'16' : 13536,	'17' : 15264,	'18' : 16416,	'19' : 18336,	'20' : 19848,	'21' : 21384,	'22' : 22920,	'23' : 24496,	'24' : 25456,	'25' : 26416,	'26' : 30576})
        self.tbsTable.append({	'0' : 1192,	'1' : 1544,	'2' : 1928,	'3' : 2536,	'4' : 3112,	'5' : 3752,	'6' : 4584,	'7' : 5352,	'8' : 5992,	'9' : 6712,	'10' : 7480,	'11' : 8760,	'12' : 9912,	'13' : 11064,	'14' : 12216,	'15' : 12960,	'16' : 14112,	'17' : 15264,	'18' : 16992,	'19' : 18336,	'20' : 19848,	'21' : 21384,	'22' : 22920,	'23' : 24496,	'24' : 26416,	'25' : 27376,	'26' : 31704})
        self.tbsTable.append({	'0' : 1224,	'1' : 1608,	'2' : 1992,	'3' : 2536,	'4' : 3112,	'5' : 3880,	'6' : 4584,	'7' : 5352,	'8' : 6200,	'9' : 6968,	'10' : 7736,	'11' : 8760,	'12' : 9912,	'13' : 11448,	'14' : 12576,	'15' : 13536,	'16' : 14112,	'17' : 15840,	'18' : 17568,	'19' : 19080,	'20' : 20616,	'21' : 22152,	'22' : 23688,	'23' : 25456,	'24' : 26416,	'25' : 28336,	'26' : 32856})
        self.tbsTable.append({	'0' : 1256,	'1' : 1608,	'2' : 2024,	'3' : 2600,	'4' : 3240,	'5' : 4008,	'6' : 4776,	'7' : 5544,	'8' : 6200,	'9' : 6968,	'10' : 7992,	'11' : 9144,	'12' : 10296,	'13' : 11448,	'14' : 12960,	'15' : 13536,	'16' : 14688,	'17' : 16416,	'18' : 17568,	'19' : 19080,	'20' : 20616,	'21' : 22920,	'22' : 24496,	'23' : 25456,	'24' : 27376,	'25' : 28336,	'26' : 32856})
        self.tbsTable.append({	'0' : 1256,	'1' : 1672,	'2' : 2088,	'3' : 2664,	'4' : 3240,	'5' : 4008,	'6' : 4776,	'7' : 5736,	'8' : 6456,	'9' : 7224,	'10' : 7992,	'11' : 9144,	'12' : 10680,	'13' : 11832,	'14' : 12960,	'15' : 14112,	'16' : 14688,	'17' : 16416,	'18' : 18336,	'19' : 19848,	'20' : 21384,	'21' : 22920,	'22' : 24496,	'23' : 26416,	'24' : 28336,	'25' : 29296,	'26' : 34008})
        self.tbsTable.append({	'0' : 1288,	'1' : 1736,	'2' : 2088,	'3' : 2728,	'4' : 3368,	'5' : 4136,	'6' : 4968,	'7' : 5736,	'8' : 6456,	'9' : 7480,	'10' : 8248,	'11' : 9528,	'12' : 10680,	'13' : 12216,	'14' : 13536,	'15' : 14688,	'16' : 15264,	'17' : 16992,	'18' : 18336,	'19' : 20616,	'20' : 22152,	'21' : 23688,	'22' : 25456,	'23' : 27376,	'24' : 28336,	'25' : 29296,	'26' : 35160})
        self.tbsTable.append({	'0' : 1320,	'1' : 1736,	'2' : 2152,	'3' : 2792,	'4' : 3496,	'5' : 4264,	'6' : 4968,	'7' : 5992,	'8' : 6712,	'9' : 7480,	'10' : 8504,	'11' : 9528,	'12' : 11064,	'13' : 12216,	'14' : 13536,	'15' : 14688,	'16' : 15840,	'17' : 17568,	'18' : 19080,	'19' : 20616,	'20' : 22152,	'21' : 24496,	'22' : 25456,	'23' : 27376,	'24' : 29296,	'25' : 30576,	'26' : 35160})
        self.tbsTable.append({	'0' : 1352,	'1' : 1800,	'2' : 2216,	'3' : 2856,	'4' : 3496,	'5' : 4392,	'6' : 5160,	'7' : 5992,	'8' : 6968,	'9' : 7736,	'10' : 8504,	'11' : 9912,	'12' : 11064,	'13' : 12576,	'14' : 14112,	'15' : 15264,	'16' : 15840,	'17' : 17568,	'18' : 19080,	'19' : 21384,	'20' : 22920,	'21' : 24496,	'22' : 26416,	'23' : 28336,	'24' : 29296,	'25' : 31704,	'26' : 36696})
        self.tbsTable.append({	'0' : 1384,	'1' : 1800,	'2' : 2216,	'3' : 2856,	'4' : 3624,	'5' : 4392,	'6' : 5160,	'7' : 6200,	'8' : 6968,	'9' : 7992,	'10' : 8760,	'11' : 9912,	'12' : 11448,	'13' : 12960,	'14' : 14112,	'15' : 15264,	'16' : 16416,	'17' : 18336,	'18' : 19848,	'19' : 21384,	'20' : 22920,	'21' : 25456,	'22' : 27376,	'23' : 28336,	'24' : 30576,	'25' : 31704,	'26' : 36696})
        self.tbsTable.append({	'0' : 1416,	'1' : 1864,	'2' : 2280,	'3' : 2984,	'4' : 3624,	'5' : 4584,	'6' : 5352,	'7' : 6200,	'8' : 7224,	'9' : 7992,	'10' : 9144,	'11' : 10296,	'12' : 11832,	'13' : 12960,	'14' : 14688,	'15' : 15840,	'16' : 16416,	'17' : 18336,	'18' : 19848,	'19' : 22152,	'20' : 23688,	'21' : 25456,	'22' : 27376,	'23' : 29296,	'24' : 31704,	'25' : 32856,	'26' : 37888})
        self.tbsTable.append({	'0' : 1416,	'1' : 1864,	'2' : 2344,	'3' : 2984,	'4' : 3752,	'5' : 4584,	'6' : 5352,	'7' : 6456,	'8' : 7224,	'9' : 8248,	'10' : 9144,	'11' : 10680,	'12' : 11832,	'13' : 13536,	'14' : 14688,	'15' : 15840,	'16' : 16992,	'17' : 19080,	'18' : 20616,	'19' : 22152,	'20' : 24496,	'21' : 26416,	'22' : 28336,	'23' : 29296,	'24' : 31704,	'25' : 32856,	'26' : 37888})
        self.tbsTable.append({	'0' : 1480,	'1' : 1928,	'2' : 2344,	'3' : 3112,	'4' : 3752,	'5' : 4776,	'6' : 5544,	'7' : 6456,	'8' : 7480,	'9' : 8248,	'10' : 9144,	'11' : 10680,	'12' : 12216,	'13' : 13536,	'14' : 15264,	'15' : 16416,	'16' : 16992,	'17' : 19080,	'18' : 21384,	'19' : 22920,	'20' : 24496,	'21' : 26416,	'22' : 28336,	'23' : 30576,	'24' : 32856,	'25' : 34008,	'26' : 39232})
        self.tbsTable.append({	'0' : 1480,	'1' : 1992,	'2' : 2408,	'3' : 3112,	'4' : 3880,	'5' : 4776,	'6' : 5736,	'7' : 6712,	'8' : 7480,	'9' : 8504,	'10' : 9528,	'11' : 11064,	'12' : 12216,	'13' : 14112,	'14' : 15264,	'15' : 16416,	'16' : 17568,	'17' : 19848,	'18' : 21384,	'19' : 22920,	'20' : 25456,	'21' : 27376,	'22' : 29296,	'23' : 30576,	'24' : 32856,	'25' : 34008,	'26' : 40576})
        self.tbsTable.append({	'0' : 1544,	'1' : 1992,	'2' : 2472,	'3' : 3240,	'4' : 4008,	'5' : 4776,	'6' : 5736,	'7' : 6712,	'8' : 7736,	'9' : 8760,	'10' : 9528,	'11' : 11064,	'12' : 12576,	'13' : 14112,	'14' : 15840,	'15' : 16992,	'16' : 17568,	'17' : 19848,	'18' : 22152,	'19' : 23688,	'20' : 25456,	'21' : 27376,	'22' : 29296,	'23' : 31704,	'24' : 34008,	'25' : 35160,	'26' : 40576})
        self.tbsTable.append({	'0' : 1544,	'1' : 2024,	'2' : 2536,	'3' : 3240,	'4' : 4008,	'5' : 4968,	'6' : 5992,	'7' : 6712,	'8' : 7736,	'9' : 8760,	'10' : 9912,	'11' : 11448,	'12' : 12576,	'13' : 14688,	'14' : 15840,	'15' : 16992,	'16' : 18336,	'17' : 20616,	'18' : 22152,	'19' : 24496,	'20' : 26416,	'21' : 28336,	'22' : 30576,	'23' : 31704,	'24' : 34008,	'25' : 35160,	'26' : 40576})
        self.tbsTable.append({	'0' : 1608,	'1' : 2088,	'2' : 2536,	'3' : 3368,	'4' : 4136,	'5' : 4968,	'6' : 5992,	'7' : 6968,	'8' : 7992,	'9' : 9144,	'10' : 9912,	'11' : 11448,	'12' : 12960,	'13' : 14688,	'14' : 16416,	'15' : 17568,	'16' : 18336,	'17' : 20616,	'18' : 22920,	'19' : 24496,	'20' : 26416,	'21' : 28336,	'22' : 30576,	'23' : 32856,	'24' : 35160,	'25' : 36696,	'26' : 42368})
        self.tbsTable.append({	'0' : 1608,	'1' : 2088,	'2' : 2600,	'3' : 3368,	'4' : 4136,	'5' : 5160,	'6' : 5992,	'7' : 6968,	'8' : 7992,	'9' : 9144,	'10' : 10296,	'11' : 11832,	'12' : 12960,	'13' : 14688,	'14' : 16416,	'15' : 17568,	'16' : 19080,	'17' : 20616,	'18' : 22920,	'19' : 25456,	'20' : 27376,	'21' : 29296,	'22' : 31704,	'23' : 32856,	'24' : 35160,	'25' : 36696,	'26' : 42368})
        self.tbsTable.append({	'0' : 1608,	'1' : 2152,	'2' : 2664,	'3' : 3496,	'4' : 4264,	'5' : 5160,	'6' : 6200,	'7' : 7224,	'8' : 8248,	'9' : 9144,	'10' : 10296,	'11' : 11832,	'12' : 13536,	'13' : 15264,	'14' : 16992,	'15' : 18336,	'16' : 19080,	'17' : 21384,	'18' : 23688,	'19' : 25456,	'20' : 27376,	'21' : 29296,	'22' : 31704,	'23' : 34008,	'24' : 36696,	'25' : 37888,	'26' : 43816})
        self.tbsTable.append({	'0' : 1672,	'1' : 2152,	'2' : 2664,	'3' : 3496,	'4' : 4264,	'5' : 5352,	'6' : 6200,	'7' : 7224,	'8' : 8504,	'9' : 9528,	'10' : 10680,	'11' : 12216,	'12' : 13536,	'13' : 15264,	'14' : 16992,	'15' : 18336,	'16' : 19848,	'17' : 21384,	'18' : 23688,	'19' : 25456,	'20' : 28336,	'21' : 30576,	'22' : 32856,	'23' : 34008,	'24' : 36696,	'25' : 37888,	'26' : 43816})
        self.tbsTable.append({	'0' : 1672,	'1' : 2216,	'2' : 2728,	'3' : 3624,	'4' : 4392,	'5' : 5352,	'6' : 6456,	'7' : 7480,	'8' : 8504,	'9' : 9528,	'10' : 10680,	'11' : 12216,	'12' : 14112,	'13' : 15840,	'14' : 17568,	'15' : 18336,	'16' : 19848,	'17' : 22152,	'18' : 24496,	'19' : 26416,	'20' : 28336,	'21' : 30576,	'22' : 32856,	'23' : 35160,	'24' : 36696,	'25' : 39232,	'26' : 45352})
        self.tbsTable.append({	'0' : 1736,	'1' : 2280,	'2' : 2792,	'3' : 3624,	'4' : 4392,	'5' : 5544,	'6' : 6456,	'7' : 7480,	'8' : 8760,	'9' : 9912,	'10' : 11064,	'11' : 12576,	'12' : 14112,	'13' : 15840,	'14' : 17568,	'15' : 19080,	'16' : 19848,	'17' : 22152,	'18' : 24496,	'19' : 26416,	'20' : 29296,	'21' : 31704,	'22' : 34008,	'23' : 35160,	'24' : 37888,	'25' : 39232,	'26' : 45352})
        self.tbsTable.append({	'0' : 1736,	'1' : 2280,	'2' : 2856,	'3' : 3624,	'4' : 4584,	'5' : 5544,	'6' : 6456,	'7' : 7736,	'8' : 8760,	'9' : 9912,	'10' : 11064,	'11' : 12576,	'12' : 14112,	'13' : 16416,	'14' : 18336,	'15' : 19080,	'16' : 20616,	'17' : 22920,	'18' : 24496,	'19' : 27376,	'20' : 29296,	'21' : 31704,	'22' : 34008,	'23' : 36696,	'24' : 37888,	'25' : 40576,	'26' : 46888})
        self.tbsTable.append({	'0' : 1800,	'1' : 2344,	'2' : 2856,	'3' : 3752,	'4' : 4584,	'5' : 5736,	'6' : 6712,	'7' : 7736,	'8' : 9144,	'9' : 10296,	'10' : 11448,	'11' : 12960,	'12' : 14688,	'13' : 16416,	'14' : 18336,	'15' : 19848,	'16' : 20616,	'17' : 22920,	'18' : 25456,	'19' : 27376,	'20' : 29296,	'21' : 31704,	'22' : 34008,	'23' : 36696,	'24' : 39232,	'25' : 40576,	'26' : 46888})
        self.tbsTable.append({	'0' : 1800,	'1' : 2344,	'2' : 2856,	'3' : 3752,	'4' : 4584,	'5' : 5736,	'6' : 6712,	'7' : 7992,	'8' : 9144,	'9' : 10296,	'10' : 11448,	'11' : 12960,	'12' : 14688,	'13' : 16992,	'14' : 18336,	'15' : 19848,	'16' : 21384,	'17' : 23688,	'18' : 25456,	'19' : 28336,	'20' : 30576,	'21' : 32856,	'22' : 35160,	'23' : 37888,	'24' : 39232,	'25' : 40576,	'26' : 48936})
        self.tbsTable.append({	'0' : 1800,	'1' : 2408,	'2' : 2984,	'3' : 3880,	'4' : 4776,	'5' : 5736,	'6' : 6968,	'7' : 7992,	'8' : 9144,	'9' : 10296,	'10' : 11448,	'11' : 13536,	'12' : 15264,	'13' : 16992,	'14' : 19080,	'15' : 20616,	'16' : 21384,	'17' : 23688,	'18' : 26416,	'19' : 28336,	'20' : 30576,	'21' : 32856,	'22' : 35160,	'23' : 37888,	'24' : 40576,	'25' : 42368,	'26' : 48936})
        self.tbsTable.append({	'0' : 1864,	'1' : 2472,	'2' : 2984,	'3' : 3880,	'4' : 4776,	'5' : 5992,	'6' : 6968,	'7' : 8248,	'8' : 9528,	'9' : 10680,	'10' : 11832,	'11' : 13536,	'12' : 15264,	'13' : 16992,	'14' : 19080,	'15' : 20616,	'16' : 22152,	'17' : 24496,	'18' : 26416,	'19' : 29296,	'20' : 31704,	'21' : 34008,	'22' : 36696,	'23' : 37888,	'24' : 40576,	'25' : 42368,	'26' : 48936})
        self.tbsTable.append({	'0' : 1864,	'1' : 2472,	'2' : 3112,	'3' : 4008,	'4' : 4968,	'5' : 5992,	'6' : 6968,	'7' : 8248,	'8' : 9528,	'9' : 10680,	'10' : 11832,	'11' : 13536,	'12' : 15264,	'13' : 17568,	'14' : 19848,	'15' : 20616,	'16' : 22152,	'17' : 24496,	'18' : 27376,	'19' : 29296,	'20' : 31704,	'21' : 34008,	'22' : 36696,	'23' : 39232,	'24' : 42368,	'25' : 43816,	'26' : 51024})
        self.tbsTable.append({	'0' : 1928,	'1' : 2536,	'2' : 3112,	'3' : 4008,	'4' : 4968,	'5' : 5992,	'6' : 7224,	'7' : 8504,	'8' : 9528,	'9' : 11064,	'10' : 12216,	'11' : 14112,	'12' : 15840,	'13' : 17568,	'14' : 19848,	'15' : 21384,	'16' : 22152,	'17' : 24496,	'18' : 27376,	'19' : 29296,	'20' : 31704,	'21' : 35160,	'22' : 36696,	'23' : 39232,	'24' : 42368,	'25' : 43816,	'26' : 51024})
        self.tbsTable.append({	'0' : 1928,	'1' : 2536,	'2' : 3112,	'3' : 4136,	'4' : 4968,	'5' : 6200,	'6' : 7224,	'7' : 8504,	'8' : 9912,	'9' : 11064,	'10' : 12216,	'11' : 14112,	'12' : 15840,	'13' : 18336,	'14' : 19848,	'15' : 21384,	'16' : 22920,	'17' : 25456,	'18' : 27376,	'19' : 30576,	'20' : 32856,	'21' : 35160,	'22' : 37888,	'23' : 40576,	'24' : 42368,	'25' : 43816,	'26' : 52752})
        self.tbsTable.append({	'0' : 1992,	'1' : 2600,	'2' : 3240,	'3' : 4136,	'4' : 5160,	'5' : 6200,	'6' : 7480,	'7' : 8760,	'8' : 9912,	'9' : 11064,	'10' : 12576,	'11' : 14112,	'12' : 16416,	'13' : 18336,	'14' : 20616,	'15' : 22152,	'16' : 22920,	'17' : 25456,	'18' : 28336,	'19' : 30576,	'20' : 32856,	'21' : 35160,	'22' : 37888,	'23' : 40576,	'24' : 43816,	'25' : 45352,	'26' : 52752})
        self.tbsTable.append({	'0' : 1992,	'1' : 2600,	'2' : 3240,	'3' : 4264,	'4' : 5160,	'5' : 6200,	'6' : 7480,	'7' : 8760,	'8' : 9912,	'9' : 11448,	'10' : 12576,	'11' : 14688,	'12' : 16416,	'13' : 18336,	'14' : 20616,	'15' : 22152,	'16' : 23688,	'17' : 26416,	'18' : 28336,	'19' : 30576,	'20' : 34008,	'21' : 36696,	'22' : 39232,	'23' : 40576,	'24' : 43816,	'25' : 45352,	'26' : 52752})
        self.tbsTable.append({	'0' : 2024,	'1' : 2664,	'2' : 3240,	'3' : 4264,	'4' : 5160,	'5' : 6456,	'6' : 7736,	'7' : 8760,	'8' : 10296,	'9' : 11448,	'10' : 12960,	'11' : 14688,	'12' : 16416,	'13' : 19080,	'14' : 20616,	'15' : 22152,	'16' : 23688,	'17' : 26416,	'18' : 29296,	'19' : 31704,	'20' : 34008,	'21' : 36696,	'22' : 39232,	'23' : 42368,	'24' : 45352,	'25' : 46888,	'26' : 55056})
        self.tbsTable.append({	'0' : 2088,	'1' : 2728,	'2' : 3368,	'3' : 4392,	'4' : 5352,	'5' : 6456,	'6' : 7736,	'7' : 9144,	'8' : 10296,	'9' : 11832,	'10' : 12960,	'11' : 14688,	'12' : 16992,	'13' : 19080,	'14' : 21384,	'15' : 22920,	'16' : 24496,	'17' : 26416,	'18' : 29296,	'19' : 31704,	'20' : 34008,	'21' : 36696,	'22' : 40576,	'23' : 42368,	'24' : 45352,	'25' : 46888,	'26' : 55056})
        self.tbsTable.append({	'0' : 2088,	'1' : 2728,	'2' : 3368,	'3' : 4392,	'4' : 5352,	'5' : 6712,	'6' : 7736,	'7' : 9144,	'8' : 10680,	'9' : 11832,	'10' : 12960,	'11' : 15264,	'12' : 16992,	'13' : 19080,	'14' : 21384,	'15' : 22920,	'16' : 24496,	'17' : 27376,	'18' : 29296,	'19' : 32856,	'20' : 35160,	'21' : 37888,	'22' : 40576,	'23' : 43816,	'24' : 45352,	'25' : 46888,	'26' : 55056})
        self.tbsTable.append({	'0' : 2088,	'1' : 2792,	'2' : 3368,	'3' : 4392,	'4' : 5544,	'5' : 6712,	'6' : 7992,	'7' : 9144,	'8' : 10680,	'9' : 11832,	'10' : 13536,	'11' : 15264,	'12' : 17568,	'13' : 19848,	'14' : 22152,	'15' : 23688,	'16' : 24496,	'17' : 27376,	'18' : 30576,	'19' : 32856,	'20' : 35160,	'21' : 37888,	'22' : 40576,	'23' : 43816,	'24' : 46888,	'25' : 48936,	'26' : 55056})
        self.tbsTable.append({	'0' : 2152,	'1' : 2792,	'2' : 3496,	'3' : 4584,	'4' : 5544,	'5' : 6712,	'6' : 7992,	'7' : 9528,	'8' : 10680,	'9' : 12216,	'10' : 13536,	'11' : 15840,	'12' : 17568,	'13' : 19848,	'14' : 22152,	'15' : 23688,	'16' : 25456,	'17' : 27376,	'18' : 30576,	'19' : 32856,	'20' : 35160,	'21' : 39232,	'22' : 42368,	'23' : 43816,	'24' : 46888,	'25' : 48936,	'26' : 57336})
        self.tbsTable.append({	'0' : 2152,	'1' : 2856,	'2' : 3496,	'3' : 4584,	'4' : 5544,	'5' : 6968,	'6' : 8248,	'7' : 9528,	'8' : 11064,	'9' : 12216,	'10' : 13536,	'11' : 15840,	'12' : 17568,	'13' : 19848,	'14' : 22152,	'15' : 23688,	'16' : 25456,	'17' : 28336,	'18' : 30576,	'19' : 34008,	'20' : 36696,	'21' : 39232,	'22' : 42368,	'23' : 45352,	'24' : 46888,	'25' : 48936,	'26' : 57336})
        self.tbsTable.append({	'0' : 2216,	'1' : 2856,	'2' : 3496,	'3' : 4584,	'4' : 5736,	'5' : 6968,	'6' : 8248,	'7' : 9528,	'8' : 11064,	'9' : 12576,	'10' : 14112,	'11' : 15840,	'12' : 18336,	'13' : 20616,	'14' : 22920,	'15' : 24496,	'16' : 25456,	'17' : 28336,	'18' : 31704,	'19' : 34008,	'20' : 36696,	'21' : 39232,	'22' : 42368,	'23' : 45352,	'24' : 48936,	'25' : 51024,	'26' : 57336})
        self.tbsTable.append({	'0' : 2216,	'1' : 2856,	'2' : 3624,	'3' : 4776,	'4' : 5736,	'5' : 6968,	'6' : 8248,	'7' : 9912,	'8' : 11064,	'9' : 12576,	'10' : 14112,	'11' : 16416,	'12' : 18336,	'13' : 20616,	'14' : 22920,	'15' : 24496,	'16' : 26416,	'17' : 29296,	'18' : 31704,	'19' : 34008,	'20' : 36696,	'21' : 40576,	'22' : 43816,	'23' : 45352,	'24' : 48936,	'25' : 51024,	'26' : 59256})
        self.tbsTable.append({	'0' : 2280,	'1' : 2984,	'2' : 3624,	'3' : 4776,	'4' : 5736,	'5' : 7224,	'6' : 8504,	'7' : 9912,	'8' : 11448,	'9' : 12960,	'10' : 14112,	'11' : 16416,	'12' : 18336,	'13' : 20616,	'14' : 22920,	'15' : 24496,	'16' : 26416,	'17' : 29296,	'18' : 31704,	'19' : 35160,	'20' : 37888,	'21' : 40576,	'22' : 43816,	'23' : 46888,	'24' : 48936,	'25' : 51024,	'26' : 59256})
        self.tbsTable.append({	'0' : 2280,	'1' : 2984,	'2' : 3624,	'3' : 4776,	'4' : 5992,	'5' : 7224,	'6' : 8504,	'7' : 9912,	'8' : 11448,	'9' : 12960,	'10' : 14688,	'11' : 16416,	'12' : 19080,	'13' : 21384,	'14' : 23688,	'15' : 25456,	'16' : 26416,	'17' : 29296,	'18' : 32856,	'19' : 35160,	'20' : 37888,	'21' : 40576,	'22' : 43816,	'23' : 46888,	'24' : 51024,	'25' : 52752,	'26' : 59256})
        self.tbsTable.append({	'0' : 2280,	'1' : 2984,	'2' : 3752,	'3' : 4776,	'4' : 5992,	'5' : 7224,	'6' : 8760,	'7' : 10296,	'8' : 11448,	'9' : 12960,	'10' : 14688,	'11' : 16992,	'12' : 19080,	'13' : 21384,	'14' : 23688,	'15' : 25456,	'16' : 27376,	'17' : 30576,	'18' : 32856,	'19' : 35160,	'20' : 39232,	'21' : 42368,	'22' : 45352,	'23' : 46888,	'24' : 51024,	'25' : 52752,	'26' : 61664})
        self.tbsTable.append({	'0' : 2344,	'1' : 3112,	'2' : 3752,	'3' : 4968,	'4' : 5992,	'5' : 7480,	'6' : 8760,	'7' : 10296,	'8' : 11832,	'9' : 13536,	'10' : 14688,	'11' : 16992,	'12' : 19080,	'13' : 21384,	'14' : 24496,	'15' : 25456,	'16' : 27376,	'17' : 30576,	'18' : 32856,	'19' : 36696,	'20' : 39232,	'21' : 42368,	'22' : 45352,	'23' : 48936,	'24' : 51024,	'25' : 52752,	'26' : 61664})
        self.tbsTable.append({	'0' : 2344,	'1' : 3112,	'2' : 3880,	'3' : 4968,	'4' : 5992,	'5' : 7480,	'6' : 8760,	'7' : 10296,	'8' : 11832,	'9' : 13536,	'10' : 14688,	'11' : 16992,	'12' : 19080,	'13' : 22152,	'14' : 24496,	'15' : 26416,	'16' : 27376,	'17' : 30576,	'18' : 34008,	'19' : 36696,	'20' : 39232,	'21' : 42368,	'22' : 45352,	'23' : 48936,	'24' : 52752,	'25' : 55056,	'26' : 61664})
        self.tbsTable.append({	'0' : 2408,	'1' : 3112,	'2' : 3880,	'3' : 4968,	'4' : 6200,	'5' : 7480,	'6' : 9144,	'7' : 10680,	'8' : 12216,	'9' : 13536,	'10' : 15264,	'11' : 17568,	'12' : 19848,	'13' : 22152,	'14' : 24496,	'15' : 26416,	'16' : 28336,	'17' : 30576,	'18' : 34008,	'19' : 36696,	'20' : 40576,	'21' : 43816,	'22' : 46888,	'23' : 48936,	'24' : 52752,	'25' : 55056,	'26' : 63776})
        self.tbsTable.append({	'0' : 2408,	'1' : 3240,	'2' : 3880,	'3' : 5160,	'4' : 6200,	'5' : 7736,	'6' : 9144,	'7' : 10680,	'8' : 12216,	'9' : 13536,	'10' : 15264,	'11' : 17568,	'12' : 19848,	'13' : 22152,	'14' : 25456,	'15' : 26416,	'16' : 28336,	'17' : 31704,	'18' : 34008,	'19' : 37888,	'20' : 40576,	'21' : 43816,	'22' : 46888,	'23' : 51024,	'24' : 52752,	'25' : 55056,	'26' : 63776})
        self.tbsTable.append({	'0' : 2472,	'1' : 3240,	'2' : 4008,	'3' : 5160,	'4' : 6200,	'5' : 7736,	'6' : 9144,	'7' : 10680,	'8' : 12216,	'9' : 14112,	'10' : 15264,	'11' : 17568,	'12' : 19848,	'13' : 22920,	'14' : 25456,	'15' : 27376,	'16' : 28336,	'17' : 31704,	'18' : 35160,	'19' : 37888,	'20' : 40576,	'21' : 43816,	'22' : 46888,	'23' : 51024,	'24' : 52752,	'25' : 55056,	'26' : 63776})
        self.tbsTable.append({	'0' : 2472,	'1' : 3240,	'2' : 4008,	'3' : 5160,	'4' : 6456,	'5' : 7736,	'6' : 9144,	'7' : 11064,	'8' : 12576,	'9' : 14112,	'10' : 15840,	'11' : 18336,	'12' : 20616,	'13' : 22920,	'14' : 25456,	'15' : 27376,	'16' : 29296,	'17' : 31704,	'18' : 35160,	'19' : 37888,	'20' : 42368,	'21' : 45352,	'22' : 48936,	'23' : 51024,	'24' : 55056,	'25' : 57336,	'26' : 66592})
        self.tbsTable.append({	'0' : 2536,	'1' : 3240,	'2' : 4008,	'3' : 5352,	'4' : 6456,	'5' : 7992,	'6' : 9528,	'7' : 11064,	'8' : 12576,	'9' : 14112,	'10' : 15840,	'11' : 18336,	'12' : 20616,	'13' : 22920,	'14' : 25456,	'15' : 27376,	'16' : 29296,	'17' : 32856,	'18' : 35160,	'19' : 39232,	'20' : 42368,	'21' : 45352,	'22' : 48936,	'23' : 51024,	'24' : 55056,	'25' : 57336,	'26' : 66592})
        self.tbsTable.append({	'0' : 2536,	'1' : 3368,	'2' : 4136,	'3' : 5352,	'4' : 6456,	'5' : 7992,	'6' : 9528,	'7' : 11064,	'8' : 12576,	'9' : 14112,	'10' : 15840,	'11' : 18336,	'12' : 20616,	'13' : 23688,	'14' : 26416,	'15' : 28336,	'16' : 29296,	'17' : 32856,	'18' : 36696,	'19' : 39232,	'20' : 42368,	'21' : 45352,	'22' : 48936,	'23' : 52752,	'24' : 55056,	'25' : 57336,	'26' : 66592})
        self.tbsTable.append({	'0' : 2536,	'1' : 3368,	'2' : 4136,	'3' : 5352,	'4' : 6456,	'5' : 7992,	'6' : 9528,	'7' : 11448,	'8' : 12960,	'9' : 14688,	'10' : 16416,	'11' : 18336,	'12' : 21384,	'13' : 23688,	'14' : 26416,	'15' : 28336,	'16' : 30576,	'17' : 32856,	'18' : 36696,	'19' : 39232,	'20' : 42368,	'21' : 46888,	'22' : 48936,	'23' : 52752,	'24' : 57336,	'25' : 59256,	'26' : 68808})
        self.tbsTable.append({	'0' : 2600,	'1' : 3368,	'2' : 4136,	'3' : 5352,	'4' : 6712,	'5' : 8248,	'6' : 9528,	'7' : 11448,	'8' : 12960,	'9' : 14688,	'10' : 16416,	'11' : 19080,	'12' : 21384,	'13' : 23688,	'14' : 26416,	'15' : 28336,	'16' : 30576,	'17' : 34008,	'18' : 36696,	'19' : 40576,	'20' : 43816,	'21' : 46888,	'22' : 51024,	'23' : 52752,	'24' : 57336,	'25' : 59256,	'26' : 68808})
        self.tbsTable.append({	'0' : 2600,	'1' : 3496,	'2' : 4264,	'3' : 5544,	'4' : 6712,	'5' : 8248,	'6' : 9912,	'7' : 11448,	'8' : 12960,	'9' : 14688,	'10' : 16416,	'11' : 19080,	'12' : 21384,	'13' : 24496,	'14' : 27376,	'15' : 29296,	'16' : 30576,	'17' : 34008,	'18' : 37888,	'19' : 40576,	'20' : 43816,	'21' : 46888,	'22' : 51024,	'23' : 55056,	'24' : 57336,	'25' : 59256,	'26' : 68808})
        self.tbsTable.append({	'0' : 2664,	'1' : 3496,	'2' : 4264,	'3' : 5544,	'4' : 6712,	'5' : 8248,	'6' : 9912,	'7' : 11448,	'8' : 13536,	'9' : 15264,	'10' : 16992,	'11' : 19080,	'12' : 21384,	'13' : 24496,	'14' : 27376,	'15' : 29296,	'16' : 30576,	'17' : 34008,	'18' : 37888,	'19' : 40576,	'20' : 43816,	'21' : 46888,	'22' : 51024,	'23' : 55056,	'24' : 57336,	'25' : 61664,	'26' : 71112})
        self.tbsTable.append({	'0' : 2664,	'1' : 3496,	'2' : 4264,	'3' : 5544,	'4' : 6968,	'5' : 8504,	'6' : 9912,	'7' : 11832,	'8' : 13536,	'9' : 15264,	'10' : 16992,	'11' : 19080,	'12' : 22152,	'13' : 24496,	'14' : 27376,	'15' : 29296,	'16' : 31704,	'17' : 35160,	'18' : 37888,	'19' : 40576,	'20' : 45352,	'21' : 48936,	'22' : 51024,	'23' : 55056,	'24' : 59256,	'25' : 61664,	'26' : 71112})
        self.tbsTable.append({	'0' : 2728,	'1' : 3496,	'2' : 4392,	'3' : 5736,	'4' : 6968,	'5' : 8504,	'6' : 10296,	'7' : 11832,	'8' : 13536,	'9' : 15264,	'10' : 16992,	'11' : 19848,	'12' : 22152,	'13' : 25456,	'14' : 28336,	'15' : 29296,	'16' : 31704,	'17' : 35160,	'18' : 37888,	'19' : 42368,	'20' : 45352,	'21' : 48936,	'22' : 52752,	'23' : 55056,	'24' : 59256,	'25' : 61664,	'26' : 71112})
        self.tbsTable.append({	'0' : 2728,	'1' : 3624,	'2' : 4392,	'3' : 5736,	'4' : 6968,	'5' : 8760,	'6' : 10296,	'7' : 11832,	'8' : 13536,	'9' : 15264,	'10' : 16992,	'11' : 19848,	'12' : 22152,	'13' : 25456,	'14' : 28336,	'15' : 30576,	'16' : 31704,	'17' : 35160,	'18' : 39232,	'19' : 42368,	'20' : 45352,	'21' : 48936,	'22' : 52752,	'23' : 57336,	'24' : 59256,	'25' : 61664,	'26' : 73712})
        self.tbsTable.append({	'0' : 2728,	'1' : 3624,	'2' : 4392,	'3' : 5736,	'4' : 6968,	'5' : 8760,	'6' : 10296,	'7' : 12216,	'8' : 14112,	'9' : 15840,	'10' : 17568,	'11' : 19848,	'12' : 22920,	'13' : 25456,	'14' : 28336,	'15' : 30576,	'16' : 31704,	'17' : 35160,	'18' : 39232,	'19' : 42368,	'20' : 46888,	'21' : 48936,	'22' : 52752,	'23' : 57336,	'24' : 61664,	'25' : 63776,	'26' : 73712})
        self.tbsTable.append({	'0' : 2792,	'1' : 3624,	'2' : 4584,	'3' : 5736,	'4' : 7224,	'5' : 8760,	'6' : 10296,	'7' : 12216,	'8' : 14112,	'9' : 15840,	'10' : 17568,	'11' : 19848,	'12' : 22920,	'13' : 25456,	'14' : 28336,	'15' : 30576,	'16' : 32856,	'17' : 36696,	'18' : 39232,	'19' : 43816,	'20' : 46888,	'21' : 51024,	'22' : 55056,	'23' : 57336,	'24' : 61664,	'25' : 63776,	'26' : 75376})
        self.tbsTable.append({	'0' : 2792,	'1' : 3752,	'2' : 4584,	'3' : 5992,	'4' : 7224,	'5' : 8760,	'6' : 10680,	'7' : 12216,	'8' : 14112,	'9' : 15840,	'10' : 17568,	'11' : 20616,	'12' : 22920,	'13' : 26416,	'14' : 29296,	'15' : 30576,	'16' : 32856,	'17' : 36696,	'18' : 40576,	'19' : 43816,	'20' : 46888,	'21' : 51024,	'22' : 55056,	'23' : 57336,	'24' : 61664,	'25' : 63776,	'26' : 75376})
        self.tbsTable.append({	'0' : 2856,	'1' : 3752,	'2' : 4584,	'3' : 5992,	'4' : 7224,	'5' : 9144,	'6' : 10680,	'7' : 12576,	'8' : 14112,	'9' : 16416,	'10' : 18336,	'11' : 20616,	'12' : 23688,	'13' : 26416,	'14' : 29296,	'15' : 31704,	'16' : 32856,	'17' : 36696,	'18' : 40576,	'19' : 43816,	'20' : 46888,	'21' : 51024,	'22' : 55056,	'23' : 59256,	'24' : 61664,	'25' : 63776,	'26' : 75376})
        self.tbsTable.append({	'0' : 2856,	'1' : 3752,	'2' : 4584,	'3' : 5992,	'4' : 7480,	'5' : 9144,	'6' : 10680,	'7' : 12576,	'8' : 14688,	'9' : 16416,	'10' : 18336,	'11' : 20616,	'12' : 23688,	'13' : 26416,	'14' : 29296,	'15' : 31704,	'16' : 34008,	'17' : 36696,	'18' : 40576,	'19' : 43816,	'20' : 48936,	'21' : 51024,	'22' : 55056,	'23' : 59256,	'24' : 63776,	'25' : 66592,	'26' : 75376})
        self.tbsTable.append({	'0' : 2856,	'1' : 3752,	'2' : 4584,	'3' : 5992,	'4' : 7480,	'5' : 9144,	'6' : 10680,	'7' : 12576,	'8' : 14688,	'9' : 16416,	'10' : 18336,	'11' : 21384,	'12' : 23688,	'13' : 26416,	'14' : 29296,	'15' : 31704,	'16' : 34008,	'17' : 37888,	'18' : 40576,	'19' : 45352,	'20' : 48936,	'21' : 52752,	'22' : 57336,	'23' : 59256,	'24' : 63776,	'25' : 66592,	'26' : 75376})
        self.tbsTable.append({	'0' : 2984,	'1' : 3880,	'2' : 4776,	'3' : 6200,	'4' : 7480,	'5' : 9144,	'6' : 11064,	'7' : 12960,	'8' : 14688,	'9' : 16416,	'10' : 18336,	'11' : 21384,	'12' : 23688,	'13' : 27376,	'14' : 30576,	'15' : 31704,	'16' : 34008,	'17' : 37888,	'18' : 42368,	'19' : 45352,	'20' : 48936,	'21' : 52752,	'22' : 57336,	'23' : 59256,	'24' : 63776,	'25' : 66592,	'26' : 75376})
        self.tbsTable.append({	'0' : 2984,	'1' : 3880,	'2' : 4776,	'3' : 6200,	'4' : 7480,	'5' : 9528,	'6' : 11064,	'7' : 12960,	'8' : 14688,	'9' : 16992,	'10' : 18336,	'11' : 21384,	'12' : 24496,	'13' : 27376,	'14' : 30576,	'15' : 32856,	'16' : 34008,	'17' : 37888,	'18' : 42368,	'19' : 45352,	'20' : 48936,	'21' : 52752,	'22' : 57336,	'23' : 61664,	'24' : 63776,	'25' : 66592,	'26' : 75376})
        self.tbsTable.append({	'0' : 2984,	'1' : 3880,	'2' : 4776,	'3' : 6200,	'4' : 7736,	'5' : 9528,	'6' : 11064,	'7' : 12960,	'8' : 15264,	'9' : 16992,	'10' : 19080,	'11' : 21384,	'12' : 24496,	'13' : 27376,	'14' : 30576,	'15' : 32856,	'16' : 35160,	'17' : 39232,	'18' : 42368,	'19' : 46888,	'20' : 48936,	'21' : 52752,	'22' : 57336,	'23' : 61664,	'24' : 66592,	'25' : 68808,	'26' : 75376})
        self.tbsTable.append({	'0' : 2984,	'1' : 4008,	'2' : 4776,	'3' : 6200,	'4' : 7736,	'5' : 9528,	'6' : 11448,	'7' : 12960,	'8' : 15264,	'9' : 16992,	'10' : 19080,	'11' : 22152,	'12' : 24496,	'13' : 27376,	'14' : 30576,	'15' : 32856,	'16' : 35160,	'17' : 39232,	'18' : 42368,	'19' : 46888,	'20' : 51024,	'21' : 55056,	'22' : 59256,	'23' : 61664,	'24' : 66592,	'25' : 68808,	'26' : 75376})
        self.tbsTable.append({	'0' : 2984,	'1' : 4008,	'2' : 4968,	'3' : 6456,	'4' : 7736,	'5' : 9528,	'6' : 11448,	'7' : 13536,	'8' : 15264,	'9' : 16992,	'10' : 19080,	'11' : 22152,	'12' : 24496,	'13' : 28336,	'14' : 31704,	'15' : 34008,	'16' : 35160,	'17' : 39232,	'18' : 43816,	'19' : 46888,	'20' : 51024,	'21' : 55056,	'22' : 59256,	'23' : 61664,	'24' : 66592,	'25' : 68808,	'26' : 75376})
        self.tbsTable.append({	'0' : 3112,	'1' : 4008,	'2' : 4968,	'3' : 6456,	'4' : 7992,	'5' : 9528,	'6' : 11448,	'7' : 13536,	'8' : 15264,	'9' : 17568,	'10' : 19080,	'11' : 22152,	'12' : 25456,	'13' : 28336,	'14' : 31704,	'15' : 34008,	'16' : 35160,	'17' : 39232,	'18' : 43816,	'19' : 46888,	'20' : 51024,	'21' : 55056,	'22' : 59256,	'23' : 63776,	'24' : 66592,	'25' : 71112,	'26' : 75376})

    def loadCqiTable(self):
        """CQI table 7.2.3-1 from 3GPP TS 36.213"""
        self.cqiTable.append({})
        self.cqiTable.append({'spctEff': 0.15 ,'cqi': 1})
        self.cqiTable.append({'spctEff': 0.23 ,'cqi': 2})
        self.cqiTable.append({'spctEff': 0.38 ,'cqi': 3})
        self.cqiTable.append({'spctEff': 0.60 ,'cqi': 4})
        self.cqiTable.append({'spctEff': 0.88 ,'cqi': 5})
        self.cqiTable.append({'spctEff': 1.18 ,'cqi': 6})
        self.cqiTable.append({'spctEff': 1.48 ,'cqi': 7})
        self.cqiTable.append({'spctEff': 1.91 ,'cqi': 8})
        self.cqiTable.append({'spctEff': 2.40 ,'cqi': 9})
        self.cqiTable.append({'spctEff': 2.73 ,'cqi': 10})
        self.cqiTable.append({'spctEff': 3.32 ,'cqi': 11})
        self.cqiTable.append({'spctEff': 3.90 ,'cqi': 12})
        self.cqiTable.append({'spctEff': 4.52 ,'cqi': 13})
        self.cqiTable.append({'spctEff': 5.12 ,'cqi': 14})
        self.cqiTable.append({'spctEff': 5.55 ,'cqi': 15})

    def loadBlerTable(self):
        """BLER tables obtained from runing simulations with the reference simulation tool."""
        self.blerTable['BER=0.016'] = []
        self.blerTable['BER=0.016'].append({'24': 0.475235796886,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00316598699789,	'22': 0.00316598699789,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.149932255927,	'22': 0.149932255927,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.753533453717,	'22': 0.753533453717,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00234636780958,	'22': 0.00234636780958,	'20': 0.00234636780958,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.021359664191,	'22': 0.021359664191,	'20': 0.021359664191,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.123548623531,	'22': 0.123548623531,	'20': 0.123548623531,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.333658839914,	'22': 0.333658839914,	'20': 0.333658839914,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.653926385148,	'22': 0.653926385148,	'20': 0.653926385148,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00074745295817,	'22': 0.00074745295817,	'20': 0.00074745295817,	'18': 0.00074745295817,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00632265146346,	'22': 0.00632265146346,	'20': 0.00632265146346,	'18': 0.00632265146346,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0281630410666,	'22': 0.0281630410666,	'20': 0.0281630410666,	'18': 0.0281630410666,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.100463826519,	'22': 0.100463826519,	'20': 0.100463826519,	'18': 0.100463826519,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.264139528918,	'22': 0.264139528918,	'20': 0.264139528918,	'18': 0.264139528918,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.534739854894,	'22': 0.534739854894,	'20': 0.534739854894,	'18': 0.534739854894,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.708806352343,	'22': 0.708806352343,	'20': 0.708806352343,	'18': 0.708806352343,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.000563804697832,	'22': 0.000563804697832,	'20': 0.000563804697832,	'18': 0.000563804697832,	'16': 0.000563804697832,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00632339519849,	'22': 0.00632339519849,	'20': 0.00632339519849,	'18': 0.00632339519849,	'16': 0.00632339519849,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0322533895489,	'22': 0.0322533895489,	'20': 0.0322533895489,	'18': 0.0322533895489,	'16': 0.0322533895489,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.11015653726,	'22': 0.11015653726,	'20': 0.11015653726,	'18': 0.11015653726,	'16': 0.11015653726,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.000238631370249,	'22': 0.000238631370249,	'20': 0.000238631370249,	'18': 0.000238631370249,	'16': 0.000238631370249,	'14': 0.000238631370249,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00159782289964,	'22': 0.00159782289964,	'20': 0.00159782289964,	'18': 0.00159782289964,	'16': 0.00159782289964,	'14': 0.00159782289964,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00722093673837,	'22': 0.00722093673837,	'20': 0.00722093673837,	'18': 0.00722093673837,	'16': 0.00722093673837,	'14': 0.00722093673837,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0317993015537,	'22': 0.0317993015537,	'20': 0.0317993015537,	'18': 0.0317993015537,	'16': 0.0317993015537,	'14': 0.0317993015537,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.08761210774,	'22': 0.08761210774,	'20': 0.08761210774,	'18': 0.08761210774,	'16': 0.08761210774,	'14': 0.08761210774,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00143258694115,	'22': 0.00143258694115,	'20': 0.00143258694115,	'18': 0.00143258694115,	'16': 0.00143258694115,	'14': 0.00143258694115,	'12': 0.00143258694115,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.00361278064982,	'22': 0.00361278064982,	'20': 0.00361278064982,	'18': 0.00361278064982,	'16': 0.00361278064982,	'14': 0.00361278064982,	'12': 0.00361278064982,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0154042786171,	'22': 0.0154042786171,	'20': 0.0154042786171,	'18': 0.0154042786171,	'16': 0.0154042786171,	'14': 0.0154042786171,	'12': 0.0154042786171,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0439197646926,	'22': 0.0439197646926,	'20': 0.0439197646926,	'18': 0.0439197646926,	'16': 0.0439197646926,	'14': 0.0439197646926,	'12': 0.0439197646926,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.111752248074,	'22': 0.111752248074,	'20': 0.111752248074,	'18': 0.111752248074,	'16': 0.111752248074,	'14': 0.111752248074,	'12': 0.111752248074,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0117406036906,	'22': 0.0117406036906,	'20': 0.0117406036906,	'18': 0.0117406036906,	'16': 0.0117406036906,	'14': 0.0117406036906,	'12': 0.0117406036906,	'10': 0.0117406036906,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.197218973257,	'22': 0.197218973257,	'20': 0.197218973257,	'18': 0.197218973257,	'16': 0.197218973257,	'14': 0.197218973257,	'12': 0.197218973257,	'10': 0.197218973257,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.000603065635079,	'22': 0.000603065635079,	'20': 0.000603065635079,	'18': 0.000603065635079,	'16': 0.000603065635079,	'14': 0.000603065635079,	'12': 0.000603065635079,	'10': 0.000603065635079,	'8': 0.000603065635079,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0,	'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.016'].append({'24': 0.0260895966053,	'22': 0.0260895966053,	'20': 0.0260895966053,	'18': 0.0260895966053,	'16': 0.0260895966053,	'14': 0.0260895966053,	'12': 0.0260895966053,	'10': 0.0260895966053,	'8': 0.0260895966053,	'6': 0.0260895966053,	'4': 0.0260895966053,	'2': 0})

        self.blerTable['BER=0.01'] = []
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.00335388766947,'22': 0.00335388766947,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.0020240570253,'22': 0.0020240570253,	'20': 0.0020240570253,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.0234078406314,'22': 0.0234078406314,	'20': 0.0234078406314,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.000147710487445,'22': 0.000147710487445,	'20': 0.000147710487445,	'18': 0.000147710487445,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.000399581971195,'22': 0.000399581971195,	'20': 0.000399581971195,	'18': 0.000399581971195,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.00611245325794,'22': 0.00611245325794,	'20': 0.00611245325794,	'18': 0.00611245325794,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.0267132761955,'22': 0.0267132761955,	'20': 0.0267132761955,	'18': 0.0267132761955,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.10678891355,'22': 0.10678891355,	'20': 0.10678891355,	'18': 0.10678891355,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.000108108108108,'22': 0.000108108108108,	'20': 0.000108108108108,	'18': 0.000108108108108,	'16': 0.000108108108108,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0.00973157784013,'22': 0.00973157784013,	'20': 0.00973157784013,	'18': 0.00973157784013,	'16': 0.00973157784013,	'14': 0.00973157784013,	'12': 0.00973157784013,	'10': 0.00973157784013,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})
        self.blerTable['BER=0.01'].append({'24': 0,'22': 0,	'20': 0,	'18': 0,	'16': 0,	'14': 0,	'12': 0,	'10': 0,	'8': 0,	'6': 0,	'4': 0,	'2': 0})

    def setMod(self,u,nprb): # AMC
        """This method calculates spectral efficiency for the UE SINR and configured BER, and obtains CQI, MCS, and TBS"""
        sinr = self.ues[u].radioLinks.linkQuality
        sp_ef = math.log(1-(sinr/(math.log(5*self.BER)/1.5)),2)
        # Set CQI and find Spectral efficiency
        ef = self.setCQI(sp_ef)
        # Find MCS and TBindex
        mcs_ = self.findMCS(ef)
        mo = self.modTable[mcs_]['mod']
        b = self.modTable[mcs_]['bitsPerSymb']
        tbs_ind = self.modTable[mcs_]['tbsi']
        # Find TBsize
        tbls = self.tbsTable[nprb][str(tbs_ind)] # nprb always > 0
        return [tbls, mo, b, mcs_]

    def setCQI(self,sp_eff):
        cqi = 0
        findCQI = False
        while cqi<15 and not(findCQI):
            cqi = cqi + 1
            if cqi < 15:
                findCQI = sp_eff<self.cqiTable[cqi+1]['spctEff']
            else:
                findCQI = True
        eff = self.cqiTable[cqi]['spctEff']
        return eff

    def findMCS(self,e):
        mcs = 0
        findMCS = False
        while mcs<29 and not(findMCS):
            mcs = mcs + 1
            if mcs < 29:
                findMCS = e<self.modTable[mcs+1]['spctEff']
            else:
                findMCS = True
        if not(mcs%2==0):
            mcs = mcs - 1
        return mcs

    def setBLER(self,u): # BLER calculation
        if (self.BER < 0.01) or (self.BER == 0.01 and self.PRBs > 6):
            self.ues[u].bler = 0
        else:
            sinr = self.ues[u].radioLinks.linkQuality
            mcs = self.ues[u].MCS
            berKey = 'BER='+str(self.BER)
            # find BLER
            sinrs = [37.0788,	33.6316,	30.6437,	28.0369,	25.7492,	23.7305,	21.9401,	20.345,	18.9178,	17.6356,	16.4795,	15.4334,	14.4839,	13.6194,	12.8301,	12.1074,	11.4441,	10.8338,	10.2711,	9.75118,	9.26971,	8.82304,	8.4079,	8.02138,	7.66092,	7.32422,	7.00923,	6.71414,	6.4373,	6.17723,	5.93262,	5.70224,	5.48504,	5.28001,	5.08626,	4.90299,	4.72944,	4.56495,	4.4089,	4.26071,	4.11987,	3.9859,	3.85836,	3.73685,	3.62098,	3.51042,	3.40485,	3.30397,	3.20751,	3.11521,	3.02684,	2.63672,	2.31743,	1.83105,	1.48315,	1.02997,	0.756711,	0.579357]
            sinrs_i = 0
            findSINR = False
            while sinrs_i<(len(sinrs)-1) and not(findSINR):
                sinrs_i = sinrs_i + 1
                findSINR = sinr>=sinrs[sinrs_i]

            if mcs<=24:
                pend = (self.blerTable[berKey][sinrs_i][str(mcs)]-self.blerTable[berKey][sinrs_i-1][str(mcs)])/(sinrs[sinrs_i]-sinrs[sinrs_i-1])
                self.ues[u].bler = self.blerTable[berKey][sinrs_i][str(mcs)] + pend*(sinr-sinrs[sinrs_i])
            else:
                self.ues[u].bler = self.blerTable[berKey][sinrs_i][str(24)]

class TBqueue: # TB queue!!!
    """This class is used to model scheduler TB queue."""
    def __init__(self,nrb):
        self.res = deque([])
        self.numRB = nrb

    def getFreeSpace(self):
        freeSpace = self.numRB
        if len(self.res)>0:
            for tbl in self.res:
                freeSpace = freeSpace - tbl.numRB
        return freeSpace

    def insertTB(self,tb):
        succ = False
        freeSpace = self.getFreeSpace()
        if freeSpace>=tb.numRB:
            self.res.append(tb) # The TB fits the free space
            succ = True
        else:
            succ = False
            print (Format.CRED+'Not enough space!!!! : '+str(freeSpace)+'/'+str(tb.numRB)+Format.CEND)
        return succ

    def removeTB(self):
        if len(self.res)>0:
            return self.res.popleft()

    def updateSize(self,newSize):
        self.numRB = newSize

class TransportBlock:
    """This class is used to describe TB properties and behabiour."""
    def __init__(self,i,m,u,typ,p_l,nrb,sz):
        self.id = i
        self.mod = m
        self.ue = u
        self.type = typ
        self.pckt_l = p_l
        self.numRB = nrb
        self.reTxNum = 0
        self.size = sz

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
