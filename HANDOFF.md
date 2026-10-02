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

**序号冲突的解法**（不要改回去）：decoder 的 `seq` 与 `controller.last_seq` 是两个独立
空间。`control.py` 早就让 `stop` 豁免序号单调检查，现在把 `arm` 也纳入这条「操作员通道」
（`operator_arm()` / `operator_stop()`），二者都不碰 `last_seq`。这样 `protocol.py` 零改动，
`JsonLineDecoder` 也能直接配本地按键。**不要**引入 decoder 必须提供的共享 `SeqCounter`
隐式契约。

**门禁**：leader 映射未标定时 `--backend sdk --mode teleop` **拒绝启动**，解码器发不出
`arm`/`stop` 而 `--operator-keys` 又没开时同样拒绝。理由见第 9 节缺口 1。两个检查都是
decoder 侧 opt-in 的（`calibrated` / `provides_arm`），`JsonLineDecoder` 不声明这两个属性，
原有硬件路径不受影响。

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
| `.venv/bin/python -m unittest discover -s tests -v` | 105 项通过，含真实 pyserial + PTY |
| leader 解码器离线测试 | 拆行、握手、`-1` 预热/故障、越界、缠绕展开、映射、`reset()` 语义 |
| leader 端到端（PTY，全 mock） | 字节 → 解码 → 映射 → 状态机 → 按键 arm/stop/FAULT 恢复 |
| 本地按键通道测试 | cbreak 的 termios 恢复、非 tty 回退、单批多键、fd 生命周期 |
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
5. leader 解码器已接入（第 6.1 节）。**下一步是标定，不是调参**：
   先只解析（不加 `--operator-keys`，见 README「外接遥操作器」一节），逐个关节实测
   `sign` / `offset_deg`，写进被忽略的 `leader_map.json` 并置 `"calibrated": true`；
   门禁会一直挡着实机 teleop，直到这一步完成。
6. 标定之后再处理第 9.1 节列出的两个解码器缺口（冻结值、值域内静默错误），
   然后才做低速实机控制，并从 mock 换成 `--backend sdk`。
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
4. **文档待更正（不改用户文档，在此记录）。** `docs/uart_packet.md:21` 称
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

- 实机运动、限位校准、leader 角度标定。
- 移动 leader 以确认编码器跨度（第 12.8 节的未决观察）。
- 用 `--backend sdk` 试跑 leader teleop：门禁会拦下未标定的映射，这是预期行为。
