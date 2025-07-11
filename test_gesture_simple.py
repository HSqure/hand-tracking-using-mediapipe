import cv2
import mediapipe as mp
import json
import socket
import time

# 简化版手势检测，便于测试
def main():
    # 网络设置
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ue5_ip = "127.0.0.1"
    ue5_port = 12345
    
    # MediaPipe设置
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils
    
    # 摄像头设置
    cap = cv2.VideoCapture(0)
    
    print(f"发送手势数据到UE5: {ue5_ip}:{ue5_port}")
    print("支持手势：握拳(停止)、张开手掌(跳跃)、指向(移动)")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        gesture_command = "idle"
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制手部关键点
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # 简单手势识别
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append([lm.x, lm.y])
                
                # 检测握拳（所有指尖都在对应关节下方）
                fingers_down = 0
                finger_tips = [4, 8, 12, 16, 20]
                finger_joints = [3, 6, 10, 14, 18]
                
                for tip, joint in zip(finger_tips, finger_joints):
                    if landmarks[tip][1] > landmarks[joint][1]:
                        fingers_down += 1
                
                if fingers_down >= 4:
                    gesture_command = "stop"
                elif fingers_down <= 1:
                    gesture_command = "jump"
                elif landmarks[8][1] < landmarks[6][1] and fingers_down >= 3:  # 食指向上
                    gesture_command = "move_forward"
        
        # 发送数据到UE5
        data = {
            "command": gesture_command,
            "timestamp": time.time()
        }
        
        try:
            json_data = json.dumps(data)
            sock.sendto(json_data.encode(), (ue5_ip, ue5_port))
        except Exception as e:
            print(f"发送失败: {e}")
        
        # 显示当前命令
        cv2.putText(frame, f"Command: {gesture_command}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Gesture Control", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    sock.close()

if __name__ == "__main__":
    main()