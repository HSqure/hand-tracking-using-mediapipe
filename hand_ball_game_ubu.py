import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import math
import sys

# 定义手部骨骼连接
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),  # 食指
    (5, 9), (9, 10), (10, 11), (11, 12), # 中指
    (9, 13), (13, 14), (14, 15), (15, 16), # 无名指
    (13, 17), (17, 18), (18, 19), (19, 20), # 小指
    (0, 17) # 手掌连接
]

class HandDetector:
    """手部检测器类，专门为游戏优化"""
    def __init__(self, detectionCon=0.8, trackCon=0.7):
        self.mpHands = mp.solutions.hands # type: ignore
        self.hands = self.mpHands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils # type: ignore

    def find_hands(self, img):
        """检测手部并返回3D关键点和左右手信息"""
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        
        hand_info = []
        if self.results.multi_hand_landmarks and self.results.multi_handedness:
            for hand_idx, handLms in enumerate(self.results.multi_hand_landmarks):
                handedness = self.results.multi_handedness[hand_idx].classification[0].label
                lmList = []
                for id, lm in enumerate(handLms.landmark):
                    # 返回归一化的坐标
                    lmList.append((lm.x, lm.y, lm.z))
                hand_info.append({"landmarks": lmList, "handedness": handedness})
        return hand_info

class Ball:
    """3D物理小球类"""
    def __init__(self, x, y, z=0, radius=20):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.radius = radius
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-8, -4)
        self.vz = random.uniform(-2, 2)
        self.gravity = 0.3
        self.bounce = 0.8
        self.friction = 0.99
        self.color = (255, 100, 100)
        self.trail = []
        self.focal_length = 500  # 虚拟摄像机焦距

    def update(self, screen_width, screen_height, depth_far=800, depth_near_scale=0.8):
        """更新球的物理状态"""
        self.trail.append((self.x, self.y, self.z))
        if len(self.trail) > 15:
            self.trail.pop(0)

        self.vy += self.gravity
        self.vx *= self.friction
        self.vy *= self.friction
        self.vz *= self.friction

        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        if self.x - self.radius <= 0 or self.x + self.radius >= screen_width:
            self.vx = -self.vx * self.bounce
            self.x = np.clip(self.x, self.radius, screen_width - self.radius)
        if self.y - self.radius <= 0:
            self.vy = -self.vy * self.bounce
            self.y = self.radius
        if self.y + self.radius >= screen_height:
            self.vy = -self.vy * self.bounce
            self.y = screen_height - self.radius
            self.vx *= 0.9

        depth_near = -self.focal_length * depth_near_scale
        if self.z < depth_near or self.z > depth_far:
            self.vz = -self.vz * self.bounce
            self.z = np.clip(self.z, depth_near, depth_far)

    def get_projection(self, screen_width, screen_height):
        """计算3D到2D的投影"""
        scale = self.focal_length / (self.focal_length + self.z)
        if scale <= 0:
            return None, None, None
        
        screen_x = int((self.x - screen_width / 2) * scale + screen_width / 2)
        screen_y = int((self.y - screen_height / 2) * scale + screen_height / 2)
        screen_radius = int(self.radius * scale)
        return screen_x, screen_y, screen_radius

    def draw(self, screen):
        """绘制球和轨迹"""
        screen_width, screen_height = screen.get_size()
        projection = self.get_projection(screen_width, screen_height)

        # 检查投影结果是否有效，如果无效则不进行任何绘制
        if projection[0] is None:
            return
        
        screen_x, screen_y, screen_radius = projection

        if screen_radius < 1:
            return

        for i in range(len(self.trail) - 1):
            p1_x, p1_y, p1_z = self.trail[i]
            p2_x, p2_y, p2_z = self.trail[i+1]

            scale1 = self.focal_length / (self.focal_length + p1_z)
            scale2 = self.focal_length / (self.focal_length + p2_z)

            if scale1 > 0 and scale2 > 0:
                s1_x = int((p1_x - screen_width / 2) * scale1 + screen_width / 2)
                s1_y = int((p1_y - screen_height / 2) * scale1 + screen_height / 2)
                s2_x = int((p2_x - screen_width / 2) * scale2 + screen_width / 2)
                s2_y = int((p2_y - screen_height / 2) * scale2 + screen_height / 2)
                
                alpha = (i / len(self.trail)) * 0.8
                color = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
                pygame.draw.line(screen, color, (s1_x, s1_y), (s2_x, s2_y), max(1, int(screen_radius * alpha * 0.5)))
        
        brightness = max(0, min(255, int(255 * (1 - self.z / (self.focal_length * 2)))))
        draw_color = tuple(np.clip([c * brightness / 255 for c in self.color], 0, 255))

        pygame.draw.circle(screen, draw_color, (screen_x, screen_y), screen_radius)
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), screen_radius, 2)

    def distance_to(self, x, y, z):
        """计算到指定点的3D距离"""
        return math.sqrt((self.x - x)**2 + (self.y - y)**2 + (self.z - z)**2)

