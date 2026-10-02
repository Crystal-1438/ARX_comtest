# ARX_comtest 接手说明

更新时间：2026-10-02。本文面向另一个 coding agent，目标是无需阅读历史对话即可继续工作。
面向操作者的安装与运行说明在 [README.md](README.md)。

> 本文记录了两台不同的机器：第 1–11 节出自一台 Ubuntu 26.04 工作机，
> 第 12 节出自连接了 USB2CAN 与机械臂的 Robot PC（Ubuntu 22.04）。
> 两节的结论不可互相覆盖，尤其"SDK 能否加载"在两台机器上答案不同。

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
| `leader_decoder.py` | 外接遥操作器 USART3 文本流解码器；见第 6 节末的契约 |
| `leader_map.py` | 单圈角度 → 关节弧度的标定映射；路径解析的唯一权威 |
| `leader_calibrate.py` | 标定工具：`session` 交互采样（单点手输方向，或多点拟合）、`sample` 单次采样、`fit` 出映射；见第 6.2 节 |
| `operator_keys.py` | 本地按键 arm/stop 通道（必须叫这个名字，见文件内注释） |
| `control.py` | STOPPED / ACTIVE / FAULT 状态机、越界限幅、指令轨迹、超时、跟随误差 |
| `td.py` | 参考实现 `ref/adrc.c` 的独立跟踪微分器（逐关节、单位为度、多圈角）；见第 12.23 节 |
| `backends.py` | `MockArm` 与 `VendorArm`；真实 SDK 状态映射、构造/模式切换 |
| `limits.example.json` | 六个关节的示例边界、轨迹速度上限与逐关节加速度上限；不是已核验实机配置 |
| `leader_map.example.json` | 遥操作器标定文件模板；用户复制为被忽略的 `leader_map.json` |
| `scripts/install_dependencies.sh` | apt 包候选检查、venv/Python 依赖、调用 SDK 编译 |
| `scripts/build_sdk.sh` | 架构/头文件/ldd 检查、构建、安装、只导入验证、READY 标记 |
| `scripts/native/CMakeLists.txt` | 编译厂商两个绑定；相对 RPATH；安装到独立 `.sdk` |
| `scripts/env.sh` | 必须 source；选择 SDK，设置 ARX_SDK_ROOT、ARX_VENV_DIR、LD_LIBRARY_PATH |
| `scripts/run.sh` | 从任意工作目录使用指定 venv 执行 app，并原样转发参数 |
| `scripts/calibrate.sh` | 同上，但执行 `leader_calibrate.py`，参数原样转发 |
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
| 3 | G_COMPENSATION | 只给 `leader_calibrate.py --arm` 标定时托住机械臂；退出前确认后回 SOFT |
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

重力补偿（状态 3）也不是失能：它按 URDF 动力学主动出力托住机械臂，是**驱动**状态。
负载、夹爪或型号不在 URDF 里，算出的力矩就会有偏差，机械臂会缓慢漂移而不是稳稳悬停——
**真机上一次都没跑过**（见 §12.10），进入前必须有支撑、有人在旁边。本项目没有外部急停。
已确认可达：头文件里的 `InterfacesPy::gravity_compensation()` 既没进 pybind 也没导出到 `.so`，
但 `set_arm_status` 已绑定，`.rodata:0x32040` 的跳转表把它映射到 `stateGravityCompensation`，
厂商自己的 `bimanual/script/single_arm.py:117` 用的也是 `set_arm_status(3)`。

上表的编号在**源码级**也一致：`InterfacesThread.hpp` 的 `enum state { SOFT, GO_HOME, PROTECT,
G_COMPENSATION, END_CONTROL, POSITION_CONTROL }`（顺序即取值），`ControllerBase` 里
`stateSoft/stateGoHome/stateProtect/stateGravityCompensation/stateEndControl/statePositionControl`
六个符号都实际存在。两点补充证据（2026-10-03 在 `.sdk` 的 `.so` 上反汇编）：

- `ControllerBase::Init()` 调用 `setEnableMotor()` —— **构造 `InterfacesPy` 就会使能电机**，
  这正是 AGENTS.md 要求"导入类做内省 ≠ 构造 `InterfacesPy`"的原因，现在有二进制证据。
- `ControllerBase::stateSoft()` 把一片力/前馈目标清零后跳到 `CatchSoft()`，**不发任何失能报文**；
  这坐实了"SOFT 是零力矩、不是失能"的区分。

**退出时的关停序列**（`InterfacesPy` 析构，实测日志）：`ControllerThread::ArmThread()` 打印
`[ArmThread] DisableMotor` → `ControllerBase::destoryFunc()`（它只把 SocketCAN 的两个回调
清空，本身不装失能帧）→ `[ArmThread] finish close` → `ControllerThread::~ControllerThread()`
打印 `[Controller] waiting for thread finish` / `[Controller] thread finish`（等线程退出）→
`SocketCan::impl::~impl()` 打印 `Destroying SocketCAN adapter...` 并 `Close()` 掉套接字。
**CAN 套接字一关，本进程就不会再发出任何指令**；`DisableMotor` 这个标签属于厂商的关停路径，
但"驱动器是否真的因此失去力矩"没有实测，不能当已验证结论。见 §12.13。

**关节增益（PID）改不了 —— 这是查证过的结论，不要再去翻。** 三条独立证据：

1. 公开 Python 接口没有增益入口（全部 pybind 导出只有位置/位姿/夹爪/模式/读取/`arx_x`）。
2. 底层帧里**确实**带 `k_p`/`k_d`（`HybridJointCmd`，DWARF 确认 40 字节，偏移 0/8/16/24/32），
   但值是 SDK 内部按关节填的：`ControllerBase::statePositionControl()` 从控制器成员取
   `k_p`/`k_d`，不是调用参数，外面没有传进去的路。
3. **没有源码，也不读配置**：厂商只给了两个 `.cpp`（pybind 壳 `single_arm_interface.cpp` 与
   `kinematic_solver.cpp`），`bimanual/CMakeLists.txt:22` 对控制器只有
   `target_link_libraries(... libarx_x5_src.so)`；这份 `.so` 的 strings 里没有任何
   `.json/.yaml/.ini/.cfg`，符号表里没有 `ifstream`/`fopen`/`loadConfig`。

所以"改源码重编"和"改参数文件"两条路都不存在，只剩给 `.so` 打二进制补丁或运行时改内存——
两者都要求动固定的快照（见本节开头），不建议。**唯一外部可见的厂商数值是
`arx_x(500, 2000, 10)`，它进的是 `arx::solve::Interpolation`（厂商自己的轨迹插值），不是增益。**
反汇编细节、已定位到的常量、以及为什么认不出哪一组是 kp/kd，见 §12.24。

## 6. 串口契约与状态机

当前协议仅用于测试，不是用户最终控制器协议。UTF-8 JSON 行、默认 115200 / 8N1：

```json
{"v":1,"seq":1,"type":"arm","deadman":true}
{"v":1,"seq":2,"type":"target","deadman":true,"joints":[0,0.2,0.2,0,0,0]}
{"v":1,"seq":3,"type":"stop"}
```

- 启动为 STOPPED；普通 target 不会使能。arm + deadman=true 以当前测量位置进入 ACTIVE。
- 目标为六维 SDK 原始坐标绝对角度，单位 rad。没有 GELLO 偏置、角度/编码器自动推断。
- 默认 max_speed=0.2 rad/s，max_following_error=0.15 rad，timeout=0.25 s；
  默认 `td_r_deg`=(400, 500, 600, 4000, 1000, 4000) deg/s²（逐关节加速度上限，见第 12.23 节）。
- 发出去的不是 target 而是**轨迹**：每个关节一个跟踪微分器（`td.py`），以该关节的
  `td_r_deg` 为加速度上限把 target 跟踪过去，`max_speed` 再给轨迹的速度设上限。
  轨迹在 arm 时从实测位置、零速度起步，且**不会越过 target**（因此不会自己出界）。
  角度是 mapper 解缠后的**多圈值**，不折回 0..360。
- ACTIVE 时 target 越过配置范围**只把该分量夹到边界并保持**（`Limits.clamp()`），
  不停止、不锁存，拉回范围内即恢复；arm 那一刻机械臂实测越界则拒绝 arm。见第 12.22 节。
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

### 6.1 外接遥操作器解码器（`leader_decoder.py`）

`docs/uart_packet.md` 描述的是**另一条串口链路**（leader 板 USART3），不是上面第 6 节的
控制器协议，两者不要混淆。它通过 `--decoder leader_decoder.py` 接入，不需要改动
`protocol.py`。线上格式：115200 8N1、约 200 Hz、ASCII 行
`<J1>..<J6>,<J7>\r\n`，前六维为 **0.1° 单圈绝对角**（`0..3599`，哨兵 `-1` = 从未采样），
J7 为夹爪 ADC（`0..1000`）。

已实现并已被测试固定的语义：

- 逐字段用 `^-?[0-9]+$` 严格匹配，字段数必须恰好 7；不符合的行**静默丢弃并计入
  `dropped`**（落单的半行不会污染下一帧）。**不用 `int()`**：它会接受 `b" 12"`、`b"+12"`，
  正是字节翻转产生形状。
- 值域越界（J1..J6 非 `-1` 且不在 `0..3599`、J7 不在 `0..1000`）→ `ProtocolError`。
  **线上没有 CRC、没有序号**，越界是唯一能被发现的损坏。
- `-1` 判据带**预热豁免**：在看到第一帧六维全有效帧之前，含 `-1` 的帧整帧丢弃、只记
  `no_data`；一旦见过有效帧，任一维 `-1` 立即 FAULT。否则每次 leader 板上电都会锁存 FAULT
  （文档 §4 说复位后头几个包就是 `-1`）。
- 板子复位由握手行 `0123456789` 宣告，只计数（`resets`）并重新进入预热，不算损坏。
- **一批里所有完整行都要过校验**，任一坏行就抛错、不返回任何 Command——坏帧不能躲在
  好帧后面。全部干净时只返回**最新一帧**（200 Hz 输入 vs 100 Hz 循环，陈旧目标无意义）。
- 解码器自造严格递增 `seq`，`deadman=True`；`seq` 数的是交给控制器的**批次数**，
  `frames` 数的是真正收到的**包数**，判丢包只能看后者。
- `last_frame` 是**粘性**的，带 `host_monotonic`：打印频率低于流频率，约一半的记录落在
  没有新字节的循环上，空白帧会让健康流看起来是断的；**时间戳不动才是流停了**。
- 声明 `provides_arm = False`：这块板只报位置，不报 arm/stop。
- **整圈锚定**（第 6.3 节）：按 `a` 时由机械臂实测姿态反解出每关节该读的角、挑一整圈
  偏置，结果进 `last_telemetry["anchor"]`（没 anchor 过是 `None`，不是 `{"checked": false}`）。
  `anchor(arm_radians)` 返回 `None` 放行或一句拒绝理由，被装成 `Controller.pre_arm`。
  `unwrap` 的原点、`reset()`、握手行、`ProtocolError` 都会经 `_restart_origin()` 清掉
  偏置与判定，因为旧偏置是相对旧原点选的。`-1` 预热帧不产生原点，也不构成可锚定的读数。
- `anchor()` **不抛异常**：它跑在 `Controller._apply("arm")` 里，抛出去会穿到 `main()`
  被 `except ValueError` 接住直接退出 2——没收到帧就按 `a` 会**杀掉进程**。没帧时返回
  理由字符串。
- `distance(arm_radians)` 是**只读**的同一个量：逐关节 `shortest_turn(needed, now)`，
  即 `--watch` 行上的数字，也是拒绝信息里"turn it"的数字。它**故意不选圈**——选圈是
  `anchor()` 的事，只在按 `a` 那一刻做一次；观看到的瞬时值若写进 `bias`，手从旁边扫过
  也会被带进会话。没帧时返回 `None`。

**给人看的输出**（`--watch` + `--print-rate`）。默认打印的是整条 JSON 记录，里面含整个
`leader` 块——真机上是一面墙，且不说该做什么。`--watch` 换成一行：
`<时钟> <STATE> | J1 .. J6 的转角度数 | out of pose: ...` 或 `in the arm's pose, press a`
（ACTIVE 时只报状态与理由，因为已经没什么可转的，被限幅时再补 `| at the limit: J3 J5`，
见第 12.22 节）。`watch_line()` 与门禁测的是**同一个**数字，所以这一行变好的瞬间就是按 `a`
能成的瞬间。解码器不提供 `distance()` 时（`JsonLineDecoder`）退回只打状态。
`--print-rate` 只影响打印，控制循环仍是 `--rate`。

**厂商 SDK 的打印**：`VendorChatter` 在 fd 层面把 1/2 重定向到 `--arm-log`
（`app.py` 默认 `teleop_arm.log`，标定工具默认 `calibration_arm.log`），它构造与析构都会
打印（"ARX方舟无限"）。类现在住在 `backends.py`——`app.py` 与 `leader_calibrate.py` 都要用，
又都在 import 厂商后端，放在 `app.py` 会形成循环。程序自己的输出走它 `dup` 出来的那份
fd（`run()` 里的 `stream`），并且 `stack.close()` 排在 `arm.close()` **之后**，让 SDK 的
临别话也进日志。**1 和 2 分别 dup**：从 1 的副本恢复 2 会把被重定向的 stderr 丢掉
（这个 bug 已被 `VendorChatterTests` 固定）。

**序号冲突的解法**（不要改回去）：decoder 的 `seq` 与 `controller.last_seq` 是两个独立
空间。`control.py` 早就让 `stop` 豁免序号单调检查，现在把 `arm` 也纳入这条「操作员通道」
（`operator_arm()` / `operator_stop()`），二者都不碰 `last_seq`。这样 `protocol.py` 零改动，
`JsonLineDecoder` 也能直接配本地按键。**不要**引入 decoder 必须提供的共享 `SeqCounter`
隐式契约。

