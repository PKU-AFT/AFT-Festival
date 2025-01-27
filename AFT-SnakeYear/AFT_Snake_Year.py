import pygame
import math
import random
from typing import List, Tuple
import time
import re
import cv2
import numpy as np

# 初始化 Pygame
pygame.init()

# 设置窗口尺寸和标题
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("春节动画")

# 设置视频输出参数
FPS = 60
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('AFT.mp4', fourcc, FPS, (WINDOW_WIDTH, WINDOW_HEIGHT))

# 定义颜色常量
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
BLUE = (0, 123, 255)
RED_PKU = (140, 0, 0)

# 每组对联之间的等待时间（秒），数组长度应该比对联数量少1
GROUP_DELAYS = [
    6.2,  # 第1组到第2组之间等待3秒
    4.9,  # 第2组到第3组之间等待4秒
    5.4,  # 第3组到第4组之间等待2.5秒
    5.1,  # 第4组到第5组之间等待3.5秒
    5.86,  # 依此类推...
    3.57,
    4.32,
    5.17,
    3.88,
    1.51
]

# 加载并缩放 PKU logo
pku_logo = pygame.image.load("PKU.png")
logo_width = WINDOW_WIDTH // 2
logo_height = int(logo_width * pku_logo.get_height() / pku_logo.get_width())
pku_logo = pygame.transform.scale(pku_logo, (logo_width, logo_height))
pku_logo.set_alpha(50)
logo_x = (WINDOW_WIDTH - logo_width) // 2
logo_y = (WINDOW_HEIGHT - logo_height) // 2

# 清理文字函数：只保留汉字，去除所有标点符号
def clean_text(text):
    return re.sub(r'[^\u4e00-\u9fff]', '', text)

# 对联文字列表
couplets = [
    clean_text("金龙含珠辞旧岁，银蛇吐宝迎新春"),
    clean_text("花柳春风率，蛇年瑞气盈"),
    clean_text("岁去年来新换旧，龙潜蛇舞景成春"),
    clean_text("金蛇狂舞丰收岁，玉燕喜迎幸福春"),
    clean_text("金蛇披彩新春到，喜鹊登梅报福音"),
    clean_text("龙来蛇去迎古韵，莺歌燕语谱新章"),
    clean_text("金蛇献瑞开新景，玉宇迎春启福门"),
    clean_text("祥蛇迎春春正暖，紫气东来万象新"),
    clean_text("福蛇献宝财源广，吉运登门家业隆"),
    clean_text("龙去神威在，蛇来紫气生"),
    clean_text("灵蛇起舞惊天地，喜气临门庆丰年")
]

def get_aft_positions() -> List[List[Tuple[float, float]]]:
    """生成 AFT 字母的点阵位置，确保与最终显示的 AFT 完全对齐"""
    a_positions = []
    f_positions = []
    t_positions = []
    
    # A 的结构
    base_x = 0.24  # A 的中心位置
    a_width = 0.20  # A 的总宽度
    a_height = 0.4  # A 的高度
    
    # 生成 A 的左斜线
    for i in range(10):
        t = i / 9
        x = base_x - (a_width/2) * (1-t)
        y = 0.65 - a_height * t
        for offset in [-0.01, 0.01]:
            a_positions.append((x + offset, y))
    
    # 生成 A 的右斜线
    for i in range(10):
        t = i / 9
        x = base_x + (a_width/2) * (1-t)
        y = 0.65 - a_height * t
        for offset in [-0.01, 0.01]:
            a_positions.append((x + offset, y))
    
    # A 的横线
    for x in range(8):
        t = x / 7
        base = base_x - a_width/4
        a_positions.append((base + t * (a_width/2), 0.45+0.09))
        a_positions.append((base + t * (a_width/2), 0.47+0.09))

    # F 的结构
    f_x = 0.47  # F 的基准位置
    f_height = 0.4  # F 的高度
    
    # F 的竖线
    for i in range(12):
        t = i / 11
        y = 0.25 + t * f_height
        for offset in [-0.01, 0.01]:
            f_positions.append((f_x + offset, y))
    
    # F 的横线
    for i in range(8):
        t = i / 7
        x = f_x + t * 0.12
        f_positions.append((x+0.02, 0.25))
        f_positions.append((x+0.02, 0.27))
        f_positions.append((x, 0.45))
        f_positions.append((x, 0.47))

    # T 的结构
    t_x = 0.79  # T 的中心位置
    t_width = 0.15  # T 的宽度
    
    # T 的顶横
    for i in range(10):
        t = i / 9
        x = t_x - t_width/2 + t * t_width
        for offset in [0, 0.02]:
            t_positions.append((x, 0.25 + offset))
    
    # T 的竖线
    for i in range(12):
        t = i / 11
        y = 0.25 + t * f_height
        for offset in [-0.01, 0.01]:
            t_positions.append((t_x + offset, y))

    return [a_positions, f_positions, t_positions]

