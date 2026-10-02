# ARX_comtest — ARX X5 独立 Python 串口控制

这是可单独克隆、运行的工程目录，包含程序、测试、配置示例及厂商 Python SDK 快照，
不依赖原来的 `teleoperation_system_RobotPC` 目录。应用使用 Python 3.10+；
实机 SDK 的 Python ABI、CPU 架构和系统库需另外匹配。

另一个 agent 接手时先阅读 [HANDOFF.md](HANDOFF.md)，其中包含需求确认、代码入口、
SDK 状态映射、验证记录、未完成事项和下一步操作；[AGENTS.md](AGENTS.md) 提供简短入口约定。

```text
ARX_comtest/
├── app.py                 # 运行入口：monitor / teleop / preflight
├── backends.py            # SDK 与模拟机械臂
├── control.py             # 状态机、限速及超时处理
├── protocol.py            # 可替换的串口帧解析器
├── leader_decoder.py      # 外接遥操作器 USART3 文本流解码器
├── leader_map.py          # 单圈角度到关节弧度的标定映射
├── leader_calibrate.py    # 采样标定：单点手输方向，或多点拟合，写出 leader_map.json
├── operator_keys.py       # 本地按键 arm/stop 通道
├── limits.example.json    # 关节限制示例
├── leader_map.example.json # 遥操作器标定示例
├── requirements.txt       # pyserial
├── requirements-sdk.txt   # SDK 编译/包装需要的 numpy、pybind11
├── scripts/               # 依赖安装、SDK 编译、环境设置和启动
├── tests/                 # 单元测试和伪终端串口测试
└── vendor/ARX_X5/          # 厂商 SDK、来源说明与许可证
```

单臂程序，不启动 ROS、ZMQ 或原项目的硬件服务器。USB2CAN 对应 SocketCAN
接口（例如 `can0`）；外接遥操作器使用另一个串口，且必须用 `/dev/serial/by-id/`
路径指定（见下方「外接遥操作器」一节的 by-id 警告）。
两者不能使用同一设备节点，也不要和其他机械臂控制进程同时占用同一 CAN 总线。

停止采用 **SOFT 零力矩模式**：`set_arm_status(0)`，并持续读取、
打印六个关节的弧度和角度。SOFT 不是驱动器失能，也不是重力补偿，机械臂需要支撑，
否则会受重力下落。`--stop-mode disabled` 在 SDK 后端会在连接前报错，不冒充真正失能。

**重力补偿是我们用到的另一个状态**：`set_arm_status(3)`，电机按 URDF 动力学算出力矩主动托住自身重量，
可以反驱（用手摆），但**同样不是失能**，也不会被当成停止手段。目前只有 `leader_calibrate.py --arm`
会用（见「标定」一节），遥操作路径仍然只用 SOFT。

## 先运行无需硬件的验证

克隆后在项目根目录执行：

```bash
git clone https://github.com/Crystal-1438/ARX_comtest.git
cd ARX_comtest
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 app.py --mode monitor --duration 1
python3 app.py --mode teleop --demo --duration 1
```

也可以使用安装和启动脚本（在 Debian/Ubuntu 上会通过 apt 安装 `python3-venv`）：

```bash
bash scripts/install_dependencies.sh --mock
bash scripts/run.sh --mode teleop --demo --duration 1
.venv/bin/python -m unittest discover -s tests -v
```

已有可创建 venv 的 Python 时，加 `--skip-system` 可以跳过 apt 和 sudo。

默认后端是 `mock`，完全不加载厂商库、不打开 CAN。demo 经由同一个 JSON 解析器、
状态机和限速器，运行停止 → 控制 → 停止。模拟关节即时响应，不能验证真实机械动态。
串口集成测试使用 Linux 伪终端和真实 pyserial，覆盖拆帧、运动、断流、恢复、异常和拔线。

## SDK 与 USB2CAN 准备

