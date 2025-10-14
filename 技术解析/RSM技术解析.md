# Reflective Shadow Maps (RSM) 技术深入解析

## 为什么RSM值得单独学习？

Reflective Shadow Maps (RSM) 是实时全局光照发展史上的一个**关键转折点**，它首次将虚拟点光源(VPL)方法成功应用到实时渲染中，并成为多个后续技术的基础。

---

## 历史地位与影响

### 开创性贡献 (2005)
- **作者**: Carsten Dachsbacher & Marc Stamminger
- **发表**: I3D 2005
- **核心思想**: 将Shadow Map扩展为包含辐射信息的G-Buffer，每个像素作为VPL

### 在GI发展中的位置

```
时间线：
1997  Instant Radiosity (Keller)
      └─ 提出VPL概念（离线）
         │
2005  Reflective Shadow Maps ⭐
      └─ VPL实时化突破
         │
         ├─ 2009: Light Propagation Volumes (基于RSM)
         │        └─ CryEngine 3采用
         │
         ├─ 2011: Voxel Cone Tracing (可用RSM初始化)
         │        └─ UE4早期探索
         │
         └─ 多种屏幕空间GI方法的启发
```

---

## 核心算法详解

### 1. RSM生成阶段

从主光源视角渲染场景，生成包含以下信息的G-Buffer：

```glsl
// RSM包含的数据
struct RSMTexel {
    vec3 worldPosition;    // 世界空间位置
    vec3 worldNormal;      // 世界空间法线
    vec3 flux;             // 出射通量 (Radiant Flux)
};

// Fragment Shader (光源视角)
void main() {
    RSM_Position = worldPos;
    RSM_Normal = worldNormal;
    RSM_Flux = surfaceAlbedo * lightColor; // 反射的通量
}
```

### 2. VPL采样阶段

在着色时，每个像素从RSM中采样多个VPL：

```glsl
vec3 computeIndirectIllumination(vec3 shadingPoint, vec3 normal) {
    vec3 indirectLight = vec3(0.0);
    
    // 采样N个VPL (通常64-256个)
    for (int i = 0; i < NUM_VPL_SAMPLES; i++) {
        // 重要性采样RSM
        vec2 vplUV = importanceSampleRSM(i);
        
        // 读取VPL数据
        vec3 vplPos = texture(RSM_Position, vplUV).xyz;
        vec3 vplNormal = texture(RSM_Normal, vplUV).xyz;
        vec3 vplFlux = texture(RSM_Flux, vplUV).xyz;
        
        // 计算VPL贡献
        vec3 vplToShading = shadingPoint - vplPos;
        float dist = length(vplToShading);
        vec3 vplDir = vplToShading / dist;
        
        // 评估几何项
        float G = max(0.0, dot(vplNormal, vplDir))  // VPL法线
                * max(0.0, dot(normal, -vplDir))    // 着色点法线
                / (dist * dist);                     // 距离衰减
        
        // BRDF (Lambertian)
        vec3 brdf = surfaceAlbedo / PI;
        
        // 累加贡献
        indirectLight += vplFlux * brdf * G;
    }
    
    return indirectLight / NUM_VPL_SAMPLES;
}
```

### 3. 重要性采样优化

随机采样会产生大量噪声，需要重要性采样：

```cpp
// 基于距离和通量的重要性采样
vec2 importanceSampleRSM(int sampleIdx) {
    // 方法1: 分层采样 (Stratified Sampling)
    int gridSize = int(sqrt(NUM_VPL_SAMPLES));
    int x = sampleIdx % gridSize;
    int y = sampleIdx / gridSize;
    vec2 jitter = vec2(random(), random());
    return (vec2(x, y) + jitter) / float(gridSize);
    
    // 方法2: 基于通量的重要性采样
    // 预先计算RSM的CDF，按照通量分布采样
}
```

---

## 优势与局限

### ✅ 优势

1. **完全动态**: 
   - 光源可以移动
   - 场景可以动态变化
   - 无需预计算

2. **概念简单**:
   - 易于理解和实现
   - 标准渲染管线的自然扩展

3. **基础性强**:
   - 为LPV、VXGI等提供输入
   - 启发了多种后续算法

4. **性能可控**:
   - 通过调整VPL数量权衡质量/性能

### ❌ 局限

1. **可见性限制**:
   - 只能处理光源可见的表面
   - 背面和遮挡物体无法产生间接光

