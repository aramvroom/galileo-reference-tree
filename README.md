# Galileo Reference Tree
![](docs/galileo-reference-tree-banner.jpg)

[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/0c4421a15b7c4559b53c6ef5839fa138)](https://app.codacy.com/gh/aramvroom/galileo-reference-tree/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0c4421a15b7c4559b53c6ef5839fa138)](https://app.codacy.com/gh/aramvroom/galileo-reference-tree/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Tests](https://github.com/aramvroom/galileo-reference-tree/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/aramvroom/galileo-reference-tree/actions/workflows/tests.yml)
[![CodeQL](https://github.com/aramvroom/galileo-reference-tree/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/aramvroom/galileo-reference-tree/actions/workflows/github-code-scanning/codeql)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

This repository contains a hobby project to show the live Galileo constellation visibility and status as LEDs in a Christmas tree. The color and brightness of the LEDs correspond to the health status and elevation respectively. It is inspired by a combination of Matt Parker's [Programmable Christmas Tree](https://www.youtube.com/watch?v=TvlpIojusBE) and Bert Hubert's [Galmon](https://galmon.eu/). 
The scripts automatically retrieve of the latest orbits from Two Line Element (TLE) and ephemeris data, compute the elevations at a preconfigured user location and control the LEDs through the GPIO pins accordingly.

Tested with Python 3.11 and 3.13 on Raspberry Pi OS (H/W: Pi 4B) and Windows (for dev. purposes)
## Features

* Control of a LED strip through a Raspberry Pi's GPIO pins
* Autonomous retrieval of the latest ephemeris from NTRIP casters,
  * Compatible with many providers, including the Dutch [Kadaster NTRIP Caster](http://monitor.use-snip.com/?hostUrl=ntrip.kadaster.nl&port=2101) and [RTK2GO](http://monitor.use-snip.com/?hostUrl=rtk2go.com&port=2101),
* Capable of displaying satellites not transmitting ephemeris through autonomous retrieval of CelesTrak Two Line Element (TLE) data,
* Satellite elevation indication through configurable LED brightness levels,
* Satellite health status indication through configurable colors,
* Configurable simulation speed for faster than real-time simulation,
* Customizable to different setups (user location, number of LEDs, used GPIO pins, etc.) through a TOML config file,
* Compatible with many different LED strips, including WS2811, WS2812 and SK6812 strips (note: only WS2811 is fully tested),
* Plots a live Skyplot and a graphical representation of the LEDs using `matplotlib`,
* Currently programmed for Galileo, but theoretically usable for any constellation
* Supports development on Windows environments through the `rpi_ws281x_mock` library

## Installation
### Raspberry Pi with LED Strip
These installation steps assume you have a Raspberry Pi (4B) with Raspberry Pi OS, git and python installed, which is reachable through SSH or VNC. If this is not the case, check the steps below. 
It is recommended to also first follow the steps under the [Hardware Setup](#hardware-setup) section to connect the LED strip to the Raspberry Pi.

Note that any values between square brackets [example] should be replaced by your values.
<details><summary>Raspberry Pi Installation Steps</summary>

1. Download the [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Install Raspberry Pi OS on an SD card using the following settings:
   - Raspberry Pi Device: [your Raspberry Pi version]
   - Operating System: Raspberry Pi OS (64-bit)
   - Storage: [your storage device]
   - Preconfigure the username, password and wireless lan
   - Go to the Services tab and enable SSH
3. Slot the SD card into the Pi, power it up and connect using ssh `ssh [username]@[ip_address]`
   - _Note: can check the IP through your router for example_
4. Optional: set up VNC:
   - Run `sudo raspi-config`
   - Go to Interface options, and enable VNC
5. Ensure git and python are installed: `sudo apt-get install git python`  

Your Pi is now ready to continue to the following steps.
</details>

#### Software Installation Steps
1. Clone this repository: `git clone https://github.com/aramvroom/galileo-reference-tree.git`
1. If you use the PWM pin (18), blacklist the analog audio from it (as it may otherwise interfere with the LED signal)
   - Create a new file: `sudo nano /etc/modprobe.d/snd-blacklist.conf`
   - Add the following to it: `blacklist snd_bcm2835`
1. Set up the virtual Python environment:
    ```
    cd galileo-reference-tree
    python -m venv venv
    source venv/bin/active
    pip install -r requirements.txt
    ```
1. Check that the unit tests pass: `sudo venv/bin/python -m unittest`
1. Customize `config.toml` to your setup (see [Configuration Options](#configuration-options) for more detail)
1. Create a service which starts on boot (optional, but highly recommended)
   - Run `sudo systemctl edit --force --full grt.service`
   - Paste the following (replacing values between square brackets): 
   ```
    [Unit]
    Description=Galileo Reference Tree
    Wants=network-online.target
    After=network-online.target
    
    [Service]
    Type=simple
    User=root
    WorkingDirectory=[Path to Repository]
    ExecStart=[Path to Repository]/venv/bin/python main.py
    Restart=always
    
    [Install]
    WantedBy=multi-user.target    
    ```
   - Enable the service with: `sudo systemctl enable grt.service`

### Development Environment without LED Strip
1. Clone this repository: `git clone https://github.com/aramvroom/galileo-reference-tree.git`
1. Set up the virtual Python environment:
    ```
   cd galileo-reference-tree
   python -m venv venv       
   source venv/bin/active                  # venv\Scripts\activate on Windows
   pip install -r requirements-dev.txt     # Uses rpi_ws281x_mock instead of rpi_ws281x
    ```
1. Check that the unit tests pass: `venv/bin/python -m unittest` (Windows: `venv\Scripts\python.exe -m unittest`)

## Hardware Setup
The hardware uses the following parts:
- 3.3V - 5V Logic Level Converter
- 470 Ohm Resistor
- Raspberry Pi 

![schematic.jpg](docs/schematic.jpg)

## Configuration Options

## Test Execution

## License

This repository and all its contents, including the 3D models and code, are provided under a permissive MIT license. As such, this is an open source project that you are able to use however you wish, as long as you include the original license and copyright. For more information, see the [LICENSE](LICENSE) file.
