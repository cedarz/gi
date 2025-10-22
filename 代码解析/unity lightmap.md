> lightmap有什么工业级的参考实现？

下面按“可读源码的开源实现”和“商用品/引擎内置”两类，列出业界常用、可对标或可直接参考的 lightmap（离线烘焙全局光照）实现与组件，并补充一套可落地的自建方案拼装清单。

开源（可读源码，适合学习/改造）
- Google Filament — Light Baker
  - 面向实时渲染引擎的离线路径追踪烘焙工具，支持烘焙到贴图、方向性光照等，代码工程清晰，便于参考整体架构与采样/去噪流水线。
- Godot Engine — LightmapGI（CPU/GPU）
  - 引擎内置的光照贴图烘焙器，支持路径追踪、方向性 lightmap、光照探针、失真/缝隙修复（dilation）、去噪等。适合参考编辑器集成与资产管线。
- Blender — Cycles Baking
  - 生产级路径追踪器的贴图烘焙（Combined/Direct/Indirect/AO 等通道），可学习采样/AOV/去噪/色彩空间与 UDIM/多对象烘焙流程；脚本化流程完善。
- xatlas / thekla_atlas（UV 展开与打包）
  - 生成 Lightmap UV、切分 chart、无缝打包与像素边距（padding/dilation）。工业界常用的轻量级参考实现。
- Microsoft UVAtlas（DirectXMesh 套件）
  - 另一套稳定的 Lightmap UV 生成与打包库，实现思路可作对照。
- Intel Embree（CPU 光线追踪内核）
  - 工业界广泛采用的高性能 BVH/射线求交库，很多开源/商用烘焙器都用它作为加速结构底座。
- Intel Open Image Denoise（OIDN）
  - 生产级去噪库，配合法线/反照率等 AOV 可显著降低蒙特卡洛噪点，是离线 lightmap 烘焙的常见标准组件。
- ericw-tools: light（Quake 系列地图工具）
  - 开源的辐射度/多次弹射烘焙器，支持“deluxemap”（方向性 lightmap 的一种），历史悠久、代码易读，适合理解传统 radiosity 与方向性存储。
- ands/lightmapper（单文件 C 库）
  - 轻量化 CPU lightmapper，便于迅速理解“逐 texel 路径追踪 + 重要性采样 + 去噪/扩展”最小闭环。

商用品/引擎内置（工业落地）
- Unreal Engine — Lightmass / GPU Lightmass
  - UE 的静态光照烘焙器。CPU 版历史成熟（irradiance cache/final gather 等），GPU 版使用 RTX 加速的路径追踪，支持多弹射、IES/区域光、发光材质、方向性 lightmap、分布式/多 GPU 等。源码可读（受 UE 许可）。
- Unity — Progressive Lightmapper（CPU/GPU）
  - Unity 内置的渐进式烘焙器，支持路径追踪、多反弹、方向性 lightmap、光照探针/Probe Volumes、去噪（OIDN/OptiX）与失真修复。闭源但文档完善。
- Bakery GPU Lightmapper（Unity 生态）
  - 行业内口碑极佳的第三方 GPU 烘焙器，基于 OptiX/RTX，支持复杂灯光/IES/发光、门户/重要性采样、级联/分块烘焙、UV 自动化与高质量去噪，项目级大规模落地。
- Geomerics Enlighten（预计算/实时 GI）
  - 偏向预计算 + 运行时更新的 GI 技术，虽不专注“纯 lightmap”路径追踪，但在大型项目中作为烘焙/预计算参照仍具代表性。
- 传统/历史方案：Autodesk Beast、Maya Turtle
  - 早期大量项目使用的静态光照烘焙器，可查阅其工作流与参数体系作为对照。
- DCC 渲染器的“烘焙到贴图”
  - V-Ray、Arnold、Corona、Renderman 等均支持把直/间接光照烘焙为纹理（Render to Texture/Bake），工程上常用于离线高质烘焙再回灌游戏引擎。

