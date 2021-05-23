import os
import sys
import matplotlib.pyplot as plt
from UE import *
from cell import Format

def initialSinrGenerator(n_ues,type,refValue):
    genSINRs = []
    delta = float(35.0 - 2.0)/n_ues
    for i in range(n_ues):
        if type == 'same':
            genSINRs.append(refValue)
        else:
            genSINRs.append(35.0-delta*i)
    return genSINRs

class UEgroup:
    def __init__(self,nuDL,nuUL,pszDL,pszUL,parrDL,parrUL,label,dly,avlty,schedulerType,mmMd,lyrs,cell,t_sim,measInterv,env):# brrar sinr
        self.num_usersDL = nuDL
        self.num_usersUL = nuUL
        self.p_sizeDL = pszDL
        self.p_sizeUL = pszUL
        self.p_arr_rateDL = parrDL
        self.p_arr_rateUL = parrUL
        self.sinr_0DL = 0
        self.sinr_0UL = 0
        self.sch = schedulerType
        self.label = label
        self.req = {}
        self.mmMd = mmMd
        self.lyrs = lyrs
        self.setReq(dly,avlty)
        self.setInitialSINR()
        if self.num_usersDL>0:
            self.usersDL,self.flowsDL = self.initializeUEs('DL',self.num_usersDL,self.p_sizeDL,self.p_arr_rateDL,self.sinr_0DL,cell,t_sim,measInterv,env)
        if self.num_usersUL>0:
            self.usersUL,self.flowsUL = self.initializeUEs('UL',self.num_usersUL,self.p_sizeUL,self.p_arr_rateUL,self.sinr_0UL,cell,t_sim,measInterv,env)

    def setReq(self,delay,avl):
        self.req['reqDelay'] = delay
        self.req['reqThroughputDL'] = 8*self.p_sizeDL*self.p_arr_rateDL
        self.req['reqThroughputUL'] = 8*self.p_sizeUL*self.p_arr_rateUL
        self.req['reqAvailability'] = avl

    def setInitialSINR(self):
        if self.num_usersDL>0:
            self.sinr_0DL = initialSinrGenerator(self.num_usersDL,'',0)
        if self.num_usersUL>0:
            self.sinr_0UL = initialSinrGenerator(self.num_usersUL,'',0)

    def initializeUEs(self,dir,num_users,p_size,p_arr_rate,sinr_0,cell,t_sim,measInterv,env):
        users = []
        flows = []
        procFlow = []
        procUE = []
        procRL = []
        for j in range (num_users):
            ue_name = 'ue'+str(j+1)#+'-'+self.label
            users.append(UE(ue_name,float(sinr_0[j]),0,20))
            flows.append(PacketFlow(1,p_size,p_arr_rate,ue_name,dir,self.label))
            users[j].addPacketFlow(flows[j])
            users[j].packetFlows[0].setQosFId(1)
            # Flow, UE and RL PEM activation
            procFlow.append(env.process(users[j].packetFlows[0].queueAppPckt(env,tSim=t_sim))) # activate(users[j].packetFlows[0],users[j].packetFlows[0].queueAppPckt(tSim=t_sim))
            procUE.append(env.process(users[j].receivePckt(env,c=cell))) # activate(users[j],users[j].receivePckt(c=cell))
            procRL.append(env.process(users[j].radioLinks.updateLQ(env,udIntrv=measInterv,tSim=t_sim,fl=False,u=num_users,r=''))) # activate(users[j].radioLinks,users[j].radioLinks.updateLQ(udIntrv=measInterv,tSim=t_sim,fl=False,u=num_users,r=''))
        return users,flows

    def activateSliceScheds(self,interSliceSche,env):
        if self.num_usersDL>0:
            procSchDL = env.process(interSliceSche.slices[self.label].schedulerDL.queuesOut(env)) #activate(interSliceSche.slices[self.label].schedulerDL,interSliceSche.slices[self.label].schedulerDL.queuesOut())
        if self.num_usersUL>0:
            procSchUL = env.process(interSliceSche.slices[self.label].schedulerUL.queuesOut(env)) #activate(interSliceSche.slices[self.label].schedulerUL,interSliceSche.slices[self.label].schedulerUL.queuesOut())

    def printSliceResults(self,interSliceSche,t_sim,bw,measInterv):
        if self.num_usersDL>0:
            printResults('DL',self.usersDL,self.num_usersDL,interSliceSche.slices[self.label].schedulerDL,t_sim,True,False,self.sinr_0DL)
            [sent_DL,lost_DL,SINR_DL,BLER_DL,times_DL,mcs_DL,rBytes_DL,rU_DL,plr_DL,th_DL] = getKPIs('DL','dlStsts'+'_'+self.label+'.txt',self.usersDL,self.num_usersDL,self.sinr_0DL,measInterv,t_sim)
            makePlots('DL',sent_DL,lost_DL,SINR_DL,BLER_DL,times_DL,mcs_DL,rBytes_DL,rU_DL,plr_DL,th_DL,self.num_usersDL,self.p_sizeDL,self.p_arr_rateDL,bw,self.sch)
            [sent_DL,lost_DL,times_DL,rBytes_DL,rU_DL,plr_DL,th_DL,cnx_DL] = getKPIsInter('DL','dlStsts_InterSlice.txt',list(interSliceSche.slices.keys()),len(list(interSliceSche.slices.keys())))
            makePlotsInter('DL',sent_DL,lost_DL,times_DL,rBytes_DL,rU_DL,plr_DL,th_DL,cnx_DL,len(list(interSliceSche.slices.keys())),bw,self.sch)
        if self.num_usersUL>0:
            printResults('UL',self.usersUL,self.num_usersUL,interSliceSche.slices[self.label].schedulerUL,t_sim,True,False,self.sinr_0UL)
            [sent_UL,lost_UL,SINR_UL,BLER_UL,times_UL,mcs_UL,rBytes_UL,rU_UL,plr_UL,th_UL] = getKPIs('UL','ulStsts'+'_'+self.label+'.txt',self.usersUL,self.num_usersUL,self.sinr_0UL,measInterv,t_sim)
            makePlots('UL',sent_UL,lost_UL,SINR_UL,BLER_UL,times_UL,mcs_UL,rBytes_UL,rU_UL,plr_UL,th_UL,self.num_usersUL,self.p_sizeUL,self.p_arr_rateUL,bw,self.sch)
            [sent_UL,lost_UL,times_UL,rBytes_UL,rU_UL,plr_UL,th_UL,cnx_UL] = getKPIsInter('UL','ulStsts_InterSlice.txt',list(interSliceSche.slices.keys()),len(list(interSliceSche.slices.keys())))
            makePlotsInter('UL',sent_UL,lost_UL,times_UL,rBytes_UL,rU_UL,plr_UL,th_UL,cnx_UL,len(list(interSliceSche.slices.keys())),bw,self.sch)

