# 全局光照核心论文清单

按主题分类整理，标注阅读优先级：⭐⭐⭐(必读) ⭐⭐(重要) ⭐(扩展)

---

## 1. 理论基础

### 渲染方程与光传输理论
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1986 | The Rendering Equation | James Kajiya | SIGGRAPH | 奠基性工作，定义现代渲染理论基础 |
| ⭐⭐ | 1995 | Optimally Combining Sampling Techniques for Monte Carlo Rendering | Eric Veach, Leonidas Guibas | SIGGRAPH | Multiple Importance Sampling (MIS) |
| ⭐⭐⭐ | 1997 | Robust Monte Carlo Methods for Light Transport Simulation | Eric Veach | PhD Thesis | MIS和BDPT的完整理论，必读 |
| ⭐⭐ | 1982 | A Reflectance Model for Computer Graphics | Robert Cook, Kenneth Torrance | SIGGRAPH | Cook-Torrance BRDF模型 |

---

## 2. 路径追踪方法

### 基础路径追踪
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1986 | The Rendering Equation | Kajiya | SIGGRAPH | 同时提出路径追踪算法 |
| ⭐⭐ | 2002 | A Practical Guide to Global Illumination using Photon Mapping | Jensen et al. | SIGGRAPH Course | 实践导向的教程 |

### 双向路径追踪
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1994 | Bidirectional Estimators for Light Transport | Veach, Guibas | Eurographics | BDPT原始论文 |
| ⭐⭐ | 2012 | Light Transport Simulation with Vertex Connection and Merging | Georgiev et al. | SIGGRAPH Asia | VCM算法，结合BDPT和光子映射 |

### Metropolis光线传输
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1997 | Metropolis Light Transport | Veach, Guibas | SIGGRAPH | MLT开创性工作 |
| ⭐⭐ | 2002 | A Simple and Robust Mutation Strategy for the Metropolis Light Transport Algorithm | Kelemen et al. | CGF | 简化的MLT实现 |
| ⭐⭐ | 2014 | Multiplexed Metropolis Light Transport | Hachisuka et al. | SIGGRAPH | 改进的MLT方法 |
| ⭐ | 2017 | Gradient-Domain Metropolis Light Transport | Kettunen et al. | SIGGRAPH | 梯度域MLT |

---

## 3. 光子映射家族

### 经典光子映射
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1996 | Global Illumination using Photon Maps | Henrik Wann Jensen | EGWR | 光子映射诞生 |
| ⭐⭐ | 2001 | A Practical Guide to Global Illumination using Photon Mapping | Jensen | SIGGRAPH Course | 实现指南 |

### 渐进式光子映射
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2008 | Progressive Photon Mapping | Hachisuka et al. | SIGGRAPH Asia | PPM突破内存限制 |
| ⭐⭐⭐ | 2009 | Stochastic Progressive Photon Mapping | Hachisuka, Jensen | SIGGRAPH Asia | SPPM进一步改进 |
| ⭐⭐ | 2011 | Progressive Photon Beams | Hachisuka, Jensen | SIGGRAPH Asia | 扩展到体积渲染 |

### 统一方法
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2012 | A Path Space Extension for Robust Light Transport Simulation | Georgiev et al. | SIGGRAPH Asia | VCM统一BDPT和PM |

---

## 4. 辐射度方法

### 经典辐射度
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 1984 | Modeling the Interaction of Light Between Diffuse Surfaces | Goral et al. | SIGGRAPH | 辐射度方法诞生 |
| ⭐⭐ | 1988 | A Progressive Refinement Approach to Fast Radiosity Image Generation | Cohen et al. | SIGGRAPH | 渐进式辐射度 |
| ⭐ | 1993 | A Two-Pass Solution to the Rendering Equation | Sillion, Puech | CGF | Final Gathering概念 |

---

## 5. 预计算实时GI

