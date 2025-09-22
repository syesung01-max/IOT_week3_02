import pyfirmata2
import time
import threading

TONE_CMD = 0x7E

# 전역 변수로 현재 재생 중인 멜로디와 스레드 상태를 관리합니다.
current_playing_melody = None
melody_thread = None
stop_event = threading.Event()

# 버튼의 마지막 눌림 시간을 저장하는 변수
last_press_time_1 = 0
last_press_time_2 = 0
DEBOUNCE_DELAY = 0.2  # 200ms 디바운스 딜레이

def play_tone(board, pin, freq, duration):
    """음계 재생 함수"""
    data = [
        pin,
        freq & 0x7F, (freq >> 7) & 0x7F,
        duration & 0x7F, (duration >> 7) & 0x7F
    ]
    board.send_sysex(TONE_CMD, data)

# 음계 주파수 정의
NOTES = {
    'C4': 261, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494, 'C5': 523,
    'REST': 0
}

# 반짝반짝 작은별 악보 (음표, 박자)
TWINKLE_STAR = [
    ('C4', 1), ('C4', 1), ('G4', 1), ('G4', 1),
    ('A4', 1), ('A4', 1), ('G4', 2),
    ('F4', 1), ('F4', 1), ('E4', 1), ('E4', 1),
    ('D4', 1), ('D4', 1), ('C4', 2),
    ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
    ('E4', 1), ('E4', 1), ('D4', 2),
    ('G4', 1), ('G4', 1), ('F4', 1), ('F4', 1),
    ('E4', 1), ('E4', 1), ('D4', 2),
]

# Happy Birthday 악보 (음표, 박자)
HAPPY_BIRTHDAY = [
    ('C4', 1), ('C4', 1), ('D4', 2), ('C4', 2), ('F4', 2), ('E4', 4),
    ('REST', 2),
    ('C4', 1), ('C4', 1), ('D4', 2), ('C4', 2), ('G4', 2), ('F4', 4),
    ('REST', 2),
    ('C4', 1), ('C4', 1), ('C5', 2), ('A4', 2), ('F4', 2), ('E4', 2), ('D4', 4),
    ('REST', 2),
    ('B4', 1), ('B4', 1), ('A4', 2), ('F4', 2), ('G4', 2), ('F4', 4)
]

def play_melody(board, pin, melody, bpm=120, led=None):
    """멜로디 재생 함수 (스레드에서 실행)"""
    global current_playing_melody
    
    if led:
        led.write(1)
        
    beat_ms = int(60000 / bpm)
    
    for note, beats in melody:
        if stop_event.is_set():
            break
            
        freq = NOTES[note]
        duration_ms = int(beat_ms * beats)
        
        if freq > 0:
            sound_duration = int(duration_ms * 0.8)
            play_tone(board, pin, freq, sound_duration)
        
        time.sleep(duration_ms / 1000)
    
    if led:
        led.write(0)

    current_playing_melody = None
    stop_event.clear()
    print("🎉 연주 완료 또는 중단")

def stop_and_start_new_melody(melody_id, melody_data, bpm, led):
    """현재 재생 중인 멜로디를 중단하고 새로운 멜로디를 시작합니다."""
    global current_playing_melody, melody_thread

    if current_playing_melody:
        print("🎵 이전 노래 재생 중, 중단 후 새로 시작")
        stop_event.set()
        if melody_thread and melody_thread.is_alive():
            melody_thread.join()
        
    print(f"🎵 {melody_id} 재생 시작")
    current_playing_melody = melody_id
    melody_thread = threading.Thread(target=play_melody, args=(board, 8, melody_data, bpm, led))
    melody_thread.start()

# Arduino 연결
board = pyfirmata2.Arduino('COM9')

# Iterator 시작 (필수!)
it = pyfirmata2.util.Iterator(board)
it.start()

# 핀 설정
buzzer_pin = 8
button_1 = board.get_pin('d:2:i')
button_2 = board.get_pin('d:3:i')
led_1 = board.get_pin('d:4:o')
led_2 = board.get_pin('d:5:o')

print("🎼 버튼을 눌러 원하는 노래를 재생하세요!")
print("Ctrl+C로 종료")

def on_button_1_press(state):
    global last_press_time_1
    current_time = time.time()
    if state == 0 and (current_time - last_press_time_1) > DEBOUNCE_DELAY:
        last_press_time_1 = current_time
        stop_and_start_new_melody('TWINKLE_STAR', TWINKLE_STAR, 100, led_1)

def on_button_2_press(state):
    global last_press_time_2
    current_time = time.time()
    if state == 0 and (current_time - last_press_time_2) > DEBOUNCE_DELAY:
        last_press_time_2 = current_time
        stop_and_start_new_melody('HAPPY_BIRTHDAY', HAPPY_BIRTHDAY, 120, led_2)

# 콜백 등록
button_1.register_callback(on_button_1_press)
button_1.enable_reporting()

button_2.register_callback(on_button_2_press)
button_2.enable_reporting()

try:
    while True:
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n프로그램 종료")
    
finally:
    board.exit()
    print("🔌 Arduino 연결 종료")