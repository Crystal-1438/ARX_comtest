# ARX X5 SDK：反馈帧如何对应到电机

更新时间：2026-10-04。

SDK 使用反馈帧中的 ID 信息识别电机，不按反馈到达顺序，也不通过“刚向哪个
电机发送了命令”判断归属。**MT4 用 CAN 帧 ID；MT2 用 CAN ID=0 加数据首字节的低 4 位。**

## 1. 适用版本与证据边界

- 来源：<https://gitee.com/li-bozha0/ARX_X5>
- 固定提交：`c78328785ea23a81d908e1dcc551eca992f2f1e9`
- 本工程核心库：`vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so`
- SHA256：`cb51e1acfccd1e904ca263d45db2035fb33a457ded0b64e5376a864aaf1abeb5`

本文根据这份 Python SDK 的接收回调和电机解码函数静态反汇编整理。
没有构造控制器、连接机械臂或发送 CAN；不将旧版 ROS 库或其他电机配置视为同一实现。

发送方向的计算和打包见 [目标位置到 CAN 数据流](ARX_X5_SDK_DATAFLOW.md)。

## 2. 接收与分发过程

```text
SocketCAN 收到一帧
  → ControllerBase::CanCallback(frame)
  → 依次调用七个电机对象的 CanAnalyze(frame)
  → 每个对象判断是否匹配自身 ID
      ├─ 不匹配：直接返回
      └─ 匹配：解码位置、速度、effort 和错误信息，更新反馈时间
  → 后续反馈交换和控制读取使用该电机对象保存的数据
```

SDK 在初始化时已经确定每个对象的电机类型和 ID，并非根据一帧数据自动识别电机型号。
接收回调将同一帧交给七个对象，由对象自行过滤；七个对象之后，回调还会把帧交给
`ARXJoy::read()`，这不改变下面的电机归属规则。

因此，哪怕 J6 的反馈先到、J1 后到，它们仍会更新各自的反馈对象。
SDK 并不要求七个反馈按固定顺序到达，也不在这里把每帧反馈与某一次发送命令配对。

## 3. MT4：匹配 CAN 帧 ID

MT4 对应 J1、J2、J3。`MotorType4::CanAnalyze()` 的归属判断等价于：

```c
if (frame->can_id != motor_id) {
    return;
}

// 匹配后，继续按本类型的反馈布局解码。
```

| 关节 | 电机类型 | 电机 ID | 普通控制帧 CAN ID | 反馈帧 CAN ID |
| --- | --- | ---: | --- | --- |
| J1 | MT4 | 1 | `0x001` | `0x001` |
| J2 | MT4 | 2 | `0x002` | `0x002` |
| J3 | MT4 | 4 | `0x004` | `0x004` |

MT4 的 `data[0]` 不是电机 ID。ENCOS 类型 1 反馈的首字节布局为：

```text
bit 7..5          bit 4..0
报文类型（3 位）   错误码（5 位）
```

原 SDK 取错误码的方式是：

```c
error = frame->data[0] & 0x1F;
```

例如 `CAN ID=0x002, data[0]=0x20`：归属 J2；按该反馈格式解释为类型 1、错误码 0。
电机归属来自 `0x002`，不是来自 `0x20`。

需要区分协议布局与原实现：**本版本 MT4 的 CanAnalyze 没有先检查首字节高 3 位
是否为类型 1，也没有在此函数内检查 DLC，就开始按固定布局解码。**
因此这里只能说它按 CAN ID 接受该帧，不能说它已完整验证该帧一定是合法的类型 1 反馈。

## 4. MT2：CAN ID 为 0，再检查载荷中的电机 ID

MT2 对应 J4、J5、J6 和夹爪。`MotorType2::CanAnalyze()` 的判断等价于：

```c
if (frame->can_id != 0) {
    return;
}

if ((frame->data[0] & 0x0F) != motor_id) {
    return;
}

// 两项都匹配后才解码反馈。
```

首字节布局：

```text
bit 7..4          bit 3..0
错误码（4 位）     电机 ID（4 位）
```

```c
motor_id_in_payload = frame->data[0] & 0x0F;
error = frame->data[0] >> 4;
```

