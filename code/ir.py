import numpy as np
from typing import List, Tuple

class VPL:
    def __init__(self, position, normal, intensity):
        self.position = np.array(position)
        self.normal = np.array(normal)
        self.intensity = np.array(intensity)

class InstantRadiosity:
    def __init__(self, scene, num_vpls=256):
        self.scene = scene
        self.num_vpls = num_vpls
        self.vpls = []
    
    def halton(self, index, base):
        """Halton序列生成"""
        result = 0.0
        f = 1.0 / base
        i = index
        while i > 0:
            result += f * (i % base)
            i //= base
            f /= base
        return result
    
    def sample_hemisphere_cosine(self, u1, u2):
        """余弦加权半球采样"""
        r = np.sqrt(u1)
        theta = 2 * np.pi * u2
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = np.sqrt(max(0, 1 - u1))
        return np.array([x, y, z])
    
    def generate_vpls(self):
        """阶段1：生成VPLs"""
        self.vpls = []
        
        for i in range(self.num_vpls):
            # 使用Halton序列采样
            u1 = self.halton(i, 2)
            u2 = self.halton(i, 3)
            
            # 在光源上采样起点
            light_point, light_normal, light_power = \
                self.scene.sample_light(u1, u2)
            
            # 追踪光子路径
            position = light_point
            power = light_power / self.num_vpls
            
            # 多次反弹
            for bounce in range(5):  # 最多5次反弹
                # 采样方向
                u3 = self.halton(i * 10 + bounce, 5)
                u4 = self.halton(i * 10 + bounce, 7)
                
                # 局部坐标系中的方向
                local_dir = self.sample_hemisphere_cosine(u3, u4)
                
                # 转换到世界坐标
                normal = self.scene.get_normal(position)
                direction = self.local_to_world(local_dir, normal)
                
                # 光线求交
                hit = self.scene.intersect(position, direction)
                
                if not hit:
                    break
                
                # 存储VPL
                albedo = self.scene.get_albedo(hit.position)
                vpl_intensity = power * albedo
                
                vpl = VPL(
                    position=hit.position,
                    normal=hit.normal,
                    intensity=vpl_intensity
                )
                self.vpls.append(vpl)
                
                # 更新路径
                position = hit.position
                power *= albedo
                
                # 俄罗斯轮盘赌终止
                continue_prob = np.mean(albedo)
                if np.random.random() > continue_prob:
                    break
                power /= continue_prob
    
    def render_pixel(self, camera_ray):
        """阶段2：渲染单个像素"""
        # 求交
        hit = self.scene.intersect(
            camera_ray.origin, 
            camera_ray.direction
        )
        
        if not hit:
            return np.array([0, 0, 0])
        
        color = np.array([0.0, 0.0, 0.0])
        
        # 直接光照
        color += self.compute_direct_lighting(hit)
        
        # VPL贡献
        for vpl in self.vpls:
            color += self.compute_vpl_contribution(hit, vpl)
        
        return color
    
    def compute_vpl_contribution(self, hit, vpl):
        """计算单个VPL的贡献"""
        # 方向和距离
        to_vpl = vpl.position - hit.position
        distance = np.linalg.norm(to_vpl)
        direction = to_vpl / distance
        
        # 可见性测试
        if not self.scene.is_visible(hit.position, vpl.position):
            return np.array([0, 0, 0])
        
        # 几何项
        cos_hit = max(0, np.dot(hit.normal, direction))
        cos_vpl = max(0, np.dot(vpl.normal, -direction))
        
        # 距离衰减（带奇点处理）
        distance_sq = max(distance * distance, 0.01)  # 避免除零
        
        # BRDF (Lambertian)
        albedo = self.scene.get_albedo(hit.position)
        brdf = albedo / np.pi
        
        # 最终贡献
        contribution = (vpl.intensity * brdf * cos_hit * cos_vpl) / distance_sq
        
        # Clamping避免fireflies
        max_contribution = 10.0
        contribution = np.minimum(contribution, max_contribution)
        
        return contribution
    
    def render(self, camera, width, height):
        """完整渲染"""
        # 生成VPLs
        print("Generating VPLs...")
        self.generate_vpls()
        print(f"Generated {len(self.vpls)} VPLs")
        
        # 渲染图像
        image = np.zeros((height, width, 3))
        
        for y in range(height):
            for x in range(width):
                # Hammersley序列用于抗锯齿
                samples_per_pixel = 4
                pixel_color = np.array([0.0, 0.0, 0.0])
                
                for s in range(samples_per_pixel):
                    u = self.halton(s, 2)
                    v = self.halton(s, 3)
                    
                    # 生成光线
                    ray = camera.generate_ray(
                        x + u, 
                        y + v, 
                        width, 
                        height
                    )
                    
                    # 渲染像素
                    pixel_color += self.render_pixel(ray)
                
                image[y, x] = pixel_color / samples_per_pixel
        
        return image