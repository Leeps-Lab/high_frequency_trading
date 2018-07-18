import numpy as np
import pandas as pd
import pdb

def createMarketEvents(nGroups,nPeriods,experimentLength,dateStr,lambdaJVec,lambdaIVec,startPrice,sigJump):
  
  # Output file
  #filePath = "/Users/ealdrich/Dropbox/Academics/Research/UCSC/oTree_HFT_CDA/config/"+dateStr+"/"
  filePath = dateStr+"/"

  # Parameters for jump distribution
  startPrice = startPrice
  muJump = 0
  sigJump = sigJump

  for ix,periodVal in enumerate(range(1,nPeriods+1)):
    
    # Parameters for jump times
    lambdaJ = lambdaJVec[ix]
    nSimJ = int(2*experimentLength*lambdaJ)
  
    # Investor parameters
    lambdaI = lambdaIVec[ix]
    nSimI = int(2*experimentLength*lambdaI)
    buyProb = 0.5
  
    for groupVal in range(1,nGroups+1):

      # Simulate times and sizes
      jumpTimes = np.cumsum(np.around(np.random.exponential(1/lambdaJ,nSimJ)))
      jumpTimes = np.hstack((jumpTimes[jumpTimes < experimentLength], jumpTimes[jumpTimes >= experimentLength][0]))
      jumpTimes = np.around(jumpTimes/1000.0,3)
      nJump = len(jumpTimes)
      jumpSizes = startPrice + np.cumsum(np.random.normal(muJump,sigJump,nJump))
      jumpSizes = (10000*jumpSizes).astype(int)

      # Save jumps to CSV
      jumpData = pd.DataFrame({'time':jumpTimes,'size':jumpSizes},columns=['time','size'])
      jumpFile = filePath+"Period"+str(periodVal)+"/jumps_period"+str(periodVal)+"_group"+str(groupVal)+".csv"
      jumpData.to_csv(jumpFile,index=False)

      # Simulate investor arrivals and directions
      investorTimes = np.cumsum(np.around(np.random.exponential(1/lambdaI,nSimI)))
      investorTimes = np.hstack((investorTimes[investorTimes < experimentLength], investorTimes[investorTimes >= experimentLength][0]))
      investorTimes = np.around(investorTimes/1000.0,3)
      nInvestor = len(investorTimes)
      investorDirections = np.random.binomial(1,buyProb,nInvestor)
      investorDirections = investorDirections.astype(str)
      investorDirections[investorDirections=='1'] = 'B'
      investorDirections[investorDirections=='0'] = 'S'

      # Save investor arrivals to CSV
      investorData = pd.DataFrame({'time':investorTimes,'direction':investorDirections},columns=['time','direction'])
      investorFile = filePath+"Period"+str(periodVal)+"/investors_period"+str(periodVal)+"_group"+str(groupVal)+".csv"
      investorData.to_csv(investorFile,index=False)
