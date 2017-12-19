# rpi-daq
Software for single-module control using a Raspberry Pi

 * Install bitarray python package
 ```
 BITARRAY_DIR=/choose/wherever/you/want
 cd ${BITARRAY_DIR}
 git clone https://github.com/ilanschnell/bitarray.git
 cd bitarray
 sudo python setup.py install
 sudo python setup.py build_ext -i
 ```
 
 * Install bcm2835 and create shared library
```
BCM_DIR=/choose/wherever/you/want
cd ${BCM_DIR}
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.52.tar.gz
tar zxvf bcm2835-1.52.tar.gz
cd bcm2835-1.52/src
gcc -shared -o libbcm2835.so -fPIC bcm2835.c
sudo cp libbcm2835.so /usr/local/lib/libbcm2835.so
```

* Compile gpiolib.c and create shared library
```
cd rpi-daq
gcc -c -I ${BCM_DIR}/bcm2835-1.52/src ${BCM_DIR}/bcm2835-1.52/src/bcm2835.c -fPIC gpiolib.c
gcc -shared -o gpiolib.so gpiolib.o
```  

* Example of acquisition:
```
python run.py --moduleNumber=63 --nEvent=1000 --acquisitionType=sweep --externalChargeInjection --channelIds=0,10,50,34 --compressRawData --channelIdsMask=22 --channelIdsDisableTOT=22  --channelIdsDisableTOA=22
```