**门禁**：leader 映射未标定时 `--backend sdk --mode teleop` **拒绝启动**，解码器发不出
`arm`/`stop` 而 `--operator-keys` 又没开时同样拒绝。理由见第 9 节缺口 1。两个检查都是
decoder 侧 opt-in 的（`calibrated` / `provides_arm`），`JsonLineDecoder` 不声明这两个属性，
原有硬件路径不受影响。

同一种 opt-in 形式还用在**运行期**，但**装在 `Controller.pre_arm`，不是装在按键处理里**：
`app.install_arm_check()` 把 `decoder.anchor`（有的话）装上去，`_apply("arm")` 在
`state == "STOPPED"` 时先读一次实测位置、交给它，返回理由就
`controller.stop("refusing to arm: ...")` 并**不** arm（**不是** FAULT：这是要重新摆姿态、
不是按 `s` 能清掉的故障）。拒绝不锁存，摆好再按 `a` 就行。

**为什么不在 `app.py` 的按键路径上拦**（这一条是被审查逼出来的，不要改回去）：进 ACTIVE
有两条路——串口帧的 `arm` 经 `Controller.handle()` → `_apply("arm")`，本地按键经
`operator_arm()` → 同一个 `_apply("arm")`。`provides_arm` 只是**声明**：
`check_decoder_for_hardware()` 只在 `provides_arm is False and not operator_keys` 时拒绝，
缺省为 True，而且它只在 `hardware and teleop` 下被调用（mock 路根本不设防）；任何
`--decoder` 自定义模块都能自己 `return Command("arm", ...)`，声明 False 也拦不住。
"给 map 加一条 `anchor` 时断言 `provides_arm` 必须为 False"这种检查是**不够的**——
所以门禁下沉到两条路唯一的汇合点。

`JsonLineDecoder` 没有 `anchor`，`pre_arm` 保持 `None`，行为一字不变。
`reference_deg` 也不再被任何门禁读取，退化成标定出处记录。

### 6.2 标定工具（`leader_calibrate.py`）

`session` 交互式逐姿态采集（采集时机由操作者按键决定），`sample` 采一个姿态，
`fit` 把若干姿态拟合成 `leader_map.json`。**不 arm、不发 target**；`--arm` 会构造
`InterfacesPy`（厂商线程、构造先落 SOFT），然后**进重力补偿（状态 3）让机械臂托住自己**，
只调 `read_joints()`；不加 `--arm` 则完全不碰 CAN、不加载厂商库。

**`--arm` 是通电操作，不再是只读**：状态 3 是电机驱动（不是失能），退出前必须回到 SOFT。
两个子命令都自己保证这一点：

- `session`（有终端）：会话结束后**先问再松手**。`confirm_release()` 打印"机械臂仍在重力补偿，
  正托着自己"，读到回车/空格/`y`/`g` 才 `stop()` 回 SOFT；stdin 关闭（没人可问）也回 SOFT。
  这样既不会在操作者还在打字时突然掉落，也不会让进程退出后机械臂留在状态 3 无人驱动 CAN。
- `sample`（无终端）：没地方问，读完直接回 SOFT 并打印说明。
- **Ctrl+C / Ctrl+D 例外**：中断就是"现在要停"，因此 `run()` 不再吞 `KeyboardInterrupt`
  （只保留 `finally` 存盘），异常直接穿到 `main()` 返回 130，跳过确认提示；
  `finally` 里的 `close()` 仍会回 SOFT 并打印一行，操作者要准备好扶住机械臂。
- **SIGTERM 走同一条路**：Python 只把 SIGINT 转成 `KeyboardInterrupt`，SIGTERM 默认直接终止进程，
  `finally` 链根本不会跑——那会让机械臂停在驱动状态而进程已消失。`sample`/`session` 用
  `@treat_sigterm_as_interrupt` 装饰，把 SIGTERM 也抛成 `KeyboardInterrupt`，代价是终止时退出码也是 130。
  `fit` 不装饰：它不碰机械臂。
- `enable_gravity_compensation()` 只在 `active=False` 时可用（绝不在跟踪目标时切模式），
  失败时抛 `RuntimeError`；`close()` 无条件回到 SOFT，是最后的兜底。

`session` 与前两者的差别只在生命周期：SDK 起停很贵，操作者又要边摆边看角度，
所以一个进程里把两侧一直开着，用**最近 `--window` 秒（默认 1.5 s）的滚动窗口**当作"当前姿态"，
按键才落盘。测试通过注入伪 source/arm/keys/clock 把它变成确定性的（见 `InteractiveTests`）。

- 按键：`c`/回车采集、`d` 单点路径（见下）、`u` 撤销、`f` 拟合多个姿态并写 map
  （失败不退出，继续补姿态）、`q` 退出、`h` 帮助。`q` 提前退出会把已采姿态写进 `--out`
  并以**退出码 2** 结束——"采了一半"和"标定完成"必须能分开，事后可用 `fit` 接着用。
- 按键读的是 **原始字符**：为此把 `operator_keys.KeyInput.poll()` 拆成
  `read_keys()`（原始字符）+ `poll()`（映射成 arm/stop），后者行为不变，
  现有调用方与测试不受影响。
- 状态行显示每个还**没动够**的关节（所有姿态跨度 < `--min-span`），直接告诉操作者该摆哪个。
- 厂商 SDK 从 C++ 直接打印（构造与析构都会），会打乱原地刷新，因此
  `VendorChatter` 在 fd 层面把 1/2 重定向到 `--arm-log`（默认 `calibration_arm.log`），
  操作台用 `dup` 出来的那份 fd 重绘。**1 和 2 分别 dup**：从 1 的副本恢复 2 会把
  被重定向的 stderr 丢掉（这个 bug 已被 `VendorChatterTests` 固定）。
- stdin 不是终端时直接拒绝（管道/CI 下会空转到 EOF），那种场合用 `sample`。

原理：把机械臂和 leader 用手摆成同一姿态并同时读两边。一个姿态给出 `offset`
（前提是方向已知），姿态之间的变化给出方向。**第一个采的姿态是基准姿态**，
`unwrap` 的圈数从它数起。

**两条路径，单点那条是默认。**

**单点 + 手输方向**（`d`）：以已采的**第一个**姿态为基准，`InteractiveSession.start_directions()`
逐关节（J1..J6）问方向，`+`/`-` 作答、backspace 退一个、`x` 取消。提示行用
`live_step(index)` 显示该关节相对基准姿态的位移（`shortest_delta` 的 leader 位移 + arm 位移），
这就是操作者据以判断的证据。六个答完后 `answer_verify` 给三个出口：`c` 复核、回车直接写、`x` 取消。
**提示期间按键完全归提示**（`handle()` 先看 `awaiting`），所以 `q` 在那个状态下不退出——
要退先 `x` 取消；Ctrl+C 仍然直接中断（不经过 `run()`）。

- 写文件走 `single_point_map(pose, signs)`：`offset_deg = arm_deg - sign * raw_deg`，
  **故意不折进 ±180**——这个数就是字面意思，而映射恰好在这个基准姿态上精确成立。
  文件里带 `HAND_ENTERED_EVIDENCE` 注释，明说方向是人打的、错了会让关节镜像。
- **复核是有牙齿的**：`verify_directions()` 比较基准姿态与新姿态，`arm_step` 必须与
  `sign * leader_step` 同号；任一关节相反 → **点名该关节并拒绝写文件**；
  一步小于 `VERIFY_MIN_DEG`（5°）的关节记为"没动够、没复核到"；**一个都没复核到也不写**
  （否则会看起来像通过了）。复核用的是最新的姿态（`self.poses[-1]`），所以 `c` 可以按多次。
- 单点路径**没有数据能反驳手打的符号**，这是它与 `fit` 的取舍：`fit` 由数据自证但要多摆几次。

**多点拟合**（`f`，备用；也是无终端时 `sample` + `fit` 的唯一路径）已实现并已被测试固定的语义：

- 复用 `app.SerialInput`（`exclusive=True`）与 `LeaderUartDecoder`——**不重写线格式**。
  `SamplingDecoder` 只重写 `_decode`，把每个通过校验的帧记下来；采的是
  `Mapper.continuous`，即**加 sign/offset 之前**的展开角，正是标定要求的量。
- 窗口内每关节取**中位数**（一个翻转字节被多数票压掉）。**jitter（max−min）不是装饰**：
  它才是"操作者没扶稳 / 这一帧被翻转"的报警信号，中位数只负责给出估计值。
- 一帧坏帧只计数不致命（这不是安全路径），但会写进 pose 并在 sample 时提示。
- 拟合用**相对基准姿态的最近圈**展开（`unwrap_from_reference`），与运行期 `Mapper`
  从第一帧按最短路径展开的约定一致。真行程超过半圈时最短路径会选错圈，
  此时斜率会明显偏离 ±1，**被拒绝而不是被将就**。
- 喂进展开的必须是 **`raw_deg`**，不是 `continuous_deg`：后者展开自**采集进程**开始
  流数据的那一刻，而运行期是从**遥操作进程**的第一帧展开。两者差着整圈时，
  拟合出的 `offset_deg` 会整体偏 `360 * sign`，而斜率、跨度、残差**全都照常通过**
  （整圈被 offset 吸收），直到 arm 的那一刻才变成机械臂走 360°。见第 12.16 节。
- 判定：leader 跨度 ≥30°、|斜率| 与 1 的差 ≤0.05、最大残差 ≤3°。**任一关节不过就
  整个拒绝、不写文件**（没有 `--force`）：只标定一半的映射比没标定更危险。
- 写文件前先把它喂给 `leader_map.load_mapping` 读一遍——**加载器不收的映射比没有映射更糟**，
  因为门禁读的是同一个文件，会照样放行。

### 6.3 按 `a` 时的整圈锚定（单圈编码器看不出圈数）

`offset_deg = arm_deg - sign * raw_deg`，是在**基准姿态**上解出来的；而 `Mapper` 把
**进程收到的第一帧**当作展开原点（第一帧的 `continuous` 就等于它的 `raw`）。这两件事
各自没问题，合起来缺的却是**圈数**：单圈绝对编码器在任何一圈上读出的都是同一个
`0..359.9` 的数，`14.2` 和 `374.2` 是同一个读数。也就是说"这个 session 从哪一圈开始"
**在 leader 这一侧无法判定**（这正是第 12.15/12.17 节那套"必须从基准姿态启动"的来历：
既然判不了圈，就要求操作者把起点摆在唯一一个已知的圈上）。

**机械臂的实测姿态能判。** 它知道自己每个关节在哪儿，所以 `resolve_turns()` 逐关节
反解 `needed = (arm_deg - offset) / sign`，取
`turns = 360 * round((needed - continuous) / 360)`——一个**整圈**偏置——写进
`Mapper.bias`，之后每帧 `sign * (continuous + bias) + offset`，直到退出。剩下没被
整圈吸收的 `residual = continuous + turns - needed` 恒在 ±180° 内，**就是机械臂会被命令
走的量**（乘 `sign`），判据取它，超过 `ANCHOR_TOLERANCE_DEG`（30°）就拒绝。

三个刻意的取舍：

- **偏置只允许整圈**（用户 2026-10-03 的选择）。实数偏置能把残差压到 0，等于让机械臂
  瞬移到 leader 的读数上；整圈偏置只修圈数歧义，**剩下的差就是真实的手摆误差**，
  所以"30°"才是个有意义的手摆公差。
- **门禁保留，阈值 10° → 30°**。判据从字面差变成残差之后，`0/360` 另一侧的失真没了
  （见 §12.18 的实测数字），值本身也不再是"重复一个存储的数"而是"对齐两个物理姿态"，
  所以可以放宽。
- **`reference_deg` 保留但降级为出处记录**，不再被任何门禁读取。标定工具的生成文案
  也一并改掉——它原来在教用户"起手必须在基准姿态 10° 内"，改完那句话就是错的。

**残余不是零**：残差就是机械臂 arm 之后要走的距离（上限 30°）。这是设计的一部分
（arm 时以实测位置为起点，随后 ramp 到 leader 的位置），但要清楚它是"按下去之后
机械臂会动一小段"，不是"一动不动"。

**判据变了，两个数的关系也变了**（对比第 12.17 节）：以前是"字面差 −308.6° 判、最短圈
−51.4° 给人看"，**两个数差 6 倍**；现在判的是残差（J2 是 +51.4°），给人看的两个数是
`turn it`（`-residual`，手要转的）和 `would move`（`sign * residual`，机械臂会走的），
**大小都是 |residual|**——整圈那部分已经被偏置吸收掉了。符号由该关节的 `sign` 决定
（J2 是 −1，所以这一对在示例里同号，都是 −51.4°；`sign` 为 +1 的 J5 则是 −91.6° 对
+91.6°）。`shortest_turn()` 仍然只用于措辞。

**收到第一帧之前按 `a` 也拒绝**（没有读数就没有可以定圈的 `continuous`），
且是**返回理由**而不是抛异常——见 6.1 那条。