可复用的“工业级”模块与特性清单（选型/自研时对标）
- 加速结构与采样
  - Embree/OptiX、MIS 对灯光/环境的重要性采样、门户采样、环境贴图分层采样、地面/天空分离采样。
- 蒙特卡洛稳定性
  - 自适应采样、渐进式渲染（进度可视）、可重复随机序列、蓝噪/低差异序列（Sobol/CMJ）。
- 质量与一致性
  - 多反弹路径追踪、能量守恒 BSDF、法线与切线空间一致性（MikkTSpace）、方向性 lightmap（RNM/低阶 SH/主导方向）与 Specular Occlusion。
- UV / 资产管线
  - 自动 Lightmap UV（xatlas/UVAtlas）、chart 自适应像素密度、gutter/padding、mip-aware dilation、重叠检测与修复、锥体背面/厚度补偿。
- 去噪与 AOV
  - OIDN/OptiX AI Denoiser，提供 Beauty/Albedo/Normal/Depth/AO 等辅助通道。
- 规模化
  - 分块/分图集烘焙、可中断断点续烘、网络分布式/多 GPU、内存外（out-of-core）纹理与几何加载。
- 动态物体支持
  - Light Probes/Probe Volumes、网格体积探针插值、混合光（Baked Indirect/Shadowmask）一致性。
- 调试/可视化
  - Texel 可视化（无效 texel、采样数、误差热力图）、光能传输/泄漏检测、阴影偏移/漏光修正工具。

想自己搭一套“开源工业级”轻量烘焙器（推荐组合）
- 光线追踪内核：Embree（CPU）或 OptiX（GPU）
- UV 展开/打包：xatlas
- 采样与渲染：路径追踪（多反弹 + MIS + 环境采样），按 texel 反向映射至三角面采样
- 去噪：OpenImageDenoise（提供 Albedo/Normal AOV）
- 贴图后处理：mip-aware dilation、色彩空间（线性/ACEScct/OCIO）
- 方向性存储：RNM（3 通道基底）或 2 阶 SH（9 系数压缩到多通道）
- 批处理与分布式：任务分片=图集/瓦片/mesh 子集，渐进式写回 EXR/TGA

补充参考关键词（论文/方法）
- Irradiance Caching/Gradients（Ward & Heckbert）
- Radiosity Normal Mapping（RNM）
- Spherical Harmonics（SH）用于方向性 lightmap
- Deluxemap（方向性法线光照贴图，Quake 系）
- Gradient-Domain/Guided Denoising for Monte Carlo

如果你更关注某个方向（开源可改造、Unity/UE 最佳实践、GPU 高速、超大场景分布式等），告诉我目标平台与约束，我可以给出更精确的选型和落地配置。



> 金属度粗糙度的pbr工作流的材质资源，目前已经有了path tracing渲染代码，如何设计lightmap算法？直接光照、间接光照，预计算哪一部分；预计算的结果如何使用？以及其他我没有想到或者没有提及到细节，请给出详尽的指导过程，以辅导我完成path tracing + lightmap项目。

下面给你一套“从零到上线”的设计与实现路线，针对金属度-粗糙度（Metallic-Roughness）PBR 工作流且你已经有路径追踪（path tracing）代码的前提，帮助你把 Lightmap（静态全局光照）整合进项目。重点回答：

- 哪些部分预计算、哪些保持实时
- 预计算结果存什么、如何求、如何在运行时使用
- 金属度-粗糙度下的注意事项（尤其是金属的间接、高光/镜面间接）
- 工程化细节：UV、采样、去噪、缝隙、精度、压缩、调试

建议先做“最小可用”版本（非方向 Lightmap，仅烘焙间接漫反射），再迭代到“方向性 Lightmap + 探针 + 反射探针”的工业级组合。

