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
| `control.py` | STOPPED / ACTIVE / FAULT 状态机、范围检查、限速、超时、跟随误差 |
| `backends.py` | `MockArm` 与 `VendorArm`；真实 SDK 状态映射、构造/模式切换 |
| `limits.example.json` | 六个关节的示例边界及限速参数；不是已核验实机配置 |
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
| `.venv/bin/python -m unittest discover -s tests -v` | 261 项通过，含真实 pyserial + PTY |
| leader 解码器离线测试 | 拆行、握手、`-1` 预热/故障、越界、缠绕展开、映射、`reset()` 语义 |
| leader 端到端（PTY，全 mock） | 字节 → 解码 → 映射 → 状态机 → 按键 arm/stop/FAULT 恢复 |
| 本地按键通道测试 | cbreak 的 termios 恢复、非 tty 回退、单批多键、fd 生命周期 |
| 标定工具测试 | 恒等/反向/带偏移、噪声、跨度不足、机械臂未动、非 1:1 斜率、姿态不互洽、跨绕圈点、拒绝写文件、生成的映射能被加载器读回并经 `Mapper` 复现采样到的臂角 |
| 交互式标定测试 | 注入伪 source/arm/keys/clock：滚动窗口只含当前姿态、撤销、未动够的关节被点名、`f` 失败留在循环里、整圈跑完写出可加载的 map、提前 `q` 以退出码 2 结束且留下的姿态能被 `fit` 直接使用 |
| 单点 + 手输方向（离线） | 六个 `+`/`-` 写出可加载的 map 并被 `Mapper` 复现出采样到的臂角；offset 不折 ±180；backspace 退格；`x` 不写文件；没有姿态/没有 `--arm` 时给出原因；复核通过才写、**位移与符号相反时点名拒绝**、**一个关节都复核不到也拒绝写**、没动的关节报为未复核（`DirectionTests` 用纯函数直接验这四种判定） |
| `session` 端到端（PTY 终端 + PTY 串口，无 SDK） | 真按键 → 真串口 → 采集 1 个姿态、退出码 2、arm.log 为空（未加载厂商库） |
| `VendorChatter` fd 重定向 | fd 1/2 都进日志、退出后两个 fd 都回到原目标（分别 dup，不共用副本） |
| 重力补偿接线（离线，无硬件） | `set_arm_status(3)` 恰好一次、跟踪目标时拒绝切模式、`close()` 后最后一条是 SOFT；`--arm` 的构造→进 3→读→`close()` 顺序；`confirm_release` 确认才 `stop()`、stdin 关闭也回 SOFT；**中断路径不进确认提示但 `close()` 仍执行** |
| SIGTERM 处理 | 真给自己发 SIGTERM：变成 `KeyboardInterrupt`（若未安装处理器，测试进程会被直接杀掉，不会静默通过）；处理前后 `SIGTERM` 处理器被恢复 |
| 重力补偿真机 | **操作者反馈"基本能用"**（2026-10-03，未量化）：跑完过一次 `session --arm`（1 个 301 帧、0 坏帧的姿态，见第 12.14 节），据此认为状态 3 能托住机械臂，标定流程不需要再等它 |
| 真机标定产物 | 已生成 `leader_map.json`（方向 `+ − − − + −`，手输，**未经第二姿态复核**），见第 12.14 节 |
| 整圈锚定与 arm 门禁（离线） | `resolve_turns` 的整圈性质（`turns` 是 360 的整数倍、残差恒在 ±180° 内、残差 ≡ −`shortest_turn` 模一圈，两函数钉在一起防漂移）、30° 边界两侧、跨 `0/360` 的 10° 必须放行（旧判据报 −350°）；`Mapper.anchor` 只在 `ok` 时写 `bias`、`reset()` 连 `bias` 一起清、`bias` 只进 `to_radians` 不污染 `continuous`（标定工具读它）；拒绝信息给"要转多少"与"会走多少"（大小相等，`-residual` 对 `sign * residual`）并列出**所有**不合格关节；解码器 `anchor()` 在首帧离 `reference_deg` 好几百时仍放行、没帧时**返回理由而不是抛**、握手/`reset()`/`ProtocolError` 后清偏置需重新 anchor、没 anchor 过时 `leader.anchor` 是 `null`；`Controller.pre_arm` 的**两条 arm 路都过**（串口帧与本地按键各一条测试）、被拒时 `arm.writes` 为空且 `arm.start` 未被调用、FAULT 下不触发 hook；map 校验 `reference_deg` 的长度/数值/`0..360` 区间（字段保留但不再是门禁）；PTY 端到端：左右同姿态→`a` 进 ACTIVE、偏 90°→`reason` 点名 J3 且 `joints_rad` 全程为 0（机械臂一个目标都没收到）、移回去重按即进 ACTIVE、首帧之前按 `a` 被拒、跨 `0/360` 的 10° 装上 360° 偏置并继续同向跟随 |
| 状态行打印节流（离线） | `due_for_print` 直接单测：未到间隔不打、到点打、`state` 变立刻打、**`state` 不变而 `reason` 变也立刻打**、同一条不重复打；PTY 里把 `--print-rate` 压到 1 Hz 跑约 2 s，记录数必须仍是"几条"而不是随 100 Hz 控制循环走（**把 `next_print` 改成每轮都到期，这条即以 60+ 条失败**），见第 12.19 节 |
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
     而它的 J2/J3 下限是 0.0，机械臂零位却在 0.006 rad 附近：反馈一旦略微为负，
     `tick()` 里的 `limits.check(feedback)` 会抛 `ProtocolError`，`main()` 直接退出（退出码 2，
     `finally` 仍把机械臂交回 SOFT）。要么先确认这几轴的实测零位离下限有余量，要么放宽下限。
7. 如要求真正失能，需厂商提供关闭/失能及失能后读反馈的正式 API/协议，当前不能承诺。
8. 每个小改动验证后提交推送，更新本文的验证边界和未完成事项。

### 9.1 解码器已知缺口（接实机前必须处理）

1. **零位不可知。** leader 报的是单圈绝对角，没有自己的零点。`sign` / `offset_deg`
   错了**不会失败得很安全**：它指向的是一个关节限位完全接受的真实位置。不标定就 arm，
   第一批 target 很可能直接撞 `Limits.check`（`control.py:26`）而 FAULT。这是设计缺口。
2. **冻结值抓不到。** 文档 §2 说编码器采到过数据后又断开会**冻结在最后一个有效值**，
   `-1` 判据完全抓不到这种坏法，而冻结值看起来是一个完美的稳定读数。
   需要「N ms 未变化」的存活性判定。本轮只计数/打印。
3. **值域内的静默错误抓不到。** `2117 → 2717` 这种翻转仍落在 `0..3599` 内，
   越界检查看不见。限速只限制单拍步长，长期仍会跟过去。需要可选的最大跳变过滤。
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
正常位置，`Limits.check()`、`max_following_error`、限速都看不见。
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

**验证**（离线，**261 项通过**）：
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