拒绝信息逐关节列出**所有**不合格的关节，而不是只报最差的那个：修好一个关节再重按、
然后才被告知还有一个不合格，是白跑一趟。

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
| `.venv/bin/python -m unittest discover -s tests -v` | 304 项通过，含真实 pyserial + PTY |
| leader 解码器离线测试 | 拆行、握手、`-1` 预热/故障、越界、缠绕展开、映射、`reset()` 语义 |
| leader 端到端（PTY，全 mock） | 字节 → 解码 → 映射 → 状态机 → 按键 arm/stop/FAULT 恢复 |
| 本地按键通道测试 | cbreak 的 termios 恢复、非 tty 回退、单批多键、fd 生命周期 |
| 标定工具测试 | 恒等/反向/带偏移、噪声、跨度不足、机械臂未动、非 1:1 斜率、姿态不互洽、跨绕圈点、拒绝写文件、生成的映射能被加载器读回并经 `Mapper` 复现采样到的臂角 |
| 交互式标定测试 | 注入伪 source/arm/keys/clock：滚动窗口只含当前姿态、撤销、未动够的关节被点名、`f` 失败留在循环里、整圈跑完写出可加载的 map、提前 `q` 以退出码 2 结束且留下的姿态能被 `fit` 直接使用 |
| 单点 + 手输方向（离线） | 六个 `+`/`-` 写出可加载的 map 并被 `Mapper` 复现出采样到的臂角；offset 不折 ±180；backspace 退格；`x` 不写文件；没有姿态/没有 `--arm` 时给出原因；复核通过才写、**位移与符号相反时点名拒绝**、**一个关节都复核不到也拒绝写**、没动的关节报为未复核（`DirectionTests` 用纯函数直接验这四种判定） |
| `session` 端到端（PTY 终端 + PTY 串口，无 SDK） | 真按键 → 真串口 → 采集 1 个姿态、退出码 2、arm.log 为空（未加载厂商库） |
| `VendorChatter` fd 重定向 | fd 1/2 都进日志、退出后两个 fd 都回到原目标（分别 dup，不共用副本）。类住在 `backends.py`（`app.py` 与 `leader_calibrate.py` 共用），测试仍在 `tests/test_leader_calibrate.py::VendorChatterTests` |
| 重力补偿接线（离线，无硬件） | `set_arm_status(3)` 恰好一次、跟踪目标时拒绝切模式、`close()` 后最后一条是 SOFT；`--arm` 的构造→进 3→读→`close()` 顺序；`confirm_release` 确认才 `stop()`、stdin 关闭也回 SOFT；**中断路径不进确认提示但 `close()` 仍执行** |
| SIGTERM 处理 | 真给自己发 SIGTERM：变成 `KeyboardInterrupt`（若未安装处理器，测试进程会被直接杀掉，不会静默通过）；处理前后 `SIGTERM` 处理器被恢复 |
| 重力补偿真机 | **操作者反馈"基本能用"**（2026-10-03，未量化）：跑完过一次 `session --arm`（1 个 301 帧、0 坏帧的姿态，见第 12.14 节），据此认为状态 3 能托住机械臂，标定流程不需要再等它 |
| 真机标定产物 | 已生成 `leader_map.json`（方向 `+ − − − + −`，手输，**未经第二姿态复核**），见第 12.14 节 |
| 整圈锚定与 arm 门禁（离线） | `resolve_turns` 的整圈性质（`turns` 是 360 的整数倍、残差恒在 ±180° 内、残差 ≡ −`shortest_turn` 模一圈，两函数钉在一起防漂移）、30° 边界两侧、跨 `0/360` 的 10° 必须放行（旧判据报 −350°）；`Mapper.anchor` 只在 `ok` 时写 `bias`、`reset()` 连 `bias` 一起清、`bias` 只进 `to_radians` 不污染 `continuous`（标定工具读它）；拒绝信息给"要转多少"与"会走多少"（大小相等，`-residual` 对 `sign * residual`）并列出**所有**不合格关节；解码器 `anchor()` 在首帧离 `reference_deg` 好几百时仍放行、没帧时**返回理由而不是抛**、握手/`reset()`/`ProtocolError` 后清偏置需重新 anchor、没 anchor 过时 `leader.anchor` 是 `null`；`Controller.pre_arm` 的**两条 arm 路都过**（串口帧与本地按键各一条测试）、被拒时 `arm.writes` 为空且 `arm.start` 未被调用、FAULT 下不触发 hook；map 校验 `reference_deg` 的长度/数值/`0..360` 区间（字段保留但不再是门禁）；PTY 端到端：左右同姿态→`a` 进 ACTIVE、偏 90°→`reason` 点名 J3 且 `joints_rad` 全程为 0（机械臂一个目标都没收到）、移回去重按即进 ACTIVE、首帧之前按 `a` 被拒、跨 `0/360` 的 10° 装上 360° 偏置并继续同向跟随 |
| 状态行打印节流（离线） | `due_for_print` 直接单测：未到间隔不打、到点打、`state` 变立刻打、**`state` 不变而 `reason` 变也立刻打**、同一条不重复打；PTY 里把 `--print-rate` 压到 1 Hz 跑约 2 s，记录数必须仍是"几条"而不是随 100 Hz 控制循环走（**把 `next_print` 改成每轮都到期，这条即以 60+ 条失败**），见第 12.19 节 |
| `--watch` 单人可读输出（离线） | `watch_line` 直接单测：六个关节的转角与 `+6.1f` 对齐、`out of pose` 点名列出的关节与容差、全部在容差内时写 `in the arm's pose, press a`、没帧时写 `waiting for the leader's first frame` 且**不打 J1**（打 0 会被读成"已经在姿态里"，是唯一错误答案）、ACTIVE/FAULT 只报状态与理由（ACTIVE 且有关节被限幅时尾部补 `at the limit: J3 J5`，测试里的假 controller 必须显式给 `saturated`——`Mock` 自动生成的属性为真且不可迭代）、没有 `distance()` 的解码器也能出一条行；PTY 里 `--watch` 真的打出**行**而不是 JSON（含 `J1`/`J6`、不含 `{`）、`a` 之前写 waiting、按 `a` 后下一行是 `ACTIVE ... armed at measured position`（成功 arm 会变 `state`，这条认不出节流退化；认得出的是 `PrintThrottleTests` 里"`state` 不变而 `reason` 变"那条）。见第 12.20 节 |
| 越界限幅与点名（离线） | 目标越界**不限幅为异常、也不停机**：六个分量各自夹到边界、被夹的关节记进 `saturated`、控制保持 ACTIVE，再发一帧范围内的 target 即恢复（同一个序列继续）；被夹在边界上时机械臂滞后 0.05 rad（在 `max_following_error` 内）走完整拍而不 FAULT——**把 `tick()` 里那条绝对越界检查加回去，这条即以 FAULT 失败**；`stop()` 清空 `saturated`。**机械臂实测**越界仍然拒绝 arm，`Limits.outside()` 逐关节给 `J6 +2.000 not in [-1.000, +1.000]`，走 `refusing to arm: ...` 而**不是抛异常**（按键路在解码器 guard 之外，抛出去会退出 2）；机械臂离指令 2.0 rad 时由 `joint following error` 兜住，是 FAULT 而非异常（`tick` 在 guard 之外，抛出去会穿到 `main()` 退出 2、屏上只剩 ERROR）。见第 12.22 节 |
| 指令轨迹：跟踪微分器（离线） | `td.py` 是 `ref/adrc.c` 的 `fst`/`TDFunction_independent` 逐项转写，用性质而非重算钉住：远场加速度恒等于 `r`、误差为零且静止时输出为 0、任意误差/速度下 `\|fst\| <= r`、静止时加速度方向与误差相反；六组 r × 五档 dt × 六种步长的**步响应从不越过目标**（这正是"指令不会自己出界"的依据）、最终停在目标上（1e-9）、速度被 `max_speed` 夹住、同一时刻 r 大的关节走得更远；**多圈**：350→370 单调穿过 360（不折回时把误差按 ±180 折一下即失败），700→730 照常收敛；`dt<=0` 原地不动、长度不符抛 `ValueError`。`control.py` 侧：arm 后第一拍就停在实测位置（步长 0 的跳变）、同一目标下一拍位移大于上一拍（还在加速）、全程不越过目标、`td_r_deg` 与 `max_speed` 分别可配置地起作用、多圈 target 穿过 360° 不回摆（`Limits((-10,)*6,(10,)*6)`）、`td_r_deg` 非法（长度、0、负数、字符串）在构造时报 `ValueError`。见第 12.23 节 |
| 关节增益不可调（离线反汇编） | 三条独立证据：pybind 只导出位置/位姿/夹爪/模式/读取；`k_p`/`k_d` 在整份 DWARF 里**只**作为 `HybridJointCmd` 的字段名存在（控制器成员没有同义名字），且 `statePositionControl()` 里它们来自控制器成员、不是调用参数；`.so` 不引用任何配置文件名、无 `ifstream`/`fopen`，所以增益是二进制内常量。仓库里也没有控制器源码（`CMakeLists.txt:22` 只 `target_link_libraries` 预编译 `.so`）。见第 12.24 节 |
| `fit` 的锚点（离线） | 夹具把 session 的 `continuous_deg` 整体挪一圈（`raw` 不变）后，写出的 map 仍能被新 `Mapper` 从 `raw` 复现出记录的臂角；**把这一行改回 `continuous_deg` 该测试即以 360.0 的差值失败**（三条测试同时失败），见第 12.16 节 |
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

leader 解码器还额外在 Robot PC 上对着**真实串流**跑通（见第 12.8 节：211 Hz、零错误），
但**只在模拟机械臂上验证过，从未驱动真机**。上表「实机读角度、串口控制器、运动：
未测试」的结论对本节工作机仍然成立。

## 9. 下一位 agent 的具体工作顺序

1. 阅读本文和 README，检查 Git 状态，跑模拟测试建立基线。不要重复克隆旧父工程。
2. 若继续实机阶段，取得 Robot PC 的系统版本、CPU 架构、实际型号、USB2CAN 类型、
   CAN 接口名和遥操作器串口名；这几项目前未确认。
3. 在具备兼容 KDL 库的环境安装 SDK，确认 `.sdk/READY` 产生，运行 preflight。
   preflight 只检查导入/设备，不证明电机在线或反馈新鲜。
4. 支撑机械臂，先用 monitor 验证 SOFT 与六关节读数方向/单位，再校准限位。
   保留外部急停，验证停止/断流的实际行为；不要自动回零或发送示例绝对位置。
5. leader 解码器已接入（第 6.1 节），标定工具已就绪（第 6.2 节）。
   **下一步是采一个姿态、手输方向**：交互式跑
   `bash scripts/calibrate.sh session --arm --model 2023 --can-port can0 --serial <by-id>`，
   把两边摆成同一姿态按 `c`，然后按 `d` 逐关节回答方向（`+`/`-`，提示行会显示该关节动到哪了），
   最后**建议按 `c` 挪到另一个明显不同的姿态复核一次**再写 `leader_map.json`；
   复核不过或想由数据自证，就多摆几个姿态按 `f` 走多点拟合。
   **`--arm` 会让机械臂进重力补偿（状态 3，电机驱动）**：先在支撑好、手能扶到、电源够得着的
   条件下确认它真的托得住（会因 URDF 不含实际负载而缓慢漂移，这是预期），再开始采集。
   结束时工具会**停下来问**，等你确认支撑好、按回车才交回 SOFT。没有任何外部急停，
   所以人不能离开；Ctrl+C 会立刻回 SOFT，按之前先扶住。
   用户已确认 leader 与 X5 关节配置相同、连杆长度略有差别，
   所以拟合斜率必须≈±1；不通过就重摆姿态，不要放宽容差。
   门禁会一直挡着实机 teleop，直到 `leader_map.json` 上写了 `"calibrated": true`。
   **第一个采的姿态是基准姿态**：交互模式已经把它的原始角度写进 map 的 comment。
   手输方向这条路**没有任何数据能反驳符号**，所以复核那一步不是走过场。
6. 标定之后再处理第 9.1 节列出的两个解码器缺口（冻结值、值域内静默错误），
   然后才做低速实机控制，并从 mock 换成 `--backend sdk`。
   **2026-10-03：标定已做（第 12.14 节）、重力补偿已由操作者确认可用，所以卡在这里的是
   9.1 的缺口 4（起始帧不校验）与"方向未经复核"。**下述首次实机 teleop 步骤把它们降级为
   人工核对，但**代码层面仍未修**：

   ```bash
   # limits.json 需自己从 limits.example.json 抄一份（不在仓库里）
   bash scripts/run.sh --mode teleop --backend sdk --model 2023 --can-port can0 \
     --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
     --decoder leader_decoder.py --operator-keys --limits limits.json
   ```

   `a` = arm、`s`（或空格）= stop，需要**真终端**（`--operator-keys`）。机械臂未 arm 时
   程序不会写任何目标。

   - **按 `a` 前把 leader 摆成和机械臂一样**（不是"摆回 `reference_deg`"——那条规则
     2026-10-03 已作废，见第 6.3、12.18 节）。程序自己会拦：任何关节的整圈残差超过 30°
     就拒绝 arm，`reason` 里逐关节写出 "reads 14.2 deg where the arm's pose calls for 322.8
     (turn it -51.4 deg)"，机械臂一个目标都不会收到。`turn it` 是手要转的，紧跟的
     `would move J2 -51.4 deg` 是机械臂会走的，**大小相等**（符号由该关节的 `sign` 决定，
     J2 是 −1 所以两个同号；J5 是 +1 则反号）。
     **实测那份 leader 现在会被拒**：J2 残差 51.4°、J5 残差 91.6°，都在 30° 之外；
     把两边摆成同一姿态再按。
     `leader.anchor` 是**按 `a` 那一刻的快照**，不随 leader 移动更新，所以照着挪要另开
     一个进程看实时值（`--backend mock` 那条命令）。
   - **按 `a` 之后机械臂会走一小段**：残差（上限 30°）就是它要走到 leader 位置的距离，
     不是"一动不动"。手别扶着。
   - **按 `a` 之前是 STOPPED**，teleop 已在读 leader 并打印。**收到第一帧之前按 `a` 会被拒**，
     所以先等 `leader.frame` 出现（这同时确认了流是活的）。
   - **默认 `--print-rate 10` 在真终端上读不过来**（一行是一整条 JSON）；用
     `--print-rate 1`（或过滤 stdout 只留状态变化，命令见 README「按键控制」）。
     调低不会漏掉按 `a` 的结果：`state` 或 `reason` 一变就当场打一行，见第 12.19 节。
     判断 `a` 有没有被处理过，看 `leader.anchor` 是不是 `null`。
   - 只动**一个**关节一点点，确认机械臂同向；反向立刻按 `s`。方向是手输且未经复核的。
   - `limits.json` 目前只能用 `limits.example.json` 抄一份——**限位本身还没在实机上校准**，
     而它的 J2/J3 下限是 0.0，机械臂零位却在 0.006 rad 附近。第 12.22 节起：
     **越界的 target 只被限幅**，顶在边界上继续跟随，不再中断会话；
     但**机械臂实测位置在界外时仍然拒绝 arm**（`refusing to arm: ...`，点名关节）。
     也就是说这套限位下 J3 实测 +0.45° 还能进，J5 实测 −90.15° 进不去——
     按厂商规格把这几轴的下限改成负数再启动，别靠限幅绕过。
