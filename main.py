import pygame as pg
import numpy as np
import cpu
from numpy import random




chip = cpu.chip8()
op = cpu.OP_CO(chip)
key = cpu.Keys()
sprites = cpu.sprites()

HEIGHT = 32
WIDTH = 64
pixel_size = 10
buffer_display = [[0 for _ in range(64)] for _ in range(32)]
# tela de 64x32


        
    

def ROMCHARG(chip):
        name = input("Name of the game: ")
        with open(f"./ROMS/{name}.ch8", 'rb') as file:
            rom_data = file.read()
            print('rom', rom_data[50:60])

        if len(rom_data) > 4096 - 0x200:
            raise ValueError("ROM é muito grande para caber na memória")  ## the mf problem is here

        # Carrega o ROM na memória a partir do endereço 0x200
        chip.Memory[chip.pc:chip.pc + len(rom_data)] = list(rom_data)
        #print(chip.Memory[0x200:0x200 + 10]) teste pra entender carga, positivo, tem dados

        print(f"ROM carregado: {len(rom_data)} bytes copiados para a memória")
        print("Primeiros 16 bytes do ROM carregado:")
        print(chip.Memory[chip.pc:chip.pc+16]) 

        return True


def fetch_opcde (screen, chip, op): 
# pegar x, y, nnn e outros, além de verificar um op code, depois programar sua saída
    if chip.pc >= len(chip.Memory): 
        chip.pc = chip.pc % len(chip.Memory)
    
    byte1 = chip.Memory[chip.pc % len(chip.Memory)] # a nao ser que o pc seja maior que o valor da memoria, o numero vai ser o mesmo, se não, vai ser memoria - pc
    byte2 = chip.Memory[(chip.pc + 1) % len(chip.Memory)]
    byte1s = int(byte1) << 8 # int() vai setar a variavel para 16 bits ao invez de 8, podendo assim fazer o shift e juntar as 2 variaveis
    byte2s = int(byte2)
    #print("mem", chip.Memory[chip.pc], chip.pc) # no primeiro print roda tudo bem, depois dele, tudo vira zero
    if byte1s | byte2s != 0:
        op.op_code = byte1s | byte2s ## here, we get the op code, the most high 4 bits of 1 8 bits data, and the same with the next, but the lowest in case
        
        op.x = byte1 & 0x0F # & - substituir, if match = match value, else = 0
        op.y = (byte2 >> 4) & 0x0F
        op.n = byte2 & 0x0F
        op.kk = byte2
        op.nnn = op.op_code & 0x0FFF
        translate_opcode(screen, chip, op)
        debug(chip, byte1, byte2, op)
        #print(op.x)
        #print(op.y)
    chip.pc+=2
    return op.op_code

