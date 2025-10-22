> 阅读理解UE4.27的lightmass代码，给出详尽的算法解析过程，解构lightmass的工程和算法细节；罗列相关的论文等资源，根据代码细节，给出相关的论文算法参考，如有相关公式，给出详尽的推导过程；将所有内容整理成markdown格式，方便我后续导出

# UE4.27 Lightmass 源码与算法全解（工程解构 + 数学推导 + 论文索引）

说明：
- 本文聚焦 UE4.27 的 CPU Lightmass（Programs/UnrealLightmass）而非 GPU Lightmass 插件。
- 内容按“工程结构 → 算法流程 → 数学推导 → 代码定位 → 参数与质量控制 → 参考文献”的脉络整理，适合导出为文档备查。
- 由于无法直接附带代码片段，这里提供关键类名/函数名/文件夹结构的检索关键词与伪代码，方便你在本地源码中精确定位。

---

## 1. 总览：Lightmass 在 UE4 的角色与数据流

Lightmass 是离线全局光照烘焙器，负责：
- 对“静态/可静态”的对象生成光照贴图（Lightmap）与阴影贴图（Shadow map）。
- 生成体积光照图（Volumetric Lightmap，供动态对象采样间接光）。
- 将环境光照（Skylight）、发光材质（Emissive）等贡献整合。
- 通过 Swarm 分布式调度在多机/多进程上并行构建。

高层数据流（Editor 侧 → Lightmass → Editor 回传）：
1) 场景导出（几何、材质、光源、Lightmass 设置、每个 UV-mapping 的 bake 任务）  
2) Lightmass 进程读取导出数据，构建加速结构（BVH/kDOP Tree）、采样与缓存数据结构  
3) 直接光（含软阴影）、光子发射与全局 photon map 构建  
4) 最终聚合（Final Gather）+ 辐照度缓存（Irradiance Cache）插值生成每个 texel/vertex 的间接光  
5) 体积光照图（Volumetric Lightmap）与方向性编码（Directional Lightmap）  
6) 结果写回 Swarm，Editor 采集并保存到关卡/资源

---

## 2. 工程结构与关键代码定位

源码位置（默认路径）：
- Engine/Source/Programs/UnrealLightmass/

常见子模块与检索关键词（便于源码游览）：
- 场景导入与表示：
  - 关键词：LightmassImporter, SceneExport, StaticLightingScene, StaticLightingMesh, StaticLightingVertex, Mapping, TextureMapping, VertexMapping
- 光线查询与加速结构：
  - 关键词：Ray, RayIntersect, Intersect, kDOP, KDOPTree, BVH, BuildAcceleration, Triangle, AABB
- 直接光照与阴影：
  - 关键词：DirectLighting, ShadowRay, AreaLightSamples, Visibility, NextEventEstimation
- 光子映射（Photon Mapping）：
  - 关键词：Photon, PhotonMap, EmitPhotons, StorePhoton, BalanceKDTree, KNearest, ConeFilter
- 最终聚合与辐照度缓存：
  - 关键词：FinalGather, IrradianceCache, CacheRecord, Gradients, InterpolateIrradiance, GatherRays
- 重要体积与门户：
  - 关键词：ImportanceVolume, Portal, SkylightPortal
- 体积光照图：
  - 关键词：VolumetricLightmap, Voxel, Probe, SHCoefficients, LMVolume
- 采样与低差异序列：
  - 关键词：Sampling, Halton, Sobol, Hammersley, CosineHemisphere
- Swarm 接口与任务分发：
  - 关键词：Swarm, Job, Task, MappingTask, Export/Import
- 设置与质量控制：
  - 关键词：LightmassSettings, NumIndirectLightingBounces, IndirectLightingQuality, IndirectLightingSmoothness, StaticLightingLevelScale

建议首次阅读路径：
- 先看场景/任务导入（Importer/StaticLightingScene）→ 构建加速结构 → 直接光 → 光子映射 → Final Gather + Irradiance Cache → Volumetric Lightmap。
- 每个阶段边读代码边对照下文算法与推导。

---

## 3. 算法分层与流程解构

### 3.1 基础：渲染方程与 Lambert 漫反射

- 渲染方程（Kajiya 1986）：
  - Lo(x, ωo) = Le(x, ωo) + ∫Ω fr(x, ωi, ωo) Li(x, ωi) (n·ωi) dωi
- Lambert 漫反射：fr = ρ/π（ρ 为反照率）
  - E(x) = ∫Ω Li(x, ωi) (n·ωi) dωi（辐照度）
  - 漫反射出射辐亮度：Lo = Le + (ρ/π) E

Lightmass 目标：稳健近似 E(x)，并为每个 Lightmap texel/vertex 生成可插值存储的结果（含方向性等扩展）。

---

### 3.2 直接光照与软阴影（Area Light Monte Carlo）

