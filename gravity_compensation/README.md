# ARX X5 独立重力补偿计算

**当前推荐交付是 [c/ 下的纯 C99 / float 版本](c/README.md)，面向 STM32，无外部依赖，连 libm 也不需要。**
复制 `x5_gravity.c`、`x5_gravity.h`、`x5_gravity_data.h` 三个文件即可接入。
其余 Python 实现及 KDL 源码保留作算法说明、模型常量生成和独立验证参考。

```c
float torque[6];
int rc = x5_gravity_compute(X5_MODEL_2025, q, 0, X5_GRAVITY_SDK, torque);
```

下文说明原始提取链路与 Python 验证参考；C 版本的范围、接口和资源优化见上述链接。

本目录提取 ARX X5 的 **URDF → 静态重力力矩 → 厂商缩放后的力矩指令**。
整个目录可以单独复制，Python 3.10+ 即可运行；不需要 NumPy、ROS、KDL 动态库、
厂商 SDK 或 CAN。没有硬件初始化、模式切换和发送命令的逻辑。

```bash
# 在本目录的父目录运行；型号必须明确选择
python3 -m gravity_compensation --model 2025 --q 0 0 0 0 0 0
```

```python
from gravity_compensation import GravityCompensator

solver = GravityCompensator.from_model("2025")
q = [0.0, 0.2, -0.3, 0.1, 0.0, 0.0]  # joint1..joint6，rad
physical_torque = solver.raw_torques(q)  # KDL G(q)，N·m
vendor_command = solver.sdk_torques(q)  # 应用厂商 0.8 / 1.32 系数
```

`2023` 对应 SDK type=0 / `x5.urdf`；`master` 对应 type=1 / `x5_master.urdf`；
`2025` 对应 type=2 / `x5_2025.urdf`。输入必须是 SDK/URDF 关节坐标，不是未经转换的
编码器数值。第七通道夹爪不参与这条六关节链的计算。模型、质量和质心均来自固定 SDK 快照，
不包含用户额外安装的工具或负载。

## 原始调用链与提取范围

```text
SingleArm.gravity_compensation() -> set_arm_status(3)
ControllerBase::read() -> 六个实际关节位置
KinematicDynamicSolver::computeGravityCompensationTorque(q)
  -> KDL::ChainDynParam::JntToGravity(q)
  -> KDL::ChainIdSolver_RNE::CartToJnt(q, 0, 0, 0)
  -> 第 1–3 关节乘 0.8，第 4–6 关节乘 1.32
ControllerBase::stateGravityCompensation()
  -> 六关节命令 torque=上述结果，position/velocity/k_p/k_d=0
  -> CatchSoft() 单独处理夹爪
```

厂商核心只提供 `.so`，没有上述两个 ARX 方法的 C++ 源码。本模块是根据该固定二进制的
符号、反汇编和常数还原的可读实现，**不是声称找到了厂商原始源码**。
KDL 与 kdl_parser 的相关公开源码保存在 `reference/`，原文件不修改。
厂商实际使用的 KDL 小版本不可从现有快照确认；参考版本固定为 Orocos KDL 1.5.1。

链条是 `base_link -> link6`，默认重力在基座坐标系中为 `(0, 0, -9.81)` m/s²。
`sdk_torques` 保留原二进制的经验缩放；这些系数的标定依据未知，不将其解释为减速比或电流转换。
这里的输出位于 CAN 编码、驱动器限幅等处理之前，不是完整硬件控制器的替代品。

## 库内部算法

KDL 的重力函数实际调用逆动力学，但将速度、加速度和外部 wrench 全部设为零。
因此旋转惯量、科里奥利项、关节惯量项都不参与结果，只需每个连杆的质量、质心和关节几何。

`urdf.py` 提取 URDF 链和坐标约定；`spatial.py` 展开三维旋转、叉乘及坐标变换；
`solver.py` 实现两次递推。`R_i,p_i` 表示子坐标系到父坐标系的变换：

