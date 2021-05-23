import os
import sys
import simpy #from SimPy.Simulation import * (simpy2.2)
from UE import *
from cell import *
from results import *

#------------------------------------------------------------------------------------------------------
# Cell & Simulation parameters
#------------------------------------------------------------------------------------------------------

bw = 5# MHz (FR1: 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 90, 100; FR2: 50, 100, 200, 400)
fr = 'FR1' # FR1 or FR2
band = 'n7'
tdd = False
buf = 81920#10240
# simulation parameters --------------------------------------
t_sim = 60000
debMode = True # to show queues information by TTI during simulation
measInterv = 1000.0 # interval between meassures

#-----------------------------------------------------------------
# Simulation process activation
#-----------------------------------------------------------------

env = simpy.Environment() #initialize() simpy2.2
cell1 = Cell('c1',bw,fr,debMode,1000000,buf,tdd)
interSliceSche1 = cell1.interSliceSched

# Different traffic profiles setting
# UEgroupN = UEgroup(nuDL,nuUL,pszDL,pszUL,parrDL,parrUL,label,dly,avlty,schedulerType,mimo_mode,layers,cell,hdr,t_sim,measInterv):
# label: eMBB, mMTC, URLLC
# schedulerType: RR: Rounf Robin, PF: Proportional Fair (10, 11)
# mimo_mode: #SU, MU
# layers: in SU-MIMO is the number of layers/UE, in MU-MIMO is the number of simultaneous UE to serve with the same resources
UEgroup1 = UEgroup(1,0,3500,0,2,0,'eMBB',20,'','RR','',1,cell1,t_sim,measInterv,env)# borrar sinr ## DL
#UEgroup1 = UEgroup(0,1,0,100000,0,1,'eMBB',20,'','RR','',1,cell1,t_sim,measInterv,env,sinr)# borrar sinr ## UL
UEgroup2 = UEgroup(0,5,0,150,0,60,'URLLC',5,'','RR','',1,cell1,t_sim,measInterv,env)#,sinr)
#UEgroup2 = UEgroup(2,0,150,0,60,0,'mMTC',20,'','RR','',1,cell1,t_sim,measInterv,env)
#UEgroup3 = UEgroup(3,0,1000,0,20,0,'URLLC',2,'','RR','',1,cell1,t_sim,measInterv,env)

UEgroups = [UEgroup1,UEgroup2]#,UEgroup3]
UEgrpsTDD = [UEgroup1]#,UEgroup2] # For UL and DL on the same slice (in 2 different groups)
if len(UEgrpsTDD)>1:
    UEgrpsAct = UEgrpsTDD
    UEgrpsRes = UEgrpsTDD
else:
    UEgrpsAct = UEgroups
    UEgrpsRes = UEgroups
# Slices creation
for ueG in UEgroups:
    interSliceSche1.createSlice(ueG.req['reqDelay'],
    ueG.req['reqThroughputDL'],
    ueG.req['reqThroughputUL'],
    '',
    ueG.num_usersDL,
    ueG.num_usersUL,
    band,
    debMode,
    ueG.mmMd,
    ueG.lyrs,
    ueG.label,
    1,ueG.sch)

# Schedulers activation (inter/intra)

procCell = env.process(cell1.updateStsts(env,interv=measInterv,tSim=t_sim)) #activate(cell1,cell1.updateStsts(interv=measInterv,tSim=t_sim)) simpy2.2
procInter = env.process(interSliceSche1.allocRes(env)) #activate(interSliceSche1,interSliceSche1.allocRes()) simpy2.2
for ueG in UEgrpsAct:
    ueG.activateSliceScheds(interSliceSche1,env)

#----------------------------------------------------------------
env.run(until=t_sim) #simulate(until=t_sim) simpy2.2
#----------------------------------------------------------------

# Closing statistic and debugging files

for slice in list(cell1.slicesStsts.keys()):
    cell1.slicesStsts[slice]['DL'].close()
    cell1.slicesStsts[slice]['UL'].close()
for slice in list(interSliceSche1.slices.keys()):
        interSliceSche1.slices[slice].schedulerDL.dbFile.close()
        interSliceSche1.slices[slice].schedulerUL.dbFile.close()

#----------------------------------------------------------------
#                          RESULTS
#----------------------------------------------------------------
# Show average PLR and Throughput in any case simulation and plots
for UEg in UEgrpsRes:
    print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'                 SLICE: '+UEg.label+'                  '+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'--------------------------------------------------\n'+Format.CEND)
    UEg.printSliceResults(interSliceSche1,t_sim,bw,measInterv)
print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
