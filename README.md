# rpi-xscreensaver-tools

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

Scripts for doing things with xscreensaver on a Raspberry Pi with the official touchscreen

## Project Status

This project is a *very* rough work in progress. It's not even a Python package, let alone anything more. If anyone in the world other than me uses it, feel free to open an issue and ask for something nicer. Maybe I'll oblige.

## Installation and Requirements

* Python 3, at least 3.7. Unfortunately that's the version that ships on Raspberry Pi OS right now, so no type annotations here.
* The [rpi-backlight](https://pypi.org/project/rpi-backlight/) package, tested against 2.2.0. **Note** that you will likely have to set up udev permissions, according to rpi-backlight's README.
* The ``Flask`` package, tested against 1.0.2.

## xscreensaver-rpi-backlight.py

This is specific to Raspberry Pis using the official 7" Touchscreen display.

[xscreensaver-rpi-backlight.py](xscreensaver-rpi-backlight.py) is a Python daemon which executes ``xscreensaver-command -watch`` to monitor when xscreensaver activates and deactivates. It uses the [rpi-backlight](https://pypi.org/project/rpi-backlight/) Python library to dim the backlight to a given level when the screensaver activates, and raise the backlight back up when the screensaver deactivates (i.e. user input). It's intended to be run as the same user that's logged in / running xscreensaver. I currently run it via a line in my ``~/.config/lxsession/LXDE-pi/autostart`` after starting xscreensaver.

See ``xscreensaver-rpi-backlight.py --help`` for usage information.

By default the daemon will sleep for 10 seconds at startup, in order to let xscreensaver start and stabilize. This can be overridden by command-line options.

## xscreensaver-web.py

This is a tiny Flask web server that provides status and control of xscreensaver via a HTTP interface. I use my touchscreen Pis as interfaces for [HomeAssistant](https://www.home-assistant.io/), and this allows me to put a button on the web-based HomeAssistant UI to activate the screensaver on the actual device I'm using. A bit crazy, but it works. It uses ``xscreensaver-command`` for querying and control. By default it listens on port 8080, but that can be overridden by setting the ``FLASK_PORT`` environment variable. For my purposes, once again, I run this via a line in my ``~/.config/lxsession/LXDE-pi/autostart`` after starting xscreensaver.

The API is dead simple:

To query the screensaver status, GET ``/``. You'll get back JSON with a ``success`` boolean (False if errors were encountered), a ``is_on`` boolean showing whether the screensaver is on or not, a ``state`` string that's either ``on`` (screensaver is active) or ``off`` (screensaver is not active), and some other helpful items.

To control the screensaver, POST a JSON document including a ``state`` boolean set to either True (activate the screensaver) or False (deactivate the screensaver). You'll get back the same response as a GET request, including the new/current status of the screensaver.

## License

Unlike most of my projects, this is released under the MIT license. This project is trivial. Do with it what you want, as long as it's not evil.
