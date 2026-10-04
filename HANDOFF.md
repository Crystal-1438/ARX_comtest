# ARX_comtest 接手说明

更新时间：2026-10-04。本文面向另一个 coding agent，目标是无需阅读历史对话即可继续工作。
面向操作者的安装与运行说明在 [README.md](README.md)。

## 1. 当前目标与已经确认的需求

用户要求一个独立 Python 工程，通过 USB2CAN 控制 ARX X5 机械臂，提供：

1. 停止状态持续打印关节角度，能够手动拖动机械臂。
2. 正常模式接收外接遥操作器的串口输入，控制机械臂。
3. 先软件验证，再实机测试。
4. 串口帧格式暂未确定，因此必须保留可替换解析接口。
5. 独立目录应带 SDK、依赖安装脚本与详细交接说明，并推送到用户的 GitHub 仓库。

用户最初要求“电机失能”。检查 SDK 后发现无公开真正失能接口，用户明确接受了
**先用 SOFT 零力矩模式**。此决定已经确认，不需重复询问。不能将 SOFT、保护模式、
重力补偿、暂停发送目标或进程退出描述成真正失能。

用户允许使用其原有 `personal/teleoperation_system_RobotPC` 中的工程。
目前已经完全抽取为独立仓库；后续变更应在本仓库进行。

## 2. 仓库、目录与提交约定

- 交付仓库：<https://github.com/Crystal-1438/ARX_comtest>
- 当前交付分支：`main`，远端 `origin`；用 `git status -sb`、`git log -5 --oneline` 确认实时状态。
- 本次工作机上的目录：`/home/zhaosuya/ARX_comtest`。
- 压缩包副本：`/home/zhaosuya/ARX_comtest.tar.gz`；它由 `git archive` 生成，不随提交自动更新。
- 原项目工作副本 `/home/zhaosuya/teleoperation_system_RobotPC` 与 SDK 原始检出
  `/home/zhaosuya/ARX_X5` 只作来源参考。新工程不能依赖这些绝对路径。
- `75645a5`：首次独立打包；`31f88a0`：安装、编译及启动脚本。
  后续提交以 Git 实际历史为准，不要将本文中的历史提交当成当前 HEAD。

用户要求频繁小步提交并及时推送，已给出常规提交/推送授权；不要 force-push。
本机未配置用户 Git 姓名邮箱，现有提交使用单次 `git -c user.name=Codex
-c user.email=codex@localhost commit ...`，未更改全局身份。不要冒用原仓库作者。
若沙箱 DNS 阻止 GitHub/PyPI，按运行环境规则请求相应联网执行，不要把 DNS 失败误判为令牌失效。

## 3. 五分钟建立工作状态

```bash
cd /path/to/ARX_comtest
git status -sb
git remote -v
git log -5 --oneline

# 没有环境时：仅安装模拟验证依赖，不碰 CAN 或电机
bash scripts/install_dependencies.sh --mock --skip-system
.venv/bin/python -m unittest discover -s tests -v
bash scripts/run.sh --mode teleop --demo --duration 1

# 审阅实际系统安装步骤；不安装、编译或写文件
bash scripts/install_dependencies.sh --sdk --dry-run
```

`--skip-system` 假定 Python 已能创建 venv。若缺 `ensurepip`/venv，Debian/Ubuntu
可以去掉该选项，让脚本安装 `python3-venv`。模拟测试不要求 SDK 可以加载。

## 4. 文件与调用关系

