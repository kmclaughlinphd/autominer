# autominer
Mines what's best on whattomine.com based on user-provided coin/algo scripts based on "btc_revenue".

I'll put more stuff here later. Getting set up is fairly involved. You need to do the following:

1) Determine your hashrates, via benchmarking or just use whattomine.com defaults; put those values into the mine.py script. If you want to disable a particular algo, enter the hashrate as zero.

2) Set up wallets/pools. Coinomi and Jaxx support a lot of coins. For the others, you should install the "official" wallet clients, e.g., ZCL, GBX, HAL. For pools, I like altminer.net, miningpoolhub.com, and suprnova.cc; though making accounts on the latter is a pain in the ass.

3) Get your miners set up.  
I typically use the following miners:  
Equihash -- ewbf_zec_miner_034b (https://github.com/nanopool/ewbf-miner/releases).   
Mostly everything else -- ccminer222 (https://github.com/tpruvot/ccminer/releases)  
I will research ethash miners soon.

4) Configure your minecmd.csv; I provided an example in the repo. You obviously need to provide your own command lines based on your set up. Make sure you type the algos in *exactly* as they appear in the whattomine.com json file (case insensitive), else it will be ignored.



To do:
1) Allow comments in minecmd.csv; and provide some instructions of getting each coin/algo set up. -- done
2) Re-execute at predetermined intervals; so we're always mining the best coins/algos. -- done
3) Log everything. -- done
4) Some sort of fail-safe? Kill the miner if it's not connecting to the pool, or rejected, etc.
5) Move hashrates into separate file or get them from somewhere on-the-fly. -- done
6) Combine all input files and write a parser for them



Maintained by kirrrbbby <(''<) ^('')^ (>'')>

BTC (lol) 1JrpBozDCm4TUsJfQD1hvtZ2rEhK1bEV9p  
BCH 1LyCM4x97rqmZRSRMTREvgbB3mYhMQvQeK  
LTC LMFmNiMhwqZBEv7Ja4ggZnRuBjuptjdxg4  
ETH 0xe8c40e39c5b36ca44c4c058fc4aec0a931d4d427