- 点光/聚光：对可见性发射影线；聚光包含锥体衰减。
- 面光/矩形光：从光源表面均匀或分层采样，进行下一事件估计（NEE），计算可见性与几何项。
- 估计公式（从面积光源 A 采样，均匀采样 y ∈ A）：
  - Ld(x, ωo) ≈ (1/N) Σ [ Le(y→x) fr(x) G(x,y) V(x,y) / p(y) ]
  - p(y) = 1/|A|，G(x,y) = (n_x·ω)(n_y·-ω)/|x−y|^2
- 对环境/天光：半球采样或基于 Portal 的重要性采样，pdf 与权重按采样分布匹配。

代码提示：
- 搜索 DirectLighting/ShadowRay/AreaLightSamples
- 质量受采样数量与低差异序列控制（Halton/Sobol）

---

### 3.3 光子映射（Photon Mapping）— 全局间接光的粗解

Lightmass 的核心之一，用于：
- 将光源能量通过多次漫反射传播进场景，构建全局光子分布（多为 diffuse-only）。
- 在最终聚合阶段用密度估计快速查询局部辐照度近似。

两阶段经典流程（Jensen）：
1) 发射与追踪光子（Photon Tracing）
   - 对每个光源按总能量发射 M 个光子：每个光子功率 Φ = P_light / M
   - 采样发射位置与方向（点光：均匀方向；面光：均匀表面+半球；聚光：受锥角约束）
   - 与场景求交；命中表面：
     - 存储光子（位置、入射方向、功率）
     - 随机选择相互作用（漫反射/吸收，Lightmass 主要考虑漫反射）
     - 俄轮盘（Russian Roulette）决定终止或继续：生存概率 p_rr，吞吐量乘以 ρ/p_rr
   - 多次反弹（受 MaxBounces 或能量阈值控制）
2) 构建光子图（Photon Map）
   - 使用 k-d tree / 平衡 kd 树建立空间索引，支持 k-NN 查询
   - 可选锥形核滤波（Cone Filter）提升估计质量

在查询点 x 的辐照度估计（k 近邻，固定半径 R 或半径取第 k 个光子距离）：
- 纯面积核（Top-hat）：
  - Ê(x) = (1/(π R^2)) Σ_i Φ_i
- 锥形核（cone filter, α > 1），权重 wi = 1 − di/(αR)：
  - Ê(x) = (1/(π R^2 (1 − 2/(3α)))) Σ_i wi Φ_i

进一步得到漫反射出射：
- L̂o(x) = (ρ/π) Ê(x)

代码提示：
- 搜索 Photon, PhotonMap, EmitPhotons, BalanceKDTree, KNearest, ConeFilter
- 注意：Lightmass 通常不单独输出明确“焦散光子图”，更偏向于全局 diffuse 光子图 + Final Gather 平滑

---

### 3.4 最终聚合（Final Gather）与辐照度缓存（Irradiance Cache）

目的：
- 在待烘焙的 texel/vertex 上获得平滑、低噪的间接光。
- 大幅减少在每个 texel 上直接做高代价多次可见性查询。

做法：
1) 在曲面上少量“昂贵点”（Cache Record）上进行高质量采样：
   - 对每个昂贵点 p，发射 N 条半球采样射线 ωj，估计 E(p)
   - 采样来源包括：直接从场景追踪/一跳再追踪（质量更高）或查询光子图密度估计（更快）
   - 计算并存储：E(p)、法线 n_p、可见性/曲率相关半径 r_p、可选的辐照度梯度 ∇E(p)
2) 对大量 texel/vertex 用缓存插值：
   - 给定查询点 q，找到邻近的若干缓存记录 {pi}，使用 Ward/Heckbert 权重插值
   - 典型权重（思想，实际实现会含参数与阈值）：
     - wi = 1 / (α·||q − pi||/ri + β·sqrt(max(0, 1 − n_q·n_i)) + γ·|bent_q − bent_i|)
     - ri 是缓存点的有效半径（基于几何/可见性变化确定）
   - 如使用梯度：E(q) ≈ Σ wi [Ei + ∇E_i · (q − pi)] / Σ wi
   - 缓存密度自适应：法线/可见性变化大处放密一点

半球辐照度的 Monte Carlo 估计（在昂贵点处）：
- 若使用余弦加权采样 p(ω) = cosθ/π，则
  - Ê(p) = (1/N) Σ_j Li(p, ωj) (n·ωj)/p(ωj) = (π/N) Σ_j Li(p, ωj)

代码提示：
- 搜索 FinalGather, GatherRays, IrradianceCache, CacheRecord, InterpolateIrradiance, Gradients
- 低差异采样：Halton/Sobol/Hammersley
- 质量控制由 IndirectLightingQuality/NumIndirectLightingBounces/IndirectLightingSmoothness 等参数参与

