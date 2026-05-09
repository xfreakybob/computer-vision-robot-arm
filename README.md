# Computer Vision_Controlled Robotic Arm
A 4-DOF pick-and-place robotic system that uses computer vision to detect and sort colored blocks autonomously. Built as a personal project May-Present 2026.

**Status**: In Development

## Overview
This project integrates a Raspberry Pi 5 running OpenCV for object detection and inverse kinematics with an ESP32-C3 microcontroller handling real-time servo control. The system detects colored blocks in its workspace, computes the joint angles needed to reach them, and executes a pick-and-place sequence.