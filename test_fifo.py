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
def write_old(data):
    for value in data:
        gpio.write_local_fifo_old(value)

@timeit
def read_old(nwords, readback):
    for i in xrange(nwords):
        readback[i] = gpio.read_local_fifo_old()

@timeit
def write_new(data):
    for value in data:
        gpio.write_local_fifo(value)

@timeit
def read_new(nwords, readback):
    for i in xrange(nwords):
        readback[i] = gpio.read_local_fifo()

def bin8(val): return '{:08b}'.format(val)
def inRed  (prt): return "\033[91m{}\033[00m" .format(prt)
def inGreen(prt): return "\033[92m{}\033[00m" .format(prt)
from pprint import pprint
def check_matches(written, readback):
    if readback==written:
        print('Reads match writes: '+inGreen('OK'))
    else:
        print(inRed('READS DO NOT MATCH WRITES!'))
        paired = zip(written,readback)
        mismatches = [
            (i, map(bin8, pair), bin8(pair[0]^pair[1]))
            for i, pair in enumerate(paired)
            if pair[1]-pair[0] != 0
        ]
        pprint(('fifo_pos', ['writen', 'readback'], 'written XOR readback'))
        if len(mismatches) < 20:
            pprint(mismatches)
        else:
            pprint(mismatches[:20])
            print('...')
        print(str(len(mismatches))+' mismatches found')


def run_once(data, title, wr_fn, rd_fn):
    wr_fn(data)
    #print(gpio.read_usedw()) #This seems to always be zero
    nwords=len(data)
    readback = [None] * nwords
    rd_fn(nwords, readback)
    check_matches(data, readback)

def clear_fifo():
    #clear the fifo by reading way over its depth
    for _ in xrange(1<<15+1):
        gpio.read_local_fifo()


if __name__ == '__main__':

    if not bcmlib.bcm2835_init():
        print("bcm2835 can not init -> exit")
        sys.exit(1)

    if not gpio.set_bus_init() == 0:
        print("gpiohb can not init -> exit")
        sys.exit(1)
        
    clear_fifo()

    combs = (
        #('1) old write and old read', write_old, read_old),
        #('2) old write and new read', write_old, read_new),
        #('3) new write and old read', write_new, read_old),
        ('4) new write and new read', write_new, read_new),
    )

    import random
    data = (
        ('Alternating 0x55-0xaa', [0x55,0xaa]*(1<<14) ),
        #('Alternating 0x33-0xcc', [0x33,0xcc]*(1<<14) ),
        #('Alternating 0x0f-0xf0', [0x0f,0xf0]*(1<<14) ),
        #('Alternating 0x00-0xff', [0x00,0xff]*(1<<14) ),
        #('Walking ones',          [ 1<<(i%8) for i in xrange(1<<15)]),
        #('Walking zeroes',        [ ~(1<<(i%8)) & 0xff for i in xrange(1<<15)]),
        ('Sequential values',     range(1<<8)*(1<<7) ),
        ('Random values',         [ random.randint(0,(1<<8)-1) for _ in xrange(1<<15) ]),
        ('Other random values',   [ random.randint(0,(1<<8)-1) for _ in xrange(1<<15) ]),

        # The following 3 patterns regarded a problem that appeared always in the same data bit position
        #('Flip DATA3 alone',      [0x00,0x08]*(1<<14) ),
        #('Random but DATA3=0',    [ random.randint(0,(1<<8)-1) & 0xf7 for _ in xrange(1<<15) ]),
        #('Random but DATA3=1',    [ random.randint(0,(1<<8)-1) | 0x08 for _ in xrange(1<<15) ]),
    )
 
    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    for datatitle, the_data in data:
         print
         print(datatitle+': '+str(len(the_data))+' words')
         pprint(map(bin8,the_data[:4]))
         print('...')
         for combtitle, wr_fn, rd_fn in combs:
             clear_fifo()
             #print('{}:{}'.format(wr_fn.__name__, rd_fn.__name__))
             pr.enable()
             run_once(the_data, combtitle, wr_fn, rd_fn)
             pr.disable()
    
    s = StringIO.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats('read_')
    ps.print_stats('write_')
    print
    print s.getvalue()

    