---

### 3.5 体积光照图（Volumetric Lightmap, VLM）

用途：
- 为动态对象/粒子在 3D 空间中查询预计算间接光，避免动态 GI。
- Lightmass 在 3D 采样点（Probe）上聚合入射辐射并编码为球谐（SH）或定向系数。

流程要点：
- 自适应体素/八叉树布点：靠近几何/重要体积更高密度
- 每个 Probe 采样多个方向，估计入射辐射 L(ω)，投影到 SH（常用 L2 或 L3 阶，源码里可查具体阶数与压缩）
- 存储：系数压缩、砖块/层级布局、插值策略（通常三线性或更高级的插值）

代码提示：
- 搜索 VolumetricLightmap, Probe, SHCoefficients, VolumeTree, SampleDirections

---

### 3.6 方向性 Lightmap、Bent Normal 与 AO

- 方向性 Lightmap：
  - 将间接光以有限个方向基编码（如三基向量或低阶 SH），以便运行时能粗略重建方向性与法线相关性。
  - 典型做法：同时存储“强度 + 方向性”（HQ/LQ 两种格式）；具体编码细节可在 Lightmap 编码路径中查找。
- Bent Normal（弯曲法线）：
  - 从半球可见性分布得到的平均可见方向，常用于环境遮蔽与环境反射调制。
- AO：
  - 可作为附加通道，通过有限半径的可见性采样得到（与 Final Gather 共用射线或单独 pass）。

代码提示：
- 搜索 DirectionalLightmap, BentNormal, Occlusion, Directionality, Encode/Decode

---

### 3.7 天空光与门户（Portal）/重要体积（Importance Volume）

- 天空光（Skylight）：半球/环境贴图采样，可能与 Portal 联合进行重要性引导，提高进入室内空间的采样效率。
- Lightmass 重要体积：限定烘焙的高质量区域，影响采样密度与 Final Gather 覆盖范围。
- 门户（Skylight Portal）：将天光的采样重心引导到门窗等开口，减少无效射线。

代码提示：
- 搜索 ImportanceVolume, Portal, Skylight, EnvironmentSampling

---

## 4. 数学推导（核心估计器与无偏性/一致性）

本节针对 Lightmass 中最关键的估计器给出推导与要点。

### 4.1 从渲染方程到漫反射出射

- 漫反射 BRDF：fr = ρ/π
- 出射辐亮度：
  - Lo = Le + ∫Ω (ρ/π) Li cosθ dω = Le + (ρ/π) E
- 目标变为估计 E(x) = ∫Ω Li cosθ dω

---

### 4.2 半球辐照度的 Monte Carlo 估计

- 设 ω ~ p(ω)，则 E = ∫ Li cosθ dω = ∫ (Li cosθ / p(ω)) p(ω) dω
- MC 估计：
  - Ê = (1/N) Σ_j Li(ωj) cosθj / p(ωj)
- 若采用余弦加权 p(ω) = cosθ/π：
  - Ê = (1/N) Σ_j Li cosθ / (cosθ/π) = (π/N) Σ_j Li
  - 这说明在 Final Gather 中用余弦加权半球采样能有效降低方差且实现简单的权重。

无偏性：
- E[Ê] = E，方差随 N 增大按 1/N 收敛（低差异序列可进一步改善收敛常数）。

---

### 4.3 面光源直接光的面积采样（Next Event Estimation）

- 目标：Ld(x) = ∫A Le(y→x) fr G(x,y) V(x,y) dA(y)
- 均匀采样 y ∈ A，p(y) = 1/|A|：
  - L̂d = (1/N) Σ [Le fr G V / p(y)] = (|A|/N) Σ [Le fr G V]
- 如进一步对出射方向也采样或采用分层/重要性采样，pdf 与权重相应更新（公式一致）。

---

### 4.4 光子映射的密度估计

- 物理上：光通量 Φ 穿过小面元 dA 的密度与辐照度关系为 E = dΦ/dA
- 若在半径 R 圆盘邻域内收集到光子 {Φi}，则面积核估计：
  - Ê = (1/(πR^2)) Σ_i Φi
- 使用 k 近邻，R 取第 k 个最近光子距离；若采用锥形滤波 wi = 1 − di/(αR)（di≤R）：
  - Ê = (1/(πR^2 Cα)) Σ_i wi Φi
  - Cα = 1 − 2/(3α) 为归一化常数（Jensen）
- 漫反射出射辐亮度：L̂o = (ρ/π) Ê

一致性：
- k → ∞ 且 R → 0，满足一定收敛条件时密度估计收敛于真值（偏差-方差权衡可通过渐进收缩 R 与递增 k 平衡）。

---

### 4.5 俄轮盘（Russian Roulette）无偏性证明

