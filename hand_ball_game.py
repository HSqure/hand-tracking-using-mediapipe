import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import math
import sys

class HandDetector:
    """手部检测器类，专门为游戏优化"""
    def __init__(self, detectionCon=0.7, trackCon=0.5):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # 只检测一只手，提高性能
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils

    def find_hands(self, img):
        """检测手部并返回关键点"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        
        hand_landmarks = []
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                lmList = []
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                hand_landmarks.append(lmList)
        return hand_landmarks

class Ball:
    """物理小球类"""
    def __init__(self, x, y, radius=20):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.vx = random.uniform(-3, 3)  # 水平速度
        self.vy = random.uniform(-8, -4)  # 垂直速度（向上抛出）
        self.gravity = 0.3  # 重力加速度
        self.bounce = 0.8   # 弹性系数
        self.friction = 0.99  # 空气阻力
        self.color = (255, 100, 100)  # 红色
        self.trail = []  # 轨迹记录
        
    def update(self, screen_width, screen_height):
        """更新球的物理状态"""
        # 记录轨迹
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 10:  # 保持轨迹长度
            self.trail.pop(0)
            
        # 应用重力
        self.vy += self.gravity
        
        # 应用空气阻力
        self.vx *= self.friction
        self.vy *= self.friction
        
        # 更新位置
        self.x += self.vx
        self.y += self.vy
        
        # 边界碰撞检测
        # 左右边界
        if self.x - self.radius <= 0 or self.x + self.radius >= screen_width:
            self.vx = -self.vx * self.bounce
            self.x = max(self.radius, min(screen_width - self.radius, self.x))
            
        # 上边界
        if self.y - self.radius <= 0:
            self.vy = -self.vy * self.bounce
            self.y = self.radius
            
        # 下边界（地面）
        if self.y + self.radius >= screen_height:
            self.vy = -self.vy * self.bounce
            self.y = screen_height - self.radius
            # 地面摩擦
            self.vx *= 0.9
            
    def draw(self, screen):
        """绘制球和轨迹"""
        # 绘制轨迹
        if len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                alpha = i / len(self.trail)
                color = (int(255 * alpha), int(100 * alpha), int(100 * alpha))
                pygame.draw.circle(screen, color, self.trail[i], max(1, int(self.radius * alpha * 0.5)))
        
        # 绘制主球
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)
        
    def distance_to(self, x, y):
        """计算到指定点的距离"""
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)

class HandBallGame:
    """手势控制抛接球游戏"""
    def __init__(self):
        # 初始化pygame
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("手势抛接球游戏 - 按ESC退出")
        self.clock = pygame.time.Clock()
        
        # 初始化摄像头（不修改分辨率）
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("错误：无法打开摄像头")
            sys.exit(1)
            
        # 获取摄像头原始分辨率
        self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"摄像头分辨率: {self.cam_width} x {self.cam_height}")
        
        # 初始化手部检测器
        self.hand_detector = HandDetector()
        
        # 游戏状态
        self.balls = []
        self.score = 0
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # 手部状态
        self.hand_pos = None
        self.prev_hand_pos = None
        self.hand_velocity = (0, 0)
        
        # 游戏参数
        self.catch_distance = 50  # 接球的有效距离
        self.throw_power_multiplier = 0.3  # 投掷力度倍数
        
        # 自动生成球的计时器
        self.ball_spawn_timer = 0
        self.ball_spawn_interval = 180  # 每3秒生成一个球（60FPS * 3）
        
    def spawn_ball(self, x=None, y=None):
        """生成新球"""
        if x is None:
            x = random.randint(50, self.screen_width - 50)
        if y is None:
            y = random.randint(50, 150)
        
        ball = Ball(x, y)
        self.balls.append(ball)
        
    def map_hand_to_screen(self, hand_x, hand_y):
        """将手部坐标映射到游戏屏幕坐标"""
        # 考虑到图像是翻转的
        screen_x = int((hand_x / self.cam_width) * self.screen_width)
        screen_y = int((hand_y / self.cam_height) * self.screen_height)
        return screen_x, screen_y
        
    def update_hand_tracking(self):
        """更新手部跟踪"""
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        frame = cv2.flip(frame, 1)  # 水平翻转
        hand_landmarks = self.hand_detector.find_hands(frame)
        
        self.prev_hand_pos = self.hand_pos
        
        if hand_landmarks:
            # 使用手掌中心（关键点9）
            palm_center = hand_landmarks[0][9]  # 手掌中心点
            self.hand_pos = self.map_hand_to_screen(palm_center[1], palm_center[2])
            
            # 计算手部速度
            if self.prev_hand_pos:
                self.hand_velocity = (
                    (self.hand_pos[0] - self.prev_hand_pos[0]) * self.throw_power_multiplier,
                    (self.hand_pos[1] - self.prev_hand_pos[1]) * self.throw_power_multiplier
                )
        else:
            self.hand_pos = None
            self.hand_velocity = (0, 0)
            
        return frame
        
    def check_ball_hand_interaction(self):
        """检查球与手的交互"""
        if not self.hand_pos:
            return
            
        for i, ball in enumerate(self.balls[:]):  # 使用切片避免修改列表时出错
            distance = ball.distance_to(self.hand_pos[0], self.hand_pos[1])
            
            # 接球
            if distance < self.catch_distance:
                # 如果手部有明显移动，就"抛出"球
                velocity_magnitude = math.sqrt(self.hand_velocity[0]**2 + self.hand_velocity[1]**2)
                if velocity_magnitude > 2:  # 最小投掷速度阈值
                    ball.vx = self.hand_velocity[0]
                    ball.vy = self.hand_velocity[1]
                    ball.color = (100, 255, 100)  # 变成绿色表示被抛出
                    self.score += 10
                else:
                    # 跟随手部移动
                    ball.x = self.hand_pos[0]
                    ball.y = self.hand_pos[1]
                    ball.vx *= 0.9  # 减缓速度
                    ball.vy *= 0.9
                    ball.color = (100, 100, 255)  # 蓝色表示被控制
                    
    def update_game(self):
        """更新游戏逻辑"""
        # 更新所有球的物理状态
        for ball in self.balls[:]:
            ball.update(self.screen_width, self.screen_height)
            
            # 移除离开屏幕太远的球
            if (ball.y > self.screen_height + 100 or 
                ball.x < -100 or ball.x > self.screen_width + 100):
                self.balls.remove(ball)
                
        # 检查球与手的交互
        self.check_ball_hand_interaction()
        
        # 自动生成球
        self.ball_spawn_timer += 1
        if self.ball_spawn_timer >= self.ball_spawn_interval:
            self.spawn_ball()
            self.ball_spawn_timer = 0
            
        # 限制球的数量
        if len(self.balls) > 8:
            self.balls.pop(0)  # 移除最老的球
            
    def draw_game(self):
        """绘制游戏画面"""
        # 清屏
        self.screen.fill((30, 30, 50))  # 深蓝色背景
        
        # 绘制所有球
        for ball in self.balls:
            ball.draw(self.screen)
            
        # 绘制手部位置
        if self.hand_pos:
            pygame.draw.circle(self.screen, (255, 255, 0), self.hand_pos, 25, 3)
            # 绘制速度向量
            if abs(self.hand_velocity[0]) > 1 or abs(self.hand_velocity[1]) > 1:
                end_pos = (
                    self.hand_pos[0] + int(self.hand_velocity[0] * 10),
                    self.hand_pos[1] + int(self.hand_velocity[1] * 10)
                )
                pygame.draw.line(self.screen, (255, 255, 0), self.hand_pos, end_pos, 3)
                
        # 绘制UI信息
        score_text = self.font.render(f"分数: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        balls_text = self.small_font.render(f"球数: {len(self.balls)}", True, (255, 255, 255))
        self.screen.blit(balls_text, (10, 50))
        
        # 绘制操作说明
        instruction_text = self.small_font.render("用手接球并快速移动来投掷!", True, (200, 200, 200))
        self.screen.blit(instruction_text, (10, self.screen_height - 60))
        
        exit_text = self.small_font.render("按ESC退出", True, (200, 200, 200))
        self.screen.blit(exit_text, (10, self.screen_height - 30))
        
        pygame.display.flip()
        
    def run(self):
        """运行游戏主循环"""
        print("游戏启动！用您的手来接球和投掷吧！")
        print("操作说明：")
        print("- 将手靠近球来接球")
        print("- 快速移动手来投掷球")
        print("- 按ESC退出游戏")
        
        # 生成初始的几个球
        for _ in range(3):
            self.spawn_ball()
            
        running = True
        while running:
            # 处理pygame事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        # 空格键手动生成球
                        self.spawn_ball()
                        
            # 更新手部跟踪
            frame = self.update_hand_tracking()
            
            # 更新游戏逻辑
            self.update_game()
            
            # 绘制游戏
            self.draw_game()
            
            # 显示摄像头画面（可选，用于调试）
            if frame is not None:
                cv2.imshow("Hand Tracking (按q关闭)", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            # 控制帧率
            self.clock.tick(60)  # 60 FPS
            
        self.cleanup()
        
    def cleanup(self):
        """清理资源"""
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        print(f"游戏结束！最终分数: {self.score}")

if __name__ == "__main__":
    try:
        game = HandBallGame()
        game.run()
    except KeyboardInterrupt:
        print("\n游戏被用户中断")
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc() 