一、总策略（推荐的分工）
- 预计算（离线烘焙）
  - 必做：间接漫反射（Diffuse Indirect Irradiance）
  - 可选：方向性信息（用 L2 SH 或 RNM），支持法线贴图对间接光的影响
  - 可选：AO、Bent Normal（用于间接高光的遮蔽/调制）
  - 可选：Shadowmask（静态-静态阴影遮罩，配合实时直射）
- 实时
  - 直射光（Direct Lighting）：所有直射保持实时（阴影、阴影软硬、IES 等）
  - 间接高光（Specular Indirect）：用预过滤环境贴图（Reflection Probes 或静态环境卷积）+ 粗糙度 MIP，辅以 Specular Occlusion（由 AO/Bent Normal 推导）
  - 动态物体的间接漫反射：Light Probes/Probe Volumes（与光照贴图对齐）

这样做的原因
- 漫反射间接是视角无关、材质几乎无关（不乘以 albedo）的低频量，最适合烘焙为贴图。
- 高光间接（镜面）强烈依赖视角与粗糙度，写进 Lightmap 会爆炸式占用内存且难以随视角变化；用反射探针更合理。
- 直射光实时能给你阴影品质与交互自由度。

二、Lightmap 表示的三种层级（由简到繁）
- Level A：非方向 Lightmap（最小实现）
  - 存储每个 texel 的漫反射“辐照度”E(x) = ∫ L(ω) max(0, n·ω) dω，RGB，线性/HDR。
  - 运行时：Ldiff_ind = (baseColor.rgb * (1 - metallic)) / π * E。
  - 缺点：不响应法线贴图；金属表面的漫反射为零（合理）。
- Level B：方向性 Lightmap（推荐）
  - 存 L2 球谐（SH）“已卷积到朗伯核的辐照度系数”，9 个系数 × RGB（可用半浮/压缩）。运行时用当前世界法线 n 评估 E(n)。
  - 优点：间接漫反射会随法线贴图改变方向响应。
  - 可压缩/裁剪：如果内存紧张，可只存每通道 4–6 个主成分或使用 RNM（3 向基底）权衡质量/体积。
- Level C：扩展通道（按需）
  - AO（单通道或 RGB），Bent Normal（RGB，单位向量）
  - Emissive Contribution 分离通道（如果需要关/开自发光而不重烘）
  - Shadowmask（每 texel 4 通道，每通道映射一盏静态灯的遮蔽，运行时直射乘遮罩）

三、烘焙核心算法（基于你已有的 Path Tracer）
1) 资产与 UV
- 为静态网格生成独立的 Lightmap UV（建议 xatlas/UVAtlas），要求：
  - 无重叠，无翻转（保持一致的三角形朝向），足够的壕沟宽度（gutter/padding）≥ 2px × 最大 mip 层数。
  - Texel 密度按重要性/可见性自适应（可选）。
- 打包到图集：同类材质或空间邻近可分图集；尽量让大 chart 连续、避免窄长碎片。

2) 逐 texel 反向映射与采样
- 对每个有效 texel，反向求取世界空间位置 p、几何法线 Ng、切线基 TBN。
- 微偏移防自相交：p += Ng * epsilon，epsilon 约为 max(1e-4, 1e-3 × 场景尺度) 或基于三角包围盒对角线比例。
- 超采样：在 texel 内做抖动/蓝噪/CMJ 多样本（例如 16–256 spp，可渐进式）。

3) “只采样间接”的积分器改造
- 目标：估计入射辐亮度 L(ω) 的投影，排除“零跳直接光”。
- 做法：
  - 在首跳处禁用对光源的 NEE（Next Event Estimation）或把首跳直射单独计为 E_dir，然后 E_indir = E_total - E_dir；推荐前者以降低差分方差。
  - 允许从第二跳起的 NEE（改善间接收敛）。
  - 俄罗斯轮盘在第二跳后启用，保持能量无偏。
  - 环境光源/天空盒属于“首跳直射”，因此也应在首跳排除；它们的能量会在后续弹射中回流到间接。