```
     Light
       ↓
    [Object A]  ← 产生VPL ✓
       ↓
    [Object B]  ← 被A遮挡，无VPL ✗
```

2. **单次反弹**:
   - 标准RSM只处理一次间接光照
   - 多次反弹需要递归RSM（昂贵）

3. **采样噪声**:
   - 需要大量VPL采样（>100）
   - 或需要强力降噪（模糊）

4. **性能问题**:
   - 每像素数百次纹理采样
   - 对于1080p分辨率压力较大

---

## 改进与变种

### 1. Imperfect Shadow Maps (2009)
**核心思想**: 使用简化几何生成RSM，减少开销

```cpp
// 简化场景几何
struct ImplicitGeometry {
    vec3 position;
    vec3 normal;
    float radius;  // 点或圆盘
};
```

### 2. Splatting方法 (2006)
**核心思想**: 将VPL贡献Splat到屏幕空间

```
传统方法:
  每个像素 → 采样VPL

Splatting:
  每个VPL → 影响多个像素 (光栅化)
```

优势: 更好的性能，更少的重复计算

### 3. 递归RSM (多次反弹)
```
Pass 1: 光源 → RSM1 (一次反弹)
Pass 2: 从RSM1的VPL → RSM2 (二次反弹)
Pass 3: 从RSM2的VPL → RSM3 (三次反弹)
...
```

问题: 性能开销指数增长

---

## RSM作为其他技术的基础

### 1. Light Propagation Volumes (LPV, 2009)

LPV使用RSM作为初始光源注入：

```
Step 1: 生成RSM
Step 2: 将RSM的VPL注入到体素网格 ← RSM在此使用
Step 3: 在体素网格中传播光照（SH）
Step 4: 从体素网格采样间接光
```

**为什么需要RSM**:
- LPV需要初始的光源分布
- RSM提供空间中的初始VPL
- 这些VPL成为体素网格的"种子"

### 2. Voxel Global Illumination (VXGI)

虽然VCT主要用体素化，但可以用RSM加速：

```
方案A (纯体素):
  体素化场景 → 锥形追踪 → 间接光

方案B (RSM辅助):
  RSM + 体素化 → 更好的初始照明 → 锥形追踪
```

### 3. 屏幕空间GI

RSM的思想影响了SSGI：

```
RSM:    光源视角G-Buffer → VPL采样
SSGI:   相机视角G-Buffer → 邻域采样
```

相似点: 都是将G-Buffer像素作为次级光源

---

## 实现要点与优化

### 1. RSM分辨率选择

```cpp
// 权衡表
RSM分辨率     VPL密度      性能      质量
256×256       低          快        粗糙
512×512       中          中等      一般  ← 推荐
1024×1024     高          慢        细腻
2048×2048     极高        很慢      最佳 (离线)
```

### 2. VPL采样数量

```cpp
// 实时应用建议
低质量模式:   32-64  VPL/像素
中质量模式:   64-128 VPL/像素
高质量模式:   128-256 VPL/像素
离线预览:     512+ VPL/像素
```

### 3. 降噪策略

```glsl
// 方法1: 双边滤波
vec3 bilateralFilter(vec3 noisyGI, vec3 normal, float depth) {
    vec3 filtered = vec3(0.0);
    float weightSum = 0.0;
    
    for (int y = -radius; y <= radius; y++) {
        for (int x = -radius; x <= radius; x++) {
            vec3 sampleNormal = getNormal(offset);
            float sampleDepth = getDepth(offset);
            
            // 边缘停止函数
            float normalWeight = pow(max(0.0, dot(normal, sampleNormal)), 32.0);
            float depthWeight = exp(-abs(depth - sampleDepth) * 10.0);
            
            float weight = normalWeight * depthWeight;
            filtered += getSample(offset) * weight;
            weightSum += weight;
        }
    }
    
    return filtered / weightSum;
}

// 方法2: 时域累积 (适合动态场景)
vec3 temporalAccumulation(vec3 currentGI, vec3 historyGI, float alpha) {
    return mix(historyGI, currentGI, alpha); // alpha = 0.1-0.2
}
```

### 4. 性能优化技巧

```cpp
// 优化1: 分辨率降采样
// 1/2或1/4分辨率计算GI，上采样到全分辨率

// 优化2: 时域复用
// 每帧只更新部分像素的RSM采样

// 优化3: 空间复用
// 相邻像素共享部分VPL样本

// 优化4: 计算着色器
// 使用Compute Shader并行处理
```