def translate_opcode (screen, chip, op): # notas opcode - V -> registrador, x base 1, y mais high, ou seja, quando for verificar fazer y - 15, para ler como um byte padrão e não como o conjunto mais alto
    if op.op_code != 0:
        if ((op.op_code & 0xF000) == 0):
            if (op.kk == 0xE0):
                for i in range(32):
                    for x in range(64):
                        buffer_display[i][x] = 0
                screen.fill((0, 0, 0,))
                print("Clear")

            if (op.kk == 0xEE):
                chip.pc = chip.stack[chip.sp - 1]
                chip.sp -= 1
                
                
        elif ((op.op_code & 0xF000) == 0x1000):
            chip.pc = op.op_code & 0x0FFF
            chip.pc -= 2 # pc exacty
        elif ((op.op_code & 0xF000) == 0x2000):
            chip.stack[chip.sp] = chip.pc
            chip.sp += 1
            chip.pc = op.nnn
            chip.pc -= 2 # garantee the exact value

        elif ((op.op_code & 0xF000) == 0x3000): 
            if chip.V[op.x] == op.kk:
                chip.pc += 2
            print(chip.V[op.x], op.kk)
        elif ((op.op_code & 0xF000) == 0x4000): 
            if chip.V[op.x] != op.kk:
                chip.pc += 2
        elif ((op.op_code & 0xF000) == 0x5000):
            if (op.n == 0):
                if (chip.V[op.x] == chip.V[op.y]):
                    chip.pc += 2
        elif ((op.op_code & 0xF000) == 0x6000):
            chip.V[op.x] = op.kk
        elif ((op.op_code & 0xF000) == 0x7000):
            chip.V[op.x] = (chip.V[op.x] + op.kk) & 0xFF
        elif ((op.op_code & 0xF000) == 0x8000): #grupo dos 8
            if (op.n == 0x0):
                chip.V[op.x] = chip.V[op.y] 
            elif (op.n == 0x1):
                Vx = chip.V[op.x]
                Vy = chip.V[op.y]
                nu = Vx | Vy
                chip.V[op.x] = nu                
            elif (op.n == 0x2):
                Vx = chip.V[op.x]
                Vy = chip.V[op.y]
                nu = Vx & Vy
                chip.V[op.x] = nu
            elif (op.n == 0x3):
                Vx = chip.V[op.x]
                Vy = chip.V[op.y]
                nu = Vx ^ Vy
                chip.V[op.x] = nu
            elif (op.n == 0x4):
                Vx = chip.V[op.x]
                Vy = chip.V[op.y]
                
                nu = Vx + Vy
                chip.V[op.x] = nu & 0xFF ######### isolar ulitmos 8 bits
                if (nu > 255):
                    chip.V[0xF] = 1
                else: 
                    chip.V[0xF] = 0
                
            elif (op.n == 0x5):
                Vx = chip.V[op.x]
                chip.V[op.x] = (chip.V[op.x] - chip.V[op.y]) & 0xFF
                chip.V[0xF] = 1 if Vx >= chip.V[op.y] else 0
                
            elif (op.n == 0x6):
                Vx = chip.V[op.x] # still having an error here, idk where
                chip.V[0xF] = Vx & 0x01
                chip.V[op.x] = (Vx >> 1) & 0xFF
            elif (op.n == 0x7):
                Vx = chip.V[op.x]
                Vy = chip.V[op.y]
                chip.V[op.x] = (Vy - chip.V[op.x]) & 0xFF
                if (Vy < Vx):
                    chip.V[0xF] = 0
                else:
                    chip.V[0xF] = 1

            elif (op.n == 0xE):
                Vx = chip.V[op.x]
                chip.V[op.x] = Vx << 1 & 0xFF
                chip.V[0xF] = (Vx >> 7) & 0x1
                

        elif ((op.op_code & 0xF000) == 0x9000):
            if op.n == 0:
                if chip.V[op.x] != chip.V[op.y]:
                    chip.pc += 2
        elif ((op.op_code & 0xF000) == 0xA000):
            chip.I = op.nnn
        elif ((op.op_code & 0xF000) == 0xB000):
            chip.pc = op.nnn + chip.V[0]
        elif ((op.op_code & 0xF000) == 0xC000):
            nu = random.randint(0, 255)
            chip.V[op.x] = nu & op.kk
        elif ((op.op_code & 0xF000) == 0xD000): #DRAWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
            print("draw") # é como se so tivesse lendo uma parte do byte, reve a logica e refaz o processo
            Vx = chip.V[op.x]
            Vy = chip.V[op.y]
            chip.V[0xF] = 0
            for n in range(op.n):
                spr = chip.Memory[chip.I+n] # 1 byte
                y = (Vy + n) % 32        # altura
                for b in range(8): # bit a bit
                        x = (Vx + b) % 64
                        if spr & (0x80 >> b): # mascara o bite pra verificar se é 1 ou 0
                            screen_px = buffer_display[y][x]
                            buffer_display[y][x] ^= 1
                            if screen_px == 1:
                                chip.V[0xF] = 1
                        if buffer_display[y][x] == 1:
                            color = (255, 255, 255)
                            pg.draw.rect(screen, color, pg.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size))
                        elif buffer_display[y][x] == 0: # just eskeleton, its not right yet, still missing data info, how pull bytes, how they influentes the buffer, its 8 bits not 1, and maybe sprites coding
                            color = (0, 0, 0)
                            pg.draw.rect(screen, color, pg.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size))
            pg.display.update()

        elif ((op.op_code & 0xF000) == 0xE000):
            get_events(chip)
            if (op.n == 0xE): # por algum motivo input ta sendo interpretado como int e não objeto ????w
                Vx = int(chip.V[op.x] % len(chip.input))
                if chip.input[Vx] == 1:
                    chip.pc += 2
            elif (op.n == 0x1):
                Vx = int(chip.V[op.x] % len(chip.input))
                if chip.input[Vx] == 0:
                    chip.pc += 2
                    
        elif ((op.op_code & 0xF000) == 0xF000):
            if (op.kk == 0x07):
                chip.V[op.x] = chip.dt
            elif (op.kk == 0x0A):
                key_press = False
                for x in range(len(chip.input)):
                    if chip.input[x] == 1:
                        chip.V[op.x] = x
                        key_press = True
                        break
                    if not key_press:
                        chip.pc -= 2

            elif (op.kk == 0x15):
                Vx = chip.V[op.x]
                chip.dt = Vx
            elif (op.kk == 0x18):
                Vx = chip.V[op.x]
                chip.st = Vx
            elif (op.kk == 0x1E):
                chip.I += chip.V[op.x]
            elif (op.kk == 0x29):
                Vx = chip.V[op.x]
                chip.I = 0x50 + (Vx * 5) # adress da fonte - acredito que esteja certo

            elif (op.kk == 0x33):
                Vx = chip.V[op.x]
                chip.Memory[chip.I] = int(Vx/100)
                chip.Memory[chip.I + 1] = int(((Vx % 100) - Vx % 10) / 10)
                chip.Memory[chip.I + 2] = (Vx % 10)

            elif (op.kk == 0x55):
                for i in range(op.x + 1):
                    chip.Memory[chip.I + i] = chip.V[i]   ## erro aqui dpois resorve
                   
            elif (op.kk == 0x65):
                for i in range(op.x + 1):
                    chip.V[i] = chip.Memory[chip.I + i] 
                   




