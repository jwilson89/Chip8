class Chip8:
    def __init__(self):
        # Memory: 4KB (4096 bytes)
        self.memory = [0] * 4096

        # 16 general-purpose 8-bit registers (V0-VF)
        self.V = [0] * 16

        # 16-bit index register (I) - used for memory addresses
        self.I = 0

        # 16-bit program counter (PC) - programs start at 0x200
        self.pc = 0x200

        # Stack: 16 levels of 16-bit values for subroutine return addresses
        self.stack = [0] * 16
        self.sp = 0  # Stack pointer

        # Timers (both count down at 60Hz when non-zero)
        self.delay_timer = 0
        self.sound_timer = 0

        # Display: 64x32 pixels (monochrome)
        self.display = [[0] * 64 for _ in range(32)]
        self.draw_flag = False  # Set when screen needs to be redrawn

        # Keypad: 16 keys (0x0-0xF)
        self.keys = [0] * 16

        # Load fontset into memory (starting at 0x000)
        self._load_fontset()

    def _load_fontset(self):
        """Load the built-in font sprites into memory at 0x000-0x04F.
        Each character is 5 bytes (5 rows of 8 pixels, but only 4 pixels wide).
        """
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
        ]

        for i, byte in enumerate(fontset):
            self.memory[i] = byte

    def load_rom(self, filepath):
        """Load a ROM file into memory starting at 0x200."""
        with open(filepath, 'rb') as f:
            rom_data = f.read()

        # Load ROM into memory starting at 0x200
        for i, byte in enumerate(rom_data):
            if 0x200 + i < 4096:
                self.memory[0x200 + i] = byte
            else:
                raise MemoryError("ROM too large to fit in memory")

        print(f"Loaded ROM: {len(rom_data)} bytes")

    def cycle(self):
        """Execute one CPU cycle: fetch, decode, execute."""
        # Fetch: Get 2-byte opcode from memory at PC
        # Chip8 opcodes are big-endian (high byte first)
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]

        # Decode and execute
        self._execute_opcode(opcode)

    def update_timers(self):
        """Update delay and sound timers. Call this at 60Hz."""
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def _execute_opcode(self, opcode):
        """Decode and execute a single opcode."""
        # Extract common opcode parts
        # nnn - 12-bit address (lowest 12 bits)
        # n   - 4-bit nibble (lowest 4 bits)
        # x   - 4-bit register index (lower 4 bits of high byte)
        # y   - 4-bit register index (upper 4 bits of low byte)
        # kk  - 8-bit constant (lowest 8 bits)

        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        kk = opcode & 0x00FF

        # Get the first nibble to determine instruction type
        first_nibble = opcode & 0xF000

        # Default: advance PC by 2 bytes (each instruction is 2 bytes)
        self.pc += 2

        # Decode based on first nibble
        if first_nibble == 0x0000:
            if opcode == 0x00E0:
                # 00E0: CLS - Clear the display
                self.display = [[0] * 64 for _ in range(32)]
                self.draw_flag = True
            elif opcode == 0x00EE:
                # 00EE: RET - Return from subroutine
                self.sp -= 1
                self.pc = self.stack[self.sp]
            else:
                # 0nnn: SYS addr - ignored on modern interpreters
                pass

        elif first_nibble == 0x1000:
            # 1nnn: JP addr - Jump to address nnn
            self.pc = nnn

        elif first_nibble == 0x2000:
            # 2nnn: CALL addr - Call subroutine at nnn
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn

        elif first_nibble == 0x3000:
            # 3xkk: SE Vx, byte - Skip next instruction if Vx == kk
            if self.V[x] == kk:
                self.pc += 2

        elif first_nibble == 0x4000:
            # 4xkk: SNE Vx, byte - Skip next instruction if Vx != kk
            if self.V[x] != kk:
                self.pc += 2

        elif first_nibble == 0x5000:
            # 5xy0: SE Vx, Vy - Skip next instruction if Vx == Vy
            if self.V[x] == self.V[y]:
                self.pc += 2

        elif first_nibble == 0x6000:
            # 6xkk: LD Vx, byte - Set Vx = kk
            self.V[x] = kk

        elif first_nibble == 0x7000:
            # 7xkk: ADD Vx, byte - Set Vx = Vx + kk (no carry flag)
            self.V[x] = (self.V[x] + kk) & 0xFF

        elif first_nibble == 0x8000:
            self._execute_8xxx(opcode, x, y, n)

        elif first_nibble == 0x9000:
            # 9xy0: SNE Vx, Vy - Skip next instruction if Vx != Vy
            if self.V[x] != self.V[y]:
                self.pc += 2

        elif first_nibble == 0xA000:
            # Annn: LD I, addr - Set I = nnn
            self.I = nnn

        elif first_nibble == 0xB000:
            # Bnnn: JP V0, addr - Jump to address nnn + V0
            self.pc = nnn + self.V[0]

        elif first_nibble == 0xC000:
            # Cxkk: RND Vx, byte - Set Vx = random byte AND kk
            import random
            self.V[x] = random.randint(0, 255) & kk

        elif first_nibble == 0xD000:
            # Dxyn: DRW Vx, Vy, n - Draw sprite at (Vx, Vy) with height n
            self._draw_sprite(x, y, n)

        elif first_nibble == 0xE000:
            if kk == 0x9E:
                # Ex9E: SKP Vx - Skip next instruction if key Vx is pressed
                if self.keys[self.V[x] & 0xF]:
                    self.pc += 2
            elif kk == 0xA1:
                # ExA1: SKNP Vx - Skip next instruction if key Vx is NOT pressed
                if not self.keys[self.V[x] & 0xF]:
                    self.pc += 2

        elif first_nibble == 0xF000:
            self._execute_Fxxx(opcode, x, kk)

        else:
            print(f"Unknown opcode: {opcode:04X}")

    def _execute_8xxx(self, opcode, x, y, n):
        """Handle 8xxx arithmetic/logic opcodes."""
        if n == 0x0:
            # 8xy0: LD Vx, Vy - Set Vx = Vy
            self.V[x] = self.V[y]
        elif n == 0x1:
            # 8xy1: OR Vx, Vy - Set Vx = Vx OR Vy
            self.V[x] |= self.V[y]
        elif n == 0x2:
            # 8xy2: AND Vx, Vy - Set Vx = Vx AND Vy
            self.V[x] &= self.V[y]
        elif n == 0x3:
            # 8xy3: XOR Vx, Vy - Set Vx = Vx XOR Vy
            self.V[x] ^= self.V[y]
        elif n == 0x4:
            # 8xy4: ADD Vx, Vy - Set Vx = Vx + Vy, VF = carry
            result = self.V[x] + self.V[y]
            self.V[0xF] = 1 if result > 255 else 0
            self.V[x] = result & 0xFF
        elif n == 0x5:
            # 8xy5: SUB Vx, Vy - Set Vx = Vx - Vy, VF = NOT borrow
            self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
        elif n == 0x6:
            # 8xy6: SHR Vx - Set Vx = Vx >> 1, VF = LSB before shift
            self.V[0xF] = self.V[x] & 0x1
            self.V[x] >>= 1
        elif n == 0x7:
            # 8xy7: SUBN Vx, Vy - Set Vx = Vy - Vx, VF = NOT borrow
            self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
        elif n == 0xE:
            # 8xyE: SHL Vx - Set Vx = Vx << 1, VF = MSB before shift
            self.V[0xF] = (self.V[x] & 0x80) >> 7
            self.V[x] = (self.V[x] << 1) & 0xFF

    def _execute_Fxxx(self, opcode, x, kk):
        """Handle Fxxx opcodes (timers, memory, BCD, etc.)."""
        if kk == 0x07:
            # Fx07: LD Vx, DT - Set Vx = delay timer
            self.V[x] = self.delay_timer
        elif kk == 0x0A:
            # Fx0A: LD Vx, K - Wait for key press, store in Vx
            # This blocks until a key is pressed
            key_pressed = False
            for i in range(16):
                if self.keys[i]:
                    self.V[x] = i
                    key_pressed = True
                    break
            if not key_pressed:
                # Repeat this instruction (don't advance PC)
                self.pc -= 2
        elif kk == 0x15:
            # Fx15: LD DT, Vx - Set delay timer = Vx
            self.delay_timer = self.V[x]
        elif kk == 0x18:
            # Fx18: LD ST, Vx - Set sound timer = Vx
            self.sound_timer = self.V[x]
        elif kk == 0x1E:
            # Fx1E: ADD I, Vx - Set I = I + Vx
            self.I = (self.I + self.V[x]) & 0xFFFF
        elif kk == 0x29:
            # Fx29: LD F, Vx - Set I = location of sprite for digit Vx
            # Each font character is 5 bytes, stored at 0x000
            self.I = (self.V[x] & 0xF) * 5
        elif kk == 0x33:
            # Fx33: LD B, Vx - Store BCD representation of Vx at I, I+1, I+2
            value = self.V[x]
            self.memory[self.I] = value // 100
            self.memory[self.I + 1] = (value // 10) % 10
            self.memory[self.I + 2] = value % 10
        elif kk == 0x55:
            # Fx55: LD [I], Vx - Store V0 through Vx in memory starting at I
            for i in range(x + 1):
                self.memory[self.I + i] = self.V[i]
        elif kk == 0x65:
            # Fx65: LD Vx, [I] - Read V0 through Vx from memory starting at I
            for i in range(x + 1):
                self.V[i] = self.memory[self.I + i]

    def _draw_sprite(self, x, y, height):
        """Draw a sprite at position (Vx, Vy) with given height.

        Sprites are XORed onto the display. If any pixel is erased
        (changed from 1 to 0), VF is set to 1, otherwise 0.
        """
        x_pos = self.V[x] % 64  # Wrap around screen
        y_pos = self.V[y] % 32

        self.V[0xF] = 0  # Reset collision flag

        for row in range(height):
            if y_pos + row >= 32:
                break  # Stop if we go off screen

            sprite_byte = self.memory[self.I + row]

            for col in range(8):
                if x_pos + col >= 64:
                    break  # Stop if we go off screen

                # Check if sprite pixel is on (read bits left to right)
                sprite_pixel = (sprite_byte >> (7 - col)) & 0x1

                if sprite_pixel:
                    # XOR with current display pixel
                    if self.display[y_pos + row][x_pos + col] == 1:
                        self.V[0xF] = 1  # Collision detected
                    self.display[y_pos + row][x_pos + col] ^= 1

        self.draw_flag = True