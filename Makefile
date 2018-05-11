# https://gist.github.com/fm4dd/c663217935dc17f0fc73c9c81b0aa845

# 100 ev in 10.5s
#MYCFLAGS= -O2 -mtune=cortex-a53 -mcpu=cortex-a53 -mfloat-abi=hard -mfpu=neon-fp-armv8 -mneon-for-64bits

# 100 ev in 10.4s
#MYCFLAGS= -O3 -mtune=cortex-a53 -mcpu=cortex-a53 -mfloat-abi=hard -mfpu=neon-fp-armv8 -mneon-for-64bits

# 100 ev in 12.0s
#MYCFLAGS= -O0

# 100 ev in 10.7s
#MYCFLAGS= -O2

# 100 ev in 10.6s
#MYCFLAGS= -O1

# 100 ev in 10.6s
MYCFLAGS= -Os -mcpu=cortex-a53 -mtune=cortex-a53

# 100 ev in 10.7s
#MYCFLAGS = -O3 -mcpu=cortex-a53 -mtune=cortex-a53

# Benchmarking command
# make distclean; make benchmark

all: lib/libgpiohb.so

src/gpiohb.o: src/gpiohb.c lib/libbcm2835.so src/data_addr_utils.h
	g++ -Wall -c -I ./src/bcm2835/src -L ./lib -fPIC $(MYCFLAGS) $< -o $@

lib/libgpiohb.so: src/gpiohb.o
	mkdir -p lib
	g++ -shared $< -o $@

lib/libbcm2835.so: src/bcm2835/src/bcm2835.o
	mkdir -p lib
	gcc -shared $< -o $@

src/bcm2835/src/bcm2835.o: src/bcm2835/src/bcm2835.c
	make -C src/bcm2835

src/bcm2835/src/bcm2835.c:
	if ! dpkg -l | grep html-xml-utils -c >>/dev/null; then sudo apt-get --yes install html-xml-utils; fi
	mkdir -p src/bcm2835
	wget -qO - `curl -sL http://www.airspayce.com/mikem/bcm2835 | hxnormalize -x -e | hxselect -s '\n' -c "div.textblock>p:nth-child(4)>a:nth-child(1)"` | tar xz --strip-components=1 -C src/bcm2835
	cd src/bcm2835 && (./configure CFLAGS=" -fPIC $(MYCFLAGS)")

.PHONY: distclean clean packages testrun

packages:
	if ! dpkg -l | grep python-bitarray -c >>/dev/null; then sudo apt-get --yes install python-bitarray; fi
	if ! dpkg -l | grep python-yaml -c >>/dev/null; then sudo apt-get --yes install python-yaml; fi
	if ! dpkg -l | grep python-zmq -c >>/dev/null; then sudo apt-get --yes install python-zmq; fi

clean:
	rm -rf lib/*
	rm -f src/*.o
	rm -f ./*.pyc
	if [ -e src/bcm2835/src ]; then make -C src/bcm2835 clean; fi;

distclean: clean
	rm -rf lib
	rm -rf src/bcm2835
	@find ./ $(RCS_FIND_IGNORE) \
        \( -name '*.orig' -o -name '*.rej' -o -name '*~' \
        -o -name '*.bak' -o -name '#*#' -o -name '.*.orig' \
        -o -name '.*.rej' -o -size 0 \
        -o -name '*%' -o -name '.*.cmd' -o -name 'core' \) \
        -type f -print | xargs rm -f

testrun: all
	python run_local.py --externalChargeInjection --channelIds=30 --acquisitionType=const_inj --injectionDAC=3000 --dataNotSaved --showRawData

testfifo: all
	python test_fifo.py
	
benchmark: all
	@echo "Timing the default acquisition"
	bash -c "time (python run_local.py --dataNotSaved > /dev/null)"