def printResults(dir,users,num_users,scheduler,t_sim,singleRunMode,fileSINR,sinr):
    PDRprom = 0.0
    SINRprom = 0.0
    MCSprom = 0.0
    THprom = 0.0
    UEresults = open('resultadosUE'+str(sinr[0])+'.txt','w')
    UEresults.write('SINR MCS BLER PLR TH ResUse'+'\n')
    print (Format.CGREEN+'Accumulated '+dir+' indicators by user:'+Format.CEND)
    for i in range (num_users):
        # Count pending packets also as lost
        users[i].packetFlows[0].lostPackets = users[i].packetFlows[0].lostPackets + len(list(scheduler.ues[users[i].id].pendingPckts.keys())) + len(users[i].packetFlows[0].appBuff.pckts) + len(scheduler.ues[users[i].id].bearers[0].buffer.pckts)
        for p in list(scheduler.ues[users[i].id].pendingPckts.keys()):
            for pp in scheduler.ues[users[i].id].bearers[0].buffer.pckts:
                if p == pp.secNum:
                     users[i].packetFlows[0].lostPackets = users[i].packetFlows[0].lostPackets - 1

        users[i].packetFlows[0].setMeassures(t_sim)
        PDRprom = PDRprom + users[i].packetFlows[0].meassuredKPI['PacketLossRate']
        THprom = THprom + users[i].packetFlows[0].meassuredKPI['Throughput']
        if singleRunMode and fileSINR:
            sinrUser = float(users[i].radioLinks.lqAv)/users[i].radioLinks.totCount
        else:
            sinrUser = users[i].radioLinks.linkQuality # not single run, or single run but not taking SINR from file
        SINRprom = SINRprom + sinrUser
        MCSprom = MCSprom + float(users[i].MCS)

        print (users[i].id+'\t'+Format.CYELLOW+ ' Sent Packets:'+Format.CEND+str(users[i].packetFlows[0].sentPackets)+Format.CYELLOW+ ' Lost Packets:'+Format.CEND+str(users[i].packetFlows[0].lostPackets))
        print ('\t'+ 'SINRav: '+str(int(sinrUser))+ ' MCSav: '+str(users[i].MCS)+' PLR: '+str(round(users[i].packetFlows[0].meassuredKPI['PacketLossRate'],2))+' %'+' Throughput: '+str(round(users[i].packetFlows[0].meassuredKPI['Throughput'],2)))

        UEresults.write(str(sinrUser)+' '+str(users[i].MCS)+' '+str(float(users[i].lostTB)/(users[i].TXedTB+users[i].lostTB))+' '+str(users[i].packetFlows[0].meassuredKPI['PacketLossRate']/100)+' '+str(users[i].packetFlows[0].meassuredKPI['Throughput'])+' '+str(users[i].resUse)+' '+str(int(float(users[i].tbsz)/8))+'\n')

    print (Format.CGREEN+'Average '+dir+' Indicators:'+Format.CEND)
    print ('Packet Loss Rate av: '+'\t'+str(round((PDRprom)/num_users,2))+' %')
    print ('Throughput av: '+'\t'+str(round(THprom/num_users,2))+' Mbps')
    print ('Connections av: '+'\t'+str(num_users))
    print ('Slice Resources: '+'\t'+str(scheduler.nrbUEmax)+ ' PRBs')
    print ('Slice Numerology: '+'\t'+str(scheduler.ttiByms*15)+ ' kHz')
    # print 'SINR av: ',str(round(SINRprom/num_users,2))
    # print 'MCS av: ',str(round(MCSprom/num_users,2))

