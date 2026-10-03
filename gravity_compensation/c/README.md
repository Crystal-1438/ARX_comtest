# STM32 用纯 C99 / float 重力补偿

将以下三个文件加入工程即可，其他文件只是说明、示例或开发验证工具：

- `x5_gravity.h`：接口；`x5_real` 就是 `float`。
- `x5_gravity.c`：三角函数和重力递推，全部单精度。
- `x5_gravity_data.h`：三个型号预计算常量。

**不需要 ROS、KDL、Eigen、Python、libm、malloc 或初始化函数。**
没有可变全局状态，可重入。仅使用 C 标准头文件里的类型/常量，不调用标准库函数。
没有单精度 FPU 的 MCU 仍可能使用编译器自己的软浮点运行时；这不是模块引入的数学库。

## 调用

```c
#include "x5_gravity.h"

float q[6] = {0.0f, 0.2f, -0.3f, 0.1f, 0.0f, 0.0f};
float torque[6];

int rc = x5_gravity_compute(
    X5_MODEL_2025, q, 0, X5_GRAVITY_SDK, torque);
if (rc == X5_GRAVITY_OK) {
    /* torque[0..5] 是计算结果，单位 N*m；由上层处理输出。 */
}
```

- `q`：SDK/URDF 关节顺序 joint1..joint6，单位 rad。
- 第三个参数为基座系重力向量，传空指针使用 `(0,0,-9.81)`；倾斜安装传入实际向量。
- `X5_GRAVITY_PHYSICAL`：原始 KDL 静态持有力矩；`X5_GRAVITY_SDK`：再乘厂商系数。
- 型号枚举与 SDK 一致：2023=0、master=1、2025=2。
- 非法型号、指针、模式、非有限重力返回 `-1`；非有限或超出范围的角度返回 `-2`。
  校验失败时不改写输出数组。
- 这只是离线算法，不含电机电流换算、CAN、限幅和安全状态机。

普通主机上也能编译示例，**不加 `-lm`**：

```bash
cc -std=c99 -O2 x5_gravity.c example.c -o example
./example
```

STM32 工程建议启用 `-O2`，并按具体芯片/整个工程 ABI 配置 FPU。
例如 Cortex-M4F 可以使用 `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard`，
但不能将此配置套用到没有相应 FPU 的 STM32。所有浮点常量均带 `f` 后缀，计算路径没有 double。
不要使用破坏 NaN 检查语义的 `-ffast-math`。

## 如何减少运算

1. 不运行时解析 URDF。质量、质心与固定连杆偏移已合并成 **3×6×3 个 float，即 216 字节**。
2. 不计算 3×3/4×4 通用矩阵。仅对 X5 的 X/Y/Z 关节轴旋转三维向量。
3. 不计算速度、加速度惯性、科里奥利或完整动力学，只保留静态重力项。
4. 子链合力可直接写成子链质量乘支持加速度，所以合并力矩臂后，省掉反向合力递推。
5. 第六轴的固定 X 旋转与关节旋转合并；固定 `-3.1416` 保留原值，不近似替换成 `-pi`。
6. 基座重力沿 Z 轴时，第一轴重力力矩严格为零，跳过第一轴三角函数和最后一次力矩递推。
7. 正常入口每次只算 5 对 sin/cos，倾斜重力时为 6 对；不用动态内存、递归、缓存表。

缩减后的静态递推为：

```text
H_i = m_i*COM_i + M_(i+1)*p_(i+1)     // 编译前计算
a_i = R_i^T * a_(i-1)                // 正向，a_0 = -gravity
N_i = H_i × a_i + R_(i+1)*N_(i+1)    // 反向
tau_i = joint_axis_i · N_i
```

`M_(i+1)` 是全部后代的质量，不仅是紧邻连杆的质量。
重力下整条后代链的合力在当前坐标系恰好为 `M_(i+1)*a_i`，因此这种合并不改变物理模型。

若上层已经计算了关节 sin/cos，调用 `x5_gravity_compute_sincos()` 可省掉所有三角运算。
调用者保证每对 sin/cos 对应同一角度、满足单位圆；接口只检查分量有限且在 `[-1,1]`。
定义 `X5_GRAVITY_NO_TRIG` 可在编译时完全移除角度入口，进一步减少代码体积。

## 三角函数精度与范围

内部用拆分的 `pi/2` 将角度归约到约 `[-pi/4,pi/4]`，再用 Horner 多项式同时求 sin/cos。
所有归约与多项式运算都是 float。限定输入 **`|q_i| <= 128 rad`（约 20 圈）**，
这是为了保持便宜、准确的单精度范围归约；超过范围明确报错，不悄悄算错。
这是计算入口的数值范围，不是机械臂允许的运动限位。预计算 sin/cos 入口没有此角度范围限制。

采用 9 次 sin / 8 次 cos 多项式，截断误差小于约 `2.5e-8`，避免使用远超 float 精度所需的阶数。
最终误差主要由 float 舍入和递推累积决定，
不能把此截断误差当作最终力矩精度。完整数值验证见 `validation.json`。

当前验证共 59,832 组（包含两种输出模式），相对已通过 KDL 验证的 double 参考，
最大绝对力矩误差 **2.16e-6 N·m 以下**；相对原 KDL/厂商独立样例，误差 **9.55e-7 N·m 以下**。
这是列出的姿态和重力样本上的测量结果，不是对任意输入的全局误差界。

## 资源测量

主机 GCC 15.2 / x86_64 / `-O2`，完整入口 `.text=2550` 字节；只保留预计算 sin/cos
入口时 `.text=1810` 字节。模型表 216 字节，另有少量只读数学常量；`.data=.bss=0`。
关闭 x86 red zone 后，`-fstack-usage` 给出的完整调用路径为约 208 字节
（入口 96 + 内部函数 112），不包含上层数组或中断栈。**这些是主机编译结果，STM32 上须重新测量。**

主机固定姿态、热缓存、100 万次调用的单次 CPU 时间约 51 ns；预计算 sin/cos 入口约 22 ns。
测试含循环和校验和开销，无 LTO，仅用于同一主机上比较两种接口，不用于推算 STM32 周期数。

```bash
# 在本目录下复现主机耗时测试；不要开启 LTO。
cc -std=c99 -O2 -c x5_gravity.c -o x5_gravity.o
cc -std=c99 -O2 benchmark.c x5_gravity.o -o benchmark
./benchmark
```

STM32 上可通过目标编译器的 `size`、链接 map、`-fstack-usage` 检查 Flash/栈占用，
再用可用的 DWT 周期计数器或定时器测量真实控制循环中的耗时。

## 验证与来源

在项目根目录运行开发验证（这一步才需要主机 Python/C 编译器）：

```bash
python3 gravity_compensation/c/verify.py
python3 gravity_compensation/c/generate_model_data.py --check
```

验证包含三个型号、正负/倾斜/零重力、随机角度、象限边界、±128 rad、厂商/KDL 独立样例、
非法输入，以及裁剪掉三角函数后的入口。以 `-Wdouble-promotion -Wfloat-conversion -Werror`
编译；主机 freestanding 对象的 `nm -u` 必须为空，检查无运行库符号依赖。
来源、许可证和厂商二进制还原边界仍见上级 `PROVENANCE.md`、`LICENSE`。
移植时应同时保留许可证；生成数据来自 ARX BSD 许可模型，保留 `../models/LICENSE`。

目前尚未在真实 STM32 上测量周期数，也未连接机械臂。主机测得的耗时不能作为 MCU 实时性承诺。
