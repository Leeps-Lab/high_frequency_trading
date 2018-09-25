import numpy as np
import pandas as pd
import pdb
import os

def createMarketEvents(rootPath,investorFile,jumpFile,periodLength,filePath,lambdaJ,lambdaI,startPrice,sigJump):

    # Parameters for jump distribution
    startPrice = startPrice
    muJump = 0
    sigJump = sigJump
    
    # Parameters for jump times
    nSimJ = int(2*periodLength*lambdaJ)
  
    # Investor parameters
    nSimI = int(2*periodLength*lambdaI)
    buyProb = 0.5
  
    # Simulate times and sizes
    jumpTimes = np.cumsum(np.around(np.random.exponential(1/lambdaJ,nSimJ)))
    jumpTimes = np.hstack((jumpTimes[jumpTimes < periodLength], jumpTimes[jumpTimes >= periodLength][0]))
    jumpTimes = np.around(jumpTimes/1000.0,3)
    nJump = len(jumpTimes)
    jumpSizes = startPrice + np.cumsum(np.random.normal(muJump,sigJump,nJump))
    jumpSizes = (10000*jumpSizes).astype(int)

    # Save jumps to CSV
    jumpData = pd.DataFrame({'time':jumpTimes,'size':jumpSizes},columns=['time','size'])
    if os.path.isfile(rootPath+'/'+jumpFile):
        raise OSError('Attempted to create a file that already exists.')
    if os.path.isdir(os.path.dirname(rootPath+'/'+jumpFile))==False:
        os.makedirs(os.path.dirname(rootPath+'/'+jumpFile))
    jumpData.to_csv(rootPath+'/'+jumpFile,index=False)

    # Simulate investor arrivals and directions
    investorTimes = np.cumsum(np.around(np.random.exponential(1/lambdaI,nSimI)))
    investorTimes = np.hstack((investorTimes[investorTimes < periodLength], investorTimes[investorTimes >= periodLength][0]))
    investorTimes = np.around(investorTimes/1000.0,3)
    nInvestor = len(investorTimes)
    investorDirections = np.random.binomial(1,buyProb,nInvestor)
    investorDirections = investorDirections.astype(str)
    investorDirections[investorDirections=='1'] = 'B'
    investorDirections[investorDirections=='0'] = 'S'

    # Save investor arrivals to CSV
    investorData = pd.DataFrame({'time':investorTimes,'direction':investorDirections},columns=['time','direction'])
    if os.path.isfile(rootPath+'/'+investorFile):
        raise OSError('Attempted to create a file that already exists.')
    if os.path.isdir(os.path.dirname(rootPath+'/'+investorFile))==False:
        os.makedirs(os.path.dirname(rootPath+'/'+investorFile))
    investorData.to_csv(rootPath+'/'+investorFile,index=False)