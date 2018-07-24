import sys
import os
import numpy as np
import pdb
import yaml
from createMarketEvents import *

nGroups = int(sys.argv[1])
nPlayersPerGroup = int(sys.argv[2])
nPeriods = int(sys.argv[3])
experimentLengthSeconds = int(sys.argv[4])
experimentLengthMS = experimentLengthSeconds*1000
dateStr = sys.argv[5]
exchangeType = "cda"
subject = "default"
startingWealth = 20
startingPrice = 100
sigJump = 0.5
speedCostList = [0.022]*12
lambdaJVec = [1/3000.0]*12
lambdaIVec = [1/4000.0]*12
maxSpread = 2
initialSpread = maxSpread/2
exchangeRate = 2
filePath = dateStr+"/"
if os.path.isdir(filePath)==False:
    os.mkdir(filePath)
configURLRoot = "https://raw.githubusercontent.com/Leeps-Lab/oTree_HFT_CDA/master/session_config/"+dateStr+"/"
exchangeURI = "exchanges" #"54.219.182.118"

# Generate jump and investor files
createMarketEvents(nGroups,nPeriods,experimentLengthMS,dateStr,lambdaJVec,lambdaIVec,startingPrice,sigJump)

# Create random group assignments
nPlayers = nGroups*nPlayersPerGroup
playerOrder = np.random.choice(range(1,nPlayers+1),nPlayers,replace=False)
groupList = list()
for group in range(nGroups):
    groupList.append(list(playerOrder[range(group*nPlayersPerGroup,(group+1)*nPlayersPerGroup)]))

# Create the yaml file
marketDict = {'matching-engine-host': str(exchangeURI),'design':exchangeType.upper()}
groupDict = {'number-of-groups':nGroups,'players-per-group':nPlayersPerGroup,'group-assignments':str(groupList)}
parametersDict = {'fundamental-price':startingPrice,'max-spread':maxSpread,'initial-spread':initialSpread,
                  'initial-endowment':startingWealth,'speed-cost':speedCostList[0],'session-length':experimentLengthSeconds}
demoDict = {'number-of-participants':nGroups*nPlayersPerGroup}
investorsDict = {}
jumpsDict = {}
filesDict = {'dir':'session_config','folder':dateStr+'/Period1/','investors':investorsDict,'jumps':jumpsDict}
for ix,period in enumerate(range(1,nPeriods+1)):
    sessionDict = {'session_name': dateStr+'_'+exchangeType+'_period_'+str(period),'display_name':'CDA Production'}
    speedCost = speedCostList[ix]
    parametersDict['speed-cost'] = speedCost
    filesDict['folder']  = filePath+'Period'+str(period)+'/'
    if os.path.isdir(filesDict['folder'])==False:
        os.mkdir(filesDict['folder'])
    for group in range(1,nGroups+1):
        marketEventsURL = configURLRoot+"Period"+str(period)+"/investors_period"+str(period)+"_group"+str(group)+".csv"
        priceChangesURL = configURLRoot+"Period"+str(period)+"/jumps_period"+str(period)+"_group"+str(group)+".csv"
        investorsDict['group_'+str(group)] = marketEventsURL
        jumpsDict['group_'+str(group)] = priceChangesURL
    outputDict = {'session':sessionDict, 'market':marketDict,'group':groupDict,
                  'parameters':parametersDict,'files':filesDict, 'demo':demoDict}
    fileName = filesDict['folder']+dateStr+'_'+exchangeType+'_'+str(experimentLengthSeconds)+'s_'+str(nGroups)+'groups_'+str(nPlayersPerGroup)+'players_period'+str(period)+'.yaml'
    with open(fileName, 'w') as outfile:
        yaml.dump(outputDict, outfile, default_flow_style=False)
        os.system('cp '+fileName+' session_configs/')