def getKPIs(dir,stFile,users,num_users,sinr_0,measInterv,tSim):
    sent = {}
    lost = {}
    SINR = {}
    BLER = {}
    times = {}
    mcs = {}
    rBytes = {}
    rU = {}
    plr = {}
    th = {}
    allTimes = {}#range(0,tSim,measInterv)
    for i in range (num_users):
        times[users[i].id] = [0]
        SINR[users[i].id] = [sinr_0[i]]
        mcs[users[i].id] = [users[i].MCS]
        BLER[users[i].id] = [users[i].bler]
        rU[users[i].id] = [0]
        sent[users[i].id] = [0]
        lost[users[i].id] = [0]
        rBytes[users[i].id] = [0]
        plr[users[i].id] = [0]
        th[users[i].id] = [0]

    with open(stFile) as dlStsts:
        lines = dlStsts.readlines()
    for line in lines[1:]:
        columns = line.split(" ",9)
        time = columns[0]
        ue = columns[1]
        sinr_ = columns[2]
        mcs_ = columns[3]
        bler = columns[4]
        resUse = columns[5]
        sntPackets = columns[6]
        lstPackets = columns[7]
        rcvdBytes = columns[8]
        slice = columns[9]

        times[ue].append(float(time))
        SINR[ue].append(float(sinr_))
        mcs[ue].append(int(mcs_))
        BLER[ue].append(float(bler))
        rU[ue].append(int(resUse) - rU[ue][len(rU[ue])-1])
        sent[ue].append(int(sntPackets))
        lost[ue].append(int(lstPackets))
        rBytes[ue].append(int(rcvdBytes))
        plr[ue].append(100*float(lost[ue][len(lost[ue])-1] - lost[ue][len(lost[ue])-2])/(sent[ue][len(sent[ue])-1] - sent[ue][len(sent[ue])-2]))
        rcvdBytes = rBytes[ue][len(rBytes[ue])-1] - rBytes[ue][len(rBytes[ue])-2]
        deltaT = times[ue][len(times[ue])-1] - times[ue][len(times[ue])-2]
        th[ue].append((float(rcvdBytes)*8000)/(deltaT*1024*1024))

    # update resource Use (rU) to consider %
    for t in range(len(times[users[0].id])):
        resU = 0
        for ue in list(times.keys()):
            resU = resU + rU[ue][t]
        for ue in list(times.keys()):
            if resU>0:
                rU[ue][t] = 100*float(rU[ue][t])/resU
    return sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th