def debug (chip, byte1, byte2, op):
    print(f"Byte 1: {byte1:02X}, Byte 2: {byte2:02X}, Opcode: {op.op_code:04X}")
    print("Stack, sp", chip.stack, chip.sp)
    print("V, I", chip.V, chip.I)
    print("pc", chip.pc)
            
def timer (chip):
    if chip.dt > 0:
        chip.dt -= 1

    if chip.st > 0:
        chip.st -= 1
        if chip.st == 0:
            print("beep!")
            pg.mixer.music.play()



def get_events (chip):
    for e in pg.event.get():
        if e.type == pg.QUIT:
            exit()
            return False
        
        

                


def init_chip (chip):
    pg.mixer.init()
    chip.pc = 0x200
    chip.op_code = np.uint16(0)
    chip.Memory = np.zeros(4096, dtype=np.uint8)
    chip.dt = 60
    chip.st = 30
    chip.sp = 0
    for i in chip.input:
        chip.input[i] = 0
    for i in sprites.fontset:
        chip.Memory[i + 0x50] = sprites.fontset[i % len(sprites.fontset)]
    pg.mixer.music.load("./ROMS/beep_sound.mp3")


def main():
    init_chip(chip) #-
    ROMCHARG(chip) #- 
    #- mas sem certeza que pode ser mudado
    #print("fora", chip.Memory[0x200:0x200 + 16])


    screen = pg.display.set_mode(((WIDTH * pixel_size), (HEIGHT * pixel_size))) # create a display with the size difined before
    clock = pg.time.Clock() # define a clock to measure the time, control some functions
    screen.fill(pg.Color(0, 0, 0))
    Running = True
    while (Running == True):
        for e in pg.event.get():
        # Verifica se o usuário fechou a janela
            if e.type == pg.QUIT:
                pg.quit()
                Running = False
            elif e.type == pg.KEYDOWN:
                
                if e.key == pg.K_1: chip.input[0x1] = 1
                elif e.key == pg.K_2: chip.input[0x2] = 1
                elif e.key == pg.K_3: chip.input[0x3] = 1
                elif e.key == pg.K_4: chip.input[0xC] = 1
                elif e.key == pg.K_q: chip.input[0x4] = 1
                elif e.key == pg.K_w: chip.input[0x5] = 1
                elif e.key == pg.K_e: chip.input[0x6] = 1
                elif e.key == pg.K_r: chip.input[0xD] = 1
                elif e.key == pg.K_a: chip.input[0x7] = 1
                elif e.key == pg.K_s: chip.input[0x8] = 1
                elif e.key == pg.K_d: chip.input[0x9] = 1
                elif e.key == pg.K_f: chip.input[0xE] = 1
                elif e.key == pg.K_z: chip.input[0xA] = 1
                elif e.key == pg.K_x: chip.input[0x0] = 1
                elif e.key == pg.K_c: chip.input[0xB] = 1
                elif e.key == pg.K_v: chip.input[0xF] = 1
                print("TECLA PRESSIONADA")
        
            elif e.type == pg.KEYUP:
                print("TECLA SOLTA")
                if e.key == pg.K_1: chip.input[0x1] = 0
                elif e.key == pg.K_2: chip.input[0x2] = 0
                elif e.key == pg.K_3: chip.input[0x3] = 0
                elif e.key == pg.K_4: chip.input[0xC] = 0
                elif e.key == pg.K_q: chip.input[0x4] = 0
                elif e.key == pg.K_w: chip.input[0x5] = 0
                elif e.key == pg.K_e: chip.input[0x6] = 0
                elif e.key == pg.K_r: chip.input[0xD] = 0
                elif e.key == pg.K_a: chip.input[0x7] = 0
                elif e.key == pg.K_s: chip.input[0x8] = 0
                elif e.key == pg.K_d: chip.input[0x9] = 0
                elif e.key == pg.K_f: chip.input[0xE] = 0
                elif e.key == pg.K_z: chip.input[0xA] = 0
                elif e.key == pg.K_x: chip.input[0x0] = 0
                elif e.key == pg.K_c: chip.input[0xB] = 0
                elif e.key == pg.K_v: chip.input[0xF] = 0


        print(chip.input)
        fetch_opcde(screen, chip, op) #-
        timer(chip)
        clock.tick(3000)
        pg.display.flip()
        #if nun == 30:
         #   Running = False

if (__name__ == "__main__"):
    main()


            