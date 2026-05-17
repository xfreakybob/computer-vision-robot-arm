## Overview
The ESP32-C3 handles all real-time servo control for the robotic arm. It receives joint angle commands from the Raspberry Pi 5 via USB serial, parses them, and drives four MG90S servos via PWM (Pulse Width Modulation).

The mechanical platform is based on a commercial kit from SIYEENOVE. All firmware, assembly, and Raspberry Pi integration were completed independently.

## Hardware

- **Board**: SIYEENOVE ESP32-C3 development board
- **Power**: 18650 Li-ion battery
- **Servos**: 4xMG90S servos

|   Joint   |    Label    | GPIO Pin |
|----------|--------------|----------|
| Base     | S1 / Servo A | GPIO 4 |
| Shoulder | S2 / Servo B | GPIO 5 |
| Elbow    | S3 / Servo C | GPIO 6 |
| Gripper  | S4 / Servo D | GPIO 7 |

## Flashing

### Prerequisites
- Arduino IDE 2.x.x
- esp32 board package by Espressif Systems (3.0.4) — add via Boards Manager using URL: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
- ESP32Servo (3.0.5) library by Kevin Harrington — install via Library Manager
- [CH340 USB driver](https://github.com/siyeenove/E1R0000/tree/main/Ch340_USB_Driver) 

### Board settings (Tools menu)
| Setting | Value |
|---------|-------|
| Board | ESP32C3 Dev Module |
| USB CDC On Boot | Enabled |
| Upload Speed | 921600 |
| Port | whichever COMx appears when board is plugged in (Windows) |

### Important: 18650 battery must be inserted before plugging in USB-C
The board's power management IC requires the battery to be present for the board to enumerate over USB. Without it, the port won't appear.

### Steps
1. Insert 18650 battery
2. Connect USB-C to board and other end to your computer
3. Select correct port under Tools → Port
4. Open the sketch in `esp32\src\serial_servo_control`
5. Click Upload (→)
6. Open Serial Monitor at 115200 baud — you should see `READY` on reset

## ⚠️ Use Serial0, not Serial

The SIYEENOVE board routes USB-C through a legacy hardware UART (Universal Asynchronous Receiver/Transmitter, *hardware protocol for serial communication*) bridge to `Serial0`, not the ESP32-C3's native USB CDC (Communications Device Class, *standard USB protocol that allows devices to emulate a standard serial port (COM/UART) over a USB cable*) peripheral (`Serial`). Any code using `Serial.println()` transmits into a dead end — use `Serial0` for all serial communication.

## Serial Protocol

Baud rate: 115200 — connection: Raspberry Pi 5 USB-A → ESP32-C3 USB-C

Commands from the Pi are a single line in the format:
`S1:<angle>,S2:<angle>,S3:<angle>,S4:<angle>`.
Angles are integers in degrees (0–180). The board responds `OK` on success,`ERR:<line>` on a parse failure, and `READY` on reset.

## Stock Firmware

A backup of the original SIYEENOVE firmware is stored in `esp32\firmware_backups\siyeenove_stock_backup.bin`.