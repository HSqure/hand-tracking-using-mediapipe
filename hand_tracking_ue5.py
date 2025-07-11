import cv2
import mediapipe as mp
import time
import json
import socket
import math

class HandGestureToUE5:
    def __init__(self, ue5_ip="127.0.0.1", ue5_port=12345):
        # 网络设置
        self.ue5_ip = ue5_ip
        self.ue5_port = ue5_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # MediaPipe设置
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mpDraw = mp.solutions.drawing_utils
        
        # 摄像头设置
        self.cap = self.find_camera()
        if self.cap is None:
            raise Exception("没有找到可用的摄像头！")
            
        print(f"准备发送数据到UE5: {ue5_ip}:{ue5_port}")
    
    def find_camera(self):
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"找到可用摄像头，索引: {i}")
                    return cap
                cap.release()
        return None
    
    def calculate_gesture_data(self, hand_landmarks):
        """计算手势相关数据"""
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append([lm.x, lm.y, lm.z])
        
        # 计算基本手势
        gesture_data = {
            "landmarks": landmarks,
            "thumb_up": self.is_thumb_up(landmarks),
            "fist": self.is_fist(landmarks),
            "open_hand": self.is_open_hand(landmarks),
            "pointing": self.is_pointing(landmarks),
            "peace": self.is_peace_sign(landmarks),
            "hand_rotation": self.calculate_hand_rotation(landmarks),
            "hand_center": self.calculate_hand_center(landmarks)
        }
        
        return gesture_data
    
    def is_thumb_up(self, landmarks):
        """检测大拇指向上手势"""
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        # 大拇指向上且其他手指弯曲
        thumb_up = thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]
        
        # 检查其他手指是否弯曲
        fingers_down = 0
        finger_tips = [8, 12, 16, 20]  # 食指、中指、无名指、小指指尖
        finger_pips = [6, 10, 14, 18]  # 对应的PIP关节
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip][1] > landmarks[pip][1]:  # 指尖在PIP关节下方表示弯曲
                fingers_down += 1
                
        return thumb_up and fingers_down >= 3
    
    def is_fist(self, landmarks):
        """检测握拳手势"""
        fingers_down = 0
        finger_tips = [4, 8, 12, 16, 20]  # 所有指尖
        finger_pips = [3, 6, 10, 14, 18]  # 对应关节
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip][1] > landmarks[pip][1]:
                fingers_down += 1
                
        return fingers_down >= 4
    
    def is_open_hand(self, landmarks):
        """检测张开手掌"""
        fingers_up = 0
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip][1] < landmarks[pip][1]:
                fingers_up += 1
                
        return fingers_up >= 4
    
    def is_pointing(self, landmarks):
        """检测指向手势（食指向上，其他手指弯曲）"""
        index_up = landmarks[8][1] < landmarks[6][1]
        other_fingers_down = 0
        
        other_tips = [4, 12, 16, 20]
        other_pips = [3, 10, 14, 18]
        
        for tip, pip in zip(other_tips, other_pips):
            if landmarks[tip][1] > landmarks[pip][1]:
                other_fingers_down += 1
                
        return index_up and other_fingers_down >= 3
    
    def is_peace_sign(self, landmarks):
        """检测V字手势（食指和中指向上）"""
        index_up = landmarks[8][1] < landmarks[6][1]
        middle_up = landmarks[12][1] < landmarks[10][1]
        
        other_fingers_down = 0
        other_tips = [4, 16, 20]
        other_pips = [3, 14, 18]
        
        for tip, pip in zip(other_tips, other_pips):
            if landmarks[tip][1] > landmarks[pip][1]:
                other_fingers_down += 1
                
        return index_up and middle_up and other_fingers_down >= 2
    
    def calculate_hand_rotation(self, landmarks):
        """计算手部旋转角度"""
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        
        dx = middle_mcp[0] - wrist[0]
        dy = middle_mcp[1] - wrist[1]
        
        angle = math.atan2(dy, dx) * 180 / math.pi
        return angle
    
    def calculate_hand_center(self, landmarks):
        """计算手部中心点"""
        center_x = sum([lm[0] for lm in landmarks]) / len(landmarks)
        center_y = sum([lm[1] for lm in landmarks]) / len(landmarks)
        center_z = sum([lm[2] for lm in landmarks]) / len(landmarks)
        
        return [center_x, center_y, center_z]
    
    def send_to_ue5(self, data):
        """发送数据到UE5"""
        try:
            json_data = json.dumps(data)
            self.sock.sendto(json_data.encode(), (self.ue5_ip, self.ue5_port))
        except Exception as e:
            print(f"发送数据失败: {e}")
    
    def run(self):
        """主运行循环"""
        pTime = 0
        
        print("手势追踪启动！支持的手势：")
        print("- 大拇指向上：向前移动")
        print("- 握拳：停止")
        print("- 张开手掌：跳跃")
        print("- 指向：转向")
        print("- V字手势：特殊动作")
        print("按 'q' 键退出")
        
        while True:
            success, img = self.cap.read()
            
            if not success or img is None:
                continue
                
            img = cv2.flip(img, 1)
            h, w, c = img.shape
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(imgRGB)
            
            # 准备发送给UE5的数据
            ue5_data = {
                "timestamp": time.time(),
                "hands": []
            }
            
            if results.multi_hand_landmarks:
                for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # 计算手势数据
                    gesture_data = self.calculate_gesture_data(hand_landmarks)
                    
                    # 添加手部索引（左手/右手）
                    handedness = results.multi_handedness[i].classification[0].label
                    gesture_data["handedness"] = handedness
                    
                    ue5_data["hands"].append(gesture_data)
                    
                    # 绘制手部关键点
                    self.mpDraw.draw_landmarks(img, hand_landmarks, self.mpHands.HAND_CONNECTIONS)
                    
                    # 在屏幕上显示检测到的手势
                    self.draw_gesture_info(img, gesture_data, i)
            
            # 发送数据到UE5
            if ue5_data["hands"]:
                self.send_to_ue5(ue5_data)
            
            # 计算和显示FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime) if pTime != 0 else 0
            pTime = cTime
            
            cv2.putText(img, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, 'Hand Gesture Control for UE5', (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("Hand Gesture Control", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cleanup()
    
    def draw_gesture_info(self, img, gesture_data, hand_index):
        """在图像上绘制手势信息"""
        y_offset = 70 + hand_index * 120
        hand_label = f"{gesture_data['handedness']} Hand:"
        
        cv2.putText(img, hand_label, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        gestures = []
        if gesture_data["thumb_up"]:
            gestures.append("Thumb Up")
        if gesture_data["fist"]:
            gestures.append("Fist")
        if gesture_data["open_hand"]:
            gestures.append("Open Hand")
        if gesture_data["pointing"]:
            gestures.append("Pointing")
        if gesture_data["peace"]:
            gestures.append("Peace")
        
        gesture_text = ", ".join(gestures) if gestures else "No Gesture"
        cv2.putText(img, gesture_text, (10, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # 显示手部旋转角度
        rotation_text = f"Rotation: {int(gesture_data['hand_rotation'])}°"
        cv2.putText(img, rotation_text, (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
    
    def cleanup(self):
        """清理资源"""
        self.cap.release()
        cv2.destroyAllWindows()
        self.sock.close()
        print("程序已退出")

if __name__ == "__main__":
    try:
        hand_tracker = HandGestureToUE5()
        hand_tracker.run()
    except Exception as e:
        print(f"程序错误: {e}") 