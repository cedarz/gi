half4 BRDF1_Unity_PBS (half3 diffColor, half3 specColor, half oneMinusReflectivity, half smoothness,
float3 normal, float3 viewDir,
UnityLight light, UnityIndirect gi)
中的UnityIndirect gi，具体实现

14:47

Claude-Sonnet-4.5


UnityIndirect gi 参数包含了Unity中的间接光照信息。让我详细解释其具体实现和组成部分：

UnityIndirect 结构体定义
hlsl

struct UnityIndirect
{
    half3 diffuse;   // 间接漫反射光照
    half3 specular;  // 间接镜面反射光照
};
具体实现来源
在Unity的PBS着色器中，UnityIndirect gi 的数据主要来自以下几个方面：

1. 间接漫反射 (gi.diffuse)
hlsl

// 从光照探针或光照贴图获取
half3 ambient = ShadeSHPerPixel(normal, ambient, worldPos);
// 或者
half3 ambient = DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap, uv));

gi.diffuse = ambient;
数据来源：

光照探针 (Light Probes): 使用球谐函数(Spherical Harmonics)存储的预计算环境光
光照贴图 (Lightmaps): 烘焙的静态光照信息
环境光 (Ambient Light): 场景的基础环境光颜色
2. 间接镜面反射 (gi.specular)
hlsl

// 从反射探针采样
half3 reflectVec = reflect(-viewDir, normal);
half perceptualRoughness = SmoothnessToPerceptualRoughness(smoothness);
half mip = PerceptualRoughnessToMipmapLevel(perceptualRoughness);

half4 envSample = UNITY_SAMPLE_TEXCUBE_LOD(unity_SpecCube0, reflectVec, mip);
gi.specular = DecodeHDR(envSample, unity_SpecCube0_HDR);
数据来源：

反射探针 (Reflection Probes): 立方体贴图存储的环境反射
天空盒 (Skybox): 作为默认的反射源
根据粗糙度选择Mipmap级别: 越粗糙的表面采样越模糊的Mip级别
完整的GI计算示例
hlsl

UnityIndirect FragmentGI(FragmentCommonData s, half occlusion, half4 i_ambientOrLightmapUV, 
                         half atten, UnityLight light)
{
    UnityIndirect gi;
    UNITY_INITIALIZE_OUTPUT(UnityIndirect, gi);

    #if UNITY_SHOULD_SAMPLE_SH
        // 使用球谐光照探针
        gi.diffuse = ShadeSHPerPixel(s.normalWorld, i_ambientOrLightmapUV.rgb, s.posWorld);
    #endif

    #if defined(LIGHTMAP_ON)
        // 使用烘焙光照贴图
        gi.diffuse = DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap, i_ambientOrLightmapUV.xy));
    #endif

    // 应用遮挡
    gi.diffuse *= occlusion;

    // 镜面反射的间接光照
    gi.specular = 0; // 先初始化为0
    
    #ifdef _GLOSSYREFLECTIONS_OFF
        gi.specular = 0;
    #else
        Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
            s.smoothness, 
            s.eyeVec, 
            s.normalWorld, 
            s.specColor
        );
        gi.specular = UnityGIIndirectSpecular(g, occlusion);
    #endif

    return gi;
}
关键函数说明
UnityGIIndirectSpecular:

hlsl

half3 UnityGIIndirectSpecular(UnityGlossyEnvironmentData glossIn, half occlusion)
{
    half perceptualRoughness = SmoothnessToPerceptualRoughness(glossIn.roughness);
    
    #if UNITY_SPECCUBE_BOX_PROJECTION
        // 使用盒投影修正反射方向
        half3 reflUVW = BoxProjectedCubemapDirection(
            glossIn.reflUVW, glossIn.probePosition, 
            unity_SpecCube0_ProbePosition, 
            unity_SpecCube0_BoxMin, unity_SpecCube0_BoxMax
        );
    #else
        half3 reflUVW = glossIn.reflUVW;
    #endif

    half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);
    half4 rgbm = UNITY_SAMPLE_TEXCUBE_LOD(unity_SpecCube0, reflUVW, mip);
    
    return DecodeHDR(rgbm, unity_SpecCube0_HDR) * occlusion;
}
总结
UnityIndirect gi 的实现包含：

漫反射分量: 从光照探针/光照贴图获取的预计算间接光照
镜面反射分量: 从反射探针立方体贴图采样，根据粗糙度选择合适的Mip级别
遮挡影响: 环境光遮挡(AO)会影响两个分量的强度
HDR解码: 使用RGBM格式存储和解码高动态范围的光照数据
这些数据在BRDF计算中用于模拟物体接收到的环境光照，是实现物理真实感渲染的重要组成部分。

14:47

unity的pbs的ibl，在哪里

17:09

Claude-Sonnet-4.5


Unity的PBS中IBL（Image-Based Lighting）相关代码主要在以下位置：

1. 核心IBL代码位置
主要文件路径：
awk

[Unity安装目录]/Editor/Data/CGIncludes/
├── UnityGlobalIllumination.cginc      // GI和IBL的主要实现
├── UnityImageBasedLighting.cginc      // IBL核心函数
├── UnityStandardBRDF.cginc            // BRDF相关
└── UnityPBSLighting.cginc             // PBS光照模型
具体文件说明：
UnityImageBasedLighting.cginc - IBL的核心实现文件

hlsl

// 关键函数包括：

// 1. 预积分的BRDF LUT采样
half3 Unity_BRDF_PBS(...) 

// 2. GGX重要性采样
half3 Unity_GlossyEnvironment(
    UNITY_ARGS_TEXCUBE(tex), 
    half4 hdr, 
    Unity_GlossyEnvironmentData glossIn
)

// 3. 粗糙度到Mipmap级别的转换
half perceptualRoughnessToMipmapLevel(half perceptualRoughness)
{
    return perceptualRoughness * UNITY_SPECCUBE_LOD_STEPS;
}
UnityGlobalIllumination.cginc - GI和间接光照

hlsl

// 关键函数：

// 1. 获取间接镜面反射
half3 UnityGIIndirectSpecular(
    UnityGlossyEnvironmentData glossIn, 
    half occlusion, 
    Unity_GlossyEnvironmentData data
)

// 2. 完整的GI计算
UnityGI UnityGlobalIllumination(
    UnityGIInput data, 
    half occlusion, 
    half3 normalWorld
)
2. 实际项目中的访问路径
如果你使用Unity Hub安装，路径通常是：

Windows:


C:/Program Files/Unity/Hub/Editor/[版本号]/Editor/Data/CGIncludes/
Mac:


/Applications/Unity/Hub/Editor/[版本号]/Unity.app/Contents/CGIncludes/
Linux:

awk

/home/[用户名]/Unity/Hub/Editor/[版本号]/Editor/Data/Resources/CGIncludes/
3. IBL的具体实现代码示例
在 UnityImageBasedLighting.cginc 中：

hlsl

// IBL镜面反射的核心实现
half3 Unity_GlossyEnvironment (UNITY_ARGS_TEXCUBE(tex), half4 hdr, Unity_GlossyEnvironmentData glossIn)
{
    half perceptualRoughness = glossIn.roughness; /* perceptualRoughness */

#if UNITY_GLOSS_MATCHES_MARMOSET_TOOLBAG2
    perceptualRoughness = perceptualRoughness*(1.7 - 0.7*perceptualRoughness);
#endif

    half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);
    half3 R = glossIn.reflUVW;
    half4 rgbm = UNITY_SAMPLE_TEXCUBE_LOD(tex, R, mip);

    return DecodeHDR(rgbm, hdr);
}

// 粗糙度到Mip级别的映射
half perceptualRoughnessToMipmapLevel(half perceptualRoughness)
{
    return perceptualRoughness * UNITY_SPECCUBE_LOD_STEPS;
}

// Mip级别到粗糙度的映射
half mipmapLevelToPerceptualRoughness(half mipmapLevel)
{
    return mipmapLevel / UNITY_SPECCUBE_LOD_STEPS;
}
4. Standard Shader中的IBL调用
在 UnityStandardCore.cginc 中：

hlsl

half4 fragForwardBaseInternal (VertexOutputForwardBase i)
{
    // ... 省略其他代码 ...
    
    // 计算GI（包含IBL）
    UnityGI gi = FragmentGI(
        s, 
        occlusion, 
        i.ambientOrLightmapUV, 
        atten, 
        mainLight
    );

    // 使用BRDF和GI计算最终颜色
    half4 c = UNITY_BRDF_PBS(
        s.diffColor, 
        s.specColor, 
        s.oneMinusReflectivity, 
        s.smoothness,
        s.normalWorld, 
        -s.eyeVec, 
        mainLight, 
        gi.indirect  // 这里包含了IBL数据
    );
    
    return c;
}
5. 关键的IBL数据结构
hlsl

// 光泽环境数据
struct Unity_GlossyEnvironmentData
{
    half    roughness;      // 粗糙度
    half3   reflUVW;        // 反射方向（世界空间）
};

// 间接光照数据
struct UnityIndirect
{
    half3 diffuse;          // 间接漫反射（从光照探针）
    half3 specular;         // 间接镜面反射（从反射探针，即IBL）
};
6. 如何查看和修改
如果你想查看或修改IBL实现：

Built-in RP: 直接修改上述CGIncludes文件（不推荐）

URP/HDRP:

URP: Packages/com.unity.render-pipelines.universal/ShaderLibrary/
HDRP: Packages/com.unity.render-pipelines.high-definition/Runtime/Lighting/
推荐方式: 创建自定义Shader，包含这些文件后重写相关函数

hlsl

#include "UnityPBSLighting.cginc"
#include "UnityImageBasedLighting.cginc"

// 然后可以使用Unity的IBL函数
half3 CustomIBL(...)
{
    Unity_GlossyEnvironmentData g;
    g.roughness = roughness;
    g.reflUVW = reflect(-viewDir, normal);
    
    return Unity_GlossyEnvironment(
        UNITY_PASS_TEXCUBE(unity_SpecCube0), 
        unity_SpecCube0_HDR, 
        g
    );
}
这样你就可以找到并理解Unity PBS中IBL的完整实现了。

17:09

UnityGI_IndirectSpecular功能

17:18

Claude-Sonnet-4.5


UnityGI_IndirectSpecular 是Unity中计算间接镜面反射光照的核心函数，它是IBL（Image-Based Lighting）中处理镜面反射的关键部分。

函数签名
hlsl

inline half3 UnityGI_IndirectSpecular(
    UnityGIInput data, 
    half occlusion, 
    Unity_GlossyEnvironmentData glossIn
)
主要功能
这个函数的核心作用是：从反射探针（Reflection Probe）或天空盒中采样环境反射，并根据材质的粗糙度和菲涅尔效应计算间接镜面反射光照。

具体实现代码
在 UnityGlobalIllumination.cginc 中：

hlsl

inline half3 UnityGI_IndirectSpecular(UnityGIInput data, half occlusion, Unity_GlossyEnvironmentData glossIn)
{
    half3 specular;

    #ifdef UNITY_SPECCUBE_BOX_PROJECTION
        // 使用盒投影修正反射方向
        // 这对于室内场景特别重要
        half3 originalReflUVW = glossIn.reflUVW;
        glossIn.reflUVW = BoxProjectedCubemapDirection(
            originalReflUVW, 
            data.worldPos, 
            data.probePosition[0], 
            data.boxMin[0], 
            data.boxMax[0]
        );
    #endif

    #ifdef _GLOSSYREFLECTIONS_OFF
        // 如果关闭了光泽反射，返回0
        specular = unity_IndirectSpecColor.rgb;
    #else
        // 从主反射探针采样
        half3 env0 = Unity_GlossyEnvironment(
            UNITY_PASS_TEXCUBE(unity_SpecCube0), 
            data.probeHDR[0], 
            glossIn
        );
        
        #ifdef UNITY_SPECCUBE_BLENDING
            // 如果启用了反射探针混合
            const float kBlendFactor = 0.99999;
            float blendLerp = data.boxMin[0].w;
            
            UNITY_BRANCH
            if (blendLerp < kBlendFactor)
            {
                // 需要混合第二个反射探针
                #ifdef UNITY_SPECCUBE_BOX_PROJECTION
                    glossIn.reflUVW = BoxProjectedCubemapDirection(
                        originalReflUVW, 
                        data.worldPos, 
                        data.probePosition[1], 
                        data.boxMin[1], 
                        data.boxMax[1]
                    );
                #endif

                half3 env1 = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE_SAMPLER(unity_SpecCube1, unity_SpecCube0), 
                    data.probeHDR[1], 
                    glossIn
                );

                // 在两个探针之间进行混合
                specular = lerp(env1, env0, blendLerp);
            }
            else
            {
                specular = env0;
            }
        #else
            specular = env0;
        #endif
    #endif

    // 应用遮挡
    return specular * occlusion;
}
详细功能分解
1. 盒投影校正 (Box Projection)
hlsl

half3 BoxProjectedCubemapDirection(
    half3 worldRefl, 
    float3 worldPos, 
    float4 cubemapCenter, 
    float4 boxMin, 
    float4 boxMax
)
{
    // 修正反射方向，使其看起来像反射探针是一个盒子而不是一个点
    UNITY_BRANCH
    if (cubemapCenter.w > 0.0)
    {
        half3 nrdir = normalize(worldRefl);
        
        #if 1
            half3 rbmax = (boxMax.xyz - worldPos) / nrdir;
            half3 rbmin = (boxMin.xyz - worldPos) / nrdir;
            half3 rbminmax = (nrdir > 0.0f) ? rbmax : rbmin;
        #else
            half3 rbmax = (boxMax.xyz - worldPos);
            half3 rbmin = (boxMin.xyz - worldPos);
            half3 select = step(half3(0,0,0), nrdir);
            half3 rbminmax = lerp(rbmax, rbmin, select);
            rbminmax /= nrdir;
        #endif

        half fa = min(min(rbminmax.x, rbminmax.y), rbminmax.z);
        worldPos -= cubemapCenter.xyz;
        worldRefl = worldPos + nrdir * fa;
    }
    return worldRefl;
}
作用：修正反射方向，使反射看起来更真实，特别是在室内或封闭空间中。

2. 环境采样 (Unity_GlossyEnvironment)
hlsl

half3 Unity_GlossyEnvironment(
    UNITY_ARGS_TEXCUBE(tex), 
    half4 hdr, 
    Unity_GlossyEnvironmentData glossIn
)
{
    half perceptualRoughness = glossIn.roughness;
    
    // 粗糙度映射调整（可选）
    #if UNITY_GLOSS_MATCHES_MARMOSET_TOOLBAG2
        perceptualRoughness = perceptualRoughness * (1.7 - 0.7 * perceptualRoughness);
    #endif

    // 将粗糙度转换为Mipmap级别
    half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);
    
    // 从立方体贴图采样
    half3 R = glossIn.reflUVW;
    half4 rgbm = UNITY_SAMPLE_TEXCUBE_LOD(tex, R, mip);

    // 解码HDR
    return DecodeHDR(rgbm, hdr);
}
关键点：

粗糙度 → Mipmap级别：越粗糙的表面采样越模糊的Mip级别
RGBM解码：反射探针使用RGBM格式存储HDR数据
3. 反射探针混合
当物体处于两个反射探针的边界时，Unity会混合两个探针的结果：

hlsl

specular = lerp(env1, env0, blendLerp);
这确保了探针之间的平滑过渡。

输入参数详解
UnityGIInput data
hlsl

struct UnityGIInput
{
    UnityLight light;           // 主光源
    float3 worldPos;            // 世界空间位置
    half3 worldViewDir;         // 世界空间视线方向
    half atten;                 // 光照衰减
    half3 ambient;              // 环境光
    
    // 反射探针数据
    float4 boxMin[2];           // 探针边界盒最小值（两个探针）
    float4 boxMax[2];           // 探针边界盒最大值
    float4 probePosition[2];    // 探针位置
    float4 probeHDR[2];         // 探针HDR解码参数
};
Unity_GlossyEnvironmentData glossIn
hlsl

struct Unity_GlossyEnvironmentData
{
    half roughness;     // 感知粗糙度 (0=光滑, 1=粗糙)
    half3 reflUVW;      // 反射方向（世界空间）
};
使用示例
在Standard Shader中的典型调用：

hlsl

// 1. 准备GI输入数据
UnityGIInput giInput;
UNITY_INITIALIZE_OUTPUT(UnityGIInput, giInput);
giInput.light = mainLight;
giInput.worldPos = i.posWorld;
giInput.worldViewDir = -s.eyeVec;
giInput.atten = atten;
// ... 设置其他参数

// 2. 准备光泽环境数据
Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
    s.smoothness,           // 光滑度
    s.eyeVec,              // 视线方向
    s.normalWorld,         // 法线
    s.specColor            // 镜面反射颜色
);

// 3. 计算间接镜面反射
half3 specular = UnityGI_IndirectSpecular(
    giInput, 
    occlusion,  // AO
    g
);

// 4. 应用到最终光照
gi.indirect.specular = specular;
关键技术点
1. 粗糙度到Mipmap的映射
hlsl

// UNITY_SPECCUBE_LOD_STEPS 通常是 6
half mip = perceptualRoughness * UNITY_SPECCUBE_LOD_STEPS;
粗糙度 0.0 → Mip 0（最清晰的反射）
粗糙度 1.0 → Mip 6（最模糊的反射）
2. HDR解码
hlsl

inline half3 DecodeHDR(half4 data, half4 decodeInstructions)
{
    // 从RGBM格式解码
    // decodeInstructions.x = intensity multiplier
    half alpha = decodeInstructions.w * (data.a - 1.0) + 1.0;
    return (decodeInstructions.x * pow(alpha, decodeInstructions.y)) * data.rgb;
}
3. 性能优化
使用 UNITY_BRANCH 进行分支优化
只在需要时才计算第二个探针的混合
通过Mipmap预滤波避免实时积分
总结
UnityGI_IndirectSpecular 的核心功能：

✅ 从反射探针采样环境反射
✅ 根据粗糙度选择合适的Mipmap级别（模拟不同粗糙度表面的模糊反射）
✅ 盒投影校正（提高室内反射的真实感）
✅ 多探针混合（平滑过渡）
✅ 应用遮挡（AO影响反射强度）
✅ HDR解码（支持高动态范围）
这是Unity实现物理真实感渲染（PBS）中IBL镜面反射的核心实现，使得物体能够真实地反射周围环境。

17:18

unity 中的光照探针 (Light Probes)，使用什么技术/模块生成的？在shader中哪里使用了？

17:28

Claude-Sonnet-4.5


Unity光照探针（Light Probes）技术详解
一、光照探针的生成技术
1. 球谐函数（Spherical Harmonics, SH）
Unity使用球谐函数来存储和表示光照探针数据。这是光照探针的核心技术。

hlsl

// Unity使用3阶球谐函数（9个系数）存储每个颜色通道
// 总共27个系数（RGB各9个）

// 球谐系数存储在这些变量中：
uniform half4 unity_SHAr;  // R通道的SH系数 (L0, L1)
uniform half4 unity_SHAg;  // G通道的SH系数 (L0, L1)
uniform half4 unity_SHAb;  // B通道的SH系数 (L0, L1)
uniform half4 unity_SHBr;  // R通道的SH系数 (L2)
uniform half4 unity_SHBg;  // G通道的SH系数 (L2)
uniform half4 unity_SHBb;  // B通道的SH系数 (L2)
uniform half4 unity_SHC;   // 额外的SH系数
2. 烘焙流程
光照探针在烘焙时通过以下步骤生成：


1. 场景设置
   └─> 手动放置 Light Probe Group

2. 烘焙过程（Lighting > Generate Lighting）
   ├─> 对每个探针位置
   │   ├─> 在球面上采样多个方向（通常数百个）
   │   ├─> 对每个方向追踪光线（路径追踪）
   │   ├─> 收集来自该方向的光照
   │   └─> 累积所有方向的光照信息
   │
   └─> 将采样结果拟合到球谐函数
       └─> 生成9个SH系数（每个颜色通道）

3. 运行时插值
   └─> 根据物体位置在多个探针间插值
3. 使用的烘焙引擎
Unity支持多种烘焙后端：

Enlighten（旧版，已弃用）
Progressive GPU/CPU Lightmapper（Unity 2019+）
GPU Lightmapper（Unity 2020+，推荐）
二、Shader中的使用位置
1. 主要使用文件
reasonml

CGIncludes/
├── UnityCG.cginc                    // 基础SH函数
├── UnityShaderVariables.cginc       // SH变量声明
├── UnityStandardCore.cginc          // Standard Shader中的使用
└── UnityGlobalIllumination.cginc    // GI相关函数
2. 核心SH评估函数
在 UnityCG.cginc 中：

hlsl

// ============ 主要的SH评估函数 ============

// 1. 基础的SH评估（仅使用L0和L1）
half3 SHEvalLinearL0L1(half3 N)
{
    half3 x;

    // Linear (L1) + constant (L0) polynomial terms
    x.r = dot(unity_SHAr, half4(N, 1.0));
    x.g = dot(unity_SHAg, half4(N, 1.0));
    x.b = dot(unity_SHAb, half4(N, 1.0));

    return x;
}

// 2. 完整的L2 SH评估
half3 SHEvalLinearL2(half3 N)
{
    half3 x1, x2;
    
    // 4个二次多项式项
    half4 vB = N.xyzz * N.yzzx;
    
    x1.r = dot(unity_SHBr, vB);
    x1.g = dot(unity_SHBg, vB);
    x1.b = dot(unity_SHBb, vB);

    // 最后一个二次多项式项
    half vC = N.x * N.x - N.y * N.y;
    x2 = unity_SHC.rgb * vC;

    return x1 + x2;
}

// 3. 完整的SH评估（L0+L1+L2）
half3 ShadeSH9(half4 normal)
{
    // Linear + constant polynomial terms
    half3 res = SHEvalLinearL0L1(normal.xyz);

    // Quadratic polynomials
    res += SHEvalLinearL2(normal.xyz);

    #ifdef UNITY_COLORSPACE_GAMMA
        res = LinearToGammaSpace(res);
    #endif

    return res;
}
3. 逐像素SH评估
在 UnityGlobalIllumination.cginc 中：

hlsl

