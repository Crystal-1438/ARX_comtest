# ARX_comtest — ARX X5 独立 Python 串口控制

这是可单独克隆、运行的工程目录，包含程序、测试、配置示例及厂商 Python SDK 快照，
不依赖原来的 `teleoperation_system_RobotPC` 目录。应用使用 Python 3.10+；
实机 SDK 的 Python ABI、CPU 架构和系统库需另外匹配。

另一个 agent 接手时先阅读 [HANDOFF.md](HANDOFF.md)，其中包含需求确认、代码入口、
SDK 状态映射、验证记录、未完成事项和下一步操作；[AGENTS.md](AGENTS.md) 提供简短入口约定。

```text
ARX_comtest/
├── app.py                 # 运行入口：monitor / teleop / preflight / probe-gripper
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

### 测量夹爪的第七通道

夹爪在 `set_catch()` 里"完全打开/完全闭合"各是什么数值，**本仓库里查不到**：SDK 头文件不给单位，
URDF 里没有夹爪关节，实现里连范围检查都没有。所以只能实测，`--mode probe-gripper` 就是干这个的。
它**只读第七通道**：不建 `Controller`、不 arm、不进位置控制或重力补偿、不发任何指令。

```bash
bash scripts/run.sh --backend sdk --mode probe-gripper --model 2023 --can-port can0
```

这一路进的是 SOFT，**零力矩、机械臂会下坠**：先把臂支撑好。工具分两次提示——先把夹爪手推到
**完全打开**并保持、回车，再推到**完全闭合**、回车，然后打印两个带标签的读数。两次相同会被判为
失败（说明夹爪没动，或第七通道根本不是夹爪），退出码 `2`。终端不是 tty 时退化成连续打印并在退出时
给出 min/max，可以用 `--duration` 限定时长：

```bash
python3 app.py --mode probe-gripper --backend mock --duration 3
```

工具**只打印，不写任何文件**。它测的也只是"读"这一半：`set_catch()` 是否吃同一个数值单位，
是从 `VendorArm.start()` 沿用下来的假设，这个工具证明不了。

## 串口正常控制

先检查 `limits.example.json`，将其复制为自己的配置并按实物、安装及允许作业范围核实。
示例角度范围沿用原项目 `teleoperation_system_RobotPC/gello/robots/x5_fixed.py`，
不是重新认证的厂商限位；全部使用
SDK 原始关节坐标、rad，不做该文件中的 GELLO 零位偏置。
`max_speed` 单位 rad/s，`max_following_error` 单位 rad，`timeout` 单位秒。
`td_r_deg` 是**逐关节**的加速度上限，单位 deg/s²——这是本文件里唯一用角度的地方，
因为参考实现（`ref/adrc.c`）里的 `r` 就是这个量纲；示例值是 400/500/600/4000/1000/4000。

```bash
bash scripts/run.sh --backend sdk --mode teleop --model 2023 \
  --can-port can0 --serial /dev/ttyUSB1 --baud 115200 \
  --limits /path/to/your-verified-limits.json