4) 投影与累积（两种表示）
- 非方向（Level A）
  - 估计 E = ∫ L(ω) max(0, Ng·ω) dω
  - 采样时用余弦加权半球采样，估计 E ≈ mean[ L(ω_i) ] × π（因为 pdf = cos/π）。
- 方向性 SH（Level B）
  - 我们希望在运行时直接计算 E(n) = ∑ c_j Y_j(n)。
  - 在烘焙时先对“入射辐亮度场 L(ω)”做 SH 投影：c_j^L = ∫ L(ω) Y_j(ω) dω
  - 然后乘以朗伯核的卷积因子得到“辐照度系数”：
    - A0 = π, A1 = 2π/3, A2 = π/4，对应 l=0,1,2 的 9 个基
    - c_j^E = c_j^L × A_l
  - 采样实现：对每个样本方向 ω_i，用 MIS/路径追踪估计 L(ω_i)，对每个基 Y_j(ω_i) 累加
    - c_j^L += L(ω_i) × Y_j(ω_i) / p(ω_i)
  - 最终存的是 c_j^E（每基 × RGB）。
- 注意：用 Ng 还是着色法线 Ns？
  - 投影应该用入射方向本身，与法线无关；但用于“首跳排除直接”的判断要以几何法线 Ng 判定可见半球。

5) 去噪与色彩
- 使用 OIDN/OptiX Denoiser；给去噪器提供 AOV：albedo（1）、normal（Ng 或 Ns）和原图。
- 对 SH 系数做去噪：可对每个系数单独去噪，或先把系数按多个“方向图像”重建近似再去噪后回投（简化起见：逐系数去噪）。
- 一律在线性色域下工作并存 HDR（半浮 16f/EXR）。
- 防火花：可对极端高亮做软裁剪或采用鲁棒均值（例如 winsorized mean）。

6) 缝隙修复与 MIP
- 对每个 chart 做 dilation（mip-aware），至少延申 8–16 像素，避免采样越界。
- 生成 MIP 时使用盒滤，避免锐化；跨 chart 边界禁止滤样。

7) 质量与收敛
- 自适应采样：估计每 texel 方差，继续对高方差 texel 追加样本，直到方差/样本数或时间预算达标。
- 分块/多线程/分布式：按图集瓦片切分，支持中断续烘。

四、运行时着色如何用这些数据
1) 漫反射间接（非方向）
- E = texLightmap(u2).rgb（线性/HDR）
- Ldiff_ind = (baseColor.rgb × (1 - metallic)) / π × E

2) 漫反射间接（方向性 SH，推荐）
- 从贴图读取 9×RGB 系数 c_j^E
- 以世界法线 n（含法线贴图，TBN->World）评估 Y_j(n) 并累加：E(n) = Σ c_j^E · Y_j(n)
- Ldiff_ind = (baseColor.rgb × (1 - metallic)) / π × E(n)

3) 直射光（实时）
- 按你的实时管线（PBR Cook-Torrance GGX）计算，阴影实时。
- 如果实现 Shadowmask：直射项乘每灯的 mask 通道（静态-静态阴影）。

4) 间接高光（IBL）
- 采用预过滤环境贴图（PMREM）或反射探针；按粗糙度选择 MIP。
- F0 = lerp(0.04 × specularColor, baseColor, metallic)
- Lspec_ind = PrefilteredEnv(R, roughness) × Fresnel_Schlick(V·H/F0) × VisibilityTerm(roughness, N·V, N·L) × SpecularOcclusion
- Specular Occlusion（建议做法）
  - 至少：基于 AO 的近似（简单鲁棒）
    - specOcc = lerp(1, AO, saturate((roughness - r0)/(1 - r0)))，r0≈0.2–0.3
    - 解读：粗糙大时镜面更低频，更多受遮蔽；粗糙小则少衰减。
  - 更好：Bent Normal + 粗糙度的圆锥近似
    - 设 Nb 为 bent normal，R 为反射方向，θc ≈ acos(1 - roughness^2) 作为反射 lobe 半角近似
    - t = smoothstep(cos(θc), 1, dot(R, Nb))；specOcc = lerp(AO, 1, t)
    - 直觉：若 R 落在可见锥内（对齐 Nb），衰减小；偏离则靠 AO 衰减
  - 注意：这是工程近似；如需更物理，可研究 specular visibility 的经验模型（Frostbite/UE 论文），但以上两种足够实用稳定。

