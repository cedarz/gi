> 根据Radiosity方法的论文和相关的course、tutorial等，给出Radiosity方法详尽的算法解析过程，给出所有相关公式详尽的推导过程，如果公式推导需要其他前置知识，请给出参考和解析，务必使我能够快速看懂并理解；将所有内容整理成markdown格式，方便我后续导出

# Radiosity 方法全解析（含公式推导与实现要点）

本文面向希望系统理解和实现 Radiosity（辐射度/辐照度法）的人群，围绕“从物理到算法”的完整链条，推导全部关键公式，并给出可直接用于实现的步骤与要点。你可以把它作为“从渲染方程到实际代码”的桥梁文档。

目录：
- 0. 读前指南与符号约定
- 1. 背景与直觉
- 2. 辐射度学基础（先修知识）
- 3. 从渲染方程到 Radiosity 积分方程（连续形式）
- 4. 形状因子（Form Factor）的定义与推导
- 5. 离散化与线性方程组（常量基/有限元）
- 6. 求解方法：直接解、迭代、渐进细化（Progressive Radiosity）
- 7. 形状因子计算：解析、半立方体（Hemicube）、半球/蒙特卡洛
- 8. 性质：互易性、能量守恒、收敛性与误差
- 9. 可见性与遮挡处理
- 10. 实现步骤与伪代码
- 11. 高阶与层次 Radiosity（有限元/分层链接）
- 12. 数值稳健性、网格细化与常见陷阱
- 13. 色彩通道与纹理/贴图出图
- 14. 小结与实践建议
- 15. 参考文献（论文、教材与教程）

——

## 0. 读前指南与符号约定

- 单位与符号：
  - 辐射通量 Φ [W]
  - 辐照度 E_in（入射）[W·m⁻²]
  - 辐射亮度 L [W·m⁻²·sr⁻¹]
  - 辐射度/出射度 B（Radiosity，总出射通量密度）[W·m⁻²]
  - 反射率 ρ（Lambert 反射，0–1）
  - 自发射 B_e（有时也记作 E，本文为避免歧义统一记 B_e）
  - 表面法向 n，方向向量 ω
  - 面元面积 A_i，面元 i 的平均量记作下标 i
  - 可见性 V(x,y) ∈ {0,1}
  - 几何项 G(x,y) = (cosθ_x cosθ_y) / r²

- 建议先读第 2 节（辐射度学基础），再读第 3 节推导主方程。

——

## 1. 背景与直觉

Radiosity 解决的是“全局照明中的漫反射能量交换”，假设表面为理想 Lambert 漫反射。其核心思想：
- 将场景表面离散为面元（patch/element）。
- 用形状因子 F_ij 表示面元 i 发出的能量有多少比例到达面元 j。
- 建立线性方程组，解出各面元的出射度 B_i，再渲染显示。

优点：物理上能量守恒，间接光、多次反射自然出现；缺点：主要适用于漫反射，计算可见性与形状因子较重。

——

## 2. 辐射度学基础（先修知识）

核心定义（简明版）：
- 辐射亮度 L(x, ω)：单位面积、单位立体角、单位投影面积的功率密度。沿光线在自由空间保持不变（无参与介质）。
- 辐照度 E_in(x) = ∫_H L_i(x, ω) (n·ω) dω，入射半球积分。
- BRDF f_r(x, ω_i, ω_o)：反射方向分布；Lambert 情况 f_r = ρ/π（与方向无关）。
- 出射亮度（反射部分）对 Lambert：L_r(x, ω_o) = (ρ/π) E_in(x)，与 ω_o 无关。
- 出射度/辐射度 B(x) 定义：B(x) = ∫_H L_o(x, ω_o) (n·ω_o) dω_o。
  - 若出射亮度在半球方向不变（Lambert），则 B = π L_o。
- 自发射（若有）：记作 B_e(x) = ∫_H L_e(x, ω_o) (n·ω_o) dω_o。

结论（Lambert）：
- B(x) = B_e(x) + ρ(x) E_in(x)

——

## 3. 从渲染方程到 Radiosity 积分方程（连续形式）

一般渲染方程（出射亮度）：
- L_o(x, ω_o) = L_e(x, ω_o) + ∫_H f_r(x, ω_i, ω_o) L_i(x, ω_i) (n·ω_i) dω_i

对 Lambert，f_r = ρ/π，与 ω_o 无关 → L_o(x, ω_o) 不随 ω_o 变。对 ω_o 积分得到 B：

- 左侧：∫_H L_o(x, ω_o) (n·ω_o) dω_o = B(x)
- 自发射项：∫_H L_e(x, ω_o) (n·ω_o) dω_o = B_e(x)
- 反射项：
  ∫_H [∫_H (ρ/π) L_i(x, ω_i) (n·ω_i) dω_i] (n·ω_o) dω_o
  = ρ ∫_H L_i(x, ω_i) (n·ω_i) dω_i
  = ρ E_in(x)

得：
- B(x) = B_e(x) + ρ(x) E_in(x)

将 E_in 写成对场景表面的积分。设 y 是场景表面上的点，r = ||x - y||，θ_x、θ_y 分别是光线与对应法向夹角，可见性 V(x,y) ∈ {0,1}。由辐射量不变性与几何关系：

- dE_in(x ← y) = L_o(y → x) (n_x · ω_{x←y}) dω_x
- dω_x = (n_y · ω_{y→x}) dA_y / r²
- L_o(y → x) = B(y) / π （Lambert）

合并：
- dE_in(x ← y) = [B(y)/π] [cosθ_x cosθ_y / r²] V(x,y) dA_y

再对 y 積分：
- E_in(x) = ∫_S [B(y)/π] G(x,y) V(x,y) dA_y

最终得到连续 Radiosity 积分方程（第二类 Fredholm 积分方程）：
- B(x) = B_e(x) + ρ(x) ∫_S K(x,y) B(y) dA_y
- 其中 K(x,y) = [G(x,y) V(x,y)] / π = [cosθ_x cosθ_y / (π r²)] V(x,y)

——

## 4. 形状因子（Form Factor）的定义与推导

定义（面元 i 到面元 j 的形状因子）：
- F_ij = (1/A_i) ∫_{A_i} ∫_{A_j} [cosθ_i cosθ_j / (π r²)] V(x,y) dA_y dA_x

直觉：F_ij 是“i 发出的能量，有多少比例抵达 j”。因此 0 ≤ F_ij ≤ 1。

微分形状因子（点/微面元级）：
- 若 dA_i 很小，dF_{i→j} = ∫_{A_j} [cosθ_i cosθ_j / (π r²)] V dA_j
- 对 j 也微分：dF_{i→j} = [cosθ_i cosθ_j / (π r²)] V dA_j