```

默认控制循环 100 Hz，250 ms 未收到有效目标则进入 FAULT 并请求 SOFT。
读取串口不阻塞，不完整帧不会延后超时；积压超过 4096 字节则报错。

**发给机械臂的不是目标，是一条轨迹**：每个关节有一个独立的跟踪微分器
（`td.py`，逐项照抄 `ref/adrc.c` 的 `TDFunction_independent`），用该关节的
`td_r_deg` 作为加速度上限，把目标跟踪过去。`td_r_deg` 越大跟得越紧、滞后越小，
也越容易把输入的抖动放大；越小越平滑。`max_speed` 仍给轨迹的**速度**设上限：
微分器限制的是加速度，它本身对速度没有上限，而机械臂跟得上多快由那条限制决定。
轨迹在按 `a` 时从实测位置、零速度起步，所以使能本身不是一次跳变；它也**不会越过目标**，
目标已经夹在范围内，所以发出去的指令不会自己跑出限位。角度用 mapper 解缠后的**多圈值**，
不折回 0..360——折回去的话，每个关节经过 0/360 的那一次都会被当成整整一圈的阶跃。
上电/启动不会回零。必须收到 `arm` 且 `deadman=true` 才以当前测量位置开始控制，
同时捕获夹爪当前位置，避免切入厂商位置模式时跳到默认夹爪目标。
本程序不提供遥操作夹爪或笛卡尔位姿控制，输入为六关节绝对目标。

坏帧、非有限角度、重复序号会触发停止；错误输入不会刷新超时计时器。
FAULT 后需要分开发送 `stop`、`arm` 再恢复，普通目标帧不会自动恢复运动。
同一读取批次中 `stop` 之后的帧会丢弃，建议至少隔一个控制周期再发 `arm`。
退出、Ctrl+C、SIGTERM 或串口异常时均尝试 SOFT；串口异常退出码为 2。

**超出 `--limits` 是限幅，不是停机**：目标位置越界时只把这一个分量夹到边界并保持，
控制不中断——对操作者来说，"手推过了一度"和"目标是真越界"在这里分不出来，而停机意味着
`arm.stop()` 走 SOFT（零力矩）、机械臂因重力下坠，比顶在限位上更糟。`--watch` 那一行会
补出 `at the limit: J5`，说明是哪个关节顶到了限位、机械臂为什么不再跟手。把 leader 拉回
范围内就立刻恢复跟随：被夹的只是发出去的那条指令，映射本身不动，不丢位置。

机械臂**实测**位置越界则拒绝 arm，并写明关节、当前值和配置区间，例如
`J6 +2.000 not in [-1.000, +1.000]`。这几乎总是 `limits.json` 与这台机械臂不符：
`limits.example.json` 是从原 gello 配置抄来的起点，**不是**在你这台机械臂上量过的限位。
这时把机械臂摆回配置范围内，或按厂商规格把 `limits.json` 改对。限位仍是一条安全边界：
范围设得比实物允许的宽，限幅也挡不住机械臂撞上真实障碍。

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
| `anchor` | 按 `a` 那一刻的整圈锚定结果：挑中的整圈、剩下的物理差、`ok`。没 anchor 过时是 `null`；见下节 |
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

**更省事：`--watch` 加 `--print-rate 1`。** `--watch` 把整条 JSON 换成一行，
每关节报"还要转多少度才到机械臂现在的姿态"，与 `a` 的门禁是**同一个数**，
所以这一行变好的瞬间就是按 `a` 能成的瞬间：

```bash
bash scripts/run.sh --mode teleop --backend mock \
  --serial /dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE8010651-if00 \
  --decoder "$PWD/leader_decoder.py" --operator-keys --limits limits.json \
  --watch --print-rate 1
```

```
01:28:38 STOPPED | J1   +0.0  J2  +35.1  J3   +0.0  J4   +0.0  J5 -129.1  J6   +0.0  | out of pose: J2 J5 (tolerance 30 deg)
01:28:40 STOPPED | J1   +0.0  J2  +33.8  J3   +0.0  J4   +0.0  J5   -0.4  J6   +0.0  | out of pose: J2 (tolerance 30 deg)
01:28:44 STOPPED | J1   +0.0  J2   +0.9  J3   +0.0  J4   +0.0  J5   -0.2  J6   +0.0  | in the arm's pose, press a
01:28:45 ACTIVE  | armed at measured position
01:28:52 ACTIVE  | armed at measured position  | at the limit: J5
```

第一列是时钟，`ACTIVE`/`FAULT` 时只报状态与理由（这时已经没什么可转的）；
尾部多出 `at the limit: J5` 表示 J5 的输入已经越界、指令被夹在限位上不再跟手
（见上文"超出 `--limits` 是限幅，不是停机"）。
`1 hz` 是打印频率，控制循环仍是 `--rate`（默认 100 Hz）；`--watch` 下不需要再管道过滤。
**厂商 SDK 自己打的 "ARX方舟无限" 不进这个画面**：它从 C++ 直接写 fd 1/2，被重定向到
`--arm-log`（默认 `teleop_arm.log`）——要看它去翻那个文件。

**不加 `--watch` 时**默认 10 行/秒、一行一整条 JSON，读不过来，用 `--print-rate` 调低。
调低不会漏掉关键信息——**`state` 或 `reason` 一变就立刻打一行**，不等定时器，
所以按 `a` 的结果（`armed at measured position`，或那句 `refusing to arm: ...`）
永远当场出现。定时器只管"什么都没变"时的心跳行。
想只要 JSON 里的状态变化，把输出喂给过滤器即可（按键从终端读，不受管道影响）：

```bash
... --operator-keys --limits limits.json | python3 -u -c '
import json, sys, time
seen = None
for line in sys.stdin:
    try:
        r = json.loads(line)
    except ValueError:
        print(line, end="", flush=True)   # tracebacks and other noise pass through
        continue
    if (r["state"], r["reason"]) == seen:
        continue
    seen = (r["state"], r["reason"])
    anchor = (r.get("leader") or {}).get("anchor")
    print(time.strftime("%H:%M:%S"), r["state"], "|", r["reason"],
          "| anchor:", "null" if anchor is None else ("ok" if anchor["ok"] else "refused"),
          flush=True)
