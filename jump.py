from PIL import ImageGrab
from time import sleep, time
import numpy as np
import pygetwindow as gw
import cv2 
import pydirectinput

# --- VARIÁVEIS DE CONFIGURAÇÃO AJUSTADAS ---
EMULATOR_WINDOW_TITLE = "RALibRetro - 1.8 - mGBA 0.11-dev c758314 - GameBoy - CarlosNatanael"
REGION = (410, 300, 750, 390) 

# Configurações dinâmicas baseadas na velocidade do jogo
BASE_CHECK_POINT_X = 100
SPEED_ADJUSTMENTS = {
    0: {'x_offset': 100, 'jump_delay': 0.05, 'check_interval': 0.05, 'detection_range': 30},
    100: {'x_offset': 80, 'jump_delay': 0.02, 'check_interval': 0.03, 'detection_range': 40},
    200: {'x_offset': 70, 'jump_delay': 0.015, 'check_interval': 0.02, 'detection_range': 50},
    300: {'x_offset': 60, 'jump_delay': 0.01, 'check_interval': 0.015, 'detection_range': 60},
    400: {'x_offset': 50, 'jump_delay': 0.008, 'check_interval': 0.01, 'detection_range': 70},
}

GAME_ACTION_KEY = 't'
MIN_OBSTACLE_AREA = 80
THRESHOLD_VALUE = 200
MAX_SCORE = 999

# Variáveis de estado - inicializadas aqui
last_jump_time = 0
detection_history = []

def focus_emulator():
    try:
        window = gw.getWindowsWithTitle(EMULATOR_WINDOW_TITLE)
        if window:
            window[0].activate() 
            sleep(0.05)
            return True
        return False
    except Exception as e:
        print(f"Erro ao focar a janela: {e}")
        return False

def get_speed_settings(score):
    """Retorna configurações baseadas no score"""
    if score >= 40:
        return SPEED_ADJUSTMENTS[40]
    elif score >= 30:
        return SPEED_ADJUSTMENTS[30]
    elif score >= 20:
        return SPEED_ADJUSTMENTS[20]
    elif score >= 10:
        return SPEED_ADJUSTMENTS[10]
    else:
        return SPEED_ADJUSTMENTS[0]

def jump(settings, obstacle_distance=None):
    """Executa um pulo com timing baseado na distância do obstáculo"""
    global last_jump_time  # Declaração global no início da função
    
    current_time = time()
    jump_cooldown = 0.3
    
    if current_time - last_jump_time < jump_cooldown:
        return
    
    if focus_emulator():
        # Se sabemos a distância, ajustamos o timing
        if obstacle_distance and obstacle_distance < 50:
            pydirectinput.keyDown(GAME_ACTION_KEY)
            sleep(0.01)
            pydirectinput.keyUp(GAME_ACTION_KEY)
            print("PULO DE EMERGÊNCIA!")
        else:
            pydirectinput.keyDown(GAME_ACTION_KEY)
            sleep(settings['jump_delay'])
            pydirectinput.keyUp(GAME_ACTION_KEY)
    
    last_jump_time = current_time

def check_for_obstacles(region, settings):
    """Detecta obstáculos com offset ajustável e calcula distância"""
    screenshot = ImageGrab.grab(region)
    img = np.array(screenshot)
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    ret, thresh = cv2.threshold(gray_img, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)
    
    roi_start_x = settings['x_offset']
    detection_range = settings['detection_range']
    roi_end_x = roi_start_x + detection_range
    
    roi_height_start = int(img.shape[0] * 0.4)
    roi_height_end = int(img.shape[0] * 0.9)
    
    roi = thresh[roi_height_start:roi_height_end, roi_start_x:roi_end_x]
    
    kernel = np.ones((3,3), np.uint8)
    roi = cv2.erode(roi, kernel, iterations=1)
    
    contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    closest_obstacle = None
    closest_distance = float('inf')
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        
        if area > MIN_OBSTACLE_AREA:
            x, y, w, h = cv2.boundingRect(cnt)
            
            abs_x = x + roi_start_x
            abs_y = y + roi_height_start
            
            distance = abs_x - roi_start_x
            
            if distance < closest_distance:
                closest_distance = distance
                closest_obstacle = {
                    'x': abs_x, 'y': abs_y, 
                    'w': w, 'h': h, 
                    'area': area,
                    'distance': distance
                }
    
    if closest_obstacle:
        cv2.rectangle(img, 
                     (closest_obstacle['x'], closest_obstacle['y']),
                     (closest_obstacle['x'] + closest_obstacle['w'], 
                      closest_obstacle['y'] + closest_obstacle['h']),
                     (0, 255, 0), 2)
        
        cv2.putText(img, f"Dist: {closest_obstacle['distance']}", 
                   (closest_obstacle['x'], closest_obstacle['y'] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        cv2.line(img, (roi_start_x, 0), (roi_start_x, img.shape[0]), (255, 0, 0), 2)
        
        print(f"Obstáculo detectado! Distância: {closest_obstacle['distance']}, Área: {closest_obstacle['area']:.1f}")
        
        if closest_obstacle['distance'] < 35:
            detection_history.append({
                'time': time(),
                'distance': closest_obstacle['distance']
            })
            
            if len(detection_history) > 10:
                detection_history.pop(0)
            
            return "JUMP", closest_obstacle['distance']
    
    cv2.imshow('(DEBUG)', img)
    cv2.waitKey(1)
    return "NONE", None

def calculate_optimal_jump_distance(settings):
    """Calcula a distância ideal para pular baseado na velocidade"""
    base_distance = 40
    speed_factor = 0.1 * (settings['x_offset'] / 100)
    return base_distance * (1 + speed_factor)

def restart_game():
    if focus_emulator():
        pydirectinput.press(GAME_ACTION_KEY)

def run_bot():
    print("Bot iniciado. Pressione Ctrl+C para parar.")
    print("Dica: Ajuste 'x_offset' nas SPEED_ADJUTMENTS para mudar o timing!")
    sleep(3)
    
    if not focus_emulator():
        print("Emulador não encontrado!")
        return
    
    restart_game()
    score = 0
    consecutive_jumps = 0
    
    try:
        while score < MAX_SCORE:
            settings = get_speed_settings(score)
            
            result, distance = check_for_obstacles(REGION, settings)
            
            if result == "JUMP":
                optimal_distance = calculate_optimal_jump_distance(settings)
                
                if distance:
                    print(f"Distância atual: {distance}, Ideal: {optimal_distance:.1f}")
                
                jump(settings, distance)
                consecutive_jumps += 1
                
                sleep(0.05)
            else:
                consecutive_jumps = 0
            
            score += 1
            
            if score % 100 == 0:
                print(f"Score: {score} | Offset X: {settings['x_offset']} | Checks/s: {1/settings['check_interval']:.1f}")
                if detection_history:
                    avg_distance = sum(d['distance'] for d in detection_history[-5:]) / min(5, len(detection_history))
                    print(f"Distância média de pulo: {avg_distance:.1f}")
            
            sleep(settings['check_interval'])
            
    except KeyboardInterrupt:
        print("\nBot parado pelo usuário.")
    finally:
        cv2.destroyAllWindows()
        print("Bot encerrado.")
        print("\nDicas para ajuste:")
        print(f"1. Ajuste 'x_offset' em SPEED_ADJUSTMENTS (valores menores = pular mais tarde)")
        print(f"2. Ajuste 'detection_range' (menor = área de detecção menor)")
        print(f"3. Teste com 'if closest_obstacle['distance'] < XX:' (linha 131)")

if __name__ == "__main__":
    run_bot()