Nusselt 类比（将表面积分转化为半球立体角积分）：
- 利用 dω = (cosθ_j / r²) dA_j，代入上式：
- dF_{i→(方向域)} = (cosθ_i / π) dω
- 因此，对某个接收物体 j：
  F_ij = (1/A_i) ∫_{A_i} [ (1/π) ∫_{Ω_i(j)} cosθ_i dω ] dA_i
  其中 Ω_i(j) 是从 i 可见并射向 j 的半球方向域。
- 这正是半立方体／半球采样方法的理论基础。

重要性质与证明概览：
- 互易性（Reciprocity）：A_i F_ij = A_j F_ji
  - 证明要点：K(x,y) 对 x、y 对称（G 与 V 都对称），交换积分次序即可。
- 能量守恒（封闭场景）：
  - 对任意 i，有 ∑_j F_ij = 1（含所有可达表面及“环境/穹顶”）。若场景完全封闭且不允许能量逃逸，则 ∑_j F_ij = 1；若存在“外部天空”这一环境面元，则将其一并纳入求和同样成立。
  - 证明要点：用 Nusselt 类比将对所有表面的积分变为对整个半球的 ∫ cosθ/π dω = 1。

——

## 5. 离散化与线性方程组（常量基/有限元）

最常用的“常量基”（每个面元上 B 近似常数）+ 面元平均：
- 对面元 i 取面积平均（或选定配点）：
  B_i = B_{e,i} + ρ_i ∑_{j=1}^N F_ij B_j

矩阵形式（按单色通道）：
- B = E + R F B
- (I − R F) B = E
  - B, E ∈ ℝ^N
  - R = diag(ρ_1, ..., ρ_N)
  - F ∈ ℝ^{N×N}，稠密，F_ij ≥ 0
  - 若多通道（RGB），F 相同，R 与 B、E 分通道解。

高阶有限元（概念）：
- 令 B(x) ≈ ∑_k β_k N_k(x)，N_k 是基函数（如顶点基/双线性/层次基）。
- 加权残量或 Galerkin：∑_k β_k ⟨W_i, N_k⟩ − ⟨W_i, B_e⟩ − ⟨W_i, ρ K B⟩ = 0
- 一般得到：A β = b，其中 A_ik = ⟨W_i, N_k⟩ − ⟨W_i, ρ K N_k⟩。
- 优点：更平滑、减少走样；代价：装配复杂。

——

## 6. 求解方法：直接解、迭代、渐进细化

- 直接解：对 A = I − R F 做 LU/Cholesky 分解
  - 复杂度 O(N³)，存储 O(N²)，仅适合 N 较小或做研究验证。

- 迭代法：
  - Jacobi：B^{k+1} = E + R F B^{k}
  - Gauss–Seidel（按 i 顺序更新）：
    - B_i^{new} = [E_i + ρ_i ∑_{j<i} F_ij B_j^{new} + ρ_i ∑_{j>i} F_ij B_j^{old}] / (1 − ρ_i F_ii)
    - 平面面元常有 F_ii = 0（自身不可见）。
  - SOR（超松弛）：B_i ← (1−ω) B_i + ω B_i^{GS}，选 ω∈(1,2) 加速。
  - 收敛条件（充分）：谱半径 ρ(RF) < 1，一般 ρ_i<1 保证能量递减；实际收敛与网格与场景相关。

- 渐进细化 Progressive Radiosity（射能量 shooting）：
  - 思想：每次选择“未射出能量”最大的面元 p，将其未射能量分发给所有接收面元。
  - 初始化：B_i = B_{e,i}；未射能量 ΔB_i = B_{e,i}
  - 迭代：
    1) 选 p = argmax_i (ΔB_i A_i)（最大未射出通量）
    2) 对所有 j：接收的平均辐照度增量 ΔE_j = (ΔB_p A_p F_pj) / A_j
    3) 反射为出射度增量：ΔB_j^ref = ρ_j ΔE_j
    4) 更新：B_j ← B_j + ΔB_j^ref，ΔB_j ← ΔB_j + ΔB_j^ref
    5) 清零射出者：ΔB_p ← 0
  - 说明：第 2 步的 A_p/A_j 比例可用互易性消去：
    - 因 A_p F_pj = A_j F_jp，故 ΔE_j = ΔB_p F_jp
    - 若能直接得到 F_jp，则 ΔB_j^ref = ρ_j ΔB_p F_jp（无需面积比）
  - 优点：每次迭代都能生成一张可预览的中间图像（逐步逼近）。

——

## 7. 形状因子计算：解析、半立方体、半球/蒙特卡洛

形状因子是计算瓶颈，关键在“遮挡 + 积分”。

1) 解析法（适用于简单几何或做基准）
- 微元到三角形的立体角（Van Oosterom & Strackee 公式）：
  - 设观察点为原点，三角形三个顶点的单位向量为 a,b,c（指向顶点方向）：
  - Ω_triangle = 2 arctan( ( a · (b × c) ) / (1 + a·b + b·c + c·a ) )
  - 则 F_{point→triangle} = Ω_triangle / π（仅当三角形在半球上方且可见）
- 多边形可三角化累加；面元到面元需要对发射面元再积分（常用数值积分或采样）。

2) 半立方体（Hemicube，经典实用）
- 在发射面元 i 的中心放置半个立方体（顶面 + 4 个侧面），对每个像素有预先计算好的 ΔF 像素权重。
- 通过光栅化 + 深度缓冲解决可见性，累加命中的像素权重即得 F_ij。
- 顶面像素的 ΔF（单位化半立方体，顶面 z=1，像素中心坐标 (x,y)）：
  - ΔF_top = ΔA / [π (x² + y² + 1)²]
- 侧面（以 x=1 面为例，像素中心 (1, y, z)，只计 z≥0）：
  - ΔF_side = z ΔA / [π (1 + y² + z²)²]
- 实现要点：
  - 每次“射”一个面元 i：渲染场景到 5 张视图（顶+4侧），用颜色编码/ID 区分接收面元；对每个像素命中 j 累加 ΔF 到 F_ij。
  - 注意近处小面元的走样 → 超采样/多重解析度/自适应细化。

3) 半球/蒙特卡洛采样（Nusselt 类比的直接应用）
- 令方向采样的概率密度 p(ω) = cosθ/π（与核相匹配），则：
  - F_ij = ∫_{Ω} I{射线命中 j} (cosθ/π) dω
  - 无偏估计：F_ij ≈ (1/N) ∑_{n=1}^N I{ray_n 命中 j}
- 优点：实现简单，天然处理复杂遮挡；缺点：方差 → 需大量样本或方差降低技术（重要性采样/分层采样/蓝噪声等）。

4) 其他
- 解析加速：边-边积分、线积分化、SVD 低秩近似
- 预计算可见性（可见性图/方向表征），层次链接（见第 11 节）

——

## 8. 性质：互易性、能量守恒、收敛性与误差