'
```

`leader.anchor` 是不是 `null` 就能看出按 `a` 有没有被处理过：`null` 表示还没有锚定过
（没按过，或按了但那会儿连一帧都没收到——后者 `reason` 会写明）。

`a` 有一个前置条件：**至少要收到过一帧，而且 leader 和机械臂得在同一个姿态（30° 以内）**。
意思是**用手把 leader 摆成机械臂现在的样子**，再按 `a`。不满足就不会 arm，
`reason` 里逐关节写出**要转到哪儿**和**为什么**，机械臂一个目标都不会收到：

```
refusing to arm: the leader and the arm are not in the same pose: J2 reads 287.9 deg where
the arm's pose calls for 323.0 (turn it +35.1 deg); J5 reads 78.8 deg where the arm's pose
calls for 309.7 (turn it -129.1 deg). Arming here would move J2 +35.1 deg and J5 +129.1 deg
(tolerance 30 deg). Hand-match the leader to the arm and press a again
```

**`reads` 就是板子上那三个数除以 10**（287.9 对应板子上的 `2879`），不是展开后的内部值——
转过 `0/360` 的关节也在这一圈里报，照着板子对得上。
两个数**等大**，方向各自与关节的 `sign` 有关：`turn it +35.1 deg` 是**你要转的**
（最短圈，符号是方向），`move J2 +35.1 deg` 是**真按下去机械臂会走的**（J2 的 `sign`
是 −1，所以两者同向；`sign` 为 +1 的 J5 就是 `turn it -129.1` 对 `move +129.1`）。
按 `a` 的瞬间给每个关节定了一整圈（2π 的整数倍）的偏置，把单圈编码器看不出的圈数补上，
之后一直带着它映射——所以 `0/360` 的另一侧不再是问题，见下面「按 `a` 时的整圈锚定」一节。

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

两条路都要有**一个**姿态作为基准（拟合的那条是第一个），因为它把零位钉死：
offset 是"在这个姿态上"解出来的。工具把这个姿态的**原始角度**写进 `reference_deg`。
它只是**出处记录**——遥操作不必从这个姿态启动，运行时由机械臂自己的反馈定圈数（见下）。

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
# 第一个姿态会作为 reference_deg 记进 map（出处记录），之后的遥操作不必从它启动。
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

### 按 `a` 时的整圈锚定：编码器看不出圈数，机械臂看得出

leader 是**单圈绝对编码器**：一个关节转到哪个圈，读数都落在 `0..359.9` 里，
所以 `14.2` 和 `374.2` 是**同一个读数**。要发关节弧度就必须知道它在哪一圈，
而这件事**在 leader 这一侧无解**——线里根本没有这个信息。

机械臂的实测关节角是唯一能补上它的东西，所以补的时机就是按 `a` 那一刻：

1. 把机械臂实测的每个关节角**反解**成 leader 该读的角（`needed = (arm_deg − offset) / sign`）；
2. 每个关节挑一个**整圈**（360° 的整数倍）偏置，让 leader 的读数离 `needed` 最近；
3. 记下这个偏置，之后每帧都带着它映射，**直到退出遥操作模式**。

于是判据是剩下那点**物理差**（`residual`，恒在 ±180° 内），超过
`ANCHOR_TOLERANCE_DEG`（30°）就拒绝，并把**所有**不合格的关节列出来——只报最差的一个
会让人修完 J2 重按、再被告知 J5 也不合格。`leader.anchor` 里能看到整圈偏置、
每关节的残差、最差关节和 `ok`。

这带来一个**操作指令上的变化**：前提不再是"把 leader 摆回 map 记的那个姿态"，
而是**"把 leader 摆成和机械臂一样"**——后者才是遥操作真正需要的前提，而且对任何
机械臂姿态都成立。`reference_deg` 退化成**出处记录**（offset 是在那个姿态上量的），
运行期不再用它判定。

判据从"字面差"换成"残差"这件事本身就是要解决的问题：以前 `0/360` 另一侧只差
10° 物理角、读数却是 350°，会按 350° 拒绝（而那时 mapper 也确实只能按 350° 发）。
现在整圈偏置把那 360° 吃掉了，只剩下那真实的几十度，两个数**大小相等**——差异全在
符号上，而符号由该关节的 `sign` 决定：

- `turn it -51.4 deg`——**你要转多少**，最短圈，符号是方向。`leader_map.shortest_turn()`。
- `move J2 -51.4 deg`——**真按下去机械臂会走多少**，即 `sign * residual`。两者等大，
  同号还是反号看该关节的 `sign`（J2 是 −1，同号；J5 是 +1，反号）。

**在收到第一帧之前按 `a` 同样被拒绝**（此时没有读数可以定圈，硬猜等于盲发目标）。

**这条门禁装在 `Controller` 的 arm 转移上，不是装在按键处理里**：进 ACTIVE 有两条路
（串口帧里的 `arm`，和本地按键），只堵一条等于没堵。解码器只要提供 `anchor` 方法
就会被装成 `pre_arm`；`JsonLineDecoder` 没有，行为一字不变。

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
主循环仍会检查序号、deadman、每个关节的加速度/速度上限和超时，越界的关节目标会被限幅（不是拒绝，
见上文"超出 `--limits` 是限幅，不是停机"）。解码器应快速返回，不做阻塞 I/O。

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
