# ARX_comtest — ARX X5 独立 Python 串口控制

这是可单独克隆、运行的工程目录，包含程序、测试、配置示例及厂商 Python SDK 快照，
不依赖原来的 `teleoperation_system_RobotPC` 目录。应用使用 Python 3.10+；
实机 SDK 的 Python ABI、CPU 架构和系统库需另外匹配。

```text
ARX_comtest/
├── app.py                 # 运行入口：monitor / teleop / preflight
├── backends.py            # SDK 与模拟机械臂
├── control.py             # 状态机、限速及超时处理
├── protocol.py            # 可替换的串口帧解析器
├── limits.example.json    # 关节限制示例
├── requirements.txt       # pyserial
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

从工程根目录进入厂商 SDK 目录。已有匹配二进制时只需设置环境；需要重编译时
先准备 CMake、pybind11、编译器及厂商库依赖，然后运行 `bash build.sh`：

```bash
cd vendor/ARX_X5/py/arx_x5_python
# 仅在需要重新编译且依赖已安装时执行：bash build.sh
source setup.sh
cd ../../../..
```

`source setup.sh` 必须在 SDK 目录执行，然后在同一终端启动本程序。
预检查仅导入扩展、查看设备，不实例化机械臂，不发送 CAN 指令：

```bash
python3 app.py --mode preflight --can-port can0 --serial /dev/ttyUSB1
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
python3 app.py --backend sdk --mode monitor --model 2023 --can-port can0
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
python3 app.py --backend sdk --mode teleop --model 2023 \
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
25 项测试通过，包括独立目录默认 SDK 路径检查。当前机器没有 CAN / USB 串口设备，
附带的扩展与本机 Python ABI 不兼容，且缺少 KDL 依赖，未进行真实 SDK
加载成功验证、实机读角度或运动测试。请先在 Robot PC 完成 preflight 和停止状态读角度，
然后再进行低速串口控制测试。
