# Project Journal

## Week 0 - Planning & Repository Setup (May 3-9 2026)
**Goals**: Order parts, set up repo, finalize architecture

**Completed**: 
- Verified parts list and ordered components
- Set up Github repo

**Blockers**: None yet - waiting for parts to arrive

**Learned**:
- How to control servos using ESP32Servo library on ArduinoIDE

**Next Week**: 
- Complete repo folder structure
- Draft complete README scaffold
- Assemble robot arm frame

## Week 1 - Assemble Arm & Raspberry Pi Setup (May 10-16 2026)
**Goals**: Assemble arm frame, ensure working servos, complete repo folder structure, set up Raspberry Pi, BOM

**Completed**:
- Assembled arm frame, working servos
- Raspberry Pi setup

**Blockers**: ESP32-C3 will not function unless 18650 battery is present due to power management integrated circuit.

**Learned**:
- The gripper servo (D) failed after being commanded to close on a rigid object. Because hobby servos have no current limiting, the control circuit drove the motor at maximum output indefinitely (stall condition), generating sustained heat. Disassembly showed the gearbox was intact, the actual failure was electrical: heat damaged the position feedback loop (potentiometer which senses commanded position and actual position or control IC), so the motor now spins continuously because the control circuit can't detect when it has reached the commanded position. Servo (MG90S) replaced.
- How to set up Raspberry Pi with imager
- How to connect to Raspberry Pi remotely using SSH 

**Next Week**:
- Flash custom ESP32-C3 firmware for serial commands from Raspberry Pi