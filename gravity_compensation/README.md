# ARX X5 独立重力补偿计算

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
倾斜/反向/零重力、输入校验和不加载 site-packages 的 CLI。
真实 KDL 数值交叉检查另见后续验证脚本；未经实机测试。

新提取的 Python 实现采用 LGPL-2.1-or-later，保留 KDL 算法作者说明，许可证为本目录
`LICENSE`。`reference/orocos_kdl` 保留其 LGPL 源文件；`reference/kdl_parser` 保留
文件头中的 BSD 许可证。`models` 来自 ARXrobotics，保留其 BSD 3-Clause `LICENSE`。
`UPSTREAM_SHA256.json` 记录原样复制文件的 SHA256。原项目 `vendor/ARX_X5` 保持不变。