class Character:
    """表示一个汉字的类，包含其显示状态和动画效果"""
    def __init__(self, text: str, letter_positions: List[List[Tuple[float, float]]], existing_chars: List['Character']):
        self.text = text
        self.existing_chars = existing_chars
        
        # 尝试找到一个不重叠的位置
        self.find_valid_position(letter_positions)
        
        # 动画参数
        self.state = "falling"  # falling 或 final
        self.speed = random.uniform(0.1, 0.2)
        self.rotation = random.uniform(-180, 180)
        self.scale = 1.0
        self.start_delay = random.uniform(0, 0.5)
        self.delay_counter = 0
        
    def find_valid_position(self, letter_positions):
        max_attempts = 50
        min_distance = 24  # 最小字符间距
        
        for _ in range(max_attempts):
            letter_index = random.randint(0, 2)
            positions = letter_positions[letter_index]
            target_pos = random.choice(positions)
            
            test_x = target_pos[0] * WINDOW_WIDTH
            test_y = target_pos[1] * WINDOW_HEIGHT
            
            valid_position = True
            for other_char in self.existing_chars:
                dist = math.sqrt((test_x - other_char.target_x)**2 + 
                               (test_y - other_char.target_y)**2)
                if dist < min_distance:
                    valid_position = False
                    break
            
            if valid_position:
                self.x = random.uniform(0.2, 0.8) * WINDOW_WIDTH
                self.y = -30
                self.target_x = test_x
                self.target_y = test_y
                return
        
        self.x = random.uniform(0.2, 0.8) * WINDOW_WIDTH
        self.y = -30
        self.target_x = test_x
        self.target_y = test_y
        
    def update(self):
        if self.delay_counter < self.start_delay:
            self.delay_counter += 0.016
            return
            
        if self.state == "falling":
            self.x += (self.target_x - self.x) * self.speed
            self.y += (self.target_y - self.y) * self.speed
            self.rotation *= 0.95
            
            if (abs(self.x - self.target_x) < 1 and 
                abs(self.y - self.target_y) < 1):
                self.state = "final"
                self.rotation = 0
        
    def draw(self, screen):
        try:
            font = pygame.font.Font('simkaibold.ttf', 24)
            text_surface = font.render(self.text, True, GOLD)
            rotated_text = pygame.transform.rotate(text_surface, self.rotation)
            screen.blit(rotated_text, (
                self.x - rotated_text.get_width()/2,
                self.y - rotated_text.get_height()/2
            ))
        except:
            pass

