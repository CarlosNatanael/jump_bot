import pyautogui
from PIL import ImageGrab
import numpy as np
import time
import pygetwindow as gw
import cv2 
import pydirectinput

EMULATOR_WINDOW_TITLE = "RALibRetro - 1.8 - mGBA 0.11-dev c758314 - GameBoy - CarlosNatanael"
REGION = (410, 300, 750, 390) 
CHECK_POINT_X_RELATIVO = 50 

GAME_ACTION_KEY = 'c'
MIN_OBSTACLE_AREA = 100
THRESHOLD_VALUE = 200

def focus_emulator():
    try:
        window = gw.getWindowsWithTitle(EMULATOR_WINDOW_TITLE)
        if window:
            window[0].activate() 
            time.sleep(0.1) 
            return True
        else:
            print(f"Aviso: Janela '{EMULATOR_WINDOW_TITLE}' não encontrada!")
            return False
    except Exception as e:
        print(f"Erro ao focar a janela: {e}")
        return False

def jump():
    if focus_emulator():
        pydirectinput.keyDown(GAME_ACTION_KEY)
        time.sleep(0.05)
        pydirectinput.keyUp(GAME_ACTION_KEY)

def restart_game():
    if focus_emulator():
        pydirectinput.press(GAME_ACTION_KEY)

def check_for_obstacles(region):
    screenshot = ImageGrab.grab(region)
    img = np.array(screenshot)
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    ret, thresh = cv2.threshold(gray_img, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)
    roi_start_x = CHECK_POINT_X_RELATIVO
    roi_end_x = roi_start_x + 55
    roi = thresh[:, roi_start_x:roi_end_x]
    contours, hierarchy = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    is_obstacle_detected = False
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        if area > MIN_OBSTACLE_AREA:
            x, y, w, h = cv2.boundingRect(cnt) 
            if y > (img.shape[0] / 3):
                cv2.rectangle(img, (x + roi_start_x, y), (x + roi_start_x + w, y + h), (0, 255, 0), 2)
                
                print(f"DETECTADO! Pulando")
                is_obstacle_detected = True
    cv2.imshow('(DEBUG)', img)
    cv2.waitKey(1)
    if is_obstacle_detected:
        return "JUMP"
    else:
        print("Nenhum obstaculo detectado.")
        return "NONE"

def run_bot():
    print("Bot iniciado.")
    time.sleep(3)
    if focus_emulator(): 
        restart_game() 
    else:
        print("Bot encerrado.")
        return
    while True:
        try:
            time.sleep(0.01)
            if check_for_obstacles(REGION) == "JUMP":
                jump()
        except KeyboardInterrupt:
            print("\nBot parado.")
            cv2.destroyAllWindows() 
            break

if __name__ == "__main__":
    run_bot()