默认 SDK 路径为本仓库 `vendor/ARX_X5/py/arx_x5_python`，相对程序文件解析，
不依赖当前工作目录；也可以通过 `--sdk-root` 指定外部 SDK 目录。
SDK 来自 <https://gitee.com/li-bozha0/ARX_X5>，版本与文件校验见
[厂商 SDK 来源说明](vendor/ARX_X5/SOURCE.md)。只使用现有
`InterfacesPy` 的公开绑定，不修改 SDK 或猜测 CAN 电机报文。

本项目已附带厂商原始 `.so`。Gitee `c783287` 提供的 Python 扩展为
CPython 3.12 / x86_64，不能直接用于本次验证环境的 Python 3.14。
厂商核心库还需要 KDL / kdl_parser 等动态库；其他 Python 版本需使用相同解释器
重新编译绑定，ARM64 则还需厂商提供匹配架构的核心库，本快照不包含 ARM64 二进制。
不要通过把不同 ABI 的库强行改名或软链接来绕过依赖问题。

### 实机依赖安装与 SDK 编译

从工程根目录执行以下脚本。预览不会安装、编译或写文件；正式安装会调用 sudo/apt
安装系统包，在 `.venv` 安装 Python 依赖，然后编译 SDK。**安装过程不连接机械臂**。

```bash
bash scripts/install_dependencies.sh --sdk --dry-run
bash scripts/install_dependencies.sh --sdk
```

依赖清单与用途：

| 依赖 | 安装位置 / 用途 |
| --- | --- |
| `python3-venv`、`python3-dev` | apt；创建虚拟环境与当前系统 Python 开发头文件 |
| `build-essential`、`cmake`、`pkg-config` | apt；编译 SDK Python 绑定 |
| `libkdl-parser-dev`、`liborocos-kdl-dev`、`liburdfdom-dev` | apt；厂商二进制依赖的运动学、URDF 库 |
| `can-utils`、`iproute2` | apt；提供 `slcand`、CAN 工具和 `ip` |
| `pyserial` | `.venv`；接收控制器串口数据 |
| `numpy`、`pybind11` | `.venv`；SDK Python 包装、重新编译绑定 |

