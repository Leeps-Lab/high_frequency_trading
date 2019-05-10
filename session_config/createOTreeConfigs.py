import sys
import os
import numpy as np
import pdb
import yaml
from createMarketEvents import *

# Session variables
nGroups = 5 #int(sys.argv[1])
nPeriods = 2 #int(sys.argv[3])
periodLengthSeconds = 240 #int(sys.argv[4])
trialLengthSeconds = 0 #int(sys.argv[5])
participationFee = 4
currency = 'EUR'
exchangeRate = 1.5
randomRoundPayment = False
sessionKey = 'CologneTest6x5'

# Configuration variables
differentDrawsForGroups = True
createDraws = True
filePath = sessionKey #sys.argv[6]+"/"
configURLRoot = "https://raw.githubusercontent.com/Leeps-Lab/oTree_HFT_CDA/master/session_config/"
exchangeURI = "localhost"
rootPath = os.getcwd()+'/'+filePath

# Environment variables
maxSpread = 2
initialSpread = maxSpread/2
startingWealth = 20

# Economic variables
nPlayersPerGroup = 6 #int(sys.argv[2])
batchLength = 3
exchangeType = "FBA"
startingPrice = 100
sigJump = 0.5
speedCost = 0.022
lambdaJ = 1/3.0
lambdaI = 1/4.0

# Determine if there will be a trial period
if trialLengthSeconds==0:
    trialFlag = 0
else:
    trialFlag = 1
if exchangeType == 'CDA':
    batchLength = 0
    
# Create file names for investors and jumps
investorFiles = list()
jumpFiles = list()
for group in range(1,nGroups+1):
    investorFilesGroup = list()
    jumpFilesGroup = list()
    if differentDrawsForGroups:
        draw = group
    else:
        draw = 1
    if trialFlag:
        investorFilesGroup.append("Trial"+str(draw)+"/investors_trial.csv")
        jumpFilesGroup.append("Trial"+str(draw)+"/jumps_trial.csv")
    for period in range(1,nPeriods+1):
        investorFilesGroup.append("Draw"+str(draw)+"/investors_period"+str(period)+".csv")
        jumpFilesGroup.append("Draw"+str(draw)+"/jumps_period"+str(period)+".csv")
    investorFiles.append(investorFilesGroup)
    jumpFiles.append(jumpFilesGroup)
    
# Either create files or check that they exist
if differentDrawsForGroups:
    nDraws = nGroups
else:
    nDraws = 1
nPeriodsWithTrial = nPeriods
if trialFlag:
    nPeriodWithTrial = nPeriodsWithTrial+1;
for draw in range(nDraws):
    investorFilesForGroup = investorFiles[draw]
    jumpFilesForGroup = jumpFiles[draw]
    for period in range(nPeriodsWithTrial):
        if createDraws == True:
            createMarketEvents(rootPath,investorFilesForGroup[period],jumpFilesForGroup[period],
                               periodLengthSeconds,lambdaJ,lambdaI,startingPrice,sigJump)
        else:
            if ((os.path.isfile(rootPath+'/'+jumpFilesForGroup[period])==False)| 
                (os.path.isfile(rootPath+'/'+investorFilesForGroup[period])==False)):
                raise OSError('File does not exist.')

# Create random group assignments
nPlayers = nGroups*nPlayersPerGroup
playerOrder = np.random.choice(range(1,nPlayers+1),nPlayers,replace=False)
groupList = list()
for group in range(nGroups):
    groupList.append(list(playerOrder[range(group*nPlayersPerGroup,(group+1)*nPlayersPerGroup)]))

# Create the yaml file
marketDict = {'matching-engine-host': str(exchangeURI),'design':exchangeType.upper()}
groupDict = {'number-of-groups':nGroups,'players-per-group':nPlayersPerGroup,'group-assignments':str(groupList)}
trialDict = {'run':trialFlag,'trial-length':trialLengthSeconds}
parametersDict = {'fundamental-price':startingPrice,'max-spread':maxSpread,
                  'initial-spread':initialSpread,'initial-endowment':startingWealth,
                  'speed-cost':speedCost,'lambda-i':lambdaI,'lambda-j':lambdaJ,
                  'session-length':periodLengthSeconds,'batch-length':batchLength}
demoDict = {'number-of-participants':nPlayers*nGroups}
directoryDict = {'folder':filePath}
sessionDict = {'session-name': sessionKey,'display-name':'CDA Production',
               'num-rounds':nPeriods,'currency':currency,'exchange-rate':exchangeRate,
               'random-round-payment':randomRoundPayment,'participation-fee':participationFee}
investorsDict = {}
jumpsDict = {}
for group in range(nGroups):
    investorsDict['group_'+str(group+1)] = investorFiles[group]
    jumpsDict['group_'+str(group+1)] = jumpFiles[group]
outputDict = {'session':sessionDict, 'market':marketDict,'group':groupDict, 'investors':investorsDict,
              'jumps':jumpsDict, 'parameters':parametersDict,'directory':directoryDict, 'demo':demoDict,'trial':trialDict}
fileName = 'session_configs/'+exchangeType+'_'+str(nGroups)+'groups_'+str(nPlayersPerGroup)+'players.yaml'
with open(fileName, 'w') as outfile:
    yaml.dump(outputDict, outfile, default_flow_style=False)