7. 如要求真正失能，需厂商提供关闭/失能及失能后读反馈的正式 API/协议，当前不能承诺。
8. 每个小改动验证后提交推送，更新本文的验证边界和未完成事项。

### 9.1 解码器已知缺口（接实机前必须处理）

1. **零位不可知。** leader 报的是单圈绝对角，没有自己的零点。`sign` / `offset_deg`
   错了**不会失败得很安全**：它指向的是一个关节限位完全接受的真实位置。不标定就 arm，
   机械臂会朝错误位置走。**2026-10-03 已在实机上应验**（不是零位，是限位本身没标定，
   见第 12.21 节）：第一次真机遥操作 arm 成功、两三秒后撞的正是这套限位。
   当时的处理是 FAULT；现在改成**越界 target 限幅、只点名不中断**（第 12.22 节）。
   `limits.json` 仍然只能用示例抄一份——**限位本身还没在实机上校准**，这条缺口没关：
   限幅只是让撞界不再终结会话，限位数值本身错得离谱时限幅一点用都没有。
2. **冻结值抓不到。** 文档 §2 说编码器采到过数据后又断开会**冻结在最后一个有效值**，
   `-1` 判据完全抓不到这种坏法，而冻结值看起来是一个完美的稳定读数。
   需要「N ms 未变化」的存活性判定。本轮只计数/打印。
3. **值域内的静默错误抓不到。** `2117 → 2717` 这种翻转仍落在 `0..3599` 内，
   越界检查看不见。限速与指令轨迹只限制单拍步长和加速度，长期仍会跟过去（第 12.23 节）。
   需要可选的最大跳变过滤。
4. ~~**`unwrap` 的原点依赖"按基准姿态启动"**~~ —— **2026-10-03 已修，见第 6.3 节、
   第 12.15 节与第 12.18 节。** 修法换了两次：12.15 是"把第一帧与 `reference_deg`
   逐关节比对、超 10° 就拒绝 arm"，只能要求操作者把起点摆在唯一已知的圈上；12.18 改成
   **按 `a` 时用机械臂实测姿态定整圈偏置**，`0/360` 两侧的失真随之消失，判据也换成
   残差。`reference_deg` 不再是门禁，只是出处记录。
5. **文档待更正（不改用户文档，在此记录）。** `docs/uart_packet.md:21` 称
   「`/dev/ttyACM0` 不是这块板的串口」，在本机被证伪：
   `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00` 正指向 `ttyACM0`。
   更要紧的是 **CANable2 与 CH340 都是 `/dev/ttyACM*`**，编号随插拔顺序变，
   必须一律用 by-id，否则可能误占 `slcand` 正在用的 CAN 适配器端口。

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

## 12. Robot PC 实机环境记录（2026-10-02，与第 8 节不同的机器）

本节是连接了 USB2CAN 与 ARX 机械臂的那台 PC 的实测结果。**不要用第 8 节
（Ubuntu 26.04 工作机）的结论覆盖本节，反之亦然。**

### 12.1 环境（已实测）

- Ubuntu 22.04.5 LTS (Jammy) / x86_64 / Python 3.10.12。
- 交互式 shell 已 source **ROS 2 Humble**，`LD_LIBRARY_PATH` 含 `/opt/ros/humble/lib`。
  厂商核心库依赖的 `libkdl_parser.so`、`liburdf.so` 正是由它提供，`liborocos-kdl.so`
  来自 `/lib/x86_64-linux-gnu`。这些路径**没有**写进 `/etc/ld.so.conf.d/`，
  所以在未 source ROS 的 shell 里 `ldd` 会报 not found —— 那是环境没加载，
  不是缺依赖。**第 8 节"本机缺 KDL 运行库"的结论不适用于本机。**
- 因此本机满足 `--skip-system` 条件，无需 apt 安装 `libkdl-parser-dev`。

### 12.2 SDK 重编译（已完成）

```bash
bash scripts/install_dependencies.sh --sdk --skip-system
```

- 用系统 python3.10 建 `.venv`，装了 pyserial 3.5 / numpy 2.2.6 / pybind11 3.1.0。
- 两个绑定按 `cpython-310` 重编译并安装到 `.sdk`，写入 `.sdk/READY`（内容 `cpython-310`）。
- 脚本自检输出 `SDK Python imports passed. No robot was constructed or commanded.`

这是仓库自带 `cpython-312` 扩展在本机不可用的正解：**用本机解释器重编译**，
不是改名或软链接。

### 12.3 preflight（已通过）

```bash
bash scripts/run.sh --mode preflight --backend sdk --model 2023 --can-port can0
# 退出码 0；errors 为空；sdk_import: ok (no arm constructed)
```

只证明扩展可导入、`can0` 是 SocketCAN，**不证明机械臂在线或反馈新鲜**。

### 12.4 USB2CAN 适配器（已实测）

| 项目 | 实测结果 |
| --- | --- |
| 型号 | CANable2，USB `16d0:117e`，序列号 `207235C34831` |
| 固件 | **SLCAN**（枚举为 CDC-ACM），不是 gs_usb 原生固件 |
| 固件版本串 | `16e7497-dirty github.com/normaldotcom/canable2.git` |
| 当前节点 | `/dev/ttyACM1` |

- **`ip link set can0 type can bitrate …` 路线不适用**，必须走 `slcand`：

  ```bash
  sudo slcand -o -f -s8 /dev/ttyACM1 can0   # -s8 = 1 Mbps
  sudo ip link set can0 up
  ```

- `-f` 的语义是"读状态标志以复位错误状态"，**不是**前台运行（前台是 `-F`）。
- 该固件是精简实现：只有 `V`（版本）有回显，标准 LAWICEL 的 `S`/`O`/`C`/`F`/`N`
  都不返回任何字节，**无法用 `F` 读取适配器侧状态标志**。
- `/dev/ttyACM0` 与 `/dev/ttyACM1` 的编号会在重新插拔后互换（dmesg 中已观察到多次）。
  写脚本用稳定路径 `/dev/serial/by-id/usb-Openlight_Labs_CANable2_…-if00`。

### 12.5 必须记住的坑：SocketCAN 本地回环

发送帧时，`candump can0` 和 `ip -s link show can0` 的 RX 会计会**显示本进程自己发出的帧**。
因此：

- 只要本进程发过帧，`candump` / RX 计数就**不能**当作"机械臂在线"的证据；
- 只有在**完全不发送**的纯监听窗口里 `RX = 0` 才可信（本机实测：6 秒静默无帧）。

### 12.6 实机连通性（已证实）

```bash
bash scripts/run.sh --backend sdk --mode monitor --model 2023 --can-port can0 --duration 3
```

- 退出码 **0**。SDK 打印 `SocketCAN adapter created` → `Successfully bound socket to
  interface N` → `ReciveThread running` → `Init completed`。
- **读到变化中的真实六关节反馈**（30 次采样，各关节跨度 0.0006–0.019 rad），
  说明主机与电机是双向通信，不是全零占位值。当时机械臂停在近零位姿。
- 退出时状态为 `STOPPED / reason=program exit / stop_mode=soft`，厂商线程正常收尾
  （`[ArmThread] finish close` → `ReciveThread finish` → `CAN socket destroyed`）。
- 结论：**PC → CANable2 → `slcan` → SocketCAN → 机械臂全链路连通。**
  适当前提：用户已确认 CAN_H/CAN_L 已接线、机械臂已上电、实物型号 **2023**
  （type=0，`x5.urdf`）。

### 12.7 两条重要观察

1. **SDK 的关闭路径会调用 DisableMotor。** 退出日志出现 `[ArmThread] DisableMotor`。
   核心库确实有 `setEnableMotor`/`packDisableMotor` 符号，但 Python 的
   `InterfacesPy` **没有公开这套接口**，且它只在析构/关闭时发生，**无确认反馈，
   也不能在进程存活期间主动进入**。因此第 1 节"停止用 SOFT 零力矩"的结论不变，
   不要把退出时的这次调用等同于可操作的运行期失能模式。若确实需要运行期失能，
   仍要厂商提供正式 API 与失能后读取反馈的说明。
2. **URDF 的 KDL 警告可忽略。** `[kdl_parser]: The root link base_link has an
   inertia` 来自厂商 URDF，不影响关节读取。

### 12.8 leader 遥操作器串流（已实测，仍未驱动真机）

`docs/uart_packet.md` 的规格在本机对真实串流验证过（纯解析、`--backend mock`、不碰 CAN）：

```bash
ls -l /dev/serial/by-id/
# usb-1a86_USB_Single_Serial_5AE8010651-if00 -> ../../ttyACM0   (leader, CH340)
# usb-Openlight_Labs_CANable2_..._20734831-if00 -> ../../ttyACM1 (USB2CAN)

bash scripts/run.sh --mode teleop --backend mock \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
  --decoder "$PWD/leader_decoder.py" --print-rate 5 --duration 5
```

- 实测 **798 帧 / 3.79 s ≈ 211 Hz**（规格写 200 Hz），`dropped=0 no_data=0 resets=0`，无错误。
- 六个关节在该次运行中全部停在 0.0° 跨度。**无法区分「leader 静止」和文档 §2 的
  「编码器先工作后冻结」**——要确认必须实际移动 leader，本轮没有做（见第 9.1 节缺口 2）。
- 全程 mock 机械臂，**没有 arm 过、没有开 CAN、没有加载厂商库**。

### 12.9 本节未做

- 实机运动、限位校准。
- 移动 leader 以确认编码器跨度（第 12.8 节的未决观察）。

### 12.10 交互式标定（2026-10-02，软件已完成，标定尚未做）

- leader **没动**已确认：第 12.8 节"停在 0.0°"是真实静止，不是冻结编码器。
- `leader_calibrate.py session` 已实现（第 6.2 节）并全部离线验证：163 项测试通过。
- leader 真机冒烟：`sample --arm --model 2023 --can-port can0` 在机械臂支起、
  SOFT 状态下跑通，读回接近零位的六个角度后干净退出；构造与析构期间
  `InterfacesPy` 的 stdout/stderr 被 `VendorChatter` 收进日志。
- 全程**没有 arm、没有发 target**。退出日志里的 `DisableMotor` 来自 SDK 析构，
  不是本工具发出的（与第 12.7 节一致）。
- `/tmp/leader-smoke.jsonl`、`/tmp/arm-smoke.jsonl` 是冒烟产物，**不是**配对姿态，应丢弃。
- 真正标定需要操作者用手把 leader 与机械臂摆成同一姿态（机械臂 SOFT 零力矩可拖动，
  但会因重力下落，**必须已支撑**；现场没有外部急停，全程不要 arm）。
- 用 `--backend sdk` 试跑 leader teleop：门禁会拦下未标定的映射，这是预期行为。

### 12.11 标定改用重力补偿（2026-10-02，软件已完成，真机未验证）

- 起因：SOFT 下要一只手托着机械臂、另一只手按键，标定基本没法做。
- 确认**不需要动 pinned 快照**：`InterfacesPy::gravity_compensation()` 既没绑到 Python
  也没导出到 `.so`，但 `set_arm_status` 已绑定，`.rodata:0x32040` 的跳转表把 3 映射到
  `stateGravityCompensation`（与第 5 节表格一致），厂商 `bimanual/script/single_arm.py:117`
  用的也是它。厂商 `SingleArm.__init__` 的构造 + `arx_x(500,2000,10)` 与我们的 `VendorArm.__init__`
  已经一致，所以只是多一次调用。
- `backends.VendorArm` 加 `GRAVITY_COMPENSATION = 3` 与 `enable_gravity_compensation()`：
  只允许从停止态进入，`stop()`/`close()` 本来就回 SOFT，即兜底路径。`stop_mode` 与
  `app.py` 遥操作路径**没有改动**——状态 3 不是停止模式。
- `leader_calibrate.py`：给了 `--arm` 就自动进 3（用户确认不做独立开关），
  `session` 退出前 `confirm_release()` 问过才回 SOFT，`sample` 无终端则自动回 SOFT 并打印。
  Ctrl+C 不再被 `run()` 吞掉，直接穿到 `main()` 返回 130 并跳过提问，`close()` 仍回 SOFT。
- 修掉文案里所有"只读/一直停在 SOFT"的说法（工具 docstring、`draw()` 表头、`h` 帮助、
  两个 `--arm` 帮助、`scripts/calibrate.sh` 注释、README 标定一节）。
- 顺带补上 `sample`/`session` 的 SIGTERM 处理：以前 SIGTERM 会直接终止进程、`finally` 不执行，
  在 SOFT 下只是损失几个姿态，在状态 3 下就变成"机械臂还在出力而进程没了"。
- 离线验证：175 项测试通过（新增 12 项，见第 8 节表格）。顺序与中断路径都用 mock 厂商类固定。
- **状态 3 从未在真机上跑过**：力矩来自 KDL + URDF 动力学，实际负载/夹爪不在模型里就会缓慢漂移；
  下一步真机验证必须支撑好、有人扶着、电源够得着，先看它是托住还是下沉/漂移再决定用不用。
- 2026-10-03 操作者两次在 Robot PC 上跑 `session --arm`：先报"已经正确启动了"（命令行、串口、
  进入路径都不报错），后报**"重力补偿基本能用，不用管"**。据此状态 3 由**未验证**改为
  **操作者确认可用**——但没有量化记录（托住多少、漂移快慢都没测），第 8 节那一行据此措辞。
  力矩精度对重力补偿本身够用，但**这不能推广成"位置保持可靠"**：状态 3 仍然是驱动状态。

### 12.12 标定改成单点 + 手输方向（2026-10-03）