- 互易性 A_i F_ij = A_j F_ji：
  - 由 K(x,y)=K(y,x) 对称性，交换双重积分次序直接得到。
  - 实用价值：用 F_ij 可推 F_ji，进而避免面积比或减少计算量。

- 能量守恒：
  - 对任一 i：∑_j F_ij = 1（封闭场景），含“自视”与环境；平面面元通常 F_ii=0。
  - 证明：∫_H (cosθ/π) dω = 1（半球的余弦加权单位化），加上可见性覆盖整个半球的分割。

- 收敛性：
  - 迭代法充分条件：谱半径 ρ(RF) < 1，一般 ρ_i<1 且 F_ij 有界即可。
  - 实测：高反射率、强耦合（封闭小腔体）会减慢收敛。

- 误差来源：
  - 离散化误差（网格太粗，B 被过度平滑）
  - 形状因子近似（半立方体像素化、蒙特卡洛方差）
  - 可见性 aliasing（亚像素几何）
  - 近场奇异性（面元相邻或几何退化，1/r² 核发散风险）

——

## 9. 可见性与遮挡处理

- Z-buffer（半立方体常用）：在每个视图用深度缓冲确定首交面元 ID。
- 光线投射（蒙特卡洛）：每条方向样本做一次最近相交。
- 几何预处理：法线一致性、双面/背面剔除、自遮挡 F_ii 的特殊处理。
- 邻接/相切面：分裂面元或使用解析近场校正，避免奇异行为。

——

## 10. 实现步骤与伪代码

最小可用实现（常量基 + 半立方体 + 渐进细化）：

- 输入：三角网格，面元属性（ρ、B_e），相机参数（仅用于最终渲染）。
- 预处理：
  1) 对表面划分面元（可直接用三角面，或将大面片再分割）
  2) 计算每个面元面积 A_i、法向 n_i、反射率 ρ_i、自发射 B_{e,i}

- 渐进细化主循环（伪代码）：
```pseudo
# 初始化
for i in 1..N:
    B[i]    = B_emit[i]         # 初始出射度：来自自发射
    dB[i]   = B_emit[i]         # 未射出能量（出射度增量）

while not converged:
    p = argmax_i ( dB[i] * A[i] )     # 选取最大未射通量的面元

    # 用半立方体从 p 出发，构建 F_pj
    Frow = HemicubeShoot(p)           # 返回长度 N 的数组（可能稀疏）

    # 将 p 的未射能量分发给所有 j（常量基的面元平均）
    for each j with Frow[j] > 0:
        dE_j    = (dB[p] * A[p] * Frow[j]) / A[j]   # 接收的平均辐照度增量
        dB_ref  = rho[j] * dE_j                     # 反射成为出射度增量
        B[j]   += dB_ref
        dB[j]  += dB_ref

    dB[p] = 0                                       # 本次已射出

    # 终止条件： ∑_i dB[i] * A[i] < ε 或迭代次数达上限
```

- HemicubeShoot(p) 要点：
  - 在 p 的质心处放置半立方体，坐标系 z 轴朝向 n_p
  - 渲染 5 个面，像素写入“面元 ID”
  - 对每个像素累加 ΔF（按顶/侧面权重公式）
  - 得到 F_pj

- 收敛判据：
  - 全局未射能量 ∑ dB_i A_i / ∑ B_i A_i < τ（例如 1%）
  - 或固定迭代次数 K（实践中几十到几百次）

- 最终出图：
  - 每面元的亮度可用 B_i 或 L_i = B_i / π（Lambert）转换到像素着色
  - 做顶点插值或纹理烘焙提升视觉平滑度

——

## 11. 高阶与层次 Radiosity（有限元/分层链接）

- 顶点/边/双线性基函数：B(x) = ∑_k β_k N_k(x)，更平滑，减少“块状”伪影。
- 面元/可见性“分层”（Hierarchical Radiosity）：
  - 将发射者和接收者组织为层次树（四叉/八叉/面片层次）
  - 建立“链接”（link）表示能量交换；若耦合弱则在粗层处理，耦合强才细化
  - 自适应细化基于能量误差估计，复杂场景可从 O(N²) 降至近似 O(N log N)

——

## 12. 数值稳健性、网格细化与常见陷阱

- 网格：
  - 面元尺度应与光照变化尺度匹配（高梯度区域细分：角落、缝隙、近光源）
  - 分离“可见性面元”（大）与“解面元/元素”（小）的“双分辨率”策略

- 近场/相邻面：
  - 核 1/r² 近奇异，面元接触/共边时要细分或用解析近场修正
  - 平面面元通常 F_ii=0；曲面可能 F_ii>0，需谨慎

- 半立方体 aliasing：
  - 亚像素接收者抖动/超采样，多重分辨率 hemicube，或改用蒙特卡洛

- 物理参数：
  - 反射率 ρ ∈ [0,1]，自发射 B_e ≥ 0；多通道时 ρ_R, ρ_G, ρ_B 各自约束
  - 能量检查：Σ_i B_i A_i 应与 Σ_i B_{e,i} A_i 及吸收一致（见线性系统残差）

- 数值：
  - 使用双精度以减少近距离误差
  - 稠密矩阵内存大，尽量行-块稀疏化或分层

——

## 13. 色彩通道与纹理/贴图出图

- 对 RGB 三通道，F 相同，分别解 (I − R_c F) B_c = E_c（c ∈ {R,G,B}）
- 反射率与自发射可从 PBR 材质映射：ρ_c(x)、B_{e,c}(x)
- 结果转为纹理烘焙（Lightmap）：每 texel 作为一个“元素”解得 B，或事后插值
- 显示时可用 L = B/π 将出射度转为亮度（Lambert 模型）

——

## 14. 小结与实践建议

- 理解主方程：B = B_e + ρ K B（连续）→ B = E + R F B（离散）
- 把精力集中在：可见性与 F_ij 的稳健计算、网格自适应、迭代收敛与误差控制
- 初学实现：半立方体 + 渐进细化；高质量：层次 Radiosity 或蒙特卡洛 + 重要性采样
- 实践检查：互易性（A_i F_ij ≈ A_j F_ji）、能量守恒（∑ F_ij ≈ 1）、残差 ||(I−RF)B−E||

——

## 15. 参考文献（论文、教材与教程）

基础与经典：
- Kajiya, J. T. The Rendering Equation. SIGGRAPH 1986.
- Goral, C. M., Torrance, K. E., Greenberg, D. P., Battaile, B. Modeling the Interaction of Light Between Diffuse Surfaces. SIGGRAPH 1984.（Radiosity 开创）
- Cohen, M. F., Greenberg, D. P. The Hemi-cube: A Radiosity Solution for Complex Environments. SIGGRAPH 1985.（半立方体）
- Cohen, M. F., Chen, S. E., Wallace, J. R., Greenberg, D. P. A Progressive Refinement Approach to Fast Radiosity Image Generation. SIGGRAPH 1988.（渐进细化）
- Hanrahan, P., Salzman, D., Aupperle, L. A Rapid Hierarchical Radiosity Algorithm. SIGGRAPH 1991.（层次 Radiosity）
- Sillion, F. X., Puech, C. Radiosity and Global Illumination. Morgan Kaufmann, 1994.（教材）
- Cohen, M. F., Wallace, J. R. Radiosity and Realistic Image Synthesis. Academic Press, 1993.（教材）