### 球谐函数与PRT
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2001 | An Efficient Representation for Irradiance Environment Maps | Ramamoorthi, Hanrahan | SIGGRAPH | SH在图形学中的应用 |
| ⭐⭐⭐ | 2002 | Precomputed Radiance Transfer for Real-Time Rendering in Dynamic, Low-Frequency Lighting Environments | Sloan et al. | SIGGRAPH | PRT开创性工作 |
| ⭐⭐ | 2003 | All-Frequency Shadows Using Non-linear Wavelet Lighting Approximation | Ng et al. | SIGGRAPH | 高频PRT |
| ⭐⭐ | 2005 | All-Frequency Precomputed Radiance Transfer for Glossy Objects | Liu et al. | EGSR | Glossy PRT |

### 瞬时辐射度与VPL
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 1997 | Instant Radiosity | Alexander Keller | SIGGRAPH | VPL概念提出，实时GI基础 |
| ⭐⭐ | 2008 | Instant Radiosity for Real-Time Rendering | Laine et al. | EGSR | 实时化 |
| ⭐ | 2009 | Incremental Instant Radiosity for Real-Time Indirect Illumination | Dachsbacher et al. | EGSR | 增量式VPL |

### Reflective Shadow Maps
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2005 | Reflective Shadow Maps | Dachsbacher, Stamminger | I3D | RSM开创性工作，VPL实时应用 |
| ⭐⭐ | 2006 | Splatting Indirect Illumination | Dachsbacher, Stamminger | I3D | RSM改进，屏幕空间splatting |
| ⭐⭐ | 2007 | Micro-Rendering for Scalable, Parallel Final Gathering | Ritschel et al. | SIGGRAPH Asia | RSM高级应用 |
| ⭐ | 2009 | Imperfect Shadow Maps for Efficient Computation of Indirect Illumination | Ritschel et al. | SIGGRAPH Asia | 简化版RSM |

---

## 6. 体素化GI方法

### Light Propagation Volumes
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2009 | Cascaded Light Propagation Volumes for Real-Time Indirect Illumination | Kaplanyan | I3D | LPV核心论文 |
| ⭐⭐ | 2010 | Light Propagation Volumes in CryEngine 3 | Kaplanyan, Dachsbacher | SIGGRAPH Advances in RT | 工业实现 |

### Voxel Cone Tracing
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2011 | Interactive Indirect Illumination Using Voxel Cone Tracing | Crassin et al. | CGI | VCT开创性工作 |
| ⭐⭐ | 2012 | Octree-Based Sparse Voxelization Using the GPU Hardware Rasterizer | Crassin, Green | GPU Pro 3 | SVO实现细节 |
| ⭐⭐ | 2012 | GigaVoxels: Ray-Guided Streaming for Efficient and Detailed Voxel Rendering | Crassin et al. | I3D | 大规模体素数据 |

### Voxel GI其他方法
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐ | 2012 | Voxel-based Global Illumination | Thiedemann et al. | I3D | 另一种体素GI方案 |
| ⭐ | 2016 | Real-Time Global Illumination using Precomputed Light Field Probes | McGuire et al. | I3D | 光场探针方法 |

---

## 7. 屏幕空间方法

### SSAO家族
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2007 | Screen Space Ambient Occlusion | Crytek | Shader X6 | SSAO原始方法 |
| ⭐⭐ | 2009 | Image-Space Horizon-Based Ambient Occlusion | Bavoil et al. | SIGGRAPH Talks | HBAO改进 |
| ⭐⭐ | 2012 | Alchemy Screen-Space Ambient Obscurance Algorithm | McGuire et al. | HPG | ASSAO |
| ⭐⭐ | 2017 | Ground Truth Ambient Occlusion | Jimenez et al. | HPG | GTAO |

### 屏幕空间GI
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2011 | Practical Real-Time Strategies for Accurate Indirect Occlusion | McGuire et al. | I3D | 早期SSGI尝试 |
| ⭐ | 2016 | Deferred Radiance Transfer Volumes | Silvennoinen, Lehtinen | I3D | 混合屏幕空间方法 |
| ⭐⭐ | 2021 | RTXGI: Screen-Space Global Illumination | NVIDIA | - | 现代SSGI方案 |