- 起因（用户要求）：**"只取一个点，然后让我自己观测关节方向，然后我自己输入终端"**。
  一个姿态 + 已知方向就能精确解出零位，所以多点拟合不是必需的。
- 用户确认的三点：逐关节依次提示（J1..J6，各答 `+`/`-`）；`fit` 那套**保留为备用**；
  写文件**前可选复核**一次。
- `leader_calibrate.py` 新增 `single_point_map()`、`verify_directions()`、`shortest_delta()`、
  `HAND_ENTERED_EVIDENCE`，`InteractiveSession` 加 `d` 键与 `direction`/`verify` 两个待答状态，
  `draw()` 用 `>` 标出正在问的关节并显示 `live_step()` 的 leader/arm 位移。
- 复核**不是走过场**：位移与符号相反 → 点名拒绝写；一个关节都复核不到 → 也不写（否则看起来像通过）；
  没动够（<`VERIFY_MIN_DEG`=5°）的关节报为"未复核"。写了 map 会带 `HAND_ENTERED_EVIDENCE` 注释，
  明说方向是人打的、错了会让该关节在离开基准姿态后镜像。
- 已实现并测得 195 项通过（新增 `DirectionTests` 6 项 + `InteractiveTests` 10 项）。
  `DirectionTests` 里专门钉住了**符号与实际位移方向解耦**这一点：基准姿态对里有的关节
  位移为负，`+` 仍必须判为一致——这正是 `verify_directions()` 第一版写错的地方
  （曾写成"两边都为正才算一致"，会把所有反向移动的关节误报为矛盾）。
- **单点路径与 `fit` 的取舍**：`fit` 由数据自证但要多摆几次；单点快，但**没有任何数据能反驳
  手打的符号**，复核是唯一的保护。这一点同时写进了 README 的标定一节和生成文件的注释。

### 12.13 一次真机退出日志的判读，与一处 SDK 版本疑点（2026-10-03）

操作者在 Robot PC 上跑完一次标定后贴来了 SDK 的关停输出：

```
DisableMotor
[Controller] waiting for thread finish
[ArmThread] DisableMotor
[Controller] waiting for thread finish
[Controller] waiting for thread finish
[ArmThread] finish close
[Controller] thread finish
DisableMotor
Destroying SocketCAN adapter...
Waiting for receiver thread to terminate.
terminate_receiver_thread_ is true
waitting receiver_thread close
ReciveThread finish
receiver_thread_running_.load()
return
CAN socket destroyed.
finish
```

判读：**这是正常关停，不是报错。** 逐行对应到本机 `.sdk` 的二进制（每个字符串的出处都用
反汇编定位过，见第 5 节）：`[ArmThread] DisableMotor` 与 `[ArmThread] finish close` 来自
`ControllerThread::ArmThread()` 的收尾；`[Controller] waiting for thread finish` 与
`[Controller] thread finish` 来自 `ControllerThread::~ControllerThread()`；`Destroying SocketCAN
adapter... / CAN socket destroyed. / finish` 来自 `SocketCan::impl::~impl()`；`ReciveThread finish`
来自 `SocketCan::impl::ReciveThreadWrapper()`。**没有一行是异常路径。**

**疑点（要查，别忽略）**：这份日志有两处字符串与 pinned 快照/本机 `.sdk` **对不上**：

| 日志里 | 本机所有副本里 |
| --- | --- |
| `DisableMotor`（两处，无前缀） | 只有 `[ArmThread] DisableMotor`，没有裸标签（已对仓库内每个 `.so` 逐字符串搜过） |
| `[Controller] thread finish` | `@[Controller] thread finish`（多一个 `@`） |

同一份源码编译出来不应该差这两个字符，所以最可能的解释是 **Robot PC 上加载的
`libarx_x5_src.so` 与本仓库 pin 的这份不是同一次构建**（可能是更早的 checkout，或系统里另装了一份）。
这件事要紧，因为第 5 节状态编号（尤其 `set_arm_status(3)` = 重力补偿）是从**本机**二进制推出来的。
下一步在 Robot PC 上做两件事即可确认：

```bash
sha256sum .sdk/bimanual/api/arx_x5_src/libarx_x5_src.so   # 与本机比
strings .sdk/bimanual/api/arx_x5_src/libarx_x5_src.so | grep "thread finish"
```

若哈希不同，就在**那台机器**上重做一次第 5 节的核对（`nm -DC` 找
`stateGravityCompensation`、`InterfacesThread.hpp` 的枚举），再谈真机标定。

### 12.14 第一次真机标定的产物：做出了 map，但**没做复核**（2026-10-03 00:17）

同一次运行在仓库根目录留下了三个（已被 `.gitignore` 忽略的）产物，是真机产物，别当垃圾删：

| 文件 | 内容 |
| --- | --- |
| `calibration_session.jsonl` | 1 个姿态，301 帧，0 坏帧，jitter ≤1.0° —— 采集本身干净 |
| `leader_map.json` | `calibrated: true`，六个方向为 `+ − − − + −`，均为手输 |
| `calibration_arm.log` | 115 KB 厂商 C++ 输出（正常关停序列见 §12.13） |

参考姿态：leader raw `75.5, 322.8, 96.4, 258.0, 309.7, 218.4`，
arm `-0.08, 0.34, 0.60, 1.39, -0.01, 0.45` 度 —— **六轴全在 1.4° 以内**，
即操作者把"基准姿态"取成了机械臂的零位姿态，于是 `offset_deg ≈ -sign * raw_deg`。
这本身没问题（基准姿态可以任选），但它意味着这个 map **只在零位姿态附近被测过**。

**要紧的一点：这次没有用第二姿态复核**（session 里只有 1 个姿态，文件注释也是
`HAND_ENTERED_EVIDENCE`）。方向是人打的，而**打错不会失败得很安全**：map 在基准姿态上
仍然完全正确，只在离开基准姿态后镜像。所以在拿它跑实机 teleop 之前，建议重跑一次
`session --arm`：把 leader 摆回同一基准姿态按 `c`，再明显挪到另一个姿态按 `c` 复核——
复核通过再信这份 map（重跑得到的 map 应当与此文件一致）。

另注：`leader_map.json` 就在仓库根目录，所以**在这个目录里，硬件 teleop 的门禁已经被打开**
（`--backend sdk --mode teleop` 不会再因"未标定"被拦）。这是文件本身的作用，不是 bug，
但别在不打算驱动机械臂的时候把它留在手边。

顺带修掉一处被这份文件暴露出来的测试脆弱性：`test_run_refuses_before_any_motor_is_constructed`
原先依赖**工作目录里没有 `leader_map.json`**（解码器的默认路径就是 `./leader_map.json`），
真机标定一做，这个门禁测试就会转而尝试打开串口并以 `SerialException` 失败。
现在它显式指定一份未标定的 map 并用 `patch.dict(os.environ)` 隔离环境，与 cwd 无关。

### 12.15 补上 9.1 缺口 4：运行期校验基准姿态（2026-10-03）

用户选了缺口 4。这是**纯软件改动，全部离线验证**，没有碰真机、没有碰 SDK。

**先说一处对缺口 4 原始描述的更正。** 原文写的是"标定时的基准姿态与运行期的起始帧
不一定同一个圈：差一圈，所有目标整体偏 360°"。**整圈的差是看不见的**：
单圈编码器在一圈之外报同样的读数，`Mapper` 以第一帧为原点，两边得到的 `continuous`
完全一致，所以"差一圈"既不报警也不出错——它根本不是可观测的情形。
真正会发生的是**一段可观察的起始偏置**：leader 起始原始角与 `reference_deg` 差多少，
映射就整体平移多少，机械臂一 arm 就朝那个方向走多少。偏移后的位置对限位来说是个
正常位置，`Limits.check()`（现为 `Limits.clamp()`，见第 12.22 节）、`max_following_error`、限速都看不见。
第 6.3 节按这个语义重写了。

**改动**：

- `leader_map.py`：map 新增**结构化字段** `reference_deg`（基准姿态的原始角，
  不再只写在 `comment` 里给人和正则看）；`check_reference()` 直接相减逐关节比对，
  返回 `{checked, ok, tolerance_deg, worst_joint, worst_deg, offsets_deg}`；
  `REFERENCE_TOLERANCE_DEG = 10.0`。缺字段 → `None`（老 map 与手写 map 照常加载）。
- `leader_decoder.py`：首个**六维有效**帧判一次（`-1` 预热帧不判，它进不了 mapper）；
  结果放进 `last_telemetry["reference"]`；`_restart_origin()` 统一了 `reset()`、
  握手行与 `ProtocolError` 三处换原点的地方，三处都会**重新待判**；
  `startup_blocker` 暴露拒绝理由，**没收到帧也返回理由**。
- `app.py`：`apply_operator_arm()` 在 `STOPPED` 下看到 `startup_blocker` 就
  `stop("refusing to arm: ...")`（不是 FAULT——原点已经定了，按 `s` 清不掉，
  只能重启进程）。
- `leader_calibrate.py`：`build_map()` 写 `reference_deg = poses[0]["raw_deg"]`，
  注释里那段"差一圈偏 360°"的说法一并改掉。

**关于 `reference_deg` 缺失时的取舍**：不拦，只在 `leader.reference` 里报
`{"checked": false}`。理由是这与仓库既有门禁同构（`calibrated` / `provides_arm` 都是
decoder 侧 opt-in，`JsonLineDecoder` 不声明就不受影响），而且缺失态是**"没有保护"**
这个既有状态，不是**"已知错误"**——拦它反而会让所有老 map 直接不能跑。
代价是这份 map 的 `reference_deg` 必须补上，否则这层保护对它是空的。
**这件事已经做了**：仓库根目录那份 `leader_map.json`（gitignored）已加入
`reference_deg`，值直接取自 `calibration_session.jsonl` 第一个姿态的 `raw_deg`，
并逐关节用 `sign * raw + offset` 复算过，与同一姿态记录的 `arm_deg` 六维全部吻合到
小数点后 4 位（J1 −0.0765、J2 0.3388、J3 0.6011、J4 1.3879、J5 −0.0109、J6 0.4481）。
手工加的这一行**与重跑标定工具会写出的内容一致**，所以下次重标定不会产生差异。

**验证**（全部离线，219 项通过）：`check_reference` 的边界与绕圈判据
（跨 `0/360` 的 10° 报成 −350°，用最近圈就会放过去）；map 校验 `reference_deg` 的
长度、数值类型与 `0..360` 区间；解码器的判一次/预热不判/换原点重判/判过即锁定/
缺字段报告不拦；PTY 端到端跑真 `app.py`：起始帧正确 → `a` 进 ACTIVE，
起始帧偏 90° → `reason` 点名 J3、`state` 停在 STOPPED、**全部记录的 `joints_rad` 为 0**
（证明不是"停了"而是"一个目标都没发"），首帧之前按 `a` 被拒。

**这次改动同时暴露的一件事（未修，见 12.16）**：`unwrap_from_reference` 的输入列是
`pose["continuous_deg"]`，而单点路径用的是 `raw_deg`。对这份真机 session 而言
**两者不等**（J2：`continuous_deg` = −37.2，`raw_deg` = 322.8），也就是当初若用 `fit`
而不是单点，写出的 map 会在 J2 上整体偏 360°。

### 12.16 修掉 12.15 暴露的 `fit` 锚点错误（2026-10-03）

第 12.15 节末尾记下的那件事已修。**纯软件改动，全部离线验证**，没碰真机、没碰 SDK。

**错在哪。** `fit_session` 把 `pose["continuous_deg"]` 交给 `unwrap_from_reference`，
那是对**采集进程**而言的展开角：它的原点是采集 session 开始流数据的那一刻，不是姿态 1。
运行期不是这样——`Mapper` 以**它自己看到的第一帧原始角**为原点。两个原点差着整圈时，
拟合出来的 `offset_deg` 就整体偏 `360 * sign`，而**这一圈不会在拟合里露出来**：
整圈的差被 `offset_deg` 吸收，`slope`、`span`、`max_residual` 全部照常通过。等到遥操作
一 arm，机械臂就朝那个方向走 360°——这正是第 12.15 节里说的那类"没有任何检查看得见"的错。

**证明它是真的，而不是理论上的**：这份真机 session 的 J2，`continuous_deg` = −37.2、
`raw_deg` = 322.8，差正好一圈。J2 的 `sign` 是 −1，所以当初若用 `fit` 写 map，
**J2 的每个目标都会差整整 360°**（其余五个关节两者相等，不受影响）。

**改法**：`fit_session` 改喂 `pose["raw_deg"]`；`unwrap_from_reference` 的 docstring 补上
"喂进来的必须是 raw"这一条契约；`build_map` 里说明 `reference_deg` 取 raw 的那段注释
与之呼应。

**测试**：新增
`test_the_fit_is_anchored_on_raw_angles_not_the_session_origin`——夹具把 session 的
`continuous_deg` 整体挪一圈而 `raw_deg` 不动（模拟"采集前操作者把某个关节转过零点"），
断言写出的 map 经新 `Mapper` 从 `raw` 驱动，仍复现出记录的 `arm_deg`。
**已验证它在改回 `continuous_deg` 时会以 360.0 的差值失败**，不是个恒真断言。
另有两处既有夹具本来靠改 `continuous_deg` 来"让某关节不动"（J3 不动、J5 不动），
现在改的是 `raw_deg`——否则这两条测试会因为改错了列而**悄悄失去被测行为**。

**顺带把真机那份 map 补成工具会写出的样子**：仓库根目录的 `leader_map.json`
（gitignored）由 `build_map(single_point_map(...), HAND_ENTERED_EVIDENCE)` 用记录在案的
方向 `+ − − − + −` 重新生成，`diff` 确认**除新增 `reference_deg` 与那两行注释的措辞外，
sign 与 offset 逐位相同**。原来那两行注释正是第 12.15 节纠正过的"差一圈偏 360°"说法，
一并换掉。逐关节用 `sign * raw + offset` 复算，与同一姿态记录的 `arm_deg` 六维全部吻合到
小数点后 4 位。