- 对于一次反射，若以概率 p_rr 保留路径，保留时将贡献除以 p_rr：
  - 原始期望贡献：E[C]  
  - 俄轮盘后期望：E[Ĉ] = p_rr·E[C/p_rr] + (1−p_rr)·0 = E[C]（无偏）
- 在多次反弹中保证吞吐量 T 乘以 ρ/p_rr，保持能量守恒。

---

### 4.6 辐照度缓存插值与梯度（思路）

- 近似：E(q) ≈ Σ wi [Ei + ∇E_i · (q − pi)] / Σ wi
- 权重 wi 随几何距离与法线偏差增大而减小，ri 为缓存点“影响半径”
- 梯度估计（Ward & Heckbert 1992）基于对半球样本的几何项与可见性变化的微分近似；实现中通常封装为 ComputeIrradianceGradients()，输出平移/旋转梯度分量以改善插值在曲率或遮挡变化区域的准确性。

备注：梯度的完整推导较长（涉及对半球积分的微分与离散化近似），Lightmass 代码实现遵循该论文思路，可在 IrradianceCache 或 Gradients 相关文件中查找。

---

### 4.7 体积光照图的球谐投影

- 在 Probe 位置 p，对方向集 {ωj} 采样 Li(ωj)，将其投影到球谐基 Ylm(ω)：
  - clm = ∫Ω Li(ω) Ylm(ω) dω ≈ (4π/N) Σ_j Li(ωj) Ylm(ωj)（若均匀方向采样）
- 运行时通过 SH 重建方向分布，供动态物体估计间接光照。Lightmass 会对系数做色彩空间/量化压缩以控制体积数据大小。

---

## 5. 关键代码执行路径（伪代码导览）

以下为典型主流程的伪代码，便于你在源码里逐段对应：

```text
Main():
  Scene = ImportSceneFromSwarmCache()
  BuildAccelerationStructure(Scene.Geometry)
  PreprocessLights(Scene.Lights)
  
  // Direct lighting (per mapping chunk)
  for each MappingChunk in DistributeBySwarm(Scene.Mappings):
    ComputeDirectLighting(MappingChunk, Scene, Accel)

  // Global photon map
  Photons = []
  for Light in Scene.Lights:
    EmitAndTracePhotons(Light, Scene, Accel, Photons, Settings)
  PhotonMap = BuildBalancedKDTree(Photons)

  // Final gather + irradiance cache
  IrrCache = CreateIrradianceCache(Settings)
  for each MappingChunk:
    for each Texel in MappingChunk:
      if IrrCache.HasGoodRecordsAround(Texel):
        Indirect = IrrCache.Interpolate(Texel)
      else:
        Record = ShootHemisphereRays(Texel, Scene, Accel, PhotonMap, Settings)
        IrrCache.Insert(Record)
        Indirect = Record.E
      StoreLightmapTexel(Texel, Direct + DirectionalEncoding(Indirect))

  // Volumetric Lightmap
  VLM = BuildVolumetricLightmap(Scene, Accel, PhotonMap, Settings)

  ExportResultsToSwarm(Lightmaps, VLM, AuxData)
```

在源码中可搜以下函数/类名来定位：
- ImportScene / StaticLightingScene / StaticLightingMesh / StaticLightingTextureMapping
- BuildAccelerationStructure / KDOPTree / Intersect
- ComputeDirectLighting / ShadowRay / AreaLightSample
- EmitAndTracePhotons / PhotonMap / BalanceKDTree / KNearest
- IrradianceCache / CacheRecord / Interpolate / ComputeGradients
- VolumetricLightmap / SHCoefficients / Probe

---

## 6. 设置参数如何影响算法与性能

常见 WorldSettings/Lightmass 设置（名称以源码与编辑器 UI 为准，含典型影响）：
- StaticLightingLevelScale
  - 缩放几何/场景尺度影响采样半径、缓存距离度量。过小导致采样不足，过大导致过度平滑。
- NumIndirectLightingBounces
  - 光子追踪/Final Gather 的反弹次数上限。增加提升真实感但成本上升。
- IndirectLightingQuality
  - 影响 Final Gather 射线数、缓存阈值、采样层级。数值越高质量越高但时间增长。
- IndirectLightingSmoothness
  - 控制插值平滑程度与缓存半径。过大易糊、过小易噪点。
- Environment Color/Intensity
  - 直接影响基底辐照度偏置与颜色溢出。
- Lightmass Importance Volume / Portals
  - 显著影响采样集中度和噪点（尤其室内）。
- Volumetric Lightmap 细节（Cell Size、Detail Cell Density 等）
  - 控制 VLM 密度与大小，影响动态物体的间接光质量与内存/烘焙时间。

