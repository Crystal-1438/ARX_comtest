# ARX_comtest — ARX X5 独立 Python 串口控制

这是可单独克隆、运行的工程目录，包含程序、测试、配置示例及厂商 Python SDK 快照，
不依赖原来的 `teleoperation_system_RobotPC` 目录。应用使用 Python 3.10+；
实机 SDK 的 Python ABI、CPU 架构和系统库需另外匹配。

另一个 agent 接手时先阅读 [HANDOFF.md](HANDOFF.md)，其中包含需求确认、代码入口、
SDK 状态映射、验证记录、未完成事项和下一步操作；[AGENTS.md](AGENTS.md) 提供简短入口约定。

需要单独研究或使用重力补偿计算时，见 [gravity_compensation](gravity_compensation/README.md)：
已提取 URDF 模型、KDL 静态递推算法及厂商力矩缩放逻辑。当前提供面向 STM32 的
[纯 C99 / float 版本](gravity_compensation/c/README.md)，无外部依赖；Python 版本保留作验证参考。
该模块仅计算六关节力矩，不连接机械臂，也不改变当前应用的停止/控制模式。

```text
ARX_comtest/
├── app.py                 # 运行入口：monitor / teleop / preflight
├── backends.py            # SDK 与模拟机械臂
├── control.py             # 状态机、限速及超时处理
├── protocol.py            # 可替换的串口帧解析器
├── gravity_compensation/  # 独立重力算法、模型、相关库源码与验证
├── limits.example.json    # 关节限制示例
├── requirements.txt       # pyserial
├── requirements-sdk.txt   # SDK 编译/包装需要的 numpy、pybind11
├── scripts/               # 依赖安装、SDK 编译、环境设置和启动
├── tests/                 # 单元测试和伪终端串口测试
└── vendor/ARX_X5/          # 厂商 SDK、来源说明与许可证
```

单臂程序，不启动 ROS、ZMQ 或原项目的硬件服务器。USB2CAN 对应 SocketCAN
接口（例如 `can0`）；外接遥操作器使用另一个串口（例如 `/dev/ttyUSB1`）。
两者不能使用同一设备节点，也不要和其他机械臂控制进程同时占用同一 CAN 总线。

停止采用 **SOFT 零力矩模式**：`set_arm_status(0)`，并持续读取、
打印六个关节的弧度和角度。SOFT 不是驱动器失能，也不是重力补偿，机械臂需要支撑，
否则会受重力下落。`--stop-mode disabled` 在 SDK 后端会在连接前报错，不冒充真正失能。

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

SOFT 和位置模式切换均无硬件确认反馈。SDK 构造函数会启动自己的线程，可能使能电机；
SDK 不提供公开的反馈时间戳、线程关闭、通信 watchdog 或失能确认接口。
因此本程序的超时保护只在 Python 循环正常运行时有效，无法保证进程被强杀、
SDK 卡住、CAN 拔线之后的电机行为。实机阶段应先验证外部急停与断流行为。

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
31 项测试通过，包括独立目录、安装预览、缺包报错和启动脚本检查。
模拟依赖安装已在新的 `.venv` 中实际运行成功；两个 SDK 绑定已用 Python 3.14 / pybind11 3
编译并安装到验证目录，但本机缺少 KDL 运行库，完整 SDK 安装正确报错且未产生 READY 标记。
本机没有 CAN / USB 串口设备，尚未完成 SDK 导入成功验证、实机读角度或运动测试。
请先在 Robot PC 完成 SDK 安装、preflight 和停止状态读角度，再进行低速串口控制测试。