def getKPIsInter(dir,stFile,slices,num_slices):
    sent = {}
    lost = {}
    times = {}
    rBytes = {}
    plr = {}
    th = {}
    rU = {}
    cnx = {}
    for i in range (num_slices):
        times[slices[i]] = [0]
        rU[slices[i]] = [0]
        sent[slices[i]] = [0]
        lost[slices[i]] = [0]
        rBytes[slices[i]] = [0]
        plr[slices[i]] = [0]
        th[slices[i]] = [0]
        cnx[slices[i]] = [0]

    with open(stFile) as Ststs:
        lines = Ststs.readlines()
    for line in lines[1:]:
        columns = line.split(" ",9)
        time = columns[0]
        slice = columns[1]
        cnxs = columns[2]
        resUse = columns[3]
        sntPackets = columns[4]
        lstPackets = columns[5]
        rcvdBytes = columns[6]

        times[slice].append(float(time))
        cnx[slice].append(float(cnxs))
        rU[slice].append(float(resUse))
        sent[slice].append(int(sntPackets))
        lost[slice].append(int(lstPackets))
        rBytes[slice].append(int(rcvdBytes))
        if (sent[slice][len(sent[slice])-1] - sent[slice][len(sent[slice])-2])>0:
            plr[slice].append(100*float(lost[slice][len(lost[slice])-1] - lost[slice][len(lost[slice])-2])/(sent[slice][len(sent[slice])-1] - sent[slice][len(sent[slice])-2]))
        else:
            plr[slice].append(0)
        rcvdBytes = rBytes[slice][len(rBytes[slice])-1] - rBytes[slice][len(rBytes[slice])-2]
        deltaT = times[slice][len(times[slice])-1] - times[slice][len(times[slice])-2]
        th[slice].append((float(rcvdBytes)*8000)/(deltaT*1024*1024))

    return sent,lost,times,rBytes,rU,plr,th,cnx

def makeUeTimePlot(u,plotName,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th):
    if plotName[0:3]=='PLR':
        plt.plot(times[u],plr[u],label='PLR(%) '+u)
    if plotName[0:2]=='TH':
        plt.plot(times[u],th[u],label='TH(Mbps) '+u)
    if plotName[0:6]=='ResUse':
        plt.plot(times[u],rU[u],label='ResUse(%) '+u)
    if plotName[0:4]=='SINR':
        plt.plot(times[u],SINR[u],label='SINR(dB) '+u)
    if plotName[0:3]=='MCS':
        plt.plot(times[u],mcs[u],label='MCS '+u)
    if plotName[0:4]=='Conn':
        plt.plot(times[u],SINR[u],label='Connections '+u)
    plt.legend()
    plt.xlabel('Time(ms)')
    plt.ylabel(plotName)