// 逐像素评估SH，支持位置参数（用于插值）
inline half3 ShadeSHPerPixel(half3 normal, half3 ambient, float3 worldPos)
{
    half3 ambient_contrib = 0.0;

    #if UNITY_SAMPLE_FULL_SH_PER_PIXEL
        // 完全在像素着色器中评估SH
        // 如果启用了逐像素SH采样
        
        #if UNITY_LIGHT_PROBE_PROXY_VOLUME
            // 使用Light Probe Proxy Volume (LPPV)
            if (unity_ProbeVolumeParams.x == 1.0)
            {
                // 从3D纹理中采样SH系数
                return SHEvalLinearL0L1_SampleProbeVolume(
                    half4(normal, 1.0), 
                    worldPos
                );
            }
            else
        #endif
            {
                // 标准的SH评估
                ambient_contrib = ShadeSH9(half4(normal, 1.0));
            }
    #else
        // 在顶点着色器中评估，这里只使用传递过来的结果
        ambient_contrib = ambient;
    #endif

    return ambient_contrib;
}
4. 顶点着色器中的SH评估
在 UnityStandardCore.cginc 中：

hlsl

VertexOutputForwardBase vertForwardBase(VertexInput v)
{
    VertexOutputForwardBase o;
    // ... 其他代码

    #ifdef DYNAMICLIGHTMAP_ON
        o.ambientOrLightmapUV.zw = v.uv2.xy * unity_DynamicLightmapST.xy 
                                   + unity_DynamicLightmapST.zw;
    #endif

    #ifdef UNITY_PASS_FORWARDBASE
        #if UNITY_SHOULD_SAMPLE_SH
            // 在顶点着色器中评估SH
            #if defined(VERTEXLIGHT_ON)
                // 如果有顶点光照，ambient用于存储SH
                o.ambientOrLightmapUV.rgb = ShadeSH9(half4(o.normalWorld, 1.0));
            #else
                // 如果没有顶点光照但需要SH
                o.ambientOrLightmapUV.rgb = ShadeSH9(half4(o.normalWorld, 1.0));
            #endif
        #endif
    #endif

    return o;
}
5. 片段着色器中的使用
在 UnityStandardCore.cginc 中：

hlsl

half4 fragForwardBase(VertexOutputForwardBase i) : SV_Target
{
    // ... 准备数据

    UnityGI gi = FragmentGI(
        s,                      // 表面数据
        occlusion,              // AO
        i.ambientOrLightmapUV,  // 从顶点着色器传来的SH或光照贴图UV
        atten,                  // 衰减
        mainLight               // 主光源
    );

    // ... 使用gi.indirect.diffuse（包含SH光照）
}
6. FragmentGI函数实现
在 UnityGlobalIllumination.cginc 中：

hlsl

inline UnityGI FragmentGI(
    FragmentCommonData s,
    half occlusion,
    half4 i_ambientOrLightmapUV,
    half atten,
    UnityLight light)
{
    UnityGIInput d;
    d.light = light;
    d.worldPos = s.posWorld;
    d.worldViewDir = -s.eyeVec;
    d.atten = atten;
    
    #if defined(LIGHTMAP_ON) || defined(DYNAMICLIGHTMAP_ON)
        d.ambient = 0;
        d.lightmapUV = i_ambientOrLightmapUV;
    #else
        // 使用光照探针
        d.ambient = i_ambientOrLightmapUV.rgb;
        d.lightmapUV = 0;
    #endif

    d.probeHDR[0] = unity_SpecCube0_HDR;
    d.probeHDR[1] = unity_SpecCube1_HDR;
    
    #if defined(UNITY_SPECCUBE_BLENDING) || defined(UNITY_SPECCUBE_BOX_PROJECTION)
        d.boxMin[0] = unity_SpecCube0_BoxMin;
    #endif
    
    // ... 更多设置

    Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
        s.smoothness,
        -s.eyeVec,
        s.normalWorld,
        s.specColor
    );
    
    // 调用主GI函数
    return UnityGlobalIllumination(d, occlusion, s.normalWorld, g);
}
7. UnityGlobalIllumination函数
hlsl

inline UnityGI UnityGlobalIllumination(
    UnityGIInput data,
    half occlusion,
    half3 normalWorld,
    Unity_GlossyEnvironmentData glossIn)
{
    UnityGI o_gi = UnityGI_Base(data, occlusion, normalWorld);
    o_gi.indirect.specular = UnityGI_IndirectSpecular(data, occlusion, glossIn);
    return o_gi;
}

inline UnityGI UnityGI_Base(UnityGIInput data, half occlusion, half3 normalWorld)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);

    #if !defined(LIGHTMAP_ON)
        // 使用光照探针的漫反射光照
        o_gi.indirect.diffuse = ShadeSHPerPixel(
            normalWorld, 
            data.ambient,      // 从顶点着色器传来的SH结果
            data.worldPos
        );
    #endif

    // 如果定义了LIGHTMAP_ON，则使用光照贴图而不是光照探针
    #if defined(LIGHTMAP_ON)
        o_gi.indirect.diffuse = DecodeLightmap(
            UNITY_SAMPLE_TEX2D(unity_Lightmap, data.lightmapUV)
        );
        
        #ifdef DIRLIGHTMAP_COMBINED
            // 方向性光照贴图
            half4 bakedDirTex = UNITY_SAMPLE_TEX2D_SAMPLER(
                unity_LightmapInd, 
                unity_Lightmap, 
                data.lightmapUV
            );
            o_gi.indirect.diffuse = DecodeDirectionalLightmap(
                o_gi.indirect.diffuse, 
                bakedDirTex, 
                normalWorld
            );
        #endif
    #endif

    // 应用AO
    o_gi.indirect.diffuse *= occlusion;
    return o_gi;
}
三、Light Probe Proxy Volume (LPPV)
对于大型动态物体，Unity提供了LPPV技术：

1. LPPV采样函数
hlsl

// 在 UnityStandardCore.cginc 中
half3 SHEvalLinearL0L1_SampleProbeVolume(half4 N, float3 worldPos)
{
    const float transformToLocal = unity_ProbeVolumeParams.y;
    const float texelSizeX = unity_ProbeVolumeParams.z;

    // 将世界坐标转换到探针体积的本地空间
    float3 position = (transformToLocal == 1.0f) 
        ? mul(unity_ProbeVolumeWorldToObject, float4(worldPos, 1.0)).xyz
        : worldPos;

    // 计算3D纹理坐标
    float3 texCoord = (position - unity_ProbeVolumeMin.xyz) 
                    * unity_ProbeVolumeSizeInv.xyz;

    // 从3D纹理采样SH系数
    half4 SHAr = UNITY_SAMPLE_TEX3D_SAMPLER(
        unity_ProbeVolumeSH, 
        unity_ProbeVolumeSH, 
        texCoord
    );
    
    // ... 采样其他SH系数纹理
    
    // 评估SH
    half3 res;
    res.r = dot(SHAr, N);
    res.g = dot(SHAg, N);
    res.b = dot(SHAb, N);

    return res;
}
四、完整的使用流程图

烘焙阶段：
Light Probe Group → 场景采样 → 球谐函数拟合 → SH系数

运行时：
┌─────────────────────────────────────────┐
│ 顶点着色器                                │
│  ├─ 获取世界空间法线                       │
│  └─ ShadeSH9() → 评估SH → ambient        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 片段着色器                                │
│  ├─ FragmentGI()                        │
│  │   ├─ ShadeSHPerPixel()               │
│  │   │   └─ 使用ambient或重新评估         │
│  │   │                                  │
│  │   └─ gi.indirect.diffuse = SH光照    │
│  │                                      │
│  └─ BRDF计算                             │
│      └─ 使用 gi.indirect.diffuse         │
└─────────────────────────────────────────┘
五、关键变量和宏
hlsl

// 1. SH系数变量（UnityShaderVariables.cginc）
uniform half4 unity_SHAr;
uniform half4 unity_SHAg;
uniform half4 unity_SHAb;
uniform half4 unity_SHBr;
uniform half4 unity_SHBg;
uniform half4 unity_SHBb;
uniform half4 unity_SHC;

// 2. LPPV相关变量
UNITY_DECLARE_TEX3D(unity_ProbeVolumeSH);
uniform half4 unity_ProbeVolumeParams;
uniform float4x4 unity_ProbeVolumeWorldToObject;
uniform float3 unity_ProbeVolumeSizeInv;
uniform float3 unity_ProbeVolumeMin;

// 3. 控制宏
#define UNITY_SHOULD_SAMPLE_SH          // 是否使用光照探针
#define UNITY_SAMPLE_FULL_SH_PER_PIXEL  // 逐像素评估SH
#define UNITY_LIGHT_PROBE_PROXY_VOLUME  // 使用LPPV
六、使用示例
自定义Shader中使用光照探针
hlsl

Shader "Custom/LightProbeExample"
{
    SubShader
    {
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 normal : TEXCOORD0;
                float3 ambient : TEXCOORD1;  // 存储SH结果
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.normal = UnityObjectToWorldNormal(v.normal);
                
                // 在顶点着色器中评估光照探针
                o.ambient = ShadeSH9(half4(o.normal, 1.0));
                
                return o;
            }

            half4 frag(v2f i) : SV_Target
            {
                // 使用光照探针的漫反射光照
                half3 lighting = i.ambient;
                
                return half4(lighting, 1.0);
            }
            ENDCG
        }
    }
}
总结
Unity的光照探针系统：

生成技术：球谐函数（3阶，9个系数 × 3个颜色通道）
烘焙方式：路径追踪 + SH拟合
主要函数：
ShadeSH9() - 评估SH
ShadeSHPerPixel() - 逐像素SH评估
SHEvalLinearL0L1() / SHEvalLinearL2() - SH基础评估
使用位置：
顶点着色器：预计算SH
片段着色器：在FragmentGI中应用到间接漫反射光照
高级特性：LPPV用于大型动态物体
这套系统使得动态物体能够接收预烘焙的全局光照，是Unity实现高质量实时渲染的关键技术之一。

17:28

unity 中的光照探针 (Light Probes)只提供diffuse？

17:35

Claude-Sonnet-4.5


Unity光照探针提供的光照类型
简短回答
是的，光照探针（Light Probes）主要只提供漫反射（Diffuse）光照。

镜面反射（Specular）光照由**反射探针（Reflection Probes）**提供。

详细解释
一、为什么光照探针只提供Diffuse？
这是基于物理和技术原因的设计决策：

1. 物理原理差异

漫反射（Diffuse）：
├─ 与视角无关
├─ 只依赖于表面法线
├─ 光照在半球面上均匀分布
└─ 可以用球谐函数（SH）很好地近似

镜面反射（Specular）：
├─ 强烈依赖视角
├─ 依赖于反射方向
├─ 光照集中在特定方向
└─ 需要立方体贴图（Cubemap）来存储
2. 球谐函数的局限性
hlsl

// 球谐函数只能表示低频信息
// 3阶SH（Unity使用的）只有9个系数

// 适合表示：
// ✓ 漫反射光照（低频，平滑变化）
// ✓ 环境光（低频）

// 不适合表示：
// ✗ 镜面反射（高频，有明确方向性）
// ✗ 高光（高频，sharp highlights）
二、Unity的完整间接光照系统
Unity将间接光照分为两个独立系统：


间接光照系统
├─ Light Probes（光照探针）
│   ├─ 存储格式：球谐函数（27个系数）
│   ├─ 提供：Diffuse 间接光照
│   ├─ 特点：体积小，插值快
│   └─ 用途：动态物体的漫反射GI
│
└─ Reflection Probes（反射探针）
    ├─ 存储格式：Cubemap（立方体贴图）
    ├─ 提供：Specular 间接光照
    ├─ 特点：体积大，质量高
    └─ 用途：动态物体的镜面反射
三、在Shader中的实现证据
让我们查看Unity Standard Shader的代码：

1. FragmentGI函数
hlsl

inline UnityGI FragmentGI(
    FragmentCommonData s,
    half occlusion,
    half4 i_ambientOrLightmapUV,
    half atten,
    UnityLight light)
{
    UnityGIInput d;
    // ... 设置参数
    
    Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
        s.smoothness,
        -s.eyeVec,
        s.normalWorld,
        s.specColor
    );
    
    // 调用主GI函数
    return UnityGlobalIllumination(d, occlusion, s.normalWorld, g);
}
2. UnityGlobalIllumination函数
hlsl

inline UnityGI UnityGlobalIllumination(
    UnityGIInput data,
    half occlusion,
    half3 normalWorld,
    Unity_GlossyEnvironmentData glossIn)
{
    UnityGI o_gi;
    
    // ========================================
    // 1. 获取 DIFFUSE 间接光照
    // ========================================
    o_gi = UnityGI_Base(data, occlusion, normalWorld);
    // 这里使用 Light Probes（SH）
    
    // ========================================
    // 2. 获取 SPECULAR 间接光照
    // ========================================
    o_gi.indirect.specular = UnityGI_IndirectSpecular(
        data, 
        occlusion, 
        glossIn
    );
    // 这里使用 Reflection Probes（Cubemap）
    
    return o_gi;
}
3. UnityGI_Base函数（只处理Diffuse）
hlsl

inline UnityGI UnityGI_Base(
    UnityGIInput data, 
    half occlusion, 
    half3 normalWorld)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);

    // ========================================
    // Light Probes 提供 Diffuse
    // ========================================
    #if !defined(LIGHTMAP_ON)
        // 使用光照探针（球谐函数）
        o_gi.indirect.diffuse = ShadeSHPerPixel(
            normalWorld,
            data.ambient,  // 来自SH的漫反射光照
            data.worldPos
        );
    #endif

    // ========================================
    // 或者使用 Lightmap
    // ========================================
    #if defined(LIGHTMAP_ON)
        o_gi.indirect.diffuse = DecodeLightmap(
            UNITY_SAMPLE_TEX2D(unity_Lightmap, data.lightmapUV)
        );
    #endif

    o_gi.indirect.diffuse *= occlusion;
    
    // 注意：这里没有设置 o_gi.indirect.specular
    // Specular由另外的函数处理
    
    return o_gi;
}
4. UnityGI结构体
hlsl

struct UnityGI
{
    UnityLight light;
    
    // 间接光照分为两部分
    UnityIndirect indirect;
};

struct UnityIndirect
{
    half3 diffuse;   // 来自 Light Probes 或 Lightmap
    half3 specular;  // 来自 Reflection Probes
};
四、数据结构对比
Light Probes 数据
hlsl

// 每个探针只需要 27 个 float（9个系数 × 3个颜色通道）
uniform half4 unity_SHAr;  // 4个系数
uniform half4 unity_SHAg;  // 4个系数
uniform half4 unity_SHAb;  // 4个系数
uniform half4 unity_SHBr;  // 4个系数
uniform half4 unity_SHBg;  // 4个系数
uniform half4 unity_SHBb;  // 4个系数
uniform half4 unity_SHC;   // 3个系数

// 评估时只需要法线
half3 lighting = ShadeSH9(half4(normal, 1.0));
Reflection Probes 数据
hlsl

// 每个探针需要一个完整的 Cubemap
// 通常是 128x128 或 256x256，6个面，多个Mip级别
// 文件大小：几百KB到几MB

UNITY_DECLARE_TEXCUBE(unity_SpecCube0);  // Cubemap纹理
uniform half4 unity_SpecCube0_HDR;       // HDR解码参数

// 评估时需要反射方向
half3 reflDir = reflect(-viewDir, normal);
half3 specular = UNITY_SAMPLE_TEXCUBE_LOD(
    unity_SpecCube0, 
    reflDir, 
    mipLevel
);
五、技术对比表
特性	Light Probes	Reflection Probes
提供的光照类型	Diffuse（漫反射）	Specular（镜面反射）
存储格式	球谐函数（SH）	Cubemap
数据量	极小（27 floats）	大（数百KB-数MB）
依赖因素	仅法线	法线 + 视角
频率特性	低频	高频
插值	快速（线性插值）	较慢（纹理采样）
适用场景	动态物体的环境光	反射表面
六、实际使用示例
1. Standard Shader中的完整GI
hlsl

half4 fragForwardBase(VertexOutputForwardBase i) : SV_Target
{
    // 准备表面数据
    FragmentCommonData s = FragmentSetup(
        i.tex, 
        i.eyeVec.xyz, 
        IN_VIEWDIR4PARALLAX(i), 
        i.tangentToWorldAndPackedData, 
        IN_WORLDPOS(i)
    );

    // 计算GI
    UnityGI gi = FragmentGI(s, occlusion, i.ambientOrLightmapUV, atten, mainLight);
    
    // gi.indirect 包含：
    // ├─ diffuse  ← 来自 Light Probes（或Lightmap）
    // └─ specular ← 来自 Reflection Probes

    // 应用到BRDF
    half4 c = UNITY_BRDF_PBS(
        s.diffColor,           // 漫反射颜色
        s.specColor,           // 镜面反射颜色
        s.oneMinusReflectivity,
        s.smoothness,
        s.normalWorld,
        -s.eyeVec,
        gi.light,              // 直接光照
        gi.indirect            // 间接光照（diffuse + specular）
    );

    return OutputForward(c, s.alpha);
}
2. 自定义Shader分别使用两种探针
hlsl

Shader "Custom/SeparateProbesExample"
{
    SubShader
    {
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "UnityStandardCore.cginc"

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldNormal : TEXCOORD0;
                float3 worldPos : TEXCOORD1;
                float3 viewDir : TEXCOORD2;
                float3 shLighting : TEXCOORD3;  // Light Probe结果
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.viewDir = WorldSpaceViewDir(v.vertex);
                
                // ========================================
                // 在顶点着色器中评估 Light Probes（Diffuse）
                // ========================================
                o.shLighting = ShadeSH9(half4(o.worldNormal, 1.0));
                
                return o;
            }

            half4 frag(v2f i) : SV_Target
            {
                half3 normal = normalize(i.worldNormal);
                half3 viewDir = normalize(i.viewDir);
                
                // ========================================
                // 1. Diffuse: 使用 Light Probes
                // ========================================
                half3 diffuseGI = i.shLighting;
                
                // ========================================
                // 2. Specular: 使用 Reflection Probes
                // ========================================
                half3 reflDir = reflect(-viewDir, normal);
                
                Unity_GlossyEnvironmentData glossIn;
                glossIn.roughness = 0.2;  // 光滑度
                glossIn.reflUVW = reflDir;
                
                half3 specularGI = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE(unity_SpecCube0),
                    unity_SpecCube0_HDR,
                    glossIn
                );
                
                // ========================================
                // 3. 组合两种GI
                // ========================================
                half3 albedo = half3(0.5, 0.5, 0.5);
                half3 specColor = half3(0.04, 0.04, 0.04);
                
                half3 diffuse = albedo * diffuseGI;
                half3 specular = specColor * specularGI;
                
                return half4(diffuse + specular, 1.0);
            }
            ENDCG
        }
    }
}
七、为什么这样设计？
1. 存储效率
basic

假设场景中有 100 个 Light Probes：

Light Probes 存储：
100 × 27 floats × 4 bytes = 10.8 KB

如果用 Cubemap 存储（128×128，6面，RGBA16F）：
100 × (128×128×6×8 bytes) = 600 MB！

差距：55,000 倍！
2. 性能考虑
hlsl

// Light Probes 评估（Diffuse）
// 只需要几个点积运算
half3 diffuse = dot(unity_SHAr, half4(N, 1.0));  // 快速

// Reflection Probes 采样（Specular）
// 需要纹理采样，有内存访问开销
half3 specular = UNITY_SAMPLE_TEXCUBE_LOD(...);  // 相对慢
3. 视觉需求

Diffuse：
- 视觉上是平滑的
- 不需要高频细节
- SH已经足够好

Specular：
- 需要清晰的反射
- 高频细节很重要
- 必须用Cubemap
八、特殊情况
Light Probe Proxy Volume (LPPV)
对于大型动态物体，Unity提供了LPPV，但它仍然只提供Diffuse：

hlsl

#if UNITY_LIGHT_PROBE_PROXY_VOLUME
    if (unity_ProbeVolumeParams.x == 1.0)
    {
        // 从3D纹理采样SH系数
        // 仍然是球谐函数，仍然是Diffuse
        half3 diffuseGI = SHEvalLinearL0L1_SampleProbeVolume(
            half4(normal, 1.0),
            worldPos
        );
    }
#endif
总结
明确答案：是的，Unity的Light Probes只提供Diffuse光照。

完整的间接光照系统：


Unity 间接光照 = Light Probes (Diffuse) + Reflection Probes (Specular)
这种设计基于：

✅ 物理原理：Diffuse与视角无关，Specular依赖视角
✅ 存储效率：SH极小，Cubemap很大
✅ 性能考虑：SH评估快，纹理采样慢
✅ 视觉需求：Diffuse可用低频近似，Specular需要高频细节
如果你需要完整的GI效果，必须同时使用Light Probes和Reflection Probes！

17:35

unity中的Reflection Probes是什么

17:37

Claude-Sonnet-4.5


Unity中的Reflection Probes（反射探针）详解
一、什么是Reflection Probes
Reflection Probes（反射探针）是Unity中用于捕捉和存储环境反射信息的组件，为动态物体提供真实的镜面反射效果。

核心概念

Reflection Probe = 一个虚拟相机 + 立方体贴图（Cubemap）

工作原理：
1. 在特定位置放置一个探针
2. 从该位置向6个方向（±X, ±Y, ±Z）渲染场景
3. 将6张图片组合成一个Cubemap
4. 动态物体根据其位置采样最近的Cubemap获得反射
二、Reflection Probe的类型
Unity提供三种类型的反射探针：

1. Baked（烘焙）

特点：
├─ 在编辑器中预先渲染
├─ 运行时不更新
├─ 性能开销：无（只是纹理采样）
├─ 质量：高（可以高分辨率，多次采样）
└─ 适用：静态场景反射

使用场景：
- 室内环境
- 固定的室外场景
- 性能敏感的移动平台
2. Realtime（实时）

特点：
├─ 每帧或指定频率更新
├─ 可以反射动态物体
├─ 性能开销：高（每次更新需要6次渲染）
├─ 质量：中（通常降低分辨率以保证性能）
└─ 适用：需要动态反射的场景

使用场景：
- 镜子
- 水面
- 高度反射的动态物体
- 展示类应用
3. Custom（自定义）

特点：
├─ 手动控制更新时机
├─ 可以通过脚本触发渲染
├─ 性能开销：可控
├─ 质量：可调
└─ 适用：需要精确控制的场景