5) 动态物体的间接漫反射
- 使用 Probe/Probe Volume，将同一烘焙的“辐照度 SH”插值得到 E(n)；保证光照贴图与探针的一致曝光与单位。

五、金属度-粗糙度工作流的要点
- 金属（metallic≈1）漫反射组分为 0，Lightmap 的漫反射能量不会直接显色；间接高光由 IBL/探针提供。
- 非金属（metallic≈0）使用 Lightmap 提供的 E(n) 乘以 baseColor/π。
- 介于两者之间时，按标准金属度混合。
- 避免把 albedo 乘进 Lightmap：Lightmap 存“材质无关”的光照量，允许材质换皮不重烘。
- 自发光材质影响会进入 E(n)；若需在运行时开关自发光，单独烘一张 emissive-only 通道（或为 emissive 对象设独立 Lightmap 集）。

六、可选的“直接光预计算”方案
- Baked Indirect（推荐默认）：只烘焙间接，直射实时。
- Subtractive/Full Baked：直射也烘到 Lightmap，运行时成本低但缺乏交互/时间变化。
- Shadowmask：直射实时，但静态-静态遮蔽预计算为每 texel RGBA 掩码（1 texel 支持最多 4 灯或用图集页扩展）。运行时：直射项 × mask，动态-静态遮蔽仍实时。

七、数据格式与压缩
- 存储格式
  - 非方向 E：RGB16F（运行时可压缩为 BC6H）
  - SH（9×RGB）：可拆成多张 RGBA16F 纹理（例如 3 张，每张 3 系数×RGB + 1 空闲通道），或压缩为 BC6H；也可用 LogLuv 变体，但复杂。
- 色彩空间：加载/存储保持线性；Tone mapping 在最终合成后做。
- 动态范围：避免硬裁剪；必要时有序压缩，比如 RGBE/BC6H。

八、实现伪代码（核心环节）
1) 烘焙（方向性 SH 版本，间接-only）
```cpp
for (Atlas& atlas : atlases) {
  for (Texel t : atlas.validTexels()) {
    RNG rng(seedFrom(t));
    SH9 accumRGB = {}; // 9 coeffs per channel
    float wsum = 0.0f;

    for (int s = 0; s < spp; ++s) {
      // 反向映射到三角形
      SurfHit surf = BackProject(t, rng.jitterInTexel());
      float3 p = OffsetByNg(surf.position, surf.normal_g);
      // 首跳只收间接：禁用直射 NEE
      Ray ray = MakeHalfSphereRay(p, surf.normal_g, rng); // 分布可自适应
      Spectrum L = TraceIndirectOnly(ray, rng, /*disableNEEAtFirstBounce=*/true);

      // 将入射辐亮度投影到 SH（L(ω)）
      float3 w = ray.dir; // 入射方向
      float Y[9];
      EvalSH9(Y, w); // 实数 SH 基 Y_lm(ω)
      for (int j=0; j<9; ++j)
        accumRGB[j] += L.rgb * (Y[j] / ray.pdf); // MIS 时使用合并后的权重

      wsum += 1.0f; // 或者存累计权重用于鲁棒均值
    }

    // 归一化 + 朗伯卷积因子
    float Al[3] = { PI, 2*PI/3, PI/4 };
    for (int j=0; j<9; ++j) {
      int l = SHBandFromIndex(j); // 0,1,2
      accumRGB[j] *= (1.0f / wsum) * Al[l];
    }

    atlas.storeSH9(t, accumRGB);
  }
}

// 去噪各系数 → dilation → 生成 MIP → 写入纹理
```

