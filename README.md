# Chip8 Emulator

A CHIP-8 emulator written in Python using Pygame for display and input handling.

## About

This code was written with the help of Claude Code (Claude Haiku 4.5).

## Features

- CHIP-8 virtual machine implementation
- Pygame-based display and input system
- ROM file loading and execution
- Keyboard input mapping for CHIP-8 16-key hexadecimal keypad

## Usage

```bash
python main.py <rom_file>
```

Example:
```bash
python main.py roms/PONG
```

## Requirements

- Python 3.x
- Pygame

## Installation

```bash
pip install pygame
```

## Controls

The keyboard is mapped to the CHIP-8 16-key hexadecimal keypad:

```
CHIP-8 Keypad:    Keyboard:
1 2 3 C           1 2 3 4
4 5 6 D      ->   Q W E R
7 8 9 E           A S D F
A 0 B F           Z X C V
```