实用建议：
- 室内优先设置 Importance Volume 覆盖可见区域；复杂开口配合 Portal。
- 提高质量时优先增大 IndirectLightingQuality 与 Final Gather 射线，缩小 Smoothness。
- 反弹次数在 2–4 往往收益最佳；更高需权衡时间。
- 体积光照若用于高移动性场景，适度增密 Probe 网格并检查内存占用与插值伪影。

---

## 7. 工程实现细节与并行/分布式

- Swarm 分发按 Mapping（Texture/Vertex）切块并行，跨进程/跨机器。
- Lightmass 进程内部多线程：加速结构构建、射线查询、Final Gather 都有线程池化的循环。
- 缓存/PhotonMap 为只读查询，多线程安全；写入阶段需局部缓冲后再合并。
- 数值稳定性：颜色空间线性化、能量保持（分光谱通道处理）、俄轮盘的吞吐量校正。

---

## 8. 局限性与近似

- 主要针对漫反射间接光；镜面/光泽间接一般不经 Lightmass 预计算（由运行时反射/捕获处理）。
- 焦散通常未特别强调单独的“焦散光子图”；复杂折射/透射仅有限近似。
- 纹理缝、UV 展开不良会造成漏光/接缝；需良好的 Lightmap UV。
- 门户与重要体积配置不当会导致室内噪点与过曝。

---

## 9. 参考论文与资源（按主题）

全局照明与核心算法：
- Kajiya, 1986. The Rendering Equation.
- Jensen, 1996/2001. Photon Mapping（论文与专著：Realistic Image Synthesis Using Photon Mapping）.
- Ward, Heckbert, 1992. Irradiance Gradients.
- Ward, Rubinstein, Clear, 1988. A Ray Tracing Solution for Diffuse Interreflection.

采样与低差异序列：
- Halton, 1960. On the efficiency of certain quasi-random sequences.
- Sobol, 1967. On the distribution of points in a cube.
- Shirley, 1991/1996. Stratified sampling of the sphere/hemisphere.

方向性编码与 SH：
- Ramamoorthi, Hanrahan, 2001. An Efficient Representation for Irradiance Environment Maps.
- Green, 2003. Spherical Harmonic Lighting: The Gritty Details.

Lightmass/UE 相关公开资料（作者与主题）：
- Daniel Wright 等（Epic Games）关于 Lightmass 的演讲与课程资料（GDC/SIGGRAPH 课程）。主题围绕：基于光子映射+最终聚合的静态 GI、方向性 Lightmap、体积光照图与工程化实践。
- Unreal Engine 文档：Lightmass 全局光照、Lightmass Portals、Volumetric Lightmap、Directional Lightmaps 的使用说明与参数释义。

提示：以上资料可用标题与作者检索。源码侧则以“PhotonMap/IrradianceCache/FinalGather/VolumetricLightmap”等关键词直接查找实现。

---

## 10. 实用检查清单（阅读与验证）

- 在 UnrealLightmass 工程内逐个确认：
  - Photon 发射路径：Light→EmitPhotons→KDTree 构建→KNN 查询接口
  - Final Gather 射线生成（Halton/Sobol）与可见性查询
  - Irradiance Cache 插入与插值的半径、权重、梯度计算
  - Volumetric Lightmap 的 Probe 采样、SH 投影与数据压缩/打包
  - 直接光对不同光型的 NEE 采样实现
- 小型场景回归：
  - 仅一盏 Area Light + 白盒室内：开启/关闭 Portal 与 Importance Volume 对比
  - 提高/降低 IndirectLightingQuality 检查噪点与时间变化
  - 增大/减小 Smoothness 检查糊化与接缝
  - NumIndirectLightingBounces 从 1 到 4 的光能分布变化
  - VLM 密度变化下动态物体阴影/漏光情况

---

## 11. 附：源码检索指引（关键词）

- “UnrealLightmass” “StaticLighting” “Mapping” “PhotonMap” “IrradianceCache”
- “FinalGather” “KDOPTree” “IntersectRay” “Halton” “Sobol” “Hammersley”
- “VolumetricLightmap” “SHCoefficient(s)” “BentNormal” “DirectionalLightmap”
- “ImportanceVolume” “Portal” “Swarm” “Task” “Job”
- “NumIndirectLightingBounces” “IndirectLightingQuality” “IndirectLightingSmoothness”
- “GatherSample(s)” “CacheRecord” “Gradients”

---

## 12. 结语

UE4.27 Lightmass 以“光子映射 + 最终聚合 + 辐照度缓存”为主干，辅以方向性编码与体积光照图，形成了工程化、可分布式的静态全局光照管线。理解其源码，建议在掌握上述数学估计器与数据结构后，按“导入/加速 → 直接光 → 光子图 → Final Gather/Cache → VLM/方向编码”的顺序阅读；与此同时，用小场景反复验证参数对质量与性能的影响，将有助于迅速建立“代码—公式—画面”的三方对照关系。



