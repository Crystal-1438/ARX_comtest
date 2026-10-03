# 来源与还原边界

## ARX X5

- 仓库：<https://gitee.com/li-bozha0/ARX_X5>
- 固定提交：`c78328785ea23a81d908e1dcc551eca992f2f1e9`
- 二进制：`py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so`，Linux x86_64。
- SHA256：`cb51e1acfccd1e904ca263d45db2035fb33a457ded0b64e5376a864aaf1abeb5`。
- Python 入口：`bimanual/script/single_arm.py:116`，调用 `set_arm_status(3)`。
- 模型：该目录下三个 `x5*.urdf`，原样复制至 `models/`。

下表地址为该二进制的虚拟地址，不适用于其他编译版本。可以用 `objdump -d -C`
复核；无需运行控制器或构造 `InterfacesPy`。

| 位置 | 已确认的行为 |
| --- | --- |
| `ControllerBase::read`, `0x153d0..0x15464` | 将六个实际位置直接写入 KDL JntArray，调用重力函数，保存六个结果 |
| `computeGravityCompensationTorque`, `0x2c120` | 创建结果数组，调用动力学对象虚表 `+0x38` 的 `JntToGravity` |
| `0x2c15d..0x2c199` | 对索引 0、1、2 乘 `.rodata:0x33058` 的 double `0.8` |
| `0x2c19b..0x2c1d5` | 对索引 3、4、5 乘 `.rodata:0x33060` 的 double `1.32` |
| `KinematicDynamicSolver` 三参数构造函数，`0x2c280` | `treeFromFile`、`getChain`、构造 `ChainDynParam` |
| `ControllerBase` 构造函数，`0x15d74..0x15e0f` | 指定 `base_link` 与 `link6` |
| `.rodata:0x33078` | 重力 Z 分量 double `-9.81`，X/Y 为零 |
| `stateGravityCompensation`, `0x13860..0x139e5` | 六关节的 torque 字段接收结果，其余四个 HybridJointCmd 字段置零；调用 CatchSoft |

这仅还原了计算与重力模式的命令字段。CAN 打包、电机电流换算、驱动器限幅、整机
保护和通信线程不属于本次计算模块。未确认系数的标定含义，也没有用推测替代厂商源码。

`verification/sdk_evidence.asm` 保留该二进制中相关方法的反汇编片段及浮点常数。
`verification/kdl_reference.cpp` 的可选 ABI 探针只调用其中的纯数学方法：
提供一个真实 KDL ChainDynParam 对象，以及该方法读取的六关节数量和 solver 指针。
对应字段位于 `this+0xc8` 和 `this+0xf8`。没有执行 ARX 类构造函数、URDF 解析器或硬件线程。
Python 验证驱动锁定架构和上述 SHA256，不能将这些偏移复用于其他厂商版本。
这项验证证明该方法的计算/缩放输出，不代表完成了 SDK 的初始化或整机控制验证。

## Orocos KDL

- 仓库：<https://github.com/orocos/orocos_kinematics_dynamics>
- 版本：`v1.5.1`，提交 `db25b7e480e068df068232064f2443b8d52a83c7`。
- `reference/orocos_kdl/src/` 保留所需 `.cpp` 及其本地头文件依赖闭包。
- `chaindynparam.cpp::JntToGravity`：零速度、零加速度、零外部 wrench 的 RNE。
- `chainidsolver_recursive_newton_euler.cpp::CartToJnt`：正向加速度/力递推，反向力矩投影。
- `segment.cpp`、`joint.cpp`：关节与连杆位姿、关节运动子空间。
- `frames.*`、`rigidbodyinertia.*` 等：坐标变换、叉乘、惯性与空间力运算。
- 许可证：LGPL-2.1-or-later，保留源文件头和 COPYING；新 Python 静态改写同样采用此许可证。

只复制所需原文件，未复制整个库。运行 Python 模块不需要编译它们。
ARX 快照只标出动态链接库名称，没有给出其原始 KDL 版本；选择 1.5.1 作为明确可复现的参考，
不声称它就是厂商构建时使用的版本。

## kdl_parser

- 仓库：<https://github.com/ros/kdl_parser>
- 版本：`1.14.2`，提交 `74d4ee3bc6938de8ae40a700997baef06114ea1b`。
- 原文件 `kdl_parser/src/kdl_parser.cpp` 保存至 `reference/kdl_parser/kdl_parser.cpp`。
- 相关逻辑：`toKdl(Joint)`、`toKdl(Inertial)`、`addChildrenToTree`。
- BSD 许可证保留在文件头。

新 `urdf.py` 直接使用 Python XML 标准库，保留重力计算所需的 URDF 坐标语义，
省去 ROS、urdfdom 和 XML C++ 依赖。它不是完整 URDF 解析器；不支持的 joint/mimic 明确报错。
标准库 XML/数学原语不另外复制；所有机器人几何与重力算法都在本目录中可见。
