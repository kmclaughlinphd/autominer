#-------------------------------------------------------------------------------
# Name:        lets fuckin mine
# Author:      kirrrbbbyPhD
# Created:     18/01/2018
# Copyright:   (c) kirrrbbbyPhD 2018
#-------------------------------------------------------------------------------

import os, time
import urllib2, json, tempfile
import re
import csv
from enum import Enum
import sys, traceback

import subprocess, shlex
from threading import Timer

class algoenum(Enum):
    Ethash = 0
    Groestl = 1
    MyriadGroestl = 1
    X11Gost = 2
    CryptoNight = 3
    Equihash = 4
    Lyra2REv2 = 5
    NeoScrypt = 6
    LBRY = 7
    Blake2b = 8
    Blake14r = 9
    Pascal = 10
    Skunkhash = 11
    NIST5 = 12

    DEFAULT = 99

def myEnum(strArg):
    try:
        return algoenum[strArg]
    except:
        print "warning: algo " + strArg + " not supported."
        return algoenum['DEFAULT']


## create a coin object that is used in the coin revenue ranking array
class coin(object):
    def __init__(self, tag, algoname, baseRevenue, baseReward, baseReward24h):
        # convert to ascii
        self.tag = tag.encode('utf-8')
        algoname = algoname.encode('utf-8')

        # get rid of non-alphanumerics in the algo name, and assign enum
        algoname = re.sub(r'\W+', '', algoname)
        #self.algo = algoenum[algoname]
        self.algo = myEnum(algoname)

        # get base revenue (in btc) and rewards (normalized to 3x 480's)
        self.__baseRevenue = baseRevenue
        self.__baseReward = baseReward
        self.__baseReward24h = baseReward24h

        # compute these when calcRewards() is called
        self.revenue = False
        self.reward = False
        self.reward24h = False

    # used as dictionary key when comparing with available mining scripts
    def coinKey(self):
        return self.tag.lower() + self.algo.name.lower()

    # renormalize rewards/revenue
    def calcRewards(self, hashrates, defaultrates):
        # calculate the revenue based on entered hash rates
        if self.algo == self.algo.DEFAULT:
            hashRatio = 0.0 #just don't mine if the algo hashrate isn't known
        else:
            hashRatio = hashrates[self.algo.value]/defaultrates[self.algo.value]

        #btc revenue (per day)
        self.revenue = float(self.__baseRevenue) * hashRatio
        #reward per day (based on NOW rate)
        self.reward = float(self.__baseReward) * hashRatio
        # (based 24h average)
        self.reward24h = float(self.__baseReward24h) * hashRatio

    # used for logging
    def strCoin(self):
        return self.tag + ' ' + self.algo.name

    # get reward for mining for *timeout* seconds
    def actualReward(self, timeout):
        return self.reward * timeout / float(24*60*60)



## grab coin data from whattomine, return temp file handle
def GetWTMJson():
    url = 'http://whattomine.com/coins.json'
    opener = urllib2.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    response = opener.open(url)

    # create a temp file to store downloaed json
    tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    tmp.write(response.read())
    tmp.close()

    return tmp


## read in hashrates and default rates from csv files;
## used for renormalizing rewards
def GetHashRates():

    # get default hashrates from csv
    with open('defaultrates.csv') as f_dr:
        reader = csv.reader(f_dr)
        for row in reader:
            # skip commented lines
            if row[0].strip()[0] == '#': continue
            # read in hashrates
            if len(row) == 13:
                defaultrates = [ float(r) for r in row ]

    # get our hashrates from csv
    with open('hashrates.csv') as f_hr:
        reader = csv.reader(f_hr)
        for row in reader:
            # skip commented lines
            if row[0].strip()[0] == '#': continue
            # read in hashrates
            if len(row) == 13:
                hashrates = [ float(r) for r in row ]

    return hashrates, defaultrates


## parse json and return ranked coin list
def GetCoinRanking(inJson, hashrates, defaultrates):

    # will populate this array with coins
    ranking = []

    # read json and parse
    data = json.load(open(inJson.name))
    coindata = data['coins']

    # create a coin object for each key
    for c in coindata.keys():
        # coin name
        cTag = coindata[c][u'tag']
        # mining algorithm
        cAlgo = coindata[c][u'algorithm']
        # revenue in btc for "default" rig per 24h
        cBtcRevenue = coindata[c][u'btc_revenue']
        # reward for "default" rig per 24h based on current rate of return
        cReward = coindata[c][u'estimated_rewards']
        # reward based on 24h average
        cReward24h = coindata[c][u'estimated_rewards24']

        # create coin, append to array, and compute renormalized rewards/revenue
        ranking.append(coin(cTag, cAlgo, cBtcRevenue, cReward, cReward24h))
        ranking[-1].calcRewards(hashrates, defaultrates)

    # sort based on revenue
    ranking.sort(key = lambda x: x.revenue, reverse = True)

    return ranking


# read scripts from csv file and make dictionary
def getScriptDict():

    scripts = {}

    with open('minecmd.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 3:
                # skip commented lines
                if row[0].strip()[0] == '#':
                    continue
                # add dictionary entry for this csv entry
                scripts[row[0].lower()+row[1].lower()] = row[2]

    return scripts


def PrintAndLog(logfile, logstring):
    logfile.write(logstring+'\n')
    logfile.flush()
    print logstring


# since python 2 doesn't support subprocess timeout, we use this
# stolen from  https://stackoverflow.com/questions/1191374/using-module-subprocess-with-timeout
def run(cmd, timeout_sec):

    # this will suppress output, which we don't want // added posix=False so it doesn't butcher backslashes
    #proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc = subprocess.Popen(shlex.split(cmd, posix=False))
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        stdout, stderr = proc.communicate()
    finally:
        timer.cancel()


# figures out which coin we want to mine, and starts the miner
def startMiner(logfile, timeout=600):

    # get Json
    tmpJson = GetWTMJson()

    # get hashrates from files
    hashrates, defaultrates = GetHashRates()

    # parse it and rank coins based on revenue
    ranking = GetCoinRanking(tmpJson, hashrates, defaultrates)

    # remove temp file
    os.remove(tmpJson.name)

    # read scripts from csv file and make dictionary
    mineScripts = getScriptDict()

    # try running scripts here

    for ii in xrange(20):
        if ranking[ii].coinKey() in mineScripts:
            PrintAndLog(logfile, time.strftime("%Y-%M-%d %H:%M:%S") \
                + ": mining " + ranking[ii].strCoin() \
                + "; est_reward: " + str(ranking[ii].actualReward(timeout)))

            # remove extra whitespace from command line, then execute
            cmdline = " ".join(mineScripts[ranking[ii].coinKey()].split())
            #subprocess.call(cmdline, shell=True, timeout=timeout)
            run(cmdline, timeout)
            break
        else:
            PrintAndLog(logfile, time.strftime("%Y-%M-%d %H:%M:%S") \
                + ": skipping " + ranking[ii].strCoin())


def main():
    timeout = 1200 #seconds
    logfile = open('automine.log.' + time.strftime("%Y%M%d%H%M%S"), 'wb')
    while True:
        startMiner(logfile, timeout)

if __name__ == '__main__':
    try:
        main()
    except:
        print sys.exc_info()[0]
        print traceback.format_exc()
        print "Press Enter to continue ..."
        raw_input()

