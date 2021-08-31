"""This is the simulation script.
Simulation, cell and traffic profile parameters can be set here.
"""
import os
import sys
import simpy
from UE import *
from Cell import *
from Results import *

#------------------------------------------------------------------------------------------------------
#              Cell & Simulation parameters
#------------------------------------------------------------------------------------------------------

bw = [10]# MHz (FR1: 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 90, 100; FR2: 50, 100, 200, 400)
"""List containing each CC's bandwidth for the simulation. """
fr = 'FR1' # FR1 or FR2
"""String with frequency range (FR) to use. 'FR1' for FR1, or 'FR2' for FR2."""
band = 'B1'
"""String with used band for simulation. In TDD mode it is important to set correctly a band from the next list: n257, n258, n260, n261."""
tdd = False
"""Boolean indicating if the cell operates in TDD mode."""
buf = 81920 #10240 #
"""Integer with the maximum Bytes the UE Bearer buffer can tolerate before dropping packets."""
schedulerInter = 'PF11'# RRp for improved Round Robin, PFXX for Proportional Fair
"""String indicating the Inter Slice Scheduler to use. For only one Slice simulations use ''.
If the simulation includes more than one slice, set '' for Round Robin, 'RRp' for Round Robin Plus,
or 'PFXY' for Proportional Fair with X=numExp and Y=denExp."""
#                   Simulation parameters
t_sim = 60000 # (ms)
"""Simulation duration in milliseconds."""
debMode = True # to show queues information by TTI during simulation
"""Boolean indicating if debugging mode is active. In that case, an html log file will be generated with schedulers operation.
Note that in simulations with a high number of UEs this file can turn quite heavy."""
measInterv = 1000.0 # interval between meassures
"""Time interval (in milliseconds) between meassures for statistics reports."""
interSliceSchGr = 3000.0 # interSlice scheduler time granularity
"""Inter slice scheduler time granularity in milliseconds."""

#-----------------------------------------------------------------
#              Simulation process activation
#-----------------------------------------------------------------

env = simpy.Environment()
"""Environment instance needed by simpy for runing PEM methods"""
cell1 = Cell('c1',bw,fr,debMode,buf,tdd,interSliceSchGr,schedulerInter)
"""Cell instance for running the simulation"""
interSliceSche1 = cell1.interSliceSched
"""interSliceScheduler instance"""

#           DIFFERENT TRAFFIC PROFILES SETTING

# A few examples ...

#UEgroup1 = UEgroup(1,3,100000,8000,3,1,'eMBB',10,'','RR','',1,cell1,t_sim,measInterv,env,'S37')
#UEgroup1 = UEgroup(0,5,0,150,0,60,'m-MTC-2',10,'','RR','',1,cell1,t_sim,measInterv,env,'D37')
#UEgroup1 = UEgroup(0,4,0,2000,0,5000,'eMBB-1',20,'','','',1,cell1,t_sim,measInterv,env,'S25')
#UEgroup2 = UEgroup(0,15,0,350,0,10,'eMBB-2',20,'','PF11','',1,cell1,t_sim,measInterv,env,'S20')
UEgroup2 = UEgroup(0,10,0,350,0,6000,'mMTC-1',20,'','RR','',1,cell1,t_sim,measInterv,env,'S5')
#UEgroup3 = UEgroup(0,8,0,1500,0,6,'URLLC-1',5,'','PF11','',1,cell1,t_sim,measInterv,env,'S25')
# UEgroup1 = UEgroup(3,0,10000,0,2,0,'LTE',20,'','RR','',1,cell1,t_sim,measInterv,env,'S37')
UEgroup1 = UEgroup(3,0,50000,0,1,0,'eMBB',20,'','','SU',4,cell1,t_sim,measInterv,env,'S37')
"""Group of users with defined traffic profile, capabilities and service requirements for which the sumulation will run.

More than one can be instantiated in one simulation.
For each one of them, the UEgroup instance must be added in the UEgroups list.

UEgroupN = UEgroup(nuDL,nuUL,pszDL,pszUL,parrDL,parrUL,label,dly,avlty,schedulerType,mimo_mode,layers,cell,hdr,t_sim,measInterv,env,sinr):

label: must contain substring according to the type of service: eMBB, mMTC, URLLC\n
schedulerType: RR: Rounf Robin, PF: Proportional Fair (10, 11)\n
mimo_mode: SU, MU\n
layers: in SU-MIMO is the number of layers/UE, in MU-MIMO is the number of simultaneous UE to serve with the same resources\n
sinr: is a string starting starting with S if all ues have the same sinr or D if not. The value next will be the initial sinr of each ue or the maximum."""

#UEgroup2 = UEgroup(3,3,800000,300,1,10,'eMBB-1',10,'','RR','',1,cell1,t_sim,measInterv,env,'D37')

# Set UEgroups list according to the defined groups!!!
UEgroups = [UEgroup1,UEgroup2]#,UEgroup3]#,UEgroup4]
"""UE group list for the configured simulation"""
#           Slices creation
for ueG in UEgroups:
    interSliceSche1.createSlice(ueG.req['reqDelay'],
    ueG.req['reqThroughputDL'],
    ueG.req['reqThroughputUL'],
    ueG.req['reqAvailability'],
    ueG.num_usersDL,
    ueG.num_usersUL,
    band,
    debMode,
    ueG.mmMd,
    ueG.lyrs,
    ueG.label,
    ueG.sch)

#      Schedulers activation (inter/intra)

procCell = env.process(cell1.updateStsts(env,interv=measInterv,tSim=t_sim))
procInter = env.process(interSliceSche1.resAlloc(env))
for ueG in UEgroups:
    ueG.activateSliceScheds(interSliceSche1,env)

#----------------------------------------------------------------
env.run(until=t_sim)
#----------------------------------------------------------------

#      Closing statistic and debugging files

for slice in list(cell1.slicesStsts.keys()):
    cell1.slicesStsts[slice]['DL'].close()
    cell1.slicesStsts[slice]['UL'].close()
for slice in list(interSliceSche1.slices.keys()):
        interSliceSche1.slices[slice].schedulerDL.dbFile.close()
        if slice != 'LTE':
            interSliceSche1.slices[slice].schedulerUL.dbFile.close()

#----------------------------------------------------------------
#                          RESULTS
#----------------------------------------------------------------
# Show average PLR and Throughput in any case simulation and plots
for UEg in UEgroups:
    print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'                 SLICE: '+UEg.label+'                  '+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'--------------------------------------------------\n'+Format.CEND)
    UEg.printSliceResults(interSliceSche1,t_sim,bw,measInterv)
print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
