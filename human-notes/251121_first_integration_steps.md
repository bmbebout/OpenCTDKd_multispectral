# Plan to integrate kdupro and OpenCTD

This is a totally new project that will use Micropython running on a Pico2W to integrate the
functionality found in kdupro (as7341 branch) and OpenCTD projects

## Requirements:

* This will be deployed to a pico2W board
* The language used will be micropython
* Code will be deployed using the mpremote command
* There will be an SPI connected sd card for data storage
* Use kdupro as an example for the data format recorded. More columns will be added for the combined sensors of the two projects. Data saved should be in csv format.
* Use a state machine pattern for switching between the different modes of the device.
* 