> 如果想阅读UE4.27 Lightmass ，并移植或参考实现一部分功能，以什么方式或者顺序开始阅读该部分代码，如果考虑实现部分功能，有什么建议和指导

# UE4.27 Lightmass 阅读与移植实战路线（顺序、方法、实现建议）

目标：
- 给出一套“从零到可改”的阅读顺序与调试方法。
- 如果你计划移植或参考实现部分功能，提供最小可行实现（MVP）与工程化建议。
- 尽量减少“看不进去”的痛点：从跑通、能观察、能替换、能验证四步走。

提示：
- 以下提到的类/函数多为关键词与惯用命名，具体位置与名称以你本地 UE4.27 源码为准，请配合全文检索（ripgrep/VS 全局搜索）定位。

---

## 一、阅读与调试的“正确打开方式”

1) 准备环境
- 构建 UE4.27（编译 Programs/UnrealLightmass）。
- 建议在 Windows + Visual Studio 下调试（Linux/Clang 也可），确保你能生成可调试的 UnrealLightmass 可执行。

2) 跑通一个最小场景
- 建一个仅含：一个房间（盒子）、一个漫反射材质、一个点光/矩形光、一个 Lightmass Importance Volume 的关卡。
- 从 Editor 触发 Build Lighting，一次完整烘焙。确认 Swarm 正常、UnrealLightmass 进程可启动并退出。

3) 断点与日志抓手
- 将 VS 设置为“附加到进程”（Attach to Process）→ 在 Build Lighting 时附加到 UnrealLightmass.exe。
- 在以下模块埋断点/日志（搜索关键词）：
  - 场景导入：Importer/StaticLightingScene/StaticLightingMesh/Mapping
  - 直接光：DirectLighting/Shadow/AreaLightSamples
  - 光子映射：EmitPhotons/PhotonMap/BalanceKDTree/KNearest
  - Final Gather/缓存：FinalGather/IrradianceCache/Interpolate/Gradients
  - 体积光照图：VolumetricLightmap/SHCoefficients/Probes
- 在上述位置打印（或观察）：
  - 导入统计：静态网格数、三角形数、Mapping 数、每张 Lightmap 的分辨率。
  - 光源统计：类型、强度、单位、面积。
  - 射线统计：总数、命中率、平均深度。
  - 光子统计：发射数、存储数、KD 构建时间、KNN 查询平均耗时。
  - 缓存统计：Irradiance Cache 命中率、插值邻居数分布、半径分布。
  - 输出统计：每张 lightmap 的写回时间与像素填充率。

4) 跟踪“一枚 texel 的一生”
- 选一个静态网格的一块 UV 图块，定位其 TextureMapping 对象的 GUID。
- 给该 Mapping 的处理流程加日志：导入→直接光→间接光（缓存命中/新建记录）→写回。
- 用这条“单像素链路”贯穿你后续的所有阅读与修改，能极大降低复杂度。

---

## 二、源码阅读顺序（由外到内、由易到难）

建议按以下顺序逐层深入，并在每一层设置“可观察点”（日志/计数/可视化切片）。

1) 进程入口与 Swarm 任务编排
- 关键词：UnrealLightmass main、Swarm、Job/Task、Mapping 分发、ImportScene
- 目标：理解 Lightmass 作为独立进程如何接收 Editor 导出的场景与任务。确认每张 Lightmap 或 VertexMapping 如何被切成任务分片。

2) 场景导入与静态表示（最重要的“桥”）
- 关键词：StaticLightingScene、StaticLightingMesh/Vertex、StaticLightingTextureMapping/VertexMapping、Material、Light、ImportanceVolume、Portal
- 目标：摸清 Lightmass 内部的数据结构（网格、材质、光、Mapping、场景边界）。这一步决定移植时你要定义的最小接口。

3) 加速结构与射线接口
- 关键词：BuildAcceleration、KDOPTree/BVH、IntersectRay、Ray/Hit、Visibility
- 目标：确认你可以从任意点/方向做可见性测试和场景求交。移植时可直接替换为 Embree 等库加速。

4) 直接光与阴影（建议第一个能“看见效果”的模块）
- 关键词：DirectLighting、ShadowRay、AreaLightSamples、Next Event Estimation
- 目标：跑通点光/方向光/矩形光的直接光与阴影，验证强度单位、衰减/余弦项、可见性偏移（epsilon）。

5) Final Gather（基础版）与 Irradiance Cache（插值）
- 关键词：FinalGather、GatherRays、IrradianceCache、CacheRecord、Interpolate、Gradients
- 目标：先实现没有梯度的缓存插值（只用位置/法线权重），再看梯度优化与半径估计。确保缓存命中率与插值质量可视化。