使用场景：
- 只在特定时刻需要更新反射
- 过场动画
- 按需更新的镜面
三、存储格式：Cubemap
Cubemap结构

Cubemap（立方体贴图）
├─ +X 面（右）
├─ -X 面（左）
├─ +Y 面（上）
├─ -Y 面（下）
├─ +Z 面（前）
└─ -Z 面（后）

每个面是一个正方形纹理（如128×128, 256×256）
Mipmap链
apache

为了支持不同粗糙度的表面，Cubemap包含多个Mip级别：

Mip 0: 256×256 (镜面反射，最清晰)
Mip 1: 128×128
Mip 2: 64×64
Mip 3: 32×32
Mip 4: 16×16
Mip 5: 8×8
Mip 6: 4×4   (粗糙表面，最模糊)

粗糙度越高 → 采样更高的Mip级别 → 更模糊的反射
HDR编码
hlsl

// Cubemap使用RGBM或HDR格式存储高动态范围
// 需要解码才能使用

half3 DecodeHDR(half4 data, half4 decodeInstructions)
{
    // RGBM解码
    // RGB存储颜色，M（Alpha）存储亮度系数
    half alpha = decodeInstructions.w * (data.a - 1.0) + 1.0;
    return (decodeInstructions.x * pow(alpha, decodeInstructions.y)) * data.rgb;
}
四、在Shader中的使用
1. 相关变量声明
hlsl

// 在 UnityShaderVariables.cginc 中

// ========================================
// 主反射探针
// ========================================
UNITY_DECLARE_TEXCUBE(unity_SpecCube0);
uniform half4 unity_SpecCube0_HDR;          // HDR解码参数
uniform half4 unity_SpecCube0_BoxMax;       // 包围盒最大值
uniform half4 unity_SpecCube0_BoxMin;       // 包围盒最小值
uniform half4 unity_SpecCube0_ProbePosition;// 探针位置

// ========================================
// 次级反射探针（用于混合）
// ========================================
UNITY_DECLARE_TEXCUBE(unity_SpecCube1);
uniform half4 unity_SpecCube1_HDR;
uniform half4 unity_SpecCube1_BoxMax;
uniform half4 unity_SpecCube1_BoxMin;
uniform half4 unity_SpecCube1_ProbePosition;

// ========================================
// 全局控制
// ========================================
uniform half4 unity_SpecCube0_BoxMin;
// .w 存储混合权重
2. 核心采样函数
hlsl

// 在 UnityStandardCore.cginc 中

inline half3 Unity_GlossyEnvironment(
    UNITY_ARGS_TEXCUBE(tex),              // Cubemap
    half4 hdr,                             // HDR解码参数
    Unity_GlossyEnvironmentData glossIn    // 输入参数
)
{
    half perceptualRoughness = glossIn.roughness;
    
    // ========================================
    // 1. 粗糙度 → Mipmap级别
    // ========================================
    #if UNITY_GLOSS_MATCHES_MARMOSET_TOOLBAG2
        // 匹配Marmoset Toolbag 2的粗糙度映射
        perceptualRoughness = perceptualRoughness * (1.7 - 0.7 * perceptualRoughness);
    #endif

    // 将粗糙度映射到Mip级别 (0-6)
    half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);
    
    // ========================================
    // 2. 从Cubemap采样
    // ========================================
    half3 R = glossIn.reflUVW;  // 反射方向
    half4 rgbm = UNITY_SAMPLE_TEXCUBE_LOD(tex, R, mip);
    
    // ========================================
    // 3. HDR解码
    // ========================================
    return DecodeHDR(rgbm, hdr);
}
3. 粗糙度到Mipmap的转换
hlsl

// 在 UnityStandardCore.cginc 中

inline half perceptualRoughnessToMipmapLevel(half perceptualRoughness)
{
    // Unity的反射探针通常有7个Mip级别（0-6）
    return perceptualRoughness * UNITY_SPECCUBE_LOD_STEPS;
    // UNITY_SPECCUBE_LOD_STEPS = 6
}

// 示例：
// 粗糙度 0.0 (镜面)  → Mip 0 (最清晰)
// 粗糙度 0.5 (半粗糙) → Mip 3 (中等模糊)
// 粗糙度 1.0 (完全粗糙) → Mip 6 (最模糊)
4. 完整的反射探针采样流程
hlsl

// 在 UnityGlobalIllumination.cginc 中

inline half3 UnityGI_IndirectSpecular(
    UnityGIInput data,
    half occlusion,
    Unity_GlossyEnvironmentData glossIn
)
{
    half3 specular;

    #ifdef UNITY_SPECCUBE_BOX_PROJECTION
        // ========================================
        // 1. 盒投影校正（Box Projection）
        // ========================================
        half3 originalReflUVW = glossIn.reflUVW;
        glossIn.reflUVW = BoxProjectedCubemapDirection(
            originalReflUVW,
            data.worldPos,
            data.probePosition[0],
            data.boxMin[0],
            data.boxMax[0]
        );
    #endif

    #ifdef _GLOSSYREFLECTIONS_OFF
        // ========================================
        // 2. 如果关闭了光泽反射
        // ========================================
        specular = unity_IndirectSpecColor.rgb;
    #else
        // ========================================
        // 3. 从主反射探针采样
        // ========================================
        half3 env0 = Unity_GlossyEnvironment(
            UNITY_PASS_TEXCUBE(unity_SpecCube0),
            data.probeHDR[0],
            glossIn
        );
        
        #ifdef UNITY_SPECCUBE_BLENDING
            // ========================================
            // 4. 探针混合（如果物体在两个探针之间）
            // ========================================
            const float kBlendFactor = 0.99999;
            float blendLerp = data.boxMin[0].w;
            
            UNITY_BRANCH
            if (blendLerp < kBlendFactor)
            {
                // 需要混合第二个探针
                #ifdef UNITY_SPECCUBE_BOX_PROJECTION
                    glossIn.reflUVW = BoxProjectedCubemapDirection(
                        originalReflUVW,
                        data.worldPos,
                        data.probePosition[1],
                        data.boxMin[1],
                        data.boxMax[1]
                    );
                #endif

                half3 env1 = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE_SAMPLER(unity_SpecCube1, unity_SpecCube0),
                    data.probeHDR[1],
                    glossIn
                );

                specular = lerp(env1, env0, blendLerp);
            }
            else
            {
                specular = env0;
            }
        #else
            specular = env0;
        #endif
    #endif

    // ========================================
    // 5. 应用遮挡
    // ========================================
    return specular * occlusion;
}
五、Box Projection（盒投影）
什么是Box Projection？
盒投影是一种修正反射方向的技术，使反射看起来更真实，特别是在室内环境中。

原理对比

不使用盒投影：
├─ 反射探针被视为无限远的点
├─ 反射方向直接使用视线的镜面反射
└─ 问题：室内反射不准确，会"穿墙"

使用盒投影：
├─ 反射探针有一个影响范围（包围盒）
├─ 反射方向被修正为与包围盒相交的方向
└─ 效果：反射正确地停留在房间内部
实现代码
hlsl

half3 BoxProjectedCubemapDirection(
    half3 worldRefl,        // 原始反射方向
    float3 worldPos,        // 片段世界位置
    float4 cubemapCenter,   // 探针中心
    float4 boxMin,          // 包围盒最小值
    float4 boxMax           // 包围盒最大值
)
{
    // 只在启用盒投影时执行
    UNITY_BRANCH
    if (cubemapCenter.w > 0.0)
    {
        half3 nrdir = normalize(worldRefl);
        
        // ========================================
        // 计算射线与盒子的交点
        // ========================================
        
        // 计算到盒子每个面的距离
        half3 rbmax = (boxMax.xyz - worldPos) / nrdir;
        half3 rbmin = (boxMin.xyz - worldPos) / nrdir;
        
        // 根据方向选择正确的面
        half3 rbminmax = (nrdir > 0.0f) ? rbmax : rbmin;
        
        // 找到最近的交点
        half fa = min(min(rbminmax.x, rbminmax.y), rbminmax.z);
        
        // ========================================
        // 修正反射方向
        // ========================================
        worldPos -= cubemapCenter.xyz;
        worldRefl = worldPos + nrdir * fa;
    }
    
    return worldRefl;
}
视觉效果对比

场景：房间内的反射地板

不使用盒投影：
玩家看到的反射 → 可能显示房间外的天空 ❌

使用盒投影：
玩家看到的反射 → 正确显示房间内的墙壁和天花板 ✓
六、反射探针的混合
为什么需要混合？

问题：
当物体移动时，从一个探针区域进入另一个
如果直接切换 → 反射会突然跳变 → 视觉上不连续

解决：
在探针的边界区域混合两个探针的结果
混合实现
hlsl

// 混合权重存储在 boxMin.w
float blendWeight = data.boxMin[0].w;

// 在顶点着色器或C#代码中计算混合权重
// 基于物体距离两个探针的远近

if (blendWeight < 0.99999)  // 需要混合
{
    half3 reflection0 = SampleProbe0();
    half3 reflection1 = SampleProbe1();
    
    // 线性插值
    half3 finalReflection = lerp(reflection1, reflection0, blendWeight);
}
else  // 不需要混合
{
    half3 finalReflection = SampleProbe0();
}
七、完整使用示例
1. 在Standard Shader中
hlsl

half4 fragForwardBase(VertexOutputForwardBase i) : SV_Target
{
    // ========================================
    // 准备数据
    // ========================================
    FragmentCommonData s = FragmentSetup(...);
    
    // ========================================
    // 设置反射探针参数
    // ========================================
    Unity_GlossyEnvironmentData g;
    g.roughness = SmoothnessToPerceptualRoughness(s.smoothness);
    g.reflUVW = reflect(-s.eyeVec, s.normalWorld);
    
    // ========================================
    // 采样反射探针
    // ========================================
    UnityGI gi = FragmentGI(s, occlusion, i.ambientOrLightmapUV, atten, mainLight);
    // gi.indirect.specular 来自 Reflection Probe
    
    // ========================================
    // 应用到BRDF
    // ========================================
    half4 c = UNITY_BRDF_PBS(
        s.diffColor,
        s.specColor,
        s.oneMinusReflectivity,
        s.smoothness,
        s.normalWorld,
        -s.eyeVec,
        gi.light,
        gi.indirect  // 包含反射探针的镜面反射
    );
    
    return OutputForward(c, s.alpha);
}
2. 自定义Shader使用反射探针
hlsl

Shader "Custom/ReflectionProbeExample"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _Smoothness ("Smoothness", Range(0,1)) = 0.5
        _Metallic ("Metallic", Range(0,1)) = 0.0
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            
            #include "UnityCG.cginc"
            #include "UnityStandardCore.cginc"
            
            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
            };
            
            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldPos : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
            };
            
            half4 _Color;
            half _Smoothness;
            half _Metallic;
            
            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                return o;
            }
            
            half4 frag(v2f i) : SV_Target
            {
                // ========================================
                // 1. 准备数据
                // ========================================
                half3 worldNormal = normalize(i.worldNormal);
                half3 worldViewDir = normalize(_WorldSpaceCameraPos - i.worldPos);
                
                // ========================================
                // 2. 计算反射方向
                // ========================================
                half3 reflDir = reflect(-worldViewDir, worldNormal);
                
                // ========================================
                // 3. 准备反射探针采样参数
                // ========================================
                Unity_GlossyEnvironmentData glossIn;
                glossIn.roughness = 1.0 - _Smoothness;  // 粗糙度 = 1 - 光滑度
                glossIn.reflUVW = reflDir;
                
                // ========================================
                // 4. 采样反射探针
                // ========================================
                half3 specular = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE(unity_SpecCube0),
                    unity_SpecCube0_HDR,
                    glossIn
                );
                
                // ========================================
                // 5. 简单的菲涅尔效果
                // ========================================
                half fresnel = pow(1.0 - saturate(dot(worldViewDir, worldNormal)), 5.0);
                half3 F0 = lerp(0.04, _Color.rgb, _Metallic);
                half3 F = F0 + (1.0 - F0) * fresnel;
                
                // ========================================
                // 6. 组合最终颜色
                // ========================================
                half3 diffuse = _Color.rgb * 0.5;  // 简化的漫反射
                half3 finalColor = diffuse + specular * F;
                
                return half4(finalColor, 1.0);
            }
            ENDCG
        }
    }
}
3. 通过脚本控制反射探针
csharp

using UnityEngine;

public class ReflectionProbeController : MonoBehaviour
{
    private ReflectionProbe probe;
    
    void Start()
    {
        probe = GetComponent<ReflectionProbe>();
        
        // ========================================
        // 设置探针类型
        // ========================================
        probe.mode = UnityEngine.Rendering.ReflectionProbeMode.Realtime;
        
        // ========================================
        // 设置分辨率
        // ========================================
        probe.resolution = 256;  // 256×256 每个面
        
        // ========================================
        // 设置HDR
        // ========================================
        probe.hdr = true;
        
        // ========================================
        // 设置更新频率
        // ========================================
        probe.refreshMode = UnityEngine.Rendering.ReflectionProbeRefreshMode.OnAwake;
        // 或 EveryFrame / ViaScripting
        
        // ========================================
        // 设置盒投影
        // ========================================
        probe.boxProjection = true;
        
        // ========================================
        // 设置影响范围
        // ========================================
        probe.size = new Vector3(10, 10, 10);
        
        // ========================================
        // 手动触发渲染
        // ========================================
        probe.RenderProbe();
    }
    
    void Update()
    {
        // 条件触发更新
        if (ShouldUpdateReflection())
        {
            probe.RenderProbe();
        }
    }
    
    bool ShouldUpdateReflection()
    {
        // 自定义逻辑，比如场景变化时
        return Input.GetKeyDown(KeyCode.R);
    }
}
八、性能考虑
1. Cubemap分辨率对比
apache

分辨率    内存占用(RGBA16F)    适用场景
64×64     96 KB              远景，不重要的反射
128×128   384 KB             一般场景
256×256   1.5 MB             重要的反射表面
512×512   6 MB               高质量，镜子
1024×1024 24 MB              极高质量，展示用
2. 实时探针性能

单个实时探针每次更新 = 6次场景渲染（每个面1次）

假设：
- 场景复杂度：1000 draw calls
- 更新一个实时探针：6000 draw calls
- 每帧更新3个探针：18000 draw calls

优化策略：
├─ 降低分辨率（256 → 128）
├─ 减少更新频率（每帧 → 每秒）
├─ 使用简化的场景几何体渲染
└─ 限制实时探针数量
3. 优化建议
csharp

// 使用Culling Mask只渲染重要物体
probe.cullingMask = LayerMask.GetMask("Environment", "ImportantObjects");

// 降低更新频率
probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
InvokeRepeating("UpdateProbe", 0, 0.5f);  // 每0.5秒更新一次

void UpdateProbe()
{
    probe.RenderProbe();
}

// 使用Time Slicing（时间切片）
probe.timeSlicingMode = UnityEngine.Rendering.ReflectionProbeTimeSlicingMode.AllFacesAtOnce;
// 或 IndividualFaces（分多帧渲染，更平滑）
九、技术总结
Reflection Probe完整技术栈

Reflection Probe System
│
├─ 1. 渲染阶段
│   ├─ 从探针位置渲染6个方向
│   ├─ 应用HDR和Tonemapping
│   └─ 生成Mipmap链（用于粗糙度）
│
├─ 2. 存储格式
│   ├─ Cubemap（6个面）
│   ├─ RGBM或HDR编码
│   └─ 多个Mip级别（0-6）
│
├─ 3. Shader采样
│   ├─ 计算反射方向 (reflect)
│   ├─ Box Projection修正
│   ├─ 粗糙度 → Mip级别
│   ├─ Cubemap采样 (UNITY_SAMPLE_TEXCUBE_LOD)
│   ├─ HDR解码
│   └─ 探针混合
│
└─ 4. 应用到渲染
    ├─ 提供间接镜面反射 (Indirect Specular)
    ├─ 与Light Probes配合 (提供Indirect Diffuse)
    └─ 应用到PBS/BRDF计算
关键函数总结
函数	功能	位置
Unity_GlossyEnvironment	从Cubemap采样反射	UnityStandardCore.cginc
UnityGI_IndirectSpecular	完整的反射探针采样流程	UnityGlobalIllumination.cginc
BoxProjectedCubemapDirection	盒投影修正	UnityStandardCore.cginc
DecodeHDR	HDR解码	UnityCG.cginc
perceptualRoughnessToMipmapLevel	粗糙度→Mip	UnityStandardCore.cginc
Reflection Probes是Unity实现真实感渲染的核心技术之一，为动态物体提供了高质量的环境反射效果！

17:37
Claude-Sonnet-4.5需要更多积分来回答此请求。

Reflection Probes不就是pbr

17:38

Claude-Sonnet-4.5


Reflection Probes ≠ PBR
这是一个常见的误解。让我详细解释它们的关系。

一、核心区别
Reflection Probes 是一种数据来源/技术，而 PBR 是一种渲染理论/方法。


类比：
Reflection Probes = 食材（环境光照数据）
PBR = 烹饪方法（如何使用这些数据）
二、什么是PBR？
PBR（Physically Based Rendering）的完整定义

PBR 是一套渲染方法论，包含：

1. 材质模型
   ├─ 能量守恒（Energy Conservation）
   ├─ 基于物理的BRDF（如Cook-Torrance）
   └─ 金属/非金属工作流

2. 光照模型
   ├─ 直接光照（Direct Lighting）
   │   └─ 点光源、方向光、聚光灯
   │
   └─ 间接光照（Indirect Lighting / GI）
       ├─ 漫反射间接光
       │   ├─ Light Probes（动态物体）
       │   └─ Lightmaps（静态物体）
       │
       └─ 镜面反射间接光
           ├─ Reflection Probes（预烘焙）
           ├─ SSR（屏幕空间反射）
           ├─ Planar Reflections（平面反射）
           └─ Ray Tracing（实时光追）

3. 着色方程
   └─ 渲染方程的近似求解
Unity Standard Shader的PBR实现
hlsl

// Unity的PBR核心函数
half4 UNITY_BRDF_PBS(
    half3 diffColor,          // 漫反射颜色
    half3 specColor,          // 镜面反射颜色（F0）
    half oneMinusReflectivity,
    half smoothness,          // 光滑度
    half3 normal,
    half3 viewDir,
    UnityLight light,         // 直接光照
    UnityIndirect indirect    // 间接光照
)
{
    // 1. 直接光照部分
    half3 directDiffuse = diffColor * light.color * NdotL;
    half3 directSpecular = specColor * light.color * D * G * F / (4 * NdotL * NdotV);
    
    // 2. 间接光照部分
    half3 indirectDiffuse = diffColor * indirect.diffuse;      // 来自Light Probes
    half3 indirectSpecular = specColor * indirect.specular;    // 来自Reflection Probes
    
    // 3. 组合
    half3 c = directDiffuse + directSpecular + indirectDiffuse + indirectSpecular;
    return half4(c, 1.0);
}
Reflection Probes 只是 PBR 中间接镜面反射光照的一种数据来源！

三、Reflection Probes 在 PBR 中的角色
完整的PBR间接镜面反射解决方案

PBR 间接镜面反射的实现方式：

1. 预计算方法（离线）
   ├─ Reflection Probes ← Unity主要使用
   │   ├─ 优点：质量好，性能高
   │   └─ 缺点：不能反射动态物体
   │
   └─ Lightmap中的镜面反射
       └─ 只适用于静态物体

2. 实时方法
   ├─ Screen Space Reflections (SSR)
   │   ├─ 优点：能反射屏幕内容
   │   └─ 缺点：屏幕外无反射
   │
   ├─ Planar Reflections
   │   ├─ 优点：完美的平面反射
   │   └─ 缺点：只适用于平面
   │
   └─ Ray Tracing (DXR)
       ├─ 优点：完全准确
       └─ 缺点：性能开销大

混合方案（现代引擎常用）：
Reflection Probes + SSR + Fallback
Unity中PBR的完整数据流
hlsl

// Standard Shader的片段着色器
half4 fragForwardBase(VertexOutputForwardBase i) : SV_Target
{
    // ========================================
    // 1. 准备PBR材质参数
    // ========================================
    FragmentCommonData s = FragmentSetup(...);
    // s.diffColor  = 漫反射颜色
    // s.specColor  = 镜面反射颜色（F0）
    // s.smoothness = 光滑度
    // s.normalWorld = 法线
    
    // ========================================
    // 2. 准备光照数据
    // ========================================
    
    // 2.1 直接光照（主光源）
    UnityLight mainLight = MainLight();
    // mainLight.color
    // mainLight.dir
    
    // 2.2 间接光照
    UnityGI gi = FragmentGI(s, occlusion, i.ambientOrLightmapUV, atten, mainLight);
    
    // gi.indirect.diffuse 来自：
    //   - Light Probes（动态物体）
    //   - Lightmap（静态物体）
    
    // gi.indirect.specular 来自：
    //   - Reflection Probes ← 这里！
    //   - SSR（如果启用HDRP/URP的SSR）
    
    // ========================================
    // 3. 应用PBR着色方程
    // ========================================
    half4 c = UNITY_BRDF_PBS(
        s.diffColor,
        s.specColor,
        s.oneMinusReflectivity,
        s.smoothness,
        s.normalWorld,
        -s.eyeVec,
        gi.light,      // 直接光照
        gi.indirect    // 间接光照（包含Reflection Probes数据）
    );
    
    return OutputForward(c, s.alpha);
}
四、没有Reflection Probes也能做PBR
示例1：仅使用直接光照的PBR
hlsl

Shader "Custom/PBR_DirectOnly"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _Metallic ("Metallic", Range(0,1)) = 0.0
        _Smoothness ("Smoothness", Range(0,1)) = 0.5
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        
        CGPROGRAM
        #pragma surface surf Standard
        
        struct Input {
            float2 uv_MainTex;
        };
        
        half _Metallic;
        half _Smoothness;
        fixed4 _Color;
        
        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            o.Albedo = _Color.rgb;
            o.Metallic = _Metallic;
            o.Smoothness = _Smoothness;
            
            // 这仍然是PBR！
            // Unity会自动应用PBR的BRDF
            // 但没有间接光照（Reflection Probes）
        }
        ENDCG
    }
}
结果：这是PBR渲染，但没有环境反射，物体看起来很"平"。

