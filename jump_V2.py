import keyboard
import pyautogui
from time import sleep

sleep(2)

# posição fixa do cursor (exemplo)
x = 500
y = 300

while True:
    color = pyautogui.pixel(x, y)
    print(color)

    if color == (0, 0, 0):  # obstáculo detectado
        print("Pula")
        keyboard.press('c')
        sleep(0.05)
        keyboard.release('c')