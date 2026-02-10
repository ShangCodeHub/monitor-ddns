# NSSM 服务安装说明

## 简介

使用 NSSM (Non-Sucking Service Manager) 将域名监控脚本安装为 Windows 服务，实现开机自启动。

## 方式一：直接使用 Python 脚本（推荐）

### 前置要求

1. **安装 Python**（如果未安装）
   - 下载地址: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **下载 NSSM**
   - 下载地址: https://nssm.cc/download
   - 或从 GitHub: https://github.com/bmatzelle/nssm/releases
   - 下载后解压，将 `nssm.exe` 复制到 `ipscan` 目录

### 安装步骤

1. **配置监控参数**
   - 编辑 `config.env`，设置监控域名、手机号等参数

2. **安装服务**
   ```bash
   install-service.bat
   ```
   - 脚本会自动检测 Python 和 NSSM
   - 自动安装服务并设置为开机自启
   - 可选择立即启动服务

3. **验证安装**
   ```bash
   sc query DomainMonitor
   ```

### 管理服务

```bash
# 启动服务
net start DomainMonitor

# 停止服务
net stop DomainMonitor

# 查看服务状态
sc query DomainMonitor

# 卸载服务
uninstall-service.bat
```

### 查看日志

- 标准输出: `logs\service_stdout.log`
- 错误输出: `logs\service_stderr.log`

---

## 方式二：打包为 EXE（独立运行）

### 前置要求

1. **安装 PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **下载 NSSM**（同上）

### 打包步骤

1. **打包为 EXE**
   ```bash
   build-exe.bat
   ```
   - 会在 `dist` 目录生成 `DomainMonitor.exe`

2. **复制文件**
   - 将 `dist\DomainMonitor.exe` 复制到目标目录
   - 将 `config.env` 复制到同一目录

3. **安装服务**
   ```bash
   install-service-exe.bat
   ```
   - 使用 EXE 方式安装服务

### 优势

- ✅ 不依赖 Python 环境
- ✅ 单文件部署，方便迁移
- ✅ 适合生产环境

### 注意事项

- EXE 文件较大（约 20-30MB）
- 首次运行可能较慢
- 需要将 `config.env` 放在 EXE 同目录

---

## 服务配置说明

### 服务名称
- 默认: `DomainMonitor`
- 可在安装脚本中修改 `SERVICE_NAME` 变量

### 启动类型
- 自动启动（开机自启）
- 可通过服务管理器修改

### 自动重启
- 服务异常退出后自动重启
- 重启延迟: 10秒
- 节流时间: 1.5秒

### 日志配置
- 标准输出和错误输出分别记录到日志文件
- 日志文件自动创建在 `logs` 目录

---

## 常见问题

### 1. 服务无法启动

**检查项：**
- Python 是否正确安装并添加到 PATH
- 依赖包是否已安装（`pip install -r requirements.txt`）
- `config.env` 是否存在且配置正确
- 查看 `logs\service_stderr.log` 错误日志

### 2. 服务启动后立即停止

**可能原因：**
- Python 脚本有语法错误
- 配置文件路径错误
- 依赖包缺失

**解决方法：**
- 手动运行 `python ipScan.py --monitor` 测试
- 查看错误日志文件

### 3. 服务无法开机自启

**检查项：**
- 服务启动类型是否为"自动"
- 用户账户是否有足够权限
- 检查 Windows 事件查看器

### 4. NSSM 下载地址

- 官网: https://nssm.cc/download
- GitHub: https://github.com/bmatzelle/nssm/releases
- 选择对应系统版本（32位/64位）

---

## 文件说明

- `install-service.bat` - 安装服务（Python脚本方式）
- `install-service-exe.bat` - 安装服务（EXE方式）
- `uninstall-service.bat` - 卸载服务
- `build-exe.bat` - 打包Python脚本为EXE
- `nssm.exe` - NSSM工具（需自行下载）

---

## 快速开始

1. 下载 `nssm.exe` 放到 `ipscan` 目录
2. 配置 `config.env`
3. 运行 `install-service.bat`
4. 完成！

服务会自动开机启动，定时检测域名并发送告警短信。
