# rpi-daq
Software for taking data from one [hexaboard module](https://edms.cern.ch/ui/#!master/navigator/item?I:1141765299:1141765299:subDocs) with four [`SKIROC2_CMS` chips](http://llr.in2p3.fr/~Geerebaert/CMS/HGCal/CMS_HGCal-SKATE_design_notes.pdf),  using the [test stand board](https://edms.cern.ch/ui/#!master/navigator/document?D:1749508128:1749508128:subDocs).

Two main acquisition programs:
- `run_local.py` for local debugging.
- `daq-zmq_client.py`, that spawns a server over the network in the device and processes data off-device. This package then needs to be installed in both machines, though only the python part in the client.


Two main sources of configuration:
- `yaml` file
- command line options

More details on the `SKIROC2_CMS` readout chip configuration can be found [here](https://cms-docdb.cern.ch/cgi-bin/DocDB/ShowDocument?docid=12963) and [here](https://indico.cern.ch/event/559024/contributions/2261087/attachments/1316812/1972848/20160727_SimuReview.pdf).

## Installation

See [here](#raspberry-pi-3-from-scratch) to install Raspbian on a Pi 3.

Then:
```bash
cd $HOME
git clone https://github.com/CMS-HGCAL/rpi-daq
cd rpi-daq
make packages
```

The following step is only needed in the server or for local running (it is not needed for the client):
```bash
make
```

Finally, a local test run with charge injection:
```bash
make testrun
```

Another example of a local acquisition:
```
python run_local.py --showRawData --dataNotSaved
```

An example of client and server running in the same machine
```
python zmq-daq-client.py -e
```

## Development

### Code structure

* `rpi_daq.py`: configures the chips and reads events.
* `src/gpiohb.c`: utilities for low-level communication with the hexaboard; uses the [`bcm2835` library](www.airspayce.com/mikem/bcm2835/).
* `unpacker.py`: parses (and compresses) raw data.
* `skiroc2cms_bit_string.py`: utilities for configuration of the readout chips.

* `run_local.py`: simple local running application.
* `daq-zmq-{client,server}.py`: full-fledged system with data processing offloaded to client side.

### Ideas for contributions

- [ ] 🚀 Optimize timing of `gpiohb.c` I/O routines.
- [ ] 💡 Develop an ASUS Tinker Board version.
- [ ] ➕ Add functionality to `skiroc2cms_bit_string.py`.
- [ ] 🔒 Improve the client-server usage, e.g., streamlining `ssh` sessions (no password, public key).

### Contributing

* Fork this project,
* Clone your repository when installing,
* _Your magic happens here_,
* Push to your repository, and
* Submit pull requests.

# Installing OS on device

## Raspberry Pi 3 from scratch

- Download [Raspbian with desktop](https://www.raspberrypi.org/downloads/raspbian/).
- Use [Etcher](https://etcher.io/) to write the image to the SD card.
- Boot the device and connect a screen, keyboard, and mouse.
- Connect device to network using desktop tools.   
   When using wired and wireless network, editing `/etc/wpa_supplicant/wpa_supplicant.conf` may be needed to sort out priorities. See also [this](https://raspberrypi.stackexchange.com/questions/58304/how-to-set-wifi-network-priority).
- Register device to network, including both wired and wireless MAC addresses that can be obtained using `ifconfig`.
- Update the system:
    ```bash
    sudo apt-get update
    sudo apt-get --yes dist-upgrade
    sudo apt-get clean
    sudo apt --yes autoremove
    ```
- `sudo reboot`
- Change `pi` user password using `passwd`.
- Enable `VNC` in pi customization GUI from `Desktop menu → Preferences → Raspberry Pi Configuration → Interfaces → VNC: Enabled`.
- Install some goodies:
    ```bash
    sudo apt-get --yes install emacs25 htop iotop nmap liquidprompt ipython elpa-markdown-mode yaml-mode
    liquidprompt_activate
    ```

## 🚧 ASUS Tinker Board from scratch 

- Download `TinkerOS-Debian` image from the downloads section in the [Tinker Board page](https://www.asus.com/Single-Board-Computer/Tinker-Board/).
- Use [Etcher](https://etcher.io/) to write the image to the SD card.
- Default user and password are `linaro:linaro`. Change it.
- Register device to network, including both wired and wireless MAC addresses that can be obtained using `ifconfig`.
- Update the system:
    ```bash
    sudo apt-get update
    sudo apt-get --yes dist-upgrade
    sudo apt-get clean
    sudo apt --yes autoremove
    ```
- Install some goodies:
    ```bash
    sudo apt-get --yes install emacs25 htop iotop nmap liquidprompt ipython elpa-markdown-mode yaml-mode
    liquidprompt_activate
    ```
- Setup the `C` GPIO API (see also the [Tinker Board page](https://www.asus.com/Single-Board-Computer/Tinker-Board/)). Basically:
    ```bash
    cd $HOME
    git clone http://github.com/TinkerBoard/gpio_lib_c.git
    cd gpio_lib_c/
    sudo ./build
    gpio -v
    gpio readall
    ```
- Set up VNC (`sudo tinker-config` allows to start VNC, but not to set it up as a deamon):
    ```bash
    # From https://tinkerboarding.co.uk/wiki/index.php?title=Software#Remote_access
    sudo apt-get --yes install x11vnc
    echo "@x11vnc -forever -ssl -geometry 1600x1200 -truecolor -noxrecord" >> ~/.config/lxsession/LXDE/autostart
    sudo service lightdm restart
    ```