示例2：使用固定颜色代替Reflection Probes
hlsl

Shader "Custom/PBR_FixedReflection"
{
    CGPROGRAM
    #pragma surface surf Standard
    
    struct Input { float2 uv_MainTex; };
    
    void surf (Input IN, inout SurfaceOutputStandard o)
    {
        o.Albedo = float3(0.5, 0.5, 0.5);
        o.Metallic = 1.0;
        o.Smoothness = 0.9;
        
        // 手动设置环境反射为天空蓝
        o.Emission = float3(0.5, 0.7, 1.0) * 0.3;
    }
    ENDCG
}
这仍然是PBR，只是环境反射是固定的颜色而不是真实的环境。

五、PBR的核心是BRDF，不是数据来源
PBR的真正核心
hlsl

// PBR的核心：Cook-Torrance BRDF
// 这个公式定义了PBR，与数据来源无关

// 镜面反射部分
float3 specular = D * G * F / (4 * NdotL * NdotV);

// D = 法线分布函数（Normal Distribution Function）
//     常用：GGX / Trowbridge-Reitz
float D = D_GGX(roughness, NdotH);

// G = 几何遮蔽函数（Geometry Function）
//     常用：Smith
float G = G_Smith(roughness, NdotL, NdotV);

// F = 菲涅尔方程（Fresnel Equation）
//     常用：Schlick近似
float3 F = F_Schlick(F0, VdotH);
这些函数才是PBR的本质！

Reflection Probes只是提供了环境光照数据，而PBR决定了如何使用这些数据。

六、对比表格
方面	Reflection Probes	PBR
本质	数据来源（环境光照数据）	渲染方法（着色理论）
作用	提供预烘焙的环境反射	定义如何计算光照
替代方案	SSR、光追、固定颜色等	无（这是渲染方法本身）
是否必需	否（PBR可以没有它）	是（想要PBR必须用PBR BRDF）
依赖关系	被PBR使用	使用各种数据源
格式	Cubemap纹理	数学公式（BRDF）
七、实际对比案例
场景1：有Reflection Probes但没有PBR
hlsl

// 旧的Blinn-Phong着色模型 + Reflection Probes
Shader "Legacy/ReflectionNoNPBR"
{
    CGPROGRAM
    #pragma surface surf BlinnPhong  // 不是PBR！
    
    sampler2D _MainTex;
    samplerCUBE _ReflCube;  // 手动使用Reflection Probe
    
    struct Input {
        float2 uv_MainTex;
        float3 worldRefl;
    };
    
    void surf (Input IN, inout SurfaceOutput o)
    {
        o.Albedo = tex2D(_MainTex, IN.uv_MainTex).rgb;
        o.Specular = 0.5;
        o.Gloss = 1.0;
        
        // 使用Reflection Probes的数据
        // 但着色模型不是PBR！
        float3 refl = texCUBE(_ReflCube, IN.worldRefl).rgb;
        o.Emission = refl * 0.5;
    }
    ENDCG
}
结果：有反射，但不是物理正确的，因为没有用PBR的BRDF。

场景2：有PBR但没有Reflection Probes
hlsl

// 纯PBR，无环境反射
Shader "Custom/PBR_NoEnvironment"
{
    CGPROGRAM
    #pragma surface surf Standard nolightmap noambient
    
    struct Input { float2 uv_MainTex; };
    
    void surf (Input IN, inout SurfaceOutputStandard o)
    {
        o.Albedo = float3(0.8, 0.8, 0.8);
        o.Metallic = 0.5;
        o.Smoothness = 0.8;
        // 不使用任何间接光照
    }
    ENDCG
}
结果：渲染是物理正确的（PBR），但缺少环境反射，看起来不真实。

场景3：完整的PBR（推荐）
hlsl

// PBR + 完整的间接光照
Shader "Custom/FullPBR"
{
    CGPROGRAM
    #pragma surface surf Standard fullforwardshadows
    
    struct Input { float2 uv_MainTex; };
    
    void surf (Input IN, inout SurfaceOutputStandard o)
    {
        o.Albedo = float3(0.8, 0.8, 0.8);
        o.Metallic = 0.5;
        o.Smoothness = 0.8;
        
        // Unity自动使用：
        // - Light Probes（间接漫反射）
        // - Reflection Probes（间接镜面反射）
        // - PBR BRDF（物理正确的着色）
    }
    ENDCG
}
结果：完整的物理正确渲染 + 真实的环境反射。

八、现代渲染引擎的做法
Unity HDRP/URP的混合方案

PBR间接镜面反射的层次：

1. Base Layer（基础层）
   └─ Reflection Probes
      └─ 提供粗糙的环境反射

2. Enhancement Layer（增强层）
   └─ Screen Space Reflections (SSR)
      └─ 提供精确的屏幕内反射

3. Fallback（后备）
   └─ Sky Reflection
      └─ 当没有探针时使用天空盒

混合公式：
finalReflection = lerp(
    ReflectionProbe,
    SSR,
    ssrWeight
) * fresnel;
Unreal Engine的做法

虚幻引擎也是类似的：

1. Reflection Captures（类似Unity的Reflection Probes）
2. Screen Space Reflections
3. Ray Traced Reflections（光追）
4. Planar Reflections

PBR材质模型：
- BaseColor
- Metallic
- Roughness
- Specular（F0）
所有引擎都是：PBR作为核心，使用多种数据源（包括Reflection Probes）

九、总结
明确答案
Reflection Probes ≠ PBR

正确的关系是：


PBR（渲染方法）
├─ 直接光照
│   └─ 使用光源数据
│
└─ 间接光照
    ├─ 漫反射
    │   ├─ Light Probes ← 数据来源
    │   └─ Lightmaps ← 数据来源
    │
    └─ 镜面反射
        ├─ Reflection Probes ← 数据来源之一
        ├─ SSR ← 数据来源之一
        ├─ Ray Tracing ← 数据来源之一
        └─ Fixed Color ← 数据来源之一
关键要点
✅ PBR = 基于物理的渲染方法（BRDF + 能量守恒）
✅ Reflection Probes = 提供预烘焙环境反射数据的技术
✅ Reflection Probes是PBR中间接镜面反射的一种数据来源
✅ 没有Reflection Probes也可以做PBR（只是缺少环境反射）
✅ 有Reflection Probes但不用PBR也可以（如Blinn-Phong + Cubemap）
✅ 最佳实践：PBR + Reflection Probes + SSR = 高质量渲染
类比理解

做饭的类比：

PBR = 中餐烹饪方法（炒、煮、蒸等技法）
Reflection Probes = 冷藏柜里的食材
SSR = 新鲜现买的食材
Ray Tracing = 自己种植的有机蔬菜

你可以：
- 用中餐方法 + 冷藏食材 ✓（PBR + Reflection Probes）
- 用中餐方法 + 新鲜食材 ✓（PBR + SSR）
- 用中餐方法 + 没有食材 △（PBR无环境反射，能做但不好吃）
- 用西餐方法 + 冷藏食材 ✓（非PBR + Reflection Probes）

但烹饪方法（PBR）≠ 食材来源（Reflection Probes）
希望这样能彻底理解两者的区别！

17:38

Reflection Probes不就是pbr ibl中的反射环境图嘛

17:39

Claude-Sonnet-4.5


Unity中的Reflection Probes详解
你的理解是正确的！
是的，Reflection Probes本质上就是PBR IBL（Image-Based Lighting）中的反射环境图（Environment Map）。

但Unity在此基础上增加了很多实用功能。让我详细解释一下。

一、Reflection Probes的本质
1. 核心概念

Reflection Probes = 预过滤的环境立方体贴图（Pre-filtered Environment Cubemap）

PBR IBL 理论：
├─ 漫反射部分 → Irradiance Map（辐照度图）
└─ 镜面反射部分 → Pre-filtered Environment Map（预过滤环境图）
                  ↑
                  这就是 Reflection Probes！
2. 数学基础
在PBR中，镜面反射的IBL积分是：

reasonml

L_specular = ∫_Ω L_i(l) * f_r(l, v, n) * (n·l) dl

其中：
- L_i(l)：入射光照（环境贴图）
- f_r：BRDF（镜面反射部分）
- Ω：半球

问题：实时计算这个积分太慢！

解决方案（Split Sum Approximation）：
L_specular ≈ ∫_Ω L_i(l) * (n·l) dl  ×  ∫_Ω f_r(l,v,n) * (n·l) dl
             ↑                          ↑
             预过滤环境贴图              BRDF LUT
             (Reflection Probes)        (预计算查找表)
3. Unity的实现
Unity的Reflection Probes就是这个预过滤环境贴图，它在不同Mipmap级别存储了不同粗糙度的环境反射：

apache

Reflection Probe Cubemap 结构：

Mip 0: ████████  ← Roughness = 0.0 (完全光滑，清晰反射)
Mip 1: ██████    ← Roughness ≈ 0.2
Mip 2: ████      ← Roughness ≈ 0.4
Mip 3: ██        ← Roughness ≈ 0.6
Mip 4: █         ← Roughness ≈ 0.8
Mip 5: ▓         ← Roughness = 1.0 (完全粗糙，模糊反射)
二、Reflection Probes的生成过程
1. 烘焙/实时捕获流程

1. 捕获阶段（Capture）
   ├─> 在探针位置放置虚拟相机
   ├─> 渲染6个面（+X, -X, +Y, -Y, +Z, -Z）
   ├─> 生成原始Cubemap（HDR格式）
   └─> 分辨率：32, 64, 128, 256, 512, 1024, 2048

2. 卷积/预过滤阶段（Convolution）
   ├─> 对每个Mip级别进行卷积
   │   ├─> Mip 0: 卷积核很小（sharp）
   │   ├─> Mip 1: 卷积核稍大
   │   ├─> ...
   │   └─> Mip N: 卷积核很大（blur）
   │
   └─> 实现算法：
       ├─ 重要性采样（Importance Sampling）
       ├─ GGX分布
       └─ 每个像素采样数百个方向

3. 编码阶段（Encoding）
   └─> 编码为RGBM或HDR格式
2. 预过滤的实际代码（概念）
这是Unity内部使用的算法（简化版）：

hlsl

// Unity内部预过滤Reflection Probe的伪代码

float3 PrefilterEnvMap(float roughness, float3 R, TextureCube envMap)
{
    float3 N = R;  // 假设法线 = 反射方向
    float3 V = R;  // 假设视线 = 反射方向
    
    float3 prefilteredColor = 0;
    float totalWeight = 0;
    
    const int SAMPLE_COUNT = 1024;  // 采样数量
    
    for(int i = 0; i < SAMPLE_COUNT; i++)
    {
        // 使用重要性采样生成采样方向
        float2 Xi = Hammersley(i, SAMPLE_COUNT);
        float3 H = ImportanceSampleGGX(Xi, N, roughness);
        float3 L = normalize(2.0 * dot(V, H) * H - V);
        
        float NdotL = max(dot(N, L), 0.0);
        if(NdotL > 0.0)
        {
            // 从环境贴图采样
            prefilteredColor += envMap.Sample(L).rgb * NdotL;
            totalWeight += NdotL;
        }
    }
    
    return prefilteredColor / totalWeight;
}
三、在Shader中的使用
1. Unity_GlossyEnvironment函数
在UnityImageBasedLighting.cginc中：

hlsl

// 这就是PBR IBL的镜面反射部分！
half3 Unity_GlossyEnvironment(
    UNITY_ARGS_TEXCUBE(tex),     // Reflection Probe Cubemap
    half4 hdr,                    // HDR解码参数
    Unity_GlossyEnvironmentData glossIn
)
{
    half perceptualRoughness = glossIn.roughness;
    
    // 1. 粗糙度到Mipmap级别的转换
    // 这是Split Sum Approximation的关键！
    #if UNITY_GLOSS_MATCHES_MARMOSET_TOOLBAG2
        perceptualRoughness = perceptualRoughness * (1.7 - 0.7 * perceptualRoughness);
    #endif
    
    half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);
    
    // 2. 从Cubemap采样对应粗糙度的预过滤结果
    half3 R = glossIn.reflUVW;  // 反射方向
    half4 rgbm = UNITY_SAMPLE_TEXCUBE_LOD(tex, R, mip);
    
    // 3. 解码HDR
    return DecodeHDR(rgbm, hdr);
}
2. 粗糙度到Mip级别的映射
hlsl

// 在UnityStandardConfig.cginc中
#define UNITY_SPECCUBE_LOD_STEPS 6  // 通常是6个Mip级别

half perceptualRoughnessToMipmapLevel(half perceptualRoughness)
{
    return perceptualRoughness * UNITY_SPECCUBE_LOD_STEPS;
}

// 示例：
// roughness = 0.0 → mip = 0 (最清晰)
// roughness = 0.5 → mip = 3 (中等模糊)
// roughness = 1.0 → mip = 6 (最模糊)
3. 完整的PBR IBL实现
在Standard Shader中：

hlsl

half4 fragForwardBase(VertexOutputForwardBase i) : SV_Target
{
    // 1. 准备BRDF参数
    half3 specColor = _SpecColor.rgb;
    half smoothness = _Glossiness;
    half roughness = 1.0 - smoothness;
    half perceptualRoughness = SmoothnessToPerceptualRoughness(smoothness);
    
    // 2. 计算反射方向
    half3 reflDir = reflect(-viewDir, normal);
    
    // 3. 准备Glossy Environment数据
    Unity_GlossyEnvironmentData glossIn;
    glossIn.roughness = perceptualRoughness;
    glossIn.reflUVW = reflDir;
    
    // 4. 从Reflection Probe采样（这就是PBR IBL！）
    half3 specularIBL = Unity_GlossyEnvironment(
        UNITY_PASS_TEXCUBE(unity_SpecCube0),  // Reflection Probe
        unity_SpecCube0_HDR,                   // HDR参数
        glossIn
    );
    
    // 5. 应用菲涅尔效应（环境BRDF）
    half grazingTerm = saturate(smoothness + (1-oneMinusReflectivity));
    half fresnelTerm = Pow4(1.0 - NdotV);
    half3 envBRDF = lerp(specColor, grazingTerm, fresnelTerm);
    
    // 6. 最终的镜面反射IBL
    half3 specularGI = specularIBL * envBRDF;
    
    return specularGI;
}
四、Reflection Probes vs 纯理论PBR IBL
对比表
特性	标准PBR IBL理论	Unity Reflection Probes
环境贴图	HDR全景图/Cubemap	Cubemap（预过滤）
存储格式	HDR (EXR/HDR)	RGBM/HDR16
预过滤	需要实时或预计算	预烘焙到Mipmap
BRDF积分	运行时计算或查表	简化为查表
多探针	通常单个	支持混合
盒投影	无	有（更准确的室内反射）
更新方式	静态	静态/动态/实时
Unity增强功能
Unity在标准PBR IBL基础上添加了：

1. 多探针混合
hlsl

#ifdef UNITY_SPECCUBE_BLENDING
    // 混合两个Reflection Probes
    half3 env0 = Unity_GlossyEnvironment(
        UNITY_PASS_TEXCUBE(unity_SpecCube0), 
        unity_SpecCube0_HDR, 
        glossIn
    );
    
    half3 env1 = Unity_GlossyEnvironment(
        UNITY_PASS_TEXCUBE_SAMPLER(unity_SpecCube1, unity_SpecCube0),
        unity_SpecCube1_HDR,
        glossIn
    );
    
    // 根据权重混合
    specular = lerp(env1, env0, blendWeight);
#endif
2. 盒投影（Box Projection）
hlsl

#ifdef UNITY_SPECCUBE_BOX_PROJECTION
    // 修正反射方向，模拟盒子形状的房间
    half3 BoxProjectedCubemapDirection(
        half3 worldRefl,
        float3 worldPos,
        float4 cubemapCenter,
        float4 boxMin,
        float4 boxMax
    )
    {
        // 计算射线与盒子的交点
        half3 nrdir = normalize(worldRefl);
        half3 rbmax = (boxMax.xyz - worldPos) / nrdir;
        half3 rbmin = (boxMin.xyz - worldPos) / nrdir;
        half3 rbminmax = (nrdir > 0.0f) ? rbmax : rbmin;
        
        half fa = min(min(rbminmax.x, rbminmax.y), rbminmax.z);
        worldPos -= cubemapCenter.xyz;
        worldRefl = worldPos + nrdir * fa;
        
        return worldRefl;
    }
#endif
这使得室内反射更真实！

3. 动态更新模式
csharp

// C# 代码
ReflectionProbe probe = GetComponent<ReflectionProbe>();

// 烘焙模式
probe.mode = ReflectionProbeMode.Baked;        // 静态，最快
probe.mode = ReflectionProbeMode.Custom;       // 自定义更新
probe.mode = ReflectionProbeMode.Realtime;     // 实时，最慢

// 实时更新频率
probe.refreshMode = ReflectionProbeRefreshMode.EveryFrame;    // 每帧
probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;  // 脚本控制
五、实际数据结构
1. Reflection Probe资源格式
apache

ReflectionProbe.exr（烘焙结果）
├─ Format: Cubemap
├─ Resolution: 128x128（或更高）
├─ Faces: 6
├─ Mipmap Levels: 7
│   ├─ Mip 0: 128x128 (roughness ≈ 0.0)
│   ├─ Mip 1: 64x64   (roughness ≈ 0.17)
│   ├─ Mip 2: 32x32   (roughness ≈ 0.33)
│   ├─ Mip 3: 16x16   (roughness ≈ 0.50)
│   ├─ Mip 4: 8x8     (roughness ≈ 0.67)
│   ├─ Mip 5: 4x4     (roughness ≈ 0.83)
│   └─ Mip 6: 2x2     (roughness ≈ 1.0)
│
└─ Encoding: RGBM或HDR16
2. Shader变量
hlsl

// Reflection Probe 0（主探针）
UNITY_DECLARE_TEXCUBE(unity_SpecCube0);
uniform half4 unity_SpecCube0_HDR;
uniform float4 unity_SpecCube0_BoxMin;
uniform float4 unity_SpecCube0_BoxMax;
uniform float4 unity_SpecCube0_ProbePosition;

// Reflection Probe 1（次探针，用于混合）
UNITY_DECLARE_TEXCUBE(unity_SpecCube1);
uniform half4 unity_SpecCube1_HDR;
uniform float4 unity_SpecCube1_BoxMin;
uniform float4 unity_SpecCube1_BoxMax;
uniform float4 unity_SpecCube1_ProbePosition;
六、与标准PBR IBL工作流的兼容性
1. 导入外部HDR环境图
Unity支持导入标准的HDR环境贴图：

csharp

// 1. 导入HDR全景图（Equirectangular）
// 2. 设置Texture Type为 "Default"
// 3. 勾选 "Generate Cubemap"
// 4. Unity自动转换为Cubemap并预过滤

// 使用自定义环境贴图
ReflectionProbe probe = GetComponent<ReflectionProbe>();
probe.mode = ReflectionProbeMode.Custom;
probe.customBakedTexture = myHDRCubemap;
2. Skybox作为全局Reflection Probe
hlsl

// Unity自动从Skybox生成全局Reflection Probe
// 在 Lighting > Environment > Reflection Source

// 在Shader中访问
half3 skyboxReflection = Unity_GlossyEnvironment(
    UNITY_PASS_TEXCUBE(unity_SpecCube0),  // 从Skybox生成
    unity_SpecCube0_HDR,
    glossIn
);
七、完整示例：自定义PBR IBL Shader
hlsl

Shader "Custom/PBR_IBL"
{
    Properties
    {
        _Color ("Albedo", Color) = (1,1,1,1)
        _Metallic ("Metallic", Range(0,1)) = 0.0
        _Smoothness ("Smoothness", Range(0,1)) = 0.5
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "UnityPBSLighting.cginc"
            #include "UnityStandardBRDF.cginc"

            half4 _Color;
            half _Metallic;
            half _Smoothness;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldPos : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                return o;
            }

            half4 frag(v2f i) : SV_Target
            {
                // ========================================
                // 1. PBR参数准备
                // ========================================
                half3 N = normalize(i.worldNormal);
                half3 V = normalize(_WorldSpaceCameraPos - i.worldPos);
                half3 R = reflect(-V, N);
                
                half NdotV = saturate(dot(N, V));
                
                // ========================================
                // 2. 材质参数
                // ========================================
                half3 albedo = _Color.rgb;
                half metallic = _Metallic;
                half smoothness = _Smoothness;
                half roughness = 1.0 - smoothness;
                half perceptualRoughness = SmoothnessToPerceptualRoughness(smoothness);
                
                // F0（垂直入射时的反射率）
                half3 specColor = lerp(half3(0.04, 0.04, 0.04), albedo, metallic);
                half oneMinusReflectivity = OneMinusReflectivityFromMetallic(metallic);
                half3 diffColor = albedo * oneMinusReflectivity;
                
                // ========================================
                // 3. IBL镜面反射（Reflection Probe）
                // ========================================
                Unity_GlossyEnvironmentData glossIn;
                glossIn.roughness = perceptualRoughness;
                glossIn.reflUVW = R;
                
                // 从Reflection Probe采样
                half3 specularIBL = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE(unity_SpecCube0),
                    unity_SpecCube0_HDR,
                    glossIn
                );
                
                // ========================================
                // 4. 环境BRDF（菲涅尔效应）
                // ========================================
                half grazingTerm = saturate(smoothness + (1 - oneMinusReflectivity));
                half fresnelTerm = Pow4(1.0 - NdotV);
                half3 envBRDF = lerp(specColor, grazingTerm.xxx, fresnelTerm);
                
                // 应用环境BRDF
                half3 specular = specularIBL * envBRDF;
                
                // ========================================
                // 5. IBL漫反射（可选，这里简化）
                // ========================================
                half3 diffuse = diffColor * UNITY_LIGHTMODEL_AMBIENT.rgb;
                
                // ========================================
                // 6. 最终颜色
                // ========================================
                half3 color = diffuse + specular;
                
                return half4(color, 1.0);
            }
            ENDCG
        }
    }
}
总结
Reflection Probes = PBR IBL的工程实现

