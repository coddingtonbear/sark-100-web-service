Sark 100 Antenna Analyzer Web Service
=====================================

Have you ever been out in your yard adjusting your antenna, but had your
antenna analyzer connected to your computer far away?

This tool will allow you to interact with your antenna analyzer to get a SWR
chart of your antenna and various statistics using a web interface from your
phone or other device.

Quickstart
==========

1. Connect your SARK 100 or MINI 60 antenna analyzer to your computer.
2. Turn on your antenna analyzer's "PC Link" mode.  You can do that by
   presssing the "config" button, and then the down arrow.
3. Start the web service by running the following command::

      sark100web /dev/tty.usbserial-A800eQA9

   .. note::

      Other options, including defining what port the web server starts on,
      are available by using the ``--help`` argument.

4. From a web browser on the device from which you'd like to view the
   generated charts (your phone, perhaps), go to the web address
   ``http://<IP ADDRESS>:8000``.
5. Enter the frequency range and step you'd like to scan, and press the
   "Submit" button.
