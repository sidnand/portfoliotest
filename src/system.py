# CODE FOR RUNNING THE MODELS USING THE DATA

import numpy as np

from src.m import *
from src.models.ew import EqualWeightModel
from src.models.minVar import MinVariance

class System:
    
    """
        param riskFree : [M x 1] array of risk free assets
        param risky : [M x N] array of risky assets
        param M : estimation window length
    """
    def __init__(self, riskFree, risky, M):
        self.policies = [
            EqualWeightModel(),
            MinVariance()
        ]

        self.riskFree = riskFree
        self.risky = risky
        self.M = M

        self.ROWS = len(riskFree)
        self.COLS = 1 + np.shape(risky)[1]
        self.N = self.COLS - 1 # number of risky variables

    def addPolicy(self, model):
        self.policies.append(model)

    """
        Computes the sharpe ratios of all the portfolio policies

        returns : Object of floas denoting the sharpe ratio of each portfolio policy
    """
    def getSharpeRatios(self):
        w = {} # portfolio policy weights
        wBuyHold = {} # portfolio weights before rebalancing
        outSample = {} # out of sample returns

        # for i in Policy:
        #     w[i.value] = np.empty((self.N, self.ROWS - self.M))
        #     wBuyHold[i.value] = np.empty((self.N, self.ROWS - self.M))
        #     outSample[i.value] = np.empty((1, self.ROWS - self.M))

        for i in self.policies:
            w[i.__str__()] = np.empty((self.N, self.ROWS - self.M))
            wBuyHold[i.__str__()] = np.empty((self.N, self.ROWS - self.M))
            outSample[i.__str__()] = np.empty((1, self.ROWS - self.M))

        T = len(self.risky) # time period
        nSubsets = 1 if self.M == T else T - self.M # if M is the same as time period, then we only have 1 subset

        for shift in range(0, nSubsets):

            riskySubset = self.risky[shift:self.M + shift, :]
            riskFreeSubset = self.riskFree[shift:self.M + shift]
            subset = np.column_stack((riskFreeSubset, riskySubset))

            nRisky = len(riskySubset)
            
            mu_horz = np.array([np.mean(riskFreeSubset)])
            mu = np.append(mu_horz, np.vstack(riskySubset.mean(axis = 0)))
            
            totalSigma = np.cov(subset.T)
            sigma = (self.M - 1) / (self.M - self.N - 2) * np.cov(riskySubset.T)
            
            sigmaMLE = (self.M - 1) / self.M * np.cov(riskySubset.T)
            invSigmaMLE = np.linalg.inv(sigmaMLE)

            AMLE = np.ones((1, self.COLS - 1)).dot(invSigmaMLE).dot(np.ones((self.COLS - 1, 1)))

            data = dict(
                cols = self.COLS,
                invSigmaMLE = invSigmaMLE,
                sigmaMLE = sigmaMLE,
                AMLE = AMLE,
                N = self.N,
                M = self.M
            )

            for i in self.policies:
                alpha = i.run(data)
                w[i.__str__()][:, shift] = alpha[:, 0]
            
            # # 5: minimum-variance
            # alphaMV = minVar(invSigmaMLE, AMLE, self.COLS)
            # w[Policy.MINIMUM_VAR][:, shift] = alphaMV[:, 0]

            # # 10: minimum-variance shortsell constraints
            # minVarCon = minVarShortSellCon(sigmaMLE)
            # w[Policy.MINIMUM_VAR_CONSTRAINED][:, shift] = minVarCon[:, 0]

            # # 11: minimum-variance generalized constraints
            # minVarGCon = jagannathanMa(sigma)
            # w[Policy.MINIMUM_VAR_GENERALIZED_CONSTRAINED][:, shift] = minVarGCon[:, 0]

            # # 12 : Kan and Zhou’s (2007) “three-fund” model
            # alphaKanZhouEw = kanZhouEw(self.N, self.M, sigma)
            # w[Policy.KAN_ZHOU_EW][:, shift] = alphaKanZhouEw[:, 0]

            # MEAN-VARIANCE Models

            # buy and hold
            if shift == 0:
                for i in self.policies:
                    alpha = i.run(data)
                    w[i.__str__()][:, shift] = alpha[:, 0]
                # wBuyHold[Policy.EW][:, shift]= alphaTew[:, 0]
                # wBuyHold[Policy.MINIMUM_VAR][:, shift]= alphaMV[:, 0]
                # wBuyHold[Policy.MINIMUM_VAR_CONSTRAINED][:, shift] = minVarCon[:, 0]
                # wBuyHold[Policy.MINIMUM_VAR_GENERALIZED_CONSTRAINED][:, shift] = minVarGCon[:, 0]
                # wBuyHold[Policy.KAN_ZHOU_EW][:, shift] = alphaKanZhouEw[:, 0]
            else:
                for i in self.policies:
                    wBuyHold[i.__str__()][:, shift] = self.buyHold(w[i.__str__()][:, shift - 1], shift)
                # wBuyHold[Policy.EW][:, shift] = self.buyHold(w[Policy.EW][:, shift - 1], shift)
                # wBuyHold[Policy.MINIMUM_VAR][:, shift] = self.buyHold(w[Policy.MINIMUM_VAR][:, shift - 1], shift)
                # wBuyHold[Policy.MINIMUM_VAR_CONSTRAINED][:, shift] = self.buyHold(w[Policy.MINIMUM_VAR_CONSTRAINED][:, shift - 1], shift)
                # wBuyHold[Policy.MINIMUM_VAR_GENERALIZED_CONSTRAINED][:, shift] = self.buyHold(w[Policy.MINIMUM_VAR_GENERALIZED_CONSTRAINED][:, shift - 1], shift)
                # wBuyHold[Policy.KAN_ZHOU_EW][:, shift] = self.buyHold(w[Policy.KAN_ZHOU_EW][:, shift - 1], shift)
                
            if (nSubsets > 1):
                # out of sample returns
                for i in self.policies:
                    alpha = i.run(data)
                    outSample[i.__str__()][:, shift] = self.outOfSampleReturns(alpha, shift)[:, 0]
                # outSample[Policy.EW][:, shift] = self.outOfSampleReturns(alphaTew, shift)[:, 0]
                # outSample[Policy.MINIMUM_VAR][:, shift] = self.outOfSampleReturns(alphaMV, shift)[:, 0]
                # outSample[Policy.MINIMUM_VAR_CONSTRAINED][:, shift] = self.outOfSampleReturns(minVarCon, shift)[:, 0]
                # outSample[Policy.MINIMUM_VAR_GENERALIZED_CONSTRAINED][:, shift] = self.outOfSampleReturns(minVarGCon, shift)[:, 0]
                # outSample[Policy.KAN_ZHOU_EW][:, shift] = self.outOfSampleReturns(alphaKanZhouEw, shift)[:, 0]

        sharpeRatios = {}
        for i in self.policies:
            sharpeRatios[i.__str__()] = round(self.sharpeRato(outSample[i.__str__()]), 4)

        return sharpeRatios

    """
        Computes a new portfolio weight after a shift

        param w : [n, row - M] array, holds portfolio weights of a specific policy
        param j : integer value, represents current shift position
    """
    def buyHold(self, w, j):

        a = (1 - sum(w)) * (1 + self.riskFree[self.M + j])
        b = (1 + (self.risky[self.M + j, :].T + self.riskFree[self.M + j]))[np.newaxis].T
        trp = a + w[np.newaxis].dot(b)
        
        return ((w * (1 + (self.risky[self.M + j, :]).T + self.riskFree[self.M + j])) / trp)

    """
        Computes the out of sample returns

        param w : [n, row - M] array, holds portfolio weights of a specific policy
        param j : integer value, represents current shift position
    """
    def outOfSampleReturns(self, w, j):
        return w.T.dot(self.risky[self.M + j, :][np.newaxis].T)

    """
        Computes the Sharpe ratio

        param x : [1, rows - M] array, holds the out of sample return values

        returns : real number
    """
    def sharpeRato(self, x):
        mean = np.mean(x.T)
        std = np.std(x.T, ddof = 1)
        
        if (abs(mean) > pow(10, -16)):
            sr = mean / std;
        else:
            sr = None
                
        return sr