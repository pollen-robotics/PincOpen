[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg


# Pinc'Open project
A low cost (~25€) and open source parallel-finger gripper, derived from Reachy 2's gripper

## Table of content

- [Pinc'Open Presentation](#pincopen-project)
    - [Reachy 2 "Pincette" gripper](#reachy-2-pincette-gripper)
    - [What is Pinc'Open](#what-is-pincopen)
- [Build Resources](#build-resources)
    - [BOM (Bill Of Materials)](#bom-bill-of-materials)
    - [STL Files and Onshape document](#stl-files-and-onshape-document)
    - [Configure the motor before assembly](#configure-the-motor-before-assembly)
    - [Assembly Guide](#assembly-guide)
    - [How to flash and test the gripper](#how-to-flash-and-test-the-gripper)
- [Project Updates & Community](#project-updates--community)
    - [Updates history](#updates-history)
    - [Project posts](#project-posts)
    - [FAQ](#faq)
    - [Contact](#contact)
    - [Thank you](#thank-you)

## Reachy 2 "Pincette" gripper
The Pincette v1.0 gripper releases at the same time as Reachy 2 is a two parallel fingers hand which has been designed for versatility and accurate strong grasping.  
![Pincette](/assets/images/Pincette.png)
Joints are based on high-quality standard components, and mechanical parts are machined from metal for greater rigidity and precision.  
However, these qualities come at a considerable cost: today, for just a few units manufactured, BOM costs ~€1,700 per unit.  

It's okay, depending on the application, but not for those who want to build a low-cost robotic gripper.


## What is Pinc'Open?
The aim of this project is to make robotic manipulation more accessible, so that anyone with an idea but not the budget can make advances in this field possible.  
The quality of movement, mechanical strength and precision may not be as good as on the Reachy 2 Pincette, but a 2-finger parallel robotic gripper can be built for less than 25€! And we'll see that the performance is still good.  
![PincOpen_weight](/assets/images/pincopen_weight.jpg)

The secondary goal is to make this gripper compatible with the [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) open source arm, so that the same motor as the current gripper can be used on our Pinc'Open. So the 25€ include a motor that is already included in the $100 of the SO-ARM100.  

To make this possible, here are the main areas of focus:
- Make every mechanical custom part 3D printable, and not easily breakable, to avoid expensive metal machining.
- Change the expensive Robotis Dynamixel motor to a cheap Feetech STS3215 motor.
- Remove all the high-quality but expensive standard component and find mechanical tricks to replace them.
- Find a trick to imitate a torque limitation while using position control on a motor that doesn't have this feature. Otherwise the motor burns (or turn off thanks to security) or the plastic mechanical part can break...


# Build Resources
## BOM (Bill Of Materials)
The list of all needed components is available here:  
[PincOpen BOM](https://docs.google.com/spreadsheets/d/1iEKxfsqo3RnKw0QtdLJ2hEtYNDy2LInxrnCFLAhpxHk/edit?usp=sharing)  

There is the standalone PincOpen gripper BOM (~25€), then optional components like the interface with the [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) project, or a Realsense camera stand for example.

## STL Files and Onshape document
STL and Steps files can be found [here](/cad/)  

Everyone can access to the Onshape document too:   
[Link onshape](https://cad.onshape.com/documents/96518c699fd03eea508b06d3/w/d5f95a6266b027d84ae48634/e/e41e675b82a4f671f01336e0)  
![pincopen onshape picture](/assets/images/pincopen_onshape.png)  

Note that you can set a configuration in the assembly, like the default assembly, or with the interface part for SO-ARM100, or the configuration for camera mounting.

## Configure the motor before assembly
To configure the motor as it should be, please first clone & install [Lerobot library](https://github.com/huggingface/lerobot/tree/main).

Then connect and power up you motor, and run the following command: 

```bash
python lerobot/scripts/configure_motor.py --port /dev/ttyACM0 --brand feetech --model sts3215 --baudrate 1000000 --ID <ID>
```

make sure to replace the port with your usb serial port and the ID with "6".

## Assembly Guide
Here is an assembly guide to explain how to print all the needed custom parts and how to use them to build this gripper.  
[=> Assembly Guide](/docs/PincOpen_Assembly_Instructions.pdf)  
![Assembly Example](/assets/images/assembly_example.png)  

## How to flash and test the gripper
First of all, please install the pypot library, updated with the feetech motors:  
https://github.com/pollen-robotics/pypot/tree/support-feetech-sts3215


# Project Updates & Community
## Updates history
[Updates history](/docs/changelog.md)  

## Project posts
WIP 

## FAQ
WIP

## Contact
[Contact me or pollen robotics](/docs/contact.md)

## Thank you
Huge thanks to those who have contributed to this project so far:
- Antoine Pirrone for making great demos, all the advice and feedback
- Pierre Rouanet for Feetech motors integration in pypot  
- Jeremy Laville & Matthieu Lapeyre for mechanical advice and original Reachy 2 Pincette co-development