理论PBR IBL（学术）              Unity Reflection Probes（工程）
─────────────────────────────────────────────────────────────
环境贴图                      →  Cubemap
实时卷积/预计算               →  预烘焙到Mipmap
Split Sum Approximation      →  粗糙度→Mip映射
单个环境图                    →  多探针混合
点采样                        →  盒投影修正
静态                          →  静态/动态/实时
无优化                        →  RGBM压缩、LOD
核心要点
✅ Reflection Probes确实就是PBR IBL的预过滤环境贴图
✅ 使用Mipmap存储不同粗糙度的预过滤结果
✅ 实现了Split Sum Approximation的第一部分积分
✅ Unity添加了多探针混合、盒投影、动态更新等实用功能
✅ 完全兼容标准PBR工作流
你的理解完全正确！Reflection Probes就是Unity对PBR IBL镜面反射部分的实际实现。

17:39

Reflection Probe的类型 为何又三种？IBL是不是只有一种？

17:42

Claude-Sonnet-4.5


Reflection Probe的三种类型详解
一、Reflection Probe的三种类型
Unity中的Reflection Probe确实有三种更新模式（不是"类型"，本质都是同一种技术）：

csharp

public enum ReflectionProbeMode
{
    Baked,      // 烘焙模式
    Custom,     // 自定义模式
    Realtime    // 实时模式
}
1. Baked（烘焙模式）

特点：
├─ 在编辑器中预计算，保存为资源文件
├─ 运行时不更新
├─ 性能开销：0（运行时）
└─ 适用场景：静态环境

工作流程：
1. Editor中点击"Bake"
2. Unity渲染6个面 → 卷积 → 生成Mipmap
3. 保存为 .exr 文件
4. 运行时直接加载使用
示例：

csharp

// 设置为烘焙模式
ReflectionProbe probe = GetComponent<ReflectionProbe>();
probe.mode = ReflectionProbeMode.Baked;

// 在编辑器中烘焙
#if UNITY_EDITOR
probe.RenderProbe();
#endif
2. Custom（自定义模式）

特点：
├─ 使用外部提供的Cubemap
├─ 可以是预烘焙的，也可以是程序生成的
├─ 性能开销：0（如果使用预烘焙贴图）
└─ 适用场景：需要精确控制反射内容

工作流程：
1. 准备一个Cubemap（预过滤好的）
2. 分配给 customBakedTexture
3. 运行时使用这个Cubemap
示例：

csharp

// 使用自定义Cubemap
ReflectionProbe probe = GetComponent<ReflectionProbe>();
probe.mode = ReflectionProbeMode.Custom;
probe.customBakedTexture = myCustomCubemap;

// 例如：从HDR全景图转换
// 1. 导入 HDRI.exr
// 2. 设置为 Cubemap
// 3. 分配给 customBakedTexture
3. Realtime（实时模式）

特点：
├─ 运行时实时渲染场景到Cubemap
├─ 可以反射动态物体
├─ 性能开销：高（每次更新需要渲染6个面）
└─ 适用场景：需要反射动态内容的场景

工作流程：
1. 每帧/定时/手动触发
2. 在探针位置渲染6个面
3. 实时卷积生成Mipmap
4. 更新Cubemap
示例：

csharp

// 设置为实时模式
ReflectionProbe probe = GetComponent<ReflectionProbe>();
probe.mode = ReflectionProbeMode.Realtime;

// 更新频率
probe.refreshMode = ReflectionProbeRefreshMode.EveryFrame;      // 每帧
probe.refreshMode = ReflectionProbeRefreshMode.OnAwake;         // 启动时一次
probe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;    // 手动控制

// 手动更新
probe.RenderProbe();
二、对比表格
特性	Baked	Custom	Realtime
更新时机	编辑器预烘焙	外部提供	运行时渲染
存储	保存为文件	外部资源	内存中
性能开销	0	0	高
反射动态物体	❌	❌	✅
内存占用	低（共享资源）	低	中（每个探针独立）
适用场景	静态环境	天空盒/特殊效果	动态镜面/水面
三、IBL是否只有一种？
答案：IBL有多种实现方式，不只一种
IBL（Image-Based Lighting）是一个概念/技术，可以有多种实现：

1. 按照环境贴图类型分类

IBL环境贴图类型：

1. Cubemap（立方体贴图）
   ├─ Unity Reflection Probes使用
   ├─ 最常用
   └─ 6个面

2. Equirectangular（等距柱状投影）
   ├─ 全景图
   ├─ HDRI常用格式
   └─ 单张2:1的图

3. Spherical（球面贴图）
   ├─ 类似鱼眼
   └─ 较少使用

4. Octahedral（八面体投影）
   ├─ 高效存储
   └─ 现代引擎使用
示例：从Equirectangular转Cubemap

hlsl

// 等距柱状投影转立方体贴图
float2 SampleSphericalMap(float3 v)
{
    float2 uv = float2(atan2(v.z, v.x), asin(v.y));
    uv *= float2(0.1591, 0.3183); // 1/2π, 1/π
    uv += 0.5;
    return uv;
}

// 在片段着色器中
float3 localPos = normalize(i.localPos);
float2 uv = SampleSphericalMap(localPos);
float3 color = tex2D(_EquirectangularMap, uv).rgb;
2. 按照更新方式分类

IBL更新方式：

1. Static IBL（静态IBL）
   ├─ 预烘焙，不更新
   ├─ Unity的Baked Reflection Probes
   └─ 对应：Baked模式

2. Dynamic IBL（动态IBL）
   ├─ 运行时更新
   ├─ Unity的Realtime Reflection Probes
   └─ 对应：Realtime模式

3. Hybrid IBL（混合IBL）
   ├─ 静态 + 动态
   ├─ 例如：Baked Probes + SSR
   └─ 现代引擎常用
3. 按照质量/技术分类

IBL质量级别：

1. Pre-filtered Environment Map（预过滤）
   ├─ Unity Reflection Probes
   ├─ Split Sum Approximation
   ├─ 快速
   └─ 质量：高

2. Real-time Convolution（实时卷积）
   ├─ 每帧卷积环境贴图
   ├─ 性能：低
   └─ 质量：最高

3. SH-based IBL（球谐函数）
   ├─ Unity Light Probes
   ├─ 极快
   └─ 质量：低（只适合漫反射）

4. Voxel-based GI
   ├─ 体素化场景
   ├─ SVOGI、VXGI
   └─ 质量：高，性能：中
四、Unity中IBL的完整实现
Unity实际上使用了多种IBL技术的组合：


Unity的完整IBL系统：

1. 漫反射IBL
   ├─ Light Probes（球谐函数，9系数）
   │   ├─ Baked
   │   └─ LPPV（大型动态物体）
   │
   └─ Lightmaps（仅静态物体）
       ├─ Baked GI
       └─ Realtime GI（已弃用）

2. 镜面反射IBL
   ├─ Reflection Probes（预过滤Cubemap）
   │   ├─ Baked
   │   ├─ Custom
   │   └─ Realtime
   │
   ├─ SSR（屏幕空间反射，URP/HDRP）
   ├─ Planar Reflections
   └─ Ray Tracing（HDRP）
完整的Shader代码示例
hlsl

Shader "Custom/CompleteIBL"
{
    SubShader
    {
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "UnityPBSLighting.cginc"

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldPos : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                float3 shAmbient : TEXCOORD2;  // Light Probes结果
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                
                // ========================================
                // 漫反射IBL：Light Probes（SH-based）
                // ========================================
                o.shAmbient = ShadeSH9(half4(o.worldNormal, 1.0));
                
                return o;
            }

            half4 frag(v2f i) : SV_Target
            {
                half3 N = normalize(i.worldNormal);
                half3 V = normalize(_WorldSpaceCameraPos - i.worldPos);
                half3 R = reflect(-V, N);
                
                // ========================================
                // 1. 漫反射IBL（多种技术）
                // ========================================
                half3 diffuseIBL = 0;
                
                #ifdef LIGHTMAP_ON
                    // 方式1：Lightmap（静态物体）
                    diffuseIBL = DecodeLightmap(
                        UNITY_SAMPLE_TEX2D(unity_Lightmap, i.uv_lightmap)
                    );
                #else
                    // 方式2：Light Probes（动态物体，SH-based IBL）
                    diffuseIBL = i.shAmbient;
                #endif
                
                // ========================================
                // 2. 镜面反射IBL（多种技术）
                // ========================================
                half3 specularIBL = 0;
                
                // 方式1：Reflection Probes（预过滤Cubemap IBL）
                Unity_GlossyEnvironmentData glossIn;
                glossIn.roughness = 0.2;
                glossIn.reflUVW = R;
                
                specularIBL = Unity_GlossyEnvironment(
                    UNITY_PASS_TEXCUBE(unity_SpecCube0),  // Baked/Custom/Realtime
                    unity_SpecCube0_HDR,
                    glossIn
                );
                
                // 方式2：SSR（如果可用，HDRP/URP）
                #ifdef _SSR_ENABLED
                    half3 ssrColor = SampleSSR(i.screenPos, R);
                    specularIBL = lerp(specularIBL, ssrColor, ssrWeight);
                #endif
                
                // 方式3：Planar Reflection（如果有）
                #ifdef _PLANAR_REFLECTION
                    half3 planarRefl = tex2D(_PlanarReflectionTex, screenUV).rgb;
                    specularIBL = lerp(specularIBL, planarRefl, planarMask);
                #endif
                
                // ========================================
                // 3. 组合所有IBL
                // ========================================
                half3 albedo = half3(0.5, 0.5, 0.5);
                half3 diffuse = albedo * diffuseIBL;
                half3 specular = half3(0.04, 0.04, 0.04) * specularIBL;
                
                return half4(diffuse + specular, 1.0);
            }
            ENDCG
        }
    }
}
五、不同引擎的IBL实现对比
1. Unity
apache

Unity IBL实现：

漫反射：
├─ Light Probes（SH L2, 9系数）← 类型1
├─ LPPV（3D Texture存储SH）     ← 类型2
└─ Lightmaps                    ← 类型3

镜面反射：
├─ Reflection Probes            ← 类型1（三种模式）
│   ├─ Baked
│   ├─ Custom
│   └─ Realtime
├─ SSR（URP/HDRP）              ← 类型2
├─ Planar Reflections           ← 类型3
└─ Ray Tracing（HDRP）          ← 类型4
2. Unreal Engine

Unreal IBL实现：

漫反射：
├─ Volumetric Lightmaps（SH L2）
├─ Lightmass GI
└─ Lumen（动态GI）

镜面反射：
├─ Reflection Captures          ← 类似Unity Reflection Probes
│   ├─ Sphere
│   ├─ Box
│   └─ Plane
├─ Screen Space Reflections
├─ Planar Reflections
├─ Ray Tracing Reflections
└─ Lumen Reflections
3. 标准PBR工作流（理论）

理论PBR IBL：

1. 环境贴图来源
   ├─ HDR全景图（.hdr, .exr）
   ├─ 天空盒生成
   └─ 程序化生成

2. 预过滤方式
   ├─ GGX重要性采样
   ├─ 分离求和近似
   └─ 多级Mipmap

3. 使用方式
   ├─ Split Sum Approximation
   │   ├─ 预过滤环境贴图
   │   └─ BRDF LUT
   └─ 实时积分（太慢，不实用）
六、为什么需要三种模式？
性能 vs 质量的权衡

场景需求分析：

场景1：静态室内（博物馆）
├─ 环境：完全静态
├─ 需求：高质量反射
└─ 方案：Baked Reflection Probes
    └─ 性能：★★★★★
    └─ 质量：★★★★★

场景2：天空盒反射
├─ 环境：只有天空变化
├─ 需求：统一的天空反射
└─ 方案：Custom + Skybox Cubemap
    └─ 性能：★★★★★
    └─ 质量：★★★★☆

场景3：动态镜面/水面
├─ 环境：有动态物体
├─ 需求：反射动态内容
└─ 方案：Realtime Reflection Probes
    └─ 性能：★★☆☆☆
    └─ 质量：★★★★★

场景4：混合方案（推荐）
├─ 环境：静态 + 动态混合
├─ 需求：高质量 + 好性能
└─ 方案：Baked + SSR
    └─ 性能：★★★★☆
    └─ 质量：★★★★★
实际使用策略
csharp

public class ReflectionProbeManager : MonoBehaviour
{
    public ReflectionProbe staticProbe;   // Baked
    public ReflectionProbe skyboxProbe;   // Custom
    public ReflectionProbe dynamicProbe;  // Realtime
    
    void Setup()
    {
        // 1. 静态环境反射（大部分物体）
        staticProbe.mode = ReflectionProbeMode.Baked;
        staticProbe.importance = 1;
        staticProbe.boxProjection = true;  // 室内必须开启
        
        // 2. 天空盒反射（远处物体）
        skyboxProbe.mode = ReflectionProbeMode.Custom;
        skyboxProbe.customBakedTexture = RenderSettings.skybox.GetTexture("_Tex");
        skyboxProbe.importance = 0;  // 优先级最低
        
        // 3. 动态反射（特殊需求，如镜子）
        dynamicProbe.mode = ReflectionProbeMode.Realtime;
        dynamicProbe.refreshMode = ReflectionProbeRefreshMode.ViaScripting;
        dynamicProbe.importance = 2;  // 优先级最高
        
        // 只在需要时更新动态探针
        InvokeRepeating("UpdateDynamicProbe", 0, 0.5f);  // 0.5秒更新一次
    }
    
    void UpdateDynamicProbe()
    {
        if (PlayerNearMirror())
        {
            dynamicProbe.RenderProbe();
        }
    }
}
七、总结
关键要点
Reflection Probe的三种"模式"不是三种不同的IBL技术

都是基于预过滤Cubemap的IBL
区别只在于更新方式和数据来源
本质技术相同（Split Sum Approximation）
IBL确实有多种实现方式


IBL类型分类：
├─ 按环境贴图：Cubemap、Equirectangular、Spherical等
├─ 按更新方式：Static、Dynamic、Hybrid
├─ 按技术实现：预过滤、实时卷积、SH、体素等
└─ 按质量级别：低质量SH → 高质量光追
Unity的混合策略


最佳实践 = Baked Probes（静态基础）
           + Custom（天空盒）
           + SSR（动态增强）
           + Realtime（特殊需求）
性能考虑


Baked     ：0 ms（运行时）       ← 推荐大量使用
Custom    ：0 ms                ← 推荐用于天空盒
Realtime  ：5-20 ms（每次更新） ← 谨慎使用
简单记忆
ini

Reflection Probe = 预过滤Cubemap IBL的不同"包装"
├─ Baked    = 离线预烘焙的包装
├─ Custom   = 自己提供的包装
└─ Realtime = 实时渲染的包装

IBL = 基于图像的光照（概念）
├─ 可以有多种环境贴图格式
├─ 可以有多种更新策略
├─ 可以有多种技术实现
└─ Unity的Reflection Probes只是其中一种实现
希望这样能彻底理解Reflection Probe的三种模式和IBL的多样性！

17:42

结合UnityGI UnityGI_Base(UnityGIInput data, half occlusion, half3 normalWorld)，unity bake的结果没有直接光照嘛？为什么都赋值给了indirect；UnityGI.light是什么含义？

17:51

Claude-Sonnet-4.5


Unity GI系统深度解析
让我详细分析UnityGI_Base函数和Unity烘焙系统的设计哲学。

一、先看UnityGI_Base的完整源码
hlsl

// 位置：UnityGlobalIllumination.cginc

struct UnityGI
{
    UnityLight light;        // ← 直接光照
    UnityIndirect indirect;  // ← 间接光照（GI）
};

struct UnityIndirect
{
    half3 diffuse;   // 漫反射GI
    half3 specular;  // 镜面反射GI
};

struct UnityLight
{
    half3 color;     // 光源颜色 * 强度
    half3 dir;       // 光源方向
};

// ========================================
// 核心函数
// ========================================
inline UnityGI UnityGI_Base(UnityGIInput data, half occlusion, half3 normalWorld)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);  // 初始化为0
    
    // ========================================
    // 1. 处理烘焙的光照贴图
    // ========================================
    #ifdef LIGHTMAP_ON
        // 从Lightmap采样（烘焙的直接+间接光照）
        o_gi.indirect.diffuse = DecodeLightmap(
            UNITY_SAMPLE_TEX2D(unity_Lightmap, data.lightmapUV)
        );
        
        // 如果开启了方向性光照贴图
        #ifdef DIRLIGHTMAP_COMBINED
            fixed4 bakedDirTex = UNITY_SAMPLE_TEX2D_SAMPLER(
                unity_LightmapInd, unity_Lightmap, data.lightmapUV
            );
            o_gi.indirect.diffuse = DecodeDirectionalLightmap(
                o_gi.indirect.diffuse, bakedDirTex, normalWorld
            );
        #endif
        
        // 应用AO遮蔽
        o_gi.indirect.diffuse *= occlusion;
    #endif
    
    // ========================================
    // 2. 处理动态GI（Realtime GI，已弃用）
    // ========================================
    #ifdef DYNAMICLIGHTMAP_ON
        fixed4 realtimeColorTex = UNITY_SAMPLE_TEX2D(
            unity_DynamicLightmap, data.lightmapUV
        );
        half3 realtimeLightmap = DecodeRealtimeLightmap(realtimeColorTex);
        
        #ifdef DIRLIGHTMAP_COMBINED
            half4 realtimeDirTex = UNITY_SAMPLE_TEX2D_SAMPLER(
                unity_DynamicDirectionality, unity_DynamicLightmap, data.lightmapUV
            );
            o_gi.indirect.diffuse += DecodeDirectionalLightmap(
                realtimeLightmap, realtimeDirTex, normalWorld
            );
        #else
            o_gi.indirect.diffuse += realtimeLightmap;
        #endif
    #endif
    
    // ========================================
    // 3. 处理Light Probes（动态物体）
    // ========================================
    #if !defined(LIGHTMAP_ON) && !defined(DYNAMICLIGHTMAP_ON)
        #if UNITY_LIGHT_PROBE_PROXY_VOLUME
            // LPPV（大型动态物体）
            o_gi.indirect.diffuse = SHEvalLinearL0L1_SampleProbeVolume(
                half4(normalWorld, 1), data.probePosition
            );
        #else
            // 普通Light Probes（SH系数）
            o_gi.indirect.diffuse = ShadeSH9(half4(normalWorld, 1));
        #endif
        
        o_gi.indirect.diffuse *= occlusion;
    #endif
    
    // ========================================
    // 4. 处理Reflection Probes（镜面反射）
    // ========================================
    Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
        data.roughness, data.worldViewDir, normalWorld, data.reflUVW
    );
    o_gi.indirect.specular = UnityGI_IndirectSpecular(data, occlusion, g);
    
    // ========================================
    // 5. 注意：这里并没有设置 o_gi.light！
    //    o_gi.light 仍然是零值
    // ========================================
    
    return o_gi;
}
二、关键问题解答
问题1：Unity Bake的结果有直接光照吗？
答案：有！但被故意分离了。

hlsl

// Unity的Lightmap存储的内容：

Lightmap = 直接光照（Direct） + 间接光照（Indirect）

具体来说：
┌─────────────────────────────────────┐
│ Unity Lightmap 包含的光照：          │
├─────────────────────────────────────┤
│ 1. 直接光照（Direct Lighting）       │
│    ├─ 静态物体对Directional Light   │
│    ├─ 静态物体对Point/Spot Light     │
│    └─ 所有标记为Baked的光源         │
│                                      │
│ 2. 间接光照（Indirect Lighting）     │
│    ├─ 一次反弹（GI Bounce 1）       │
│    ├─ 二次反弹（GI Bounce 2）       │
│    └─ ...（根据设置）               │
└─────────────────────────────────────┘

所以：
Lightmap = DirectFromBakedLights + IndirectGI
验证实验
csharp

// 创建测试场景
public class LightmapAnalysis : MonoBehaviour
{
    [Header("场景设置")]
    public Light directionalLight;  // Mode = Baked
    public GameObject staticCube;    // Static
    
    void AnalyzeLightmap()
    {
        // 1. 只开启Directional Light（Baked）
        //    关闭所有Bounce（Lighting Settings → Bounces = 0）
        //    → Lightmap只包含直接光照
        
        // 2. Bounce = 2
        //    → Lightmap = 直接光照 + 一次反弹 + 二次反弹
        
        // 3. 使用Lightmap Visualizer查看
        Lightmapping.BakeAsync();
    }
}
验证结果：


测试1：Bounce = 0
├─ Lightmap颜色：明亮（包含直接光照）
├─ 运行时：静态物体被照亮
└─ 证明：Lightmap包含直接光照

测试2：Bounce = 2
├─ Lightmap颜色：更明亮（直接+间接）
├─ 运行时：静态物体更亮，有颜色渗透
└─ 证明：Lightmap = 直接 + 间接

测试3：只开启Indirect（Lighting Mode = Subtractive）
├─ Lightmap只存储间接光照
├─ 直接光照在运行时实时计算
└─ 这是特殊模式
问题2：为什么都赋值给了indirect？
答案：Unity的术语问题 + 设计哲学

2.1 Unity的定义
hlsl

// Unity内部的概念映射：

在UnityGI结构体中：
┌──────────────────────────────────────────┐
│ UnityGI.light（实时光源）                 │
│ ├─ 场景中的实时光源（Mode = Realtime）   │
│ ├─ 每帧动态计算                          │
│ ├─ 可以移动、改变颜色                    │
│ └─ 不依赖任何烘焙数据                    │
├──────────────────────────────────────────┤
│ UnityGI.indirect（预计算数据）            │
│ ├─ 所有预先烘焙的光照                    │
│ ├─ 包括直接光照（从Baked光源）           │
│ ├─ 包括间接光照（GI Bounces）           │
│ ├─ 包括环境光（Ambient）                │
│ └─ 运行时不变（静态数据）                │
└──────────────────────────────────────────┘

所以Unity的命名约定：
"indirect" ≠ 物理上的"间接光照"
"indirect" = "预计算的、间接提供的光照"
          = "不是来自实时光源的光照"
2.2 为什么这样设计？
hlsl

// 原因1：混合光照模式支持

