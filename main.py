import pygame
import sys
from Chip8 import Chip8

# Display scaling (64x32 native, scaled up for visibility)
SCALE = 10
SCREEN_WIDTH = 64 * SCALE
SCREEN_HEIGHT = 32 * SCALE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Chip8 keypad layout:      Keyboard mapping:
#   1 2 3 C                   1 2 3 4
#   4 5 6 D       ->          Q W E R
#   7 8 9 E                   A S D F
#   A 0 B F                   Z X C V

KEY_MAP = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF,
}


def draw_display(screen, chip8):
    """Render the Chip8 display to the pygame window."""
    for y in range(32):
        for x in range(64):
            color = WHITE if chip8.display[y][x] else BLACK
            rect = pygame.Rect(x * SCALE, y * SCALE, SCALE, SCALE)
            pygame.draw.rect(screen, color, rect)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <rom_file>")
        print("Example: python main.py roms/PONG")
        sys.exit(1)

    rom_path = sys.argv[1]

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Chip8 Emulator - {rom_path}")
    clock = pygame.time.Clock()

    # Initialize Chip8
    chip8 = Chip8()
    chip8.load_rom(rom_path)

    # Main emulation loop
    running = True
    cycles_per_frame = 10  # Adjust for speed (higher = faster)

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in KEY_MAP:
                    chip8.keys[KEY_MAP[event.key]] = 1
            elif event.type == pygame.KEYUP:
                if event.key in KEY_MAP:
                    chip8.keys[KEY_MAP[event.key]] = 0

        # Execute CPU cycles
        for _ in range(cycles_per_frame):
            chip8.cycle()

        # Update timers at 60Hz
        chip8.update_timers()

        # Render display if needed
        if chip8.draw_flag:
            draw_display(screen, chip8)
            pygame.display.flip()
            chip8.draw_flag = False

        # Play beep if sound timer is active
        # (You could add actual sound here with pygame.mixer)
        if chip8.sound_timer > 0:
            pass  # Beep!

        # Cap at 60 FPS (timers run at 60Hz)
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
