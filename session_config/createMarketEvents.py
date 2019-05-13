import numpy as np
import pandas as pd
import pdb
import os


# grid definition

max_ask = 2147483647
min_bid = 0


def price_grid(price, gridsize=1e4):
    integer_price = int(price)
    if integer_price < min_bid:
        integer_price = min_bid
    elif integer_price > max_ask:
        integer_price = max_ask
    grid_formula = round((integer_price - min_bid) / gridsize)
    grid_price = int(grid_formula * gridsize)
    return grid_price

vector_grid = np.vectorize(price_grid)


def createMarketEvents(rootPath,investorFile,jumpFile,periodLength,lambdaJ,lambdaI,startPrice,
                       sigJump,muI,sigI,lambdaTIF,tifRandomFlag,csvFlag, grid=vector_grid):


    # JUMPS

    # Parameters for jump distribution
    startPrice = startPrice
    muJump = 0
    sigJump = sigJump
    
    # Parameters for jump times
    nSimJ = int(2*periodLength*lambdaJ)

    # Simulate times and sizes
    np.random.seed(59337)
    jumpTimes = np.cumsum(np.random.exponential(1/lambdaJ,nSimJ))
    jumpTimes = np.hstack((jumpTimes[jumpTimes < periodLength], jumpTimes[jumpTimes >= periodLength][0]))
    jumpTimes = np.around(jumpTimes,3)
    nJump = len(jumpTimes)
    jumpSizes = startPrice + np.cumsum(np.random.normal(muJump,sigJump,nJump))
    jumpSizes = (10000*jumpSizes).astype(int)

    # Save jumps to CSV
    jumpData = pd.DataFrame({'Time':jumpTimes,'V':jumpSizes})
    if csvFlag:
        if os.path.isfile(rootPath+'/'+jumpFile):
            raise OSError('Attempted to create a file that already exists.')
        if os.path.isdir(os.path.dirname(rootPath+'/'+jumpFile))==False:
            os.makedirs(os.path.dirname(rootPath+'/'+jumpFile))
        jumpData.to_csv(rootPath+'/'+jumpFile,index=False)

    # Investor parameters
    #nSimI = int(2*periodLength*lambdaI)
    nSimI = np.random.poisson(lam=lambdaI*periodLength,size=1)
    buyProb = 0.5

    # Simulate investor arrivals and directions
    np.random.seed(2)
    investorTimes = np.sort(np.random.uniform(low=0,high=periodLength,size=nSimI))
    investorTimes = np.around(investorTimes,3)
    investorDirections = 2*np.random.binomial(1,buyProb,nSimI) - 1
    investorV = jumpData.V.asof(investorTimes)
    investorPrices = (investorV + 10000*np.random.normal(muI,sigI,nSimI)*investorDirections).astype('int')
    investorPrices = vector_grid(investorPrices)
    investorDirections = investorDirections.astype(str)
    investorDirections[investorDirections=='1'] = 'S'
    investorDirections[investorDirections=='-1'] = 'B'
    if tifRandomFlag:
        investorTimeInForces = np.random.exponential(lambdaTIF,nSimI)
    else:
        investorTimeInForces = lambdaTIF
    
    # Save investor arrivals to CSV
    investorData = pd.DataFrame({'arrival_time':investorTimes,'buy_sell_indicator':investorDirections,
                                 'price':investorPrices,'time_in_force':investorTimeInForces})
    if csvFlag:
        if os.path.isfile(rootPath+'/'+investorFile):
            raise OSError('Attempted to create a file that already exists.')
        if os.path.isdir(os.path.dirname(rootPath+'/'+investorFile))==False:
            os.makedirs(os.path.dirname(rootPath+'/'+investorFile))
        investorData.to_csv(rootPath+'/'+investorFile,index=False)
    else:
        return(investorData)