### 12.17 拒绝信息改成"要转多少"，以及两个数为什么不是一个（2026-10-03）

用户读第 12.15 节那份报告时指出：**J2 那个"−308.6°"其实只差几十度**。这一点是对的，
而且暴露的是报告而不是判据的问题。

**两个量，都真，但不是一回事：**

| 量 | 定义 | 实测（真正那份 leader）| 用途 |
| --- | --- | --- | --- |
| 字面差 | `now - reference_deg` | J2 **−308.6°**、J5 **−268.4°** | **判据**：这就是 `Mapper` 会命令出去的误差 |
| 最短圈差 | `shortest_turn(reference, now)` | J2 **−51.4°**、J5 **−91.6°** | **只写给操作者**：手要转多少、往哪边 |

字面差就是命令误差，理由和 6.3/12.15 里同一条：mapper 第一帧令 `continuous = raw`，
于是 `target = sign * raw + offset`。实测 J2 现在 raw 14.2 → 目标 308.94°，
而基准姿态上应当是 0.34°，差的正是 308.6°。所以**判据不能改成最短圈**：
"基准 354°、现在 4°"物理只差 10°，最短圈会放行，而它会命令 −350°。

**改动**（`leader_map.py` / `leader_decoder.py`）：

- 新增 `leader_map.shortest_turn(reference_deg, raw_deg)`：纯函数，最短圈、带方向符号，
  docstring 明写它是给人看的、不参与判定。它和 `check_reference` 分开住，就是为了不让
  这两个量在调用点被混用。
- `startup_blocker` 逐关节列出**所有**超出容差的关节（原来只报最差的一个）：
  "J2 reads 14.2 deg and has to read 322.8 (turn it -51.4 deg); J5 reads 41.3 deg and has
  to read 309.7 (turn it -91.6 deg). Arming here would command J2 -308.6 deg away from
  where it belongs and J5 -268.4 deg away from where it belongs (tolerance 10 deg)."
  两个数各自标清是什么。为此解码器多存了一份**第一帧的原始角**（`reference_frame`），
  并随 `_restart_origin()` 一起清掉。
- 只报最差那一个是真的会坑人：实测那一刻 **J2 与 J5 同时不合格**，而判定锁死在第一帧上，
  按提示修好 J2 再重启、才会被告知 J5 也不合格。

**验证**（离线，226 项通过，比上一条多 6 项）：`shortest_turn` 的一般值、
跨 `0/360` 的两侧、零转角、以及"绝不超过半圈"的性质；解码器侧断言拒绝信息里
**同时**出现 −350.0（命令误差）、−10.0（要转的量）与 354.0（要读到的值），
以及 J1/J3 同时不合格时**两个都被点到**。判据本身的行为没动，
原来的"跨 `0/360` 的 10° 必须报 −350°"测试原样通过。

### 12.18 按 `a` 时用机械臂反馈定整圈，取代"必须从基准姿态启动"（2026-10-03）

**用户的原话**：「修改一下映射的逻辑：在按键确认进入遥操作状态时，将编码器反馈的每个关节
都先映射到与机械臂真实反馈的最短边，然后将最短边映射带来的圈数（2π 的整数倍）偏置记录
下来，直到退出遥操作模式之前都带着这个圈数偏置进行映射」，动机是「避免编码在初始位置
附近过 0 带来的不便」。

**为什么这是对的、也是唯一可能的做法。** 第 12.15/12.17 节那套"必须从基准姿态启动"
是在**绕**一个问题而不是解它：单圈绝对编码器在每个圈上读出的都是同一个数，所以
"这个 session 现在在哪一圈"在 leader 这一侧**原理上无解**——`14.2` 和 `374.2` 是同一个
读数。既然从 leader 判不出来，就只能要求操作者把起点摆在唯一一个已知的圈上（基准姿态），
再用字面差把它钉住。用户指出的是：这个绕法在**基准角靠近 0/360** 时特别难用——
这份 map 的 J2 基准是 322.8（离 360 只有 37.2°），操作者把 leader 摆回去时落在 14.2，
被判 `-308.6°` 并拒绝。而机械臂的实测关节角是循环里**唯一**知道圈数的东西。

**规则**（用户已确认的两个选择：整圈偏置、阈值 30°）：

| 量 | 定义 |
| --- | --- |
| `needed_i` | 机械臂实测姿态反解出的 leader 角：`(q_i_deg - offset_i) / sign_i` |
| `turns_i` | `360 * round((needed_i - continuous_i) / 360)`，按 `a` 时记录，直到退出 |
| `residual_i` | `(continuous_i + turns_i) - needed_i`，恒在 ±180° 内 |
| 映射 | 之后每帧 `target = sign * (continuous + turns) + offset` |
| 判据 | `|residual| <= 30°` 才 arm；否则按 `residual` 反号给出机械臂会走的距离 |

**一个含义上的变化，要在交付时讲清楚**：`needed` 来自机械臂**当前**姿态，所以判据其实
是「**leader 和机械臂必须摆成同一个姿态（30° 以内）**」，而不是"leader 必须摆在 map 记的
那个姿态"。操作指令随之从"让 J2 读到 322.8"变成"**用手把 leader 摆成机械臂的样子，
再按 `a`**"。这也让 `reference_deg` 降级成**出处记录**（offset 是在那个姿态上量的），
运行期不再读它。

**实测数字（真正那份 leader，用户当时的姿态）**：J2 残差 **51.4°**、J5 残差 **91.6°**
（整圈偏置只能把字面差 308.6°/268.4° 减到最短圈差，不能再小），**在 30° 之外，
仍然会被拒绝**。这次改动**不会**让那个姿态直接通过——它消除的是"在 0/360 另一侧几度"
这类误判、把拒绝信息里的数字从 308.6 变成 51.4，并把指令换成人能执行的"把两边摆成
同一姿态"。用户已知悉。

**改动**：

- `leader_map.py`：删 `check_reference()` 与 `REFERENCE_TOLERANCE_DEG`；新增
  `resolve_turns()`（纯函数，返回 `ok / turns_deg / residual_deg / worst_joint /
  worst_deg / tolerance_deg`，`continuous` 里有 `None` 时抛 `ValueError`）与
  `ANCHOR_TOLERANCE_DEG = 30.0`；`JointMap.from_arm_deg()` 放在正向映射旁边；
  `Mapper` 新增**独立的** `self.bias`（只被 `to_radians` 读，`continuous` 一个字节不改
  ——`leader_calibrate.py` 的 `SamplingDecoder` 读的就是它）与 `Mapper.anchor()` 只在
  `ok` 时写 `bias`；`reset()` 连 `bias` 一起清。`reference_deg` 字段、校验与
  `leader_map.example.json` 里的字段都保留，只是改成出处记录的说法。
- `leader_decoder.py`：删首帧判定（`reference` / `reference_pending` / `reference_frame`
  / `judge_reference` / `startup_blocker`）；新增 `anchor(arm_radians)`，反解 `needed`、
  调 `mapper.anchor()`、结果存 `anchor_verdict` 并**当场 `_publish(None)`**
  （不然读数是上一帧的，`anchor` 块会晚一拍）；telemetry 的 `"reference"` 块换成
  `"anchor"`，没锚过是 `null` 而不是 `{"checked": false}`。
- `control.py`：`Controller.pre_arm`，`_apply("arm")` 里读一次实测位置、过一遍 hook，
  被拒就 `stop("refusing to arm: ...")` 并 return（`state` 本来就是 STOPPED，`arm.stop()`
  幂等；FAULT 在更早的分支就 return 了）。顺带把原来"anchor 读一次、`_apply` 再读一次"
  的双采样合成一次。
- `app.py`：**删 `apply_operator_arm()`**（只剩转发），新增 `install_arm_check(controller,
  decoder)` = `controller.pre_arm = getattr(decoder, "anchor", None)`，在 hardware 与
  mock 两条路都装；按键处理直接 `controller.operator_arm()`。
- `leader_calibrate.py`：import 换名，三处**生成文案**改掉（`build_map()` 写进 map
  comment 的那段、`--out` 之后的 Next 提示、交互式写盘后的提示），标定行为不动。

**为什么门禁装在 `Controller` 而不是 `app.py`（一次对抗审查逼出来的，别改回去）**：
进 ACTIVE 有两条互不相交的路——串口帧的 `arm` 走 `handle` → `_apply("arm")`，
本地按键走 `operator_arm` → `_apply("arm")`。`provides_arm` 只是**声明**：
`check_decoder_for_hardware()` 只在 `provides_arm is False and not operator_keys` 时拒绝
（缺省 True），而且只在 `hardware and teleop` 下被调用（mock 路不设防）；任何
`--decoder` 自定义模块都能自己返回 `Command("arm", ...)`。所以"在 map 加一条 `anchor`
时断言 `provides_arm` 必须为 False"这种检查**拦不住声明 False 却照样发 arm 帧的解码器**。
`pre_arm` 是个普通 callable，`control.py` 仍然只 import `protocol`。

**测试**：新增 `tests/test_leader_map.py::ResolveTurnsTests` / `::AnchorTests`、
`tests/test_leader_decoder.py::AnchorTests`、`tests/test_control.py::PreArmTests`、
`tests/test_app.py::ArmCheckWiringTests`；`tests/test_leader_integration.py` 的
`ReferenceGateTests` / `OffReferenceTests` 换成 `MatchedPoseTests` / `MismatchedPoseTests` /
`RolloverTests`。

**一个会静默改语义的坑，值得单独记**：PTY 集成测试的 map 原来 `offset_deg` 全是 0、
mock 臂停在零位，而 `CAPTURED` 是 79.5/328.1/…——新判据下**每一个 arm 测试都会被拒**
（残差 79.5° 等）。夹具改成 `mapping_from(reference)`：`offset_deg = -sign * angle`，
让 leader 的 captured 姿态正好对应机械臂的零位。**这不是测试适配，是新规则的直接后果**：
判据从"和存储的姿态比"变成"和机械臂当前姿态比"，任何把两者分开的夹具都不再成立。

**验证**（离线，**255 项通过**）：
`.venv/bin/python -m unittest discover -s tests`；`git diff --check`；`bash -n scripts/*.sh`。
四处关键行为各做了一次**变异检验**（改坏后确认测试真的红；2026-10-03 交付前逐条重跑）：

| 改坏的地方 | 结果 |
| --- | --- |
| `to_radians` 里去掉 `+ bias` | 3 项失败：`RolloverTests`（PTY）与两份 `AnchorTests::test_the_bias_carries_the_stream_past_the_rollover` |
| 删掉 `_apply` 里的 `pre_arm` 分支 | `PreArmTests` + 两个 PTY 组共 11 项失败 |
| 把夹具 map 换回全零 offset（旧夹具） | `MatchedPoseTests` 失败 |
| 删掉 `anchor()` 里 `continuous` 为 `None` 的前置判断 | 2 失败 3 错误——没帧时按 `a` 变成抛异常 |

另有一条测试把 `residual_deg` 与 `-shortest_turn(needed, now)` **模一圈钉成同一个数**，
防止两个函数各算一遍之后漂移（半圈处允许差整整一圈，那里两个都是 ±180）。

**真机**：本轮未接硬件。真 arm 前的操作步骤已按新语义改写在 README「按 `a` 时的整圈锚定」
与第 9 节第 6 条。

### 12.19 状态行按定时器打，但状态/理由一变就当场打（2026-10-03）

操作者实机反馈：**「日志跳动太快，什么都看不清，也不知道按 a 后有没有响应」**。
两个问题，第一个是默认值，第二个是设计。

**默认太快**：`--print-rate` 缺省 10 行/秒，一行是一整条 JSON（含整个 `leader` 块，
里面有最近一帧的七个字段），屏幕上就是一面墙。已经在 README「按键控制」里写明
调低它（`--print-rate 1` 甚至 `0.2`）以及"关键信息不会因为调低而漏掉"，并给了一段
只打状态/理由变化的过滤器脚本（过滤 stdout 不影响 stdin 上的按键）。

**"不知道按 a 有没有响应"是个真 bug，不是观感问题。** 原判断是

```python
if now >= next_print or controller.state != previous_state:
```

而**拒绝时 `state` 根本不变**（还是 `STOPPED`），变的只有 `reason`。于是把
`--print-rate` 调低到能看的程度之后，按 `a` 被拒的答复要**等满一个打印间隔**才出来
——2 秒的间隔就是 2 秒的沉默，恰好是操作者正盯着屏幕等回话的那一刻。改成把
`(state, reason)` 一起记：

```python
def due_for_print(now, next_print, seen, state, reason):
    return now >= next_print or (state, reason) != seen
```

抽成纯函数是为了能直接单测（控制循环本身没法单测）。`reason` 在 ACTIVE 跟踪期间
是常量（"armed at measured position"），只在 `stop()` / `_apply` 里改，所以不会退化成
每轮都打。`grep` 一遍 `control.py` 确认 `self.reason` 的赋值点只有这两处。

**验证**（离线，当时 **261 项通过**；后续章节又加了测试）：
- `tests/test_app.py::PrintThrottleTests`：未到间隔不打、到点打、`state` 变立刻打、
  **`state` 不变而 `reason` 变也立刻打**、同一条不重复打。
- `tests/test_leader_integration.py::PrintRateTests`：PTY 里 `--print-rate 1` 跑约 2 s
  （`frames ≥ 60`），断言落下的记录数 `< 6`——控制循环是 100 Hz，这一条同时证明
  `--print-rate` 真的接到了循环上（此前**完全没测**）。harness 的 `--print-rate` 从写死的
  `"100"` 提成类属性 `PRINT_RATE`。
- 两次变异检验：把 `due_for_print` 退回只比 `state` → `PrintThrottleTests` 里那条失败；
  把 `next_print` 改成每轮都到期 → `PrintRateTests` 那条约 60 条记录、失败。
- 套件总时长从 8.2 s 涨到 10.3 s（那条 PTY 测试要真等约 2 s）。

