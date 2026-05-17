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

## Week 1 - Arm Assembly, Raspberry Pi Setup, ESP32-C3 Custom Firmware (May 10-16 2026)
**Goals**: Assemble arm frame, ensure working servos, set up Raspberry Pi, BOM

**Completed**:
- Assembled arm frame, working servos
- Raspberry Pi set up
- BOM file created
- Backed up 4MB of SIYEENOVE stock firmware
- Wrote and flashed custom firmware to ESP32-C3 (`esp32/src/serial_servo_control/`)
- Calibrated arm initial position (90/90/90/90)

**Blockers**: ESP32-C3 will not function unless 18650 battery is present due to power management integrated circuit.

**Learned**:
Arm
- The gripper servo (D) failed after being commanded to close on a rigid object. Because hobby servos have no current limiting, the control circuit drove the motor at maximum output indefinitely (stall condition), generating sustained heat. Disassembly showed the gearbox was intact, the actual failure was electrical: heat damaged the position feedback loop (potentiometer which senses commanded position and actual position or control IC), so the motor now spins continuously because the control circuit can't detect when it has reached the commanded position. Servo (MG90S) replaced.
- Calibration: adjusting servo horn mounting so that commanding 90/90/90/90 (degree of servos) places the arm in a vertical reference pose with gripper horizontal. 

Raspberry Pi
- How to set up Raspberry Pi with imager
- How to connect to Raspberry Pi remotely using SSH as well as with monitor + mouse + keyboard plugged in

ESP32-C3
- ESP32-C3 has two physically separate serial interfaces: USB Communications Device Class peripheral (accessed as 'Serial') and ledgacy hardware UART0 (accessed as 'Serial0'). The SIYEENOVE dev board has an unconventional USB-C connection. The USB-C connector is routed to UART0 via an onboard USB-to-UART bridge as opposed to the native USB peripheral, leaving the native USB peripheral electrically disconnected. As a result, 'Serial.println()' in user code transmits into a dead end, while Serial0.println() reaches the host. Switching all serial calls from 'Serial' to 'Serial0' resolved the issue completely.
- Diagnostic Path: identical failure in both Arduino IDE Serial Monitor and a direct pyserial miniterm session ruled out the IDE as the cause. Claude identified the distinct serial interfaces on the ESP32-C3 and provided troubleshooting steps to identify the connection discrepancy. 

**Next Week**:
- Define and document safe angle ranges for all servos - implement angle bounds to prevent stall-induced servo damage like servo D
- Begin Pi-side serial communication module (follows ESP32 firmware serial command format, error handling,...) via Python
- Computer vision basic understanding and integration

## Week 2 - ... (May 17-23 2026)