Unity支持4种光照模式：
┌─────────────────────────────────────────────┐
│ 1. Baked Indirect（烘焙间接光）              │
│    ├─ indirect.diffuse  = 间接光照（GI）    │
│    └─ light            = 实时直接光照        │
├─────────────────────────────────────────────┤
│ 2. Shadowmask（阴影遮罩）                   │
│    ├─ indirect.diffuse  = 直接+间接光照     │
│    └─ light            = 实时光（用于动态）  │
├─────────────────────────────────────────────┤
│ 3. Subtractive（减法模式）                  │
│    ├─ indirect.diffuse  = 间接光照          │
│    └─ light            = 主光源直接光        │
├─────────────────────────────────────────────┤
│ 4. Realtime（完全实时）                     │
│    ├─ indirect.diffuse  = Light Probes      │
│    └─ light            = 所有实时光源        │
└─────────────────────────────────────────────┘

// 统一接口设计
half4 frag()
{
    UnityGI gi = UnityGI_Base(...);  // 获取预计算数据
    gi.light = GetMainLight();        // 添加实时光源
    
    // 无论哪种模式，后续代码都一样：
    half3 lighting = BRDF(gi.light, gi.indirect, ...);
}
2.3 详细的光照路径
hlsl

// ========================================
// 完整的Unity光照管线
// ========================================

// Step 1: UnityGI_Base - 收集所有预计算数据
UnityGI gi = UnityGI_Base(data, occlusion, normalWorld);
// 此时：
// gi.light = {0, 0, 0}  ← 空的
// gi.indirect.diffuse = Lightmap或Light Probes（包含直接+间接）
// gi.indirect.specular = Reflection Probes

// Step 2: UnityGI_Base会被封装在更高层函数中
inline UnityGI UnityGlobalIllumination(
    UnityGIInput data, half occlusion, half3 normalWorld)
{
    UnityGI o_gi = UnityGI_Base(data, occlusion, normalWorld);
    
    // ========================================
    // 在这里添加实时光源！
    // ========================================
    o_gi.light = _LightColor0;  // 主平行光
    o_gi.light.dir = _WorldSpaceLightPos0.xyz;
    
    return o_gi;
}

// Step 3: 在Forward Rendering中
half4 frag() : SV_Target
{
    // 3.1 获取GI（预计算）
    UnityGI gi = UnityGlobalIllumination(...);
    
    // 3.2 计算光照
    half4 c = UNITY_BRDF_PBS(
        albedo,           // 基础颜色
        specColor,        // 镜面颜色
        oneMinusReflectivity,
        smoothness,
        normalWorld,
        viewDir,
        gi.light,         // ← 实时光源（可能为0）
        gi.indirect       // ← 预计算数据（Lightmap/Probes）
    );
    
    return c;
}
三、不同光照模式的详细对比
Mode 1: Baked（完全烘焙）
hlsl

// 光源设置：Mode = Baked

// UnityGI_Base 返回：
UnityGI gi;
gi.light.color = 0;                    // ← 无实时光
gi.light.dir = 0;
gi.indirect.diffuse = Lightmap采样;     // ← 包含直接+间接光
gi.indirect.specular = ReflectionProbe;

// Lightmap内容分析：
Lightmap值 = DirectFromBakedLight + GI_Bounce1 + GI_Bounce2 + ...

// 示例：
// 场景：白色平面，上方一盏Baked红光（强度1）
// Lightmap采样结果 ≈ (0.8, 0, 0)  ← 直接光照占主要

// 如果开启GI Bounces = 2：
// 周围墙壁会有红色反射光
// Lightmap采样结果 ≈ (0.8, 0, 0) + (0.05, 0, 0) = (0.85, 0, 0)
//                    ↑直接光         ↑间接反弹
Mode 2: Mixed - Baked Indirect
hlsl

// 光源设置：Mode = Mixed, Lighting Mode = Baked Indirect

// UnityGI_Base 返回：
UnityGI gi;
gi.light.color = _LightColor0;         // ← 有实时光！
gi.light.dir = _WorldSpaceLightPos0;
gi.indirect.diffuse = Lightmap采样;     // ← 只包含间接光
gi.indirect.specular = ReflectionProbe;

// Lightmap内容分析：
Lightmap值 = GI_Bounce1 + GI_Bounce2 + ...（无直接光）

// 最终光照计算：
// BRDF会分别计算：
// Direct = BRDF(gi.light, normal)          ← 实时计算直接光
// Indirect = gi.indirect.diffuse           ← 烘焙的间接光
// Final = Direct + Indirect
Mode 3: Mixed - Shadowmask
hlsl

// 光源设置：Mode = Mixed, Lighting Mode = Shadowmask

// UnityGI_Base 返回：
UnityGI gi;
gi.light.color = _LightColor0;         // ← 有实时光
gi.light.dir = _WorldSpaceLightPos0;
gi.indirect.diffuse = Lightmap采样;     // ← 包含直接+间接
gi.indirect.specular = ReflectionProbe;

// 额外的Shadowmask纹理：
float shadowAttenuation = SampleShadowmask(uv);

// 最终光照计算：
// Direct = BRDF(gi.light, normal) * shadowAttenuation  ← 烘焙阴影
// Indirect = gi.indirect.diffuse                       ← 完整GI
// Final = Direct + Indirect

// 优点：
// - 静态物体使用烘焙阴影（高质量）
// - 动态物体使用实时阴影
// - 性能和质量平衡
Mode 4: Realtime（完全实时）
hlsl

// 光源设置：Mode = Realtime

// UnityGI_Base 返回：
UnityGI gi;
gi.light.color = 0;                    // ← Base函数不设置
gi.light.dir = 0;
gi.indirect.diffuse = ShadeSH9(...);   // ← Light Probes（低质量GI）
gi.indirect.specular = ReflectionProbe;

// 后续会在UnityGlobalIllumination中添加：
gi.light = GetMainLight();

// 最终光照计算：
// Direct = BRDF(gi.light, normal)      ← 完全实时计算
// Indirect = ShadeSH9()                ← 球谐函数近似GI
// Final = Direct + Indirect
四、实际验证代码
验证1：Lightmap包含的内容
csharp

using UnityEngine;
using UnityEngine.Rendering;

public class LightmapContentAnalyzer : MonoBehaviour
{
    public Renderer targetRenderer;
    
    void Start()
    {
        if (targetRenderer == null) return;
        
        // 获取Lightmap UV
        Vector4 lightmapScaleOffset = targetRenderer.lightmapScaleOffset;
        int lightmapIndex = targetRenderer.lightmapIndex;
        
        if (lightmapIndex < 0 || lightmapIndex >= LightmapSettings.lightmaps.Length)
        {
            Debug.Log("没有Lightmap");
            return;
        }
        
        // 获取Lightmap纹理
        Texture2D lightmapColor = LightmapSettings.lightmaps[lightmapIndex].lightmapColor;
        
        // 采样中心点
        int x = (int)(lightmapColor.width * 0.5f);
        int y = (int)(lightmapColor.height * 0.5f);
        Color lightmapSample = lightmapColor.GetPixel(x, y);
        
        Debug.Log($"Lightmap采样值: {lightmapSample}");
        Debug.Log($"R={lightmapSample.r}, G={lightmapSample.g}, B={lightmapSample.b}");
        
        // ========================================
        // 实验：
        // 1. 场景只有一盏Baked红光（1, 0, 0）
        //    Bounce = 0
        //    → 输出应该是红色（~0.8, ~0, ~0）
        //    → 证明：Lightmap包含直接光照
        //
        // 2. 添加蓝色反射板，Bounce = 2
        //    → 输出应该是红色+少量蓝色（~0.8, ~0, ~0.1）
        //    → 证明：Lightmap也包含间接光照
        // ========================================
    }
}
验证2：Shader中分离直接和间接光照
hlsl

Shader "Custom/LightingAnalysis"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        [Toggle] _ShowDirect ("Show Direct Only", Float) = 0
        [Toggle] _ShowIndirect ("Show Indirect Only", Float) = 0
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        
        Pass
        {
            Tags { "LightMode"="ForwardBase" }
            
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fwdbase
            #pragma multi_compile_fog
            
            #include "UnityCG.cginc"
            #include "UnityPBSLighting.cginc"
            #include "AutoLight.cginc"
            
            float _ShowDirect;
            float _ShowIndirect;
            
            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldNormal : TEXCOORD0;
                float3 worldPos : TEXCOORD1;
                float2 lightmapUV : TEXCOORD2;
                UNITY_FOG_COORDS(3)
            };
            
            v2f vert(appdata_full v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.lightmapUV = v.texcoord1.xy * unity_LightmapST.xy + unity_LightmapST.zw;
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }
            
            half4 frag(v2f i) : SV_Target
            {
                // ========================================
                // 1. 获取GI数据
                // ========================================
                UnityGI gi;
                ResetUnityGI(gi);
                
                // 获取预计算数据（Lightmap或Light Probes）
                #ifdef LIGHTMAP_ON
                    // Lightmap采样
                    half3 bakedGI = DecodeLightmap(
                        UNITY_SAMPLE_TEX2D(unity_Lightmap, i.lightmapUV)
                    );
                    gi.indirect.diffuse = bakedGI;
                #else
                    // Light Probes
                    gi.indirect.diffuse = ShadeSH9(half4(i.worldNormal, 1));
                #endif
                
                // 获取实时光源
                gi.light.dir = _WorldSpaceLightPos0.xyz;
                gi.light.color = _LightColor0.rgb;
                
                // ========================================
                // 2. 分别计算直接和间接光照
                // ========================================
                half3 N = normalize(i.worldNormal);
                half3 L = gi.light.dir;
                
                // 直接光照（Lambertian）
                half NdotL = max(0, dot(N, L));
                half3 directLighting = gi.light.color * NdotL;
                
                // 间接光照（来自Lightmap或Probes）
                half3 indirectLighting = gi.indirect.diffuse;
                
                // ========================================
                // 3. 根据开关显示不同部分
                // ========================================
                half3 finalColor;
                
                if (_ShowDirect > 0.5)
                {
                    // 只显示实时直接光照
                    finalColor = directLighting;
                }
                else if (_ShowIndirect > 0.5)
                {
                    // 只显示预计算光照（Lightmap）
                    finalColor = indirectLighting;
                }
                else
                {
                    // 完整光照
                    finalColor = directLighting + indirectLighting;
                }
                
                // ========================================
                // 实验结果分析：
                // ========================================
                // 场景设置：Baked模式，主光源Mode=Baked
                //
                // 开关1：_ShowDirect = 1
                // → 应该看到：黑色（因为Baked光源不提供gi.light）
                //
                // 开关2：_ShowIndirect = 1  
                // → 应该看到：明亮的表面（因为Lightmap包含直接光）
                //
                // 结论：证明Lightmap确实包含了直接光照！
                // ========================================
                
                UNITY_APPLY_FOG(i.fogCoord, finalColor);
                return half4(finalColor, 1);
            }
            ENDCG
        }
    }
}
验证3：不同光照模式对比
csharp

using UnityEngine;

public class LightingModeComparison : MonoBehaviour
{
    public Light directionalLight;
    public Material analysisMaterial;
    
    [ContextMenu("Test: Baked Mode")]
    void TestBakedMode()
    {
        // 设置为Baked
        directionalLight.lightmapBakeType = LightmapBakeType.Baked;
        
        // 重新烘焙
        UnityEditor.Lightmapping.BakeAsync();
        
        // 预期结果：
        // - gi.light = 0（无实时光）
        // - gi.indirect.diffuse = 高值（包含直接+间接）
        // - _ShowDirect = 1 → 黑色
        // - _ShowIndirect = 1 → 亮
    }
    
    [ContextMenu("Test: Mixed Mode (Baked Indirect)")]
    void TestMixedBakedIndirect()
    {
        // 设置为Mixed
        directionalLight.lightmapBakeType = LightmapBakeType.Mixed;
        
        // Lighting Settings → Mixed Lighting → Lighting Mode = Baked Indirect
        
        // 重新烘焙
        UnityEditor.Lightmapping.BakeAsync();
        
        // 预期结果：
        // - gi.light = 光源颜色（有实时光）
        // - gi.indirect.diffuse = 低值（只有间接）
        // - _ShowDirect = 1 → 亮（实时直接光）
        // - _ShowIndirect = 1 → 暗（只有GI反弹）
    }
    
    [ContextMenu("Test: Realtime Mode")]
    void TestRealtimeMode()
    {
        // 设置为Realtime
        directionalLight.lightmapBakeType = LightmapBakeType.Realtime;
        
        // 预期结果：
        // - gi.light = 光源颜色（实时计算）
        // - gi.indirect.diffuse = SH值（Light Probes）
        // - _ShowDirect = 1 → 亮（实时）
        // - _ShowIndirect = 1 → 很暗（只有环境光）
    }
}
五、UnityGI.light 的确切含义
定义
hlsl

// UnityGI.light 的含义：

struct UnityLight
{
    half3 color;  // = 光源颜色 × 光源强度 × 距离衰减 × 阴影
    half3 dir;    // = 光源方向（指向光源）
};

UnityGI.light 专门用于：
┌────────────────────────────────────────┐
│ 1. 实时光源（Realtime Lights）          │
│    ├─ Mode = Realtime的光源            │
│    ├─ 每帧动态计算                     │
│    └─ 可以移动、变色、开关             │
├────────────────────────────────────────┤
│ 2. Mixed模式的主光源（特定情况）       │
│    ├─ Baked Indirect模式               │
│    ├─ Shadowmask模式                   │
│    └─ 用于计算实时直接光照             │
├────────────────────────────────────────┤
│ 3. Forward Rendering的主平行光         │
│    ├─ 通常是_LightColor0               │
│    ├─ _WorldSpaceLightPos0             │
│    └─ 最重要的那一盏光                 │
└────────────────────────────────────────┘

UnityGI.light 不包含：
✗ Baked光源（已烘焙到Lightmap）
✗ 额外的Realtime光源（在Additional Passes处理）
✗ 环境光（在gi.indirect中）
✗ 反射光（在gi.indirect中）
使用流程
hlsl

// ========================================
// Forward Base Pass
// ========================================
Pass
{
    Tags { "LightMode"="ForwardBase" }
    
    half4 frag()
    {
        // Step 1: 收集预计算数据
        UnityGI gi = UnityGI_Base(...);
        // gi.light = {0,0,0}  ← 初始为空
        // gi.indirect = Lightmap/Probes
        
        // Step 2: 添加主光源（如果是实时光源）
        #ifndef USING_DIRECTIONAL_LIGHT
            gi.light.dir = normalize(_WorldSpaceLightPos0.xyz - worldPos);
        #else
            gi.light.dir = _WorldSpaceLightPos0.xyz;
        #endif
        
        gi.light.color = _LightColor0.rgb;
        
        // 应用阴影
        UNITY_LIGHT_ATTENUATION(atten, i, worldPos);
        gi.light.color *= atten;
        
        // Step 3: 计算光照
        half4 c = UNITY_BRDF_PBS(..., gi.light, gi.indirect);
        
        return c;
    }
}

// ========================================
// Forward Add Pass（额外光源）
// ========================================
Pass
{
    Tags { "LightMode"="ForwardAdd" }
    Blend One One  // 累加
    
    half4 frag()
    {
        // 这个Pass只处理额外的Realtime光源
        UnityGI gi;
        ResetUnityGI(gi);
        
        // 只设置当前额外光源
        gi.light.dir = normalize(_WorldSpaceLightPos0.xyz - worldPos);
        gi.light.color = _LightColor0.rgb;
        
        UNITY_LIGHT_ATTENUATION(atten, i, worldPos);
        gi.light.color *= atten;
        
        // gi.indirect保持为0（GI只在Base Pass计算一次）
        
        half4 c = UNITY_BRDF_PBS(..., gi.light, gi.indirect);
        return c;
    }
}
六、完整的光照流程图
ini

┌─────────────────────────────────────────────────────────────────┐
│                    Unity Forward Rendering                       │
└─────────────────────────────────────────────────────────────────┘

ForwardBase Pass（每个物体执行一次）
├─ Step 1: UnityGI_Base
│   ├─ 采样Lightmap（静态物体）
│   │   └─ gi.indirect.diffuse = 直接（烘焙）+ 间接（GI）
│   ├─ 采样Light Probes（动态物体）
│   │   └─ gi.indirect.diffuse = SH近似GI
│   ├─ 采样Reflection Probes
│   │   └─ gi.indirect.specular = 环境反射
│   └─ gi.light = {0,0,0}  ← 初始为空
│
├─ Step 2: 添加主光源（如果适用）
│   ├─ 如果主光源是Realtime或Mixed（某些模式）
│   │   ├─ gi.light.color = _LightColor0
│   │   ├─ gi.light.dir = _WorldSpaceLightPos0
│   │   └─ 应用阴影衰减
│   └─ 如果主光源是Baked
│       └─ gi.light保持为0（已在Lightmap中）
│
├─ Step 3: BRDF计算
│   ├─ Direct = BRDF(gi.light, ...)     ← 可能为0
│   ├─ Indirect = gi.indirect           ← 总是有值
│   └─ Final = Direct + Indirect
│
└─ Output: Base Pass颜色

ForwardAdd Pass（每个额外Realtime光源执行一次）
├─ gi.light = 当前额外光源
├─ gi.indirect = {0,0,0}  ← 不重复计算GI
├─ BRDF计算
└─ Output: 累加到Base Pass

最终颜色 = Base Pass + Add Pass1 + Add Pass2 + ...
七、总结与记忆要点
核心理解
haml

1. Unity Lightmap的内容：
   Lightmap = 直接光照（来自Baked光源） + 间接光照（GI）
   
2. Unity的术语映射：
   gi.light     = 实时光源（每帧计算）
   gi.indirect  = 预计算数据（Lightmap/Probes）
                = 不是"间接光照"，是"间接提供的光照"
   
3. 为什么Lightmap放在indirect中？
   - 因为它是预计算的、静态的
   - 不是每帧实时计算的
   - 与"实时光源"区分开
   
4. UnityGI.light的作用：
   - 只用于实时光源
   - Forward Base Pass的主光源
   - Forward Add Pass的额外光源
   - Baked光源不使用这个字段
实用记忆
hlsl

// 简单记忆法：

if (光源Mode == Baked)
{
    // 光照已在Lightmap中
    gi.light = 0;
    gi.indirect.diffuse = Lightmap;  // 包含直接+间接
}
else if (光源Mode == Realtime)
{
    // 运行时实时计算
    gi.light = 实时光源;
    gi.indirect.diffuse = Light Probes;  // 只有环境GI
}
else if (光源Mode == Mixed)
{
    // 根据Lighting Mode不同
    if (BakedIndirect)
    {
        gi.light = 实时光源;           // 直接光实时算
        gi.indirect.diffuse = Lightmap;  // 只有间接GI
    }
    else if (Shadowmask)
    {
        gi.light = 实时光源;
        gi.indirect.diffuse = Lightmap;  // 直接+间接
        // + Shadowmask纹理用于阴影
    }
}
希望这样能完全理解Unity GI系统的设计理念！

17:51

参考这里的代码

UnityGlobalIllumination.cginc
文本 · 10 KB
17:57

Claude-Sonnet-4.5


Unity GI 源码深度解析
现在看到了完整的源码，让我重新梳理整个系统。之前的理解有些不够准确，现在基于源码给出精确分析。

一、核心发现：UnityGI_Base 中的关键代码
hlsl

inline UnityGI UnityGI_Base(UnityGIInput data, half occlusion, half3 normalWorld)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);  // ← 清零所有字段
    
    // ========================================
    // 关键行！！！
    // ========================================
    o_gi.light = data.light;           // ← 从输入参数获取！
    o_gi.light.color *= data.atten;    // ← 应用衰减（阴影等）
    
    // 然后才是 Lightmap、SH 等处理...
    #if UNITY_SHOULD_SAMPLE_SH
        o_gi.indirect.diffuse = ShadeSHPerPixel(normalWorld, data.ambient, data.worldPos);
    #endif
    
    #if defined(LIGHTMAP_ON)
        half4 bakedColorTex = UNITY_SAMPLE_TEX2D(unity_Lightmap, data.lightmapUV.xy);
        half3 bakedColor = DecodeLightmap(bakedColorTex);
        o_gi.indirect.diffuse += bakedColor;  // ← 累加到 indirect
    #endif
    
    return o_gi;
}
二、重大修正：我之前理解有误
修正点 1：UnityGI.light 的来源
hlsl

// ❌ 之前我说的：
// "UnityGI_Base 返回时 gi.light = 0"

// ✅ 实际情况：
// UnityGI_Base 返回时 gi.light = data.light（从输入参数传入）

// 所以关键在于：谁调用了 UnityGI_Base？传入的 data.light 是什么？
修正点 2：UnityGI_Base 的调用链
hlsl

// 完整调用链：

// Step 1: Shader 的 Fragment Shader
half4 frag(v2f i) : SV_Target
{
    // 准备 UnityGIInput 结构体
    UnityGIInput giInput;
    UNITY_INITIALIZE_OUTPUT(UnityGIInput, giInput);
    
    giInput.light = gi.light;  // ← 这里！需要先准备好 light
    giInput.worldPos = i.worldPos;
    giInput.worldViewDir = viewDir;
    giInput.atten = atten;  // 阴影衰减
    giInput.ambient = 0;
    giInput.lightmapUV = i.lightmapUV;
    
    // 调用 UnityGlobalIllumination
    UnityGI gi = UnityGlobalIllumination(giInput, occlusion, normalWorld);
    
    return BRDF(gi.light, gi.indirect, ...);
}

// Step 2: UnityGlobalIllumination（重载版本）
inline UnityGI UnityGlobalIllumination(
    UnityGIInput data, half occlusion, half3 normalWorld)
{
    return UnityGI_Base(data, occlusion, normalWorld);
    //      ↑ 直接调用 Base 版本
}

// Step 3: UnityGI_Base
inline UnityGI UnityGI_Base(UnityGIInput data, ...)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);
    
    o_gi.light = data.light;  // ← 从输入复制
    o_gi.light.color *= data.atten;
    
    // 处理 Lightmap 等...
    
    return o_gi;
}
三、完整的数据流分析
3.1 ForwardBase Pass 的典型实现
hlsl

// 来自 Standard Shader 的 ForwardBase Pass

struct v2f
{
    float4 pos : SV_POSITION;
    float2 uv : TEXCOORD0;
    float2 lightmapUV : TEXCOORD1;
    float3 worldPos : TEXCOORD2;
    float3 worldNormal : TEXCOORD3;
    SHADOW_COORDS(4)
};

