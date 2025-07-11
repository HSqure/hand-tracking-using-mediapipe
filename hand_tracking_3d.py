import cv2
import mediapipe as mp
import time

class HandDetector():
    """
    使用MediaPipe库查找用户的手。
    导出地标坐标，并可以判断哪些手指是伸出的。
    """
    def __init__(self, mode=False, maxHands=2, model_complexity=1, detectionCon=0.5, trackCon=0.5):
        """
        初始化HandDetector。
        :param mode: 是否为静态图像模式。
        :param maxHands: 最多检测几只手。
        :param model_complexity: 地标模型的复杂度 (0或1)。
        :param detectionCon: 最小检测置信度。
        :param trackCon: 最小跟踪置信度。
        """
        self.mode = mode
        self.maxHands = maxHands
        self.model_complexity = model_complexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands # type: ignore
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.model_complexity, self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils # type: ignore

        # 马卡龙配色 (BGR)
        macaron_pink = (203, 192, 255)
        macaron_green = (192, 255, 192)
        self.landmark_drawing_spec = self.mpDraw.DrawingSpec(color=macaron_pink, thickness=2, circle_radius=2)
        self.connection_drawing_spec = self.mpDraw.DrawingSpec(color=macaron_green, thickness=2)
        
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []
        self.handedness = ""

    def findHands(self, img, draw=True):
        """
        从图像中检测手部，并绘制骨架。
        :param img: 要处理的图像。
        :param draw: 是否在图像上绘制关键点和连接线。
        :return: 处理后的图像。
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS,
                                               self.landmark_drawing_spec,
                                               self.connection_drawing_spec)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        """
        获取一只手上所有关键点的3D坐标。
        :param img: 要处理的图像。
        :param handNo: 手的编号 (0或1)。
        :param draw: 是否在关键点上绘制圆圈。
        :return: 返回一个列表，包含每个关键点的 [id, x, y, z]。
        """
        self.lmList = []
        if self.results.multi_hand_landmarks:
            # 只处理指定的一只手
            if len(self.results.multi_hand_landmarks) > handNo:
                myHand = self.results.multi_hand_landmarks[handNo]
                # 获取手的左右信息
                hand_info = self.results.multi_handedness[handNo]
                self.handedness = hand_info.classification[0].label

                for id, lm in enumerate(myHand.landmark):
                    h, w, c = img.shape
                    # 获取x,y,z坐标
                    cx, cy, cz = int(lm.x * w), int(lm.y * h), lm.z
                    self.lmList.append([id, cx, cy, cz])
                    if draw:
                        # 马卡龙粉色
                        cv2.circle(img, (cx, cy), 5, (203, 192, 255), cv2.FILLED)
        return self.lmList

    def fingersUp(self):
        """
        判断哪些手指是伸出的。
        :return: 一个包含5个元素的列表 (0或1)，1代表手指伸出。
        """
        fingers = []
        if not self.lmList:
            return []

        # 大拇指: 比较指尖和下一个关节的x坐标。
        # 需要根据左右手来判断。图像是翻转的，所以逻辑也要跟着变。
        # 右手：大拇指在左边。伸开时，指尖x坐标 < 关节x坐标。
        # 左手：大拇指在右边。伸开时，指尖x坐标 > 关节x坐标。
        if self.handedness == "Right":
            if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else: # Left Hand
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # 其他四个手指: 比较指尖和下面关节的y坐标。
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

def main():
    pTime = 0
    cap = cv2.VideoCapture(0)
    # 增加分辨率以提高精度
    # cap.set(3, 1280)
    # cap.set(4, 720)
    detector = HandDetector(detectionCon=0.75, maxHands=1) # 为了简化，先只处理一只手

    # 马卡龙配色 (BGR)
    macaron_bg = (221, 255, 221)  # 背景框: 淡绿
    macaron_text = (255, 204, 204) # 文字: 淡蓝
    macaron_info = (221, 160, 221) # 信息: 淡紫

    while True:
        success, img = cap.read()
        if not success:
            continue
        
        img = cv2.flip(img, 1) # 翻转图像，符合直觉
        
        # 1. 检测手并绘制
        img = detector.findHands(img)
        
        # 2. 获取关键点位置信息
        lmList = detector.findPosition(img, handNo=0, draw=False) # handNo=0 代表第一只检测到的手

        if lmList:
            # 3. 判断手指是否伸出
            fingers = detector.fingersUp()
            totalFingers = fingers.count(1)
            
            # 打印Z坐标以供观察
            # print(f"Wrist Z: {lmList[0][3]:.2f}, Index Tip Z: {lmList[8][3]:.2f}")

            # 4. 在屏幕上显示结果
            cv2.rectangle(img, (20, 20), (120, 120), macaron_bg, cv2.FILLED)
            cv2.putText(img, str(totalFingers), (45, 100), cv2.FONT_HERSHEY_PLAIN,
                        5, macaron_text, 5)
            
            # 在右上角显示指尖的Z坐标
            h, w, c = img.shape
            finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
            font_face = cv2.FONT_HERSHEY_PLAIN
            font_scale = 1.2
            font_thickness = 1
            text_color = (255, 255, 255)  # 白色
            bg_color = (0, 0, 0)          # 黑色

            y_pos = 20  # y轴起始位置
            for i, tip_id in enumerate(detector.tipIds):
                if len(lmList) > tip_id:
                    z_val = lmList[tip_id][3]
                    text = f"{finger_names[i]}: {z_val:.2f}"
                    
                    (text_w, text_h), baseline = cv2.getTextSize(text, font_face, font_scale, font_thickness)
                    
                    # 绘制背景
                    cv2.rectangle(img, (w - text_w - 25, y_pos), (w - 10, y_pos + text_h + baseline), bg_color, cv2.FILLED)
                    # 绘制文字
                    cv2.putText(img, text, (w - text_w - 20, y_pos + text_h), font_face, font_scale, text_color, font_thickness)
                    
                    y_pos += text_h + baseline + 10 # 移动到下一行

        # 计算并显示FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (10, 160), cv2.FONT_HERSHEY_PLAIN, 2, 
                    macaron_info, 2)

        # 显示图像
        cv2.imshow("3D Hand Tracking", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 