| 关节 | 电机 ID | 普通控制帧 CAN ID | 反馈帧 CAN ID | `data[0] & 0x0F` |
| --- | ---: | --- | --- | ---: |
| J4 | 5 | `0x005` | `0x000` | 5 |
| J5 | 6 | `0x006` | `0x000` | 6 |
| J6 | 7 | `0x007` | `0x000` | 7 |
| 夹爪 | 8 | `0x008` | `0x000` | 8 |

**控制帧发给 ID 5～8，但反馈 CAN ID 都是 0，靠载荷区分电机。**
这几个 MT2 对象只会接受符合上述两项条件的帧。
若设备配置的反馈 CAN ID 不是 0，即使载荷中 ID 正确，当前 SDK 也会忽略。
MT2 的此解码函数同样没有先检查 DLC。

## 5. 识别示例

下表只演示归属判断，假定其余载荷字节符合相应反馈格式。

| CAN ID | `data[0]` | 本 SDK 的电机归属判断 |
| --- | --- | --- |
| `0x001` | `0x20` | J1，MT4；按类型 1 解释时错误码 0 |
| `0x002` | `0x21` | J2，MT4；按类型 1 解释时错误码 1 |
| `0x004` | `0x20` | J3，MT4 |
| `0x000` | `0x05` | J4，MT2，错误码 0 |
| `0x000` | `0x06` | J5，MT2，错误码 0 |
| `0x000` | `0x16` | J5，MT2，错误码 1 |
| `0x000` | `0x07` | J6，MT2，错误码 0 |
| `0x000` | `0x08` | 夹爪，MT2，错误码 0 |
| `0x006` | `0x06` | 不匹配本机七个电机对象；MT2 要求 CAN ID=0 |
| `0x000` | `0x02` | 不匹配本机七个电机对象；J2 是 MT4，要求 CAN ID=2 |

“不匹配电机对象”不表示整个接收回调绝不处理该帧，因为还有 ARXJoy 等分支。
若两个实体电机的协议归属信息完全相同，以上规则无法再区分它们；它们必须有可区分的 ID 配置。

## 6. 调试或移植时应保留的区别

- CAN 帧 ID 和载荷中的电机 ID 是两个不同字段；MT2 必须同时检查它们。
- MT4 的 `data[0]` 低 5 位是错误码，不能用 MT2 的低 4 位 ID 规则去解释它。
- 发送帧和反馈帧的 CAN ID 不一定相同，MT2 就是本工程中的例子。
- 新实现应明确检查帧类型、有效载荷长度和所支持的反馈报文类型，再进入解码。
  这是移植建议，不是宣称原 SDK 已经实现了这些检查。
- 相同 ID 的数据可能来自错误报文类型；“匹配到对象”与“反馈内容有效”应分开理解。

## 7. 静态证据与复核

已保留的 [sdk_parameters.asm](gravity_compensation/sdk_parameters/reference/sdk_parameters.asm)
包含 MT2 和 MT4 解码函数；参数概览见 [SDK 参数说明](gravity_compensation/sdk_parameters/README.md)。

下列地址仅适用于本文固定哈希的动态库：

| 地址 | 内容 |
| --- | --- |
| `0x127b0` | `ControllerBase::CanCallback()`，遍历七个电机对象后调用 ARXJoy |
| `0x2dae8` | `MotorType2::CanAnalyze()` |
| `0x2db01..0x2db24` | MT2：CAN ID=0；`data[0] & 0x0F` 与自身 ID 比较 |
| `0x2db92..0x2dba4` | MT2：首字节右移 4 位作为错误码 |
| `0x2eb04` | `MotorType4::CanAnalyze()` |
| `0x2eb21..0x2eb2f` | MT4：帧 CAN ID 与自身 ID 比较 |
| `0x2eb9d..0x2ebb1` | MT4：`data[0] & 0x1F` 作为错误码 |

在项目根目录只读复核接收回调，不需要加载 SDK：

```bash
objdump -d -C --no-show-raw-insn \
  --start-address=0x127b0 --stop-address=0x127f1 \
  vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so
```

静态证据确认软件接收规则，不代表实机 ID 配置、反馈频率或总线通信已经通过验证。