形状因子与立体角：
- Van Oosterom, A., Strackee, J. The Solid Angle of a Plane Triangle. IEEE Trans. Biomed. Eng., 1983.（三角形立体角公式）
- Arvo, J. The Irradiance Jacobian for Partially Occluded Polyhedra. SIGGRAPH 1994.（几何与可见性微分，拓展理解）

采样与可见性：
- Ward, G., Heckbert, P. A New Object Sampling Method for Form Factor Computation. SIGGRAPH 1992.
- Baum, D. R., Rushmeier, H. E., Winget, J. M. Improving Radiosity Solutions Through the Use of Texture Maps. SIGGRAPH 1991.（纹理烘焙思想）

课程与教程（建议）：
- Physically Based Rendering（PBRT）对辐射度学与蒙特卡洛有系统讲解
- Cornell/RPI/UC Berkeley 等图形学课程讲义的 Radiosity 章节（含推导与作业）

——

# 附录 A：关键公式的逐步推导（便于快速查阅）

A.1 从渲染方程到 Radiosity
- 渲染方程（Lambert）：L_o = L_e + ∫ (ρ/π) L_i (n·ω_i) dω_i
- 两侧乘以 (n·ω_o) 并对 ω_o∈H 积分：
  - ∫ L_o (n·ω_o) dω_o = ∫ L_e (n·ω_o) dω_o + ∫∫ (ρ/π) L_i (n·ω_i) (n·ω_o) dω_i dω_o
  - 左：B；第一项：B_e；第二项：交换积分，内层 ∫ (ρ/π) dω_o = ρ
  - 得：B = B_e + ρ ∫ L_i (n·ω_i) dω_i = B_e + ρ E_in

A.2 入射辐照度的面面积分
- dE_in(x ← y) = L_o(y → x) (n_x·ω_{x}) dω_x
- dω_x = (n_y·ω_y) dA_y / r²
- L_o(y → x) = B(y)/π
- ⇒ dE_in = [B(y)/π] [cosθ_x cosθ_y / r²] V dA_y
- ⇒ E_in(x) = ∫_S [B(y)/π] G(x,y) V dA_y
- ⇒ B(x) = B_e(x) + ρ(x) ∫ [G V/π] B(y) dA_y

A.3 形状因子
- 定义：F_ij = (1/A_i) ∫_{A_i} ∫_{A_j} [cosθ_i cosθ_j / (π r²)] V dA_j dA_i
- 互易性：
  - A_i F_ij = ∬ K(x,y) dA_j dA_i = ∬ K(y,x) dA_i dA_j = A_j F_ji
- 能量守恒：
  - ∑_j F_ij = (1/A_i) ∫_{A_i} ∫_{Ω} (cosθ_i/π) dω dA_i = 1（封闭且全可见的半球）

A.4 半立方体像素权重
- 顶面（z=1）：点 (x,y,1)，r² = x²+y²+1
  - Δω = (cosθ_face dA) / r² = (1/√(r²)) dA / r² = dA / r³
  - cosθ_i = ω_z = 1/√(r²)
  - ΔF_top = (cosθ_i/π) Δω = (1/π) (1/√r²) (dA / r²) = dA / [π (x²+y²+1)²]
- 侧面（x=1）：点 (1,y,z)，r² = 1+y²+z²，cosθ_face=ω_x=1/√r²，cosθ_i=ω_z=z/√r²
  - ΔF_side = (ω_z/π) (ω_x dA / r²) = z dA / [π (1+y²+z²)²]（仅 z≥0 有效）

A.5 渐进细化的能量守恒推导
- 面元 p 未射出能量：ΔΦ_p = ΔB_p A_p
- 到达 j 的能量：ΔΦ_{p→j} = ΔΦ_p F_pj
- j 的平均辐照度增量：ΔE_j = ΔΦ_{p→j} / A_j = ΔB_p (A_p/A_j) F_pj
- 反射后的出射度增量：ΔB_j = ρ_j ΔE_j
- 用互易性 A_p F_pj = A_j F_jp，可得 ΔE_j = ΔB_p F_jp

——

如果你希望把本文导出为文档：直接复制为 Markdown 即可，无需改动。建议配合你已有的课程讲义/论文 PDF 对照阅读与实现。任何环节需要配图或交互演示（半立方体像素权重、层次链接等），告诉我，我可以为你生成自适应移动端的可视化 HTML 小工具来辅助理解与调试。




> 如果我想实现Radiosity算法，上面给出的公式细节，如果转变为c++代码，请给出思考和实现过程，写成markdown格式，方便我后续导出

下面给出将上一条答复中的公式与流程“落地到 C++”的一套可执行参考实现与思考路径。目标是最小可用、易懂、便于扩展：用常量基（每面元出射度常数）+ 渐进细化 Progressive Radiosity；形状因子行按需用蒙特卡洛方向采样（cosine-weighted hemisphere）+ 射线求交（BVH 加速）估计。这样无需依赖图形 API（OpenGL）或外部库，你可以单文件编译直接跑通，并据此替换为半立方体、层次 radiosity 等更高阶方案。

目录
- 1. 实现思路总览（公式到代码）
- 2. 数据结构与关键组件
- 3. 形状因子 F 的蒙特卡洛估计（从 Nusselt 类比到代码）
- 4. 渐进细化（shooting）更新公式到代码
- 5. 完整参考实现（单文件 C++17）
- 6. 构建与运行
- 7. 验证与调参
- 8. 可扩展方向与替换点

——

1) 实现思路总览（公式到代码）

- 连续到离散：
  - B_i = B_{e,i} + ρ_i ∑_j F_ij B_j
  - Progressive Radiosity：每次选择未射能量最大的面元 p（ΔB_p），“从 p 向外射能量”，把能量分给命中的面元 j：
    - ΔE_j = ΔB_p A_p F_pj / A_j
    - ΔB_j = ρ_j ∘ ΔE_j    （向量逐分量乘，RGB 情况）
    - B_j += ΔB_j；ΔB_j（未射）也累加，然后将 ΔB_p 清零
- 形状因子 F_pj 的估计（Nusselt 类比 + 可见性）：
  - F_pj = (1/A_p) ∬_{x∈A_p, ω∈H} (cosθ_x/π) I{从 x 沿 ω 出射的首交面元为 j} dω dA_x
  - 蒙特卡洛无偏估计：从面元 p 上均匀采样点，再在其法线半球按 cosθ/π 采样方向，射线求交。命中 j 的次数 / 总样本数 ≈ F_pj。
