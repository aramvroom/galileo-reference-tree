# Galileo Reference Tree
<img src="docs/galileo-reference-tree-banner.jpg" alt="Galileo Reference Tree">
<div align="left">
  <a href="https://app.codacy.com/gh/aramvroom/galileo-reference-tree/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage">
    <img src="https://app.codacy.com/project/badge/Coverage/0c4421a15b7c4559b53c6ef5839fa138"/>
  </a>
  <a href="https://app.codacy.com/gh/aramvroom/galileo-reference-tree/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade">
    <img src="https://app.codacy.com/project/badge/Grade/0c4421a15b7c4559b53c6ef5839fa138"/>
  </a>
  <a href="https://github.com/aramvroom/galileo-reference-tree/actions/workflows/tests.yml">
    <img src="https://github.com/aramvroom/galileo-reference-tree/actions/workflows/tests.yml/badge.svg?branch=main"/>
  </a>
  <a href="https://github.com/aramvroom/galileo-reference-tree/actions/workflows/github-code-scanning/codeql">
    <img src="https://github.com/aramvroom/galileo-reference-tree/actions/workflows/github-code-scanning/codeql/badge.svg"/>
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg"/>
  </a>
</div>

---

This repository contains a hobby project to show the live Galileo constellation visibility and status as LEDs in a Christmas tree. The color and brightness of the LEDs correspond to the health status and elevation respectively. It is inspired by a combination of Matt Parker's [Programmable Christmas Tree](https://www.youtube.com/watch?v=TvlpIojusBE) and Bert Hubert's [Galmon](https://galmon.eu/). 
The scripts automatically retrieve of the latest orbits from Two Line Element (TLE) and ephemeris data, compute the elevations at a preconfigured user location and control the LEDs through the GPIO pins accordingly.

## Features

---

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

---

## Test Execution

---


## Configuration Options

---

## License

---

This repository and all its contents, including the 3D models and code, are provided under a permissive MIT license. As such, this is an open source project that you are able to use however you wish, as long as you include the original license and copyright. For more information, see the [LICENSE](LICENSE) file.