6) 光子映射（Photon Map）
- 关键词：EmitPhotons、Photon、PhotonMap、BalanceKDTree、KNearest、ConeFilter
- 目标：先实现全局 diffuse 光子图，用 kNN 密度估计辅助 Final Gather。关注俄轮盘、能量归一化、滤波核。

7) 体积光照图（Volumetric Lightmap）
- 关键词：VolumetricLightmap、Voxel/Probe、SHCoefficients、Tree/Brick
- 目标：理解其布点策略与 SH 投影，作为高级功能可后置。

8) Lightmap 输出与方向性编码
- 关键词：Directional Lightmap、Bent Normal、Encode/Decode、Packing
- 目标：至少理解强度/方向性两个通道的编码方式，移植时可先做最简单的非方向性三通道。

阅读习惯建议：
- 每读完一层，做一个“对照实验”：只切换该层开关，验证画面或统计如何变化。
- 以“最小场景 + 小差异切换（A/B）”逼你理解该层的真实作用。

---

## 三、移植/参考实现的“最小可行产品”（MVP）

如果你要脱离 UE 做参考实现，建议这样切片与排序：

阶段 0：基础设施
- 使用 C++17 + Embree（或其它 BVH）+ Eigen/GLM（向量）+ PCG/MT RNG。
- 定义最小场景接口：
  - 三角网格：位置/法线/切线/材质 ID；Lightmap UV（第二 UV 集）。
  - 材质：漫反射反照率 ρ（Lambert）。
  - 光源：点/方向/矩形（面积），强度/颜色/尺寸/方向。
  - Mapping：每个网格的 Lightmap 分辨率与 UV→世界的采样迭代器。
- 输出：每个网格一张 RGB 贴图（EXR/PNG）。

阶段 1：直接光 + 硬阴影
- 面向每个 texel：根据其 UV 找到落在的三角形，插值世界位置/法线。
- 对每盏光做 N 次样本（点/方向光可 N=1；面积光 N>=16），做可见性检测，累加直接光。
- 重点：单位一致性（UE 常用厘米）、余弦/距离平方/可见性偏移 epsilon。

阶段 2：面积光软阴影 + 天空光
- 面积均匀采样 + NEE；天空光半球采样（可先用常量天空）；门户/重要体积暂不实现。
- 引入低差异序列（Halton/Sobol）。

阶段 3：Final Gather + Irradiance Cache（不带梯度）
- 为稀疏“缓存点”发射半球射线估计辐照度 E，并存储位置/法线/半径/结果。
- 查询时按 Ward/Heckbert 风格权重插值（位置距离/法线差异），可先不用梯度。
- 半径估计：基于邻域遮挡/曲率简单启发或固定比例（随场景尺度）。

阶段 4：光子图（可选但推荐）
- 对每盏光发射 M 光子，多次漫反射，存储位置+功率，构建 kd-tree。
- Final Gather 时优先查询光子密度估计作为近似，加快收敛与去噪。
- 采用 kNN + 锥形核（cone filter）。

阶段 5：方向性/体积光（进阶）
- Directional Lightmap：存储“强度 + 方向性基”（如 3 方向加权）或低阶 SH。
- Volumetric Lightmap：自适应布点 + SH 投影（L2/L3 阶）。

关键实现提示：
- Texel 迭代：对每个三角形在其 Lightmap UV2 上做栅格化，逐像素计算重心坐标，再插值世界位置/法线（避免纹理接缝处漏采样，配合像素膨胀）。
- 颜色空间：线性空间计算，输出到 EXR 或写 PNG 前再转 sRGB。
- 偏移与漏光：交点沿法线偏移 t_min = max(1e-4, 1e-4 × 场景尺度)；薄墙场景可启用双面材质或背面可见性特殊规则。
- 并行：按图块/三角形切片；线程本地 RNG 与样本序列；锁free 读取加速结构。

---

## 四、你真的会用到的工程化细节（踩坑清单）

- 单位/尺度
  - UE 缺省单位为厘米；射线偏移、光强、面积/立体角单位要一致。移植时统一使用米或厘米，并调参一次性对齐。
- PDF/权重一致性
  - 面积光的几何项 G(x,y) 与采样 pdf p(y) 的匹配；半球采样的余弦权重与 p(ω)=cosθ/π 的抵消。
- RNG 与序列
  - 低差异序列需跳跃（scrambling）避免条纹；多线程时每线程/每像素用不同维度与 index。
- Irradiance Cache 半径
  - 过大糊、过小噪；把半径与“StaticLightingLevelScale / 物体曲率 / 可见性差异”关联；给插值设置法线差阈值。
- 光子能量归一
  - 每盏光的发射光子总能量应等于其总功率；俄轮盘后吞吐量乘以 ρ/p_rr；最终密度估计再除以 πR^2 或 kNN 归一常数。