| 文件 | 职责 / 接手时重点 |
| --- | --- |
| `app.py` | CLI、100 Hz 主循环、非阻塞串口、状态输出、Ctrl+C/SIGTERM 清理 |
| `protocol.py` | 临时 JSON 行协议；`Command`、`ProtocolError` 与 `feed(bytes)` 契约 |
| `control.py` | STOPPED / ACTIVE / FAULT 状态机、范围检查、限速、超时、跟随误差 |
| `backends.py` | `MockArm` 与 `VendorArm`；真实 SDK 状态映射、构造/模式切换 |
| `limits.example.json` | 六个关节的示例边界及限速参数；不是已核验实机配置 |
| `scripts/install_dependencies.sh` | apt 包候选检查、venv/Python 依赖、调用 SDK 编译 |
| `scripts/build_sdk.sh` | 架构/头文件/ldd 检查、构建、安装、只导入验证、READY 标记 |
| `scripts/native/CMakeLists.txt` | 编译厂商两个绑定；相对 RPATH；安装到独立 `.sdk` |
| `scripts/env.sh` | 必须 source；选择 SDK，设置 ARX_SDK_ROOT、ARX_VENV_DIR、LD_LIBRARY_PATH |
| `scripts/run.sh` | 从任意工作目录使用指定 venv 执行 app，并原样转发参数 |
| `tests/` | 控制、解析、SDK 替身、PTY 串口、安装脚本测试 |
| `vendor/ARX_X5/` | 固定 SDK 快照、许可证、来源说明、SHA256 校验清单 |

数据路径：外接控制器串口 → 解码器 → `Command` → 控制状态机 → SDK → SocketCAN → USB2CAN → 机械臂。
USB2CAN 的串口节点与遥操作器串口是两条不同链路，不能混用。

## 5. SDK 来源、绑定与状态语义

来源：<https://gitee.com/li-bozha0/ARX_X5>，固定提交
`c78328785ea23a81d908e1dcc551eca992f2f1e9`。快照位置：
`vendor/ARX_X5/py/arx_x5_python`。保留厂商 BSD 3-Clause 许可证。
未复制缓存/字节码与重复安装头文件，详细边界在 `vendor/ARX_X5/SOURCE.md`。

```bash
cd vendor/ARX_X5
sha256sum -c SHA256SUMS
```

368 个原始文件（包括许可证）的内容均与来源检出一致。不要把自己编译的 `.so`
覆盖这些文件；我们的构建脚本使用 `.sdk/`，而厂商原始 build.sh 会修改 vendor 安装目录。

接口由 `bimanual/src/single_arm_interface.cpp` 导出。程序直接加载
`arx_x5_python.InterfacesPy`，避免不必要的 `bimanual` 初始化副作用。

| 状态值 | SDK 枚举 | 本程序用途 |
| --- | --- | --- |
| 0 | SOFT | 停止、故障、退出时请求零力矩 |
| 1 | GO_HOME | 不调用 |
| 2 | PROTECT | 不冒充失能，不作为当前停止实现 |
| 3 | G_COMPENSATION | 不作为停止实现 |
| 4 | END_CONTROL | 当前未做笛卡尔控制 |
| 5 | POSITION_CONTROL | 正常六关节绝对位置控制 |

2023 对应构造参数 type=0 / `x5.urdf`；2025 对应 type=2 / `x5_2025.urdf`。
实机型号尚未得到明确回答。原项目用 type=0 不能证明用户的实物就是 2023，所以 SDK
后端要求显式 `--model`。`arx_x(500, 2000, 10)` 沿用厂商 `SingleArm` 初始化参数。

`get_joint_positions()` 的第七通道是夹爪。读角度展示只取前六维；进入位置控制前，
必须能读到七维反馈，并以第七维设置夹爪当前目标，再设置关节当前目标，最后切入状态 5。
这是为了避免厂商位置模式同时控制夹爪时跳到默认值。当前没有遥操作夹爪功能。

**边界**：SDK 构造会启动线程，可能使能电机。公开 Python 接口没有明确电机失能、
关闭线程、停止确认、反馈时间戳或通信 watchdog。SOFT 无重力支撑，机械臂会下落；
异常清理只能尽力请求 SOFT，不能保证 SIGKILL、SDK 卡住或 CAN 断开后的硬件行为。

## 6. 串口契约与状态机