**离线复算**（用真实那份 `leader_map.json`，不改硬件）：操作者当时那个姿态的锚定结果是
J2 `turns +360°`、残差 **+51.4°**（机械臂会走 −51.4°，J2 的 `sign` 是 −1），
J5 `turns +360°`、残差 **+91.6°**（会走 +91.6°），最差关节 J5，`ok = false`
——即 30° 之下**仍然会被拒**，与 README 里的拒绝样例逐字一致。

### 12.20 给人看的输出：`--watch` 行、拒绝信息里的读数、厂商横幅（2026-10-03）

操作者实机跑了一晚，回来三件事挤在一起：(1) 屏幕上混着厂商 SDK 打的"ARX方舟无限"，
(2) 默认的 JSON 记录在真机上是一面墙（第 12.19 节），(3) 他贴回来的拒绝信息里
**J2 写的是 "reads -72.1"、"reads 438.8"**——而板子上此刻显示的数是 **287.9 / 78.8**。
第三条是真 bug，不是观感。

**（1）厂商横幅。** 厂商库从 C++ 直接写 fd 1，构造和析构各打一次
（用户贴回来的样本正好前后各一行）。`VendorChatter` 本已在标定工具里做了 fd 层重定向，
这次把它**从 `leader_calibrate.py` 挪到 `backends.py`**（两边都要用，两边又都 import
厂商后端，放在 `app.py` 会成循环）。`run()` 用 `ExitStack` 进去、拿到 `dup` 出来的
`stream`，程序自己的一切输出都写 `stream`；`stack.close()` 排在 `arm.close()` **之后**，
SDK 的临别话也进日志。`app.py` 新增 `--arm-log`（默认 `teleop_arm.log`）。
`tests/test_leader_calibrate.py::VendorChatterTests` 原样覆盖这个类，行为一字未改。

**（2）`--watch`。** 新增 `--watch`（`watch_line()`），把每轮那条 JSON 换成一行：

```
01:28:38 STOPPED | J1   +0.0  J2  +35.1  J3   +0.0  J4   +0.0  J5 -129.1  J6   +0.0  | out of pose: J2 J5 (tolerance 30 deg)
01:28:50 ACTIVE  | armed at measured position
```

数字来自新的 `LeaderUartDecoder.distance(arm_radians)`（只读，见第 6.1 节），**与门禁同一个
`shortest_turn`**，所以这一行说 "in the arm's pose, press a" 的瞬间按 `a` 就是能成的
（第 12.19 节的 `due_for_print` 保证答案当场打出来，不用等打印间隔）。
没有 `distance()` 的解码器（`JsonLineDecoder`）退回只打状态，不报错。
上面那段样例是**真跑出来的**（PTY + mock 臂 + 真 `app.py`），下面那条 out-of-pose 用的是
操作者实测的那组数（把 mock 臂的零位对到 J2 323.0 / J5 309.7，让板子读 287.9 / 78.8）。

**（3）拒绝信息里的读数。** `self.mapper.continuous` 是从**流开始那一刻**展开的，
操作者把某个关节转过 0/360 之后它就是 `-72.1` 或 `438.8`；而 `needed` 是模一圈算的。
两个不同基准的数并排写在同一句话里，读的人（正确）认为自己在读板子上的数——于是信息
指着一个板上根本没有的数让人去对。修法：两边都 `% 360.0` 再打印：

```python
now = self.mapper.continuous[index] % 360.0
needed = needed_deg[index] % 360.0
```

判决本身不受影响（残差是**距离**，与展开原点无关），改的只是给人看的字。
`tests/test_leader_decoder.py::AnchorTests` 里加了一条用操作者**原样那组数**
（J2 读 287.9、要 323.0；J5 读 78.8、要 309.7）断言信息里出现的是这两个数而不是
`-72.1/438.8`——**把 `% 360.0` 去掉这条即以这些数失败**。

**（4）顺带纠正一处文档错误。** 上一轮写下的"拒绝信息里两个数等大反号"是**错的**：
`turn it` = `shortest_turn(needed, now)` = `−residual`，"会走" = `sign · residual`，
两者**大小恒等**，符号在 `sign = −1` 时相同、`sign = +1` 时相反。真实那份 map 的方向是
`+ − − − + −`，所以 J2（sign −1）两个数都是 −51.4，J5（sign +1）是 −91.6 / +91.6。
README 与 HANDOFF 里的三处措辞按此改写。

**验证**（离线，**277 项通过**，含真 pyserial + PTY）：
- `tests/test_app.py::WatchLineTests`（6）、`PrintThrottleTests`（5）；
- `tests/test_leader_decoder.py::AnchorTests` 里的 `distance()` 只读性、
  走到姿态里归零、没帧返回 `None`、拒绝信息引用的是板上的数；
- `tests/test_leader_integration.py::WatchModeTests`（5，`--watch` 跑真 `app.py`）
  与 `PrintRateTests`（`--print-rate 1` 下记录数仍是个位数）。
- 变异检验：去掉 `% 360.0` → 读数测试失败；把 `distance()` 改成写 `bias` →
  "只在 `anchor()` 选圈"那条失败；`--watch` 打成 JSON → `WatchModeTests` 失败。
- **PTY 测试的坑（踩过一次，记下来）**：往 pty master 写数据时若 app 还没 open slave，
  这些字节会**丢掉**（写 master 得到 EIO）。harness 的 `wait_for(..., stream=...)` 每轮
  重发一帧正是为此；手写的临时脚本只发一次，就会看到 "waiting for the leader's first
  frame" 永远不消失——**那是脚本的问题，不是产品的**。

### 12.21 第一次真机遥操作：整条链通了，然后撞上限位（2026-10-03）

操作者用第 12.20 节的命令（`--watch --print-rate 1` + 真 `leader_map.json`）跑了第一次真机遥操作。
**这是整圈锚定、整圈偏置、门禁、映射在真实机械臂上的第一次端到端验证**：

```
01:32:04 STOPPED | J1  -10.3  J2  +17.1  J3   +6.0  J4   -6.1  J5  -25.4  J6  -20.5  | in the arm's pose, press a
01:32:04 ACTIVE  | armed at measured position
01:32:05 ACTIVE  | armed at measured position
01:32:07 FAULT   | invalid serial input: joint position outside configured limits
```

门禁在最差 25.4° 处放行（≤ 30°），arm 成功，机械臂跟着 leader 走——`a` 之前那行
"in the arm's pose, press a" 与实际能 arm 逐字对上，`due_for_print` 也证明了答案当场出现。
**这一段是实测证据，此前只有 PTY。**

**然后两三秒就 FAULT。** 诊断：

- 理由前缀 `invalid serial input` 说明它来自 `app.py` 那句 `except ProtocolError`
  ——即**解码后的 target** 越界，不是 arm 那一刻（arm 走的是按键路，在 `try` 之外，
  若在 arm 时越界会变成 `main()` 的 `ERROR: ...` + 退出 2，不是 FAULT）。
- 时间也对得上：arm 之后 `self.target = measured`，**下一帧**才换成解码值，
  若 arm 时就越界会在 10 ms 内 FAULT；日志里 ACTIVE 连续三秒（`--print-rate 1` 三拍），
  所以 arm 时的 target 是合法的，是**操作者随后移动 leader**把某个关节推过了配置范围。
- 根因不是映射，是 **`limits.json` 没标定**：它是 `limits.example.json` 的逐字拷贝
  （第 9.1 节缺口 1 早就写着"不校准很可能直接撞 `Limits.check`"——应验了）。
  可疑项是 J2/J3 的下界**正好是 0.0**（这版限制里 J2、J3 不许为负），以及 J5/J6 只有
  ±90°/±120°：arm 后走的量也不小（约 J5 +25.4°、J6 +20.5°），把本来就贴着界的关节推了出去。

**这次改的不是门禁，是那句话。** 当时的理由字符串是 `joint position outside configured limits`
——六关节的机械臂上，这句话不告诉操作者任何能动手的信息。现在 `Limits.outside()`
逐关节给出 `J5 +1.610 not in [+1.570, +1.570]`，串口 target 与机械臂实测两条路都点出关节。

**顺带补一个洞**：`tick()` 里的 `self.limits.check(feedback)` 在 `app.py` 的解码器
`try` **之外**，所以"机械臂自身实测越界"会抛 `ProtocolError` 穿出 `run()`，被 `main()`
当 `ValueError` 接住 → 打一行 ERROR、退出 2。状态机被绕过，操作者看不到 FAULT，
也没法按 `s`。现已改成和 `joint following error` 同类的
`stop("the arm is outside the configured limits: ...", fault=True)`。
（触发路径真实存在：target 在限位内时，机械臂因 `max_following_error=0.15 rad`
的容差轻微过冲就可能把自己读到界外。）

**安全提醒（已写进 README）**：FAULT → `arm.stop()` → SOFT（零力矩），机械臂会因重力下坠。
日志里 01:32:14 那组大数（J2 −50.6、J6 +46.5）多半就是下坠后 `distance()` 换了个机械臂姿态
算出来的，不是 leader 乱跳。**限位没校准之前，遥操作时手不要离开机械臂。**

**还没做（已知缺口，留待判断）**：arm 那一刻没有检查"按这个残差走过去会不会出界"。
门禁只看姿态失配（≤ 30°），看不到 `--limits`，所以操作者在一个贴着界的姿态上 arm 时，
第一批 target 可以直接越界。**这次不是它**——arm 时的 target 是合法的（否则不会等两三秒）。
要不要补这个检查，取决于限位校准之后还会不会经常贴界：如果是，就该让 arm 前的检查
一并看见 `--limits`，像现在这样先拒绝、别等撞了再 FAULT（FAULT 会走 SOFT，机械臂下坠）。
**这个判断已作出，见第 12.22 节**：不补 arm 前的出界预判，改成越界 target 限幅——
连"撞了再 FAULT"本身也不要了。

### 12.21 附：重标定把上一条缺口坐实了（2026-10-03）

操作者重跑了一次 `session`（单点 + 手输方向，1 个姿态）。两件事：

**（1）新的 map 是对的，旧的不是。** 用采到的那个姿态回代：
`leader_map.hand.json` 的 J5 偏了 **84.6°**（其余关节 1~5°），新的 `leader_map.json`
六个关节全 0.0°。J5 的 offset 从 −309.71 变成 **−394.35**（差 84.64°）——
手输那份的 J5 整圈算错了。这正是当初"手输方向未经复核"的风险兑现，也说明重标定值得。
方向仍然是 `+ − − − + −`，与手输一致。

**（2）`limits.json` 与这台机械臂不合，现在有实测数字。** 标定姿态下六关节实测对比配置范围：

| | 实测 | 配置范围 | 余量 |
| --- | --- | --- | --- |
| J1 | +2.63° | [−179.9, +179.9]° | 177° |
| J2 | **+0.27°** | [+0.00, +209.1]° | **0.27°** |
| J3 | **+0.45°** | [+0.00, +179.9]° | **0.45°** |
| J4 | +5.56° | [−89.95, +89.95]° | 84° |
| J5 | **−90.15°** | [−89.95, +89.95]° | **已越界 0.19°** |
| J6 | +3.25° | [−119.8, +119.8]° | 116° |

第 12.21 节那次 FAULT 至此有了确定解释：机械臂静止时就坐在 J2/J3/J5 三个界的边缘上
（J5 甚至在界外），leader 一动就出界。**这不是映射或锚定的问题，是 `limits.json` 没在
这台机械臂上量过**（第 9.1 节缺口 1）。

**（3）由此补的一个洞**：arm 那一刻的 `limits.check(measured)` 原本会**抛**。
按键路不在解码器 `try` 里，抛出去会穿到 `main()` → 打 ERROR、退出 2。也就是说
**机械臂恰好停在界外时按 `a` 会杀掉进程**——而上面这张表说明这台机械臂现在就是这个状态。
改成 `refusing to arm: the arm is outside the configured limits: J5 −1.573 not in [...]`，
与别的"摆位不对"拒绝一致：停在 STOPPED、不锁存、改好再按。

### 12.22 越界的输入限幅，而不是终局（2026-10-03）

**决定（操作者）：** "当控制输入量越界时不要直接终止控制，而是将发给机械臂的位置指令进行限幅。"
这条取代第 12.21 节的 FAULT 设计——撞上限位不再是会话的终点。

**为什么停机比顶界更糟。** 越界有两条来源，在这里分不出来：手把 leader 推过了一度，和
target 真的算到了界外（限位没校准、映射错）。停机意味着 `arm.stop()` → SOFT（零力矩）
→ 机械臂因重力下坠；而顶在限位上只是不跟手。选后果轻的那个，把"越界了"变成操作者能看见
并撤回的信息，而不是替他做决定。限幅还有个性质：**只有指令被夹，映射不动**，
所以把 leader 拉回范围内立刻从原位续上，不丢位置、不用重按 `a`。

**改动：**

- `Limits.check()` → `Limits.clamp(joints)`，返回 `(clamped, saturated)`：
  逐分量 `min(max(q, lo), hi)`，`saturated` 是被夹过的关节下标。
- `Controller.saturated`：`__init__` 置空、`stop()` 清空、arm 成功时清空、每帧 target
  重新赋值。这是"当前哪个关节顶在界上"的唯一来源。
- `tick()` **删掉** `self.limits.outside(feedback)` 那条绝对检查。理由是指令不可能自己出界
  （arm 时实测已在范围内、target 被夹、限速在两个界内点之间插值——逐关节凸性），
  而机械臂本身会**合理地**短暂越过边界：限幅把指令停在界上，伺服到位的机械臂就滞留在界外
  一个 `max_following_error` 以内。绝对检查会对"机械臂执行刚收到的限幅指令"报 FAULT，
  正好是这次要消掉的行为。超过这个滞后的部分是跟踪失败，由 `joint following error` 兜住。
- `app.watch_line()`：ACTIVE 行尾部补 `| at the limit: J3 J5`。顶界时机械臂不再跟手，
  没有这一句，读起来和"机械臂在慢慢跟"一模一样。
