import ctypes
import sys
import yaml
from time import sleep

import os
path = os.path.dirname(os.path.realpath(__file__))

bcmlib = ctypes.CDLL(path+"/lib/libbcm2835.so", mode = ctypes.RTLD_GLOBAL)
gpio   = ctypes.CDLL(path+"/lib/libgpiohb.so")


from functools import wraps
from time import time
def timeit(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        start = time()
        func(*args, **kwargs)
        end = time()
        print('Run time of '+func.__name__+': '+'{:1.3e}'.format(end-start)+' s')
    return wrapped


@timeit
def write_old(trials):
    for trial in trials:
        gpio.write_local_fifo_old(trial)

@timeit
def read_old(nwords, results):
    for i in xrange(nwords):
        results[i] = gpio.read_local_fifo_old()

@timeit
def write_new(trials):
    for trial in trials:
        gpio.write_local_fifo(trial)

@timeit
def read_new(nwords, results):
    for i in xrange(nwords):
        results[i] = gpio.read_local_fifo()


def inRed  (prt): return "\033[91m{}\033[00m" .format(prt)
def inGreen(prt): return "\033[92m{}\033[00m" .format(prt)
def check_matches(trials, results):
    if results==trials:
        print('Reads match writes: '+inGreen('OK'))
    else:
        print(inRed('READS DO NOT MATCH WRITES!'))
        paired = zip(trials,results)
        mismatches = [pair for pair in paired if pair[1]-pair[0] != 0]
        if len(mismatches) < 10:
            print paired
            print mismatches
        print(str(len(mismatches))+' mismatches found')


def run_one(trials, title, wr_fn, rd_fn):
    nwords=len(trials)
    #print
    #print title
    #print('Writing '+str(nwords)+' words')
    wr_fn(trials)
    
    #print('Reading '+str(nwords)+' words')
    results = [None] * nwords
    rd_fn(nwords, results)
    
    check_matches(trials, results)
    

if __name__ == '__main__':

    if bcmlib.bcm2835_init() != 1 :
        print("bcm2835 can not init -> exit")
        sys.exit(1)

    gpio.set_bus_init()
    #clear the fifo by reading way over its depth
    for _ in xrange(33000):
        gpio.read_local_fifo();


    combs = (
        ('1) old write and old read', write_old, read_old),
        ('2) old write and new read', write_old, read_new),
        ('3) new write and old read', write_new, read_old),
        ('4) new write and new read', write_new, read_new),
    )


    seq_trials = [ i for i in range(1<<8)*(1<<7) ]

    print
    print('A) Sequential data: '+str(len(seq_trials))+' words')
    for title, wr_fn, rd_fn in combs:
        run_one(seq_trials, title, wr_fn, rd_fn)

    
    import random
    rand_trials = [ random.randint(0,(1<<8)-1) for _ in xrange(1<<15) ]

    print
    print('B) Random data: '+str(len(rand_trials))+' words')
    for title, wr_fn, rd_fn in combs:
        run_one(rand_trials, title, wr_fn, rd_fn)



