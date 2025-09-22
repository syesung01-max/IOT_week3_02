import pyfirmata2
import time
import threading

# --- 설정 및 상수 ---
TONE_CMD = 0x7E
DEBOUNCE_TIME = 0.2  # 디바운싱 시간 (초)

# 음계 주파수 정의 (Hz)
NOTES = {
    'C4': 261, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494, 'C5': 523,
    'REST': 0
}

# 악보: (음표, 박자) 튜플 리스트
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

HAPPY_BIRTHDAY = [
    ('C4', 1), ('C4', 1), ('D4', 2), ('C4', 2), ('F4', 2), ('E4', 4),
    ('C4', 1), ('C4', 1), ('D4', 2), ('C4', 2), ('G4', 2), ('F4', 4),
    ('C4', 1), ('C4', 1), ('C5', 2), ('A4', 2), ('F4', 2), ('E4', 2), ('D4', 4),
    ('B4', 1), ('B4', 1), ('A4', 2), ('F4', 2), ('G4', 2), ('F4', 4)
]

# --- 전역 변수 ---
board = None
BUTTON_PIN_INDEX = 0  # 아날로그 핀 0번
LED1_PIN_INDEX = 13
LED2_PIN_INDEX = 12
BUZZER_PIN_INDEX = 8
current_state = 0
last_press_time = 0
stop_playing = threading.Event()  # 멜로디 중단을 위한 이벤트 플래그

def play_tone(pin, freq, duration):
    """Firmata 프로토콜을 사용하여 지정된 핀에서 소리를 재생합니다."""
    data = [
        pin,
        freq & 0x7F, (freq >> 7) & 0x7F,
        duration & 0x7F, (duration >> 7) & 0x7F
    ]
    board.send_sysex(TONE_CMD, data)

def play_melody(pin, melody, bpm=120):
    """악보 리스트를 바탕으로 멜로디를 재생합니다."""
    print("🎵 멜로디 연주 시작...")
    beat_ms = int(60000 / bpm)
    
    for note, beats in melody:
        if stop_playing.is_set():
            break  # 중단 신호가 감지되면 즉시 루프 종료
        
        freq = NOTES[note]
        duration_ms = int(beat_ms * beats)
        
        if freq > 0:
            sound_duration = int(duration_ms * 0.8)
            play_tone(pin, freq, sound_duration)
        
        # 멜로디 재생 중에도 버튼 입력을 감지할 수 있도록 짧게 나누어 sleep
        start_time = time.time()
        while time.time() - start_time < duration_ms / 1000:
            if stop_playing.is_set():
                break
            time.sleep(0.01)

    play_tone(pin, 0, 0)  # 멜로디가 끝나거나 중단되면 톤 끄기
    print("🎉 연주 완료 또는 중단!")
    stop_playing.clear() # 중단 신호 초기화

def button_callback(data):
    """버튼 상태 변경 시 호출되는 콜백 함수."""
    global current_state, last_press_time
    
    # 버튼이 눌렸는지 확인 (전압이 0.5V 이상)
    if data > 0.5:
        # 디바운싱 로직: 마지막 누름 시간과 현재 시간 차이가 DEBOUNCE_TIME보다 커야 유효한 입력으로 간주
        if time.time() - last_press_time > DEBOUNCE_TIME:
            last_press_time = time.time()
            
            # 중단 신호를 보냅니다.
            stop_playing.set()
            
            # 상태를 다음 단계로 변경합니다. (0 -> 1 -> 2 -> 0)
            current_state = (current_state + 1) % 3
            
            # 모든 LED를 끄고 소리를 멈춥니다.
            board.digital[LED1_PIN_INDEX].write(0)
            board.digital[LED2_PIN_INDEX].write(0)
            play_tone(BUZZER_PIN_INDEX, 0, 0)
            
            # 새로운 상태에 따라 동작을 실행합니다.
            if current_state == 1:
                print("\n▶️ '반짝반짝 작은별'을 연주합니다...")
                board.digital[LED1_PIN_INDEX].write(1)
                play_melody(BUZZER_PIN_INDEX, TWINKLE_STAR, bpm=100)
            elif current_state == 2:
                print("\n▶️ 'Happy Birthday'를 연주합니다...")
                board.digital[LED2_PIN_INDEX].write(1)
                play_melody(BUZZER_PIN_INDEX, HAPPY_BIRTHDAY, bpm=120)
            else:
                print("\n⏹️ 리셋합니다. 모든 LED가 꺼집니다. 다음 누름을 기다립니다.")
            
# --- 메인 실행 로직 ---

if __name__ == "__main__":
    try:
        # 아두이노 연결
        board = pyfirmata2.Arduino('COM9')
        
        # 핀 모드 설정
        board.digital[LED1_PIN_INDEX].mode = pyfirmata2.OUTPUT
        board.digital[LED2_PIN_INDEX].mode = pyfirmata2.OUTPUT
        board.digital[BUZZER_PIN_INDEX].mode = pyfirmata2.OUTPUT
        
        # 아날로그 핀 콜백 설정
        board.samplingOn(10)  # 10ms 간격으로 데이터 수신
        board.analog[BUTTON_PIN_INDEX].enable_reporting()
        board.analog[BUTTON_PIN_INDEX].register_callback(button_callback)
        
        print("🔌 아두이노 핀 초기화 완료.")
        print("버튼 누르기를 기다리는 중...")
        print("종료하려면 Ctrl+C를 누르세요.")
        
        # 프로그램이 종료되지 않도록 무한 루프 유지
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    finally:
        if board:
            board.exit()
            print("🔌 아두이노 연결 종료.")