2) 运行时（片段着色，方向性 SH）
```glsl
// 输入：baseColor, metallic, normalMap, TBN, viewDir, reflectionProbe
// Lightmap: 9×RGB 系数纹理（可拆多张）
float3 n = normalize( mul(TBN, normalMapSample) ); // 世界法线
float Y[9]; evalSH9_YofN(Y, n);

float3 E = 0;
for (int j=0; j<9; ++j) {
  float3 c = sampleSHCoeffTexture(j, uv2); // 每基 RGB
  E += c * Y[j]; // 得到辐照度
}

float3 diffuseColor = baseColor * (1.0 - metallic);
float3 Ldiff_ind = diffuseColor * (E / PI);

// 实时直射 Ldir 实现略

// IBL 镜面
float3 R = reflect(-V, n);
float3 prefiltered = SamplePMREM(reflectionProbe, R, roughness);
float3 F0 = lerp(0.04.xxx * specularColor, baseColor, metallic);
float3 F = Fresnel_Schlick(max(dot(H, V), 0.0), F0);
float specOcc = SpecularOcclusionApprox(AO, roughness, bentNormal, R);
float3 Lspec_ind = prefiltered * F * specOcc;

// 最终能量守恒混合（与直射、烘焙间接叠加）
float3 Lo = Ldir + Ldiff_ind + Lspec_ind;
```

九、常见坑与对策
- 接缝与漏光
  - UV 壕沟不足、dilation 不够 → 增大 padding，mip-aware 扩展
  - 自相交噪点 → 加大偏移或“背面厚度”补偿
- 能量重复/遗漏
  - 确保“首跳直射”只在实时路径里算，不进 Lightmap；避免重复。
  - 环境光不要额外叠加到漫反射（已在间接里）。
- 曝光与单位
  - 如果路径追踪是物理单位（lm/cd/lux），运行时直射与 IBL 的能量单位需一致；否则以“相对能量 + 曝光”方式，统一在相机曝光/色调映射上。
- 去噪失败/过平
  - 提供法线与反照率 AOV 给去噪器；对于 SH，可对每个系数单独去噪，或分通道做频率自适应。
- 方向性 Lightmap 与法线空间
  - SH 评估使用世界法线；法线贴图从切线空间正确变换到世界（MikkTSpace 保一致）。

十、进阶与扩展
- 低体积方向性：RNM/“主导方向 + 各向异性系数”压缩；先实现 SH 再做数据驱动压缩（PCA）。
- 动态天光/时间变化
  - 只改变直射和 IBL；Lightmap 只存间接，仍然大体看起来自然。
- 大场景/分布式
  - 图集瓦片化 + 渐进写回 + 网络分发；OIDN 在线块去噪。
- 调试可视化
  - 显示：texel 有效性、样本数/方差热力图、SH 低/高阶量、间接/直射分离、AO/弯曲法线。

十一、落地建议的最小与完整版本
- 最小版本（1–2 周）
  - 非方向 Lightmap（间接-only，RGB16F）
  - 实时直射 + PMREM IBL + 简单 AO 调制
  - xatlas UV、dilation、OIDN 去噪
- 完整版本（4–8 周）
  - 方向性 SH Lightmap（9×RGB），法线贴图响应
  - Bent Normal + Specular Occlusion 近似
  - Light Probes/Probe Volumes 覆盖动态物体
  - Shadowmask（可选）
  - 资产流水线与调试视图

如果你提供当前引擎/平台（例如 Unity/UE/自研渲染器/移动端）、目标内存预算与是否需要 Shadowmask/Probe Volume，我可以按你的约束把上面的方案收敛成具体的纹理布局、格式、采样数与代码模板。