---

## 8. 探针与辐照度场

### 辐照度探针
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2019 | Dynamic Diffuse Global Illumination with Ray-Traced Irradiance Fields | Majercik et al. | JCGT | DDGI核心论文 |
| ⭐⭐ | 2021 | Scaling Probe-Based Real-Time Dynamic Global Illumination for Production | Majercik et al. | JCGT | DDGI生产级优化 |
| ⭐⭐ | 2016 | Real-Time Global Illumination using Precomputed Light Field Probes | McGuire et al. | I3D | 光场探针 |

### 辐射度缓存
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 1988 | A Ray Tracing Solution for Diffuse Interreflection | Ward et al. | SIGGRAPH | Irradiance Caching |
| ⭐ | 2008 | Fast Global Illumination on Dynamic Height Fields | Umenhoffer et al. | CGF | 动态场景缓存 |

---

## 9. 硬件光线追踪时代

### ReSTIR系列
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2020 | Spatiotemporal Reservoir Resampling for Real-Time Ray Tracing with Dynamic Direct Lighting | Bitterli et al. | SIGGRAPH | ReSTIR DI开创性工作 |
| ⭐⭐⭐ | 2021 | ReSTIR GI: Path Resampling for Real-Time Path Tracing | Ouyang et al. | CGF | 扩展到全局光照 |
| ⭐⭐ | 2022 | Rearchitecting Spatiotemporal Resampling for Production | Wyman, Panteleev | HPG | 生产级ReSTIR |
| ⭐ | 2023 | ReSTIR PT: A Scalable Real-Time Path Tracer | Lin et al. | CGF | 完整路径追踪 |

### 实时降噪
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2017 | Spatiotemporal Variance-Guided Filtering (SVGF) | Schied et al. | HPG | 现代降噪基础方法 |
| ⭐⭐ | 2018 | Gradient Estimation for Real-Time Adaptive Temporal Filtering | Hasselgren et al. | PACMCGIT | 梯度域降噪 |
| ⭐⭐ | 2011 | Interactive Reconstruction of Monte Carlo Image Sequences | Rousselle et al. | SIGGRAPH | BMFR方法 |
| ⭐ | 2020 | Temporally Reliable Motion Vectors for Real-time Ray Tracing | Zheng et al. | CGF | 运动向量处理 |

### 其他硬件光追技术
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2018 | Sampling the GGX Distribution of Visible Normals | Heitz | JCGT | 微表面采样 |
| ⭐ | 2019 | A Fast and Robust Method for Avoiding Self-Intersection | Wächter, Binder | Ray Tracing Gems | 光追实现细节 |
| ⭐⭐ | 2021 | Continuous Multiple Importance Sampling | Grittmann et al. | SIGGRAPH Asia | MIS改进 |

---

## 10. 神经网络与AI

### 神经降噪
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2017 | Interactive Reconstruction of Monte Carlo Image Sequences using a Recurrent Denoising Autoencoder | Chaitanya et al. | SIGGRAPH | 深度学习降噪 |
| ⭐⭐ | 2020 | Denoising Deep Monte Carlo Renderings | Xu et al. | CGF | 改进的神经降噪 |

### 神经重要性采样与缓存
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐⭐ | 2019 | Neural Importance Sampling | Müller et al. | SIGGRAPH | 神经网络指导采样 |
| ⭐⭐⭐ | 2021 | Real-time Neural Radiance Caching for Path Tracing | Müller et al. | SIGGRAPH | NRC突破性工作 |
| ⭐⭐ | 2022 | Neural Radiosity | Hadadan et al. | SIGGRAPH | 神经辐射度 |

