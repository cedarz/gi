# 全局光照实践项目指南

从零开始，逐步实现完整的GI系统。每个项目包含目标、关键技术点和验证方法。

---

## 项目难度分级
- 🟢 **入门级** - 1-2周完成
- 🟡 **中级** - 3-4周完成  
- 🔴 **高级** - 4-8周完成
- ⚫ **挑战级** - 8周以上

---

## Phase 1: 离线渲染基础 (建议6-8周)

### 项目1.1: 简单光线追踪器 🟢
**预计时间**: 1-2周  
**技术栈**: C++/Rust/任意语言

**目标**:
- 实现基础光线-球体/平面求交
- 支持漫反射、镜面反射、折射材质
- 生成Cornell Box渲染图

**关键步骤**:
1. **光线生成**: 相机模型、视平面采样
2. **求交系统**: 
   - 球体求交
   - 平面/三角形求交
   - 场景管理（简单数组即可）
3. **材质系统**:
   - Lambertian diffuse
   - Perfect specular (镜面)
   - Dielectric (玻璃，Snell定律)
4. **光照计算**: 直接光照 + 递归反射/折射

**参考资源**:
- 📚 "Ray Tracing in One Weekend" - Peter Shirley
- 💻 [smallpt](http://www.kevinbeason.com/smallpt/) - 99行参考实现

**验证标准**:
- ✅ 能渲染经典Cornell Box
- ✅ 玻璃球正确折射
- ✅ 镜面球正确反射
- ✅ 软阴影（区域光源）

**扩展挑战**:
- 添加景深效果（光圈模拟）
- 支持三角网格模型（OBJ加载）
- 实现BVH加速结构

---

### 项目1.2: 路径追踪器 🟡
**预计时间**: 2-3周  
**基于**: 项目1.1

**目标**:
- 实现无偏路径追踪
- 支持多重重要性采样(MIS)
- 渲染复杂间接光照场景

**关键步骤**:
1. **蒙特卡洛积分**:
   - 半球均匀采样
   - Cosine加权采样
   - BRDF重要性采样
2. **路径追踪循环**:
   - 递归改迭代实现
   - 俄罗斯轮盘赌终止
   - 能量累积
3. **多重重要性采样**:
   - 光源采样
   - BRDF采样
   - Balance heuristic权重计算
4. **性能优化**:
   - BVH加速结构（SAH构建）
   - 多线程渲染

**参考资源**:
- 📚 PBRT Book - Chapter 13-14
- 📄 Veach Thesis - Chapter 9 (MIS)
- 💻 [PBRT-v3](https://github.com/mmp/pbrt-v3)

**验证标准**:
- ✅ 正确的间接光照（color bleeding）
- ✅ 焦散效果（通过玻璃的光斑）
- ✅ 收敛速度对比（有无MIS）
- ✅ 渲染Veach的MIS测试场景

**调试技巧**:
- 渲染单次反弹vs多次反弹对比
- 可视化采样方向分布
- 输出每像素样本数热力图

**扩展挑战**:
- 实现Microfacet BRDF (GGX)
- 支持环境贴图光照
- 实现次表面散射

---

### 项目1.3: 光子映射 🟡
**预计时间**: 3-4周  
**可独立或基于1.2**

**目标**:
- 实现经典光子映射
- 处理焦散和间接光照
- 理解有偏估计

**关键步骤**:
1. **光子发射**:
   - 光源采样
   - 光子追踪（与路径追踪反向）
   - 俄罗斯轮盘赌吸收
2. **光子存储**:
   - KD-Tree构建（3D点）
   - 光子数据结构（位置、方向、功率）
3. **光子收集**:
   - K近邻搜索
   - 核密度估计
   - Final gathering改进
4. **渲染整合**:
   - 直接光照用路径追踪
   - 间接光照用光子映射
   - 焦散单独一个光子图

**参考资源**:
- 📚 "Realistic Image Synthesis Using Photon Mapping" - Jensen
- 💻 [SmallPPM](https://github.com/xelatihy/smallppm)
- 📄 Jensen 1996论文

**验证标准**:
- ✅ 清晰的焦散效果（玻璃杯、钻石）
- ✅ 间接光照比路径追踪更快收敛（某些场景）
- ✅ 理解偏差产生原因

**经典测试场景**:
- 玻璃球焦散
- 水杯焦散
- Cornell Box间接光照

**扩展挑战**:
- 实现渐进式光子映射(PPM)
- 实现SPPM算法
- 对比光子密度与收敛质量

---

### 项目1.4: 双向路径追踪 🔴
**预计时间**: 4-6周  
**基于**: 项目1.2

**目标**:
- 实现BDPT算法
- 处理复杂光传输路径
- 深入理解MIS

**关键步骤**:
1. **路径构建**:
   - 从相机追踪子路径
   - 从光源追踪子路径
   - 路径顶点数据结构
2. **路径连接**:
   - 枚举所有连接策略 (s,t)
   - 可见性测试
   - 重要性评估
3. **MIS权重**:
   - 计算每个策略的PDF
   - Balance heuristic
   - Power heuristic
4. **特殊情况处理**:
   - s=0: 直接击中光源
   - t=0: 光源直接可见
   - s=1,t=1: 传统路径追踪

**参考资源**:
- 📄 Veach PhD Thesis - Chapter 10 ⭐核心
- 📚 PBRT Book - Chapter 16
- 💻 [Mitsuba 3](https://github.com/mitsuba-renderer/mitsuba3)

**验证标准**:
- ✅ 在"光传输困难场景"中优于PT
- ✅ Veach的门缝场景（light through door）
- ✅ 水下焦散 + 体积散射
- ✅ 对比每个(s,t)策略的贡献

**调试技巧**:
- 单独可视化每个(s,t)策略的结果
- 输出MIS权重分布
- 对比有无MIS的方差

**扩展挑战**:
- 实现VCM算法（结合光子映射）
- 实现Manifold Exploration（处理SDS路径）

---

## Phase 2: 实时GI基础 (建议4-6周)

### 项目2.1: 屏幕空间环境光遮蔽(SSAO) 🟢
**预计时间**: 1周  
**技术栈**: OpenGL/DirectX/Vulkan

**目标**:
- 实现标准SSAO
- 理解屏幕空间方法的优缺点

**关键步骤**:
1. **G-Buffer准备**:
   - 位置（或深度）
   - 法线
   - View-space数据
2. **SSAO Pass**:
   - 生成采样核（半球）
   - 随机旋转（噪声纹理）
   - 深度比较判断遮挡
3. **模糊Pass**:
   - 边缘保持模糊
   - 双边滤波
4. **组合Pass**:
   - AO应用到最终光照

**参考资源**:
- 📝 LearnOpenGL - SSAO教程
- 💻 [SSAO示例代码](https://learnopengl.com/Advanced-Lighting/SSAO)

**验证标准**:
- ✅ 角落和缝隙变暗
- ✅ 性能≥60fps (1080p)
- ✅ 无明显噪点（模糊后）

**优化挑战**:
- 实现HBAO (Horizon-Based AO)
- 实现GTAO (Ground Truth AO)
- 对比质量和性能

---

### 项目2.2: 屏幕空间反射(SSR) 🟡
**预计时间**: 2周  
**基于**: 项目2.1的G-Buffer

**目标**:
- 实现基础SSR
- 处理光线步进和衰减

**关键步骤**:
1. **反射光线生成**:
   - 从G-Buffer读取法线
   - 计算反射方向
   - View空间光线步进
2. **光线步进**:
   - 层次化深度缓冲（Hi-Z）
   - 深度比较判断相交
   - 二分查找精确交点
3. **边缘处理**:
   - 屏幕边界淡出
   - 基于距离/粗糙度淡出
4. **时域降噪**:
   - 历史帧重投影
   - 颜色clamping

**参考资源**:
- 📝 GPU Gems / GPU Pro相关章节
- 🎮 Unreal Engine SSR源码
- 📄 "Stochastic Screen Space Reflections" (SIGGRAPH 2015)

**验证标准**:
- ✅ 平滑表面正确反射
- ✅ 边缘淡出自然
- ✅ 性能≥60fps (1080p)

**已知限制**:
- ❌ 无法反射屏幕外物体
- ❌ 背面物体无法反射
- ❌ 粗糙表面反射困难

**扩展挑战**:
- 实现随机光线SSR（粗糙反射）
- 结合环境贴图fallback
- Contact-hardening反射

---

### 项目2.3: 反射阴影图(RSM) 🟢
**预计时间**: 1-2周  
**技术栈**: OpenGL/DirectX/Vulkan

**目标**:
- 实现基础RSM算法
- 理解VPL方法
- 为LPV打基础

**关键步骤**:
1. **RSM生成**:
   - 从主光源视角渲染场景
   - 生成包含位置、法线、通量(flux)的G-Buffer
   - 类似Shadow Map，但存储更多信息
2. **VPL采样**:
   - 每个像素从RSM中采样N个VPL（64-256个）
   - 重要性采样（基于距离、法线）
   - 计算每个VPL的贡献
3. **间接光照计算**:
   - 对每个VPL:
     - 计算到着色点的方向和距离
     - 评估BRDF（通常是Lambertian）
     - 应用距离衰减 (1/r²)
     - 考虑法线朝向
   - 累加所有VPL贡献
4. **降噪**:
   - 双边滤波减少噪声
   - 或使用简单高斯模糊

**参考资源**:
- 📄 Dachsbacher & Stamminger 2005论文
- 🎓 GAMES202 Lecture 6
- 💻 [RSM教程](https://github.com/search?q=reflective+shadow+maps)

**验证标准**:
- ✅ 明显的color bleeding效果
- ✅ 动态光源产生动态间接光
- ✅ 性能可实时（30fps+）

**已知限制**:
- ❌ 需要大量VPL采样（噪声vs性能）
- ❌ 只能看到光源可见的表面
- ❌ 单次反弹限制
- ❌ 背面物体无法接收间接光

**调试技巧**:
- 可视化RSM内容（位置、法线、flux）
- 渲染单个VPL的影响范围
- 输出采样的VPL位置
- 对比不同VPL数量的效果

**扩展挑战**:
- 实现Imperfect Shadow Maps (简化几何)
- 多次反弹（RSM递归）
- 自适应VPL采样密度
- Splatting方法（屏幕空间累积）

---

### 项目2.4: 光照传播体积(LPV) 🟡
**预计时间**: 3-4周  
**技术栈**: Compute Shader推荐

**目标**:
- 实现基础LPV系统
- 理解体素化GI方法

**关键步骤**:
1. **RSM生成**:
   - 从光源视角渲染场景
   - 存储位置、法线、flux
2. **注入Pass**:
   - 将RSM像素转为虚拟点光源
   - 注入到3D体素网格
   - SH系数存储方向信息
3. **传播Pass**:
   - 迭代4-6次
   - 6个方向传播（±X/Y/Z）
   - SH旋转和累加
4. **渲染Pass**:
   - 查询体素网格
   - 三线性插值
   - 应用间接光照

**参考资源**:
- 📄 Kaplanyan 2009论文
- 🎥 CryEngine GDC Talk
- 💻 社区LPV实现（GitHub搜索）

**验证标准**:
- ✅ 动态物体产生间接光照
- ✅ Color bleeding效果
- ✅ 实时性能（可动态更新）

**已知问题与改进**:
- 光泄漏问题（几何遮挡）
- 级联LPV处理大场景
- 几何体积注入改进精度

---

### 项目2.5: 体素锥追踪(VCT) 🔴
**预计时间**: 4-6周  
**技术栈**: OpenGL 4.5+/Vulkan (需要图像原子操作)

**目标**:
- 实现SVO体素化
- 实现锥形追踪
- 处理动态场景

**关键步骤**:
1. **体素化**:
   - 使用保守光栅化
   - 原子操作写入3D纹理
   - 生成稀疏体素八叉树(SVO)
2. **各向异性体素Mipmap**:
   - 6个方向的Mipmap（±X/Y/Z）
   - 硬件Mipmap或手动生成
3. **锥形追踪**:
   - 漫反射：5-6个锥
   - 镜面反射：1个锥（基于粗糙度）
   - 遮挡锥（AO）
   - 步进 + Mipmap采样
4. **动态更新**:
   - 每帧重新体素化
   - 或标记脏区域增量更新

**参考资源**:
- 📄 Crassin 2011核心论文 ⭐
- 💻 [VoxelConeTracing GitHub](https://github.com/Friduric/voxel-cone-tracing)
- 📄 "Octree-Based Sparse Voxelization" (Crassin)

**验证标准**:
- ✅ 高质量间接光照（类似离线）
- ✅ 光泽反射（基于粗糙度）
- ✅ 动态物体正确交互
- ✅ 性能30-60fps (中等场景)

**关键挑战**:
- 内存管理（SVO可能很大）
- 体素分辨率 vs 性能权衡
- 减少光泄漏

**优化方向**:
- 使用体素片段列表（Voxel Fragment List）
- GPU驱动的SVO构建
- 时域抗闪烁

---

## Phase 3: 硬件光线追踪 (建议6-8周)

### 项目3.1: DXR/VkRT入门 🟡
**预计时间**: 2-3周  
**技术栈**: DXR (DirectX 12)或Vulkan Ray Tracing

**目标**:
- 配置光追管线
- 实现基础路径追踪

**关键步骤**:
1. **加速结构**:
   - BLAS (Bottom-Level)：几何体
   - TLAS (Top-Level)：实例
   - 构建和更新
2. **Shader配置**:
   - Ray Generation Shader
   - Closest Hit Shader
   - Miss Shader
   - Any Hit Shader（透明）
3. **基础路径追踪**:
   - 射线发射
   - 材质着色
   - 递归追踪（或TraceRayInline）
4. **降噪集成**:
   - 简单时域累积
   - 或使用NVIDIA NRD库

**参考资源**:
- 📚 "Ray Tracing Gems" - Part 2
- 🎓 [NVIDIA DXR Tutorial](https://developer.nvidia.com/rtx/raytracing/dxr/DX12-Raytracing-tutorial-Part-1)
- 💻 [Microsoft DXR Samples](https://github.com/microsoft/DirectX-Graphics-Samples)

**验证标准**:
- ✅ 能渲染硬阴影
- ✅ 反射/折射正确
- ✅ 理解BLAS/TLAS概念
- ✅ 基础降噪工作

**性能注意**:
- 监控射线数量（RenderDoc/PIX）
- 优化BLAS几何
- 使用TraceRayInline减少递归

---

### 项目3.2: 动态漫反射全局光照(DDGI) 🔴
**预计时间**: 4-6周  
**基于**: 项目3.1

**目标**:
- 实现基于探针的GI系统
- 理解辐照度场方法

**关键步骤**:
1. **探针网格布局**:
   - 均匀网格或自适应
   - 探针数据结构（位置）
2. **探针更新**:
   - 每个探针发射多条射线（随机分布）
   - 光线追踪获取辐照度
   - 存储到八面体映射（Octahedral Map）
3. **辐照度/可见性纹理**:
   - Irradiance: RGB辐照度
   - Visibility: 距离信息（AO）
   - 时域混合（指数移动平均）
4. **探针采样**:
   - 找到8个最近探针
   - 三线性插值
   - 基于可见性权重调整
5. **应用到着色**:
   - 直接光照单独计算
   - 间接光照从探针采样

**参考资源**:
- 📄 Majercik 2019 JCGT论文 ⭐
- 💻 [RTXGI SDK](https://github.com/NVIDIAGameWorks/RTXGI)
- 🎥 NVIDIA RTXGI Webinars

**验证标准**:
- ✅ 动态物体产生间接光照
- ✅ 实时更新（60fps目标）
- ✅ 时域稳定（无闪烁）
- ✅ 空间稳定（探针过渡平滑）

**优化要点**:
- 探针射线数量（32-128根）
- 探针更新频率（轮询更新）
- 八面体映射分辨率（6x6到16x16）

**扩展挑战**:
- 自适应探针密度
- 探针分类（静态/动态）
- Infinite bounces（探针递归查询）

---

### 项目3.3: ReSTIR直接光照 🔴
**预计时间**: 4-6周  
**基于**: 项目3.1

**目标**:
- 实现ReSTIR DI算法
- 处理大量动态光源

**关键步骤**:
1. **RIS基础**:
   - 候选样本生成
   - 权重计算
   - Reservoir数据结构
2. **初始采样**:
   - 每像素M个候选光源
   - 更新Reservoir（流式）
3. **时域重用**:
   - 重投影到历史帧
   - Disocclusion检测
   - 合并历史Reservoir
4. **空间重用**:
   - 采样邻域像素Reservoir
   - 可见性验证
   - 多次空间迭代
5. **着色**:
   - 从最终Reservoir采样
   - MIS权重计算
   - 应用光照

**参考资源**:
- 📄 Bitterli 2020 SIGGRAPH论文 ⭐⭐⭐
- 💻 [RTXDI SDK](https://github.com/NVIDIAGameWorks/RTXDI)
- 📄 "Rearchitecting Spatiotemporal Resampling" (2022)

**验证标准**:
- ✅ 支持数千动态光源
- ✅ 1-2 spp达到可接受质量
- ✅ 时空域稳定

**关键难点**:
- Bias理解（时空重用引入偏差）
- Jacobian校正（运动物体）
- Visibility重用策略

**扩展挑战**:
- 实现ReSTIR GI
- 实现ReSTIR PT (Full path tracing)

---

### 项目3.4: 实时降噪(SVGF) 🟡
**预计时间**: 2-3周  
**可配合任何光追项目**

**目标**:
- 实现SVGF降噪器
- 1-4 spp达到可接受质量

**关键步骤**:
1. **方差估计**:
   - 每像素估计颜色方差
   - 时域累积方差
2. **时域滤波**:
   - 运动向量重投影
   - 历史帧混合（Exponential Moving Average）
   - 自适应混合权重（基于方差）
3. **空间滤波**:
   - À-Trous小波变换（5x5核）
   - 边缘停止函数：
     - 深度梯度
     - 法线差异
     - 颜色差异
   - 多尺度迭代（4-5次）
4. **方差引导**:
   - 基于方差调整滤波核大小
   - 高方差区域更多模糊

**参考资源**:
- 📄 Schied 2017 HPG论文
- 💻 [Falcor框架](https://github.com/NVIDIAGameWorks/Falcor) (内置SVGF)
- 💻 [NRD (NVIDIA Real-Time Denoisers)](https://github.com/NVIDIAGameWorks/RayTracingDenoiser)

**验证标准**:
- ✅ 1 spp输入→清晰输出
- ✅ 边缘保持清晰
- ✅ 时域稳定（无拖尾鬼影）
- ✅ 性能<2ms (1080p)

**调试技巧**:
- 可视化方差
- 可视化时域混合权重
- 禁用时域/空间滤波对比

---

## Phase 4: 高级与生产级 (持续学习)

### 项目4.1: 混合GI系统 ⚫
**预计时间**: 8-12周  
**整合前述多个项目**

**目标**:
- 设计类似Lumen的混合方案
- 根据场景特征选择算法

**系统架构**:
```
Hybrid GI System
├── Screen Space (近距离，高频细节)
│   ├── SSAO
│   ├── SSR
│   └── SSGI
├── Probe System (中距离，动态间接光)
│   ├── DDGI
│   └── Screen Probes (UE5 Lumen)
├── Ray Tracing (远距离，fallback)
│   ├── Hardware RT (支持时)
│   ├── Software RT (距离场/SDF)
│   └── 光追级联(距离LOD)
└── Denoising & Temporal (统一降噪)
    ├── SVGF
    └── 时域累积
```

**关键决策点**:
1. **何时用屏幕空间**:
   - 高频细节（小物体AO）
   - 平面反射
   - 性能受限平台
2. **何时用探针**:
   - 大范围间接光照
   - 动态物体交互
   - 稳定性要求高
3. **何时用光追**:
   - 屏幕外物体
   - 精确反射/折射
   - 硬件支持

**实现步骤**:
1. 实现各子系统（已完成）
2. 设计Fallback策略
3. 数据共享优化（G-Buffer统一）
4. 时域累积统一
5. 可配置系统（运行时切换）

**参考案例**:
- 🎮 Unreal Engine 5 Lumen
- 🎮 Metro Exodus Enhanced
- 🎮 Cyberpunk 2077

---

### 项目4.2: 自定义渲染器 ⚫
**预计时间**: 3-6个月  
**从零构建完整引擎**

**目标**:
- 整合所有学习成果
- 生产级质量

**核心模块**:
1. **渲染后端**:
   - 抽象API (DX12/Vulkan)
   - 资源管理
   - Render Graph
2. **光追系统**:
   - BVH构建优化
   - 材质系统
   - 光源系统
3. **GI Pipeline**:
   - 选择你喜欢的方案
   - 多级fallback
4. **后处理**:
   - Tone mapping
   - Bloom
   - TAA
5. **工具链**:
   - 场景编辑器
   - 性能分析器
   - 实时调试可视化

**推荐技术栈**:
- C++20
- DXR或Vulkan RT
- ImGui (调试UI)
- Assimp (模型加载)
- stb_image (纹理)

**里程碑**:
- ✅ Week 4: 基础光栅化渲染
- ✅ Week 8: 光追集成
- ✅ Week 12: DDGI工作
- ✅ Week 16: 降噪 + 后处理
- ✅ Week 20: 优化 + Demo场景

---

## 调试工具与技巧

### 可视化调试
1. **渲染通道可视化**:
   - 单独显示每个GI组件
   - 直接光照 vs 间接光照
   - 每个Bounce分别显示
2. **热力图**:
   - 采样数量
   - 方差/噪声
   - 性能热点（像素耗时）
3. **向量场可视化**:
   - 采样方向
   - 法线/切线
   - 光线传播

### 性能分析
1. **GPU Profiler**:
   - RenderDoc (跨平台)
   - PIX (Windows)
   - Nsight Graphics (NVIDIA)
2. **关键指标**:
   - 每帧射线数
   - BVH遍历深度
   - 内存带宽
   - 着色器占用率

### 单元测试场景
1. **Cornell Box**: 间接光照基准
2. **Sponza**: 复杂几何
3. **Bistro**: 室外大场景
4. **San Miguel**: 高多边形
5. **自定义**: 针对特定算法设计

---

## 学习资源补充

### 开源项目学习
| 项目 | 特点 | 适合学习 |
|------|------|---------|
| [PBRT-v3/v4](https://github.com/mmp/pbrt-v3) | 教科书代码，质量极高 | 离线渲染 |
| [Mitsuba 3](https://github.com/mitsuba-renderer/mitsuba3) | 研究级，支持微分渲染 | 高级算法 |
| [Falcor](https://github.com/NVIDIAGameWorks/Falcor) | NVIDIA实时框架 | 实时GI |
| [Filament](https://github.com/google/filament) | Google移动PBR | 工程实践 |
| [Ray Tracing in One Weekend](https://github.com/RayTracing/raytracing.github.io) | 入门友好 | 第一个项目 |

### 测试场景下载
- **McGuire Computer Graphics Archive**: 高质量场景
- **ORCA Scenes**: 学术界标准测试
- **Benedikt Bitterli's Rendering Resources**: 路径追踪场景
- **Morgan McGuire's Data**: 各种格式资源

---

## 时间规划建议

### 兼职学习路线 (6-9个月)
```
Month 1-2: 项目1.1 + 1.2 (路径追踪器)
Month 3:   项目1.3 (光子映射)
Month 4:   项目2.1 + 2.2 + 2.3 (屏幕空间 + RSM)
Month 5-6: 项目2.4或2.5 (LPV或VCT，建议先RSM)
Month 7:   项目3.1 (DXR基础)
Month 8-9: 项目3.2 (DDGI) + 3.4 (降噪)
```

### 全职学习路线 (3-4个月)
```
Week 1-2:  项目1.1 + 1.2
Week 3-4:  项目1.3 + 论文阅读
Week 5-6:  项目2.3 (RSM) + 2.4 (LPV) 或 2.5 (VCT)
Week 7-8:  项目3.1 (DXR) + 3.4 (降噪)
Week 9-12: 项目3.2 (DDGI) 或 3.3 (ReSTIR)
Week 13+:  项目4.1 (混合系统) 或开始项目4.2
```

### 每日学习建议
- **理论学习**: 1-2小时 (论文/书籍)
- **编码实践**: 2-4小时
- **代码阅读**: 1小时 (开源项目)
- **调试优化**: 根据进度

---

## 评估标准

### 技能检查清单
- [ ] 能从零实现路径追踪器
- [ ] 理解并实现MIS
- [ ] 实现至少一种光子映射变体
- [ ] 实现屏幕空间GI效果
- [ ] 配置DXR/VkRT管线
- [ ] 实现探针系统（DDGI或类似）
- [ ] 实现降噪算法
- [ ] 理解各算法适用场景
- [ ] 能阅读SIGGRAPH最新论文
- [ ] 能设计混合GI方案

### 作品集展示
建议准备以下Demo:
1. **离线渲染器**: 高质量渲染图（Cornell Box, Sponza等）
2. **实时Demo**: 可交互场景，展示动态GI
3. **对比视频**: 有无GI、不同算法对比
4. **技术文档**: 实现细节、性能数据
5. **博客文章**: 学习笔记、踩坑经验

---

## 常见问题

### Q1: 先学离线还是实时?
**A**: 建议先离线。离线渲染帮助理解物理正确性，再学实时近似更容易理解权衡。

### Q2: 数学基础不够怎么办?
**A**: 边学边补：
- 线性代数: 向量、矩阵、变换
- 微积分: 积分、立体角
- 概率论: PDF、期望、方差
- 推荐《3D数学基础》

### Q3: C++不熟练能学吗?
**A**: 可以用其他语言:
- Python: 适合原型和算法理解（较慢）
- Rust: 现代语言，安全性好
- C#: Unity/Godot生态
- 但生产级项目多用C++

### Q4: 需要高端GPU吗?
**A**: 
- 离线项目: CPU也可以（慢点）
- 实时项目: 至少需要支持DXR的显卡 (RTX 20系列+)
- 云GPU: 可以租用AWS/Azure GPU实例

### Q5: 如何验证实现正确性?
**A**:
- 对比参考图像（PBRT等）
- 能量守恒检查
- 白炉测试（White Furnace Test）
- 单位测试（已知解析解场景）

---

**祝你实践顺利！代码是最好的老师。** 🚀

遇到问题时的调试流程:
1. 可视化中间结果
2. 简化场景（单个球+点光源）
3. 对比参考实现
4. 逐行调试 + 日志输出
5. 社区求助（Shadertoy, Reddit, Discord）

