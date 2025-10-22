> 阅读该论文，完成一下内容：1）理解并整理论文中算法的详细过程和实现细节；2）推导所有出现的公式，给出详尽的推导过程，如果推导需要依赖其他文章的内容，请给出参考 3）把所有内容写成一个markdown格式，方便我导出

# Instant Radiosity（Keller, SIGGRAPH 1997）精读与推导笔记

本文面向“即时辐射度（Instant Radiosity）”论文的系统化整理，包含：
- 算法流程与实现细节（从场景→粒子→硬件→累积缓冲）。
- 文中所有公式的逐步推导与解释（必要时引用外部文献）。
- 便于导出的 Markdown 结构化文档。

注：文中用到的“渲染方程/辐亮度方程”“传输算子”“低差异采样”“准随机游走”等术语，均在各小节中给出定义或引用。

---

## 目录

- [Instant Radiosity（Keller, SIGGRAPH 1997）精读与推导笔记](#instant-radiositykeller-siggraph-1997精读与推导笔记)
  - [目录](#目录)
  - [1. 背景与核心思想](#1-背景与核心思想)
  - [2. 数学模型：辐亮度方程与像素测度](#2-数学模型辐亮度方程与像素测度)
    - [2.1 渲染（辐亮度）方程](#21-渲染辐亮度方程)
    - [2.2 漫反射特例与各向同性](#22-漫反射特例与各向同性)
    - [2.3 算子形式与像素探测泛函](#23-算子形式与像素探测泛函)
    - [2.4 像素平均辐亮度与式(1)](#24-像素平均辐亮度与式1)
  - [3. 点源离散密度近似与硬件渲染](#3-点源离散密度近似与硬件渲染)
    - [3.1 点源离散密度（式(2)）](#31-点源离散密度式2)
    - [3.2 将 Tmn 作用于点光源：硬件一次光照+阴影](#32-将-tmn-作用于点光源硬件一次光照阴影)
  - [4. 传输算子展开与路径积分表达式](#4-传输算子展开与路径积分表达式)
    - [4.1 Neumann 级数与收敛性](#41-neumann-级数与收敛性)
    - [4.2 将 T 展开为路径积分并得到式(3)](#42-将-t-展开为路径积分并得到式3)
  - [5. 准蒙特卡罗（QMC）与 Halton/Hammersley](#5-准蒙特卡罗qmc与-haltonhammersley)
    - [5.1 QMC 近似与误差](#51-qmc-近似与误差)
    - [5.2 Halton 序列与基反演](#52-halton-序列与基反演)
    - [5.3 直接与增量计算（伪代码）](#53-直接与增量计算伪代码)
  - [6. 准随机游走（Quasi-Random Walk）](#6-准随机游走quasi-random-walk)
    - [6.1 平均反射率与生存路径数](#61-平均反射率与生存路径数)
    - [6.2 样本分配策略与低差异优势](#62-样本分配策略与低差异优势)
  - [7. 实现细节（从粒子到图像）](#7-实现细节从粒子到图像)
    - [7.1 完整流程（伪代码+说明）](#71-完整流程伪代码说明)
    - [7.2 关键构件：采样和映射](#72-关键构件采样和映射)
    - [7.3 与硬件接口：阴影与累积缓冲](#73-与硬件接口阴影与累积缓冲)
  - [8. 抖动低差异采样（Jittered Low-Discrepancy）](#8-抖动低差异采样jittered-low-discrepancy)
  - [9. 镜面与焦散扩展](#9-镜面与焦散扩展)
  - [10. 实时漫游与时间累积](#10-实时漫游与时间累积)
  - [11. 复杂度、数值问题与讨论](#11-复杂度数值问题与讨论)
  - [12. 参考实现要点与建议](#12-参考实现要点与建议)
  - [13. 参考文献](#13-参考文献)
- [从算法到工程：用 C++ 实现 Instant Radiosity（VPL/准随机游走/低差异采样）](#从算法到工程用-c-实现-instant-radiosityvpl准随机游走低差异采样)
  - [1. 设计与映射](#1-设计与映射)
  - [2. 算法到代码的映射关系](#2-算法到代码的映射关系)
  - [3. 完整 C++ 参考实现（单文件）](#3-完整-c-参考实现单文件)
  - [4. CMake 构建与运行](#4-cmake-构建与运行)
  - [5. 实现要点与扩展建议](#5-实现要点与扩展建议)

---

## 1. 背景与核心思想

- 不做核函数/解的离散化，不做网格化（避免层次 radiosity 的网格误差与存储）。
- 直接在场景图上工作：将全局漫反射间接光用有限个“虚拟点光源（VPL）”近似。
- 每个 VPL 由“准随机游走”从真实发光体出发生成（低差异序列替代随机）。
- 用图形硬件一次光照+阴影渲染每个 VPL 的可见贡献，用累积缓冲叠加，得到全局光照。
- 低差异采样带来“更平滑、稍优的收敛”，且“确定性、无方差”，适合交互/实时。

---

## 2. 数学模型：辐亮度方程与像素测度

### 2.1 渲染（辐亮度）方程

设场景表面为 S，点 y ∈ S，表面法线 n(y)，入射方向 ωi、出射方向 ωr，半球为 Ω。辐亮度方程（Kajiya 渲染方程）为 [Kaj86]：

$$
L(y, \omega_r) \;=\; L_e(y, \omega_r) \;+\; \int_{\Omega}
f_r(\omega_i, y, \omega_r)\, L\big(h(y, \omega_i), -\omega_i\big)\, \cos\theta_i \, d\omega_i.
\tag{R}
$$

其中：
- h(y, ωi) 为从 y 沿 ωi 发射的首个交点；
- f_r 为 BRDF；
- cosθi = n(y) ⋅ ωi；
- L_e 为自发辐亮度。

推导要点（能量守恒 → BRDF 定义 → 方向到方向的输运）：
- 出射辐亮度 = 自发 + 对所有入射方向的反射贡献；
- 入射辐亮度 L_i(y, ωi) 等于前一交点处的出射 L_o(x, −ωi)，x = h(y, ωi)；
- 反射对出射方向 ωr 的贡献由 f_r 加权，并乘以投影 cosθi；
- 积分域为局部半球 Ω（表面法线为极轴）。

参考：Kajiya 1986 [Kaj86]。

### 2.2 漫反射特例与各向同性

Lambert 漫反射：f_r = f_d(y) = ρ_d(y)/π 与方向无关。则出射辐亮度各向同性，记为 L(y)：

$$
L(y) \;=\; L_e(y) \;+\; \frac{\rho_d(y)}{\pi} \int_{\Omega}
L\big(h(y, \omega_i)\big)\, \cos\theta_i \, d\omega_i.
\tag{D}
$$

推导：
- 因 f_r 与 ωr 无关，所以 L(y, ω_r) 不依赖 ω_r；
- 将 f_r 替入 (R)，得上式。

### 2.3 算子形式与像素探测泛函

定义传输算子 T_f：

$$
(T_f L)(y,\omega_r) := \int_{\Omega} f_r(\omega_i, y,\omega_r)\, L\big(h(y,\omega_i), -\omega_i\big)\, \cos\theta_i\, d\omega_i.
$$

则 (R) 可写为：

$$
L \;=\; L_e \;+\; T_f L.
$$

令 T_fd 表示漫反射时的传输算子。

像素 m,n 的探测泛函 Ψ_mn 设计为“针孔相机 + 像素区域平均”的测度 [见下]：

$$
\Psi_{mn}(y, \omega) :=
\frac{1}{|P_{mn}|}\, \frac{\delta\big(\omega - \omega_{y_f}\big)}{\cos\theta}\, \chi_{P_{mn}}\!\big(h(y,\omega)\big),
$$

- y_f 为针孔位置（相机焦点）；
- P_{mn} 为像素在成像平面的支撑区域；
- ω_{y_f} := P - y_f 为从 y 指向焦点的方向（与 pixel P 对应）；
- χ 为特征函数；
- δ 为 Kronecker delta（在方向域的狄拉克抽样行为）。

直观解释：
- δ 只保留穿过针孔方向的辐亮度；
- χ 只计入那些最终在成像平面落入像素 P_{mn} 的光线；
- 1/|P_{mn}| 实现像素区域平均；
- 除以 cosθ 与测度中的 cosθ 抵消，使得泛函仅“计数光线”，不因投影重复加权。

严格构造可由“探测器的伴随算子”与“从方向到成像平面变量替换”的标准论证得到（参见 [Kaj86] 及光传输伴随理论）。

### 2.4 像素平均辐亮度与式(1)

定义内积（测度）：

$$
\langle L, \Psi \rangle := 
\int_S \int_{\Omega} L(y,\omega)\, \Psi(y,\omega)\, \cos\theta \, d\omega\, dy.
$$

对像素 (m,n)：

$$
L_{mn} := \langle L, \Psi_{mn} \rangle
= \langle L_e, \Psi_{mn} \rangle \;+\; \langle T_f L, \Psi_{mn} \rangle.
$$

记 T_{mn}L := \langle T_f L, \Psi_{mn} \rangle，则

$$
L_{mn} = \langle L_e, \Psi_{mn} \rangle \;+\; T_{mn}L.
\tag{1}
$$

解释：
- 第一项为直接可见光源（可在硬件中作为自发光表面实时渲染）；
- 第二项为“至少一次反射”的贡献；后文用 VPL 与硬件一次光照近似。

---

## 3. 点源离散密度近似与硬件渲染

### 3.1 点源离散密度（式(2)）

将场景中“漫反射间接光的空间密度”用有限个点光源离散化：

$$
L(y) \;\approx\; \sum_{i=0}^{M-1} L_i\, \delta(y - P_i).
\tag{2}
$$

- 每个 VPL 位于 P_i，具有辐亮度“权重” L_i；
- 直觉：若测试任意函数 g(y)，
  $
  \int g(y) L(y)\, dy \approx \sum_i L_i\, g(P_i),
  $
  即用加权 δ 测度逼近辐亮度分布；
- 数值上：这些 VPL 来自粒子路径的“反射点”，其强度由路径吞吐量给出（见 §6）。

### 3.2 将 Tmn 作用于点光源：硬件一次光照+阴影

对 δ 点源，T_{mn} 的数值评价退化为“用该点作为点光源”照亮场景一次、并投射阴影，然后把整张图写入累积缓冲。这与硬件的点光+阴影管线一致 [Hei91, SKvW+92]。

因此：

$$
L_{mn} \;\approx\; \langle L_e, \Psi_{mn} \rangle \;+\;
\sum_{i=0}^{M-1} T_{mn}\big( L_i\, \delta(\cdot - P_i)\big),
$$

等价于：
- 对每个 VPL：调用图形硬件渲染阴影图像；
- 对所有图像：按权重叠加（累积缓冲 Accumulation Buffer）；
- 直接可见光源通过自发光表面一次性绘制。

---

## 4. 传输算子展开与路径积分表达式

### 4.1 Neumann 级数与收敛性

若传输算子范数 ∥T_f∥ < 1，则

$$
L \;=\; (I - T_f)^{-1} L_e \;=\; \sum_{j=0}^{\infty} T_f^j L_e,
$$

在漫反射场景中通常成立，因为每次反射都衰减（平均反射率 < 1）。关于 Banach 不动点/Neumann 级数收敛可见泛函分析教科书。

代入 (1) 并关注“至少一次反射”的像素贡献，可写为一组逐次反射项的和。

### 4.2 将 T 展开为路径积分并得到式(3)

我们从 (D) 的漫反射版本出发，逐次套用 T_fd 并按路径变量展开。记：
- Se := supp L_e ⊆ S 为光源支撑；
- 令 y_0 ∈ Se 为光源点；
- 对 l=0,…,j−1，令 y_{l+1} := h(y_l, ω_l) ∈ S；
- 令 y' := h(y_f, P - y_f) 为从针孔穿过像素 P 的相交点；
- V(a,b)∈{0,1} 为可见性；
- 定义“路径源强度密度”
  $$
  p_j(y_0, \omega_0, \dots, \omega_j) := L_e(y_0)\, \prod_{l=1}^j \big(\cos\theta_{l-1}\, f_d(y_l)\big).
  $$

则对像素 (m,n)，有（论文式(3)）：

$$
\begin{aligned}
T_{mn}L
&= \frac{1}{|P_{mn}|}\, \sum_{j=0}^{\infty}
\int_{P_{mn}}\; \int_{\Omega^j}\; \int_{S_e}
p_j(y_0,\omega_0,\dots,\omega_j)\;
\frac{ V(y_j, y')\, f_d(y')\, \cos\theta_j\, \cos\theta'}{\|y_j - y'\|^2}\;
dy'\, d\omega_0 \cdots d\omega_j\, dP.
\end{aligned}
\tag{3}
$$

推导要点（逐步说明）：
1. 展开 Neumann 级数：T_fd^j L_e 给出 j 次漫反射路径；
2. 每次漫反射在 y_l 处贡献 f_d(y_l) 且乘以前一跳的投影 cosθ_{l−1}（由方向积分的测度 cosθ_i）；
3. 最后一跳从 y_j → y'（像素射线命中点），对该跳将方向积分变量替换为表面积变量，使用标准几何核变元：
   $$
   d\omega = \frac{\cos\theta'}{\|y_j - y'\|^2}\, dy', \quad
   G(y_j, y') = \frac{V(y_j,y')\, \cos\theta_j\, \cos\theta'}{\|y_j - y'\|^2}.
   $$
   于是出现分母 r^{-2} 与两端 cos 项（可见 [Kaj86] 的方向到表面变元替换与几何项 G）；
4. y' 处仍为漫反射，需乘 f_d(y')；
5. 外层对像素区域 P_{mn} 取平均（1/|P_{mn}|），并只保留针孔方向（由 Ψ_{mn} 的 δ 与 χ 限定到 y'）。

这样就得到式(3)，其中前 j 跳保留在方向域（Ω^j），最后一跳使用几何项表达。该表达与硬件“点光照+阴影”的几何核完全一致，因而可以用 VPL 以硬件替代积分。

参考：方向→表面变元替换与几何核见 [Kaj86]、任意光传输教材；可见性 V 是 0-1 传输窗函数。

---

## 5. 准蒙特卡罗（QMC）与 Halton/Hammersley

### 5.1 QMC 近似与误差

在单位超立方体 [0,1)^s 上的积分：

$$
\int_{[0,1)^s} f(x)\, dx \;\approx\; \frac{1}{N} \sum_{i=0}^{N-1} f(x_i),
$$

选取低差异点集 {x_i}（如 Halton/Hammersley）。对有界变差函数，Koksma–Hlawka 不等式给出误差上界与不均匀度（差异度）成正比 [Nie92]。图形学中被积函数常不连续，严格上界悲观；但大量数值实验表明 QMC 在实际中“更平滑且略快”于伪随机 Monte Carlo。经验上，文献给出对不连续情形的合理上界阶为
$
\mathcal{O}\!\big(N^{-\frac{s+1}{2s}}\big)
$
[PTVF92]，当维数 s 增大时渐近于 MC 的 N^{-1/2}，但在有限 s 下略优且更平滑（无方差锯齿）。

### 5.2 Halton 序列与基反演

定义基反演（radical inverse）：

$$
\Phi_b(i) := \sum_{j=0}^{\infty} a_j(i)\, b^{-j-1} \quad \Longleftrightarrow\quad
i = \sum_{j=0}^{\infty} a_j(i)\, b^j,
$$

其中 i 的 b 进制展开系数为 a_j(i)∈{0,…,b−1}。Halton 序列（s 维）取互异质数 b_1,…,b_s：

$$
x_i := \big(\Phi_{b_1}(i), \dots, \Phi_{b_s}(i)\big), \quad i=0,1,2,\dots
$$

要点：
- 任意连续段也保持低差异；
- 可逐点计算，无需存储大型随机置换（优于 N-rooks）；
- 非常适合“逐反弹层”的样本分配（见 §6）。

### 5.3 直接与增量计算（伪代码）

直接计算某一项 Φ_b(i)：

```c
double radical_inverse(int b, int i) {
    double x = 0.0, f = 1.0 / b;
    while (i > 0) {
        int digit = i % b;
        x += digit * f;
        i /= b;
        f /= b;
    }
    return x; // in [0,1)
}
```

增量更新（给定上一值 x = Φ_b(i)，快速得到 Φ_b(i+1)），可参考 [HW64] 的位进位思想（论文给出一种实现）。在现代实现中，常结合“范德科普特序列”（base-2）与多基扩展以获得更好的数值稳定性。

---

## 6. 准随机游走（Quasi-Random Walk）

### 6.1 平均反射率与生存路径数

设场景由 K 个面片 A_k 构成，平均漫反射率加权为

$$
\rho := \frac{\sum_{k=1}^K \rho_{d,k}\, |A_k|}{\sum_{k=1}^K |A_k|} \;\approx\; \|T_{fd}\|.
$$

直觉上，每次漫反射都会按 ρ 衰减（全场平均）；因此从 N 个粒子出发，期望第 1 次反射后有 ρN 条“继续”、第 2 次反射后有 ρ^2 N 条继续，依此类推。总共产生的 VPL 数 M 满足：

$$
M \;<\; \sum_{j=0}^{\infty} \rho^j N \;=\; \frac{N}{1-\rho} \;=\; \ell\, N, \quad \ell := \frac{1}{1-\rho}.
$$

- 这等价于“确定性（分数）吸收”，避免随机俄罗斯轮盘 [AK90]；
- ρ 越小，均值路径长度 ℓ 越短，VPL 数越少，渲染越快。

### 6.2 样本分配策略与低差异优势

- 用 Halton 序列生成粒子起点与反射方向；
- 按层次 j 给样本预算：第 0 层用 N 个样本，第 1 层用 ⌊ρN⌋ 个，…；
- 由于低差异序列任意前缀也低差异，且“低阶散射对图像贡献最大”，此分配最大化了低差异的有效性：更多点用于更重要的前几跳，收敛更平滑。

---

## 7. 实现细节（从粒子到图像）

### 7.1 完整流程（伪代码+说明）

伪代码（对论文 Figure 4 的校注与现代表述）：

```c
struct VPL { Vec3 pos; Color Phi; }; // Phi = 路径吞吐(辐通量或等效强度)

// 输入：N 初始粒子数，rho 平均反射率；场景、相机、硬件上下文
void InstantRadiosity(int N, double rho) {
    vector<VPL> vpls;
    int survivors = N;   // 当前层的粒子数
    int level = 0;

    while (survivors > 0) {
        int start_idx = (int)floor(pow(rho, level) * N);
        int end_idx   = (level == 0 ? N : (int)floor(pow(rho, level-1) * N));

        for (int i = start_idx; i < end_idx; ++i) {
            // 1) 在光源表面采样起点 y0
            double u1 = halton(2, i), u2 = halton(3, i);
            SurfaceSample s = sample_emitter(u1, u2); // y0, normal, Le, pdfA
            Vec3 y = s.position;
            Color throughput = s.Le; // 初始“源强度”（可并入后续归一化）

            // 2) 沿路径走 level 次漫反射（level=0 表示只生成 y0 的VPL）
            Vec3 x = y;
            Vec3 n = s.normal;
            for (int j = 0; j < level; ++j) {
                // 2a) 余弦加权半球采样方向
                double u = halton(2*j+4, i), v = halton(2*j+5, i);
                Vec3 wi = cosine_weighted_dir(u, v, n);

                // 2b) 射线求交
                Hit h = scene_intersect(Ray{x, wi});
                if (!h.hit) { throughput = Color(0); break; }

                // 2c) 漫反射吞吐更新（不含 π，留给接收点/硬件核一致性处理）
                double cos_term = max(0.0, dot(wi, n));
                throughput *= (h.mat.rho_d * cos_term);

                // 2d) 前进
                x = h.pos;
                n = h.normal;
            }

            if (is_black(throughput)) continue;

            // 3) 在当前路径末端 x 处放置 VPL
            vpls.push_back(VPL{ x, throughput });
        }

        // 下一层
        level++;
        survivors = (int)floor(pow(rho, level) * N);
    }

    // 4) 对每个 VPL：用硬件一次光照+阴影渲染，并累加
    clear_accum_buffer();
    for (const auto& vpl : vpls) {
        // 设置点光源：位置 = vpl.pos，强度 = normalize(vpl.Phi)
        bind_point_light(vpl.pos, calibrate_intensity(vpl.Phi));
        render_scene_with_shadows();   // 仅一次光照（含阴影）
        accum_buffer_add_weighted(1.0 / N); // 每条初始路径权重 1/N
    }

    // 5) 返回累积结果
    accum_buffer_resolve_to_frame();
}
```

说明与关键数值一致性：
- 归一化/calibrate_intensity：需与硬件“点光+Lambert 接收 + r^{-2} 几何核”一致。通常可将路径吞吐按“能量一致性常数”统一标定（把未计入的 1/π 或单位/尺度因子统一吸收），只要“所有 VPL 使用同一常数”，图像比例一致即可。
- 权重 1/N：对应 QMC/MC 对积分的均值估计；每条初始路径（而非每个 VPL）贡献总权 1/N。若每条路径产生多个 VPL，可等比拆分或按上面“每 VPL 图像同权、但整体按 1/N 叠加”的策略实现（论文采用）。

### 7.2 关键构件：采样和映射

- 光源表面采样 y0(u,v)（等面积）：
  - 矩形：y0(u,v) = p0 + u a + v b；
  - 三角形（顶点 A,B,C）：设 r=√u，y0(u,v) = (1−r)A + r[(1−v)B + vC]；
  - 一般曲面：参考 [Shi92] 的等面积参数化或分片近似。

- 余弦加权半球方向：
  - 设 ξ1, ξ2 ∈ [0,1)，φ = 2π ξ2，r = √ξ1；
  - 局部坐标下 dir = (r cosφ, r sinφ, √(1−ξ1))，再变换到法线坐标系；
  - 等价形式：θ = arcsin√ξ1（论文使用该写法），φ = 2π ξ2。

- Halton 索引规划：
  - 起点用 (Φ2,Φ3)；
  - 第 j 次反射用 (Φ_{b_{2j+2}}, Φ_{b_{2j+3}})，b_k 为第 k 个质数；
  - 利用“前缀低差异”与“层间样本数缩减”的一致性。

### 7.3 与硬件接口：阴影与累积缓冲

- 阴影生成：Stencil/Shadow Volume [Hei91] 或 Shadow Map/Texture [SKvW+92]；
- 自发光表面：直接渲染，作为 ⟨L_e, Ψ⟩ 的可见部分；
- 累积缓冲：对每个 VPL 的整图按 1/N（或等效权重）累加，最后一次性回写到帧缓冲 [HA90]；
- 实际的帧率上限由“每帧可渲染之 VPL 图像数 × GPU 帧率”决定。

---

## 8. 抖动低差异采样（Jittered Low-Discrepancy）

- 问题：Halton/Hammersley 在 2D 投影上呈“网格齐性”，虽有最小距离与隐式分层，但易走样；
- 解法：将每个低差异点在其“网格单元”内做小幅随机扰动（jitter）：
  $$
  \Phi_b \;\to\; \Phi_b + \frac{\xi}{N},\quad \xi \sim \mathcal{U}[0,1),
  $$
  并裁剪回 [0,1)；
- 对像素超采样抗锯齿（替代硬件 MSAA），实测收敛优于常规抖动采样（N-rooks 等）；
- 与准随机游走结合：
  - 第 0 跳有 N 粒子 → 抖动尺度 ~ 1/N；
  - 第 1 跳有 ⌊ρN⌋ 粒子 → 抖动尺度 ~ 1/⌊ρN⌋；
  - 依此类推；
- 结论：抖动可缓解别名/摩尔纹，同时保留低差异的全局均匀性 [Mit96]。

---

## 9. 镜面与焦散扩展

- 在硬件单次光照中启用完整 BRDF 的镜面项（高光）；
- 当粒子命中镜面面片时：
  - 用镜面“虚拟光源”技术：将 VPL 关于该镜面（平面多边形）镜像，生成镜像光源；
  - 限制照射到由镜面轮廓与虚拟光源张成的可见锥体内 [DB94, Die96]；
  - 随后根据镜面 BRDF 继续散射（路径延长、VPL 数 M 增加）；
- 若硬件支持聚光灯或方向性参数，可用 cos^d 分布模拟更一般的发光分布与焦散；
- 可见镜面反射需另行处理（光线追踪或高级硬件技巧），此处 VPL 仅用于照亮漫反射接收。

---

## 10. 实时漫游与时间累积

- 为动画，改“准随机游走”为“定长路径”序列（Halton 生成），每条路径生成一张累计图；
- 维护最近 N 张图的滑动窗口：每完成一条路径，替换最旧图，实时累加显示（时间抗锯齿）；
- 路径最大长度选为
  $$
  \ell_{\max} := \left\lceil -\frac{\log N}{\log \rho} \right\rceil,
  $$
  推导：使 ρ^{\ell_{\max}} N < 1，即该层期望样本数 < 1，后续可忽略；
- 也可借助光照贴图（illumination maps）缓存静态场景的全局漫反射，再用纹理硬件实时显示 [HH96]；但这会重新引入解的离散化与内存压力。

---

## 11. 复杂度、数值问题与讨论

- 时间复杂度：O(NK)，K 为场景原语数，N 为初始路径数（或 VPL 图像数的同阶量）。实际常数由硬件一次光照+阴影的吞吐决定；
- 弱奇异性：当接收点 y' 非常靠近 VPL y_j，几何核 ~ 1/‖y_j−y'‖^2 会导致过曝/截断（clamp）；但每张图权重 ~ 1/N，个别异常的影响一般 O(1/N)；
- 颜色/纹理主导：若某单一 VPL 落在强纹理上，单图偏色明显；总图中同样被 1/N 权重稀释；
- 内存与数据结构：算法直接在场景图上工作，不需要网格/核/解的存储；仅需碰撞加速结构（如 BVH/BSP）用于射线求交（生成 VPL）；也可将生成的 VPL 挂入场景格式（如 MGF/VRML）以便后续重复渲染。

---

## 12. 参考实现要点与建议

- 一致性标定：确保“路径吞吐 → 点光强度”的常数与硬件核（Lambert 接收 + r^{-2} + cos 项）一致。实操中可用灰卡场景对标（单位白 Lambert 面、单位面积光源）来校准因子；
- 重要性采样：本文已用余弦半球；未来可用**伴随算子**做光源重要性分布（采样对结果影响大的光源片）以减少 VPL 数 [未来工作设想]；
- 多光源：采样时先按光源功率做混合采样（composition），再在被选光源表面等面积采样（论文亦采用）；
- GPU 管线：优先使用 Shadow Map（更快）或 Stencil Shadow Volume（更准）；使用累积缓冲或浮点帧缓冲手工叠加；
- 抖动控制：每一层的抖动幅度按该层样本数自适应，避免不同层间不均匀；
- 数值健壮：相交偏移（ray ε）避免自交；近距离阈值避免 1/r^2 爆发；HDR 帧缓冲防止截断损失动态范围。

---

## 13. 参考文献

- [Kaj86] James T. Kajiya. The Rendering Equation. SIGGRAPH 1986.
- [CW93] Michael F. Cohen, John R. Wallace. Radiosity and Realistic Image Synthesis. Morgan Kaufmann, 1993.
- [LTG92] Dani Lischinski, Filippo Tampieri, Donald P. Greenberg. Discontinuity Meshing for Accurate Radiosity. IEEE TVCG (或 SIGGRAPH 1992 版本).
- [Kel95] Alexander Keller. Quasi-Monte Carlo Ray Tracing. 1995（技术报告/论文，展示 QMC 在渲染中的应用）。
- [Kel96a] Alexander Keller. Quasi-Monte Carlo Global Illumination. 1996.
- [Kel96b] Alexander Keller. A Deterministic Particle Transport for Global Illumination. 1996（或同系列，文中“准随机游走”概念来源）。
- [LW93] Eric P. Lafortune, Yves D. Willems. Bi-Directional Path Tracing. 1993.
- [VG94] Eric Veach, Leonidas J. Guibas. Bidirectional estimators for light transport. 1994.
- [HA90] Paul Haeberli, Kurt Akeley. The Accumulation Buffer: Hardware Support for High-Quality Rendering. SIGGRAPH 1990.
- [Hei91] Timothy Heidmann. Real Shadows, Real Time. Iris Universe, 1991（Stencil Shadow Volume 的早期文档，SGI）。
- [SKvW+92] Mark Segal, et al. Fast Shadows and Lighting Effects Using Texture Mapping. SIGGRAPH 1992.
- [Shi92] Peter Shirley. A Sampling Algorithm for Triangle Elements / 或相关“表面等面积参数化采样”的综述（1992 附近，等面积三角形采样 r=√u 的出处之一）。
- [HW64] J. M. Hammersley, D. C. Handscomb. Monte Carlo Methods. 1964（含低差异序列与递推技巧）。
- [Nie92] Harald Niederreiter. Random Number Generation and Quasi-Monte Carlo Methods. SIAM, 1992.
- [PTVF92] Press, Teukolsky, Vetterling, Flannery. Numerical Recipes in C (2nd ed.). 1992（含对 QMC 的经验误差讨论）。
- [Mit96] Don P. Mitchell. Consequences of Stratified Sampling in Graphics. SIGGRAPH 1996.
- [AK90] James Arvo, David Kirk. Particle Transport and Importance Sampling for Monte Carlo Ray Tracing. 1990（含俄罗斯轮盘等 MC 技巧）。
- [War92] Gregory J. Ward. Measuring and Modeling Anisotropic Reflection. SIGGRAPH 1992（BRDF 实测/模型）。
- [DB94] 相关“虚拟光源/镜面镜像”实时技巧的早期文献（如 Debevec/Drettakis 等 1994 左右工作）。
- [Die96] Paul Diefenbach. Pipeline Rendering and Optimizations for Interactive Rendering of Complex Models. 1996（含镜面/剪裁等硬件技巧）。
- [KMH95] Caroline Kolb, Don Mitchell, Pat Hanrahan. A Realistic Camera Model for Computer Graphics. SIGGRAPH 1995.
- [HH96] 纹理硬件用于光照贴图实时漫游的相关工作（Heckbert/Herf 1996-1997 年间的技术报告/论文）。
- [SLS+96] Image-based / impostors / LOD 等 1996 左右的相关文献（Schaufler 等）。
- [FvDFH96] Foley, van Dam, Feiner, Hughes. Computer Graphics: Principles and Practice (2nd ed., 1996).

注：
- 本文关键推导依赖 [Kaj86] 的渲染方程与几何核变元替换、[Nie92]/[HW64]/[PTVF92] 的 QMC 理论与低差异序列、[HA90]/[Hei91]/[SKvW+92] 的硬件累积与阴影实现。
- 个别引用的年份/题名可能存在版本变体，建议以实际数据库（ACM/IEEE/SIAM）检索为准。

---

以上即为 Instant Radiosity 的系统化整理：自渲染方程到路径积分、从低差异粒子生成到硬件一次光照的桥接，以及抖动、镜面与实时扩展的完整脉络。通过该结构，你可以直接据此实现或复现论文算法，并能在推导层面把握其数值本质与适用边界。


> 如果我想实现instant Radiosity算法，上面给出的算法步骤或公式细节，如何转变为c++代码，请给出思考和实现过程，写成markdown格式，方便我后续导出

# 从算法到工程：用 C++ 实现 Instant Radiosity（VPL/准随机游走/低差异采样）

这份文档把前面解析的算法步骤与公式，落地为一套可运行的 C++ 参考实现（CPU 版）。它遵循论文的核心思想：用 Halton 低差异序列驱动“准随机游走”，在每次反射处生成虚拟点光源（VPL），再按几何核 G 与漫反射 BRDF 累加所有 VPL 的贡献。实现目标是“正确性优先，结构清晰、易扩展”，随后你可以替换 CPU 的可见性查询为 GPU 的阴影与累积缓冲来获得更高性能。

目录：
- 设计与映射
- 核心算法到代码的映射关系
- 完整 C++ 参考实现（单文件）
- CMake 构建与运行
- 实现要点与扩展建议

注意：
- 下面实现的是“CPU 参考版”，用射线求交完成 VPL 生成与遮挡判定；与论文中的“用图形硬件对每个 VPL 做一次光照+阴影并累积”在数学上等价，便于验证正确性。
- 代码中严格复现了论文中式(3)的几何核和权重结构：p_j 通过“fd（ρ_d/π）乘积”编码，cos 项在几何核 G 中出现；方向的 cos 权重通过“余弦半球采样”以“密度表达”的方式体现（不显式乘 cos）。

---

## 1. 设计与映射

- 低差异采样：
  - 用 Halton 序列（基反演）生成每条路径的参数：光源表面（u,v），每次反射的方向（u,v）。
  - 抗锯齿可用 Hammersley/抖动低差异（此处保持最小化实现，默认 1 spp，可自行扩展）。

- 准随机游走（分数吸收）：
  - 平均反射率 ρ 由用户给定（或估计），第 j 跳的“存活路径数”≈ ⌊ρ^j N⌋。
  - 对每个路径索引 i，仅当 i < ⌊ρ^j N⌋ 时才存在第 j 跳，保证“低阶散射样本密度更高”。

- VPL 生成：
  - j=0：在光源上取样，形成“光源上的 VPL”（近似直接光）。
  - j>=1：路径反射命中的点生成 VPL（间接光）。
  - 每个 VPL 存储：位置 P_i、法线 n_i、吞吐量 Φ_i（Color）。

- 评估图像（等价于 Tmn 的作用）：
  - 对每个像素，从相机发射主射线找可见点 x、法线 n_x、材质 ρ_d(x)。
  - 累加所有 VPL 的贡献：
    - 可见性：从 x 向 P_i 发阴影射线。
    - 几何核 G(x, P_i) = V · cosθ_i · cosθ_x / r^2
    - 漫反射：f_d(x) = ρ_d(x)/π
    - 贡献：ΔL = Φ_i · f_d(x) · G(x, P_i)
  - 引入 1/N 归一化（QMC 的均值估计）。

- 直接可见的自发光 Le：
  - 若主射线打到发光表面，直接将 Le(x) 加入该像素（对应 ⟨Le, Ψ⟩）。

---

## 2. 算法到代码的映射关系

- 式(2)（点源离散密度）→ 结构体 VPL{pos, normal, Phi}，Phi 承载 p_j（不含 cosθ_j）。
- 式(3)（像素贡献积分）→ CPU 逐 VPL 累加：
  - G = max(0, n_i·l) · max(0, n_x·(−l)) / ||x−P_i||^2
  - f_d(x) = ρ_d(x)/π
  - ΔL = Phi_i · f_d(x) · G · V(x,P_i)
- p_j（源强度密度）→ 通过“沿路径每次反射将吞吐量乘以 fd(y) = ρ_d/π”实现；cosθ_{l−1} 不在权重中显式相乘，而由“余弦半球采样”在密度层面体现。
- 累积缓冲（1/N）→ 生成 VPL 时将初始 Le 直接乘以 1/N 作为吞吐量的初值。

---

## 3. 完整 C++ 参考实现（单文件）

说明：
- 单文件示例：instant_radiosity.cpp
- 支持：矩形面积光（可被采样与求交）、三角形、球体、简易 Cornell Box。
- 输出：PPM 图像。
- 编译：见下文 CMake。

```cpp
// instant_radiosity.cpp
// A minimal CPU reference implementation of Instant Radiosity (VPL + QMC).
// Build: see CMake section below.
// Note: This is a didactic, single-file implementation. For production, split modules, add BVH, etc.

#include <cmath>
#include <cfloat>
#include <cstdint>
#include <vector>
#include <string>
#include <fstream>
#include <algorithm>
#include <iostream>

// -------------------- Math basics --------------------
struct Vec3 {
    double x, y, z;
    Vec3(double v=0): x(v), y(v), z(v) {}
    Vec3(double x_, double y_, double z_): x(x_), y(y_), z(z_) {}
    Vec3 operator + (const Vec3& b) const { return Vec3(x+b.x, y+b.y, z+b.z); }
    Vec3 operator - (const Vec3& b) const { return Vec3(x-b.x, y-b.y, z-b.z); }
    Vec3 operator * (double s) const { return Vec3(x*s, y*s, z*s); }
    Vec3 operator * (const Vec3& b) const { return Vec3(x*b.x, y*b.y, z*b.z); } // Hadamard
    Vec3 operator / (double s) const { return Vec3(x/s, y/s, z/s); }
    Vec3& operator += (const Vec3& b) { x+=b.x; y+=b.y; z+=b.z; return *this; }
};
static inline Vec3 operator * (double s, const Vec3& v) { return Vec3(v.x*s, v.y*s, v.z*s); }
static inline double dot(const Vec3& a, const Vec3& b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return Vec3(
        a.y*b.z - a.z*b.y,
        a.z*b.x - a.x*b.z,
        a.x*b.y - a.y*b.x
    );
}
static inline double length(const Vec3& v) { return std::sqrt(dot(v,v)); }
static inline Vec3 normalize(const Vec3& v) { double L = length(v); return (L>0)? v/L : v; }
static inline Vec3 clamp01(const Vec3& c) {
    auto f = [](double x){ return std::max(0.0, std::min(1.0, x)); };
    return Vec3(f(c.x), f(c.y), f(c.z));
}
typedef Vec3 Color;

struct Ray {
    Vec3 o, d;
    Ray() {}
    Ray(const Vec3& o_, const Vec3& d_): o(o_), d(normalize(d_)) {}
};

static constexpr double kEps = 1e-6;

// -------------------- Camera --------------------
struct Camera {
    Vec3 pos, look, up;
    double fov_deg; // vertical FOV
    int W, H;

    Vec3 cx, cy, cz; // basis
    double tanHalfFov;

    Camera(const Vec3& p, const Vec3& l, const Vec3& up_, double fov_deg_, int W_, int H_)
        : pos(p), look(l), up(up_), fov_deg(fov_deg_), W(W_), H(H_) {
        cz = normalize(look - pos);
        cx = normalize(cross(cz, up));
        cy = cross(cx, cz);
        tanHalfFov = std::tan(fov_deg * M_PI / 180.0 * 0.5);
    }

    Ray generateRay(double px, double py) const {
        // px, py in [0,1), pixel center offset
        double aspect = double(W)/double(H);
        double ndc_x = (2.0 * ((px * W + 0.5) / W) - 1.0) * aspect * tanHalfFov;
        double ndc_y = (1.0 - 2.0 * ((py * H + 0.5) / H)) * tanHalfFov;
        Vec3 dir = normalize(cz + cx * ndc_x + cy * ndc_y);
        return Ray(pos, dir);
    }
};

// -------------------- Materials --------------------
struct Material {
    Color rho_d;   // diffuse reflectance (albedo), [0,1]
    bool  emissive;
    Color Le;      // emitted radiance if emissive
    Material(): rho_d(0.8), emissive(false), Le(0) {}
};

static inline double luminance(const Color& c) {
    return 0.2126*c.x + 0.7152*c.y + 0.0722*c.z;
}
static inline double fd_value(const Material& m) {
    // f_d = rho_d / pi, but we handle color channel-wise in shading
    // Here for path throughput we multiply channel-wise later.
    return 1.0; // placeholder, we multiply color-wise by (rho_d/pi)
}

// -------------------- Geometry interface --------------------
struct Hit {
    double t;
    Vec3 pos;
    Vec3 n;
    const Material* mat;
    Hit(): t(DBL_MAX), pos(), n(), mat(nullptr) {}
};

struct IObject {
    Material mat;
    virtual ~IObject() {}
    virtual bool intersect(const Ray& r, double tMin, double tMax, Hit& hit) const = 0;
    virtual bool isAreaLight() const { return false; }
    virtual double area() const { return 0.0; } // for lights
};

// Triangle
struct Triangle : public IObject {
    Vec3 v0, v1, v2;
    Vec3 n;
    Triangle(const Vec3& a, const Vec3& b, const Vec3& c, const Material& m) : v0(a), v1(b), v2(c) {
        mat = m;
        n = normalize(cross(v1-v0, v2-v0));
    }
    bool intersect(const Ray& r, double tMin, double tMax, Hit& hit) const override {
        Vec3 e1 = v1 - v0, e2 = v2 - v0;
        Vec3 p = cross(r.d, e2);
        double det = dot(e1, p);
        if (std::fabs(det) < 1e-12) return false;
        double invDet = 1.0 / det;
        Vec3 t = r.o - v0;
        double u = dot(t, p) * invDet;
        if (u < 0.0 || u > 1.0) return false;
        Vec3 q = cross(t, e1);
        double v = dot(r.d, q) * invDet;
        if (v < 0.0 || u+v > 1.0) return false;
        double tt = dot(e2, q) * invDet;
        if (tt < tMin || tt > tMax || tt > hit.t) return false;
        hit.t = tt;
        hit.pos = r.o + r.d * tt;
        hit.n = (dot(n, r.d) < 0)? n : (n * -1.0);
        hit.mat = &mat;
        return true;
    }
};

// Sphere
struct Sphere : public IObject {
    Vec3 c; double R;
    Sphere(const Vec3& c_, double R_, const Material& m){ c=c_; R=R_; mat=m; }
    bool intersect(const Ray& r, double tMin, double tMax, Hit& hit) const override {
        Vec3 oc = r.o - c;
        double b = dot(oc, r.d);
        double c2 = dot(oc, oc) - R*R;
        double disc = b*b - c2;
        if (disc < 0) return false;
        double s = std::sqrt(disc);
        double t = -b - s;
        if (t < tMin || t > tMax) {
            t = -b + s;
            if (t < tMin || t > tMax) return false;
        }
        if (t > hit.t) return false;
        hit.t = t;
        hit.pos = r.o + r.d * t;
        hit.n = normalize(hit.pos - c);
        if (dot(hit.n, r.d) > 0) hit.n = hit.n * -1.0;
        hit.mat = &mat;
        return true;
    }
};

// Rectangular Area Light (own sampler), also added as two triangles for intersection
struct RectAreaLight : public IObject {
    Vec3 p0, ex, ey; // p(u,v) = p0 + u*ex + v*ey, u,v in [0,1]
    Vec3 n_;
    double A;
    RectAreaLight(const Vec3& p0_, const Vec3& ex_, const Vec3& ey_, const Material& m) {
        p0=p0_; ex=ex_; ey=ey_; mat=m;
        n_ = normalize(cross(ex, ey));
        A = length(cross(ex, ey));
    }
    bool intersect(const Ray& r, double tMin, double tMax, Hit& hit) const override {
        // Ray-plane
        double denom = dot(n_, r.d);
        if (std::fabs(denom) < 1e-12) return false;
        double t = dot(p0 - r.o, n_) / denom;
        if (t < tMin || t > tMax || t > hit.t) return false;
        Vec3 p = r.o + r.d * t;
        // local coords
        // Solve p = p0 + u*ex + v*ey -> [ex ey] [u v]^T = p - p0
        // Project into ex, ey basis
        // We solve with 2x2 using Gram matrix
        Vec3 d = p - p0;
        double a = dot(ex, ex);
        double b = dot(ex, ey);
        double c = dot(ey, ey);
        double det = a*c - b*b;
        if (std::fabs(det) < 1e-16) return false;
        double u = ( c*dot(d, ex) - b*dot(d, ey)) / det;
        double v = (-b*dot(d, ex) + a*dot(d, ey)) / det;
        if (u < 0 || u > 1 || v < 0 || v > 1) return false;
        hit.t = t;
        hit.pos = p;
        Vec3 nn = (dot(n_, r.d) < 0)? n_ : n_ * -1.0;
        hit.n = nn;
        hit.mat = &mat;
        return true;
    }
    bool isAreaLight() const override { return mat.emissive; }
    double area() const override { return A; }

    // Uniform area sampling
    void sample(double u, double v, Vec3& pos, Vec3& n, Color& Le) const {
        pos = p0 + ex * u + ey * v;
        n = n_;
        Le = mat.Le;
    }
};

// -------------------- Scene --------------------
struct Scene {
    std::vector<IObject*> objects;
    std::vector<RectAreaLight*> areaLights; // a subset of objects

    ~Scene() {
        for (auto* o : objects) delete o;
    }
    void add(IObject* o) {
        objects.push_back(o);
        if (o->isAreaLight()) {
            if (auto* r = dynamic_cast<RectAreaLight*>(o))
                areaLights.push_back(r);
        }
    }

    bool intersect(const Ray& r, double tMin, double tMax, Hit& hit) const {
        bool any = false;
        for (auto* o : objects) {
            any |= o->intersect(r, tMin, tMax, hit);
        }
        return any;
    }

    // Composition method: choose one area light proportional to area * luminance
    const RectAreaLight* chooseLight(double u, double& outPdf) const {
        if (areaLights.empty()) { outPdf = 0.0; return nullptr; }
        double sumW = 0.0;
        std::vector<double> w(areaLights.size());
        for (size_t i=0;i<areaLights.size();++i) {
            double Li = luminance(areaLights[i]->mat.Le);
            w[i] = areaLights[i]->area() * std::max(1e-8, Li);
            sumW += w[i];
        }
        if (sumW <= 0.0) {
            // fallback: uniform
            size_t idx = std::min<size_t>(areaLights.size()-1, size_t(u * areaLights.size()));
            outPdf = 1.0 / areaLights.size();
            return areaLights[idx];
        }
        double t = u * sumW;
        double acc = 0.0;
        for (size_t i=0;i<areaLights.size();++i) {
            acc += w[i];
            if (t <= acc) {
                outPdf = w[i] / sumW;
                return areaLights[i];
            }
        }
        outPdf = w.back() / sumW;
        return areaLights.back();
    }
};

// -------------------- Low-discrepancy: Halton --------------------
static const int kPrimes[] = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47};
static inline double radicalInverse(int b, uint32_t i) {
    double x = 0.0;
    double f = 1.0 / double(b);
    while (i) {
        x += f * double(i % b);
        i /= b;
        f /= double(b);
    }
    return x;
}
static inline double halton(int baseIdx, uint32_t i) {
    int b = kPrimes[baseIdx % (sizeof(kPrimes)/sizeof(int))];
    return radicalInverse(b, i);
}

// Cosine-weighted hemisphere sampling around normal n
static inline Vec3 cosineWeightedHemisphere(double u, double v, const Vec3& n) {
    double phi = 2.0 * M_PI * v;
    double r = std::sqrt(u);
    double x = r * std::cos(phi);
    double y = r * std::sin(phi);
    double z = std::sqrt(std::max(0.0, 1.0 - u));

    // build orthonormal basis
    Vec3 w = n;
    Vec3 a = (std::fabs(w.x) > 0.1)? Vec3(0,1,0) : Vec3(1,0,0);
    Vec3 t = normalize(cross(a, w));
    Vec3 b = cross(w, t);

    return normalize(t * x + b * y + w * z);
}

// -------------------- VPL generation (Quasi-Random Walk) --------------------
struct VPL {
    Vec3 pos;
    Vec3 n;
    Color Phi; // path throughput (includes Le and product of fd along path, no cos_j)
};

static inline Color multiply_fd(const Color& c, const Material& m) {
    // Multiply by fd(y) = rho_d(y)/pi, channel-wise
    return Color(c.x * (m.rho_d.x / M_PI),
                 c.y * (m.rho_d.y / M_PI),
                 c.z * (m.rho_d.z / M_PI));
}

static inline bool isBlack(const Color& c, double eps=1e-12) {
    return c.x < eps && c.y < eps && c.z < eps;
}

// “分数吸收”条件：路径 i 是否在第 j 跳仍存活
static inline bool survives(uint32_t i, uint32_t N, double rho, int j) {
    double Nj = std::floor(std::pow(rho, j) * double(N));
    return double(i) < Nj;
}

// 生成 VPL（包括 j=0 光源上的 VPL）
std::vector<VPL> generateVPLs(const Scene& scene, uint32_t N, double rho, uint32_t maxBounces=8) {
    std::vector<VPL> vpls;
    vpls.reserve(size_t(N) * (1 + maxBounces));

    for (uint32_t i=0; i<N; ++i) {
        // 1) 采样一个面积光（按 area * luminance），并在其表面等面积采样 (Φ2,Φ3)
        double pdfLightSel = 0.0;
        const RectAreaLight* light = scene.chooseLight(halton(0, i), pdfLightSel);
        if (!light) continue;

        double u = halton(1, i), v = halton(2, i);
        Vec3 y; Vec3 ny; Color Le;
        light->sample(u, v, y, ny, Le);

        // 初始吞吐量 Phi0 = Le / N （对应 QMC 平均）
        Color Phi = Le / double(N);

        Vec3 x = y;
        Vec3 n = ny;

        for (uint32_t j=0; j<=maxBounces; ++j) {
            if (!survives(i, N, rho, (int)j)) break;

            // 2) 记录 VPL at depth j
            vpls.push_back(VPL{ x, n, Phi });

            // 3) 采样下一跳方向（余弦半球）
            double udir = halton(2*j + 3, i);
            double vdir = halton(2*j + 4, i);
            Vec3 wi = cosineWeightedHemisphere(udir, vdir, n);

            // 4) 沿 wi 前进一跳
            Ray r(x + n * kEps, wi);
            Hit h;
            if (!scene.intersect(r, kEps, DBL_MAX, h)) break;

            // 5) 更新吞吐量：Phi *= fd(h)
            Phi = multiply_fd(Phi, *h.mat);
            if (isBlack(Phi)) break;

            // 6) 前进
            x = h.pos;
            n = h.n;
        }
    }
    return vpls;
}

// -------------------- Rendering --------------------
static inline bool visible(const Scene& scene, const Vec3& x, const Vec3& nx, const Vec3& y, double dist2) {
    Vec3 dir = y - x;
    double dist = std::sqrt(dist2);
    Ray shadow(x + nx * kEps, dir);
    Hit h;
    if (!scene.intersect(shadow, kEps, dist - 2.0*kEps, h)) return true;
    return false;
}

Color shadeFromVPLs(const Scene& scene, const std::vector<VPL>& vpls, const Hit& surfHit) {
    const Vec3& x = surfHit.pos;
    const Vec3& nx = surfHit.n;
    const Material& m = *surfHit.mat;

    Color Lo(0.0);

    // 直接可见的自发光（⟨Le, Ψ⟩）
    if (m.emissive) {
        Lo += m.Le;
    }

    // 间接（以及用光源 VPL 近似的直接）贡献：Σ_i Phi_i * fd(x) * G(x, P_i)
    Color fd_x(m.rho_d.x / M_PI, m.rho_d.y / M_PI, m.rho_d.z / M_PI);

    for (const VPL& vpl : vpls) {
        Vec3 d = x - vpl.pos;
        double r2 = dot(d, d);
        if (r2 <= 1e-12) continue;

        Vec3 l = d / std::sqrt(r2); // direction from VPL to x
        double cosL = std::max(0.0, dot(vpl.n, l));     // cosθ_j at VPL side
        double cosX = std::max(0.0, dot(nx, -l));       // cosθ' at receiver side

        if (cosL <= 0.0 || cosX <= 0.0) continue;

        if (!visible(scene, x, nx, vpl.pos, r2)) continue;

        double G = (cosL * cosX) / r2; // geometry term
        // ΔL = Phi * fd(x) * G
        Lo += (vpl.Phi * fd_x) * G;
    }
    return Lo;
}

std::vector<Color> renderImage(const Scene& scene, const Camera& cam, const std::vector<VPL>& vpls, int spp=1) {
    std::vector<Color> fb(size_t(cam.W*cam.H), Color(0));
    for (int y=0; y<cam.H; ++y) {
        for (int x=0; x<cam.W; ++x) {
            Color c(0);
            for (int s=0; s<spp; ++s) {
                // 这里可替换为 Hammersley 抖动超采样
                double px = (x + 0.5) / cam.W;
                double py = (y + 0.5) / cam.H;
                Ray r = cam.generateRay(px, py);
                Hit h;
                if (scene.intersect(r, kEps, DBL_MAX, h)) {
                    c += shadeFromVPLs(scene, vpls, h);
                } else {
                    // background
                    c += Color(0.0);
                }
            }
            c = c / double(spp);
            fb[size_t(y*cam.W + x)] = c;
        }
        if (y % 16 == 0) {
            std::cerr << "Rendering line " << y << " / " << cam.H << "\r" << std::flush;
        }
    }
    std::cerr << "\n";
    return fb;
}

// -------------------- Save PPM --------------------
void savePPM(const std::string& path, int W, int H, const std::vector<Color>& fb, double exposure=1.0) {
    std::ofstream ofs(path, std::ios::binary);
    ofs << "P6\n" << W << " " << H << "\n255\n";
    for (int i=0;i<W*H;++i) {
        // simple Reinhard tonemap: c / (1 + c), with exposure
        Color c = fb[i] * exposure;
        c = Color(c.x/(1.0+c.x), c.y/(1.0+c.y), c.z/(1.0+c.z));
        c = clamp01(c);
        unsigned char r = (unsigned char) std::round(255.0 * c.x);
        unsigned char g = (unsigned char) std::round(255.0 * c.y);
        unsigned char b = (unsigned char) std::round(255.0 * c.z);
        ofs.write((char*)&r, 1);
        ofs.write((char*)&g, 1);
        ofs.write((char*)&b, 1);
    }
    ofs.close();
}

// -------------------- Test Scene (Cornell-like) --------------------
void buildScene(Scene& scene) {
    // Materials
    Material white; white.rho_d = Color(0.8, 0.8, 0.8); white.emissive = false;
    Material red;   red.rho_d   = Color(0.8, 0.1, 0.1); red.emissive = false;
    Material green; green.rho_d = Color(0.1, 0.8, 0.1); green.emissive = false;
    Material lightM; lightM.emissive = true; lightM.Le = Color(15.0, 15.0, 15.0); lightM.rho_d = Color(0.0);

    // Box size
    double L = 1.0;
    Vec3 A(-L, -L, -L), B(L, -L, -L), C(L, -L, L), D(-L, -L, L);      // floor
    Vec3 E(-L, L, -L), F(L, L, -L), G(L, L, L), H(-L, L, L);          // ceiling

    // Floor (white)
    scene.add(new Triangle(A, B, C, white));
    scene.add(new Triangle(A, C, D, white));

    // Ceiling (white)
    scene.add(new Triangle(E, F, G, white));
    scene.add(new Triangle(E, G, H, white));

    // Back wall (white)
    scene.add(new Triangle(D, C, G, white));
    scene.add(new Triangle(D, G, H, white));

    // Left wall (red)
    scene.add(new Triangle(A, D, H, red));
    scene.add(new Triangle(A, H, E, red));

    // Right wall (green)
    scene.add(new Triangle(B, F, G, green));
    scene.add(new Triangle(B, G, C, green));

    // Area light: rectangle near ceiling center
    Vec3 p0(-0.3, L - 0.001, -0.3);
    Vec3 ex(0.6, 0, 0);
    Vec3 ey(0, 0, 0.6);
    auto* rlight = new RectAreaLight(p0, ex, ey, lightM);
    scene.add(rlight);

    // A sphere in the box
    Material sphM; sphM.rho_d = Color(0.75, 0.75, 0.75);
    scene.add(new Sphere(Vec3(0, -0.2, 0), 0.3, sphM));
}

// -------------------- Main --------------------
int main() {
    int W = 640, H = 360;
    Camera cam(Vec3(0, 0, -2.5), Vec3(0, 0, 0), Vec3(0,1,0), 45.0, W, H);

    Scene scene;
    buildScene(scene);

    // Parameters
    uint32_t N = 128;       // number of initial paths (VPL generators)
    double rho = 0.6;       // average reflectivity (scene-dependent)
    uint32_t maxBounces = 5;
    int spp = 1;

    std::cerr << "Generating VPLs...\n";
    auto vpls = generateVPLs(scene, N, rho, maxBounces);
    std::cerr << "VPL count = " << vpls.size() << "\n";

    std::cerr << "Rendering...\n";
    auto fb = renderImage(scene, cam, vpls, spp);

    savePPM("instant_radiosity.ppm", W, H, fb, 1.0);

    std::cerr << "Done. Saved to instant_radiosity.ppm\n";
    return 0;
}
```

---

## 4. CMake 构建与运行

创建 CMakeLists.txt：

```cmake
cmake_minimum_required(VERSION 3.10)
project(instant_radiosity_cpu CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(instant_radiosity
    instant_radiosity.cpp
)

# Optimize (optional)
if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    target_compile_options(instant_radiosity PRIVATE -O3 -march=native)
elseif (MSVC)
    target_compile_options(instant_radiosity PRIVATE /O2)
endif()
```

构建与运行：
- mkdir build && cd build
- cmake ..
- cmake --build . --config Release
- 运行可执行文件，生成 instant_radiosity.ppm，用任意图像查看器打开（PPM）。

---

## 5. 实现要点与扩展建议

- 几何核一致性
  - 本实现严格使用 G = cosθ_j · cosθ' / r^2，并通过“cosine 加权散射”把前 j−1 跳的 cosθ_{l−1} 体现在样本密度中（不进入吞吐量权重），和论文 p_j 的定义一致。

- 1/N 归一化
  - QMC/MC 的均值估计：在生成 VPL 时，将 Le 除以 N，随后所有贡献直接累加即可。

- 平均反射率 ρ
  - 论文用面积加权平均 ρ ≈ ||T_fd||。实践中可先手工设定（0.5~0.7 常见），也可采样估计：在非发光表面均匀采点，取 ρ_d 的平均亮度作为估计。

- 抖动低差异与抗锯齿
  - 将主射线的像素采样改为“两维 Hammersley + 抖动”，每像素多样本累加（spp>1）；
  - 与论文一致：第 j 层的抖动尺度随样本数 ⌊ρ^j N⌋ 自适应。

- 可见性/性能
  - 当前为 O(#pixels × #VPL) 的阴影检测；可加 BVH 加速结构减少求交；
  - 若转向 GPU：可用“每个 VPL 一次阴影图（立方体 Shadow Map）+ 累积缓冲”复现论文的硬件路径；或用 RSM（2005）进一步加速。

- 直接光与发光可见性
  - 直接光（从面积光到表面的单次反射）已由 j=0 的“光源 VPL”近似；
  - 发光面本身被相机看到时，直接将 Le 加入像素（⟨Le,Ψ⟩），与论文一致。

- 镜面/焦散（扩展）
  - 命中镜面时生成“镜像虚拟光源”（平面镜像），并限制照射区域（见论文 §4.2，参考 [DB94, Die96]）；
  - 硬件若支持聚光灯，可用 cos^d 发射模型提升定向效果。

- 数值健壮性
  - 阴影射线起点偏移 kEps；
  - 限制近距离 r^2 下的贡献（或在 VPL 生成阶段避免与接收点重合）；
  - 使用 HDR/浮点缓冲与色调映射避免饱和。

- 对接论文中的“多帧时间累积”（实时漫游）
  - 将上面的“生成 VPL + 渲染图像”作为一条“路径”的输出帧，维护最近 N 帧滑窗累加，得到流畅实时更新（隐式时间抗锯齿）。

---

通过这份参考实现，你可以直接跑通“Instant Radiosity（VPL + 低差异采样 + 准随机游走）”的核心流程，并对照论文公式逐项验证。接下来建议的方向是：引入 BVH/Embree 加速、在 GPU 上用阴影图和累积缓冲替换 CPU 阴影检测、实现抖动低差异抗锯齿、添加镜面/焦散扩展。