def main():
    letter_positions = get_aft_positions()
    all_characters = []
    current_group_index = 0
    active_characters = []
    frame_count = 0

    # 添加初始等待时间控制（5秒）
    initial_delay = 20.0
    animation_started = False
    
    # 记录时间和状态
    last_group_time = time.time()
    start_time = time.time()
    current_group_settled = False
    
    # 过渡动画控制
    transition_start = False
    transition_alpha = 0
    
    # 为每个对联创建字符组
    for couplet in couplets:
        couplet_chars = []
        existing_chars = [char for group in all_characters for char in group]
        for char in couplet:
            char_obj = Character(char, letter_positions, existing_chars)
            couplet_chars.append(char_obj)
            existing_chars.append(char_obj)
        all_characters.append(couplet_chars)

    # 创建渲染表面
    final_aft_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    glow_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    font = pygame.font.Font(None, 720)

    def render_metallic_aft():
        """渲染带有金属立体质感的 AFT"""
        final_aft_surface.fill((0, 0, 0, 0))
        glow_surface.fill((0, 0, 0, 0))
        
        # 定义金属效果的颜色层次
        metallic_colors = [
            (255, 215, 0),    # 标准金色
            (255, 200, 0),    # 深金色
            (255, 230, 150),  # 浅金色
            (255, 180, 0),    # 暗金色
            (255, 240, 180)   # 高光色
        ]
        
        # 渲染主体金属效果
        for i in range(10):
            depth_offset = i * 1.5  # 控制立体深度
            # 计算颜色渐变
            color_index = min(i // 2, len(metallic_colors) - 1)
            base_color = metallic_colors[color_index]
            alpha = 255 - i * 20
            if alpha < 0: alpha = 0
            
            # 渲染主文字
            color = (*base_color, alpha)
            text_surface = font.render("AFT", True, color)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + depth_offset))
            
            # 添加立体阴影
            shadow_color = (max(base_color[0]-40, 0), 
                          max(base_color[1]-40, 0), 
                          max(base_color[2]-40, 0), 
                          alpha)
            shadow_surface = font.render("AFT", True, shadow_color)
            shadow_rect = shadow_surface.get_rect(
                center=(WINDOW_WIDTH/2 + depth_offset/2, WINDOW_HEIGHT/2 + depth_offset)
            )
            
            # 组合效果
            glow_surface.blit(shadow_surface, shadow_rect)
            final_aft_surface.blit(text_surface, text_rect)
        
        # 添加高光效果
        for i in range(3):
            highlight_color = (255, 255, 220, 50)
            highlight_surface = font.render("AFT", True, highlight_color)
            highlight_rect = highlight_surface.get_rect(
                center=(WINDOW_WIDTH/2 - 3 + i, WINDOW_HEIGHT/2 - 3 + i)
            )
            final_aft_surface.blit(highlight_surface, highlight_rect)
        
        # 添加边缘光晕
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x_offset = math.cos(rad) * 4
            y_offset = math.sin(rad) * 4
            edge_color = (255, 215, 0, 30)
            edge_surface = font.render("AFT", True, edge_color)
            edge_rect = edge_surface.get_rect(
                center=(WINDOW_WIDTH/2 + x_offset, WINDOW_HEIGHT/2 + y_offset)
            )
            glow_surface.blit(edge_surface, edge_rect)
        
        final_aft_surface.blit(glow_surface, (0, 0))

    running = True
    show_final = False
    final_frame_count = 0
    clock = pygame.time.Clock()
    
    while running:
        current_time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 绘制背景色
        screen.fill(RED_PKU)
        
        # 绘制 PKU logo 在背景上
        screen.blit(pku_logo, (logo_x, logo_y))
        
        # 检查是否已经过了初始等待时间
        if not animation_started:
            if current_time - start_time >= initial_delay:
                animation_started = True
                last_group_time = current_time  # 重置计时器
        
        # 检查是否所有字符都已就位
        all_chars_in_position = (current_group_index == len(all_characters) and
                               all(char.state == "final" for group in all_characters 
                                   for char in group))
        
        # 开始渐变过渡
        if all_chars_in_position and current_time - start_time > (15 + initial_delay):
            transition_start = True
        
        if not show_final and animation_started:  # 只有在等待时间结束后才开始动画
            # 检查当前组是否已经全部就位
            if active_characters and all(char.state == "final" for char in active_characters):
                if not current_group_settled:
                    current_group_settled = True
                    last_group_time = current_time

            # 检查是否可以开始下一组
            if (not active_characters or current_group_settled) and current_group_index < len(all_characters):
                # 获取应该等待的时间（第一组不等待）
                wait_time = 0 if current_group_index == 0 else GROUP_DELAYS[current_group_index - 1]
                
                # 如果等待时间已到，开始下一组
                if current_time - last_group_time >= wait_time:
                    active_characters = all_characters[current_group_index]
                    current_group_index += 1
                    current_group_settled = False

            # 绘制所有字符
            char_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            for group in all_characters[:current_group_index]:
                for char in group:
                    char.update()
                    char.draw(char_surface)

            # 渐变效果处理
            if transition_start:
                transition_alpha = min(transition_alpha + 2, 255)
                screen.blit(char_surface, (0, 0))
                
                render_metallic_aft()
                temp_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                temp_surface.blit(final_aft_surface, (0, 0))
                temp_surface.set_alpha(transition_alpha)
                screen.blit(temp_surface, (0, 0))
                
                if transition_alpha >= 255:
                    show_final = True
            else:
                screen.blit(char_surface, (0, 0))
        
        # 显示最终的金属效果 AFT
        if show_final:
            render_metallic_aft()
            screen.blit(final_aft_surface, (0, 0))
            final_frame_count += 1
            if final_frame_count >= FPS * 3:  # 在最终状态保持3秒
                break
        
        # 更新显示
        pygame.display.flip()
        
        # 将当前帧转换为视频帧并写入
        frame_data = pygame.surfarray.array3d(screen)
        frame_data = frame_data.transpose([1, 0, 2])
        frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)
        out.write(frame_data)
        
        frame_count += 1
        clock.tick(FPS)  # 控制帧率

    # 清理资源
    out.release()
    pygame.quit()

if __name__ == "__main__":
    main()
        