- 可见性与遮挡：用 BVH 加速的三角形最近交（Möller–Trumbore）。只计“正面命中”：dot(n_j, -ray.dir) > 0。
- 多通道：B、ΔB、ρ、B_e 全部用 Vec3（RGB）表示，公式逐分量应用。

——

2) 数据结构与关键组件

- 几何
  - Patch（三角形面元）= 3 顶点 + 法线 + 面积 + 材质（ρ、B_e，RGB）
  - Scene = patches + BVH（AABB 树）
- 数学
  - Vec3、Ray、AABB、正交基（由法线 n 构建切线/副法线）
  - 采样：均匀三角形采样、余弦半球采样（同心圆映射）
- BVH
  - 中值划分（最大范围轴），叶子包含若干三角索引
  - AABB slab intersection，遍历求最近交

——

3) 形状因子 F 的蒙特卡洛估计（从 Nusselt 类比到代码）

- 公式回顾：F_pj = E[I{射线命中 j}]（当点按面元均匀、方向按 cosθ/π）
- 代码对应：
  - 对 p：
    - 重复 N 次：
      - 采样点 x ∈ A_p（均匀三角形）
      - 采样方向 ω ~ cosθ/π（局部半球），变换到世界坐标
      - Ray(x + ε n_p, ω)，射线求最近交，得到 patch id = j
      - 若 j != p 且 dot(n_j, -ω) > 0：hits[j]++
    - F_pj = hits[j] / N
  - 逃逸到外部（未命中任意面元）的样本自然体现开放环境（能量泄露）。

——

4) 渐进细化（shooting）更新公式到代码

- 选择射能量最大者 p：
  - 未射通量 Φ_p = A_p * luminance(ΔB_p)
- MC 得到 F_p* 后，对每个 j：
  - ΔE_j = ΔB_p ∘ (A_p F_pj / A_j)  注意：ΔB_p 为 RGB，A_p/A_j 为标量，F_pj 标量
  - ΔB_ref_j = ρ_j ∘ ΔE_j
  - B_j += ΔB_ref_j；ΔB_j += ΔB_ref_j
- 将 ΔB_p 置 0
- 终止：全局未射通量 / 总出射通量 < ε 或迭代步数上限

——

5) 完整参考实现（单文件 C++17）

说明：
- 教学参考为主，尽量清晰，便于你改造成自己的工程。
- 包含：Vec3、采样、三角求交、AABB/BVH、形状因子 MC、渐进细化。
- 场景示例：简化版 Cornell-ish 盒子（地面、左右墙、背墙、顶面+小灯），面元=三角形常量基。
- 可直接 g++ -O2 -std=c++17 radiosity.cpp -o radiosity 编译。