- arm 那一刻的实测越界检查**保留**（第 12.21 节附）：那时 `commanded = target = measured`，
  没有"夹一下"可夹——夹了就是使能瞬间跳一下。实测在界外仍然 `refusing to arm`，点名关节。

**明确写下的代价（安全边界变小了）**：以前"target 越界"是一条硬闸，现在没有这条硬闸了。
留下的三条：arm 时实测必须在配置范围内；指令只能停在界上、不会自己往外走；
`joint following error`（0.15 rad）限制机械臂的实际位置——也就是**机械臂最多越过配置边界
一个 `max_following_error`**。丢掉的是"程序替你判断限位数值对不对"：限位如果设得比实物
允许的更宽，限幅一样挡不住机械臂撞上真实障碍。所以 README 里那句 limit 是安全边界的话保留。

**验证**（离线，**285 项通过**，比第 12.21 节多 5 项，见第 8 节）：

- `test_control.py` 新增 `test_an_out_of_range_target_is_clamped_named_not_fatal`（越界不发
  异常、不换状态，`target` 被夹、`saturated == [1]`，再发一帧范围内的 target 即清空）、
  `test_the_arm_lagging_past_a_bound_is_not_a_fault_of_its_own`（J6 滞留在 1.05 而界是 1.0，
  在 0.15 容差内 → 仍 ACTIVE，且指令停在 1.0 不追出去；**把绝对越界检查加回去这条即失败**）、
  `test_stopping_clears_the_saturated_joints`；原来的"机械臂实测越界走 `stop(fault=True)`"
  一条改成"离指令 2.0 rad 由 `joint following error` 兜住"——原来的理由字符串已经不存在了。
- `test_app.py` 新增 `test_while_armed_it_says_which_joints_are_held_at_a_bound`；
  `WatchLineTests` 的假 controller 现在显式给 `saturated`（`Mock` 自动生成的属性是真的、
  不可迭代，`list()` 会抛）。
- PTY 端到端新增两条（`test_leader_integration.py`，真 `app.py` + mock 臂 + 真解码器）：
  把 J1 的上界压到 +0.05 rad 而让 leader 要多 4.0°，`ClampedTargetTests` 看到
  `state` 仍是 ACTIVE、`joints_rad[0]` 停在 0.05 不越界，而解码器自己的
  `target_rad[0]` 是 0.0698——指令被夹、映射没被夹；`ClampedWatchLineTests` 用 `--watch`
  看到那一行补出 `at the limit: J1`。
  **变异验证**：把 `clamp` 改成原样返回（不夹），这两个类加 `ControlTests` 共 5 条失败
  （`[5]` 变成 `[]`、`joints_rad[0]` 越过 0.05）；改回来即全绿。

### 12.23 发给关节的指令改成跟踪微分器的轨迹（2026-10-03）

**需求（操作者，原话）：** "参考 `ref/adrc.*`，使用其中的独立 td 跟踪微分器，对发给每个关节的
角度进行处理，其中 r 参数（单位：角度）使用：400, 500, 600, 4000, 1000, 4000"；追加一句
"注意要使用多圈角度"。

**转写了什么、没转写什么。** 只取 `ref/adrc.c` 里与闭环无关的那一件：
`TDFunction_independent()` 和它调用的 `fst()`（`adrc.c:81`，逐项照抄，含 `fsg` 的区域切换），
放进新文件 `td.py`。同一个文件里的 `NLSEFFunction()`/`ESOFunction()`/`ADRCFunction()` **不用**：
那是给"自己算力矩去驱动电机"的闭环用的（还要接陀螺/编码器做状态观测），而这里发给机械臂的
是**位置指令**，闭环在厂商的位置模式里，外面再套一个 ESO 只会与厂商的伺服打架。

**两个照做的前提，都是操作者指定的：**

- **单位是度**。`r` 在参考实现里就是加速度上限，量纲 = 输入单位/秒²；输入用度，`r` 就是 deg/s²。
  `Limits` 其余部分全是弧度，所以换算只发生在 `tick()` 里那一处交接（`math.degrees` /
  `math.radians` 各一次），其余代码不动。
- **多圈角**。`Mapper.to_radians()` 输出的是解缠后的连续角（`leader_map.py:258`），可能超过 360°
  或为负；`math.degrees()` 原样保留圈数。**绝不折回 0..360**：折回去的话，关节每次经过
  `0/360`，微分器看到的误差都会突然变成整整一圈，轨迹会朝反方向甩一圈去追一个没发生过的动作。
  `test_td.py::test_a_multi_turn_angle_is_not_wrapped`（350→370 单调穿过 360）与
  `test_control.py::test_a_multi_turn_target_is_not_wrapped`（`Limits((-10,)*6,(10,)*6)` 下
  350°→370° 不回摆）钉住这一条；把误差按 ±180 折一下的变异体只被这一条抓到。

**`max_speed` 保留为速度上限（这是一个选择，写在这里）。** 微分器限制的是加速度，对速度没有上限：
对阶跃 Δ，峰值速度约 `sqrt(r*Δ)`。J4/J6 的 r=4000 在 30° 的阶跃上就要 ~338 deg/s ≈ 5.9 rad/s，
而 `max_following_error`（0.6 rad）是拿指令与实测比的——真按这个速度发，机械臂跟不上就是
`joint following error` → FAULT → `arm.stop()` → SOFT（零力矩）→ 下坠。所以轨迹的速度仍由
`max_speed` 夹住（`0.2` 默认 / 现场配置 `2.0` rad/s = 114.6 deg/s）。**代价要说明白**：
速度上限一旦顶住，`r` 只决定起步/刹车的形状，跟手快慢还是 `max_speed` 说了算——
想让 `r` 成为唯一限制就得把 `max_speed` 调大，那也就等于把上面那条保护调松。

**参数与状态：**

- `h` = 本拍实测的 `dt`（`tick()` 里已有），`h0` = 2h，照 `adrc.h` 的调参说明取两倍。
- 状态 `(角度, 角速度)` 就是**发出去的那条指令本身**（`step()` 返回什么就写什么），
  所以状态不会与控制流分叉，跟随误差检查比的还是同一条轨迹。
- arm 时 `reset(实测位置)`、零速度：否则第一拍就是一次没人要求的跳变。
  `stop()` 之后不需要重置——下一次 arm 一律重置。

**实测（离线仿真，100 Hz）：**

- 阶跃 30°、r=400：峰值速度 102.8 deg/s（0.25 s 处），±0.05° 内收敛 0.62 s，**全程不越过目标**。
  旧线性限速是 0.26 s 到达——新的更慢但两头是平滑的，这正是加速度上限换来的东西。
- 斜坡跟踪（leader 匀速 100 deg/s，即 1.75 rad/s）的稳态滞后：r=400 为 14.5°，
  r=4000 为 3.2°；速度跟得上（稳态速度误差为 0）。这就是逐关节 r 的用途——
  基座关节滞后大一点、更平滑，腕关节跟得更紧。
- 现场 `max_speed=2.0` 时上限开始顶住的阶跃：r=400 约 33° 以上，r=4000 约 3.3° 以上。

**改动的文件：** `td.py`（新）、`control.py`（`Limits.td_r_deg` + `Controller.tracker` +
`tick()` 里的交接）、`limits.example.json` 与现场 `limits.json`（补上 `td_r_deg`）、
`tests/test_td.py`（新）、`tests/test_control.py`、`tests/test_leader_integration.py`
（`WIDE_LIMITS` 显式写出 `td_r_deg`，让整份配置真的走一遍 JSON）、README 第「串口正常控制」节。

**验证**（离线，**304 项通过**，比第 12.22 节多 19 项，见第 8 节）。变异验证：
把轨迹改成直通（`step` 直接返回 target）失败 5 条；把每个关节的 r 固定成 4000 失败 4 条；
把误差折回 ±180 失败 1 条（就是上面那条多圈测试）。`test_slew_limit_and_deadman` 原来钉的是
"一拍走 `max_speed*dt`"，那条是旧限速器的行为，已改成钉轨迹（第一拍只走千分之几弧度、
第二拍位移大于第一拍）。

**遗留 / 操作者要知道的：** `ref/` 是未跟踪目录（文件头版权归哈工大（深圳）南工骁鹰机器人队，
且依赖该工程自己的 `common.h`），**不提交**，只作为本次转写的出处；`td.py` 是转写而非引用。§12.22 里"限速在两个界内点之间插值（逐关节凸性）"这句话在新实现下由"轨迹不越过目标"
承接（性质由 `test_a_step_is_approached_without_passing_it` 钉住），结论不变，措辞已过时。
`limits.json` 的 `lower`/`upper` 仍未标定，与本次改动无关。

### 12.24 SDK 里的关节增益改不了（2026-10-03，只反汇编，未动任何文件）

**问题（操作者，依次三问）：** "arx 的 sdk 支持控制速度吗" → "我可以调整电机的参数吗" →
"准确地说是 pid 的参数" → "能不能修改 sdk 中的 pid 参数"。答案为**否**，且是查证过的否。
本节把证据留在这里，省掉下一次反汇编。全程只读：`.so`、头文件、DWARF 都没改。

**速度控制：没有。** 三条证据：`InterfacesPy.hpp:20` 的 `set_joint_velocities()` 声明处自己写着
`// useless` 且无参数；它没进 pybind（`single_arm_interface.cpp` 的完整导出列表里没有）；
`nm -DC` 的符号表里根本没有这个符号。头文件里"声明了但没实现"的方法不止这一个（例如
`gravity_compensation()`，见 §5），**所以头文件不是规格，只能当线索**。

**增益（PID）：接口没有，源码没有，配置也没有。**

- 接口层：全部 pybind 导出是 `set_joint_positions` / `set_ee_pose` / `set_arm_status` /
  `set_catch` / `get_joint_*` / `get_catch_status` / `arx_x`。没有任何接受 kp/kd/增益的函数。
- 数据层：底层 CAN 命令帧**确实**带 `k_p`/`k_d`（MIT 式），`HybridJointCmd{position, velocity,
  torque, k_p, k_d}` 由 DWARF 确认（`byte_size` 40，`decl_file` = `HybridJointTypeDef.hpp`，
  偏移 0/8/16/24/32）。但 `ControllerBase::statePositionControl()`（0x132c0）填帧时
  `k_p ← 0x4f8(%rbp)` 解引用、`k_d ← 0x510(%rbp)`、`torque ← 0x4b8(%rbp)`——都是控制器成员，
  不是调用参数，没有外部注入路径。
- 名字层：整份 DWARF（1.3 MB，`readelf --debug-dump=info`）里 `k_p`/`k_d` **只**出现在
  `HybridJointCmd`。没有任何 gain/PID 结构体、配置项或同义成员名。
- 源码层：仓库里厂商只给了 `bimanual/src/single_arm_interface.cpp`（pybind 壳）与
  `kinematic_solver.cpp`。`bimanual/CMakeLists.txt:22` 对控制器是
  `target_link_libraries(${PROJECT_NAME} PUBLIC .../lib/arx_x5_src/libarx_x5_src.so ...)`——
  `ControllerBase`/`MotorType2`/`MotorType4`/`SocketCan` 全部只有预编译 `.so`，**没有源码可改**。
- 配置层：该 `.so` 的 strings 里搜不到任何 `.json/.yaml/.ini/.cfg`，符号表里也没有
  `ifstream`/`fopen`/`loadConfig`/yaml 之类。**它不读配置文件**，所以"改参数文件"也不成立。

**已定位到的常量（供参考，但认不出哪一组是增益）。** `ControllerBase::ControllerBase`
（0x158d0）用 `movdqa` 把 rodata 常量拷进对象，在 `.rodata` 里解出来是：

| 地址 | 值 | 形状 |
| --- | --- | --- |
| 0x32160 | 0.53, 0.53, 0.53, 1.74533, 1.48353, 1.48353 | 6 个（≈30°,30°,30°,100°,85°,85°） |
| 0x321a0 | 上面对应的负值 | 6 个，负向 |
| 0x321e0–0x32210 | **13.0 × 7** | 7 个（6 关节 + 夹爪？） |

`Init()` / `statePositionControl()` 还读到一批标量：0.08、0.1、0.2、0.5、1、2、8、13、200、
1000、5000、1.74533、-2.618（地址 0x325a0–0x32830）。**那 7 个 13.0 是 kp 的候选，但同样
可能是电流/力矩上限**——没有符号名，从外部无法证明。猜错一个常量就是在实机上改一段没人
验证过的硬件行为，所以本节到此为止，不给"大概是哪个"的结论。

**剩下两条技术路线，都不建议：** ①给 `.so` 打二进制补丁（改常量字节）——违反 §5 开头
"快照不变"的约定，改完版本不可追溯，重装/升级即失效，无法回滚；②运行时内存改写
（ctypes 定位控制器对象改数组）——不改文件但更脆，每次启动重做，且依赖偏移认对。

**正路**：向 ARX 索取带增益接口的 SDK/固件，或用厂商自己的上位机改驱动器侧参数——那个工具
不在这份快照里，**本仓库无法评价它能改什么**，不能替它下结论。

**唯一外部可见的厂商数值是 `arx_x(a, b, c)`。** 厂商自己的 `bimanual/script/single_arm.py:95`
在 `__init__` 里调 `arx_x(500, 2000, 10)`；`InterfacesPy::arx_x`（0x19dd0）把三个 double 存进
对象 0x178/0x180 等偏移，而 `statePositionControl()` 又把 `0x178(%rbp)`/`0x180(%rbp)` 读出来
交给 `arx::solve::Interpolation(double*, double*, double*, double, double, double)`（0x29a30）。
即：**这三个数调的是厂商自己那层轨迹插值，不是 kp/kd。** 想要"更跟手"能调的是这里，
加上我们自己的 `td_r_deg` / `max_speed`（§12.23），而不是驱动器增益。

**安全（照 §5 的边界说）：** 这套系统没有外部急停。任何改驱动器参数的动作都是硬件行为变更，
必须在机械臂已被支撑、且手能立刻断电的前提下做；SOFT 是零力矩，不是失能。