硬件安装要求 Linux x86_64。apt 路线要求上述软件包在当前发行版的软件源可用；
[Ubuntu 22.04 universe 提供 libkdl-parser-dev](https://packages.ubuntu.com/jammy/libkdl-parser-dev)。
不能假设每个 Ubuntu 版本都有该包：本次 Ubuntu 26.04 环境中无可用候选版本，脚本会在
安装系统包之前报错退出。不要为此混用其他发行版的 apt 源或创建冒充 ABI 的软链接。
已有厂商/KDL 环境时，先加载其库路径，再用 `--skip-system`；最终仍需通过 SDK 导入检查。

常用选项：

```bash
# 指定 Python；须自行确保有对应版本的 Python.h，python3-dev 仅对应系统 Python
bash scripts/install_dependencies.sh --sdk --python python3.12

# 系统编译工具和 KDL 已安装，只安装 Python 依赖并编译
bash scripts/install_dependencies.sh --sdk --skip-system

# 自定义虚拟环境目录
bash scripts/install_dependencies.sh --mock --venv /path/to/arx-env
ARX_VENV_DIR=/path/to/arx-env bash scripts/run.sh --mode monitor --duration 1

# 依赖已就绪，仅重新编译 SDK
bash scripts/build_sdk.sh --python "$PWD/.venv/bin/python"
```

编译使用仓库自带的两个 C++ 绑定源文件，输出到 `build/`，安装到 `.sdk/`。
原始 `vendor/` 不会被修改。只有依赖、编译、两个 Python 扩展导入及所需 API 检查全部
成功，才写入 `.sdk/READY`。这些检查不会实例化 `InterfacesPy`。
`scripts/run.sh` 自动加载环境：优先使用有 READY 标记的 `.sdk`，否则使用原厂快照。
原厂快照仍需匹配 Python 3.12 与系统库，回退不代表 SDK 已经可用。

可选手动启动方式：`source scripts/env.sh` 后使用 `.venv/bin/python app.py ...`。
`env.sh` 设置 `ARX_SDK_ROOT`、`ARX_VENV_DIR` 和动态库路径，不会自动切换当前 Python；
显式 `--sdk-root` 优先于环境变量。无需向系统目录复制库、修改 sudoers 或安装 ROS 服务。

### 设备预检查

预检查仅导入扩展、查看设备，不实例化机械臂，不发送 CAN 指令：

```bash
bash scripts/run.sh --mode preflight --can-port can0 --serial /dev/ttyUSB1
```

退出码 `0` 表示上述检查通过；`2` 表示缺少依赖、设备或 ABI 不兼容，需先解决。
这不是电机在线/反馈新鲜度检查。

USB2CAN 根据适配器类型二选一配置，命令只供实机执行：

```bash
# 原生 SocketCAN 型适配器（确认适配器/固件支持 1 Mbps）
sudo ip link set can0 up type can bitrate 1000000

# 或厂商 SLCAN 型适配器；/dev/arxcan0 是 USB2CAN 的设备节点
sudo slcand -o -f -s8 /dev/arxcan0 can0
sudo ip link set can0 up
```

SLCAN 参数来自上游 SDK 的 `ARX_CAN/arx_can/arx_can0.sh`，设备命名由实际 udev 规则决定。
程序不会修改 udev、sudo 权限、CAN 配置或自动启动/杀死 slcand。

## 停止状态打印关节角度

先支撑机械臂，选择正确型号。2023 使用 `--model 2023`（type=0），
2025 使用 `--model 2025`（type=2），应以实物型号为准。

```bash
bash scripts/run.sh --backend sdk --mode monitor --model 2023 --can-port can0
```

启动进入 SOFT；按 10 Hz 输出 JSON，包含 `joints_rad`、`joints_deg`、状态及原因。
可用 `--print-rate 5` 调整输出频率。读取 SDK 返回的前六个关节，第七通道是夹爪。
`host_read_monotonic` 是本机读取时刻，不是电机反馈时间戳。

## 串口正常控制

先检查 `limits.example.json`，将其复制为自己的配置并按实物、安装及允许作业范围核实。
示例角度范围沿用原项目 `teleoperation_system_RobotPC/gello/robots/x5_fixed.py`，
不是重新认证的厂商限位；全部使用
SDK 原始关节坐标、rad，不做该文件中的 GELLO 零位偏置。
`max_speed` 单位 rad/s，`max_following_error` 单位 rad，`timeout` 单位秒。

```bash
bash scripts/run.sh --backend sdk --mode teleop --model 2023 \
  --can-port can0 --serial /dev/ttyUSB1 --baud 115200 \
  --limits /path/to/your-verified-limits.json
```

默认控制循环 100 Hz，应用目标变化率上限 0.2 rad/s，250 ms 未收到有效目标则进入
FAULT 并请求 SOFT。读取串口不阻塞，不完整帧不会延后超时；积压超过 4096 字节则报错。
上电/启动不会回零。必须收到 `arm` 且 `deadman=true` 才以当前测量位置开始控制，
同时捕获夹爪当前位置，避免切入厂商位置模式时跳到默认夹爪目标。
本程序不提供遥操作夹爪或笛卡尔位姿控制，输入为六关节绝对目标。

坏帧、非法角度、重复序号会触发停止；错误输入不会刷新超时计时器。
FAULT 后需要分开发送 `stop`、`arm` 再恢复，普通目标帧不会自动恢复运动。
同一读取批次中 `stop` 之后的帧会丢弃，建议至少隔一个控制周期再发 `arm`。
退出、Ctrl+C、SIGTERM 或串口异常时均尝试 SOFT；串口异常退出码为 2。

SOFT、重力补偿和位置模式切换均无硬件确认反馈：发出去就在本端当作已生效，
读不回当前状态，也无法确认机械臂真的进入了该模式。SDK 构造函数会启动自己的线程，可能使能电机；
SDK 不提供公开的反馈时间戳、线程关闭、通信 watchdog 或失能确认接口。
因此本程序的超时保护只在 Python 循环正常运行时有效，无法保证进程被强杀、
SDK 卡住、CAN 拔线之后的电机行为。实机阶段应先验证外部急停与断流行为。

## 外接遥操作器（Leader_f103c8t6）

`docs/uart_packet.md` 是这块板的完整线格式规格。要点：USART3、115200 8N1、
ASCII 行 `<J1>,<J2>,<J3>,<J4>,<J5>,<J6>,<J7>\r\n`，约 200 Hz；
前六维是 **0.1° 单圈绝对角**（`0..3599`），第七维是夹爪 ADC（`0..1000`）。
**没有 CRC，也没有序号**——一个被翻转的字节会变成一个看起来合法的数值，
所以解码器唯一能抓到的损坏就是落到了文档区间之外的值（那会按故障处理）。
包之间也判不出丢包，只能靠统计收包数反推。

### 端口必须用 by-id

CH340（这块板）和 CANable2（USB2CAN）**都是 `/dev/ttyACM*`**，编号会随插拔顺序变。
`docs/uart_packet.md` 里「`/dev/ttyACM0` 不是这块板的串口」这句话在 Robot PC 上不成立
（实测该 by-id 正指向 `ttyACM0`）。始终用 by-id 路径，不要用 `ttyACM` 编号，
否则可能误占 `slcand` 正在用的 CAN 适配器端口。

```bash
ls -l /dev/serial/by-id/      # 确认哪一个是 1a86 CH340、哪一个是 CANable2
```

### 先只解析，不驱动机械臂

不加 `--operator-keys` 就永远不会 arm，属于纯解析；用输出的 `leader` 块看结果。
这一步只读串口、用模拟机械臂，不开 CAN、不加载厂商库：

```bash
bash scripts/run.sh --mode teleop --backend mock \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
  --decoder "$PWD/leader_decoder.py" --print-rate 5 --duration 10
```

`leader` 块里的字段：

| 字段 | 含义 |
| --- | --- |
| `frames` / `dropped` / `no_data` / `resets` | 累计收到、丢弃、`-1`、板子复位次数 |
| `frame.angle_deg` / `gripper` / `fields` | 最近一帧的解读 |
| `frame.target_rad` | 经映射后真正要发给机械臂的六维目标 |
| `frame.host_monotonic` | 该帧的解析时刻；**它不动就说明流停了**（值会保留，不会变空） |
| `map_source` / `calibrated` | 实际加载的标定文件；`<uncalibrated default>` 表示没有标定 |
| `reference` | 起始帧与 map 记录的基准姿态的比对；见下节 |
| `error` | 本批被判为故障的原因 |

`frames` 与 `seq` 不是一回事：`seq` 每个控制周期最多加一，跟的是控制循环；
`frames` 数的是真正收到的包，判 200 Hz 和丢包要看它。

### 按键控制

这块板只报位置，不报 arm/stop，所以必须由本地按键显式使能：

```bash
bash scripts/run.sh --mode teleop --backend mock \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
  --decoder "$PWD/leader_decoder.py" --operator-keys --limits /path/to/limits.json
```

`a` 使能（以当前测量位置为起点），`s` 或空格停止，`q`/Ctrl+C 退出。
按键先于同批串口帧处理，所以本地停止不会被同一批的目标盖过。
FAULT 后必须先按 `s` 再按 `a`，与线协议恢复语义一致。

`a` 有一个前置条件：**至少要收到过一帧，且这一帧要落在 map 记录的基准姿态附近**。
不满足就不会 arm，`reason` 里写的是为什么（例如 `refusing to arm: the leader started +90.0 deg
from the calibrated pose (J3, tolerance 10 deg); ...`），机械臂一个目标都不会收到。
理由见下面「基准姿态」一节。

### 标定：接实机之前必须做

leader 报的是**单圈绝对角**，没有自己的零点。要变成关节弧度，需要每个关节的
方向（`sign`）、零位（`offset_deg`）和是否多圈（`unwrap`）——**规格里没有，必须实测标定**。
`leader_calibrate.py` 做这件事：**把机械臂和 leader 用手摆成同一个姿态**，同时读两边。

有两条路，**默认走第一条**：

- **单点 + 手输方向（快）**：只摆**一个**姿态，按 `d`，然后**自己看着机械臂**逐关节回答方向。
  方向已知时一个姿态就能把零位钉死——映射在这个基准姿态上精确成立。代价是
  **没有任何数据能反驳你打的符号**，所以它带一个可选的第二姿态复核（见下）。
- **多点拟合（慢，但由数据自证）**：摆 3~4 个姿态按 `f`，方向和零位都由数据解出。
  斜率必须≈±1 才写文件。适合单点那条路复核不过、或者你不想靠肉眼判断的时候。

两条路都要求**第一个姿态是基准姿态**：遥操作的展开是从进程收到的第一帧数圈数的，
所以每次遥操作都要把 leader 摆在基准姿态再启动程序。工具把这个姿态的**原始角度**写进
`reference_deg`，运行期由程序替你核对（见下）。

命令不 arm、不发目标。**加了 `--arm` 就会让机械臂进重力补偿**（状态 3）：电机主动托住自身重量，
所以你可以用手摆姿势、松手它也不掉——这是标定能单手做的原因。**它是通电驱动状态，不是失能**，
而且本机没有外部急停：机械臂必须已经支撑好，人不能离开。
它也不等于"稳"：力矩由 URDF 动力学算出，实际负载和夹爪不在模型里就会缓慢漂移，**别指望它自己悬停**。
不加 `--arm` 时一切照旧：不碰 CAN、构造厂商库都不会发生，机械臂仍是 SOFT 零力矩（会下落，需支撑）。

推荐用交互模式，**采集时机由你决定**（`scripts/calibrate.sh` 只是 source 好环境的包装）：

```bash
bash scripts/calibrate.sh session --arm --model 2023 --can-port can0 \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00
```

屏幕上实时显示 leader 六个关节的角度、抖动和机械臂当前角度。**用手把两边摆成同一个姿态**，
扶稳，然后按键：

| 键 | 作用 |
| --- | --- |
| `c` 或回车 | 采集当前姿态（取最近 `--window` 秒的中位数） |
| `d` | 从**已采集的第一个姿态**出发，逐关节问你方向，可选复核，再写 map |
| `u` | 撤销上一条 |
| `f` | 拟合多个姿态并写 `leader_map.json`，成功即退出 |
| `q` | 退出（已采集的姿态留在 `calibration_session.jsonl`，可事后 `fit`） |
| `h` | 帮助 |

#### 单点 + 手输方向（默认）

摆好一个姿态、扶稳，按 `c` 采集（这就是基准姿态），然后按 `d`。屏幕上从 J1 开始逐个问，
**当前问的那个关节前面有 `>`**，提示行同时显示它相对基准姿态动了多少：

```
  J1 direction: + if the arm angle rises when the leader angle rises, - if it falls
  moved since the pose: leader +12.3   arm +12.4   [backspace] back   [x] cancel
```

**这就是你要看的证据**：轻轻动一下那一个关节，看 leader 和 arm 两列是同向还是反向，
同向按 `+`、反向按 `-`。`backspace` 退回上一个关节，`x` 取消（姿态还在，按 `d` 重来）。
**问答期间按键都归问答**（`q` 也不例外），想退出先按 `x` 取消。

六个答完后再选：

| 键 | 作用 |
| --- | --- |
| `c` | **复核**：把两边摆到**另一个明显不同的姿态**再按一次，用位移方向反查你打的符号 |
| 回车 | 直接写文件，文件里会注明"未复核" |
| `x` | 什么都不写 |

复核是有牙齿的：**只要有任何一个关节的位移和你的符号相反，就拒绝写文件**并点名那个关节；
如果新姿态离基准太近、什么也证明不了，也不会装作通过，而是让你把关节再挪开一点。
`c` 可以按多次，每次都对最新那个姿态复核。

**为什么复核值得做**：单点路径对你输入的方向**毫无抵抗力**——符号错了不会失败得很安全，
它只是让那个关节在离开基准姿态后走反（在基准姿态上反而完全正确，所以当场看不出来）。
这一点写在生成文件的注释里。

#### 多点拟合（备用）

状态行里的 `still needing range` 会点名**哪些关节所有姿态加起来动得还不够**（跨度 < 30°），
照着把那个关节多摆开一点。`f` 拟合失败不会退出，按提示补姿态再来即可。
`q` 提前退出时退出码是 2、且不写 map——"采了一半"和"标定完成"能分开。

**用了 `--arm` 的话，退出前还有一步确认**：会话结束（`q` 或 `f` 成功）后工具不会自己松手，
而是提示"机械臂仍在重力补偿、正托着自己"，等你确认它已支撑好、**按回车**才交回 SOFT
（零力矩，会落到支撑上）。这样机械臂不会在你还在打字时突然掉下来，也不会在进程退出后
还留在通电状态无人看管。Ctrl+C / Ctrl-D / SIGTERM 属于"现在就要停"，**跳过确认直接回 SOFT**
（退出码 130），所以按中断键时要准备好扶住机械臂。SIGTERM 是被显式接管的：不接管的话进程会被
直接杀掉，`finally` 根本轮不到执行。

不使用终端时（管道、CI）交互模式会直接拒绝，那种场合退回到 `sample` + `fit`，
也就是上面那条**多点拟合**路子——`sample` 没有地方输入方向，所以它只能拟合：

```bash
# 非交互：每个姿态一条命令。--arm 在同一进程里进重力补偿、取一次手臂角度，
# 因为这里没有终端可以问，命令结束时会自动交回 SOFT 并打印说明（机械臂会落到支撑上）。
# 第一个姿态是基准姿态，后面必须从它开始。
bash scripts/calibrate.sh sample --arm --model 2023 --can-port can0 \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
  --label "pose A"

# 3 个姿态起，4 个更稳。然后：
bash scripts/calibrate.sh fit calibration_session.jsonl --out leader_map.json
```

- **每个关节都要动**：某个关节在所有姿态里几乎没变，拟合会拒绝它（跨度最小 30°）。
- 姿态之间leader 每个关节的**真实行程不要超过半圈**，否则单圈编码器分不清正负绕行，拟合会拒绝。
- `--arm` 需要 SDK 环境：先 `source scripts/env.sh`，或直接对着 `.sdk` 运行。

`fit` 输出是一张表：`关节 | leader 跨度 | 斜率 | sign | offset | 最大残差`。
斜率就是方向，**因为两边关节配置相同，它必须≈±1**；明显不是 ±1 说明假设错了，
工具会拒绝写文件而不是硬凑。最大残差衡量的是你把两边摆成"同一个姿态"的重复程度，
几个度以内是正常的。

**任一关节不通过就整个拒绝**（没有 `--force`）：半标定的映射比没标定更危险。
公式是 `sdk_deg = sign * continuous_deg + offset_deg`（再转 rad）。
**未标定的映射不会失败得很安全**：符号或零位错了，指向的是一个关节限位完全接受的
真实位置。因此程序在 `--backend sdk` 的 teleop 下会**拒绝启动**，直到配置文件里
写了 `"calibrated": true`；解码器发不出 `arm`/`stop` 而 `--operator-keys` 又没开时同样拒绝。
`JsonLineDecoder` 不声明这两个属性，因此原有硬件路径不受影响。

### 基准姿态：为什么必须有，以及程序怎么替你查

生成的 `leader_map.json` 里记了 `reference_deg`——**基准姿态的原始角度**。
展开是从进程收到的第一帧开始数圈数的，而 offset 是"在基准姿态上"解出来的，
两者的起点必须重合，所以**每次遥操作都要把 leader 摆在那个姿态再启动程序**。

起点不重合的后果不是"报错"，而是**机械臂自己走**：整个映射被平移了那么多，
所以差多少、它就朝那个方向走多少。基准姿态上这套映射完全正确，离开它就整个偏掉，
而偏掉之后的目标位置对关节限位来说是个完全正常的位置，控制环里没有任何东西能看出不对。

所以运行期会核对：**第一帧**与 `reference_deg` 逐关节比较，任何一个关节超出
`REFERENCE_TOLERANCE_DEG`（10°）就拒绝 arm，并点名最差的那个关节。
比较用的是**直接相减**而不是最近圈——`0/360` 的另一侧只差 10° 物理角，
读数却是 350°，而 mapper 也只能按 350° 去发（这时候它还没有历史可以展开）。
`leader.reference` 里能看到每关节的差值和 `ok`。

**在收到第一帧之前按 `a` 同样被拒绝**：否则先按键的人就绕过了这个检查。

`reference_deg` 缺失（早于这个字段、或手写的 map）时会照常运行，但
`leader.reference` 会是 `{"checked": false, ...}`——**表示没查过，不是查过没问题**。
`leader_calibrate.py` 生成的文件都带这个字段。

已知缺口，接实机前必须处理：文档 §2 说编码器采到过数据后又断开会**冻结在最后一个有效值**，
`-1` 判据抓不到这种坏法；值域内的静默错误（`2117 → 2717`）也抓不到。
两者都需要额外的存活性/跳变判定。标定工具只会在采样窗口里提示 jitter 大不大，
运行期还没有这个检查。这两条见 [HANDOFF.md](HANDOFF.md) 第 9.1 节。

## 临时帧格式与后续替换

当前只为开发验证提供 UTF-8 JSON，每帧以换行结束，115200 8N1 是默认测试值。
**这不是外接遥操作器的最终协议**。`seq` 在本次进程内严格递增；控制器重启后需同时
重启接收程序，避免旧序号被误认为新指令。布尔值必须为 JSON 的 true/false。

```json
{"v":1,"seq":1,"type":"arm","deadman":true}
{"v":1,"seq":2,"type":"target","deadman":true,"joints":[0.0,0.2,0.2,0.0,0.0,0.0]}
{"v":1,"seq":3,"type":"stop"}
```

按键释放时发 `deadman=false` 或 `stop`；控制时以稳定频率持续发 `target`。
最大帧长 1024 字节。不接受 NaN/Inf、错误关节数量、重复字段、未知字段或字符串角度。
临时协议没有 CRC、控制器时间戳和会话握手，正式硬件协议应明确这些内容、关节顺序、
单位、零位、方向及夹爪通道，不能直接把编码器数值当作机械臂角度发送。

确定协议后只需提供自定义 Python 文件：

```python
from protocol import Command, ProtocolError

class Decoder:
    def feed(self, data: bytes) -> list[Command]:
        # 缓存半帧、找帧头、校验长度/CRC、解码与单位/零位映射。
        # 没有完整帧返回 []；非法帧 raise ProtocolError；禁止在此访问机械臂。
        # 返回 Command("target", seq, tuple(six_angles_rad), deadman=True)。
        raise NotImplementedError("等待控制器协议")

def create_decoder():
    return Decoder()
```

通过 `--decoder /path/to/controller_protocol.py` 加载。每批返回至多 64 个 Command，
主循环仍会检查序号、关节范围、deadman、限速和超时。解码器应快速返回，不做阻塞 I/O。

## 本次验证边界（2026-10-02）

已验证 Python 控制逻辑、SDK 调用顺序（替身）、伪终端串口接收和模拟运行。
105 项测试通过，包括独立目录、安装预览、缺包报错和启动脚本检查，
以及遥操作器解码（拆行、握手、`-1`、越界、映射与展开）、本地按键通道和
「leader 字节→解码→映射→状态机」的伪终端端到端链路（全程 mock，不碰 CAN）。
模拟依赖安装已在新的 `.venv` 中实际运行成功；两个 SDK 绑定已用 Python 3.14 / pybind11 3
编译并安装到验证目录，但本机缺少 KDL 运行库，完整 SDK 安装正确报错且未产生 READY 标记。
工作机上没有 CAN / USB 串口设备，未完成 SDK 导入成功验证、实机读角度或运动测试。
这些已在另一台 Robot PC（Ubuntu 22.04，接 USB2CAN 与机械臂）完成，见
[HANDOFF.md](HANDOFF.md) 第 12 节；**两节的结论不可互相覆盖**，尤其「SDK 能否加载」
在两台机器上答案不同。遥操作器解码器已在 Robot PC 上对着真实串流跑通（约 211 Hz，
零错误），但仍然只在模拟机械臂上验证，未驱动过真机。
请先完成标定（见上），再进行低速串口控制测试。