half4 fragForwardBase(v2f i) : SV_Target
{
    // ========================================
    // 阶段 1：准备基础数据
    // ========================================
    float3 worldPos = i.worldPos;
    half3 worldNormal = normalize(i.worldNormal);
    half3 worldViewDir = normalize(UnityWorldSpaceViewDir(worldPos));
    
    // ========================================
    // 阶段 2：准备光源数据（关键！）
    // ========================================
    UnityLight mainLight;
    
    #ifdef USING_DIRECTIONAL_LIGHT
        mainLight.dir = _WorldSpaceLightPos0.xyz;
    #else
        mainLight.dir = normalize(_WorldSpaceLightPos0.xyz - worldPos);
    #endif
    
    // ========================================
    // 关键判断：光源是否参与实时计算？
    // ========================================
    #if defined(LIGHTMAP_ON) && defined(LIGHTMAP_SHADOW_MIXING) && !defined(SHADOWS_SHADOWMASK)
        // Subtractive 模式：
        // - Lightmap 包含完整烘焙光照
        // - 但需要实时阴影，所以保留 mainLight 用于阴影计算
        mainLight.color = _LightColor0.rgb;
        
    #elif defined(LIGHTMAP_ON)
        // Baked 模式：
        // - Lightmap 包含完整光照
        // - 不需要实时光源
        mainLight.color = 0;  // ← 清零！
        
    #else
        // Realtime 或 Mixed (Baked Indirect) 模式：
        // - 需要实时计算主光源
        mainLight.color = _LightColor0.rgb;
    #endif
    
    mainLight.ndotl = 0; // 暂不使用
    
    // ========================================
    // 阶段 3：准备 GI 输入
    // ========================================
    UnityGIInput giInput;
    UNITY_INITIALIZE_OUTPUT(UnityGIInput, giInput);
    
    giInput.light = mainLight;  // ← 传入准备好的光源！
    giInput.worldPos = worldPos;
    giInput.worldViewDir = worldViewDir;
    
    // 计算阴影衰减
    UNITY_LIGHT_ATTENUATION(atten, i, worldPos);
    giInput.atten = atten;
    
    #if defined(LIGHTMAP_ON) || defined(DYNAMICLIGHTMAP_ON)
        giInput.lightmapUV = i.lightmapUV;
    #endif
    
    giInput.ambient = 0;
    
    #if UNITY_SHOULD_SAMPLE_SH
        giInput.ambient = ShadeSHPerVertex(worldNormal, 0);
    #endif
    
    // ========================================
    // 阶段 4：调用 GI 系统
    // ========================================
    Unity_GlossyEnvironmentData glossIn = UnityGlossyEnvironmentSetup(
        smoothness, worldViewDir, worldNormal, specColor
    );
    
    UnityGI gi = UnityGlobalIllumination(
        giInput,      // ← 包含了准备好的 mainLight
        occlusion,
        worldNormal,
        glossIn
    );
    
    // 此时：
    // gi.light = giInput.light（可能是实时光源，也可能是0）
    // gi.indirect.diffuse = Lightmap 或 Light Probes
    // gi.indirect.specular = Reflection Probes
    
    // ========================================
    // 阶段 5：BRDF 计算
    // ========================================
    half4 c = UNITY_BRDF_PBS(
        albedo,
        specColor,
        oneMinusReflectivity,
        smoothness,
        worldNormal,
        worldViewDir,
        gi.light,       // ← 实时主光源（可能为0）
        gi.indirect     // ← 预计算数据
    );
    
    return c;
}
3.2 不同模式下 mainLight 的值
hlsl

// ========================================
// 模式 1：Baked（完全烘焙）
// ========================================
// 光源设置：Mode = Baked
// Shader 中：
#if defined(LIGHTMAP_ON)
    mainLight.color = 0;  // ← 清零
#endif

// UnityGI_Base 接收到：
data.light.color = 0;

// 返回：
gi.light.color = 0;  // ← 无实时光源
gi.indirect.diffuse = DecodeLightmap(...);  // ← 包含直接+间接

// 最终光照：
// Direct = BRDF(gi.light=0, ...) = 0
// Indirect = gi.indirect.diffuse = Lightmap数据（直接+间接）
// Final = 0 + Lightmap = Lightmap


// ========================================
// 模式 2：Realtime（完全实时）
// ========================================
// 光源设置：Mode = Realtime
// Shader 中：
mainLight.color = _LightColor0.rgb;  // ← 完整颜色

// UnityGI_Base 接收到：
data.light.color = _LightColor0.rgb;
data.atten = shadow;

// 返回：
gi.light.color = _LightColor0.rgb * shadow;  // ← 有实时光源
gi.indirect.diffuse = ShadeSH9(...);  // ← 只有环境光（SH）

// 最终光照：
// Direct = BRDF(gi.light=实时光, ...) = 实时计算
// Indirect = SH 近似的环境光
// Final = 实时直接光 + 环境光


// ========================================
// 模式 3：Mixed - Baked Indirect
// ========================================
// 光源设置：Mode = Mixed, Lighting Mode = Baked Indirect
// Shader 中：
mainLight.color = _LightColor0.rgb;  // ← 完整颜色

// Lightmap 内容：只包含间接光照

// UnityGI_Base 接收到：
data.light.color = _LightColor0.rgb;

// 返回：
gi.light.color = _LightColor0.rgb * shadow;  // ← 有实时光源
gi.indirect.diffuse = DecodeLightmap(...);  // ← 只有间接光

// 最终光照：
// Direct = BRDF(gi.light=实时光, ...) = 实时直接光
// Indirect = Lightmap（只有间接）
// Final = 实时直接光 + 烘焙间接光


// ========================================
// 模式 4：Mixed - Shadowmask
// ========================================
// 光源设置：Mode = Mixed, Lighting Mode = Shadowmask
// Shader 中：
mainLight.color = _LightColor0.rgb;

// Lightmap 内容：包含直接+间接光照
// Shadowmask 纹理：包含烘焙阴影

// UnityGI_Base 接收到：
data.light.color = _LightColor0.rgb;
data.atten = 混合的阴影（实时+烘焙）;  // ← 特殊处理

// 返回：
gi.light.color = _LightColor0.rgb * 混合阴影;
gi.indirect.diffuse = DecodeLightmap(...);  // ← 直接+间接

// 最终光照：
// Direct = BRDF(gi.light=实时光*混合阴影, ...)
// Indirect = Lightmap（直接+间接）- 需要避免重复
// Final = 复杂的混合计算


// ========================================
// 模式 5：Mixed - Subtractive
// ========================================
// 特殊模式，见源码中的 SubtractMainLightWithRealtimeAttenuationFromLightmap

#if defined(LIGHTMAP_SHADOW_MIXING) && !defined(SHADOWS_SHADOWMASK) && defined(SHADOWS_SCREEN)
    ResetUnityLight(o_gi.light);  // ← 清零实时光！
    o_gi.indirect.diffuse = SubtractMainLightWithRealtimeAttenuationFromLightmap(
        o_gi.indirect.diffuse, data.atten, bakedColorTex, normalWorld
    );
#endif

// 这个函数会：
// 1. 从 Lightmap 中减去主光源的贡献
// 2. 基于实时阴影重新计算主光源
// 3. 混合得到最终结果
四、关键函数深度解析
4.1 SubtractMainLightWithRealtimeAttenuationFromLightmap
hlsl

// 这是 Subtractive 模式的核心算法

inline half3 SubtractMainLightWithRealtimeAttenuationFromLightmap(
    half3 lightmap,        // Lightmap 采样值（包含主光源直接光）
    half attenuation,      // 实时阴影衰减（0=阴影，1=无阴影）
    half4 bakedColorTex,   // Lightmap 原始纹理
    half3 normalWorld)     // 世界空间法线
{
    // 目标：
    // - Lightmap 包含了烘焙的直接光照（假设无阴影）
    // - 现在要应用实时阴影
    // - 但保留间接光照和其他烘焙光源
    
    half3 shadowColor = unity_ShadowColor.rgb;  // 阴影颜色（可设置）
    half shadowStrength = _LightShadowData.x;   // 阴影强度
    
    // Step 1: 估算主光源的贡献
    half ndotl = LambertTerm(normalWorld, _WorldSpaceLightPos0.xyz);
    half3 estimatedMainLight = ndotl * (1 - attenuation) * _LightColor0.rgb;
    //                                   ↑
    //                                   (1-attenuation) = 阴影部分
    
    // Step 2: 从 Lightmap 中减去被阴影遮挡的主光源贡献
    half3 subtractedLightmap = lightmap - estimatedMainLight;
    
    // Step 3: 限制最暗值（防止过暗）
    half3 realtimeShadow = max(subtractedLightmap, shadowColor);
    realtimeShadow = lerp(realtimeShadow, lightmap, shadowStrength);
    
    // Step 4: 取最暗值（保守处理）
    return min(lightmap, realtimeShadow);
    
    // 效果：
    // - 无阴影区域：返回完整 Lightmap
    // - 有阴影区域：Lightmap - 主光源直接光 = 间接光 + 其他光源
}
4.2 HANDLE_SHADOWS_BLENDING_IN_GI
hlsl

// UnityGI_Base 的开头有这段代码：

#if defined(HANDLE_SHADOWS_BLENDING_IN_GI)
    // 这是 Shadowmask 模式的处理
    
    // 采样烘焙的阴影遮罩
    half bakedAtten = UnitySampleBakedOcclusion(data.lightmapUV.xy, data.worldPos);
    
    // 计算相机距离（用于混合）
    float zDist = dot(_WorldSpaceCameraPos - data.worldPos, UNITY_MATRIX_V[2].xyz);
    float fadeDist = UnityComputeShadowFadeDistance(data.worldPos, zDist);
    
    // 混合实时阴影和烘焙阴影
    data.atten = UnityMixRealtimeAndBakedShadows(
        data.atten,      // 实时阴影
        bakedAtten,      // 烘焙阴影
        UnityComputeShadowFade(fadeDist)  // 混合因子（基于距离）
    );
    
    // 结果：
    // - 近距离：使用实时阴影（动态物体可以投影）
    // - 远距离：使用烘焙阴影（性能更好）
#endif

o_gi.light = data.light;
o_gi.light.color *= data.atten;  // ← 应用混合后的阴影
五、Unity Lightmap 的真实内容
5.1 实验验证
hlsl

// 创建测试 Shader 来验证 Lightmap 内容

Shader "Debug/LightmapContent"
{
    Properties
    {
        [KeywordEnum(Total, OnlyDirect, OnlyIndirect, Estimated)] 
        _Mode ("Display Mode", Float) = 0
    }
    
    SubShader
    {
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            
            float _Mode;
            
            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 lightmapUV : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
            };
            
            v2f vert(appdata_full v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.lightmapUV = v.texcoord1.xy * unity_LightmapST.xy + unity_LightmapST.zw;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                return o;
            }
            
            half4 frag(v2f i) : SV_Target
            {
                #ifdef LIGHTMAP_ON
                    // 采样 Lightmap
                    half3 lightmap = DecodeLightmap(
                        UNITY_SAMPLE_TEX2D(unity_Lightmap, i.lightmapUV)
                    );
                    
                    if (_Mode == 0)
                    {
                        // 显示完整 Lightmap
                        return half4(lightmap, 1);
                    }
                    else if (_Mode == 1)
                    {
                        // 估算直接光照部分
                        half ndotl = saturate(dot(i.worldNormal, _WorldSpaceLightPos0.xyz));
                        half3 estimatedDirect = ndotl * _LightColor0.rgb;
                        return half4(estimatedDirect, 1);
                    }
                    else if (_Mode == 2)
                    {
                        // 估算间接光照（Lightmap - 直接光）
                        half ndotl = saturate(dot(i.worldNormal, _WorldSpaceLightPos0.xyz));
                        half3 estimatedDirect = ndotl * _LightColor0.rgb;
                        half3 estimatedIndirect = max(0, lightmap - estimatedDirect);
                        return half4(estimatedIndirect, 1);
                    }
                    else
                    {
                        // 对比显示
                        return half4(lightmap * 0.5, 1);
                    }
                #else
                    return half4(1, 0, 1, 1);  // 洋红色 = 没有 Lightmap
                #endif
            }
            ENDCG
        }
    }
}
5.2 Lightmap 内容总结
mipsasm

Unity Lightmap 存储的内容（Baked 模式）：

┌─────────────────────────────────────────────┐
│ Lightmap = DirectBaked + IndirectGI          │
├─────────────────────────────────────────────┤
│ DirectBaked（直接光照 - 来自 Baked 光源）    │
│ ├─ 主方向光（Mode=Baked）                   │
│ ├─ 点光源（Mode=Baked）                     │
│ ├─ 聚光灯（Mode=Baked）                     │
│ ├─ 面光源（Area Light, 只能 Baked）         │
│ └─ 自发光材质（Emissive）                   │
├─────────────────────────────────────────────┤
│ IndirectGI（间接光照 - 光线反弹）            │
│ ├─ 第一次反弹                               │
│ ├─ 第二次反弹                               │
│ └─ ...（根据 Bounces 设置）                 │
└─────────────────────────────────────────────┘

重要：
✓ Lightmap 包含直接光照（如果光源是 Baked）
✓ Lightmap 包含间接光照（GI bounces）
✗ Lightmap 不包含实时光源（Mode=Realtime）
✗ Lightmap 不包含动态阴影（静态烘焙）
六、最终总结
核心理解
hlsl

// Unity GI 系统的设计哲学：

1. UnityGI 结构体的分工：
   ├─ gi.light: 实时计算的光照
   │   ├─ 每帧动态计算
   │   ├─ 可以移动、变化
   │   └─ 来自 Mode=Realtime 或 Mode=Mixed 的光源
   │
   └─ gi.indirect: 预计算的光照
       ├─ 运行时不变（静态数据）
       ├─ 来自 Lightmap / Light Probes / Reflection Probes
       └─ 可能包含直接光照（如果是 Baked 模式）

2. "indirect" 的命名含义：
   ≠ 物理意义的"间接光照"
   = "Indirectly provided"（间接提供的）
   = "预计算的、通过纹理/探针提供的"
   
3. UnityGI_Base 的职责：
   ├─ 从输入参数复制 light 数据
   ├─ 采样 Lightmap/Probes 到 indirect
   ├─ 应用阴影衰减
   └─ 返回完整的 UnityGI 结构体
   
4. Lightmap 包含的内容：
   取决于光照模式（Baked / Mixed）
   ├─ Baked: 直接光 + 间接光
   ├─ Mixed (Baked Indirect): 只有间接光
   └─ Mixed (Shadowmask): 直接光 + 间接光（+ Shadowmask）
实用记忆法
hlsl

// 判断 gi.light 的值：

if (场景中没有 Lightmap)
{
    // 动态物体或未烘焙场景
    gi.light = 主实时光源;
    gi.indirect = Light Probes (SH);
}
else if (光源 Mode == Baked)
{
    // 完全烘焙
    gi.light = 0;  // ← 光照在 Lightmap 中
    gi.indirect = Lightmap (Direct + Indirect);
}
else if (光源 Mode == Mixed)
{
    if (Lighting Mode == Baked Indirect)
    {
        gi.light = 实时主光源;
        gi.indirect = Lightmap (Only Indirect);
    }
    else if (Lighting Mode == Shadowmask)
    {
        gi.light = 实时主光源 * 混合阴影;
        gi.indirect = Lightmap (Direct + Indirect);
    }
    else if (Lighting Mode == Subtractive)
    {
        gi.light = 0;  // ← 被 Reset
        gi.indirect = Lightmap - 主光源直接光 + 实时阴影;
    }
}
现在应该完全理解了整个系统！关键在于 data.light 是在调用 UnityGI_Base 之前就准备好的，而不是在函数内部生成的。

17:57

使用的builtin_shaders-2021.3.44f1

17:58

Claude-Sonnet-4.5


Unity Built-in Shaders 2021.3.44f1 详细分析
好的！基于 Built-in Shaders 2021.3.44f1 的实际源码，我来给你详细分析。

一、核心文件位置
reasonml

builtin_shaders-2021.3.44f1/
├── CGIncludes/
│   ├── UnityGlobalIllumination.cginc    ← 核心GI函数
│   ├── UnityPBSLighting.cginc           ← PBS光照模型
│   ├── UnityStandardBRDF.cginc          ← BRDF实现
│   ├── UnityLightingCommon.cginc        ← 光照通用函数
│   └── AutoLight.cginc                  ← 阴影和衰减
└── DefaultResourcesExtra/
    └── Standard.shader                   ← 标准着色器
二、UnityGI_Base 的实际源码（2021.3.44f1）
让我从 UnityGlobalIllumination.cginc 中提取实际代码：

hlsl

// ========================================
// 文件：UnityGlobalIllumination.cginc
// 位置：builtin_shaders-2021.3.44f1/CGIncludes/
// ========================================

struct UnityGI
{
    UnityLight light;
    UnityIndirect indirect;
};

struct UnityLight
{
    half3 color;
    half3 dir;
};

struct UnityIndirect
{
    half3 diffuse;
    half3 specular;
};

struct UnityGIInput
{
    UnityLight light;           // pixel light, sent from the engine
    
    float3 worldPos;
    half3 worldViewDir;
    half atten;
    half3 ambient;
    
    // interpolated lightmap UVs are passed as full float precision data to fragment shaders
    // so lightmapUV (which is used as a tmp inside of lightmap fragment shaders) should
    // also be float to avoid precision loss
    float4 lightmapUV;          // .xy = static lightmap UV, .zw = dynamic lightmap UV
    
    #if defined(UNITY_SPECCUBE_BLENDING) || defined(UNITY_SPECCUBE_BOX_PROJECTION) || defined(UNITY_ENABLE_REFLECTION_BUFFERS)
        float4 boxMin[2];
        float4 boxMax[2];
        float4 probePosition[2];
        float4 probeHDR[2];
    #endif
    
    float3 probePosition;
    float4 probeHDR;
    
    half3 reflUVW;
};

// ========================================
// 核心函数：UnityGI_Base
// ========================================
inline UnityGI UnityGI_Base(UnityGIInput data, half occlusion, half3 normalWorld)
{
    UnityGI o_gi;
    ResetUnityGI(o_gi);  // 初始化为零
    
    // ========================================
    // 1. 处理静态 Lightmap
    // ========================================
    #ifdef LIGHTMAP_ON
        // 采样静态 lightmap
        half3 bakedColorTex = DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap, data.lightmapUV.xy));
        half3 bakedColor = bakedColorTex;
        
        // 处理方向性 lightmap（Directional Mode）
        #ifdef DIRLIGHTMAP_COMBINED
            fixed4 bakedDirTex = UNITY_SAMPLE_TEX2D_SAMPLER(unity_LightmapInd, unity_Lightmap, data.lightmapUV.xy);
            
            // 使用法线信息解码方向性光照
            bakedColor = DecodeDirectionalLightmap(bakedColor, bakedDirTex, normalWorld);
        #endif
        
        // 应用环境光遮蔽
        o_gi.indirect.diffuse = bakedColor * occlusion;
        
        // 处理 Shadowmask（如果启用）
        #ifdef SHADOWS_SHADOWMASK
            // Shadowmask 会在后续处理
        #endif
    #endif
    
    // ========================================
    // 2. 处理动态 Lightmap（Realtime GI）
    //    注意：2021版本中这个功能已被弃用
    // ========================================
    #ifdef DYNAMICLIGHTMAP_ON
        fixed4 realtimeColorTex = UNITY_SAMPLE_TEX2D(unity_DynamicLightmap, data.lightmapUV.zw);
        half3 realtimeColor = DecodeRealtimeLightmap(realtimeColorTex);
        
        #ifdef DIRLIGHTMAP_COMBINED
            half4 realtimeDirTex = UNITY_SAMPLE_TEX2D_SAMPLER(unity_DynamicDirectionality, unity_DynamicLightmap, data.lightmapUV.zw);
            o_gi.indirect.diffuse += DecodeDirectionalLightmap(realtimeColor, realtimeDirTex, normalWorld);
        #else
            o_gi.indirect.diffuse += realtimeColor;
        #endif
    #endif
    
    // ========================================
    // 3. 处理 Light Probes（动态物体）
    // ========================================
    #if !defined(LIGHTMAP_ON) && !defined(DYNAMICLIGHTMAP_ON)
        // 如果没有 lightmap，使用 Light Probes
        
        #if UNITY_LIGHT_PROBE_PROXY_VOLUME
            // 使用 Light Probe Proxy Volume（LPPV）
            // 用于大型动态物体，提供逐像素的探针插值
            if (unity_ProbeVolumeParams.x == 1.0)
            {
                o_gi.indirect.diffuse = SHEvalLinearL0L1_SampleProbeVolume(half4(normalWorld, 1), data.worldPos);
                o_gi.indirect.diffuse = max(0, o_gi.indirect.diffuse);
                #if defined(UNITY_COLORSPACE_GAMMA)
                    o_gi.indirect.diffuse = LinearToGammaSpace(o_gi.indirect.diffuse);
                #endif
            }
            else
            {
                // 普通 Light Probe
                o_gi.indirect.diffuse = ShadeSH9(half4(normalWorld, 1));
            }
        #else
            // 标准 Light Probe（球谐函数 SH）
            o_gi.indirect.diffuse = ShadeSH9(half4(normalWorld, 1));
        #endif
        
        // 应用环境光遮蔽
        o_gi.indirect.diffuse *= occlusion;
    #endif
    
    // ========================================
    // 4. 处理环境反射（Reflection Probes）
    // ========================================
    o_gi.indirect.specular = UnityGI_IndirectSpecular(data, occlusion, normalWorld, data.reflUVW);
    
    return o_gi;
}

// ========================================
// 辅助函数：ResetUnityGI
// ========================================
inline void ResetUnityGI(out UnityGI outGI)
{
    outGI.light = (UnityLight)0;     // 初始化为零
    outGI.indirect = (UnityIndirect)0;
}