当前协议仅用于测试，不是用户最终控制器协议。UTF-8 JSON 行、默认 115200 / 8N1：

```json
{"v":1,"seq":1,"type":"arm","deadman":true}
{"v":1,"seq":2,"type":"target","deadman":true,"joints":[0,0.2,0.2,0,0,0]}
{"v":1,"seq":3,"type":"stop"}
```

- 启动为 STOPPED；普通 target 不会使能。arm + deadman=true 以当前测量位置进入 ACTIVE。
- 目标为六维 SDK 原始坐标绝对角度，单位 rad。没有 GELLO 偏置、角度/编码器自动推断。
- 默认 max_speed=0.2 rad/s，max_following_error=0.15 rad，timeout=0.25 s。
- ACTIVE 时有效 target 刷新超时；重复 arm 不刷新。先检查超时，再处理新数据，迟到帧不能自动恢复。
- 超时、坏帧或序号问题请求 SOFT 并锁定 FAULT；需要 stop → arm 才能恢复。
- deadman=false 请求停止。重复/旧序号的 stop 仍被执行，但不会降低序号高水位。
- 单批读取中的 stop 后续命令丢弃；stop 和 arm 至少隔一个控制周期分开发。
- 单帧上限 1024 字节，接收积压上限 4096 字节，每批至多 64 个 Command。
- 退出/串口异常会关闭端口并尝试 SOFT；串口异常退出码 2。程序正常退出码 0。
- 输出 `host_read_monotonic` 是主机读取时刻，不是 CAN 反馈的新鲜度证明。

自定义解析器通过 `--decoder /path/to/file.py` 接入：导出 `create_decoder()`，其对象提供
`feed(data: bytes) -> list[Command]`。自行缓存拆帧、同步帧头、校验 CRC 和单位/零位转换，
无法解析时抛 `ProtocolError`。不要阻塞、访问机械臂或绕过状态机。

最终协议还缺：帧头、长度、字节序、校验、关节顺序/方向/单位/零位、发送频率、
deadman/arm/stop 来源、序号/时间戳/重启握手，以及是否增加夹爪。不要自行猜测。

## 7. 安装与运行环境

应用 Python 3.10+；SDK 原装扩展是 Linux x86_64 / CPython 3.12。
快照未提供 ARM64 核心库，脚本不会假装支持 ARM64 实机。

安装选项详见 `bash scripts/install_dependencies.sh --help`：

- `--mock`：只需 pyserial，系统阶段仅安装 python3-venv。
- `--sdk`（默认）：增加开发工具、KDL/URDF、CAN 工具和 numpy/pybind11，随后编译 SDK。
- `--skip-system`：不调用 apt/sudo；原生依赖必须由环境事先提供。
- `--python` / `--venv`：可指定解释器和环境目录；已有 venv 主/次版本不同会拒绝复用。
- `--dry-run`：无安装、编译或文件写入，仅显示将执行的命令。

apt 源缺包时脚本在安装包之前退出（apt-get update 可能已执行）。Ubuntu 22.04 universe
有 libkdl-parser-dev；本机 Ubuntu 26.04 没有该包候选，不能直接完成全套硬件环境安装。
其他发行版/厂商镜像是否可用，需以 apt 候选及实际 SDK 导入结果为准。

`build_sdk.sh` 先用 ldd 检查厂商库，再用同一 Python 的 pybind11/头文件生成绑定。
成功导入两个扩展、检查必需方法后写 `.sdk/READY`，不构造机械臂。
`scripts/run.sh` / `env.sh` 按 READY 选择生成 SDK；若手动执行 app，路径优先级为
`--sdk-root` > `ARX_SDK_ROOT` > 仓库原装 SDK。env.sh 不激活虚拟环境，手动执行时要使用
`.venv/bin/python`（自定义 venv 用对应解释器）。