### NeRF与神经场景表示
| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2020 | NeRF: Representing Scenes as Neural Radiance Fields | Mildenhall et al. | ECCV | NeRF开创性工作 |
| ⭐ | 2022 | Instant Neural Graphics Primitives | Müller et al. | SIGGRAPH | Instant-NGP加速 |
| ⭐ | 2023 | Relighting Neural Radiance Fields | Rudnev et al. | ICCV | NeRF重光照 |

---

## 11. 距离场与全局光照

| 优先级 | 年份 | 论文标题 | 作者 | 会议/期刊 | 笔记 |
|-------|------|---------|------|-----------|------|
| ⭐⭐ | 2015 | Dynamic Diffuse Global Illumination with Distance Field Volumes | Kavan, Wright | SIGGRAPH Poster | UE4早期DFGI |
| ⭐ | 2016 | Distance Field Soft Shadows | Wright | Unreal Dev Day | 距离场软阴影 |

---

## 12. 生产级系统与案例

### 引擎技术
| 优先级 | 年份 | 论文标题/分享 | 作者/公司 | 会议 | 笔记 |
|-------|------|---------------|----------|------|------|
| ⭐⭐⭐ | 2022 | A Deep Dive into Lumen | Daniel Wright | SIGGRAPH | UE5 Lumen详解 |
| ⭐⭐ | 2021 | The Rendering of The Last of Us Part II | Naughty Dog | SIGGRAPH | 顽皮狗GI方案 |
| ⭐⭐ | 2021 | Ghost of Tsushima: Procedural Grass | Sucker Punch | GDC | 对马岛之魂GI |
| ⭐⭐ | 2020 | Cyberpunk 2077 Ray Tracing | CD Projekt RED | - | 赛博朋克2077光追 |
| ⭐ | 2021 | Marvel's Spider-Man: Miles Morales Ray Tracing | Insomniac | GDC | 蜘蛛侠光追实现 |

---

## 13. 经典教科书章节推荐

### PBRT (Physically Based Rendering)
- **Chapter 5**: Color and Radiometry
- **Chapter 13**: Monte Carlo Integration
- **Chapter 14**: Light Transport I: Surface Reflection
- **Chapter 15**: Light Transport II: Volume Rendering
- **Chapter 16**: Light Transport III: Bidirectional Methods

### Real-Time Rendering (4th Edition)
- **Chapter 11**: Global Illumination
- **Chapter 12**: Image-Space Effects
- **Chapter 26**: Real-Time Ray Tracing

### Advanced Global Illumination (2nd Edition)
- **Chapter 2**: The Physics of Light Transport
- **Chapter 3**: Monte Carlo Methods
- **Chapter 4**: Stochastic Radiosity
- **Chapter 5**: Particle Tracing
- **Chapter 6**: Hybrid Algorithms

---

## 14. 重要课程与教程

### 在线课程
| 课程名称 | 讲师 | 平台 | 笔记 |
|---------|------|------|------|
| GAMES101: 现代计算机图形学入门 | 闫令琪 | Bilibili | 基础必修 |
| GAMES202: 高质量实时渲染 | 闫令琪 | Bilibili | 实时GI重点 ⭐⭐⭐ |
| TU Wien Rendering Course | Károly Zsolnai | YouTube | 深入理论 |
| Ray Tracing Course | Peter Shirley | 在线书籍 | 实践入门 ⭐⭐⭐ |

### SIGGRAPH Courses
| 年份 | 课程标题 | 讲师 | 笔记 |
|------|---------|------|------|
| 2010 | Global Illumination Across Industries | 多位专家 | GI综述 |
| 2017 | Path Tracing in Production | 工业界专家 | 生产级路径追踪 ⭐⭐⭐ |
| 2019 | Production Volume Rendering | Disney等 | 体积渲染 |
| 2021 | A Deep Dive into Nanite & Lumen | Epic Games | UE5技术细节 ⭐⭐⭐ |

---

## 15. 阅读顺序建议

### 第一阶段：建立理论基础
1. Kajiya - The Rendering Equation (1986) ⭐⭐⭐
2. Cook-Torrance BRDF (1982) ⭐⭐
3. PBRT Book Chapter 5, 13 ⭐⭐⭐
4. Veach PhD Thesis - Chapter 1-3 (理论部分) ⭐⭐⭐