1. 基座支持加速度 `a_0 = -gravity`。
2. 正向：`a_i = R_i^T a_parent`，`F_i = m_i a_i`，`N_i = com_i × F_i`。
3. 反向：先将累计力矩投影到当前关节轴，得到 `tau_i = axis_i · N_i`。
4. 将该连杆及后代的 wrench 传给父节点：
   `F_parent += R_i F_i`，`N_parent += R_i N_i + p_i × (R_i F_i)`。
5. `raw_torques()` 返回持住所需的力矩；`sdk_torques()` 再应用 ARX 六个缩放系数。

质心 xyz 已在 link 坐标系中；不要再用 inertial rpy 旋转它。
URDF 的 joint rpy 则必须参与几何变换，顺序是 `Rz(yaw) Ry(pitch) Rx(roll)`。
固定关节的质量也会传回父关节。支持 prismatic 的底层求解器返回相应轴向力 N，
但 X5 的经验缩放仅用于保持原命名与顺序的六个转动关节。

机械臂倾斜安装时可显式传入基座坐标系的重力方向：
`GravityCompensator.from_model("2025", gravity=(gx, gy, gz))`。
这是本模块提供的扩展；原 SDK 的该构造函数固定为负 Z 方向。

## 验证与许可证

运行项目测试：`.venv/bin/python -m unittest discover -s tests -v`。
当前测试包含单摆解析解、移动关节与固定负载、三个型号的势能数值梯度、
倾斜/反向/零重力、输入校验、不加载 site-packages 的 CLI，以及独立原生计算生成的回归样例。

已完成两层原生数值验证，固定随机种子 `20261003`：

| 对比对象 | 覆盖范围 | 最大绝对误差 |
| --- | --- | --- |
| 原版 KDL 1.5.1 `JntToGravity` | 3 个型号 × 105 个姿态 × 3 个重力向量 = 945 组 | 3.56e-15 N·m 以下 |
| 厂商 `.so` 的 `computeGravityCompensationTorque` | 3 个型号 × 105 个姿态 = 315 组，包含厂商缩放 | 3.56e-15 N·m 以下 |

两层对比都不连接硬件。第二层是锁定特定 x86_64 库的数学方法 ABI 探针，**不构造厂商对象**，
不验证厂商 URDF 解析、CAN、驱动器及实机；具体边界见 [PROVENANCE.md](PROVENANCE.md)。
报告见 `verification/result.json`，15 组独立回归样例见 `verification/fixtures.json`。

要重做原生验证，在项目根目录执行（需 C++17 编译器、CMake；仅验证需要 Eigen）：

```bash
cmake -S gravity_compensation/verification -B build/gravity-reference -DCMAKE_BUILD_TYPE=Release
cmake --build build/gravity-reference -j 2
python3 gravity_compensation/verification/verify.py

# 可选：同固定厂商库的纯数学方法比较。此命令不会构造 SDK 控制器。
python3 gravity_compensation/verification/verify.py \
  --vendor-library vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so
```

编译默认使用项目 vendor 中现有的 Eigen 头文件；也可通过
`-DEIGEN_INCLUDE_DIR=/path/to/eigen3` 指定位置。安装在虚拟环境中的 CMake 可用
`.venv/bin/cmake` 调用。**正常 Python 计算完全不需要这个编译步骤。**
`libkdl_parser.so` 占位文件只用于隔离数学探针，不实现解析，不应作为真实 SDK 的依赖使用。
不要将验证目录加入实机程序的库搜索路径。

校验所有原样复制文件：

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('gravity_compensation')
for name, digest in json.loads((root / 'UPSTREAM_SHA256.json').read_text()).items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
print('upstream checksums OK')
PY
```

新提取的 Python 实现采用 LGPL-2.1-or-later，保留 KDL 算法作者说明，许可证为本目录
`LICENSE`。`reference/orocos_kdl` 保留其 LGPL 源文件；`reference/kdl_parser` 保留
文件头中的 BSD 许可证。`models` 来自 ARXrobotics，保留其 BSD 3-Clause `LICENSE`。
`UPSTREAM_SHA256.json` 记录原样复制文件的 SHA256。原项目 `vendor/ARX_X5` 保持不变。