---

## 与现代方法的对比

| 特性 | RSM | DDGI | Lumen | ReSTIR |
|-----|-----|------|-------|--------|
| **年份** | 2005 | 2019 | 2022 | 2020 |
| **基础** | VPL | 探针+RT | 混合 | 重采样 |
| **动态性** | ✅ 完全 | ✅ 完全 | ✅ 完全 | ✅ 完全 |
| **质量** | 中 | 高 | 极高 | 高 |
| **性能** | 中 | 好 | 中-好 | 优秀 |
| **硬件需求** | 低 | RT推荐 | RT必需 | RT必需 |
| **多次反弹** | ❌ 困难 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **适用场景** | 中等规模 | 大场景 | AAA游戏 | 大量光源 |

---

## 学习RSM的价值

### 1. 教育价值
- **理解VPL方法**: RSM是最直观的VPL实现
- **实时GI入门**: 相对简单，适合初学者
- **理论与实践**: 连接Instant Radiosity理论和实时应用

### 2. 工程价值
- **Fallback方案**: 非RT硬件的GI选择
- **混合系统**: 可作为其他方法的补充
- **快速原型**: 验证GI效果的快速方法

### 3. 历史价值
- **技术演进**: 理解GI算法的发展脉络
- **影响力**: 启发了LPV、VXGI等重要技术
- **工业应用**: CryEngine等引擎曾广泛使用

---

## 实践建议

### 学习路径
```
第1周: 理论学习
  ├─ 阅读Keller 1997 (Instant Radiosity)
  ├─ 阅读Dachsbacher 2005 (RSM原论文)
  └─ 观看GAMES202 Lecture 6

第2周: 基础实现
  ├─ 实现RSM生成
  ├─ 实现简单VPL采样
  └─ 验证间接光照效果

第3周: 优化与改进
  ├─ 实现重要性采样
  ├─ 添加降噪
  └─ 性能优化

第4周: 扩展（可选）
  ├─ 尝试Splatting方法
  ├─ 实现Imperfect Shadow Maps
  └─ 作为LPV的准备
```

### 调试检查清单
- [ ] RSM纹理内容正确（可视化位置/法线/通量）
- [ ] VPL分布均匀（可视化采样位置）
- [ ] 间接光照方向正确（color bleeding）
- [ ] 无明显噪声（或降噪工作）
- [ ] 性能达标（30fps+ at 1080p）

### 测试场景
1. **Cornell Box**: 经典color bleeding测试
2. **Sponza**: 复杂几何，多表面交互
3. **动态物体**: 验证实时性
4. **移动光源**: 验证动态光照

---

## 参考资源总结

### 核心论文
1. **Keller, A.** (1997). "Instant Radiosity" - SIGGRAPH
   - VPL理论基础
2. **Dachsbacher, C. & Stamminger, M.** (2005). "Reflective Shadow Maps" - I3D ⭐
   - RSM开创性工作
3. **Dachsbacher, C. & Stamminger, M.** (2006). "Splatting Indirect Illumination" - I3D
   - Splatting改进
4. **Ritschel, T. et al.** (2009). "Imperfect Shadow Maps" - SIGGRAPH Asia
   - 简化几何优化

### 课程与教程
- **GAMES202** Lecture 6 - RSM详解（闫令琪）
- **Real-Time Rendering 4th** Chapter 11.4 - VPL方法
- **GPU Pro / GPU Gems** 相关章节

### 代码参考
- GitHub搜索: "reflective shadow maps"
- 参考LPV实现（通常包含RSM部分）

---

## 结论

Reflective Shadow Maps虽然提出于2005年，但它的核心思想——**将Shadow Map扩展为辐射度信息的载体**——至今仍在影响实时GI的设计。

作为VPL方法的实时化突破，RSM：
- ✅ 开启了实时动态GI的新纪元
- ✅ 为LPV等后续技术奠定基础
- ✅ 提供了简单易懂的GI入门路径

**学习建议**: 在学习LPV之前务必理解RSM，这将大大帮助你理解LPV的光源注入阶段，以及整个实时GI的演进逻辑。

---

**文档版本**: v1.0  
**创建日期**: 2025年10月  
**适用人群**: 学习实时全局光照的开发者

