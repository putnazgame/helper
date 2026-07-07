# -*- coding: utf-8 -*-
import pygame
pygame.init()
pygame.joystick.init()
screen = pygame.display.set_mode((560, 340))
pygame.display.set_caption("ทดสอบจอย — กด ESC ออก")
font  = pygame.font.SysFont("tahoma", 24)
small = pygame.font.SysFont("tahoma", 18)
clock = pygame.time.Clock()

if pygame.joystick.get_count() == 0:
    print("ไม่พบจอย"); pygame.quit(); exit()

js = pygame.joystick.Joystick(0)
print(f"จอย: {js.get_name()}  |  axes={js.get_numaxes()}  buttons={js.get_numbuttons()}")

last_btn  = "-"
last_axis = "-"

running = True
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT: running = False
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: running = False

        if ev.type == pygame.JOYBUTTONDOWN:
            last_btn = f"Button {ev.button}"
            print(last_btn)

        if ev.type == pygame.JOYAXISMOTION:
            # แสดงเฉพาะ axis ที่ขยับเกิน 0.3 เพื่อไม่ให้รก
            if abs(ev.value) > 0.3:
                last_axis = f"Axis {ev.axis}  =  {ev.value:.2f}"
                print(last_axis)

    screen.fill((20, 20, 35))
    screen.blit(font.render(f"ปุ่มล่าสุด:  {last_btn}",  True, (100, 220, 100)), (30, 80))
    screen.blit(font.render(f"Axis ล่าสุด: {last_axis}", True, (100, 180, 255)), (30, 130))
    screen.blit(small.render("กด LT แล้วดูค่า Axis ที่เปลี่ยน", True, (200, 200, 100)), (30, 200))
    screen.blit(small.render("ESC = ออก", True, (150, 150, 150)), (30, 290))
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