不自动配置 CAN、修改 udev/sudoers、变更用户组、杀死已有 slcand、启动 ROS 或发送电机命令。
这些设备操作的例子在 README 中，应在实际 Robot PC 上按设备类型进行。

## 8. 已验证事项与证据

本次工作机：Ubuntu 26.04 / x86_64 / Python 3.14.4，无 CAN 与 USB 串口设备。

| 项目 | 结果 |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -v` | 31 项通过，含真实 pyserial + PTY |
| `bash -n scripts/*.sh` | Shell 语法检查通过 |
| `install_dependencies.sh --mock --skip-system` | 新 venv 实际安装 pyserial 3.5 成功 |
| `scripts/run.sh` | 模拟启动通过；测试覆盖不同 cwd、带空格路径、参数转发和 SDK 选择 |
| SDK 两个绑定编译 | Python 3.14.4 / pybind11 3.1.0 / CMake 4.4.3 / GNU C++ 15.2 下成功 |
| SDK 验证目录安装 | `build/install-check` 生成两个 cp314 扩展、库与 URDF，设置相对 RPATH |
| 完整 build_sdk.sh | 正确识别 libkdl_parser.so、liborocos-kdl.so 缺失并退出；未生成 READY |
| SDK 成功加载 / 控制器构造 | 未验证，不可宣称成功 |
| 实机读角度、串口控制器、运动 | 未测试 |
| 原始 SDK 完整性 | 368 文件 SHA256 与上游对应内容一致 |
| 独立压缩包 | 解压后跨目录模拟启动通过；版本变更后需重新打包 |

为单独检查 CMake 编译，我们直接运行了 scripts/native 的 configure/build/install，
产物只在被忽略的 `build/binding-compile-check` 和 `build/install-check`。
这不意味着通过了 build_sdk.sh 的运行库检查，更不意味着 SDK 已可用。
当前 `.venv` 额外安装了用于编译验证的 cmake / numpy / pybind11；正式脚本的 CMake 来自 apt。

## 9. 下一位 agent 的具体工作顺序

1. 阅读本文和 README，检查 Git 状态，跑模拟测试建立基线。不要重复克隆旧父工程。
2. 若继续实机阶段，取得 Robot PC 的系统版本、CPU 架构、实际型号、USB2CAN 类型、
   CAN 接口名和遥操作器串口名；这几项目前未确认。
3. 在具备兼容 KDL 库的环境安装 SDK，确认 `.sdk/READY` 产生，运行 preflight。
   preflight 只检查导入/设备，不证明电机在线或反馈新鲜。
4. 支撑机械臂，先用 monitor 验证 SOFT 与六关节读数方向/单位，再校准限位。
   保留外部急停，验证停止/断流的实际行为；不要自动回零或发送示例绝对位置。
5. 拿到正式协议后实现独立 decoder，补捕获字节流的离线测试和 PTY 集成测试；
   明确编码器到 SDK 角度的转换。随后再接入低速实机控制。
6. 如要求真正失能，需厂商提供关闭/失能及失能后读反馈的正式 API/协议，当前不能承诺。
7. 每个小改动验证后提交推送，更新本文的验证边界和未完成事项。

## 10. 常见阻塞的排查入口

| 症状 | 检查 / 处理 |
| --- | --- |
| 无兼容 Python 扩展 | 对比 Python ABI 与 .so 文件名；使用匹配解释器或重新编译 |
| libkdl_parser.so / liborocos-kdl.so not found | ldd 厂商核心库；安装兼容 dev 包或加载厂商库路径 |
| apt 没有 libkdl-parser-dev 候选 | 当前发行版不提供；选择已配置环境，不混用其他发行版包 |
| Python.h missing | 安装当前解释器对应的开发头；python3-dev 不覆盖任意自定义版本 |
| cmake missing（--skip-system） | 提供已有 CMake 到 PATH；不要将跳过系统安装理解成无需编译工具 |
| CAN interface absent / down / not SocketCAN | 在实机配置适配器，核对 --can-port；不要把控制器 tty 当作 CAN 名称 |
| FAULT 后目标不生效 | 单独发 stop，再 arm，再稳定发送目标；检查 deadman 和 seq |
| 控制器重启后序号报错 | 临时协议需同时重启接收进程；正式协议应加入会话握手 |
| SOFT 时机械臂下落 | 这是零力矩行为；需要支撑，不是位置保持或重力补偿 |

## 11. 提交与交付核对

```bash
git diff --check
.venv/bin/python -m unittest discover -s tests -v
bash -n scripts/install_dependencies.sh scripts/build_sdk.sh scripts/env.sh scripts/run.sh
git status --short
# 仅暂存本任务文件；不要提交 .venv、.sdk、build、设备日志或凭据
git add <reviewed-files>
git commit -m '<coherent change>'
git push origin main
git status -sb

# 根据最新 HEAD 更新独立压缩包
git archive --format=tar.gz --prefix=ARX_comtest/ --output=../ARX_comtest.tar.gz HEAD
```

推送成功以实际命令结果为准；出现权限/网络阻塞时保留本地提交并准确报告。
不要因为所有模拟测试通过就将“实机联调”标记为完成。

## 12. 独立重力补偿提取（2026-10-03）

用户要求提取 ARX X5 的重力计算以及所用库中的相关逻辑，允许放在本机有 Git 的仓库。
新增 `gravity_compensation/`，不接入当前实机状态机，不修改固定 vendor 快照。
入口和调用说明见该目录 README；Python 3.10+ 标准库即可离线使用。

已从固定 x86_64 核心库确认：读取六个实际位置，计算 `base_link -> link6` 链的
KDL `JntToGravity`，重力 `(0,0,-9.81)`，前三轴乘 `0.8`、后三轴乘 `1.32`。
厂商 ARX 核心方法只有二进制；新代码是行为还原，不是厂商原始 C++ 源码。
KDL 的相关源码及依赖、kdl_parser 源文件、三个型号的 URDF 和许可证已另存。
数学测试包括解析单摆、固定负载/移动关节及三个模型的势能梯度对比。
新增分支 `feat/extract-gravity-compensation`。验证结果：

- 项目全套 41 项测试通过；15 组回归样例来自独立原生计算。
- 提取的 KDL 源码子集通过 CMake/GNU C++17 构建，无 ROS/urdfdom 系统依赖。
- 与真实 KDL 1.5.1 比较 945 组，与固定厂商库的纯数学方法比较 315 组，
  最大绝对误差均为 `3.552713678800501e-15`。
- 厂商数学方法的验证使用特定二进制哈希/架构锁定的 ABI 探针，不构造任何厂商对象。
  测试用 `libkdl_parser.so` 只是 DT_NEEDED 占位库，不可用于实机 SDK。
- 复现命令、来源与边界见 `gravity_compensation/README.md` 和 `PROVENANCE.md`。

以上不代表已验证厂商初始化、CAN 命令、驱动器或实机力矩。主应用没有新增重力补偿模式。

用户随后要求改为 **C、无外部依赖、尽量少计算，目标 STM32，明确使用 float**。
新增主交付 `gravity_compensation/c/`：只需三个 `x5_gravity*.[ch]` 文件，无堆、无 libm、
无 double 计算。三型号的质量/质心已合并为 216 字节常量；轴向旋转替代矩阵，
静态子链合力消元；竖直重力跳过第一轴，常规入口每次只算 5 对内部 sin/cos。
角度有效范围 ±128 rad，超出明确报错；预计算 sin/cos 入口可完全省掉三角计算。
Python 与原版库保留用于独立核验。C 的验证/接入说明见 `c/README.md`，未在实机 STM32 测试。

C 验证已完成：59,832 组对比最大绝对误差 `2.1511475907232125e-6 N·m`，
预计算 sin/cos 接口也已核验；原 KDL/厂商样例误差 `9.544817327622468e-7 N·m`。
主机 freestanding 核心对象未解析符号为空，无堆内存、无运行库函数调用。
项目当前全套 **42 项测试通过**，包括 C 编译与数值/错误输入测试。
GCC x86_64 `-O2` `.text` 2550 字节、模型表 216 字节、可写全局数据 0；
主机完整调用栈约 208 字节；耗时约 51 ns/次，复用 sin/cos 约 22 ns/次。
这些资源/耗时数字不代表 STM32，目标机周期数仍待实际测量。

### SDK 关节与电机参数提取（2026-10-03）

用户要求把关节限幅、复位角、所有可确认的电机参数放入上述独立模块。
新增 `gravity_compensation/sdk_parameters/`：JSON 原始数值、BSD 来源副本、
关键函数静态反汇编和中文说明。没有修改 vendor、没有构造控制器或连接 CAN。
`c/x5_sdk_parameters.h/.c` 为单精度只读参数表，生成器 `sdk_parameters/generate_c.py`
以 JSON 为来源；六轴限幅/增益、三组应用复位预设、七电机 ID/类型/反馈阈值、
两种协议范围、夹爪型号差异、插值/积分常量、URDF 和末端约束均已提取。
主机 `.rodata` 832 字节，`.text/.data/.bss` 为 0，`nm -u` 为空。

注意：六轴默认 home 全 0，夹爪 home 运行时采集；ROS1/ROS2 示例是可选应用预设。
协议范围不等于额定参数；SDK 将同一反馈 effort 写入 torque/current，没有 Kt 换算。
Type4 Kd 量化 12 bit、打包仅低 9 bit；Interpolation 固定步长 0.03，忽略第三参数。
这些异常按原样留证，不在本任务内改动硬件控制行为。电机商品型号、减速比、
额定值、固件内环 PID、设备标定值无法由当前 SDK 确认，文档和 JSON 明确列出未知项。
当前全套 47 项测试通过，包含 ELF 常量、配置来源和全部编译后 C 表核验。
复核区分了 Type4 的 25 rad 计圈累加和 2π rad 范围修正，分别保留其常量证据。
主应用的用户指定硬件限位策略没有改变；C 参数表本身不实现限幅或保护状态机。

### SDK 目标位置到 CAN 数据流说明（2026-10-04）

新增 [ARX_X5_SDK_DATAFLOW.md](ARX_X5_SDK_DATAFLOW.md)，README 已添加入口。
文档覆盖输入缓存、线程顺序、关节限幅、插补、重力和积分、协议限幅/量化、
MT4/MT2 字节排列、SocketCAN 发送及完整 J2 算例，附版本哈希和复核地址。
进一步静态核对 ArmThread（0x18b00）及常量 0x32820，确认线程以 5000 μs
作为循环耗时阈值；这与插补固定乘 0.03 是两个独立事实，不能混用。
已检查文档 14 个相对链接、代码围栏、float32 算例字节及 diff 空白；
重新运行全部 47 项软件测试通过。未构造硬件控制器、未发送 CAN、未修改 vendor。

### CAN 反馈帧与电机识别（2026-10-04）

新增 [ARX_X5_CAN_FEEDBACK_ROUTING.md](ARX_X5_CAN_FEEDBACK_ROUTING.md)，README
和数据流文档均已添加入口。包含接收回调的七对象分发、MT4 按 CAN ID 匹配、
MT2 按 CAN ID=0 加 data[0] 低 4 位匹配、收发 ID 对照和 10 个识别示例。
文档区分帧归属与合法性验证：原 MT4 解码函数不先检查报文类型，两类函数
均未在入口检查 DLC；移植时应补充检查，本文未改动厂商实现。
文档相对链接、代码围栏、全部 10 个示例及 diff 空白检查通过；47 项软件测试通过。
本次仅修改文档，没有构造控制器、连接 CAN 或改动 vendor 快照。