class HandBallGame:
    """手势控制3D抛接球AR游戏"""
    def __init__(self):
        pygame.init()
        self.screen_width = 640
        self.screen_height = 480
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("3D手势抛接球 (AR) - 按ESC退出")
        self.clock = pygame.time.Clock()

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("错误：无法打开摄像头")
            sys.exit(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen_height)
        self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"请求摄像头分辨率: {self.screen_width}x{self.screen_height}, 实际: {self.cam_width}x{self.cam_height}")

        self.hand_detector = HandDetector()
        
        self.balls = []
        self.score = 0
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 30)
        
        self.hand_landmarks_3d = []
        self.hand_pos = None
        self.prev_hand_pos = None
        self.hand_velocity = (0, 0, 0)
        
        # 优化抓取和投掷机制
        self.raw_landmarks = []
        self.handedness = None
        self.is_pinching = False
        self.pinch_point = None
        self.prev_pinch_point = None
        self.pinch_velocity = np.array([0, 0, 0])
        self.grabbed_ball = None
        self.tipIds = [4, 8, 12, 16, 20] # 重新加入手指指尖ID
        self.PINCH_THRESHOLD = 35 # 捏合手势的距离阈值 (3D空间单位)

        self.catch_distance = 50 # 抓球/碰撞的有效距离
        self.throw_power_multiplier = 1.2 # 增强投掷力度
        
        self.ball_spawn_timer = 0
        self.ball_spawn_interval = 180
        
    def spawn_ball(self, x=None, y=None, z=None):
        """生成新球"""
        if x is None:
            x = random.randint(100, self.screen_width - 100)
        if y is None:
            y = random.randint(100, 200)
        if z is None:
            z = random.randint(0, 200)
        self.balls.append(Ball(x, y, z))
        
    def map_hand_to_screen(self, hx, hy, hz):
        """将手部归一化坐标映射到游戏3D空间坐标"""
        screen_x = int(hx * self.cam_width)
        screen_y = int(hy * self.cam_height)
        # 将z坐标缩放，使其在游戏世界中有意义
        screen_z = int(hz * self.cam_width * 0.8) 
        return screen_x, screen_y, screen_z
        
    def update_hand_tracking(self):
        """更新手部跟踪和手势状态"""
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        frame = cv2.flip(frame, 1)
        all_hands_info = self.hand_detector.find_hands(frame)
        
        self.prev_hand_pos = self.hand_pos
        self.hand_landmarks_3d = []
        
        # 更新捏合状态
        self.prev_pinch_point = self.pinch_point

        if all_hands_info:
            hand_info = all_hands_info[0] # 只处理第一只手
            self.raw_landmarks = hand_info['landmarks']
            self.handedness = hand_info['handedness']

            # 将归一化坐标转换为3D游戏世界坐标
            for hx, hy, hz in self.raw_landmarks:
                sx, sy, sz = self.map_hand_to_screen(hx, hy, hz)
                self.hand_landmarks_3d.append((sx, sy, sz))

            palm_center_3d = self.hand_landmarks_3d[9]
            self.hand_pos = palm_center_3d
            
            if self.prev_hand_pos:
                self.hand_velocity = (
                    (self.hand_pos[0] - self.prev_hand_pos[0]),
                    (self.hand_pos[1] - self.prev_hand_pos[1]),
                    (self.hand_pos[2] - self.prev_hand_pos[2])
                )
            
            # 更新捏合手势状态
            thumb_tip = np.array(self.hand_landmarks_3d[4])
            index_tip = np.array(self.hand_landmarks_3d[8])
            self.pinch_point = (thumb_tip + index_tip) / 2
            distance = np.linalg.norm(thumb_tip - index_tip)
            self.is_pinching = distance < self.PINCH_THRESHOLD

            # 计算捏合点的速度，用于投掷
            if self.prev_pinch_point is not None:
                self.pinch_velocity = (self.pinch_point - self.prev_pinch_point) * self.throw_power_multiplier

        else:
            self.hand_pos = None
            self.hand_velocity = (0, 0, 0)
            self.raw_landmarks = []
            self.handedness = None
            self.is_pinching = False
            self.pinch_point = None
            self.grabbed_ball = None # 手消失时，释放球
            
        return frame

    def fingersUp(self):
        """根据 self.raw_landmarks 判断手指是否伸出"""
        if not self.raw_landmarks or not self.handedness:
            return []
        
        fingers = []
        # 大拇指 (基于X坐标)
        if self.handedness == "Right":
            if self.raw_landmarks[self.tipIds[0]][0] < self.raw_landmarks[self.tipIds[0] - 1][0]:
                fingers.append(1)
            else:
                fingers.append(0)
        else: # Left Hand
            if self.raw_landmarks[self.tipIds[0]][0] > self.raw_landmarks[self.tipIds[0] - 1][0]:
                fingers.append(1)
            else:
                fingers.append(0)

        # 其他四个手指 (基于Y坐标)
        for id in range(1, 5):
            if self.raw_landmarks[self.tipIds[id]][1] < self.raw_landmarks[self.tipIds[id] - 2][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def get_bone_velocity(self, bone_id):
        """获取单根骨骼的平均速度"""
        # (此功能在更复杂的实现中会用到，暂时返回手掌的整体速度)
        return self.hand_velocity

    def check_ball_hand_interaction(self):
        """检查球与手的交互（抓取、投掷、碰撞）"""
        # 哨兵：如果手部数据不存在，则不进行任何交互检测
        if not self.hand_landmarks_3d:
            # 如果手消失时正抓着球，则释放球
            if self.grabbed_ball:
                self.grabbed_ball = None
            return

        # 1. 如果已经抓着球，处理持有或投掷
        if self.grabbed_ball:
            if self.is_pinching and self.pinch_point is not None:
                # 让球跟随捏合点
                self.grabbed_ball.x, self.grabbed_ball.y, self.grabbed_ball.z = self.pinch_point
                self.grabbed_ball.vx, self.grabbed_ball.vy, self.grabbed_ball.vz = 0, 0, 0
                self.grabbed_ball.color = (255, 255, 0) # 黄色代表被抓住
            else:
                # 手势变为非捏合，即为“投掷”，赋予小球捏合点的速度
                self.grabbed_ball.vx = self.pinch_velocity[0]
                self.grabbed_ball.vy = self.pinch_velocity[1]
                self.grabbed_ball.vz = self.pinch_velocity[2]
                self.grabbed_ball = None
            return # 只要处理了抓球/投掷，本帧就不再进行其他交互

        # 2. 如果没有抓球，则检测新的抓取或碰撞
        # 2a. 检测新的抓取
        if self.is_pinching and self.pinch_point is not None:
            for ball in self.balls:
                dist_to_pinch = ball.distance_to(*self.pinch_point)
                if dist_to_pinch < self.catch_distance:
                    self.grabbed_ball = ball
                    self.score += 5
                    return # 抓到球后，立即返回，避免同一帧内还进行碰撞检测

        # 2b. 如果没有发生抓取，则进行碰撞检测
        for ball in self.balls:
            min_dist = float('inf')
            collided_with_bone = None
            closest_point_on_bone = None
            ball_pos = np.array([ball.x, ball.y, ball.z])
            
            # 遍历所有骨骼，找到最近的碰撞点
            for p1_id, p2_id in HAND_CONNECTIONS:
                p1 = np.array(self.hand_landmarks_3d[p1_id])
                p2 = np.array(self.hand_landmarks_3d[p2_id])
                
                line_vec = p2 - p1
                point_vec = ball_pos - p1
                line_len_sq = np.dot(line_vec, line_vec)

                t = 0
                if line_len_sq > 0:
                    t = max(0, min(1, np.dot(point_vec, line_vec) / line_len_sq))
                
                closest_point_tmp = p1 + t * line_vec
                dist = np.linalg.norm(ball_pos - closest_point_tmp)

                if dist < min_dist:
                    min_dist = dist
                    collided_with_bone = (p1_id, p2_id)
                    closest_point_on_bone = closest_point_tmp

            # 3. 根据距离和手势决定行为
            if collided_with_bone and min_dist < ball.radius + self.catch_distance / 2:
                # A. 如果是抓取手势，则抓球
                # (由于抓取逻辑已前置，此处均为张开的手)
                bone_velocity = np.array(self.get_bone_velocity(collided_with_bone)) * self.throw_power_multiplier
                velocity_magnitude = np.linalg.norm(bone_velocity)
                
                if velocity_magnitude > 5:
                    normal = ball_pos - closest_point_on_bone
                    if np.linalg.norm(normal) > 0:
                        normal /= np.linalg.norm(normal)

                    impact_speed = np.dot(bone_velocity, normal)
                    
                    ball.vx = bone_velocity[0] + normal[0] * abs(impact_speed) * 0.8
                    ball.vy = bone_velocity[1] + normal[1] * abs(impact_speed) * 0.8
                    ball.vz = bone_velocity[2] + normal[2] * abs(impact_speed) * 0.8

                    ball.x += ball.vx
                    ball.y += ball.vy
                    ball.z += ball.vz

                    ball.color = (100, 255, 100)
                    self.score += 10
                else:
                    # 低速接触时轻微弹开，避免粘滞
                    ball.vx *= -0.3
                    ball.vy *= -0.3
                    ball.vz *= -0.3
            
    def update_game(self):
        """更新游戏逻辑"""
        for ball in self.balls[:]:
            ball.update(self.screen_width, self.screen_height)
            if (ball.y > self.screen_height + 200 or 
                ball.x < -200 or ball.x > self.screen_width + 200):
                self.balls.remove(ball)
                
        self.check_ball_hand_interaction()
        
        self.ball_spawn_timer += 1
        if self.ball_spawn_timer >= self.ball_spawn_interval:
            self.spawn_ball()
            self.ball_spawn_timer = 0
            
        if len(self.balls) > 8:
            self.balls.pop(0)
            
    def draw_game(self, frame):
        """绘制游戏画面 (AR)"""
        # 1. 绘制手部骨骼（直接在摄像头画面上绘制，确保对齐）
        if frame is not None and self.raw_landmarks:
            for p1_id, p2_id in HAND_CONNECTIONS:
                p1 = self.raw_landmarks[p1_id]
                p2 = self.raw_landmarks[p2_id]
                p1_px = (int(p1[0] * self.cam_width), int(p1[1] * self.cam_height))
                p2_px = (int(p2[0] * self.cam_width), int(p2[1] * self.cam_height))
                cv2.line(frame, p1_px, p2_px, (0, 255, 255), 2)
            for lm in self.raw_landmarks:
                p_px = (int(lm[0] * self.cam_width), int(lm[1] * self.cam_height))
                cv2.circle(frame, p_px, 3, (0, 255, 0), cv2.FILLED)

        # 2. 将摄像头画面转为Pygame表面并显示
        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))
            self.screen.blit(frame_surface, (0, 0))
        else:
            self.screen.fill((30, 30, 50))

        # 3. 绘制3D球体
        for ball in self.balls:
            ball.draw(self.screen)
            
        # 4. 绘制UI
        score_text = self.font.render(f"分数: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))
        
        balls_text = self.small_font.render(f"球数: {len(self.balls)}", True, (255, 255, 255))
        self.screen.blit(balls_text, (20, 80))
        
        # 显示抓取状态
        grab_text_str = "状态: 捏合" if self.is_pinching else "状态: 张开"
        grab_text_color = (255, 255, 0) if self.is_pinching else (255, 255, 255)
        grab_text = self.small_font.render(grab_text_str, True, grab_text_color)
        self.screen.blit(grab_text, (20, 110))
        
        instruction_text = self.small_font.render("捏合手指抓球, 松开投掷!", True, (200, 200, 200))
        text_rect = instruction_text.get_rect(centerx=self.screen_width/2, y=self.screen_height - 70)
        self.screen.blit(instruction_text, text_rect)
        
        exit_text = self.small_font.render("按ESC退出", True, (200, 200, 200))
        self.screen.blit(exit_text, (20, self.screen_height - 40))
        
        pygame.display.flip()
        
    def run(self):
        """运行游戏主循环"""
        print("3D AR 抛接球游戏已启动！")
        print("- 将手靠近球来接球")
        print("- 快速移动手来投掷球")
        print("- 按ESC退出游戏")
        
        for _ in range(3):
            self.spawn_ball()
            
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.spawn_ball()
                        
            frame = self.update_hand_tracking()
            self.update_game()
            self.draw_game(frame)
            
            # cv2.imshow已经被AR视图取代
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     running = False
                    
            self.clock.tick(60)
            
        self.cleanup()
        
    def cleanup(self):
        """清理资源"""
        print(f"游戏结束！最终分数: {self.score}")
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = HandBallGame()
        game.run()
    except (KeyboardInterrupt, SystemExit):
        print("\n游戏被用户关闭")
    except Exception as e:
        print(f"游戏运行出错: {e}")
        import traceback
        traceback.print_exc() 