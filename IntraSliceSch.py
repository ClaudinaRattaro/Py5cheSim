import os
import sys
import simpy #from SimPy.Simulation import * (simpy2.2)
from collections import deque
import math
import random

class IntraSliceScheduler():
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
        self.tbsTable = []
        self.sinrModTable = [] # 5G
        self.ind_u = 0
        self.nrbUEmax = n
        self.BER = 0.005
        self.sbFrNum = 0
        self.bcst_sg = True
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
        self.loadTBStable()
        self.loadSINR_MCStable() # 5G
        self.sliceLabel = slcLbl # 5G
        self.dbFile = open(self.sliceLabel+dir+'dbFile.html','w') # 5G


    def loadModTable(self):

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



    def loadTBStable(self):

        self.tbsTable = [0,24,	32,	40,	48,	56,	64,	72,	80,	88,	96,	104,	112,	120,	128,	136,	144,	152,	160,	168,	176,	184,	192,	208,	224,	240,	256,	272,	288,	304,	320,	336,	352,	368,	384,	408,	432,	456,	480,	504,	528,	552,	576,	608,	640,	672,	704,	736,	768,	808,	848,	888,	928,	984,	1032,	1064,	1128,	1160,	1192,	1224,	1256,	1288,	1320,	1352,	1416,	1480,	1544,	1608,	1672,	1736,	1800,	1864,	1928,	2024,	2088,	2152,	2216,	2280,	2408,	2472,	2536,	2600,	2664,	2728,	2792,	2856,	2976,	3104,	3240,	3368,	3496,	3624,	3752,	3824]

    def queuesOut(self,env): # ---------- PEM -------------
        while True:
            if self.dbMd:
                self.printQstate(env)
            self.queueUpdate() # RESOURCE ALLOCATION
            yield env.timeout(1.0/self.ttiByms) #yield hold, self, (1.0/self.ttiByms)
            self.printDebDataDM('<h4>Transport Blocks served at time = '+ str(env.now)+'</h4>')
            if len(self.queue.res)>0:# and len(self.queue.res[0])>0:
                for i in range (len(self.queue.res)):#[0])):
                    tbl = self.queue.removeTB()
                    ue = tbl.ue
                    self.ues[ue].resUse = self.ues[ue].resUse + 1
                    if random.random()<=(1.0-self.ues[ue].bler) or (tbl.reTxNum>0): # not sending again retransmitted TB
                        self.printDebDataDM('<p style="color:green">'+ue+ 'TB '+str(tbl.id)+ ' Served '+' ---------'+'</p>')
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
                #self.queue.removeTTI()
            else:
                self.printDebDataDM('<p style="color:green">'+'no more TBs in queue'+'</p>')
            self.sbFrNum = self.sbFrNum + 1
            self.bcst_sg = True

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
        # Make Resource allocation and Insert generated TBs into Scheduler queue,for 1 TTI
        packts = 1
        self.ueLst = list(self.ues.keys())
        self.resAlloc(self.nrbUEmax)
        rb = 0
        if self.mimomd == 'MU':
            self.rb_lim = self.nrbUEmax*self.nlayers # max allocated RB/TTI
        else:
            self.rb_lim = self.nrbUEmax

        while len(self.ueLst)>0 and packts>0 and rb < self.rb_lim:
            #rb = rb + self.rrcBrcstSigIn() # To add Broadcast signalling (MIB and SIB)
            ue = self.ueLst[self.ind_u]
            self.printDebDataDM('---------------- '+ue+' ------------------<br>') # print more info in debbug mode
            if self.ues[ue].prbs>0:
                if len(self.ues[ue].bearers)>0 and rb < self.rb_lim:
                    if len(self.ues[ue].pendingTB)==0: # No TB to reTX
                        rb = rb + self.rrcUncstSigIn(ue)
                        if  len(self.ues[ue].bearers[0].buffer.pckts)>0 and rb < self.rb_lim:
                            rb = rb + self.dataPtoTB(ue)
                    else: # There are TB to reTX
                        #self.printPendTB()
                        rb = rb + self.retransmitTB(ue)
                    if self.dbMd:
                        self.printQtb() # Print TB queue in debbug mode
            # else:
            #     self.printDebDataDM( ue+' has not resources in this subframe')
            self.updIndUE()
            packts = self.updSumPcks()

        #self.printDebDataDM(str(packts)+' Total packets for all ue  ???????????????<br>') # # print more info in debbug mode

    def rrcBrcstSigIn(self):
        rrcSigCond = (self.sbFrNum%10 == 0 or (self.sbFrNum-5)%20 == 0) and self.bcst_sg
        if rrcSigCond:
            ins = self.insertTB(0,'4-QAM','Broadcast','Sig',[],self.nrbUEmax,19)
            r = self.nrbUEmax
            self.bcst_sg = False
        else:
            r = 0
        return r

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
        return n

    def retransmitTB(self,u):
        pendingTbl = self.ues[u].pendingTB[0]
        if pendingTbl.reTxNum < 3000:# or pendingTbl.type == 'Sig': # TB retransmission
            intd = self.queue.insertTB(pendingTbl)
            self.ues[u].pendingTB.pop(0)
            pendingTbl.reTxNum = pendingTbl.reTxNum + 1
            r = self.ues[u].prbs
        else:
            self.ues[u].pendingTB.pop(0) # Drop!!!
            r = 0
        return r

    def resAlloc(self,Nrb):
        if len(list(self.ues.keys()))>0:
            for ue in list(self.ues.keys()): # TS 38.214 table 5.1.2.2.1-1  RBG size for configuration 2
                # if self.ues[ue].BWPs<37:
                #     self.ues[ue].prbs = 4
                # elif self.ues[ue].BWPs<73:
                #     self.ues[ue].prbs = 8
                # else:
                #     self.ues[ue].prbs = 16
                self.ues[ue].prbs = Nrb # To compare with lena-5G
        # Print Resource Allocation
        self.printResAlloc()

    def setMod(self,u,nprb): # AMC
        sinr = self.ues[u].radioLinks.linkQuality # = 10 log10 sinr_
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
        #self.printDebDataDM('MCS: '+str(mcsi)+', TBsize (bytes): '+str(int(float(tbls)/8))+'<br>')
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
            # Ninfo = Nre__*self.ues[u_].prbs*r*qm*self.nlayers
            Ninfo = Nre__*nprb*r*qm*self.nlayers
        else:
            # Ninfo = Nre__*self.ues[u_].prbs*r*qm
            Ninfo = Nre__*nprb*r*qm
            tbs = Ninfo
            #print(str(self.TDDsmb)+'-----------------> '+str(Nre__)+' ----- '+str(qm)+' '+str(r)+' '+str(nprb)+'=========> '+str(Ninfo))

        return tbs

    def findTBS(self,ninfo):
        tbsi = 0
        findTBS = False
        while tbsi<93 and not(findTBS):
            tbsi = tbsi + 1
            if tbsi < 93:
                findTBS = ninfo<float(self.tbsTable[tbsi])
            else:
                findTBS = True
            #print '-------',ninfo,self.tbsTable[tbsi],findTBS,'------'
        return self.tbsTable[tbsi]

    def setBLER(self,u): # BLER calculation
        self.ues[u].bler = 0.0
        #print self.ues[u].bler, sp_ef, ef0, ef0+(deltaEf), mcs,sinr,self.BER
    def insertTB(self,id,m,uu,type,pack_lst,n,s):
        tb = TransportBlock(id,m,uu,type,pack_lst,n,s)
        succ = self.queue.insertTB(tb)
        #self.printQtb()
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
            #self.printQtb()
            for ue in list(self.ues.keys()):
                self.ues[ue].packetFlows[0].setMeassures(env.now)
                #self.printDebData(ue+ 'PacketLossRate: '+str(self.ues[ue].packetFlows[0].meassuredKPI['PacketLossRate'])+'<br>')
                #self.printDebData(ue+ 'Throughput: '+str(self.ues[ue].packetFlows[0].meassuredKPI['Throughput'])+'<br>')
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
                resAllocMsg = resAllocMsg + ue +' '+ str(self.ues[ue].pfFactor)+' '+str(self.ues[ue].prbs)+ ' '+str(self.ues[ue].num)+' '+ str(self.ues[ue].lastDen)+'<br>'
            self.printDebData(resAllocMsg)
            self.printDebData('+++++++++++++++++++++++++++++++++++'+'<br>')

#--------------------------------------------------------------

class LTE_scheduler(IntraSliceScheduler):
    def __init__(self,ba,n,debMd,ber,sLod):
        IntraSliceScheduler.__init__(self,ba,n,debMd,ber,sLod,'RR',1,'',1,'DL',14,False,'LTE')

class TBqueue: # TB queue!!!
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
            print (Format.CRED+'No dentraaaaaaaaaa: '+str(freeSpace)+'/'+str(tb.numRB)+Format.CEND)
        return succ

    def removeTB(self):
        if len(self.res)>0:
            return self.res.popleft()

    def updateSize(self,newSize):
        self.numRB = newSize

class TransportBlock:
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