- UV 接缝与膨胀
  - 生成 Lightmap 时对每个 chart 做像素膨胀（dilate），降低采样穿缝导致的黑边。
- 双面/薄壁
  - 默认背面不参与可见性；有窗帘/纸片类网格需要双面材质，避免可见性穿透导致漏光。
- 性能瓶颈
  - 90% 时间在射线；用 Embree 或 SIMDe 优化；尽早构建、复用加速结构；减少每像素样本，转而提升缓存命中率。
- 调试可视化
  - 输出中间图：仅直接光、仅间接光、AO、缓存影响半径、光子密度热力图、FG 射线方向分布、Bent Normal。

---

## 五、在 UE4.27 内部“对着改”的建议

如果你想在 UE 里直接增强/替换 Lightmass 的部分能力：

- 先不碰 Swarm/导出格式，专注计算核心
  - 在 DirectLighting、FinalGather、PhotonMap 等模块内部打开开关与插桩，验证你的估计器或采样策略。
- 以特性为单位做“最小替换”
  - 例如只替换面积光采样分布、Final Gather 的样本布局、Irradiance Cache 的插值权重函数、光子滤波核。
- 增量验证
  - 每次修改都用最小场景 A/B 对比 + 统计打印（射线数、方差、耗时）。
- 质量参数接入
  - 把新特性挂到 IndirectLightingQuality / Smoothness 或单独的控制台变量，便于回退。
- 不建议第一步就改导入格式/Swarm
  - 那是耦合面最大的一层；确认你的计算核心稳定后再考虑。

---

## 六、实现参考的模块接口（便于移植时“抄骨架”）

- IScene
  - triangles(): 位置/法线/材质
  - lights(): 类型/强度/几何
  - intersect(ray): 返回 hit {p, n, triID, matID}
- IAccel
  - build(triangles), intersect(ray)
- IBakeTarget
  - for_each_texel(meshID, callback(uv, triID, barycentric))
- Sampler
  - next2D()/next1D()，支持 Halton/Sobol/蓝噪声
- DirectLightingPass
  - evaluate(texel) → Ld
- PhotonMap
  - emit(scene, M), knn(query, k) → {photons}
- IrradianceCache
  - lookup(query) 或 insert(record), interpolate(query)
- Output
  - write_lightmap(meshID, image)

---

## 七、验证与基准

- 场景集
  - Cornell Box、室内走廊、带窗户室内（Portal 场景）、室外阴影场景、薄壁房间。
- 指标
  - 总耗时、射线数、缓存命中率、每像素样本数、光子数量/内存、峰值内存。
- 画质
  - 噪点水平、漏光/接缝、阴影软硬过渡、能量守恒（墙面亮度变化）。

---

## 八、时间安排建议（4–6 周）

- 第 1 周：搭建环境、能附加调试、跑通最小场景；读完“导入/场景/加速/直接光”并做 A/B。
- 第 2 周：实现面积光与天空光的重要性采样；把直接光结果写回并对齐 Editor 结果。
- 第 3 周：实现 Final Gather 基础版 + Irradiance Cache 插值；做缓存命中率调优。
- 第 4 周：加入光子映射（发射/存储/KNN/滤波）；与 FG 结合，降低射线数。
- 第 5–6 周：体积光照图与方向性编码（可选），参数打磨与回归测试。

---

## 九、若只移植“某一功能”的具体建议

- 目标：把 Lightmass 的“Final Gather + Irradiance Cache”思想移植到你的烘焙器
  - 先实现缓存插值权重：位置距离/法线角差两项即可
  - 缓存记录的“有效半径”：与可见性变化（命中率/遮挡差）挂钩
  - 射线选择：余弦加权 + 低差异序列；每记录 128–512 条射线起步
  - 插值邻居：k=8–16，设最大法线差阈值，避免越界插值
- 目标：把“光子密度估计”移植
  - 每盏光发射 N 光子（按能量分配），俄轮盘维持能量守恒
  - KNN=50–100，锥形核 α≈1.1–1.3，逐场景校准
  - 与 Final Gather 融合：把光子密度作为 FG 样本命中时的 Li 近似，减少二次可见性开销

---

## 十、最后的建议

- 先让“直接光 + 基础 Final Gather”稳定产出可用图，再引入光子图；不要一开始就齐活所有模块。
- 多做“统计 + 可视化”而不是仅看最终图：你看得到问题，才调得动质量/性能。
- 不急于复刻所有 UE 的工程细节（Swarm、导出格式、VLM 压缩），优先把物理估计器与可见性、采样打牢。
- 当你能在自己的实现中稳定再现 UE 的几个典型画面（室内/门户/室外阴影），再考虑做方向性编码、VLM 等进阶项。

如果你告诉我你打算优先移植哪一段（例如：面积光软阴影、Irradiance Cache、光子图），我可以按该目标给出更细的任务拆解与参数初值。