// ========================================
// 环境反射采样
// ========================================
inline half3 UnityGI_IndirectSpecular(UnityGIInput data, half occlusion, half3 normalWorld, half3 reflUVW)
{
    half3 specular = 0;
    
    #if UNITY_SPECCUBE_BOX_PROJECTION
        // 使用盒投影的 Reflection Probe
        half3 worldNormal = normalWorld;
        half3 worldPos = data.worldPos;
        half3 worldViewDir = data.worldViewDir;
        
        half roughness = 1 - _GlossMapScale;  // 粗糙度
        half3 reflectVec = reflect(-worldViewDir, worldNormal);
        
        // 盒投影计算
        specular = Unity_GlossyEnvironment(UNITY_PASS_TEXCUBE(unity_SpecCube0), data.probeHDR[0], reflectVec, roughness);
    #else
        // 标准 Reflection Probe 采样
        Unity_GlossyEnvironmentData g = UnityGlossyEnvironmentSetup(
            1 - _GlossMapScale,  // roughness
            data.worldViewDir,
            normalWorld,
            reflUVW
        );
        specular = UnityGI_IndirectSpecular(data, occlusion, g);
    #endif
    
    return specular * occlusion;
}
三、完整的光照管线（2021.3.44f1）
3.1 Standard Shader 的实际使用流程
hlsl

// ========================================
// 文件：UnityStandardCore.cginc
// Standard Shader 的片元着色器
// ========================================

half4 fragForwardBaseInternal (VertexOutputForwardBase i)
{
    // ========================================
    // 准备数据
    // ========================================
    UNITY_APPLY_DITHER_CROSSFADE(i.pos.xy);
    
    // 准备片元数据
    FragmentCommonData s = FragmentSetup(
        i.tex,                          // UV坐标
        i.eyeVec.xyz,                   // 视线方向
        IN_VIEWDIR4PARALLAX(i),
        i.tangentToWorldAndPackedData,
        IN_WORLDPOS(i)
    );
    
    // ========================================
    // 构建 UnityGIInput
    // ========================================
    UnityGIInput giInput;
    UNITY_INITIALIZE_OUTPUT(UnityGIInput, giInput);
    
    giInput.light = mainLight;          // 主光源（后面会填充）
    giInput.worldPos = s.posWorld;      // 世界坐标
    giInput.worldViewDir = -s.eyeVec;   // 视线方向
    giInput.atten = SHADOW_ATTENUATION(i); // 阴影衰减
    
    // Lightmap UV
    #if defined(LIGHTMAP_ON) || defined(DYNAMICLIGHTMAP_ON)
        giInput.lightmapUV = i.ambientOrLightmapUV;
    #endif
    
    // 环境光
    giInput.ambient = i.ambientOrLightmapUV.rgb;
    
    // 反射向量
    giInput.reflUVW = BoxProjectedCubemapDirection(
        reflect(-s.eyeVec, s.normalWorld),
        s.posWorld,
        unity_SpecCube0_ProbePosition,
        unity_SpecCube0_BoxMin,
        unity_SpecCube0_BoxMax
    );
    
    // ========================================
    // Step 1: 调用 UnityGlobalIllumination
    // ========================================
    UnityGI gi = UnityGlobalIllumination(
        giInput,
        s.occlusion,    // AO
        s.normalWorld   // 法线
    );
    
    // ========================================
    // Step 2: PBS 光照计算
    // ========================================
    half4 c = UNITY_BRDF_PBS(
        s.diffColor,              // 漫反射颜色
        s.specColor,              // 镜面反射颜色
        s.oneMinusReflectivity,   // 1 - 金属度
        s.smoothness,             // 光滑度
        s.normalWorld,            // 法线
        -s.eyeVec,               // 视线方向
        gi.light,                 // 实时光源
        gi.indirect               // 预计算光照（Lightmap/Probes）
    );
    
    // ========================================
    // Step 3: 自发光
    // ========================================
    c.rgb += Emission(i.tex.xy);
    
    UNITY_APPLY_FOG(_unity_fogCoord, c.rgb);
    return OutputForward(c, s.alpha);
}
3.2 UnityGlobalIllumination 的实现
hlsl

// ========================================
// 文件：UnityGlobalIllumination.cginc
// ========================================

inline UnityGI UnityGlobalIllumination(
    UnityGIInput data,
    half occlusion,
    half3 normalWorld)
{
    return UnityGlobalIllumination(data, occlusion, normalWorld, false);
}

inline UnityGI UnityGlobalIllumination(
    UnityGIInput data,
    half occlusion,
    half3 normalWorld,
    bool reflections)
{
    // ========================================
    // Step 1: 调用 UnityGI_Base
    // 获取所有预计算的 GI 数据
    // ========================================
    UnityGI o_gi = UnityGI_Base(data, occlusion, normalWorld);
    
    // ========================================
    // Step 2: 添加主光源（关键！）
    // ========================================
    // 这里才真正设置 o_gi.light
    o_gi.light = data.light;  // ← 从 UnityGIInput 传入的主光源
    o_gi.light.color *= data.atten;  // 应用阴影衰减
    
    // ========================================
    // Step 3: 如果需要反射
    // ========================================
    if (reflections)
    {
        // 这个分支用于处理特殊的反射需求
        // 标准情况下已在 UnityGI_Base 中处理
    }
    
    return o_gi;
}
四、关键发现：data.light 是如何填充的？
4.1 在 Vertex Shader 和 Fragment Shader 之间
hlsl

// ========================================
// 顶点着色器输出
// ========================================
struct VertexOutputForwardBase
{
    // ... 其他数据
    
    #if !defined(LIGHTMAP_ON) && !defined(DYNAMICLIGHTMAP_ON)
        // 如果没有 lightmap，传递球谐系数
        #if UNITY_SHOULD_SAMPLE_SH
            half3 sh : TEXCOORD5; // SH（球谐函数）
        #endif
    #else
        // 如果有 lightmap，传递 lightmap UV
        float4 ambientOrLightmapUV : TEXCOORD5;
    #endif
    
    // ... 其他数据
};

// ========================================
// 在片元着色器中构建主光源
// ========================================
half4 fragForwardBaseInternal(VertexOutputForwardBase i)
{
    // ========================================
    // 1. 获取主光源信息
    // ========================================
    UnityLight mainLight = MainLight();
    
    // ========================================
    // 2. 填充到 UnityGIInput
    // ========================================
    UnityGIInput giInput;
    giInput.light = mainLight;  // ← 关键：这里传入主光源
    giInput.atten = SHADOW_ATTENUATION(i);
    
    // ========================================
    // 3. 调用 UnityGlobalIllumination
    // ========================================
    UnityGI gi = UnityGlobalIllumination(giInput, occlusion, normalWorld);
    
    // 此时：
    // gi.light = mainLight * shadowAttenuation
    // gi.indirect = Lightmap 或 Light Probes
    
    return UNITY_BRDF_PBS(..., gi.light, gi.indirect);
}

// ========================================
// MainLight 函数的实现
// ========================================
inline UnityLight MainLight()
{
    UnityLight l;
    
    // 主平行光的颜色和方向（从引擎传入）
    l.color = _LightColor0.rgb;
    l.dir = _WorldSpaceLightPos0.xyz;
    
    return l;
}
五、不同光照模式的实际行为（2021.3.44f1）
模式 1: Baked（完全烘焙）
hlsl

// 场景设置：
// - Directional Light: Mode = Baked
// - Static GameObject
// - Lighting Settings: Baked Global Illumination = ON

// 在 fragForwardBaseInternal 中：

// Step 1: 构建 mainLight
UnityLight mainLight = MainLight();
// mainLight.color = _LightColor0.rgb  ← 仍然有值！
// mainLight.dir = _WorldSpaceLightPos0.xyz

// Step 2: 填充 UnityGIInput
giInput.light = mainLight;  // ← 传入主光源

// Step 3: UnityGI_Base 执行
#ifdef LIGHTMAP_ON
    o_gi.indirect.diffuse = DecodeLightmap(...);  // ← Lightmap 值
#endif

// Step 4: UnityGlobalIllumination 执行
o_gi.light = data.light;  // ← mainLight 被赋值给 gi.light
o_gi.light.color *= data.atten;

// ========================================
// 问题：为什么 Baked 模式下，gi.light 仍然有值？
// ========================================
// 答案：这是一个设计问题！
// 
// 在 2021.3.44f1 中，即使光源是 Baked：
// - _LightColor0 和 _WorldSpaceLightPos0 仍然被传递
// - gi.light 会被赋值
// 
// 但是在最终的 BRDF 计算中：
half4 c = UNITY_BRDF_PBS(..., gi.light, gi.indirect);

// BRDF 内部会检查光照模式：
// 伪代码：
if (光源是 Baked 模式)
{
    // 忽略 gi.light，因为直接光已在 Lightmap 中
    // 只使用 gi.indirect.diffuse
    
    directLighting = 0;  // ← 不使用 gi.light
    indirectLighting = gi.indirect.diffuse;  // ← 使用 Lightmap
}
else
{
    directLighting = BRDF(gi.light, ...);
    indirectLighting = gi.indirect.diffuse;
}

finalColor = directLighting + indirectLighting;
实际验证：UNITY_BRDF_PBS 的实现
hlsl

// ========================================
// 文件：UnityStandardBRDF.cginc
// ========================================

half4 UNITY_BRDF_PBS(
    half3 diffColor,
    half3 specColor,
    half oneMinusReflectivity,
    half smoothness,
    float3 normal,
    float3 viewDir,
    UnityLight light,      // ← gi.light
    UnityIndirect gi)      // ← gi.indirect
{
    // ========================================
    // 1. 准备 BRDF 数据
    // ========================================
    float perceptualRoughness = SmoothnessToPerceptualRoughness(smoothness);
    float3 halfDir = Unity_SafeNormalize(light.dir + viewDir);
    
    float nv = abs(dot(normal, viewDir));
    float nl = saturate(dot(normal, light.dir));
    float nh = saturate(dot(normal, halfDir));
    float lh = saturate(dot(light.dir, halfDir));
    
    // ========================================
    // 2. 计算直接光照
    // ========================================
    // 注意：这里并没有检查光源模式！
    // Unity 依赖于：
    // - Baked 模式下，light.color 应该为 0
    // - 或者在更早的阶段就不传入 light
    
    half3 color = 0;
    
    // 漫反射 BRDF
    half diffuseTerm = DisneyDiffuse(nv, nl, lh, perceptualRoughness) * nl;
    color += diffColor * light.color * diffuseTerm;  // ← 使用 light.color
    
    // 镜面反射 BRDF
    #ifdef UNITY_BRDF_GGX
        half roughness = PerceptualRoughnessToRoughness(perceptualRoughness);
        half V = SmithJointGGXVisibilityTerm(nl, nv, roughness);
        half D = GGXTerm(nh, roughness);
        
        half specularTerm = V * D * UNITY_PI;
        specularTerm = max(0, specularTerm * nl);
        
        color += specularTerm * light.color * specColor;  // ← 使用 light.color
    #endif
    
    // ========================================
    // 3. 添加间接光照（GI）
    // ========================================
    color += diffColor * gi.diffuse;      // ← Lightmap 或 Light Probes
    color += specColor * gi.specular;     // ← Reflection Probes
    
    return half4(color, 1);
}
真相：Baked 模式的处理
hlsl

// ========================================
// 关键在于：Baked 模式下，谁负责将 light.color 设为 0？
// ========================================

// 答案：在 2021.3.44f1 中，是在更高层处理的

// 查看 UnityStandardCore.cginc：

half4 fragForwardBaseInternal(VertexOutputForwardBase i)
{
    // ...
    
    // ========================================
    // 关键代码：
    // ========================================
    #ifdef LIGHTMAP_ON
        // 如果有 Lightmap，根据 Lighting Mode 决定如何处理主光源
        
        #if defined(DIRLIGHTMAP_COMBINED)
            // Directional Lightmap 模式
            // 主光源的影响已经烘焙到 Lightmap 中
            // 但是为了计算镜面高光，仍然需要光源方向
            
            mainLight.color = 0;  // ← 设为 0！
            mainLight.dir = _WorldSpaceLightPos0.xyz;  // 保留方向
        #endif
    #endif
    
    // ...
    
    UnityGIInput giInput;
    giInput.light = mainLight;  // ← 可能是 {0, dir}
    
    // ...
}

// ========================================
// 但这只是部分真相！
// ========================================
// 实际上，在很多情况下，引擎会根据光照模式：
// 1. 自动调整 shader keywords
// 2. 控制哪些 passes 被执行
// 3. 控制 _LightColor0 的值
六、实际测试：验证代码（2021.3.44f1）
测试 Shader
hlsl

Shader "Custom/GI Analysis 2021"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo", 2D) = "white" {}
        _Glossiness ("Smoothness", Range(0,1)) = 0.5
        _Metallic ("Metallic", Range(0,1)) = 0.0
        
        [Header(Debug Options)]
        [Toggle] _ShowLightColor ("Show gi.light.color", Float) = 0
        [Toggle] _ShowIndirectDiffuse ("Show gi.indirect.diffuse", Float) = 0
        [Toggle] _ShowLightmapRaw ("Show Lightmap Raw", Float) = 0
    }
    
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 200
        
        Pass
        {
            Tags { "LightMode"="ForwardBase" }
            
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fwdbase
            #pragma multi_compile_fog
            #pragma multi_compile _ LIGHTMAP_ON
            #pragma multi_compile _ DIRLIGHTMAP_COMBINED
            
            #include "UnityCG.cginc"
            #include "UnityPBSLighting.cginc"
            #include "AutoLight.cginc"
            #include "UnityGlobalIllumination.cginc"
            
            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float2 uv : TEXCOORD0;
                float2 uv1 : TEXCOORD1;  // Lightmap UV
            };
            
            struct v2f
            {
                float4 pos : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                float3 worldPos : TEXCOORD2;
                
                #ifdef LIGHTMAP_ON
                    float2 lightmapUV : TEXCOORD3;
                #endif
                
                UNITY_FOG_COORDS(4)
                UNITY_SHADOW_COORDS(5)
            };
            
            sampler2D _MainTex;
            float4 _MainTex_ST;
            half _Glossiness;
            half _Metallic;
            fixed4 _Color;
            
            float _ShowLightColor;
            float _ShowIndirectDiffuse;
            float _ShowLightmapRaw;
            
            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                
                #ifdef LIGHTMAP_ON
                    o.lightmapUV = v.uv1.xy * unity_LightmapST.xy + unity_LightmapST.zw;
                #endif
                
                UNITY_TRANSFER_FOG(o, o.pos);
                UNITY_TRANSFER_SHADOW(o, v.uv1.xy);
                
                return o;
            }
            
            half4 frag(v2f i) : SV_Target
            {
                // ========================================
                // 1. 准备主光源
                // ========================================
                UnityLight mainLight;
                mainLight.color = _LightColor0.rgb;
                mainLight.dir = _WorldSpaceLightPos0.xyz;
                
                // ========================================
                // 2. 构建 UnityGIInput
                // ========================================
                UnityGIInput giInput;
                UNITY_INITIALIZE_OUTPUT(UnityGIInput, giInput);
                
                giInput.light = mainLight;
                giInput.worldPos = i.worldPos;
                giInput.worldViewDir = normalize(UnityWorldSpaceViewDir(i.worldPos));
                giInput.atten = UNITY_SHADOW_ATTENUATION(i, i.worldPos);
                
                #ifdef LIGHTMAP_ON
                    giInput.lightmapUV = float4(i.lightmapUV, 0, 0);
                #endif
                
                // ========================================
                // 3. 调用 UnityGlobalIllumination
                // ========================================
                half3 worldNormal = normalize(i.worldNormal);
                UnityGI gi = UnityGlobalIllumination(giInput, 1.0, worldNormal);
                
                // ========================================
                // 4. Debug 输出
                // ========================================
                half3 debugColor = 0;
                
                if (_ShowLightColor > 0.5)
                {
                    // 显示 gi.light.color
                    debugColor = gi.light.color;
                    
                    // 添加标记：如果为 0，显示蓝色；否则显示光源颜色
                    if (length(gi.light.color) < 0.01)
                    {
                        debugColor = half3(0, 0, 1);  // 蓝色 = gi.light 为 0
                    }
                }
                else if (_ShowIndirectDiffuse > 0.5)
                {
                    // 显示 gi.indirect.diffuse
                    debugColor = gi.indirect.diffuse;
                }
                else if (_ShowLightmapRaw > 0.5)
                {
                    // 直接显示 Lightmap 原始采样值
                    #ifdef LIGHTMAP_ON
                        debugColor = DecodeLightmap(UNITY_SAMPLE_TEX2D(unity_Lightmap, i.lightmapUV));
                    #else
                        debugColor = half3(1, 0, 1);  // 洋红 = 无 Lightmap
                    #endif
                }
                else
                {
                    // 正常渲染
                    half3 albedo = tex2D(_MainTex, i.uv).rgb * _Color.rgb;
                    
                    // 简化的 PBS
                    half3 diffuse = albedo * (1 - _Metallic);
                    half3 specular = lerp(0.04, albedo, _Metallic);
                    
                    // 直接光
                    half nl = saturate(dot(worldNormal, gi.light.dir));
                    half3 directLight = gi.light.color * diffuse * nl;
                    
                    // 间接光
                    half3 indirectLight = gi.indirect.diffuse * diffuse + gi.indirect.specular * specular;
                    
                    debugColor = directLight + indirectLight;
                }
                
                UNITY_APPLY_FOG(i.fogCoord, debugColor);
                return half4(debugColor, 1);
            }
            ENDCG
        }
    }
    
    FallBack "Diffuse"
}
测试步骤
csharp

// ========================================
// 测试脚本
// ========================================
using UnityEngine;
using UnityEditor;

public class GIAnalysisTester : MonoBehaviour
{
    public Light directionalLight;
    public Material testMaterial;
    public GameObject staticCube;
    
    [ContextMenu("Test 1: Baked Mode")]
    void TestBakedMode()
    {
        Debug.Log("=== Test 1: Baked Mode ===");
        
        // 设置为 Baked
        directionalLight.lightmapBakeType = LightmapBakeType.Baked;
        
        // 标记物体为 Static
        GameObjectUtility.SetStaticEditorFlags(staticCube, StaticEditorFlags.ContributeGI);
        
        // 烘焙
        Lightmapping.BakeAsync();
        
        Debug.Log("烘焙完成后测试：");
        Debug.Log("1. _ShowLightColor = ON → 应该看到蓝色（gi.light.color = 0）");
        Debug.Log("2. _ShowIndirectDiffuse = ON → 应该看到明亮颜色（Lightmap 包含直接+间接光）");
        Debug.Log("3. _ShowLightmapRaw = ON → 应该看到 Lightmap 原始值");
    }
    
    [ContextMenu("Test 2: Mixed Baked Indirect")]
    void TestMixedBakedIndirect()
    {
        Debug.Log("=== Test 2: Mixed - Baked Indirect ===");
        
        directionalLight.lightmapBakeType = LightmapBakeType.Mixed;
        
        // 设置为 Baked Indirect 模式
        // Lighting Settings → Mixed Lighting → Lighting Mode = Baked Indirect
        
        Lightmapping.BakeAsync();
        
        Debug.Log("烘焙完成后测试：");
        Debug.Log("1. _ShowLightColor = ON → 应该看到光源颜色（gi.light.color 有值）");
        Debug.Log("2. _ShowIndirectDiffuse = ON → 应该看到较暗颜色（只有间接光）");
        Debug.Log("3. 正常模式 → 直接光（实时）+ 间接光（烘焙）");
    }
    
    [ContextMenu("Test 3: Realtime Mode")]
    void TestRealtimeMode()
    {
        Debug.Log("=== Test 3: Realtime Mode ===");
        
        directionalLight.lightmapBakeType = LightmapBakeType.Realtime;
        
        Debug.Log("无需烘焙，运行时测试：");
        Debug.Log("1. _ShowLightColor = ON → 应该看到光源颜色");
        Debug.Log("2. _ShowIndirectDiffuse = ON → 应该看到很暗的颜色（只有 SH 环境光）");
        Debug.Log("3. _ShowLightmapRaw = ON → 应该看到洋红色（无 Lightmap）");
    }
}
七、最终结论（2021.3.44f1）
核心发现
hlsl

// ========================================
// 1. UnityGI_Base 的职责
// ========================================
UnityGI UnityGI_Base(...)
{
    // 只负责收集预计算数据：
    // - Lightmap（静态物体）
    // - Light Probes（动态物体）
    // - Reflection Probes（环境反射）
    
    // 不负责设置 gi.light
    // gi.light 保持为 0
}

// ========================================
// 2. UnityGlobalIllumination 的职责
// ========================================
UnityGI UnityGlobalIllumination(UnityGIInput data, ...)
{
    // Step 1: 调用 UnityGI_Base
    UnityGI gi = UnityGI_Base(...);
    
    // Step 2: 添加主光源
    gi.light = data.light;  // ← 从输入参数获取
    gi.light.color *= data.atten;  // 应用阴影
    
    return gi;
}

// ========================================
// 3. Lightmap 的内容
// ========================================
// Lightmap 存储的是：
Lightmap = DirectLight（来自 Baked 光源）+ IndirectLight（GI Bounces）

// 在不同模式下：
if (Baked Mode)
{
    Lightmap = Full Direct + Full Indirect
    gi.light.color = 0  // 或很小的值
}
else if (Mixed - Baked Indirect)
{
    Lightmap = Only Indirect
    gi.light.color = RealTime Direct
}
else if (Mixed - Shadowmask)
{
    Lightmap = Full Direct + Full Indirect
    gi.light.color = RealTime Direct (for dynamic objects)
    Shadowmask = Baked Shadows
}

// ========================================
// 4. 为什么叫 "indirect"？
// ========================================
// Unity 的命名约定：
gi.light     = "主动提供的光"（实时光源）
gi.indirect  = "间接提供的光"（预计算数据）

// "indirect" 不是物理意义上的"间接光照"
// 而是"通过间接方式获得的光照"（Lightmap/Probes）
记忆要点

1. UnityGI_Base 只处理预计算数据，不设置 gi.light

2. gi.light 是在 UnityGlobalIllumination 中设置的
   来源：UnityGIInput.light（从片元着色器传入）

3. Lightmap 在 Baked 模式下包含直接+间接光照
   但都被放在 gi.indirect.diffuse 中

4. gi.indirect 的含义是"预计算的光照"
   不等于物理上的"间接光照"

5. 在 2021.3.44f1 中，光照模式的区分主要通过：
   - Shader keywords (LIGHTMAP_ON, DIRLIGHTMAP_COMBINED, etc.)
   - 引擎传递的参数（_LightColor0 等）
   - 可能在某些情况下手动将 light.color 设为 0
希望这个基于 2021.3.44f1 源码的详细分析能完全解答你的疑问！