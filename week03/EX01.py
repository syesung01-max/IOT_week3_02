import pyfirmata2
import time

TONE_CMD = 0x7E

def play_tone(board, pin, freq, duration):
    """음계 재생 함수"""
    data = [
        pin,
        freq & 0x7F, (freq >> 7) & 0x7F,
        duration & 0x7F, (duration >> 7) & 0x7F
    ]
    board.send_sysex(TONE_CMD, data)

# Arduino 연결
board = pyfirmata2.Arduino('COM9')  # COM3 -> COM9으로 변경

# Iterator 시작 (필수!)
it = pyfirmata2.util.Iterator(board)
it.start()

# 버튼 설정
button = board.get_pin('d:2:i')

# 음계 리스트
SCALE = [261, 294, 330, 349, 392, 440, 494, 523]  # C4~C5
NOTE_NAMES = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']
current_note = 0

def play_next_note(state):
    """버튼 눌림 시 다음 음계 재생"""
    global current_note
    
    if state == 0:  # 버튼 눌림 (풀업이므로 LOW)
        freq = SCALE[current_note]
        note_name = NOTE_NAMES[current_note]
        
        play_tone(board, 8, freq, 500)  # 500ms 재생
        print(f"🎵 {note_name} ({freq}Hz)")
        
        current_note = (current_note + 1) % len(SCALE)  # 다음 음계로

# 콜백 등록
button.register_callback(play_next_note)
button.enable_reporting()

print("🎮 버튼으로 음계 제어")
print("버튼을 눌러서 음계를 연주하세요!")
print("Ctrl+C로 종료")

try:
    while True:
        time.sleep(0.1)  # CPU 효율적인 대기
        
except KeyboardInterrupt:
    print("\n프로그램 종료")
    
finally:
    board.exit()