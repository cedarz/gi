# 体数据与全局光照技术结合指南

本文档详细说明如何将体积数据（Volume Data）与各种全局光照（GI）技术相结合。

---

## 目录
1. [体数据基础概念](#体数据基础概念)
2. [RSM + 体数据](#rsm--体数据)
3. [LPV + 体数据](#lpv--体数据)
4. [VCT + 体数据](#vct--体数据)
5. [DDGI + 体数据](#ddgi--体数据)
6. [ReSTIR + 体数据](#restir--体数据)
7. [体数据专用技术](#体数据专用技术)
8. [混合方案架构](#混合方案架构)
9. [实现路线图](#实现路线图)
10. [参考资源](#参考资源)

---

## 体数据基础概念

### 核心参考资源

**经典教材**：
- 📚 **"Physically Based Rendering" (PBRT)** - Pharr, Jakob, Humphreys
  - [官方网站](https://www.pbr-book.org/)
  - Chapter 11 & 15: Volume Scattering
  - ⭐⭐⭐ 体积渲染的圣经级教材
  - 免费在线阅读
- 📚 **"Real-Time Rendering" 4th Edition** - Akenine-Möller et al.
  - Chapter 14: Volumetric and Translucency Rendering
  - 实时体积渲染综述

**基础理论**：
- 📄 **"Optical Models for Direct Volume Rendering"** - Max (IEEE TVCG 1995)
  - 体渲染方程的数学推导
- 📄 **"A Practical Analytic Model for Daylight"** - Preetham et al. (SIGGRAPH 1999)
  - 大气散射模型
- 📄 **"Display of Surfaces from Volume Data"** - Levoy (IEEE CG&A 1988)
  - 体积渲染的早期工作

**GPU Gems系列**：
- 📚 **GPU Gems 3 - Chapter 13: "Volumetric Light Scattering as a Post-Process"**
  - [免费在线](https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process)
  - God Rays实现
- 📚 **GPU Pro/GPU Zen系列**
  - 多篇体积渲染相关文章

**SIGGRAPH Course Notes**：
- 📄 **"Production Volume Rendering"** (SIGGRAPH 2017)
  - [Course Website](https://graphics.pixar.com/library/)
  - Pixar, DreamWorks, Disney等公司的生产经验
- 📄 **"Advances in Real-Time Rendering"** - 历年SIGGRAPH Courses
  - [网站](https://advances.realtimerendering.com/)
  - 包含多个体积渲染专题

**相位函数**：
- 📄 **"A New Analytic Phase Function"** - Cornette & Shanks (1992)
  - Henyey-Greenstein的改进
- 📄 **"Importance Sampling for Production Rendering"** - Pharr & Humphreys
  - 相位函数采样技术

**在线资源**：
- 📝 **Scratchapixel**
  - [https://www.scratchapixel.com/](https://www.scratchapixel.com/)
  - Volume Rendering教程系列
- 📝 **Shadertoy**
  - [https://www.shadertoy.com/](https://www.shadertoy.com/)
  - 搜索"volumetric"查看实时演示

### 体数据与表面渲染的区别

**表面渲染（Surface Rendering）**:
- 光线与几何体表面单次交互
- 使用BRDF描述反射特性
- 单点着色计算

**体数据渲染（Volume Rendering）**:
- 光线在介质中持续交互
- 使用相位函数（Phase Function）描述散射
- 需要光线步进和体积积分

### 体渲染方程

$$
L_o(x, \omega) = \int_0^d T(x, t) \cdot \sigma_s(x_t) \cdot L_s(x_t, \omega) \, dt
$$

其中：
- \( T(x, t) \): 透射率（Transmittance）
- \( \sigma_s \): 散射系数
- \( L_s \): 散射辐射度
- \( d \): 光线行进距离

### 关键参数

```cpp
struct VolumeProperties {
    float3 position;
    float density;           // 密度 ρ
    float3 albedo;          // 散射反照率
    float anisotropy;       // 各向异性 g (-1到1)
    float absorption;       // 吸收系数 σ_a
    float scattering;       // 散射系数 σ_s
    float extinction;       // 消光系数 σ_t = σ_a + σ_s
};
```

### 相位函数

**Henyey-Greenstein 相位函数**（最常用）:

```glsl
float phaseHG(float cosTheta, float g) {
    float g2 = g * g;
    float denom = 1.0 + g2 - 2.0 * g * cosTheta;
    return (1.0 - g2) / (4.0 * PI * pow(denom, 1.5));
}
```

- g = 0: 各向同性散射（如大气）
- g > 0: 前向散射（如雾、云）
- g < 0: 后向散射（如雪）

---

## RSM + 体数据

### 概念：体积RSM（Volumetric RSM）

传统RSM生成虚拟点光源（VPL）照亮表面，体积RSM将这些VPL的影响扩展到体积介质中。

### 核心论文与资源

**原始论文**：
- 📄 **"Reflective Shadow Maps"** - Carsten Dachsbacher, Marc Stamminger (I3D 2005)
  - [论文链接](https://doi.org/10.1145/1053427.1053460)
  - 首次提出RSM概念，奠定VPL方法基础

**体积扩展**：
- 📄 **"Incremental Instant Radiosity for Real-Time Indirect Illumination"** (Eurographics Symposium on Rendering 2007)
  - 讨论VPL在体积中的应用
- 📄 **"Fast, Arbitrary BRDF Shading for Low-Frequency Lighting Using Spherical Harmonics"** (EGSR 2002)
  - VPL采样的理论基础

**实现参考**：
- 💻 [RSM Implementation (OpenGL)](https://github.com/tatsy/OpenGLCourseJP/tree/master/src/rsm)
  - 日本OpenGL教程中的完整RSM实现
- 💻 [Reflective Shadow Maps Tutorial](https://github.com/Angelo1211/SoftwareRenderer/blob/master/documentation/ReflectiveShadowMaps.md)
  - 详细的实现教程和代码
- 💻 [RSM in Three.js](https://github.com/mrdoob/three.js/issues/7063)
  - Web端实现讨论和示例

**视频教程**：
- 🎥 **GAMES202 Lecture 6** - 闫令琪
  - [Bilibili链接](https://www.bilibili.com/video/BV1YK4y1T7yY?p=6)
  - 中文讲解，包含VPL采样细节
- 🎥 **"Reflective Shadow Maps Explained"** - ThinMatrix
  - [YouTube链接](https://www.youtube.com/results?search_query=reflective+shadow+maps)

**引擎实现**：
- CryEngine 3的RSM实现（已公开部分源码）
- Unreal Engine的LPV系统基于RSM注入

### 实现步骤

#### 1. RSM生成（与传统相同）

```glsl
// RSM Pass - 从光源视角渲染
layout(location = 0) out vec4 RSM_Position;   // 世界空间位置
layout(location = 1) out vec4 RSM_Normal;     // 世界空间法线
layout(location = 2) out vec4 RSM_Flux;       // 反射通量

void main() {
    RSM_Position = worldPosition;
    RSM_Normal = worldNormal;
    RSM_Flux = albedo * lightIntensity * max(0, dot(normal, lightDir));
}
```

#### 2. 体积光线步进

```glsl
// 体积渲染Pass
float3 volumetricLighting(float3 rayOrigin, float3 rayDir, 
                          float tMin, float tMax,
                          sampler2D RSM_Position, 
                          sampler2D RSM_Normal,
                          sampler2D RSM_Flux) {
    float3 scatteredLight = float3(0);
    float transmittance = 1.0;
    
    const int numSteps = 64;
    float stepSize = (tMax - tMin) / numSteps;
    
    for(int i = 0; i < numSteps; i++) {
        float t = tMin + stepSize * (i + random());
        float3 samplePos = rayOrigin + rayDir * t;
        
        // 采样体积密度
        float density = sampleVolumeDensity(samplePos);
        if(density < 0.001) continue;
        
        // 从RSM采样VPL
        float3 vplContribution = sampleVPLs(samplePos, RSM_Position, 
                                            RSM_Normal, RSM_Flux);
        
        // 体积散射
        float extinction = density * extinctionCoeff;
        float scattering = density * scatteringCoeff;
        
        scatteredLight += transmittance * scattering * vplContribution * stepSize;
        transmittance *= exp(-extinction * stepSize);
        
        if(transmittance < 0.01) break; // 早期终止
    }
    
    return scatteredLight;
}
```

#### 3. VPL采样（考虑相位函数）

```glsl
float3 sampleVPLs(float3 worldPos, sampler2D RSM_Pos, 
                  sampler2D RSM_Normal, sampler2D RSM_Flux) {
    float3 totalContribution = float3(0);
    
    const int numVPLSamples = 128;
    for(int i = 0; i < numVPLSamples; i++) {
        // 从RSM随机采样
        float2 uv = randomSample2D();
        float3 vplPos = texture(RSM_Pos, uv).xyz;
        float3 vplNormal = texture(RSM_Normal, uv).xyz;
        float3 vplFlux = texture(RSM_Flux, uv).rgb;
        
        // 计算VPL到采样点的方向
        float3 vplDir = vplPos - worldPos;
        float dist = length(vplDir);
        vplDir /= dist;
        
        // 相位函数（代替BRDF）
        float phase = phaseHG(dot(-vplDir, lightDir), anisotropy);
        
        // VPL贡献（考虑法线、距离衰减）
        float geometry = max(0, dot(vplNormal, -vplDir)) / (dist * dist);
        totalContribution += vplFlux * phase * geometry;
    }
    
    return totalContribution / numVPLSamples;
}
```

### 性能优化

#### A. 重要性采样VPL

```glsl
// 基于距离和通量的重要性采样
float vplWeight(float3 vplPos, float3 vplFlux, float3 samplePos) {
    float dist = length(vplPos - samplePos);
    float luminance = dot(vplFlux, float3(0.299, 0.587, 0.114));
    return luminance / (1.0 + dist * dist);
}
```

#### B. 降噪

体积渲染本身噪声较大，需要：
- **时域累积**：混合历史帧
- **空间滤波**：双边模糊（保持密度边界）
- **低分辨率计算 + 上采样**

### 适用场景

✅ 适合：
- 体积雾与间接光照结合
- 单次散射占主导的场景
- 静态或缓慢变化的体积

❌ 限制：
- 多次散射不准确
- 需要大量VPL采样（噪声问题）
- 只能处理光源可见区域

### 实际案例

**项目扩展**：在"项目2.3: RSM"基础上添加
- 实现时间：+1-2周
- 测试场景：Cornell Box + 均匀雾
- 验证效果：雾中的color bleeding

---

## LPV + 体数据

### 为什么LPV天然适合体数据？

LPV（Light Propagation Volumes）本身就是基于体素网格的，可以直接存储和传播体积辐射场。

### 核心论文与资源

**原始论文**：
- 📄 **"Cascaded Light Propagation Volumes for Real-Time Indirect Illumination"** - Anton Kaplanyan, Carsten Dachsbacher (I3D 2010)
  - [论文链接](https://doi.org/10.1145/1730804.1730821)
  - LPV的原始论文，CryEngine 3采用
- 📄 **"Light Propagation Volumes in CryEngine 3"** - Anton Kaplanyan (SIGGRAPH 2009 Course)
  - [Course Notes](https://advances.realtimerendering.com/s2009/index.html)
  - 工业级实现细节

**球谐光照基础**：
- 📄 **"Stupid Spherical Harmonics (SH) Tricks"** - Peter-Pike Sloan (GDC 2008)
  - [论文PDF](http://www.ppsloan.org/publications/)
  - SH在实时渲染中的应用
- 📚 **"Spherical Harmonics Lighting: The Gritty Details"** - Robin Green
  - [技术报告](https://www.research.scea.com/gdc2003/spherical-harmonic-lighting.pdf)

**体积扩展**：
- 📄 **"Real-Time Diffuse Global Illumination Using Radiance Hints"** (HPG 2011)
  - 讨论体积中的辐射度传播
- 📄 **"Voxel-based Global Illumination"** - Cyril Crassin PhD Thesis (2011)
  - 第4章讨论LPV与体积结合

**实现参考**：
- 💻 [LPV Implementation (OpenGL)](https://github.com/djbozkosz/Light-Propagation-Volumes)
  - 完整的LPV实现，包含注入、传播、采样
- 💻 [Cascaded LPV in Unity](https://github.com/ConorStokes/CascadedLightPropagationVolumes)
  - Unity实现，含级联支持
- 💻 [LPV Tutorial](https://github.com/Raikiri/LegitEngine/wiki/Light-Propagation-Volumes)
  - 详细教程和性能分析
- 💻 [UE4 LPV Source Code](https://github.com/EpicGames/UnrealEngine/blob/release/Engine/Shaders/Private/LPVCommon.ush)
  - Unreal Engine 4的LPV shader实现（需要Epic账号访问）

**视频教程**：
- 🎥 **GAMES202 Lecture 7** - 闫令琪
  - [Bilibili链接](https://www.bilibili.com/video/BV1YK4y1T7yY?p=7)
  - 中文讲解LPV原理
- 🎥 **"Light Propagation Volumes"** - CryEngine GDC Talk
  - [YouTube链接](https://www.youtube.com/results?search_query=light+propagation+volumes+cryengine)
- 🎥 **"Implementing LPV"** - Two Minute Papers
  - 论文可视化讲解

**引擎实现**：
- **CryEngine 3/5**: 原始实现者，生产级代码
- **Unreal Engine 4**: 内置LPV支持（已在UE5中移除）
- **Godot 4.0**: SDFGI系统部分借鉴LPV思想

**工具与调试**：
- RenderDoc捕获LPV网格可视化
- CryEngine的LPV调试可视化模式

### 增强架构

```cpp
struct LPV_Cell {
    // 传统LPV数据
    float SH_R[4];  // 红色通道球谐系数
    float SH_G[4];  // 绿色通道
    float SH_B[4];  // 蓝色通道
    
    // 新增：体积数据
    float volumeDensity;        // 体积密度
    float volumeAlbedo[3];      // 散射反照率
    float volumeAnisotropy;     // 相位函数参数
};
```

### 实现步骤

#### 1. 注入阶段（Injection）

**表面注入**（传统）:
```glsl
// 从RSM注入表面VPL
void injectSurfaceVPL(float3 worldPos, float3 normal, float3 flux) {
    ivec3 gridCoord = worldToGrid(worldPos);
    SH coeffs = projectToSH(normal, flux);
    atomicAdd(lpvGrid[gridCoord].SH_R, coeffs.r);
    atomicAdd(lpvGrid[gridCoord].SH_G, coeffs.g);
    atomicAdd(lpvGrid[gridCoord].SH_B, coeffs.b);
}
```

**体积注入**（新增）:
```glsl
// 注入体积密度和散射属性
void injectVolumeDensity(float3 worldPos, float density, float3 albedo) {
    ivec3 gridCoord = worldToGrid(worldPos);
    atomicAdd(lpvGrid[gridCoord].volumeDensity, density);
    lpvGrid[gridCoord].volumeAlbedo = albedo; // 或混合
}
```

#### 2. 传播阶段（Propagation）

修改传播以考虑体积遮挡：

```glsl
void propagateLPV(inout LPV_Grid currentGrid, LPV_Grid previousGrid) {
    for(int z = 0; z < gridSize.z; z++)
    for(int y = 0; y < gridSize.y; y++)
    for(int x = 0; x < gridSize.x; x++) {
        ivec3 coord = ivec3(x, y, z);
        SH accumulated = SH(0);
        
        // 从6个方向传播
        const ivec3 directions[6] = {
            ivec3(1,0,0), ivec3(-1,0,0),
            ivec3(0,1,0), ivec3(0,-1,0),
            ivec3(0,0,1), ivec3(0,0,-1)
        };
        
        for(int i = 0; i < 6; i++) {
            ivec3 neighborCoord = coord + directions[i];
            if(!isValidCoord(neighborCoord)) continue;
            
            SH neighborLight = getSH(previousGrid, neighborCoord);
            
            // 考虑体积遮挡
            float density = previousGrid[neighborCoord].volumeDensity;
            float transmittance = exp(-density * cellSize * extinctionCoeff);
            
            // 旋转SH并衰减
            SH rotated = rotateSH(neighborLight, directions[i]);
            accumulated += rotated * transmittance;
        }
        
        setSH(currentGrid, coord, accumulated);
    }
}
```

#### 3. 采样阶段（Sampling）

体积中的点查询LPV：

```glsl
float3 sampleLPV_Volume(float3 worldPos, float3 viewDir) {
    // 三线性插值LPV
    SH lightSH = trilinearSample(lpvGrid, worldPos);
    
    // 采样体积属性
    float density = trilinearSample(lpvGrid.volumeDensity, worldPos);
    float3 albedo = trilinearSample(lpvGrid.volumeAlbedo, worldPos);
    
    // 计算入射辐射度（从SH积分）
    float3 irradiance = evaluateSH(lightSH);
    
    // 应用相位函数（简化为各向同性）
    float phase = 1.0 / (4.0 * PI);
    
    // 体积散射
    return density * albedo * irradiance * phase;
}
```

### 多次散射

LPV的迭代传播自然支持多次散射：

```glsl
// 主循环
for(int iteration = 0; iteration < 6; iteration++) {
    propagateLPV(lpvGrids[(iteration+1)%2], lpvGrids[iteration%2]);
}
// 更多迭代 = 更多散射反弹
```

### 几何体积（Geometry Volume）

处理体积对光的遮挡：

```glsl
// 在传播前，注入几何遮挡信息
void injectGeometryOcclusion() {
    // 体素化场景几何
    for(each triangle) {
        ivec3 voxelCoord = voxelize(triangle);
        lpvGrid[voxelCoord].volumeDensity += occlusionWeight;
    }
}
```

### 性能特点

- **固定开销**：与体积复杂度无关（依赖网格分辨率）
- **传播成本**：64³网格，6次迭代 ≈ 1-2ms
- **内存占用**：合理（每个cell约64字节）

### 适用场景

✅ 优势：
- 动态体积雾（实时更新）
- 统一表面和体积照明
- 多次散射近似
- 性能可控

❌ 限制：
- 光泄漏问题（需要GV改进）
- 网格分辨率限制细节
- 各向异性散射支持有限（SH频带限制）

### 实际案例

**CryEngine实现**：
- 基础网格：64³
- 级联LPV：3级（近、中、远）
- 更新频率：30Hz（与主渲染解耦）

**项目扩展**：在"项目2.4: LPV"基础上添加
- 实现时间：+1周
- 关键修改：传播shader、采样逻辑
- 测试场景：动态光源 + 动态雾

---

## VCT + 体数据

### 完美契合

体素锥追踪（Voxel Cone Tracing）本质就是体素化渲染，天然支持半透明和体积。

### 核心论文与资源

**原始论文**：
- 📄 **"Interactive Indirect Illumination Using Voxel Cone Tracing"** - Cyril Crassin et al. (Computer Graphics Forum 2011)
  - [论文链接](https://doi.org/10.1111/j.1467-8659.2011.02063.x)
  - VCT的奠基之作，NVIDIA首次提出
- 📄 **"GigaVoxels: Ray-Guided Streaming for Efficient and Detailed Voxel Rendering"** - Cyril Crassin et al. (I3D 2009)
  - 稀疏体素八叉树（SVO）技术
- 📄 **PhD Thesis: "Voxel-based Global Illumination"** - Cyril Crassin (2011)
  - [完整论文](https://tel.archives-ouvertes.fr/tel-00760453/document)
  - 300+页详细讲解VCT所有细节

**体素化技术**：
- 📄 **"Octree-Based Sparse Voxelization Using the GPU Hardware Rasterizer"** - Cyril Crassin, Simon Green (OpenGL Insights 2012)
  - [章节PDF](https://www.nvidia.com/docs/IO/88889/OpenGLInsights.pdf)
  - 保守光栅化实现细节
- 📄 **"Real-Time Voxelization for Complex Polygonal Models"** - Eisemann, Décoret (Pacific Graphics 2008)
  - 几何着色器体素化

**各向异性体素**：
- 📄 **"A Voxel-Based Rendering Pipeline for Large 3D Line Sets"** (IEEE TVCG 2013)
  - 6方向Mipmap生成技术

**实现参考**：
- 💻 [Voxel Cone Tracing (OpenGL)](https://github.com/Friduric/voxel-cone-tracing)
  - ⭐ 最完整的开源实现，含详细注释
  - 支持动态场景、锥追踪、SVO
- 💻 [VCT Tutorial](https://github.com/jose-villegas/VCTRenderer)
  - 带教程的实现，易于学习
- 💻 [VXGI-like Implementation](https://github.com/otaku690/SparseVoxelOctree)
  - NVIDIA VXGI风格的实现
- 💻 [Unity VCT Plugin](https://github.com/Flafla2/Voxel-Cone-Tracing)
  - Unity集成示例

**NVIDIA VXGI**：
- 📄 **"VXGI: Dynamic Global Illumination for Games"** - NVIDIA GameWorks
  - [技术文档](https://developer.nvidia.com/vxgi)
  - 商业级实现（已停止更新）
- 🎥 **GDC 2015: "VXGI - Voxel Cone Tracing"**
  - [Slides](https://on-demand.gputechconf.com/gtc/2014/presentations/S4552-rt-voxel-based-global-illumination-gpus.pdf)

**视频教程**：
- 🎥 **GAMES202 Lecture 9-10** - 闫令琪
  - [Bilibili链接](https://www.bilibili.com/video/BV1YK4y1T7yY?p=9)
  - 详细中文讲解，包含体素化和锥追踪
- 🎥 **"Voxel Cone Tracing Explained"** - Two Minute Papers
  - [YouTube](https://www.youtube.com/watch?v=T2pJGVCZhvQ)
- 🎥 **Cyril Crassin's SIGGRAPH Talk**
  - [视频链接](https://www.youtube.com/results?search_query=cyril+crassin+voxel+cone+tracing)

**引擎实现**：
- **NVIDIA GameWorks VXGI**: 停止更新但代码可参考
- **Unreal Engine 5**: Lumen部分借鉴VCT思想
- **Unity**: 第三方插件支持

**博客文章**：
- 📝 **"Voxel Cone Tracing and Sparse Voxel Octree"** - MJP's Blog
  - [链接](https://therealmjp.github.io/)
  - 实现细节和优化技巧
- 📝 **"Voxel-Based GI Implementation Notes"**
  - [LearnOpenGL CN](https://learnopengl-cn.github.io/)

### 数据结构扩展

```cpp
struct Voxel {
    float3 color;           // 表面反照率
    float3 normal;          // 平均法线
    float opacity;          // 不透明度 [0,1]
    
    // 新增：体积属性
    float density;          // 体积密度（用于半透明累积）
    float emissive;         // 自发光
};

// 存储格式：八叉树 (SVO) 或 3D纹理
```

### 体素化阶段

#### 保守光栅化 + 半透明支持

```glsl
// Geometry Shader - 体素化
layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;

out float gOpacity;

void main() {
    // 选择主轴投影
    vec3 faceNormal = cross(
        gl_in[1].gl_Position.xyz - gl_in[0].gl_Position.xyz,
        gl_in[2].gl_Position.xyz - gl_in[0].gl_Position.xyz
    );
    int axis = getDominantAxis(faceNormal);
    
    // 保守光栅化（扩展三角形）
    for(int i = 0; i < 3; i++) {
        vec4 pos = projectToAxis(gl_in[i].gl_Position, axis);
        pos.xy += expandTriangle(pos.xy, viewportSize);
        gl_Position = pos;
        gOpacity = materialOpacity;
        EmitVertex();
    }
    EndPrimitive();
}
```

#### Fragment Shader - 体素写入

```glsl
// Fragment Shader
layout(location = 0) out vec4 outColor;

uniform layout(r32ui) volatile uimage3D voxelGrid;

void main() {
    ivec3 voxelCoord = ivec3(gl_FragCoord.xyz);
    
    // 原子操作写入颜色（平均）
    uint packedColor = packColor(materialColor * opacity);
    imageAtomicMax(voxelGrid, voxelCoord, packedColor);
    
    // 写入密度（用于体积渲染）
    float density = 1.0 - opacity; // 透明度转密度
    imageAtomicAdd(voxelDensity, voxelCoord, packFloat(density));
}
```

### Mipmap生成（各向异性）

```glsl
// 为6个方向生成Mipmap
void generateAnisotropicMipmap() {
    for(int mipLevel = 1; mipLevel < maxMipLevel; mipLevel++) {
        int size = voxelGridSize >> mipLevel;
        
        for(int z = 0; z < size; z++)
        for(int y = 0; y < size; y++)
        for(int x = 0; x < size; x++) {
            ivec3 coord = ivec3(x, y, z);
            
            // 从8个子体素采样
            vec4 avgColor = vec4(0);
            float avgDensity = 0;
            for(int i = 0; i < 8; i++) {
                ivec3 childCoord = coord * 2 + offsets[i];
                avgColor += texelFetch(voxelMip[mipLevel-1], childCoord);
                avgDensity += texelFetch(densityMip[mipLevel-1], childCoord).r;
            }
            avgColor /= 8.0;
            avgDensity /= 8.0;
            
            imageStore(voxelMip[mipLevel], coord, avgColor);
            imageStore(densityMip[mipLevel], coord, vec4(avgDensity));
        }
    }
}
```

### 锥追踪（体积版本）

```glsl
// 漫反射锥追踪（5个锥）
vec4 traceDiffuseCone(vec3 origin, vec3 normal) {
    const vec3 coneDirections[5] = {
        normal,
        normalize(normal + tangent),
        normalize(normal - tangent),
        normalize(normal + bitangent),
        normalize(normal - bitangent)
    };
    const float coneWeights[5] = {0.25, 0.15, 0.15, 0.15, 0.15};
    
    vec4 result = vec4(0);
    for(int i = 0; i < 5; i++) {
        result += traceConeVolume(origin, coneDirections[i], 0.577) * coneWeights[i];
    }
    return result;
}

// 单个锥追踪（支持体积累积）
vec4 traceConeVolume(vec3 origin, vec3 direction, float aperture) {
    vec3 color = vec3(0);
    float alpha = 0;
    float dist = voxelSize; // 起始距离
    
    origin += direction * dist; // 避免自相交
    
    while(dist < maxTraceDistance && alpha < 0.95) {
        // Mipmap级别基于锥径
        float diameter = 2.0 * aperture * dist;
        float mipLevel = log2(diameter / voxelSize);
        
        // 采样体素
        vec4 voxelSample = textureLod(voxelGridMip, origin, mipLevel);
        float densitySample = textureLod(densityGridMip, origin, mipLevel).r;
        
        // 体积累积（前向后向混合）
        float stepSize = diameter;
        float transmittance = exp(-densitySample * stepSize * extinctionCoeff);
        
        // 散射内散（In-scattering）
        float scattering = densitySample * scatteringCoeff;
        color += (1.0 - alpha) * scattering * voxelSample.rgb * stepSize;
        
        // 更新不透明度
        alpha += (1.0 - alpha) * (1.0 - transmittance);
        
        // 推进
        dist += stepSize;
        origin += direction * stepSize;
    }
    
    return vec4(color, alpha);
}
```

### 镜面反射锥

```glsl
// 基于粗糙度的镜面锥
vec4 traceSpecularCone(vec3 origin, vec3 reflectDir, float roughness) {
    float aperture = max(0.05, roughness); // 粗糙度→锥角
    return traceConeVolume(origin, reflectDir, aperture);
}
```

### 环境光遮蔽锥

```glsl
// 使用锥追踪计算AO（考虑体积）
float traceAOCone(vec3 origin, vec3 normal) {
    const int numCones = 4;
    float occlusion = 0;
    
    for(int i = 0; i < numCones; i++) {
        vec3 dir = getConeDirection(normal, i, numCones);
        vec4 result = traceConeVolume(origin, dir, 0.6);
        occlusion += result.a; // 累积不透明度
    }
    
    return 1.0 - (occlusion / numCones);
}
```

### 性能优化

#### A. 自适应步进

```glsl
float adaptiveStepSize(float currentDist, float density, float mipLevel) {
    if(density < 0.01) 
        return voxelSize * (1 << int(mipLevel + 1)); // 大步
    else
        return voxelSize * (1 << int(mipLevel));     // 小步
}
```

#### B. 早期终止

```glsl
if(alpha > 0.95) break;
if(dist > maxDistance) break;
if(voxelSample.a < 0.001 && densitySample < 0.001) {
    dist += largeStep; // 跳过空白区域
}
```

### 适用场景

✅ 优势：
- 高质量间接光照（类似离线）
- 统一处理不透明和半透明
- 自然的软阴影和AO
- 支持光泽反射

✅ 特别适合：
- 体积雾与GI结合
- 玻璃、水等半透明材质
- 粒子系统照明
- 次表面散射近似

❌ 限制：
- 内存消耗大（SVO或高分辨率3D纹理）
- 体素分辨率限制细节
- 光泄漏问题
- 需要每帧或增量更新体素

### 实际案例

**NVIDIA"VXGI"**：
- 分辨率：256³ ~ 512³
- Clipmap级联：4-6级
- 性能：3-8ms (1080p, GTX 1080)

**项目扩展**：在"项目2.5: VCT"基础上添加
- 实现时间：+2周
- 关键修改：锥追踪着色器、体素数据结构
- 测试场景：体积雾 + 彩色玻璃 + 间接光照

---

## DDGI + 体数据

### 探针系统扩展

DDGI（Dynamic Diffuse Global Illumination）使用探针网格存储辐照度场，可以扩展支持体积。

### 核心论文与资源

**原始论文**：
- 📄 **"Dynamic Diffuse Global Illumination with Ray-Traced Irradiance Fields"** - Zander Majercik et al. (JCGT 2019)
  - [论文链接](http://jcgt.org/published/0008/02/01/)
  - ⭐ 开放获取，DDGI的完整理论和实现
  - 包含详细的伪代码和参数设置
- 📄 **"Scaling Probe-Based Real-Time Dynamic Global Illumination for Production"** - Majercik et al. (JCGT 2021)
  - [论文链接](http://jcgt.org/published/0010/02/01/)
  - 生产级优化和扩展

**辐照度场基础**：
- 📄 **"Irradiance Gradients"** - Greg Ward, Paul Heckbert (Eurographics Workshop 1992)
  - 辐照度场的理论基础
- 📄 **"Light Field Probes"** - Morgan McGuire et al. (I3D 2017)
  - 探针系统的前身

**八面体映射**：
- 📄 **"Survey of Efficient Representations for Independent Unit Vectors"** - Cigolle et al. (JCGT 2014)
  - [论文链接](http://jcgt.org/published/0003/02/01/)
  - 八面体映射编码原理
- 📄 **"Octahedral Impostors"** - Shopf et al.
  - 实现细节

**实现参考**：
- 💻 **[RTXGI SDK - Official NVIDIA Implementation](https://github.com/NVIDIAGameWorks/RTXGI)**
  - ⭐⭐⭐ 官方SDK，生产级质量
  - 包含D3D12, Vulkan, Unreal, Unity集成
  - MIT许可证，可商用
- 💻 [DDGI Implementation (WebGPU)](https://github.com/maierfelix/dawn-ray-tracing)
  - 现代API实现
- 💻 [Mini DDGI (Educational)](https://github.com/diharaw/hybrid-rendering)
  - 简化版实现，易于学习
- 💻 [Falcor DDGI](https://github.com/NVIDIAGameWorks/Falcor)
  - NVIDIA研究框架中的DDGI实现

**NVIDIA资源**：
- 🎥 **"RTXGI: Scalable Ray Traced Global Illumination"** - NVIDIA DevTalk
  - [YouTube](https://www.youtube.com/watch?v=3NelkAsVdn8)
  - 官方深度讲解
- 📝 **RTXGI Documentation**
  - [官方文档](https://github.com/NVIDIAGameWorks/RTXGI/blob/main/docs/index.md)
  - API使用和最佳实践
- 🎥 **GDC 2020: "Ray Tracing in Unreal Engine"**
  - 包含DDGI在UE中的应用

**视频教程**：
- 🎥 **"Dynamic Diffuse Global Illumination"** - Two Minute Papers
  - [YouTube](https://www.youtube.com/watch?v=qnJvkNXvW_g)
- 🎥 **SIGGRAPH 2019 Talk**
  - Zander Majercik的原始演讲

**引擎集成**：
- **Unreal Engine 5**: Lumen部分使用类似探针技术
- **Unity**: HDRP的Adaptive Probe Volumes
- **Custom Engines**: RTXGI SDK提供集成示例

**博客文章**：
- 📝 **"Implementing DDGI"** - MJP's Blog
  - 实现笔记和陷阱
- 📝 **"DDGI Deep Dive"** - NVIDIA Developer Blog
  - [链接](https://developer.nvidia.com/blog/)

**论文扩展阅读**：
- 📄 **"Precomputed Radiance Transfer"** - Sloan et al. (SIGGRAPH 2002)
  - PRT理论，探针系统的基础
- 📄 **"Real-Time Global Illumination using Precomputed Light Field Probes"** (I3D 2017)
  - 探针方法的另一种实现

### 架构调整

```cpp
struct Probe {
    float3 position;
    
    // 传统DDGI数据（八面体映射）
    Texture2D irradianceMap;    // RGB辐照度
    Texture2D visibilityMap;    // 距离/遮挡
    
    // 新增：体积支持
    Texture2D scatteringMap;    // 体积散射辐照度
    float maxRayDistance;       // 有效半径
};
```

### 实现步骤

#### 1. 探针射线追踪（穿透体积）

```glsl
// 每个探针发射多条射线
void updateProbe(int probeIndex) {
    Probe probe = probes[probeIndex];
    const int raysPerProbe = 128;
    
    for(int i = 0; i < raysPerProbe; i++) {
        // 生成随机方向（球面分布）
        vec3 rayDir = randomHemisphere();
        vec3 rayOrigin = probe.position;
        
        // 光线追踪（考虑体积）
        vec3 radiance = vec3(0);
        float transmittance = 1.0;
        bool hitSurface = false;
        float t = 0;
        
        // 步进穿过体积
        while(t < maxRayDistance && transmittance > 0.01) {
            float stepSize = getAdaptiveStepSize(t);
            t += stepSize;
            vec3 samplePos = rayOrigin + rayDir * t;
            
            // 采样体积密度
            float density = sampleVolumeDensity(samplePos);
            
            if(density > 0.001) {
                // 体积散射贡献
                vec3 volumeEmission = getVolumeEmission(samplePos);
                vec3 volumeScattering = getVolumeScattering(samplePos, rayDir);
                
                float extinction = density * extinctionCoeff;
                float scattering = density * scatteringCoeff;
                
                radiance += transmittance * (volumeEmission + scattering * volumeScattering) * stepSize;
                transmittance *= exp(-extinction * stepSize);
            }
            
            // 检查表面相交
            RayHit hit = traceRay(rayOrigin, rayDir, t, t + stepSize);
            if(hit.valid) {
                // 表面贡献
                vec3 surfaceRadiance = shadeSurface(hit);
                radiance += transmittance * surfaceRadiance;
                hitSurface = true;
                break;
            }
        }
        
        // 存储到八面体映射
        vec2 octCoord = directionToOctahedral(rayDir);
        storeProbeRadiance(probeIndex, octCoord, radiance);
    }
}
```

#### 2. 时域混合（考虑体积稳定性）

```glsl
// 历史帧混合
vec3 blendHistory(vec3 newRadiance, vec3 historyRadiance, float variance) {
    // 体积变化快，使用较高的混合速度
    float blendWeight = variance > threshold ? 0.2 : 0.05;
    return mix(historyRadiance, newRadiance, blendWeight);
}
```

#### 3. 体积采样（查询探针）

```glsl
// 从体积中的点采样DDGI
vec3 sampleDDGI_Volume(vec3 worldPos, vec3 normal) {
    // 找到8个最近探针
    int nearestProbes[8];
    float weights[8];
    findNearestProbes(worldPos, nearestProbes, weights);
    
    vec3 irradiance = vec3(0);
    
    for(int i = 0; i < 8; i++) {
        Probe probe = probes[nearestProbes[i]];
        
        // 计算方向（探针→采样点）
        vec3 dir = normalize(worldPos - probe.position);
        
        // 采样八面体映射
        vec2 octCoord = directionToOctahedral(dir);
        vec3 probeRadiance = texture(probe.irradianceMap, octCoord).rgb;
        
        // 可见性权重（避免错误的光泄漏）
        float visibility = texture(probe.visibilityMap, octCoord).r;
        float dist = length(worldPos - probe.position);
        float visWeight = max(0, 1.0 - dist / visibility);
        
        // 累积
        irradiance += probeRadiance * weights[i] * visWeight;
    }
    
    // 应用相位函数（简化）
    return irradiance / (4.0 * PI);
}
```

#### 4. 可见性处理（体积遮挡）

```glsl
// 更新可见性图（考虑体积）
float updateVisibility(vec3 probePos, vec3 rayDir, float hitDistance) {
    // 积累透射率
    float transmittance = 1.0;
    float t = 0;
    
    while(t < hitDistance) {
        vec3 pos = probePos + rayDir * t;
        float density = sampleVolumeDensity(pos);
        transmittance *= exp(-density * extinctionCoeff * stepSize);
        t += stepSize;
    }
    
    // 有效距离 = 物理距离 * 透射率
    return hitDistance * transmittance;
}
```

### 性能考虑

#### 探针密度

体积需要更密集的探针（3D覆盖）：
- **表面GI**：探针沿表面分布，稀疏
- **体积GI**：探针需填充3D空间，密集

```cpp
// 自适应探针密度
void placeProbes() {
    // 高密度体积区域
    for(vec3 pos : volumeRegions) {
        if(hasHighDensity(pos)) {
            addProbe(pos, highDensitySpacing); // 如 1m
        }
    }
    
    // 低密度或空白区域
    for(vec3 pos : lowDensityRegions) {
        addProbe(pos, lowDensitySpacing); // 如 4m
    }
}
```

#### 更新策略

```cpp
// 轮询更新（每帧只更新一部分探针）
int probesPerFrame = totalProbes / 8; // 8帧更新一轮
for(int i = 0; i < probesPerFrame; i++) {
    int probeIndex = (frameCount * probesPerFrame + i) % totalProbes;
    updateProbe(probeIndex);
}
```

### 适用场景

✅ 优势：
- 动态体积雾 + 动态GI
- 探针自然处理多次散射
- 高质量、低噪声
- 时域稳定

❌ 限制：
- 探针数量需求大（体积覆盖）
- 内存和更新开销高
- 实现复杂度高

### 实际案例

**UE5 Lumen**：
- 使用Screen Probes（屏幕空间探针）+ World Probes
- 体积雾通过Froxel系统单独处理，然后与探针结合
- 性能：2-4ms (探针更新) + 1-2ms (体积计算)

**项目扩展**：在"项目3.2: DDGI"基础上添加
- 实现时间：+3-4周
- 关键挑战：探针密度、光线步进、性能优化
- 测试场景：动态光源 + 动态雾 + 复杂场景

---

## ReSTIR + 体数据

### 背景

ReSTIR（Reservoir-based Spatiotemporal Importance Resampling）是一种强大的采样技术，可以扩展到体积光传输。

### 核心论文与资源

**原始论文**：
- 📄 **"Spatiotemporal reservoir resampling for real-time ray tracing with dynamic direct lighting"** - Bitterli et al. (ACM TOG/SIGGRAPH 2020)
  - [论文链接](https://doi.org/10.1145/3386569.3392481)
  - ⭐⭐⭐ ReSTIR的原始论文，必读
  - 包含完整算法和伪代码
- 📄 **"Rearchitecting Spatiotemporal Resampling for Production"** - Wyman et al. (HPG 2021)
  - [论文链接](https://doi.org/10.2312/hpg.20211282)
  - 解决原始算法的偏差问题

**理论基础**：
- 📄 **"Optimally Combining Sampling Techniques for Monte Carlo Rendering"** - Veach & Guibas (SIGGRAPH 1995)
  - 多重重要性采样（MIS）的理论基础
- 📄 **"Resampled Importance Sampling (RIS)"** - Talbot et al. (Eurographics 2005)
  - RIS算法的数学原理

**ReSTIR扩展**：
- 📄 **"ReSTIR GI: Path Resampling for Real-Time Path Tracing"** - Ouyang et al. (Computer Graphics Forum 2021)
  - [论文链接](https://doi.org/10.1111/cgf.14378)
  - 扩展到间接光照
- 📄 **"Generalized Resampled Importance Sampling: Foundations of ReSTIR"** - Bitterli et al. (ACM TOG 2022)
  - [论文链接](https://doi.org/10.1145/3528223.3530127)
  - 统一的理论框架
- 📄 **"ReSTIR PT: Path Reusing for Real-Time Path Tracing"** - Lin et al. (SIGGRAPH Asia 2023)
  - 扩展到完整路径追踪

**体积相关**：
- 📄 **"Neural Importance Sampling for Participating Media"** (SIGGRAPH Asia 2023)
  - ReSTIR在体积中的应用探索
- 📄 **"Reservoir-Based Spatiotemporal Importance Resampling for Participating Media"** - 研究进行中
  - 体积散射的ReSTIR

**实现参考**：
- 💻 **[RTXDI SDK - Official NVIDIA Implementation](https://github.com/NVIDIAGameWorks/RTXDI)**
  - ⭐⭐⭐ NVIDIA官方ReSTIR DI实现
  - 生产级质量，包含优化和最佳实践
  - D3D12和Vulkan支持
- 💻 [ReSTIR Implementation (Educational)](https://github.com/DQLin/ReSTIR_PT)
  - ReSTIR PT的参考实现
- 💻 [Falcor ReSTIR](https://github.com/NVIDIAGameWorks/Falcor)
  - NVIDIA研究框架中的ReSTIR
- 💻 [Mini Path Tracer with ReSTIR](https://github.com/wiwiwuwuwa/path_tracer)
  - 简化版实现

**NVIDIA资源**：
- 🎥 **"Spatiotemporal Reservoir Resampling (ReSTIR)"** - NVIDIA GTC Talk
  - [YouTube](https://www.youtube.com/results?search_query=restir+nvidia)
  - Benedikt Bitterli的官方讲解
- 📝 **RTXDI Documentation**
  - [官方文档](https://github.com/NVIDIAGameWorks/RTXDI/tree/main/doc)
  - 包含集成指南和性能调优
- 🎥 **GDC 2021: "ReSTIR in Production"**
  - 生产环境的经验分享

**视频教程**：
- 🎥 **"ReSTIR: Real-Time Ray Tracing"** - Two Minute Papers
  - [YouTube](https://www.youtube.com/watch?v=11O8vrzT2VQ)
  - 可视化效果展示
- 🎥 **SIGGRAPH 2020 Technical Papers Preview**
  - 原始论文的视频摘要

**博客文章**：
- 📝 **"Understanding ReSTIR"** - Chris Wyman's Blog
  - [链接](https://cwyman.org/)
  - 算法详解和实现笔记
- 📝 **"ReSTIR Deep Dive"** - Activision Research
  - 《使命召唤》中的ReSTIR应用
- 📝 **"Implementing ReSTIR DI"** - RayTracingGems.com
  - [Ray Tracing Gems II](https://www.realtimerendering.com/raytracinggems/rtg2/index.html)
  - Chapter 22

**开源游戏引擎**：
- **Unreal Engine 5**: Lumen考虑集成ReSTIR
- **Custom Engines**: RTXDI SDK提供完整集成

**论文代码**：
- 💻 [ReSTIR GI Official Code](https://research.nvidia.com/labs/rtr/publication/ouyang2021restir/)
  - 论文作者发布的代码

### 核心概念

**传统ReSTIR DI**（直接光照）:
- 每像素存储一个Reservoir
- 时空重用光源样本
- 1-2 spp达到高质量

**ReSTIR for Volumes**:
- 体积样本点也使用Reservoir
- 考虑相位函数的PDF
- 处理体积散射的时空重用

### 数据结构

```cpp
struct VolumeReservoir {
    int selectedLightID;        // 被选中的光源ID
    float3 lightSamplePos;      // 光源采样位置
    float weight;               // Reservoir权重 W
    int M;                      // 观测样本数
    float3 targetPDF;           // 目标PDF（用于MIS）
};
```

### 实现步骤

#### 1. 初始采样（Initial Sampling）

```glsl
// 为体积样本点生成候选光源
VolumeReservoir initialSampling(vec3 volumePos, vec3 viewDir, int numCandidates) {
    VolumeReservoir reservoir = createEmpty();
    
    for(int i = 0; i < numCandidates; i++) {
        // 随机选择光源
        int lightID = randomLightSelection();
        Light light = lights[lightID];
        
        // 采样光源
        vec3 lightSamplePos;
        vec3 lightIntensity;
        sampleLight(light, volumePos, lightSamplePos, lightIntensity);
        
        // 计算贡献（目标函数）
        vec3 lightDir = normalize(lightSamplePos - volumePos);
        float phase = phaseHG(dot(-viewDir, lightDir), anisotropy);
        float density = sampleVolumeDensity(volumePos);
        
        vec3 contribution = lightIntensity * phase * density;
        float targetPDF = luminance(contribution);
        
        // 更新Reservoir
        float weight = targetPDF / (selectionPDF * numCandidates);
        updateReservoir(reservoir, lightID, lightSamplePos, weight);
    }
    
    return reservoir;
}
```

#### 2. 时域重用（Temporal Reuse）

```glsl
// 从历史帧重用
VolumeReservoir temporalReuse(vec3 currentPos, VolumeReservoir currentReservoir) {
    // 重投影到历史帧
    vec3 historyPos = reprojectToHistory(currentPos, motionVector);
    VolumeReservoir historyReservoir = sampleHistoryReservoir(historyPos);
    
    // Disocclusion检测
    if(isDisoccluded(currentPos, historyPos)) {
        return currentReservoir; // 不重用
    }
    
    // 验证历史样本
    vec3 lightDir = normalize(historyReservoir.lightSamplePos - currentPos);
    
    // 计算当前位置的目标PDF
    float phase = phaseHG(dot(-viewDir, lightDir), anisotropy);
    float density = sampleVolumeDensity(currentPos);
    vec3 lightIntensity = evaluateLight(historyReservoir.selectedLightID, currentPos);
    vec3 contribution = lightIntensity * phase * density;
    float targetPDF = luminance(contribution);
    
    // 合并Reservoir
    float weight = targetPDF * historyReservoir.M;
    updateReservoir(currentReservoir, 
                    historyReservoir.selectedLightID, 
                    historyReservoir.lightSamplePos, 
                    weight);
    currentReservoir.M += historyReservoir.M;
    
    // Clamp M防止过度重用
    currentReservoir.M = min(currentReservoir.M, 20 * numInitialCandidates);
    
    return currentReservoir;
}
```

#### 3. 空间重用（Spatial Reuse）

```glsl
// 从邻域重用
VolumeReservoir spatialReuse(vec3 currentPos, VolumeReservoir currentReservoir, 
                              int numSpatialSamples) {
    for(int i = 0; i < numSpatialSamples; i++) {
        // 采样邻域（3D）
        vec3 neighborPos = currentPos + randomOffset3D(searchRadius);
        VolumeReservoir neighborReservoir = sampleReservoir(neighborPos);
        
        // 可见性验证（光线追踪到光源）
        if(!isVisible(currentPos, neighborReservoir.lightSamplePos)) {
            continue; // 跳过不可见样本
        }
        
        // 密度相似性检查（防止从不同密度区域重用）
        float currentDensity = sampleVolumeDensity(currentPos);
        float neighborDensity = sampleVolumeDensity(neighborPos);
        if(abs(currentDensity - neighborDensity) > densityThreshold) {
            continue;
        }
        
        // 重新评估邻域样本
        vec3 lightDir = normalize(neighborReservoir.lightSamplePos - currentPos);
        float phase = phaseHG(dot(-viewDir, lightDir), anisotropy);
        vec3 lightIntensity = evaluateLight(neighborReservoir.selectedLightID, currentPos);
        vec3 contribution = lightIntensity * phase * currentDensity;
        float targetPDF = luminance(contribution);
        
        // 合并
        float weight = targetPDF * neighborReservoir.M;
        updateReservoir(currentReservoir, 
                        neighborReservoir.selectedLightID, 
                        neighborReservoir.lightSamplePos, 
                        weight);
    }
    
    return currentReservoir;
}
```

#### 4. 最终着色

```glsl
// 使用最终Reservoir着色
vec3 shadeWithReservoir(vec3 volumePos, vec3 viewDir, VolumeReservoir reservoir) {
    if(reservoir.selectedLightID < 0) return vec3(0);
    
    // 评估选中的光源
    Light light = lights[reservoir.selectedLightID];
    vec3 lightIntensity = evaluateLight(light, volumePos, reservoir.lightSamplePos);
    
    // 相位函数
    vec3 lightDir = normalize(reservoir.lightSamplePos - volumePos);
    float phase = phaseHG(dot(-viewDir, lightDir), anisotropy);
    
    // 密度
    float density = sampleVolumeDensity(volumePos);
    
    // 可见性
    float visibility = traceShadowRay(volumePos, reservoir.lightSamplePos);
    
    // 最终贡献
    vec3 radiance = lightIntensity * phase * density * visibility;
    
    // 应用Reservoir权重（无偏估计）
    return radiance * reservoir.weight / max(reservoir.M, 1);
}
```

### 偏差校正（Bias Correction）

体积中的时空重用会引入偏差，需要校正：

```glsl
// Jacobian校正（处理运动物体）
float computeJacobian(vec3 currentPos, vec3 historyPos, vec3 lightPos) {
    float currentDist = length(lightPos - currentPos);
    float historyDist = length(lightPos - historyPos);
    
    // 距离平方衰减的Jacobian
    return (historyDist * historyDist) / (currentDist * currentDist);
}

// 在temporalReuse中应用
weight *= computeJacobian(currentPos, historyPos, historyReservoir.lightSamplePos);
```

### 性能特点

- **初始采样**：32-64个候选光源/样本点
- **时域重用**：M通常累积到200-500
- **空间重用**：5-8个邻域样本
- **总开销**：2-4ms (1080p, 体积分辨率128³)

### 适用场景

✅ 优势：
- 大量动态光源的体积散射
- 低样本数（1-2 spp）
- 高质量、低噪声
- 适合实时应用

✅ 特别适合：
- 火焰、爆炸等自发光体积
- 数千点光源的场景
- 复杂异质介质

❌ 限制：
- 实现复杂度极高
- 偏差问题需要仔细处理
- 需要运动向量和历史缓冲
- 空间重用的可见性验证开销大

### 前沿研究

**ReSTIR PT for Participating Media** (SIGGRAPH 2023):
- 扩展到完整路径追踪
- 处理多次散射
- 路径重用策略

**项目扩展**：在"项目3.3: ReSTIR DI"基础上添加
- 实现时间：+4-6周
- 前置知识：ReSTIR DI + 体渲染基础
- 测试场景：多光源 + 体积雾

---

## 体数据专用技术

除了改造表面GI技术，还有专门为体积设计的方法。

### 1. Deep Shadow Maps (DSM)

**概念**：存储沿光线的透射率函数，而非单一深度。

#### 核心论文与资源

**原始论文**：
- 📄 **"Deep Shadow Maps"** - Tom Lokovic, Eric Veach (SIGGRAPH 2000)
  - [论文链接](https://graphics.pixar.com/library/DeepShadows/)
  - ⭐ Pixar提出，用于《怪兽电力公司》
  - 体积阴影的经典方法
- 📄 **"Opacity Shadow Maps"** - Kim & Neumann (Rendering Techniques 2001)
  - 另一种体积阴影表示

**压缩技术**：
- 📄 **"Adaptive Volumetric Shadow Maps"** - Salvi et al. (EGSR 2010)
  - [论文链接](https://doi.org/10.2312/EGSR/EGSR10/385-394)
  - AVSM算法，更高效的存储
- 📄 **"Deep Opacity Maps"** - Yuksel & Keyser (Computer Graphics Forum 2008)
  - 分段线性压缩

**实现参考**：
- 💻 [Deep Shadow Maps Tutorial](https://github.com/search?q=deep+shadow+maps)
  - 多个教育性实现
- 💻 [AVSM Implementation](https://github.com/TheRealMJP/Shadows)
  - ⭐ MJP的完整阴影技术合集，包含AVSM
- 📝 **"Deep Shadow Maps"** - Pixar's RenderMan Documentation
  - [文档链接](https://rmanwiki.pixar.com/)

**视频**：
- 🎥 **"Volumetric Shadows in Production"** - Pixar SIGGRAPH Course
  - Pixar的实际应用经验

**数据结构**：
```cpp
struct DeepPixel {
    std::vector<float> depths;          // 深度样本
    std::vector<float> transmittances;  // 对应透射率
};

// 压缩存储（分段线性函数）
struct CompressedDSM {
    float4 segments[8]; // (depth, transmittance)
};
```

**生成**：
```glsl
// 从光源视角光线步进
void generateDSM(vec3 lightPos, vec3 lightDir) {
    for(int pixel = 0; pixel < shadowMapSize; pixel++) {
        vec3 rayOrigin = lightPos;
        vec3 rayDir = getRayDirection(pixel);
        
        float transmittance = 1.0;
        float t = 0;
        
        DeepPixel deepPixel;
        
        while(t < maxDistance) {
            float density = sampleVolumeDensity(rayOrigin + rayDir * t);
            transmittance *= exp(-density * stepSize * extinctionCoeff);
            
            // 记录关键点（透射率变化显著时）
            if(shouldRecord(transmittance)) {
                deepPixel.depths.push_back(t);
                deepPixel.transmittances.push_back(transmittance);
            }
            
            t += stepSize;
        }
        
        storeDSM(pixel, deepPixel);
    }
}
```

**查询**：
```glsl
// 查询任意点的阴影
float queryDSM(vec3 worldPos, vec3 lightPos) {
    // 投影到shadow map
    vec2 shadowUV = projectToLightSpace(worldPos, lightPos);
    float depth = length(worldPos - lightPos);
    
    // 查询Deep Shadow Map
    DeepPixel deepPixel = sampleDSM(shadowUV);
    
    // 插值透射率
    return interpolateTransmittance(deepPixel, depth);
}
```

**优势**：
- 一次生成，多次查询
- 支持半透明阴影
- 比实时光线步进快

**限制**：
- 内存占用大
- 压缩质量 vs 存储权衡
- 动态体积需要每帧更新

---

### 2. Volumetric Lightmaps

**概念**：预计算3D体积中的辐照度，类似传统2D lightmap。

#### 核心论文与资源

**理论基础**：
- 📄 **"Irradiance Volumes for Games"** - Greger et al. (EGSR 1998)
  - 体积辐照度场的早期应用
- 📄 **"Real-Time Radiance Caching using Chrominance Compression"** - Krivanek et al. (JCGT 2014)
  - 辐照度缓存技术

**引擎实现**：
- 📝 **Unreal Engine 4: Volumetric Lightmaps**
  - [官方文档](https://docs.unrealengine.com/4.27/en-US/BuildingWorlds/LightingAndShadows/VolumetricLightmaps/)
  - UE4的完整实现
- 📝 **Unity: Light Probes**
  - [官方文档](https://docs.unity3d.com/Manual/LightProbes.html)
  - 类似概念，探针系统
- 📝 **Godot: GI Probes**
  - [文档](https://docs.godotengine.org/en/stable/tutorials/3d/gi_probes.html)

**实现参考**：
- 💻 [Volumetric Lightmap Baker](https://github.com/search?q=volumetric+lightmap)
  - 离线烘焙工具
- 📝 **"Implementing Volumetric Lightmaps"** - UE4 Source Code
  - `Engine/Source/Runtime/Renderer/Private/VolumetricLightmap.cpp`

**视频教程**：
- 🎥 **"UE4 Volumetric Lightmaps Tutorial"**
  - [YouTube](https://www.youtube.com/results?search_query=ue4+volumetric+lightmap)
- 🎥 **"Light Probes Explained"**
  - Unity官方教程

**烘焙流程**：
```cpp
// 离线烘焙
void bakeVolumetricLightmap() {
    // 均匀网格或八叉树
    for(vec3 probePos : volumeGrid) {
        // 半球积分（蒙特卡洛）
        vec3 irradiance = vec3(0);
        for(int i = 0; i < numSamples; i++) {
            vec3 dir = randomHemisphere();
            
            // 光线追踪（离线，可用路径追踪）
            vec3 Li = traceRayOffline(probePos, dir);
            irradiance += Li * dot(normal, dir);
        }
        irradiance /= numSamples;
        
        storeProbe(probePos, irradiance);
    }
}
```

**运行时查询**：
```glsl
vec3 sampleVolumetricLightmap(vec3 worldPos) {
    // 三线性插值
    return trilinearInterpolate(volumeLightmap, worldPos);
}
```

**优势**：
- 运行时开销极低（纹理采样）
- 高质量（离线计算）
- 支持任意复杂光传输

**限制**：
- 仅静态场景
- 内存占用大（3D纹理）
- 不支持动态光源

---

### 3. Froxel-based GI

**Froxel** = Frustum Voxel（视锥体素）

**概念**：相机视锥内的3D网格，逐帧累积体积散射。

#### 核心论文与资源

**原始论文**：
- 📄 **"Real-Time Volumetric Cloudscapes"** - Schneider & Vos (GPU Pro 7, SIGGRAPH 2015)
  - [论文链接](https://www.guerrilla-games.com/read/nubis-realtime-volumetric-cloudscapes)
  - ⭐⭐⭐ Guerrilla Games（《地平线：零之曙光》）
  - Froxel方法的奠基之作
- 📄 **"Physically Based Sky, Atmosphere and Cloud Rendering"** - Hillaire (SIGGRAPH 2020 Course)
  - [Course Notes](https://sebh.github.io/publications/)
  - Frostbite的体积渲染

**Unreal Engine实现**：
- 📄 **"Volumetric Fog in Unreal Engine 4"** - Epic Games
  - [Official Blog](https://www.unrealengine.com/en-US/tech-blog)
  - UE4.16+的体积雾系统
- 💻 **UE4/UE5 Source Code**
  - `Engine/Shaders/Private/VolumetricFog.usf`
  - `Engine/Source/Runtime/Renderer/Private/VolumetricFog.cpp`
  - [GitHub](https://github.com/EpicGames/UnrealEngine)（需要Epic账号）

**Frostbite实现**：
- 📄 **"The Rendering of Uncharted 4"** - EA/DICE (SIGGRAPH 2016)
  - Frostbite引擎的体积光照
- 🎥 **"Physically Based Sky, Atmosphere and Cloud Rendering in Frostbite"**
  - [Slides](https://media.contentapi.ea.com/content/dam/eacom/frostbite/files/s2016-pbs-frostbite-sky-clouds-new.pdf)
  - Sébastien Hillaire的详细讲解

**Unity HDRP实现**：
- 📝 **"Volumetric Lighting in HDRP"**
  - [官方文档](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@latest)
- 💻 [HDRP Source Code](https://github.com/Unity-Technologies/Graphics)
  - `com.unity.render-pipelines.high-definition/Runtime/Lighting/Volumetrics/`

**实现参考**：
- 💻 [Froxel-based Volumetric Fog](https://github.com/search?q=froxel+volumetric)
  - 多个开源实现
- 💻 [Volumetric Lighting Unity](https://github.com/SlightlyMad/VolumetricLights)
  - Unity插件实现
- 💻 [WebGL Volumetric Lighting](https://github.com/wwwtyro/glsl-atmosphere)
  - Web端参考

**视频教程**：
- 🎥 **"Volumetric Fog - Behind the Scenes"** - Unreal Engine
  - [YouTube](https://www.youtube.com/watch?v=VHmpdRRWPxU)
- 🎥 **"Real-Time Volumetric Cloudscapes"** - GDC Talk
  - Guerrilla Games的演讲
- 🎥 **SIGGRAPH 2015 Presentation**
  - [视频链接](https://www.youtube.com/results?search_query=real+time+volumetric+cloudscapes)

**博客文章**：
- 📝 **"Volumetric Fog in UE4"** - Ryan Brucks (Epic Games)
  - 实现细节和性能分析
- 📝 **"Froxel-based Volumetric Rendering"** - Alex Tardif
  - [Blog](https://www.alextardif.com/)

**时域技术**：
- 📄 **"Temporal Reprojection Anti-Aliasing"** - SIGGRAPH 2014
  - 时域累积的理论基础
- 📄 **"A Survey of Temporal Antialiasing Techniques"** - Lei Yang et al. (2020)
  - [论文PDF](https://arxiv.org/abs/2006.02977)

**网格生成**：
```cpp
// 初始化Froxel网格
struct FroxelGrid {
    int3 resolution;  // 如 (160, 90, 64)
    float nearPlane;
    float farPlane;
    Texture3D scattering;      // 散射辐射度
    Texture3D transmittance;   // 透射率
};

vec3 froxelToWorld(int3 coord, FroxelGrid grid) {
    // 线性深度或对数深度
    float depth = grid.nearPlane * pow(grid.farPlane / grid.nearPlane, 
                                       coord.z / float(grid.resolution.z));
    vec2 ndc = (vec2(coord.xy) / grid.resolution.xy) * 2.0 - 1.0;
    return reconstructWorldPos(ndc, depth);
}
```

**散射注入**：
```glsl
// Compute Shader - 注入光源散射
[numthreads(8, 8, 1)]
void InjectLighting(uint3 dispatchThreadID : SV_DispatchThreadID) {
    uint3 froxelCoord = dispatchThreadID;
    vec3 worldPos = froxelToWorld(froxelCoord, froxelGrid);
    
    float density = sampleVolumeDensity(worldPos);
    if(density < 0.001) return;
    
    vec3 scattering = vec3(0);
    
    // 累积所有光源
    for(int i = 0; i < numLights; i++) {
        Light light = lights[i];
        vec3 lightDir = normalize(light.position - worldPos);
        float dist = length(light.position - worldPos);
        
        // 阴影
        float visibility = sampleShadowMap(worldPos, light);
        
        // 相位函数
        float phase = phaseHG(dot(-viewDir, lightDir), anisotropy);
        
        // 贡献
        vec3 lightIntensity = light.color * light.intensity / (dist * dist);
        scattering += lightIntensity * phase * visibility;
    }
    
    // 存储
    froxelGrid.scattering[froxelCoord] = scattering * density;
}
```

**光线行进积分**：
```glsl
// 最终渲染
vec4 renderVolumetricFog(vec3 rayOrigin, vec3 rayDir, float rayLength) {
    vec3 scatteredLight = vec3(0);
    float transmittance = 1.0;
    
    // 沿Froxel网格步进
    for(int i = 0; i < froxelGrid.resolution.z; i++) {
        float t = froxelDepth(i);
        if(t > rayLength) break;
        
        vec3 worldPos = rayOrigin + rayDir * t;
        
        // 采样Froxel
        vec3 scattering = sampleFroxel(froxelGrid.scattering, worldPos);
        float extinction = sampleFroxel(froxelGrid.extinction, worldPos);
        
        float stepSize = froxelDepth(i+1) - t;
        
        // 累积
        scatteredLight += transmittance * scattering * stepSize;
        transmittance *= exp(-extinction * stepSize);
    }
    
    return vec4(scatteredLight, 1.0 - transmittance);
}
```

**时域累积**：
```glsl
// 历史帧混合
vec3 blendHistory(vec3 current, vec3 history, float blendFactor) {
    return mix(history, current, blendFactor);
}

// 主循环
froxelGrid.scattering = blendHistory(
    newScattering, 
    reprojectHistory(froxelGrid.scattering, motionVector), 
    0.1
);
```

**优势**：
- 与相机空间对齐（高效）
- 自然处理屏幕空间效果
- 逐帧累积（时域稳定）
- UE4/UE5采用

**性能**：
- 分辨率：160×90×64
- 注入：1-2ms
- 光线行进：1-2ms
- 总计：<3ms (1080p)

---

### 4. Photon Beams

**概念**：光子映射的体积版本，光子存储为线段（beams）而非点。

#### 核心论文与资源

**原始论文**：
- 📄 **"The Beam Radiance Estimate for Volumetric Photon Mapping"** - Jarosz et al. (Computer Graphics Forum 2008)
  - [论文链接](https://cs.dartmouth.edu/~wjarosz/publications/jarosz08beam.html)
  - ⭐ Photon Beams的原始论文
- 📄 **"Progressive Photon Beams"** - Jarosz et al. (SIGGRAPH Asia 2011)
  - [论文链接](https://cs.dartmouth.edu/~wjarosz/publications/jarosz11progressive.html)
  - 渐进式改进

**理论基础**：
- 📄 **"Realistic Image Synthesis Using Photon Mapping"** - Henrik Wann Jensen (2001)
  - 📚 经典教材，光子映射基础
- 📄 **"A Practical Guide to Global Illumination using Photon Mapping"** - Jensen (SIGGRAPH 2000 Course)
  - [Course Notes](https://graphics.stanford.edu/courses/cs348b-00/)

**扩展研究**：
- 📄 **"Comprehensive Theory of Volumetric Radiance Estimation using Photon Points and Beams"** - Jarosz et al. (ACM TOG 2011)
  - [论文链接](https://cs.dartmouth.edu/~wjarosz/publications/jarosz11points.html)
  - 统一理论框架
- 📄 **"Bidirectional Photon Beams"** - Vorba & Křivánek (SIGGRAPH Asia 2016)
  - 双向光子束

**实现参考**：
- 💻 [SmallPPM](https://github.com/xelatihy/smallppm)
  - 小型PPM实现，可扩展到beams
- 💻 [PBRT Photon Mapping](https://github.com/mmp/pbrt-v3)
  - PBRT中的光子映射（可参考）
- 💻 [Mitsuba Renderer](https://github.com/mitsuba-renderer/mitsuba3)
  - 支持多种光子映射变体

**Wojciech Jarosz的资源**：
- 📝 **Personal Website**
  - [https://cs.dartmouth.edu/~wjarosz/](https://cs.dartmouth.edu/~wjarosz/)
  - 论文、代码、补充材料
- 📄 **PhD Thesis: "Efficient Monte Carlo Methods for Light Transport in Scattering Media"**
  - [完整论文](https://cs.dartmouth.edu/~wjarosz/publications/dissertation/)
  - 体积渲染的全面讲解

**视频**：
- 🎥 **"Photon Beams Explained"** - Dartmouth
  - 论文作者的演讲
- 🎥 **SIGGRAPH Talks**
  - 相关技术讲解

**光子发射**：
```cpp
struct PhotonBeam {
    vec3 start;
    vec3 end;
    vec3 power;
    float radius;
};

void emitPhotonBeams() {
    for(int i = 0; i < numPhotons; i++) {
        // 从光源发射
        vec3 pos = sampleLightPosition();
        vec3 dir = sampleLightDirection();
        vec3 power = lightPower / numPhotons;
        
        // 光线步进穿过体积
        vec3 beamStart = pos;
        while(true) {
            float density = sampleVolumeDensity(pos);
            
            // 俄罗斯轮盘赌
            if(random() < density * scatteringCoeff) {
                // 散射事件
                PhotonBeam beam;
                beam.start = beamStart;
                beam.end = pos;
                beam.power = power;
                beam.radius = beamRadius;
                storeBeam(beam);
                
                // 改变方向（相位函数采样）
                dir = samplePhaseFunction(dir, anisotropy);
                power *= albedo;
                beamStart = pos;
            }
            
            pos += dir * stepSize;
            
            if(hitGeometry || outOfBounds) break;
        }
    }
}
```

**渲染时查询**：
```glsl
vec3 estimateRadiance(vec3 worldPos, vec3 viewDir) {
    // 查询附近的photon beams
    PhotonBeam beams[K] = kNearestBeams(worldPos, searchRadius);
    
    vec3 radiance = vec3(0);
    for(int i = 0; i < K; i++) {
        // Beam到点的距离
        float dist = distanceToLine(worldPos, beams[i].start, beams[i].end);
        
        // 核密度估计
        float kernel = epanechnikovKernel(dist, beams[i].radius);
        
        // 相位函数
        vec3 beamDir = normalize(beams[i].end - beams[i].start);
        float phase = phaseHG(dot(-viewDir, beamDir), anisotropy);
        
        radiance += beams[i].power * phase * kernel;
    }
    
    // 归一化
    return radiance / (searchVolume * K);
}
```

**优势**：
- 高效处理单次散射
- 比体积光子映射更准确
- 适合细长几何（如光束）

**限制**：
- 仍然是有偏估计
- KD-tree查询开销
- 多次散射需要更多技术

---

## 混合方案架构

实际生产中，往往结合多种技术。

### 推荐架构

```
实时体积GI系统
│
├── Layer 1: 近场高频细节 (< 50m)
│   ├── Froxel Grid (160×90×64)
│   │   ├── 直接光照注入
│   │   ├── 时域累积
│   │   └── 运行时：2-3ms
│   └── 用途：主相机视野内的雾、烟雾
│
├── Layer 2: 中场间接光照 (50-500m)
│   ├── LPV (64³ 或级联)
│   │   ├── RSM注入
│   │   ├── 4-6次传播
│   │   └── 运行时：1-2ms
│   └── 用途：大范围间接光照、多次散射近似
│
├── Layer 3: 高质量增强 (选择性)
│   ├── DDGI Probes (稀疏网格)
│   │   ├── 关键区域高密度探针
│   │   ├── 轮询更新
│   │   └── 运行时：2-3ms
│   └── 用途：室内空间、重要区域
│
├── Layer 4: 静态预计算
│   ├── Volumetric Lightmap
│   │   ├── 离线烘焙
│   │   └── 运行时：<0.5ms (采样)
│   └── 用途：静态大气、天空散射
│
└── 降噪与合成
    ├── 时域抗闪烁
    ├── 空间滤波
    └── 与表面GI统一合成
```

### 数据流

```
光源变化
    ↓
[RSM生成] (1ms)
    ↓
    ├─→ [注入Froxel] (1ms)
    │       ↓
    │   [时域累积] (0.5ms)
    │       ↓
    │   [光线行进] (1-2ms)
    │       ↓
    │   近场体积散射
    │
    ├─→ [注入LPV] (0.5ms)
    │       ↓
    │   [传播4-6次] (1-2ms)
    │       ↓
    │   中场间接光照
    │
    └─→ [更新DDGI] (轮询, 2ms/N)
            ↓
        高质量区域增强
            ↓
        [合成所有层]
            ↓
        最终体积渲染
```

### 切换策略

```cpp
// 运行时自适应
void selectGIMethod(SceneContext ctx) {
    if(ctx.isIndoor && ctx.hasRTSupport) {
        use_DDGI();
    } else if(ctx.isDynamic) {
        use_Froxel_Plus_LPV();
    } else {
        use_Volumetric_Lightmap();
    }
    
    // 性能预算
    if(ctx.fps < 30) {
        reduce_Froxel_Resolution();
        reduce_LPV_Propagation_Iterations();
    }
}
```

### 质量级别

```cpp
enum QualityLevel {
    LOW,    // Froxel 80×45×32 + LPV 32³
    MEDIUM, // Froxel 160×90×64 + LPV 64³
    HIGH,   // 上述 + DDGI稀疏探针
    ULTRA   // 上述 + 更高分辨率 + 更多传播
};
```

### 性能预算（1080p, RTX 3080）

| 技术组合 | 时间 (ms) | 质量 | 适用场景 |
|---------|----------|------|---------|
| Froxel Only | 2-3 | 中 | 轻量级雾效 |
| Froxel + LPV | 4-5 | 高 | 开放世界 |
| Froxel + DDGI | 5-7 | 极高 | 室内场景 |
| 全混合 | 7-10 | 最高 | 展示模式 |

---

## 实现路线图

### 阶段1：基础体积渲染 (1-2周)

**目标**：实现基础的体积光线步进。

**步骤**：
1. 实现简单的均匀体积（常量密度）
2. 实现Henyey-Greenstein相位函数
3. 直接光照的单次散射
4. 渲染一个简单的体积雾

**验证**：
- ✅ 正确的透射率衰减
- ✅ 相位函数产生合理的散射方向性
- ✅ 光源产生体积光束（God Rays效果）

---

### 阶段2：RSM + 体数据 (1-2周)

**目标**：将RSM扩展到体积。

**步骤**：
1. 复用"项目2.3: RSM"的表面RSM生成
2. 实现体积光线步进采样VPL
3. 添加降噪（双边滤波）

**验证**：
- ✅ 体积雾中的color bleeding
- ✅ 动态光源产生动态体积散射

---

### 阶段3：LPV + 体数据 (2-3周)

**目标**：扩展LPV支持体积。

**步骤**：
1. 修改LPV数据结构（添加density字段）
2. 修改传播shader（考虑体积遮挡）
3. 实现体积采样

**验证**：
- ✅ 多次散射近似
- ✅ 动态体积与动态GI结合

---

### 阶段4：Froxel系统 (2-3周)

**目标**：实现独立的Froxel系统。

**步骤**：
1. 生成相机空间体素网格
2. 注入直接光照
3. 实现光线行进积分
4. 时域累积

**验证**：
- ✅ 实时性能（<3ms）
- ✅ 时域稳定
- ✅ 与表面渲染正确合成

---

### 阶段5：VCT + 体数据 (3-4周)

**目标**：修改锥追踪支持体积累积。

**步骤**：
1. 扩展体素数据（添加density）
2. 修改锥追踪shader（半透明累积）
3. 测试复杂场景

**验证**：
- ✅ 半透明物体的间接光照
- ✅ 体积雾与VCT GI结合

---

### 阶段6：DDGI + 体数据 (4-6周)

**目标**：扩展探针系统支持体积。

**步骤**：
1. 修改探针射线追踪（穿透体积）
2. 调整探针密度（3D覆盖）
3. 实现体积采样
4. 性能优化（轮询更新）

**验证**：
- ✅ 动态体积 + 高质量GI
- ✅ 探针正确处理体积散射

---

### 阶段7：混合系统集成 (2-3周)

**目标**：整合多种技术。

**步骤**：
1. 设计分层架构
2. 实现切换逻辑
3. 统一降噪和合成
4. 性能调优

**验证**：
- ✅ 根据场景自动选择算法
- ✅ 总性能预算<10ms
- ✅ 无明显接缝或过渡

---

### 总时间估计

- **兼职学习**：3-4个月
- **全职学习**：6-8周

---

## 参考资源汇总

### 📚 必读教材

| 书籍 | 作者 | 章节 | 获取方式 |
|------|------|------|---------|
| **Physically Based Rendering (4th Ed)** | Pharr, Jakob, Humphreys | Ch 11, 15 | [免费在线](https://www.pbr-book.org/) |
| **Real-Time Rendering (4th Ed)** | Akenine-Möller et al. | Ch 14 | 购买或图书馆 |
| **Production Volume Rendering** | SIGGRAPH 2017 Course | 全部 | [免费PDF](https://graphics.pixar.com/library/) |
| **Realistic Image Synthesis Using Photon Mapping** | Henrik Wann Jensen | Ch 8-10 | 购买 |

---

### 📄 核心论文列表

#### 体积渲染基础理论
| 论文 | 作者 | 会议/期刊 | 年份 | 链接 |
|------|------|-----------|------|------|
| Display of Surfaces from Volume Data | Levoy | IEEE CG&A | 1988 | [DOI](https://doi.org/10.1109/38.511) |
| Optical Models for Direct Volume Rendering | Max | IEEE TVCG | 1995 | [DOI](https://doi.org/10.1109/2945.468400) |
| A Practical Analytic Model for Daylight | Preetham et al. | SIGGRAPH | 1999 | [ACM DL](https://doi.org/10.1145/311535.311545) |

#### RSM相关
| 论文 | 作者 | 会议 | 年份 | 链接 |
|------|------|------|------|------|
| **Reflective Shadow Maps** | Dachsbacher, Stamminger | I3D | 2005 | [DOI](https://doi.org/10.1145/1053427.1053460) |
| Incremental Instant Radiosity | Laine et al. | EGSR | 2007 | [DOI](https://doi.org/10.2312/EGSR/EGSR07/277-286) |

#### LPV相关
| 论文 | 作者 | 会议 | 年份 | 链接 |
|------|------|------|------|------|
| **Cascaded Light Propagation Volumes** | Kaplanyan, Dachsbacher | I3D | 2010 | [DOI](https://doi.org/10.1145/1730804.1730821) |
| Light Propagation Volumes in CryEngine 3 | Kaplanyan | SIGGRAPH Course | 2009 | [Slides](https://advances.realtimerendering.com/s2009/) |
| Real-Time Diffuse GI Using Radiance Hints | Papaioannou et al. | HPG | 2011 | [DOI](https://doi.org/10.1145/2018323.2018342) |

#### VCT相关
| 论文 | 作者 | 会议/期刊 | 年份 | 链接 |
|------|------|-----------|------|------|
| **Interactive Indirect Illumination Using Voxel Cone Tracing** | Crassin et al. | CGF | 2011 | [DOI](https://doi.org/10.1111/j.1467-8659.2011.02063.x) |
| GigaVoxels | Crassin et al. | I3D | 2009 | [DOI](https://doi.org/10.1145/1507149.1507152) |
| Voxel-based Global Illumination (PhD Thesis) | Cyril Crassin | 论文 | 2011 | [PDF](https://tel.archives-ouvertes.fr/tel-00760453/) |
| Octree-Based Sparse Voxelization | Crassin, Green | OpenGL Insights | 2012 | [PDF](https://www.nvidia.com/docs/IO/88889/OpenGLInsights.pdf) |

#### DDGI相关
| 论文 | 作者 | 期刊 | 年份 | 链接 |
|------|------|------|------|------|
| **Dynamic Diffuse GI with Ray-Traced Irradiance Fields** | Majercik et al. | JCGT | 2019 | [开放获取](http://jcgt.org/published/0008/02/01/) |
| Scaling Probe-Based Real-Time DDGI for Production | Majercik et al. | JCGT | 2021 | [开放获取](http://jcgt.org/published/0010/02/01/) |
| Irradiance Gradients | Ward, Heckbert | EGWR | 1992 | 经典论文 |
| Light Field Probes | McGuire et al. | I3D | 2017 | [DOI](https://doi.org/10.1145/3023368.3023378) |

#### ReSTIR相关
| 论文 | 作者 | 会议/期刊 | 年份 | 链接 |
|------|------|-----------|------|------|
| **Spatiotemporal Reservoir Resampling for Real-Time Ray Tracing** | Bitterli et al. | ACM TOG | 2020 | [DOI](https://doi.org/10.1145/3386569.3392481) |
| Rearchitecting Spatiotemporal Resampling for Production | Wyman et al. | HPG | 2021 | [DOI](https://doi.org/10.2312/hpg.20211282) |
| ReSTIR GI: Path Resampling for Real-Time PT | Ouyang et al. | CGF | 2021 | [DOI](https://doi.org/10.1111/cgf.14378) |
| Generalized RIS: Foundations of ReSTIR | Bitterli et al. | ACM TOG | 2022 | [DOI](https://doi.org/10.1145/3528223.3530127) |
| ReSTIR PT | Lin et al. | SIGGRAPH Asia | 2023 | [Project](https://research.nvidia.com/publication/2023-07_restir-pt) |

#### Froxel/体积雾
| 论文 | 作者 | 来源 | 年份 | 链接 |
|------|------|------|------|------|
| **Real-Time Volumetric Cloudscapes** | Schneider, Vos | GPU Pro 7 | 2015 | [PDF](https://www.guerrilla-games.com/read/nubis-realtime-volumetric-cloudscapes) |
| Physically Based Sky, Atmosphere and Cloud Rendering | Hillaire | SIGGRAPH Course | 2020 | [Slides](https://sebh.github.io/publications/) |
| Volumetric Fog in Unreal Engine 4 | Epic Games | Blog | 2016 | [Link](https://www.unrealengine.com/) |

#### Deep Shadow Maps
| 论文 | 作者 | 会议 | 年份 | 链接 |
|------|------|------|------|------|
| **Deep Shadow Maps** | Lokovic, Veach | SIGGRAPH | 2000 | [Pixar](https://graphics.pixar.com/library/DeepShadows/) |
| Adaptive Volumetric Shadow Maps | Salvi et al. | EGSR | 2010 | [DOI](https://doi.org/10.2312/EGSR/EGSR10/385-394) |
| Opacity Shadow Maps | Kim, Neumann | RT | 2001 | [DOI](https://doi.org/10.2312/EGWR/EGWR01/177-182) |

#### Photon Beams
| 论文 | 作者 | 会议/期刊 | 年份 | 链接 |
|------|------|-----------|------|------|
| **The Beam Radiance Estimate for Volumetric PM** | Jarosz et al. | CGF | 2008 | [Project](https://cs.dartmouth.edu/~wjarosz/publications/jarosz08beam.html) |
| Progressive Photon Beams | Jarosz et al. | SIGGRAPH Asia | 2011 | [Project](https://cs.dartmouth.edu/~wjarosz/publications/jarosz11progressive.html) |
| Comprehensive Theory of Volumetric Radiance Estimation | Jarosz et al. | ACM TOG | 2011 | [Project](https://cs.dartmouth.edu/~wjarosz/publications/jarosz11points.html) |

---

### 💻 开源实现（按推荐度排序）

#### 生产级SDK
| 项目 | 技术 | 语言/API | License | 推荐度 |
|------|------|---------|---------|--------|
| [RTXGI SDK](https://github.com/NVIDIAGameWorks/RTXGI) | DDGI | D3D12/Vulkan | MIT | ⭐⭐⭐ |
| [RTXDI SDK](https://github.com/NVIDIAGameWorks/RTXDI) | ReSTIR DI | D3D12/Vulkan | MIT | ⭐⭐⭐ |
| [Falcor](https://github.com/NVIDIAGameWorks/Falcor) | 多种GI | D3D12 | BSD-3 | ⭐⭐⭐ |
| [Mitsuba 3](https://github.com/mitsuba-renderer/mitsuba3) | 离线渲染 | Python/C++ | BSD-3 | ⭐⭐⭐ |
| [PBRT-v4](https://github.com/mmp/pbrt-v4) | 离线渲染 | C++ | Apache 2.0 | ⭐⭐⭐ |

#### VCT实现
| 项目 | 特点 | 语言 | 推荐度 |
|------|------|------|--------|
| [voxel-cone-tracing](https://github.com/Friduric/voxel-cone-tracing) | ⭐ 最完整的教育实现 | C++/OpenGL | ⭐⭐⭐ |
| [VCTRenderer](https://github.com/jose-villegas/VCTRenderer) | 带教程 | C++/OpenGL | ⭐⭐ |
| [SparseVoxelOctree](https://github.com/otaku690/SparseVoxelOctree) | SVO实现 | C++ | ⭐⭐ |

#### LPV实现
| 项目 | 特点 | 语言 | 推荐度 |
|------|------|------|--------|
| [Light-Propagation-Volumes](https://github.com/djbozkosz/Light-Propagation-Volumes) | 完整实现 | C++/OpenGL | ⭐⭐⭐ |
| [CascadedLightPropagationVolumes](https://github.com/ConorStokes/CascadedLightPropagationVolumes) | Unity版 | C# | ⭐⭐ |
| [LegitEngine LPV Tutorial](https://github.com/Raikiri/LegitEngine) | 详细教程 | C++ | ⭐⭐ |

#### 体积渲染
| 项目 | 技术 | 语言 | 推荐度 |
|------|------|------|--------|
| [VolumetricLights](https://github.com/SlightlyMad/VolumetricLights) | Unity插件 | C# | ⭐⭐ |
| [glsl-atmosphere](https://github.com/wwwtyro/glsl-atmosphere) | WebGL大气 | GLSL | ⭐⭐ |

#### 引擎源码（需注册）
| 引擎 | 路径 | 语言 | 访问 |
|------|------|------|------|
| Unreal Engine 5 | `Engine/Shaders/Private/VolumetricFog.usf` | HLSL | 需Epic账号 |
| Unity HDRP | `com.unity.render-pipelines.high-definition/Runtime/Lighting/Volumetrics/` | C#/HLSL | [GitHub](https://github.com/Unity-Technologies/Graphics) |
| Godot 4 | `servers/rendering/renderer_rd/environment/` | C++/GLSL | [GitHub](https://github.com/godotengine/godot) |

---

### 🎥 视频教程与讲座

#### 中文资源
| 课程 | 讲师 | 平台 | 内容 |
|------|------|------|------|
| **GAMES202** | 闫令琪 | [Bilibili](https://www.bilibili.com/video/BV1YK4y1T7yY) | 完整GI课程，含RSM/LPV/VCT |
| GAMES101 | 闫令琪 | Bilibili | 图形学基础 |

#### 英文资源
| 讲座 | 主题 | 来源 | 链接 |
|------|------|------|------|
| Real-Time Volumetric Cloudscapes | Froxel | GDC 2015 | [YouTube](https://www.youtube.com/results?search_query=real+time+volumetric+cloudscapes) |
| RTXGI Deep Dive | DDGI | NVIDIA GTC | [YouTube](https://www.youtube.com/watch?v=3NelkAsVdn8) |
| ReSTIR Explained | ReSTIR | SIGGRAPH 2020 | [YouTube](https://www.youtube.com/watch?v=11O8vrzT2VQ) |
| Voxel Cone Tracing | VCT | Two Minute Papers | [YouTube](https://www.youtube.com/watch?v=T2pJGVCZhvQ) |

---

### 🛠️ 工具与数据

#### 体积数据工具
| 工具 | 用途 | License | 链接 |
|------|------|---------|------|
| **OpenVDB** | 体积数据格式 | MPL-2.0 | [GitHub](https://github.com/AcademySoftwareFoundation/openvdb) |
| **Houdini** | 体积编辑 | 商业 | [SideFX](https://www.sidefx.com/) |
| **Blender** | 体积着色 | GPL | [Blender.org](https://www.blender.org/) |
| **Mitsuba** | 离线渲染 | BSD | [Mitsuba](https://www.mitsuba-renderer.org/) |

#### 测试场景与数据集
| 数据集 | 内容 | 来源 | 链接 |
|--------|------|------|------|
| Disney Cloud Dataset | 真实云数据 | Disney | [链接](https://www.disneyanimation.com/resources/clouds/) |
| OpenVDB Examples | 示例体积 | DreamWorks | [GitHub](https://github.com/AcademySoftwareFoundation/openvdb) |
| McGuire Archive | 测试场景 | Morgan McGuire | [Website](https://casual-effects.com/data/) |
| ORCA Scenes | 学术测试 | 多来源 | [Website](https://developer.nvidia.com/orca) |

#### 性能分析工具
| 工具 | 平台 | 功能 | 免费 |
|------|------|------|------|
| **RenderDoc** | 全平台 | 帧捕获、分析 | ✅ |
| **Nsight Graphics** | NVIDIA | GPU调试 | ✅ |
| **PIX** | Windows/Xbox | DirectX分析 | ✅ |
| **Intel GPA** | Intel GPU | 性能分析 | ✅ |
| **AMD Radeon GPU Profiler** | AMD | GPU分析 | ✅ |

---

### 📝 重要博客与网站

| 网站 | 作者/组织 | 内容 | 语言 |
|------|----------|------|------|
| [Scratchapixel](https://www.scratchapixel.com/) | 教育网站 | 完整图形学教程 | 英文 |
| [LearnOpenGL](https://learnopengl.com/) | Joey de Vries | OpenGL教程 | 英/中 |
| [NVIDIA Developer Blog](https://developer.nvidia.com/blog/) | NVIDIA | 最新技术文章 | 英文 |
| [Real-Time Rendering Resources](http://www.realtimerendering.com/) | 社区 | 资源集合 | 英文 |
| [Advances in Real-Time Rendering](https://advances.realtimerendering.com/) | SIGGRAPH | Course Notes | 英文 |
| [Wojciech Jarosz](https://cs.dartmouth.edu/~wjarosz/) | 个人 | 体积渲染专家 | 英文 |
| [Sébastien Hillaire](https://sebh.github.io/) | 个人 | Frostbite开发者 | 英文 |
| [Matt Pettineo (MJP)](https://therealmjp.github.io/) | 个人 | 渲染工程师 | 英文 |

---

### 🎮 游戏引擎文档

| 引擎 | 体积雾文档 | GI文档 | API |
|------|-----------|--------|-----|
| **Unreal Engine 5** | [Volumetric Fog](https://docs.unrealengine.com/5.0/en-US/volumetric-fog-in-unreal-engine/) | [Lumen](https://docs.unrealengine.com/5.0/en-US/lumen-global-illumination-and-reflections-in-unreal-engine/) | C++ |
| **Unity HDRP** | [Volumetric Lighting](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@latest) | [GI](https://docs.unity3d.com/Manual/lighting-global-illumination.html) | C# |
| **Godot 4** | [Volumetric Fog](https://docs.godotengine.org/en/stable/tutorials/3d/volumetric_fog.html) | [SDFGI](https://docs.godotengine.org/en/stable/tutorials/3d/global_illumination/using_sdfgi.html) | GDScript/C++ |
| **CryEngine** | [官方文档](https://docs.cryengine.com/) | LPV文档 | C++ |

---

### 学习路径建议

```
第1个月：
  - 体积渲染基础
  - 单次散射实现
  - GPU Gems 3相关章节

第2个月：
  - RSM + 体数据
  - LPV + 体数据
  - 理解球谐光照

第3个月：
  - Froxel系统实现
  - VCT + 体数据
  - 时域累积技术

第4个月（可选）：
  - DDGI + 体数据
  - 混合系统设计
  - 性能调优
```

---

## 常见问题

### Q1: 体积渲染性能开销太大怎么办？

**A**: 多种优化策略：
- **降低分辨率**：1/2或1/4分辨率计算 + 上采样
- **自适应步进**：空白区域大步，高密度区域小步
- **早期终止**：透射率<1%时停止
- **时域累积**：低采样率 + 历史帧混合
- **空间缓存**：Froxel / LPV避免每像素步进

### Q2: 如何避免光泄漏（Light Leaking）？

**A**:
- **几何体积（Geometry Volume）**：注入遮挡信息
- **可见性查询**：在采样时验证可见性
- **更高分辨率**：增加体素/Froxel分辨率
- **混合方法**：关键区域用DDGI（准确），其他用LPV

### Q3: 时域闪烁（Temporal Flickering）如何解决？

**A**:
- **指数移动平均**：`result = mix(history, current, 0.05-0.1)`
- **方差裁剪**：类似TAA的color clamping
- **Jitter技术**：每帧偏移采样位置
- **更多探针/更高分辨率**：减少欠采样

### Q4: 多次散射如何处理？

**A**:
- **LPV迭代**：增加传播次数（6→10）
- **探针递归**：DDGI探针查询其他探针
- **路径追踪**：离线或低频更新
- **近似**：大多数场景单次散射已足够

### Q5: 异质介质（Heterogeneous Media）怎么处理？

**A**:
- **3D纹理**：存储密度场
- **程序化**：噪声函数生成（Perlin/Worley）
- **模拟**：物理模拟（流体、烟雾）
- **OpenVDB**：复杂数据用VDB格式

---

## 总结

### 技术对比矩阵

| 技术 | 质量 | 性能 | 动态支持 | 实现难度 | 适用场景 |
|------|------|------|---------|---------|---------|
| RSM + 体数据 | ⭐⭐⭐ | ⭐⭐⭐ | ✅ | 🟢 简单 | 单次散射 |
| LPV + 体数据 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | 🟡 中等 | 多次散射近似 |
| VCT + 体数据 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 🔴 复杂 | 高质量GI |
| DDGI + 体数据 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 🔴 复杂 | 室内/重要区域 |
| ReSTIR + 体数据 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ⚫ 极难 | 多光源场景 |
| Froxel | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 🟡 中等 | 相机空间体积 |
| 体积Lightmap | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 🟢 简单 | 静态场景 |

### 推荐起步路线

**初学者**：
1. Froxel系统（简单、直观、实用）
2. LPV + 体数据（理解传播）
3. 混合方案（实际应用）

**进阶**：
4. VCT + 体数据（高质量）
5. DDGI + 体数据（探针方法）

**研究级**：
6. ReSTIR + 体数据（前沿技术）

### 最终建议

体数据与GI结合**不需要重写所有系统**：
- **LPV**：天然支持，小修改
- **VCT**：修改锥追踪即可
- **Froxel**：独立系统，渐进式添加
- **混合方案**：逐步整合，性能可控

**从小规模原型开始**，逐步扩展到生产级系统！

---

**祝你实践顺利！体积渲染是图形学中最美的领域之一。** ✨

