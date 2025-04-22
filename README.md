[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg

[![Watch the video](https://img.youtube.com/vi/unkeuLdbagM/maxresdefault.jpg)](https://www.youtube.com/watch?v=unkeuLdbagM)

# Pinc'Open project
[Pinc'Open](https://github.com/pollen-robotics/PincOpen/tree/main) is a low-cost (~25€) and open-source parallel-finger gripper, derived from [Pollen Robotics Reachy 2](https://www.pollen-robotics.com/reachy/)'s gripper

## Table of contents

- [Pinc'Open Presentation](#pincopen-project)
    - [What is Pinc'Open](#what-is-pincopen)
    - [Reachy 2 "Pincette" gripper](#reachy-2-pincette-gripper)
    - [Areas of focus](#areas-of-focus)
- [Build Resources](#build-resources)
    - [BOM (Bill Of Materials)](#bom-bill-of-materials)
    - [STL Files and Onshape document](#stl-files-and-onshape-document)
    - [Configure the motor before assembly](#configure-the-motor-before-assembly)
    - [Assembly Guide](#assembly-guide)
    - [How to flash and test the gripper](#how-to-flash-and-test-the-gripper)
- [Project Updates & Community](#project-updates--community)
    - [Updates history](#updates-history)
    - [Project posts](#project-posts)
    - [To Do List](#to-do-list)
    - [FAQ](#faq)
    - [Contact](#contact)
    - [Thank you](#thank-you)

## What is Pinc'Open?
The aim of this project is to make robotic manipulation more accessible, so that anyone with an idea but not the budget can make advances in this field possible.  
The quality of movement, mechanical strength and precision may not be as good as an industrial product, but a 2-finger parallel robotic gripper can be built for less than 25€! And we'll see that the performance is still good.  
![PincOpen_weight](/assets/images/pincopen_weight.jpg)

The secondary goal is to make this gripper compatible with the [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) open-source arm, so that the same motor as the current gripper can be used on our Pinc'Open. So the 25€ includes a motor that is already included in the $100 of the SO-ARM100.

What's more, the tip is interchangeable! That way, you can fit exactly what you need for your particular application.  
![removable_tip](/assets/images/removable_tip.png)

## Reachy 2 "Pincette" gripper
The Pincette v1.0 gripper, released at the same time as [Reachy 2](https://www.pollen-robotics.com/reachy/), is a two-parallel-finger hand designed for versatility and accurate, strong grasping.  
![Pincette](/assets/images/Pincette.png)
Joints are based on high-quality standard components, and mechanical parts are machined from metal for greater rigidity and precision.  
However, these qualities come at a considerable cost: today, for just a few units manufactured, the BOM costs ~€1,700 per unit.  

This is acceptable depending on the application, but not for those who want to build a low-cost robotic gripper.

## Areas of focus:
- Make every mechanical custom part 3D printable, and not easily breakable, to avoid expensive metal machining.
- Change the expensive [Robotis Dynamixel motor](https://emanual.robotis.com/docs/en/dxl/x/xm430-w210/) to a cheap [Feetech STS3215](https://www.feetechrc.com/525603.html) motor.
- Remove all the high-quality but expensive standard components and find mechanical tricks to replace them.
- Find a trick to imitate a torque limitation while using position control on a motor that doesn't have this feature. Otherwise, the motor burns (or turns off thanks to security) or the plastic mechanical part can break...


# Build Resources
## BOM (Bill Of Materials)
The list of all needed components is available here:  
[PincOpen BOM](https://docs.google.com/spreadsheets/d/1iEKxfsqo3RnKw0QtdLJ2hEtYNDy2LInxrnCFLAhpxHk/edit?usp=sharing)  

There is the standalone PincOpen gripper BOM (~25€), then optional components like the interface with the [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) project, or a Realsense camera stand for example.

## STL Files and Onshape document
STL and Steps files can be found [here](https://github.com/pollen-robotics/PincOpen/tree/main/cad)  

Everyone can access the Onshape document too:   
[Link Onshape](https://cad.onshape.com/documents/96518c699fd03eea508b06d3/w/d5f95a6266b027d84ae48634/e/e41e675b82a4f671f01336e0)  
![pincopen onshape picture](/assets/images/pincopen_onshape.png)  

Note that you can set a configuration in the assembly, like the default assembly, or with the interface part for SO-ARM100, or the configuration for camera mounting.

## Configure the motor before assembly
To configure the motor as it should be, please first clone & install [Lerobot library](https://github.com/huggingface/lerobot/tree/main).

Then connect and power up your motor, and run the following command: 

```bash
python lerobot/scripts/configure_motor.py --port /dev/ttyACM0 --brand feetech --model sts3215 --baudrate 1000000 --ID <ID>
```

Make sure to replace the port with your USB serial port and the ID with "6".

## Assembly Guide
Here is an assembly guide to explain how to print all the needed custom parts and how to use them to build this gripper.  
[=> Assembly Guide](/docs/PincOpen_Assembly_Instructions.pdf)  
![Assembly Example](/assets/images/assembly_example.png)  

## How to flash and test the gripper
First of all, please install the pypot library, updated with the Feetech motors:  
https://github.com/pollen-robotics/pypot/tree/support-feetech-sts3215  

Then, please refer to the [flash&test notebook](https://github.com/pollen-robotics/PincOpen/tree/main/flash_and_tests)


# Project Updates & Community
## Updates history
[Updates history](/docs/changelog.md)  

## To Do List
- Video showing the advantages of this more complex mechanism
- Technical explanation about how it was designed
- Non-downsized version for humanoid arms (like Reachy2)
- New camera mounting supports

## Project posts
- [Fingertips for better grip](/docs/grip_tip.md)

## FAQ
WIP

## Contact
[Contact me or Pollen Robotics](/docs/contact.md)

## Thank you
Huge thanks to those who have contributed to this project so far:
- [Antoine Pirrone](https://github.com/apirrone) for making great demos, all the advice and feedback
- [Pierre Rouanet](https://github.com/pierre-rouanet) for Feetech motors integration in pypot  
- [Jeremy Laville](https://www.linkedin.com/in/jeremy-laville-1038b176/) & [Matthieu Lapeyre](https://www.linkedin.com/in/matthieulapeyre/) for mechanical advice and original Reachy 2 Pincette co-development