```cpp
// radiosity.cpp
// Minimal progressive radiosity (constant basis) with Monte Carlo form factors + BVH ray casting.
// C++17 single-file reference implementation for learning and extension.
// Author: GPT-5 Pro (educational reference)

#include <bits/stdc++.h>
using namespace std;

using Real = double;

struct Vec3 {
    Real x{}, y{}, z{};
    Vec3() = default;
    Vec3(Real x_, Real y_, Real z_) : x(x_), y(y_), z(z_) {}
    Vec3 operator+(const Vec3& b) const { return {x+b.x, y+b.y, z+b.z}; }
    Vec3 operator-(const Vec3& b) const { return {x-b.x, y-b.y, z-b.z}; }
    Vec3 operator*(Real s) const { return {x*s, y*s, z*s}; }
    Vec3 operator/(Real s) const { return {x/s, y/s, z/s}; }
    Vec3& operator+=(const Vec3& b) { x+=b.x; y+=b.y; z+=b.z; return *this; }
    Vec3& operator-=(const Vec3& b) { x-=b.x; y-=b.y; z-=b.z; return *this; }
    Vec3& operator*=(Real s) { x*=s; y*=s; z*=s; return *this; }
    Vec3& operator/=(Real s) { x/=s; y/=s; z/=s; return *this; }
};
static inline Vec3 operator*(Real s, const Vec3& v){ return v*s; }
static inline Vec3 operator*(const Vec3& a, const Vec3& b){ return {a.x*b.x, a.y*b.y, a.z*b.z}; } // Hadamard
static inline Real dot(const Vec3& a, const Vec3& b){ return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 cross(const Vec3& a, const Vec3& b){
    return { a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x };
}
static inline Real length(const Vec3& v){ return std::sqrt(dot(v,v)); }
static inline Vec3 normalize(const Vec3& v){
    Real L = length(v); if(L==0) return v; return v / L;
}
static inline Real luminance(const Vec3& c){ // Rec.709
    return 0.2126*c.x + 0.7152*c.y + 0.0722*c.z;
}
static inline Vec3 clamp01(const Vec3& c){
    auto clamp1 = [](Real v){ return std::max((Real)0, std::min((Real)1, v)); };
    return {clamp1(c.x), clamp1(c.y), clamp1(c.z)};
}

struct Ray {
    Vec3 o, d;
    Real tmin{1e-6}, tmax{1e30};
};

struct AABB {
    Vec3 mn{+1e30, +1e30, +1e30};
    Vec3 mx{-1e30, -1e30, -1e30};
    void expand(const Vec3& p){
        mn.x = std::min(mn.x, p.x); mn.y = std::min(mn.y, p.y); mn.z = std::min(mn.z, p.z);
        mx.x = std::max(mx.x, p.x); mx.y = std::max(mx.y, p.y); mx.z = std::max(mx.z, p.z);
    }
    void expand(const AABB& b){ expand(b.mn); expand(b.mx); }
    bool intersect(const Ray& r, Real& t0, Real& t1) const {
        Real tmin = r.tmin, tmax = r.tmax;
        for(int a=0;a<3;++a){
            Real invD = 1.0 / (a==0? r.d.x : (a==1? r.d.y : r.d.z));
            Real tNear = ((a==0? mn.x : (a==1? mn.y : mn.z)) - (a==0? r.o.x : (a==1? r.o.y : r.o.z))) * invD;
            Real tFar  = ((a==0? mx.x : (a==1? mx.y : mx.z)) - (a==0? r.o.x : (a==1? r.o.y : r.o.z))) * invD;
            if(invD < 0) std::swap(tNear, tFar);
            tmin = std::max(tmin, tNear);
            tmax = std::min(tmax, tFar);
            if(tmax < tmin) return false;
        }
        t0 = tmin; t1 = tmax; return true;
    }
};

// RNG
struct RNG {
    std::mt19937_64 gen;
    std::uniform_real_distribution<Real> dist;
    RNG(uint64_t seed = 42) : gen(seed), dist(0.0, 1.0) {}
    Real next(){ return dist(gen); }
};

// Concentric disk sampling (Shirley)
static inline pair<Real,Real> concentricSampleDisk(Real u1, Real u2){
    Real sx = 2*u1 - 1;
    Real sy = 2*u2 - 1;
    if(sx==0 && sy==0) return {0,0};
    Real r, theta;
    if(std::abs(sx) > std::abs(sy)){
        r = sx;
        theta = (M_PI/4.0) * (sy/sx);
    }else{
        r = sy;
        theta = (M_PI/2.0) - (M_PI/4.0) * (sx/sy);
    }
    return { r*std::cos(theta), r*std::sin(theta) };
}

// Cosine-weighted hemisphere sampling; local frame z为法线方向
static inline Vec3 sampleCosineHemisphere(RNG& rng){
    auto uv = concentricSampleDisk(rng.next(), rng.next());
    Real x = uv.first, y = uv.second;
    Real z = std::sqrt(std::max((Real)0, 1 - x*x - y*y));
    return {x, y, z};
}

// Build an ONB from normal
struct ONB {
    Vec3 t, b, n;
};
static inline ONB make_onb(const Vec3& n){
    Vec3 N = normalize(n);
    Vec3 h = (std::abs(N.z) < 0.999) ? Vec3{0,0,1} : Vec3{1,0,0};
    Vec3 t = normalize(cross(h, N));
    Vec3 b = cross(N, t);
    return {t,b,N};
}
static inline Vec3 localToWorld(const ONB& onb, const Vec3& vLocal){
    return onb.t * vLocal.x + onb.b * vLocal.y + onb.n * vLocal.z;
}

struct Triangle {
    Vec3 v0, v1, v2;
    int   matId{-1}; // optional
};

struct Material {
    Vec3 rho{0.8,0.8,0.8};   // diffuse reflectance (RGB)
    Vec3 emit{0,0,0};        // emitted radiosity B_e (RGB)
};

struct Patch { // constant basis on a triangle
    Triangle tri;
    Vec3 n;     // unit normal (geometric)
    Real area;  // triangle area
    int matId{0};
    // radiosity state:
    Vec3 rho;   // reflectance
    Vec3 Be;    // emission (radiosity) RGB
};

struct Hit {
    Real t{1e30};
    int patchId{-1};
    Real u{}, v{}; // barycentric
};

// Möller–Trumbore ray-triangle intersection
static inline bool rayTriangleIntersect(const Ray& ray, const Triangle& tri, Real& t, Real& u, Real& v){
    const Real EPS = 1e-9;
    Vec3 v0v1 = tri.v1 - tri.v0;
    Vec3 v0v2 = tri.v2 - tri.v0;
    Vec3 pvec = cross(ray.d, v0v2);
    Real det = dot(v0v1, pvec);
    if(std::abs(det) < EPS) return false;
    Real invDet = 1.0 / det;
    Vec3 tvec = ray.o - tri.v0;
    u = dot(tvec, pvec) * invDet;
    if(u < 0 || u > 1) return false;
    Vec3 qvec = cross(tvec, v0v1);
    v = dot(ray.d, qvec) * invDet;
    if(v < 0 || u + v > 1) return false;
    t = dot(v0v2, qvec) * invDet;
    return t > ray.tmin && t < ray.tmax;
}

// BVH
struct BVHNode {
    AABB box;
    int left{-1}, right{-1};
    int start{0}, count{0}; // leaf range in indices
    bool isLeaf() const { return left < 0; }
};
struct BVH {
    vector<BVHNode> nodes;
    vector<int> indices; // triangle indices into patches
    const vector<Patch>* patches{nullptr};

    AABB triBounds(int idx) const {
        const Triangle& t = (*patches)[idx].tri;
        AABB b; b.expand(t.v0); b.expand(t.v1); b.expand(t.v2);
        return b;
    }
    Vec3 triCentroid(int idx) const {
        const Triangle& t = (*patches)[idx].tri;
        return (t.v0 + t.v1 + t.v2) / 3.0;
    }

    int buildNode(int start, int end){
        BVHNode node;
        AABB box;
        for(int i=start;i<end;++i){
            box.expand(triBounds(indices[i]));
        }
        node.box = box;
        int n = end - start;
        if(n <= 4){
            node.start = start; node.count = n;
            int idx = (int)nodes.size();
            nodes.push_back(node);
            return idx;
        }
        // choose split axis by largest extent
        Vec3 ext = box.mx - box.mn;
        int axis = 0;
        if(ext.y > ext.x) axis = 1;
        if(ext.z > (axis==0?ext.x:ext.y)) axis = 2;
        int mid = (start + end)/2;
        std::nth_element(indices.begin()+start, indices.begin()+mid, indices.begin()+end,
            [&](int a, int b){
                Vec3 ca = triCentroid(a), cb = triCentroid(b);
                Real va = (axis==0? ca.x : (axis==1? ca.y : ca.z));
                Real vb = (axis==0? cb.x : (axis==1? cb.y : cb.z));
                return va < vb;
            });
        int idx = (int)nodes.size();
        nodes.push_back(BVHNode{});
        int L = buildNode(start, mid);
        int R = buildNode(mid, end);
        nodes[idx].left = L; nodes[idx].right = R;
        nodes[idx].box = box;
        return idx;
    }

    void build(const vector<Patch>& p){
        patches = &p;
        indices.resize(p.size());
        std::iota(indices.begin(), indices.end(), 0);
        nodes.clear(); nodes.reserve(p.size()*2);
        buildNode(0, (int)indices.size());
    }

    bool intersect(const Ray& r, Hit& hit) const {
        bool any = false;
        array<int, 64> stack; int sp=0;
        stack[sp++] = 0; // root
        Real closest = hit.t;
        while(sp){
            int ni = stack[--sp];
            const BVHNode& nd = nodes[ni];
            Real t0, t1;
            if(!nd.box.intersect(r, t0, t1) || t0 > closest) continue;
            if(nd.isLeaf()){
                for(int i=0;i<nd.count;++i){
                    int triIdx = indices[nd.start + i];
                    Real t,u,v;
                    if(rayTriangleIntersect(r, (*patches)[triIdx].tri, t, u, v)){
                        if(t < closest){
                            closest = t; hit.t = t; hit.patchId = triIdx; hit.u = u; hit.v = v;
                            any = true;
                        }
                    }
                }
            }else{
                stack[sp++] = nd.left;
                stack[sp++] = nd.right;
            }
        }
        return any;
    }
};

struct Scene {
    vector<Patch> patches;
    vector<Material> materials;
    BVH bvh;
    AABB sceneBounds;
    Real sceneScale{1.0};

    void finalize(){
        // compute patch normals, areas, material assignment
        sceneBounds = AABB{};
        for(size_t i=0;i<patches.size();++i){
            Triangle& t = patches[i].tri;
            Vec3 n = cross(t.v1 - t.v0, t.v2 - t.v0);
            Real a = 0.5 * length(n);
            if(a < 1e-16){
                // degenerate, fix a bit
                n = {0,0,1}; a = 1e-12;
            }
            patches[i].n = normalize(n);
            patches[i].area = a;
            sceneBounds.expand(t.v0); sceneBounds.expand(t.v1); sceneBounds.expand(t.v2);
            // attach material
            int mid = patches[i].matId;
            patches[i].rho = materials[mid].rho;
            patches[i].Be  = materials[mid].emit;
        }
        Vec3 diag = sceneBounds.mx - sceneBounds.mn;
        sceneScale = std::max({diag.x, diag.y, diag.z});
        bvh.build(patches);
    }
};

// Uniform sample on triangle
static inline Vec3 sampleTriangle(const Triangle& t, RNG& rng){
    Real u = rng.next();
    Real v = rng.next();
    Real su = std::sqrt(u);
    Real b0 = 1 - su;
    Real b1 = v * su;
    Real b2 = 1 - b0 - b1;
    return t.v0 * b0 + t.v1 * b1 + t.v2 * b2;
}

// Compute one row F_p* by MC sampling
static inline void estimateFormFactorRow_MC(
    const Scene& scene, int p, int samplesPerPatchPoint, int patchPointCount,
    vector<Real>& Frow, RNG& rng)
{
    const Patch& P = scene.patches[p];
    ONB onb = make_onb(P.n);
    int N = samplesPerPatchPoint * patchPointCount;
    if(N<=0) return;
    // To reduce variance, we stratify both point and direction loops simply by nested loops
    vector<int> hits(scene.patches.size(), 0);
    Real eps = 1e-5 * scene.sceneScale;

    for(int s=0; s<patchPointCount; ++s){
        Vec3 x = sampleTriangle(P.tri, rng);
        for(int k=0; k<samplesPerPatchPoint; ++k){
            Vec3 dirLocal = sampleCosineHemisphere(rng);
            Vec3 dir = localToWorld(onb, dirLocal);
            Ray ray{ x + P.n * eps, dir, 0.0, 1e30 };
            Hit h;
            if(scene.bvh.intersect(ray, h)){
                if(h.patchId != p){
                    const Patch& J = scene.patches[h.patchId];
                    // count only if front-facing (cosθ_j > 0)
                    if(dot(J.n, (Vec3{-ray.d.x, -ray.d.y, -ray.d.z})) > 0){
                        hits[h.patchId] ++;
                    }
                }
            }
        }
    }
    // Normalize to F_pj
    for(size_t j=0;j<scene.patches.size();++j){
        Frow[j] = (Real)hits[j] / (Real)N;
    }
}

// Build a small Cornell-like box scene (triangles), with an area light on the ceiling
static Scene buildCornellLike(){
    Scene scene;
    // Materials
    int MAT_WHITE = 0, MAT_RED = 1, MAT_GREEN = 2, MAT_LIGHT = 3;
    scene.materials.resize(4);
    scene.materials[MAT_WHITE] = Material{ {0.8,0.8,0.8}, {0,0,0} };
    scene.materials[MAT_RED]   = Material{ {0.75,0.15,0.15}, {0,0,0} };
    scene.materials[MAT_GREEN] = Material{ {0.15,0.75,0.15}, {0,0,0} };
    scene.materials[MAT_LIGHT] = Material{ {0.0,0.0,0.0},   {20,20,20} }; // strong emitter (radiosity)

    auto addQuad = [&](Vec3 a, Vec3 b, Vec3 c, Vec3 d, int mat){
        Patch p1, p2;
        p1.tri = Triangle{a,b,c}; p1.matId = mat;
        p2.tri = Triangle{a,c,d}; p2.matId = mat;
        scene.patches.push_back(p1);
        scene.patches.push_back(p2);
    };

    // Box size
    Real L = 1.0;
    // Floor (y=0)
    addQuad({0,0,0},{L,0,0},{L,0,L},{0,0,L}, MAT_WHITE);
    // Ceiling (y=L)
    addQuad({0,L,0},{0,L,L},{L,L,L},{L,L,0}, MAT_WHITE);
    // Back wall (z=L)
    addQuad({0,0,L},{L,0,L},{L,L,L},{0,L,L}, MAT_WHITE);
    // Left wall (x=0)
    addQuad({0,0,0},{0,0,L},{0,L,L},{0,L,0}, MAT_RED);
    // Right wall (x=L)
    addQuad({L,0,0},{L,L,0},{L,L,L},{L,0,L}, MAT_GREEN);
    // Small light on ceiling center
    Real s = 0.2;
    Real c0 = 0.5*(1.0 - s), c1 = 0.5*(1.0 + s);
    addQuad({c0,L-1e-4,c0},{c1,L-1e-4,c0},{c1,L-1e-4,c1},{c0,L-1e-4,c1}, MAT_LIGHT);

    scene.finalize();
    // Flip normals to face inward for box patches if needed (ensure normals roughly point inward)
    // We can orient them by checking which side faces the box center.
    Vec3 center = (scene.sceneBounds.mn + scene.sceneBounds.mx) / 2.0;
    for(auto& p : scene.patches){
        Vec3 triC = (p.tri.v0 + p.tri.v1 + p.tri.v2) / 3.0;
        Vec3 toCenter = normalize(center - triC);
        if(dot(p.n, toCenter) < 0) {
            // flip triangle winding and normal
            std::swap(p.tri.v1, p.tri.v2);
            p.n = p.n * -1.0;
        }
    }
    scene.bvh.build(scene.patches);
    return scene;
}

struct RadiosityState {
    vector<Vec3> B;   // current radiosity per patch (RGB)
    vector<Vec3> dB;  // unshot radiosity per patch (RGB)
    vector<Real> A;   // area per patch
    vector<Vec3> rho; // reflectance
    vector<Vec3> Be;  // emission
};

static RadiosityState initRadiosity(const Scene& scene){
    RadiosityState st;
    int N = (int)scene.patches.size();
    st.B.resize(N);
    st.dB.resize(N);
    st.A.resize(N);
    st.rho.resize(N);
    st.Be.resize(N);
    for(int i=0;i<N;++i){
        st.A[i] = scene.patches[i].area;
        st.rho[i] = clamp01(scene.patches[i].rho);
        st.Be[i]  = scene.patches[i].Be;
        st.B[i]   = st.Be[i];
        st.dB[i]  = st.Be[i];
    }
    return st;
}

// Choose shooter p with maximum unshot flux A[p] * luminance(dB[p])
static int pickShooter(const RadiosityState& st){
    Real best = -1; int idx = -1;
    int N = (int)st.B.size();
    for(int i=0;i<N;++i){
        Real flux = st.A[i] * luminance(st.dB[i]);
        if(flux > best){ best = flux; idx = i; }
    }
    return idx;
}

static void progressiveRadiosity(Scene& scene,
                                 int samplesPerPatchPoint,
                                 int patchPointCount,
                                 int maxIters,
                                 Real stopRelUnshot,
                                 bool verbose = true)
{
    RadiosityState st = initRadiosity(scene);
    int N = (int)scene.patches.size();
    RNG rng(1234567);

    auto totalFlux = [&](const vector<Vec3>& B){
        Real s = 0;
        for(int i=0;i<N;++i) s += st.A[i] * luminance(B[i]);
        return s;
    };

    vector<Real> Frow(N, 0.0);

    Real initialUnshot = totalFlux(st.dB);
    if(verbose) {
        cout << "Initial unshot flux: " << initialUnshot << "\n";
        cout << "Patches: " << N << "\n";
    }

    for(int it=0; it<maxIters; ++it){
        int p = pickShooter(st);
        if(p < 0) break;
        Real remaining = totalFlux(st.dB);
        Real rel = (initialUnshot>0)? (remaining / initialUnshot) : 0.0;
        if(verbose && it%10==0){
            cout << "Iter " << it << " remaining rel unshot = " << rel << "\n";
        }
        if(remaining <= stopRelUnshot * initialUnshot) {
            if(verbose) cout << "Converged by unshot threshold.\n";
            break;
        }
        if(luminance(st.dB[p]) <= 0) {
            if(verbose) cout << "No more unshot energy, stopping.\n";
            break;
        }

        // Estimate F_p*
        std::fill(Frow.begin(), Frow.end(), 0.0);
        estimateFormFactorRow_MC(scene, p, samplesPerPatchPoint, patchPointCount, Frow, rng);

        // Shoot energy from p
        Vec3 dBp = st.dB[p]; // unshot radiosity (RGB)
        Real Ap = st.A[p];

        // distribute
        for(int j=0;j<N;++j){
            Real Fpj = Frow[j];
            if(Fpj <= 0) continue;
            Real Aj = st.A[j];
            // ΔE_j (RGB) = ΔB_p * (Ap * F_pj / Aj)
            Vec3 dEj = dBp * (Ap * Fpj / Aj);
            // ΔB_ref_j = ρ_j ∘ dEj
            Vec3 dBref = st.rho[j] * dEj;
            st.B[j]  += dBref;
            st.dB[j] += dBref;
        }

        // Mark shooter p as shot
        st.dB[p] = {0,0,0};
    }

    // Output final per-patch radiosity (B) and exitance luminance
    cout << "\nFinal per-patch radiosity (B, RGB) and luminance:\n";
    for(int i=0;i<N;++i){
        Vec3 Bi = st.B[i];
        Real lum = luminance(Bi);
        cout << "Patch " << i << "  B=(" << Bi.x << "," << Bi.y << "," << Bi.z << ")  L=" << lum << "\n";
    }

    // Optionally, you can write a simple OBJ/PLY with vertex colors from patch B/π
    // or bake to a lightmap. For brevity we just print values here.
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    Scene scene = buildCornellLike();

    // Parameters
    int samplesPerPatchPoint = 64; // K
    int patchPointCount      = 8;  // M => total N = M*K per shooter
    int maxIters             = 200;
    Real stopRelUnshot       = 0.01; // stop when remaining unshot < 1% initial

    progressiveRadiosity(scene, samplesPerPatchPoint, patchPointCount, maxIters, stopRelUnshot, true);
    return 0;
}
```

