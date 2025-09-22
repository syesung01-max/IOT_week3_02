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

# 음계 주파수 정의
NOTES = {
    'C4': 261, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494, 'C5': 523,
    'REST': 0  # 쉼표
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

def play_melody(board, pin, melody, bpm=120):
    """멜로디 재생 함수"""
    beat_ms = int(60000 / bpm)  # 1박자 길이 (밀리초)
    
    print(f"🎵 BPM {bpm}로 멜로디 재생 시작...")
    
    for i, (note, beats) in enumerate(melody):
        freq = NOTES[note]
        duration_ms = int(beat_ms * beats)
        
        if freq > 0:  # 음표
            # 실제 소리 지속시간을 약간 짧게 (80%)하여 음표 구분
            sound_duration = int(duration_ms * 0.8)
            play_tone(board, pin, freq, sound_duration)
            print(f"♪ {note} ({freq}Hz) - {beats}박자")
        else:  # 쉼표
            print(f"♫ 쉼표 - {beats}박자")
        
        time.sleep(duration_ms / 1000)  # 박자만큼 대기
    
    print("🎉 연주 완료!")

# Arduino 연결
board = pyfirmata2.Arduino('COM9')  # COM3 -> COM9으로 변경

# Iterator 시작 (필수!)
it = pyfirmata2.util.Iterator(board)
it.start()

print("🎼 반짝반짝 작은별 무한 재생")
print("Ctrl+C로 종료")

try:
    while True:
        play_melody(board, 8, TWINKLE_STAR, bpm=100)
        time.sleep(3)  # 3초 휴식 후 다시 재생
        
except KeyboardInterrupt:
    print("\n🎵 연주 중단")
    
finally:
    board.exit()
    print("🔌 Arduino 연결 종료")