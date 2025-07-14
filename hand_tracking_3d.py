import cv2
import mediapipe as mp
import time
import math
import pygame
import numpy as np

# --- 死亡搁浅风格辉光绘制函数 (优化版) ---
def draw_glowing_line(surface, color, start, end, thickness, glow_intensity=0.8):
    """
    绘制扁平化且带有辉光效果的线条。
    :param surface: 目标Pygame Surface (必须支持 per-pixel alpha)。
    :param color: 线条的RGB颜色。
    :param start: 起始点。
    :param end: 结束点。
    :param thickness: 核心线条粗细。
    :param glow_intensity: 辉光强度。
    """
    r, g, b = color
    
    # 外层辉光 (更粗、更透明)
    glow_alpha1 = int(60 * glow_intensity)
    pygame.draw.line(surface, (r, g, b, glow_alpha1), start, end, thickness * 4)
    
    # 内层核心 (较细、较不透明)
    glow_alpha2 = int(180 * glow_intensity)
    pygame.draw.line(surface, (r, g, b, glow_alpha2), start, end, thickness)

def draw_glowing_circle(surface, color, center, radius, core_alpha, glow_intensity=0.8):
    """
    绘制半透明且带有辉光效果的圆形。
    :param surface: 目标Pygame Surface (必须支持 per-pixel alpha)。
    :param color: 圆形的RGB颜色。
    :param center: 圆心。
    :param radius: 核心圆形的半径。
    :param core_alpha: 核心圆的alpha值 (0-255)。
    :param glow_intensity: 辉光强度。
    """
    r, g, b = color
    
    # 辉光层 (更大、更透明)
    glow_alpha = int(120 * glow_intensity)
    pygame.draw.circle(surface, (r, g, b, glow_alpha), center, radius + 4)
    
    # 核心半透明层
    pygame.draw.circle(surface, (r, g, b, core_alpha), center, radius)


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
        self.results = None

    def findHands(self, img, draw=True):
        """
        从图像中检测手部，并绘制骨架。
        :param img: 要处理的图像。
        :param draw: 是否在图像上绘制关键点和连接线。
        :return: 处理后的图像。
        """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results and self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
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
        if self.results and self.results.multi_hand_landmarks:
            # 只处理指定的一只手
            if len(self.results.multi_hand_landmarks) > handNo:
                myHand = self.results.multi_hand_landmarks[handNo]
                # 获取手的左右信息
                if self.results.multi_handedness:
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
    # --- Pygame 初始化 ---
    pygame.init()
    
    # --- 分辨率定义 ---
    CAM_W, CAM_H = 640, 480
    SIDEBAR_W = 320
    WINDOW_W, WINDOW_H = CAM_W + SIDEBAR_W, CAM_H
    
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    # 辉光渲染层
    glow_surface = pygame.Surface((CAM_W, CAM_H), pygame.SRCALPHA)
    pygame.display.set_caption("Death Stranding UI - Hand Tracking")
    
    # --- 字体 (优先使用更具科技感的字体) ---
    try:
        font_main = pygame.font.SysFont('bahnschrift', 22)
        font_title = pygame.font.SysFont('bahnschrift', 16)
        font_large = pygame.font.SysFont('impact', 80)
    except:
        font_main = pygame.font.SysFont('calibri', 22)
        font_title = pygame.font.SysFont('calibri', 16)
        font_large = pygame.font.SysFont('impact', 80)

    # --- 死亡搁浅风格颜色 ---
    C_BACKGROUND = (3, 10, 19)
    C_PANEL = (9, 21, 38)
    C_ACCENT = (110, 169, 255)   # 骨架线条颜色 (#6EA9FF)
    C_JOINT = (248, 63, 23)       # 关节点颜色 (#F83F17)
    C_TEXT = (210, 220, 230)
    C_TEXT_DIM = (100, 110, 120)
    C_BTN_EXIT = (19, 31, 48)
    C_BTN_EXIT_HOVER = (255, 70, 70)
    C_SEPARATOR = (35, 54, 69)      # 分割线颜色 (更暗)
    
    # --- OpenCV & MediaPipe 初始化 ---
    pTime = 0
    cap = cv2.VideoCapture(0)
    cap.set(3, CAM_W)
    cap.set(4, CAM_H)
    detector = HandDetector(detectionCon=0.75, maxHands=1)

    # --- 距离估算标定参数 ---
    D_REF_CM = 30.0
    PIX_DIST_REF = 150.0 

    # --- UI 布局计算 ---
    cam_area_rect = pygame.Rect(0, 0, CAM_W, CAM_H)
    sidebar_rect = pygame.Rect(CAM_W, 0, SIDEBAR_W, WINDOW_H)
    exit_btn_rect = pygame.Rect(sidebar_rect.left, WINDOW_H - 50, SIDEBAR_W, 50)

    running = True
    while running:
        # --- 事件处理 ---
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if exit_btn_rect.collidepoint(mouse_pos):
                    running = False
        
        # --- 获取图像 & 手部检测 ---
        success, img_bgr = cap.read()
        if not success: continue
        
        img_flipped = cv2.flip(img_bgr, 1)
        img_rgb = cv2.cvtColor(img_flipped, cv2.COLOR_BGR2RGB)
        
        img_rgb.flags.writeable = False
        detector.results = detector.hands.process(img_rgb)
        img_rgb.flags.writeable = True
        lmList = detector.findPosition(img_flipped, draw=False)
        
        img_pygame = pygame.image.frombuffer(img_rgb.tobytes(), (CAM_W, CAM_H), "RGB")

        # --- 核心绘制 ---
        screen.fill(C_BACKGROUND)
        screen.blit(img_pygame, (0, 0))
        
        # 清空辉光层
        glow_surface.fill((0, 0, 0, 0))

        # 初始化数据变量
        totalFingers, dist_cm = 0, 0

        if lmList:
            # --- 绘制辉光骨架 ---
            # 绘制骨骼连接
            for conn in detector.mpHands.HAND_CONNECTIONS:
                p1 = lmList[conn[0]]
                p2 = lmList[conn[1]]
                draw_glowing_line(glow_surface, C_ACCENT, (p1[1], p1[2]), (p2[1], p2[2]), 2)
                
            # 绘制关节点 (后画，覆盖在线条上)
            for point in lmList:
                draw_glowing_circle(glow_surface, C_JOINT, (point[1], point[2]), 6, core_alpha=190)


            # --- 功能计算 ---
            fingers = detector.fingersUp()
            totalFingers = fingers.count(1)
            x1, y1, x2, y2 = lmList[0][1], lmList[0][2], lmList[9][1], lmList[9][2]
            pixel_dist = math.hypot(x2 - x1, y2 - y1)
            if pixel_dist > 0: dist_cm = (PIX_DIST_REF * D_REF_CM) / pixel_dist

        # 将辉光层叠加到主屏幕
        screen.blit(glow_surface, (0, 0))

        # --- 侧边栏UI绘制 (V2 - 优化布局) ---
        pygame.draw.rect(screen, C_PANEL, sidebar_rect)
        y_pos = 40
        
        # 1. 标题
        pygame.draw.line(screen, C_ACCENT, (sidebar_rect.left + 20, y_pos), (sidebar_rect.left + 50, y_pos), 2)
        title = font_title.render("SYSTEM DETAILS", True, C_TEXT)
        screen.blit(title, (sidebar_rect.left + 60, y_pos - 10))
        y_pos += 40

        # 2. FPS (元数据)
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime
        label_fps = font_main.render(f"FPS: {int(fps)}", True, C_TEXT_DIM)
        screen.blit(label_fps, (sidebar_rect.left + 20, y_pos))
        y_pos += 40

        # 分割线
        pygame.draw.line(screen, C_SEPARATOR, (sidebar_rect.left + 20, y_pos), (sidebar_rect.right - 20, y_pos), 1)
        y_pos += 30

        # 3. 手指计数 (核心数据)
        label_fingers = font_main.render("Active Fingers", True, C_TEXT_DIM)
        screen.blit(label_fingers, (sidebar_rect.left + 20, y_pos))
        text_fingers = font_large.render(str(totalFingers), True, C_TEXT)
        screen.blit(text_fingers, (sidebar_rect.left + 15, y_pos + 25))
        y_pos += 150

        # 4. 距离 (核心数据)
        label_dist = font_main.render("Distance Estimate", True, C_TEXT_DIM)
        screen.blit(label_dist, (sidebar_rect.left + 20, y_pos))
        text_dist = font_large.render(f"{dist_cm:.0f}", True, C_TEXT)
        text_cm = font_main.render("cm", True, C_TEXT_DIM)
        screen.blit(text_dist, (sidebar_rect.left + 15, y_pos + 25))
        screen.blit(text_cm, (sidebar_rect.left + 25 + text_dist.get_width(), y_pos + 90))
        
        # 5. 退出按钮 (操作)
        btn_color = C_BTN_EXIT_HOVER if exit_btn_rect.collidepoint(mouse_pos) else C_BTN_EXIT
        pygame.draw.rect(screen, btn_color, exit_btn_rect)
        exit_text = font_main.render("EXIT", True, C_TEXT)
        exit_rect = exit_text.get_rect(center=exit_btn_rect.center)
        screen.blit(exit_text, exit_rect)
        
        pygame.display.flip()

    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()