要点说明：
- 面元=三角形，常量基：每个三角形上的 B 近似常数。
- 形状因子行 F_p* 按需估计，避免 O(N²) 全矩阵存储。
- 方向采样使用余弦权重，配合 Nusselt 类比保证 F 的无偏估计。
- 射线求交用 BVH 加速，保证复杂场景也能跑起来（当然仍非工业性能）。

——

6) 构建与运行

- 编译：
  - Linux/macOS: g++ -O2 -std=c++17 radiosity.cpp -o radiosity
  - Windows (MSYS2/MinGW): g++ -O2 -std=gnu++17 radiosity.cpp -o radiosity.exe
- 运行：
  - ./radiosity
- 输出：
  - 每个面元最终 radiosity B（RGB）与其亮度值。你可进一步把 B/π 转为亮度 L 并烘焙为顶点色或纹理。

——

7) 验证与调参

- 验证性质
  - 互易性（统计意义）：随机抽几个 i,j，检查 A_i F_ij ≈ A_j F_ji（需足够样本）。
  - 能量守恒（封闭场景）：对封闭盒子且无外泄，检查 ∑_j F_ij ≈ 1；本实现若有缝隙/数值误差，会有轻微偏差。
- 收敛
  - 提高 samplesPerPatchPoint 和 patchPointCount 可降低噪声，加快收敛稳定性（但增时）。
  - stopRelUnshot 设为 1%~0.5% 常见。
