import keyboard
import pyautogui
from time import sleep

sleep(2)
delay = 0.2

while True:
    x, y = pyautogui.position()
    color = pyautogui.pixel(x, y)
    # print(color)

    if color == (0, 0, 0):
        print("Pula")
        keyboard.press('c')
        sleep(0.05)
        keyboard.release('c')
        sleep(delay)

        if delay > 0.05:
            delay -= 0.005