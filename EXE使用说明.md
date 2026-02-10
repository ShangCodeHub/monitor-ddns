# EXE 打包后使用说明

## 打包完成后

打包完成后，会在 `dist` 目录生成 `DomainMonitor.exe` 文件。

## 使用方式

### 方式一：直接运行（测试用）

1. **复制文件**
   - 将 `dist\DomainMonitor.exe` 复制到目标目录
   - 将 `config.env` 复制到同一目录（**必须**）

2. **运行**
   ```bash
   DomainMonitor.exe --monitor
   ```
   或直接双击运行（如果配置了默认启动监控）

3. **测试**
   ```bash
   DomainMonitor.exe --check
   ```
   立即检测一次域名（不持续运行）

---

### 方式二：安装为 Windows 服务（推荐）

#### 步骤 1：准备文件

1. **创建部署目录**（例如：`C:\DomainMonitor`）
   ```bash
   mkdir C:\DomainMonitor
   ```

2. **复制文件**
   - 将 `dist\DomainMonitor.exe` 复制到 `C:\DomainMonitor`
   - 将 `config.env` 复制到 `C:\DomainMonitor`
   - 将 `nssm.exe` 复制到 `C:\DomainMonitor`
   - 将 `install-service-exe.bat` 复制到 `C:\DomainMonitor`

#### 步骤 2：配置

编辑 `C:\DomainMonitor\config.env`，确保配置正确：
```env
# 手机号码（多个用逗号分隔）
SMS_ALIYUN_PHONE_NUMBERS=15114874206,15969144248

# 监控域名（多个用逗号分隔）
MONITOR_URLS=http://nas.ritual-edu.com/,http://sci-z.ritual-edu.com/

# 其他配置...
```

#### 步骤 3：安装服务

1. **以管理员身份运行** `install-service-exe.bat`
   - 右键点击 `install-service-exe.bat`
   - 选择"以管理员身份运行"

2. **按照提示操作**
   - 脚本会自动检测并安装服务
   - 选择是否立即启动服务

3. **验证安装**
   ```bash
   sc query DomainMonitor
   ```

#### 步骤 4：管理服务

**启动服务**
```bash
net start DomainMonitor
```

**停止服务**
```bash
net stop DomainMonitor
```

**查看服务状态**
```bash
sc query DomainMonitor
```

**查看日志**
- 标准输出：`C:\DomainMonitor\logs\service_stdout.log`
- 错误输出：`C:\DomainMonitor\logs\service_stderr.log`

**卸载服务**
```bash
uninstall-service.bat
```

---

## 文件结构

部署后的目录结构应该是：
```
C:\DomainMonitor\
├── DomainMonitor.exe      # 主程序
├── config.env              # 配置文件（必须）
├── nssm.exe                # NSSM工具
├── install-service-exe.bat  # 安装脚本
├── uninstall-service.bat    # 卸载脚本
└── logs\                   # 日志目录（自动创建）
    ├── service_stdout.log  # 标准输出日志
    └── service_stderr.log  # 错误日志
```

---

## 服务特性

- ✅ **开机自启动** - 服务设置为自动启动
- ✅ **自动重启** - 服务异常退出后自动重启（延迟10秒）
- ✅ **日志记录** - 所有输出记录到日志文件
- ✅ **后台运行** - 作为Windows服务在后台运行

---

## 常见问题

### 1. 服务无法启动

**检查项：**
- 确保 `config.env` 文件存在且配置正确
- 检查日志文件：`logs\service_stderr.log`
- 确保以管理员身份安装服务

**解决方法：**
```bash
# 查看错误日志
type logs\service_stderr.log

# 手动测试EXE
DomainMonitor.exe --check
```

### 2. 配置文件找不到

**问题：** EXE 无法找到 `config.env`

**解决：** 确保 `config.env` 与 `DomainMonitor.exe` 在同一目录

### 3. 服务启动后立即停止

**可能原因：**
- 配置文件错误
- 依赖缺失（EXE已包含所有依赖，通常不会发生）

**解决方法：**
- 查看 `logs\service_stderr.log`
- 手动运行 `DomainMonitor.exe --monitor` 测试

### 4. 如何更新服务

1. **停止服务**
   ```bash
   net stop DomainMonitor
   ```

2. **替换文件**
   - 用新的 `DomainMonitor.exe` 替换旧文件
   - 更新 `config.env`（如果需要）

3. **启动服务**
   ```bash
   net start DomainMonitor
   ```

---

## 快速部署脚本

可以创建一个快速部署脚本 `deploy.bat`：

```batch
@echo off
echo Deploying Domain Monitor...
echo.

REM 创建目录
if not exist "C:\DomainMonitor" mkdir "C:\DomainMonitor"

REM 复制文件
copy /Y "dist\DomainMonitor.exe" "C:\DomainMonitor\"
copy /Y "config.env" "C:\DomainMonitor\"
copy /Y "nssm.exe" "C:\DomainMonitor\"
copy /Y "install-service-exe.bat" "C:\DomainMonitor\"
copy /Y "uninstall-service.bat" "C:\DomainMonitor\"

echo.
echo Files copied to C:\DomainMonitor
echo.
echo Next steps:
echo   1. Edit C:\DomainMonitor\config.env
echo   2. Run install-service-exe.bat as Administrator
echo.
pause
```

---

## 验证服务运行

安装服务后，可以通过以下方式验证：

1. **查看服务状态**
   ```bash
   sc query DomainMonitor
   ```

2. **查看日志**
   ```bash
   type C:\DomainMonitor\logs\service_stdout.log
   ```

3. **测试域名检测**
   - 等待10分钟（默认检测间隔）
   - 或手动触发：`DomainMonitor.exe --check`

4. **查看Windows服务管理器**
   - 按 `Win + R`，输入 `services.msc`
   - 找到 `DomainMonitor` 服务
   - 查看状态和启动类型

---

## 注意事项

1. **配置文件必须存在** - `config.env` 必须与 EXE 在同一目录
2. **管理员权限** - 安装/卸载服务需要管理员权限
3. **防火墙** - 如果使用HTTP检测，确保防火墙允许出站连接
4. **日志文件** - 日志文件会不断增长，建议定期清理或设置日志轮转

---

## 完成！

服务安装完成后，监控程序会：
- ✅ 开机自动启动
- ✅ 每10分钟检测一次域名
- ✅ 域名异常时发送短信告警
- ✅ 自动记录日志

无需手动操作，完全自动化运行！