- 质量
  - MC 噪声：可做分层采样（stratified）、蓝噪点序列、Sobol 序列替代 RNG。
  - 相邻面/近场：加大样本数；或进行自适应网格细化（见下）。

——

8) 可扩展方向与替换点

- 半立方体（Hemicube）替换 MC：
  - 用图形 API 渲染 5 张视图，按像素权重累加 ΔF，构建 F_p*。代码结构只需替换 estimateFormFactorRow_MC。
- 层次 Radiosity：
  - 用面片层次树和链接（links），用能量误差驱动自适应细化，近似 O(N log N)。
- 网格细化与双分辨率：
  - 细化高梯度区域（角隅、近光），减小常量基块状感；用大 patch 处理可见性、小元素解 B。
- 直接解线性系统：
  - 预估计 F（例如采样多次累计），装配 A = I − R F，选用 BiCGSTAB/GMRES 求解（A 非对称）。适用于较小场景或离线高精度。
- 多反射率/材质：
  - ρ(x) 可贴图采样，Be 也可按纹理设定；结果烘焙到 lightmap。

——

附：公式到代码的关键对应清单

- B = B_e + ρ K B（连续）→ Progressive：迭代传播 ΔB
- F_ij = (1/A_i) ∬ (cosθ_i cosθ_j / π r²) V dA_j dA_i
  - 代码中用 F_ij = E[I(hit j)]（在 i 上均匀+半球 cos 采样）无偏估计
- ΔE_j = ΔB_p A_p F_pj / A_j；ΔB_j = ρ_j ∘ ΔE_j
  - 代码中 dEj = dBp * (Ap * Fpj / Aj)；dBref = rho_j * dEj
- 终止：∑ dB_i A_i / ∑ 初始dB_i A_i < ε
  - 代码中 totalFlux(dB)/initialUnshot < stopRelUnshot

如果你需要将上述 MC 形状因子替换为半立方体版本、或者添加 OBJ/GLTF 网格加载、输出 PPM/EXR 烘焙图，我可以继续给出对应的完整 C++ 代码模块。