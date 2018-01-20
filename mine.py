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

import subprocess, shlex
from threading import Timer


## fill this shit in, cuckboi -- set to zero to disable an algo
#EthHash Groestl X11Gost CryptoN EquiHsh Lyra2v2 NeoScry LBRY___ Blake2b Blake14 Pascal_ SknkHsh
HashRates = \
[35.   , 58.   , 19.5  , 830.  , 685.  , 64000., 1400. , 460.  , 2800. , 4350. , 1700. , 47.5  ]
#EtHash_ Groestl X11Gost CryptoN EquiHsh Lyra2v2 NeoScry LBRY___ Blake2b Blake14 Pascal_ SknkHsh


## leave this one alone -- used for renormalization of the json file
# LEAVE THIS THE FUCK ALONE LEAVE THIS THE FUCK ALONE LEAVE THIS THE FUCK ALONE
RenormRates = \
[84., 63.9, 20.1, 2190., 870., 14700., 1950., 315., 3450., 5910., 2100., 54.]
# LEAVE THIS THE FUCK ALONE LEAVE THIS THE FUCK ALONE LEAVE THIS THE FUCK ALONE


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


## create a coin object that is used in the coin revenue ranking array
class coin(object):
    def __init__(self, tag, algoname, baseRevenue):
        # convert to ascii
        self.tag = tag.encode('utf-8')
        algoname = algoname.encode('utf-8')

        # get rid of non-alphanumerics in the algo name, and assign enum
        algoname = re.sub(r'\W+', '', algoname)
        self.algo = algoenum[algoname]

        # get base revenue (normalized to 3x 480's)
        self.baseRevenue = baseRevenue

    def coinKey(self):
        return self.tag.lower() + self.algo.name.lower()

    def calcRevenue(self):
        # calculate the revenue based on entered hash rates
        self.revenue = float(self.baseRevenue) * HashRates[self.algo.value]/RenormRates[self.algo.value]

    def printCoin(self):
        print self.tag, self.algo.name, self.revenue

    def strCoin(self):
        return self.tag + ' ' + self.algo.name


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



## parse json and return ranked coin list
def GetCoinRanking(inJson):

    # will populate this array with coins
    ranking = []

    # read json and parse
    data = json.load(open(inJson.name))
    coindata = data['coins']

    # create a coin object for each key
    for c in coindata.keys():
        cTag = coindata[c][u'tag']
        cAlgo = coindata[c][u'algorithm']
        cReward = coindata[c][u'btc_revenue']
        ranking.append(coin(cTag, cAlgo, cReward))
        ranking[-1].calcRevenue()

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
    print logstring
    logfile.write(logstring)


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

    # parse it and rank coins based on revenue
    ranking = GetCoinRanking(tmpJson)

    # remove temp file
    os.remove(tmpJson.name)

    # read scripts from csv file and make dictionary
    mineScripts = getScriptDict()

    # try running scripts here

    for ii in xrange(20):
        if ranking[ii].coinKey() in mineScripts:
            PrintAndLog(logfile, time.strftime("%Y-%M-%d %H:%M:%S") + ": mining " + ranking[ii].strCoin())
            # remove extra whitespace from command line, then execute
            cmdline = " ".join(mineScripts[ranking[ii].coinKey()].split())
            #subprocess.call(cmdline, shell=True, timeout=timeout)
            run(cmdline, timeout)
            break
        else:
            PrintAndLog(logfile, time.strftime("%Y-%M-%d %H:%M:%S") + ": skipping " + ranking[ii].strCoin())


def main():
    timeout = 1200 #seconds
    logfile = open('automine.log.' + time.strftime("%Y%M%d%H%M%S"), 'wb')
    while True:
        startMiner(logfile, timeout)

if __name__ == '__main__':
    main()