def makeUeSinrPlot(u,plotName,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th):
    if plotName[0:3]=='PLR':
        plt.scatter(SINR[u][1:],plr[u][1:],label='PLR(%) '+u)
    if plotName[0:2]=='TH':
        plt.scatter(SINR[u][1:],th[u][1:],label='TH(Mbps) '+u)
    if plotName[0:6]=='ResUse':
        plt.scatter(SINR[u][1:],rU[u][1:],label='ResUse(%) '+u)
    plt.legend()
    plt.xlabel('SINR(dB)')
    plt.ylabel(plotName)

def makeUeThPlot(u,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th):
    plt.scatter(th[u][1:],rU[u][1:],label='ResUse '+u)
    plt.legend()
    plt.xlabel('Throughput(Mbps))')
    plt.ylabel('Resource Use(%)')

def makeAllUesPlot(plotName,xAxes,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch):
    plt.figure()
    for ue in list(times.keys()):
        if xAxes=='|Time':
            makeUeTimePlot(ue,plotName,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th)
        if xAxes=='|SINR':
            makeUeSinrPlot(ue,plotName,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th)
        if xAxes=='|TH':
            makeUeThPlot(ue,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th)
    if p_size == 0: # InterSlicePlots
        plt.title(plotName+' BAND='+str(bw)+' '+str(num_users)+' Slices'+' sched='+str(sch))
        plt.savefig('Figures/'+plotName+xAxes+'_BAND='+str(bw)+'_sched='+str(sch))
    else:
        plt.title(plotName+' BAND='+str(bw)+' '+str(num_users)+' UEs'+' pSize='+str(p_size)+' pInter='+str(p_arr_rate)+' sched='+str(sch))
        plt.savefig('Figures/'+plotName+xAxes+'_BAND='+str(bw)+'_pSize='+str(p_size)+'_pInter='+str(p_arr_rate)+'_sched='+str(sch))


def makePlots(dir,sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch):
    # Plot results ---------------------------------------------------------
    if not os.path.exists('Figures'):
        os.mkdir('Figures')
    makeAllUesPlot('PLR'+dir,'|Time',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    makeAllUesPlot('TH'+dir,'|Time',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    makeAllUesPlot('ResUse'+dir,'|Time',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    makeAllUesPlot('SINR'+dir,'|Time',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    makeAllUesPlot('MCS'+dir,'|Time',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    # makeAllUesPlot('PLR'+dir,'|SINR',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    # makeAllUesPlot('TH'+dir,'|SINR',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    # makeAllUesPlot('ResUse'+dir,'|SINR',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)
    # makeAllUesPlot('ResUse'+dir,'|TH',sent,lost,SINR,BLER,times,mcs,rBytes,rU,plr,th,num_users,p_size,p_arr_rate,bw,sch)

def makePlotsInter(dir,sent,lost,times,rBytes,rU,plr,th,cnx,num_slices,bw,sch):
    # Plot results ---------------------------------------------------------
    if not os.path.exists('Figures'):
        os.mkdir('Figures')
    makeAllUesPlot('PLR'+dir,'|Time',sent,lost,None,None,times,None,rBytes,rU,plr,th,num_slices,0,0,bw,sch)
    makeAllUesPlot('TH'+dir,'|Time',sent,lost,None,None,times,None,rBytes,rU,plr,th,num_slices,0,0,bw,sch)
    makeAllUesPlot('ResUse'+dir,'|Time',sent,lost,None,None,times,None,rBytes,rU,plr,th,num_slices,0,0,bw,sch)
    makeAllUesPlot('Connections'+dir,'|Time',sent,lost,cnx,None,times,None,rBytes,rU,plr,th,num_slices,0,0,bw,sch)
