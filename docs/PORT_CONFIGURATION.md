# 端口配置说明

## 问题描述

macOS系统默认会占用端口5000（AirPlay Receiver功能），导致Flask应用无法启动。

## 解决方案

已实现**自动端口选择**功能，系统会自动查找可用端口。

### 端口选择逻辑

1. **优先使用环境变量**: 如果设置了 `FLASK_PORT` 环境变量，使用该端口
2. **自动查找**: 如果没有设置环境变量，从5000开始依次尝试，直到找到可用端口
3. **尝试范围**: 默认尝试5000-5009共10个端口

### 代码实现

```python
def find_free_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"无法找到可用端口（尝试了 {start_port}-{start_port+max_attempts-1}）")
```

## 使用方法

### 方式1: 使用默认端口（自动选择）

```bash
python web_app.py
```

系统会自动查找可用端口（通常是5001，因为5000被macOS占用）。

### 方式2: 指定端口

```bash
export FLASK_PORT=5002
python web_app.py
```

### 方式3: 在启动脚本中指定

```bash
FLASK_PORT=5002 ./start_web_app_python313.sh
```

## 禁用macOS AirPlay Receiver（可选）

如果你想使用端口5000，可以禁用macOS的AirPlay Receiver：

1. 打开 **系统设置** (System Settings)
2. 搜索 **AirPlay Receiver**
3. 关闭 **AirPlay Receiver** 功能

## 当前配置

- **默认端口**: 5000（如果被占用则自动选择5001）
- **当前运行端口**: 5001（因为5000被macOS占用）
- **访问地址**: http://localhost:5001

## 注意事项

1. 每次启动时，系统会显示实际使用的端口
2. 如果所有端口都被占用，会抛出异常
3. 建议使用环境变量固定端口，避免每次启动端口不同

