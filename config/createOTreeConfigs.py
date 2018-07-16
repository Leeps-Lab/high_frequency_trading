import sys
import pdb
from createMarketEvents import *

nGroups = int(sys.argv[1])
nPlayersPerGroup = int(sys.argv[2])
nPeriods = int(sys.argv[3])
experimentLength = int(sys.argv[4])*1000
dateStr = sys.argv[5]
exchangeType = "cda"
subject = "default"
startingWealth = 200000
speedCostList = [0.022]*12
lambdaJVec = [1/1000.0]*12
lambdaIVec = [1/2000.0]*12
maxSpread = 20000
exchangeRate = 20000
filePath = dateStr+"/"+sys.argv[4]+"/"
marketEventsURLRoot = "https://raw.githubusercontent.com/Leeps-Lab/oTree_HFT_CDA/master/config/"+dateStr+"/Investors/investors_period"
priceChangesURLRoot = "https://raw.githubusercontent.com/Leeps-Lab/oTree_HFT_CDA/master/config/"+dateStr+"/Jumps/jumps_period"
exchangeURI = "54.219.182.118"

# Generate jump and investor files
createMarketEvents(nGroups,nPeriods,experimentLength,dateStr,lambdaJVec,lambdaIVec)

groupList = list()
for group in range(1,nGroups+1):
    groupList.append(range((group-1)*nPlayersPerGroup+1,group*nPlayersPerGroup+1))

for ix,period in enumerate(range(1,nPeriods+1)):
    speedCost = speedCostList[ix]
    marketEventsURL = marketEventsURLRoot+str(period)+"_group1.csv"
    priceChangesURL = priceChangesURLRoot+str(period)+"_group1.csv" 
    fName = filePath+exchangeType+"_config_"+str(int(experimentLength/1000))+"s_"+str(nGroups)+"groups_"+str(nPlayersPerGroup)+"players_"+"period"+str(period)+".csv"
    fOut = open(fName,"w")
    fOut.write("period,subject,groups,startingWealth,speedCost,maxSpread,marketEventsURL,priceChangesURL,NULL,experimentLength,exchangeRate,exchangeURI,sessionNumber\n")
    fOut.write("1,"+subject+",\""+str(groupList).replace(" ","")+"\","+str(startingWealth)+","+str(speedCost)+","+str(maxSpread)+","+marketEventsURL+","+priceChangesURL+",'',"+str(experimentLength)+","+str(exchangeRate)+","+exchangeURI+","+str(period))
    fOut.close()