### 第二阶段：离线渲染算法
1. Jensen - Photon Mapping (1996) ⭐⭐⭐
2. Veach - BDPT (1994) + MLT (1997) ⭐⭐⭐
3. Hachisuka - Progressive Photon Mapping (2008, 2009) ⭐⭐⭐
4. Georgiev - Vertex Connection and Merging (2012) ⭐⭐

### 第三阶段：预计算实时方法
1. Ramamoorthi - SH Environment Maps (2001) ⭐⭐⭐
2. Sloan - PRT (2002) ⭐⭐⭐
3. Keller - Instant Radiosity (1997) ⭐⭐ - VPL理论基础
4. Dachsbacher - Reflective Shadow Maps (2005) ⭐⭐⭐ - RSM实时VPL
5. Kaplanyan - LPV (2009) ⭐⭐⭐ - 基于RSM

### 第四阶段：现代实时GI
1. Crassin - Voxel Cone Tracing (2011) ⭐⭐⭐
2. Schied - SVGF Denoising (2017) ⭐⭐⭐
3. Majercik - DDGI (2019) ⭐⭐⭐
4. McGuire - Light Field Probes (2016) ⭐⭐
5. Lumen Deep Dive (2022) ⭐⭐⭐

### 第五阶段：硬件光追前沿
1. Bitterli - ReSTIR (2020) ⭐⭐⭐
2. Ouyang - ReSTIR GI (2021) ⭐⭐⭐
3. Müller - Neural Radiance Caching (2021) ⭐⭐⭐
4. Ray Tracing Gems I & II (精选章节) ⭐⭐⭐

---

## 16. 论文获取资源

### 学术资源
- **ACM Digital Library**: SIGGRAPH论文官方来源
- **Eurographics DL**: 欧洲图形学会议论文
- **arXiv.org**: 预印本论文
- **Google Scholar**: 搜索和引用追踪

### 开放资源
- **Ke-Sen Huang's Page**: SIGGRAPH论文汇总 (http://kesen.realtimerendering.com/)
- **Papers We Love**: 精选论文仓库
- **Self Shadow**: SIGGRAPH Course笔记
- **作者个人主页**: 很多作者会公开论文PDF

### 视频资源
- **SIGGRAPH YouTube Channel**: 会议录像
- **GDC Vault**: 游戏开发者大会分享
- **Two Minute Papers**: 论文快速解读

---

## 17. 实践验证建议

### 论文阅读方法
1. **第一遍**: 快速浏览，理解核心思想和创新点
2. **第二遍**: 详细阅读，理解算法细节和公式推导
3. **第三遍**: 实现或复现，验证理解

### 笔记记录
- 论文核心贡献（1-2句话总结）
- 解决的问题和使用场景
- 算法伪代码
- 与其他方法的对比
- 实现难点和优化思路
- 适用场景和局限性

### 代码验证
- 对于⭐⭐⭐级别论文，建议实现核心算法
- 对于⭐⭐级别论文，阅读相关开源实现
- 对于⭐级别论文，理解思想即可

---

## 附录：论文数量统计

- **⭐⭐⭐ 必读论文**: 约25篇
- **⭐⭐ 重要论文**: 约40篇
- **⭐ 扩展论文**: 约20篇
- **总计**: 85+篇核心文献

**预计阅读时间**:
- 精读必读论文: 50-75小时
- 阅读重要论文: 60-80小时
- 浏览扩展论文: 20-30小时
- **总计**: 130-185小时纯阅读时间

结合实践项目，完整学习周期建议6-9个月。

---

**说明**: 
- 本清单持续更新，关注SIGGRAPH/Eurographics新论文
- 优先级基于历史影响力和实用性
- 建议先看综述类论文/课程，再深入细节
- 论文阅读与代码实践相结合效果最佳

祝论文阅读顺利！

