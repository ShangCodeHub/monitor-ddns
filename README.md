# monitor-ddns — 域名监控与 DDNS 工具

**解决动态公网 IP 环境下内网服务外网访问的自动化方案**：定时检测本地运营商分配的公网 IP 变化，自动更新西部数码域名解析（DDNS），将内网服务器映射到固定域名；同时监控域名可用性，异常时通过阿里云短信告警。支持 Windows 下以服务或 EXE 方式运行。

- **仓库地址**：[https://github.com/ShangCodeHub/monitor-ddns](https://github.com/ShangCodeHub/monitor-ddns)

---

## 🎯 使用场景

### 典型场景

你有一台内网服务器（如 NAS、Web 服务、API 服务），需要通过域名从外网访问，但：

- ✅ **运营商提供公网 IP**（但 IP 会动态变化，非固定 IP）
- ✅ **已配置端口转发/NAT**（路由器将公网端口映射到内网服务器）
- ✅ **拥有域名**（在西部数码管理）
- ❌ **IP 变化后域名解析失效**，需要手动更新 DNS 记录

### 解决方案

本工具自动完成：

1. **检测公网 IP 变化**：定时查询当前出口公网 IP
2. **自动更新 DDNS**：IP 变化时调用西部数码 API 更新域名 A 记录
3. **域名可用性监控**：定时检测配置的域名是否可访问（HTTP/Ping）
4. **异常告警**：域名不可访问时发送短信通知

### 工作流程

```
内网服务器 (192.168.1.100:8080)
    ↓ [路由器端口转发]
公网 IP (动态变化: 1.2.3.4 → 5.6.7.8)
    ↓ [本工具自动更新]
域名解析 (nas.example.com → 5.6.7.8)
    ↓ [定时检测]
可用性监控 + 短信告警
```

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **公网 IP 检测** | 定时查询当前运营商分配的公网 IP，检测 IP 是否发生变化 |
| **西部数码 DDNS** | IP 变化时自动调用西部数码 API，更新域名 A 记录，将域名指向新的公网 IP |
| **域名可用性监控** | 定时检测配置的域名/URL 是否可访问（HTTP 请求或 Ping），验证映射是否生效 |
| **短信告警** | 域名不可访问时通过阿里云短信发送告警，支持多号码、防重复发送 |
| **Windows 服务部署** | 支持打包为 EXE 或通过 NSSM 安装为系统服务，实现开机自启、后台运行 |

---

## 环境要求

- **Python** 3.8+
- 可选：Windows 下可打包为 EXE、或通过 NSSM 安装为系统服务

---

## 从配置到启动（完整步骤）

按下面顺序做，即可从零到正常运行。

### 第一步：克隆项目并安装依赖

```bash
git clone https://github.com/ShangCodeHub/monitor-ddns.git
cd monitor-ddns
pip install -r requirements.txt
```

说明：克隆后目录名为 `monitor-ddns`，所有命令都在该目录下执行。

---

### 第二步：准备前置条件（必读）

| 准备项 | 说明 | 哪里获取 |
|--------|------|----------|
| **路由器端口转发** | 把公网端口（如 8080）映射到内网服务器 IP:端口 | 在路由器管理页「端口转发 / 虚拟服务器」里配置 |
| **西部数码域名** | 主域名 + 子域名 A 记录（如 `nas.你的域名.com`） | [西部数码](https://www.west.cn) 购买/管理域名，在解析里添加 A 记录 |
| **西部数码 ApiKey** | 用于调用 API 更新 A 记录 | 西部数码 → 域名管理 → 点进该域名 → 复制 ApiKey，详见 [西部数码DDNS说明.md](./西部数码DDNS说明.md) |
| **阿里云短信** | 用于告警短信 | [阿里云控制台](https://dysms.console.aliyun.com/) 开通短信、申请签名与模板、创建 AccessKey |

---

### 第三步：创建并填写 config.env

1. 在 **`monitor-ddns`** 目录下（与 `ipScan.py` 同级）将 **`config.env.example`** 复制为 **`config.env`**（或新建同名文件）。  
2. 用记事本或 VS Code 打开 **`config.env`**，按下面 **逐项填写**。**阿里云 AccessKey、西部数码 ApiKey 等仅保存在 config.env，勿提交到 Git。**  
3. 填写时不要有多余空格或引号。

#### 3.1 阿里云短信（告警用）

| 配置项 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `SMS_ALIYUN_ENABLED` | 是 | 是否启用短信 | `true` |
| `SMS_ALIYUN_REGION_ID` | 是 | 区域 | `cn-hangzhou` |
| `SMS_ALIYUN_ACCESS_KEY_ID` | 是 | 阿里云 AccessKey ID（勿提交到仓库） | 控制台 RAM 里复制 |
| `SMS_ALIYUN_ACCESS_KEY_SECRET` | 是 | 阿里云 AccessKey Secret（勿提交到仓库） | 同上 |
| `SMS_ALIYUN_SIGN_NAME` | 是 | 短信签名名称 | 在短信控制台申请的签名 |
| `SMS_ALIYUN_TEMPLATE_CODE` | 是 | 短信模板 Code | 如 `SMS_502210001` |
| `SMS_ALIYUN_TEMPLATE_PARAM_NAME` | 否 | 模板里变量名，多为验证码 | `code` |
| `SMS_ALIYUN_PHONE_NUMBERS` | 是 | 接收告警的手机号，多个用英文逗号 | `13800138000,13900139000` |
| `SMS_COOLDOWN_SECONDS` | 否 | 同一内容多少秒内只发一次 | `3600`（1 小时） |

#### 3.2 域名监控（检测哪些地址可访问）

| 配置项 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `MONITOR_ENABLED` | 是 | 是否启用监控 | `true` |
| `MONITOR_INTERVAL` | 是 | 检测间隔（秒） | `600`（10 分钟） |
| `MONITOR_URLS` | 是 | 要检测的完整 URL，多个用英文逗号分隔，必须带 `http://` 或 `https://` | `http://nas.你的域名.com:8080/,http://www.你的域名.com/` |
| `MONITOR_TIMEOUT` | 否 | 单次请求超时（秒） | `10` |
| `MONITOR_CHECK_TYPE` | 否 | 检测方式 | `http` 或 `ping` |

#### 3.3 西部数码 DDNS（IP 变化时自动改解析）

| 配置项 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `WESTCN_DOMAIN` | 是 | 主域名（不带 www 和子域名） | `example.com` |
| `WESTCN_APIKEY` | 是 | 该域名在西部数码的 ApiKey（勿提交到仓库） | 在西部数码域名详情页复制 |
| `WESTCN_HOSTNAMES` | 是 | 要自动更新 A 记录的子域名，多个用英文逗号 | `nas,www,sci-z` |

**对应关系**：`WESTCN_HOSTNAMES=nas,www` 表示会更新 `nas.你的主域名`、`www.你的主域名` 的 A 记录；`MONITOR_URLS` 里填的地址应包含这些主机名（如 `http://nas.example.com:8080/`），这样监控和 DDNS 一致。

#### 3.4 config.env 完整示例（请替换成你自己的值，**密钥勿提交到 Git**）

```env
# ---------- 阿里云短信（密钥仅保存在本地 config.env，勿提交） ----------
SMS_ALIYUN_ENABLED=true
SMS_ALIYUN_REGION_ID=cn-hangzhou
SMS_ALIYUN_ACCESS_KEY_ID=***请填写阿里云AccessKeyId***
SMS_ALIYUN_ACCESS_KEY_SECRET=***请填写阿里云AccessKeySecret***
SMS_ALIYUN_SIGN_NAME=***你的短信签名***
SMS_ALIYUN_TEMPLATE_CODE=SMS_xxx
SMS_ALIYUN_TEMPLATE_PARAM_NAME=code
SMS_ALIYUN_PHONE_NUMBERS=13800138000
SMS_COOLDOWN_SECONDS=3600

# ---------- 域名监控 ----------
MONITOR_ENABLED=true
MONITOR_INTERVAL=600
MONITOR_URLS=http://nas.example.com:8080/,http://www.example.com/
MONITOR_TIMEOUT=10
MONITOR_CHECK_TYPE=ping

# ---------- 西部数码 DDNS（ApiKey 仅保存在本地 config.env，勿提交） ----------
WESTCN_DOMAIN=example.com
WESTCN_APIKEY=***请填写西部数码域名ApiKey***
WESTCN_HOSTNAMES=nas,www
```

保存后确认 **`config.env` 与 `ipScan.py` 在同一目录**（即都在 `monitor-ddns` 下）。**请勿将 `config.env` 提交到 Git**（已通过 `.gitignore` 排除）。

---

### 第四步：启动

在 **`monitor-ddns`** 目录下打开命令行（PowerShell 或 CMD），执行：

```bash
python ipScan.py --monitor
```

- 若正常：程序会一直运行，按间隔检测公网 IP、更新 DDNS、检测 `MONITOR_URLS`，异常时发短信。  
- 若想先测试再长期运行：用 `python ipScan.py --check` 只检测一次；用 `python ipScan.py --phone 你的手机号 --code 1234` 测试短信是否收到。

**如何确认已生效**：

1. 控制台有周期性的检测日志（无报错即配置基本正确）。  
2. 在西部数码解析页查看对应 A 记录，应变为你当前公网 IP（可先运行 `python get_public_ip.py` 看当前公网 IP）。  
3. 用手机或外网访问 `MONITOR_URLS` 里的地址，能打开说明映射和 DDNS 都正常。

---

### 第五步（可选）：安装为 Windows 服务

需要开机自启、后台运行时：

1. 下载 [NSSM](https://nssm.cc/download)，把 `nssm.exe` 放到 `monitor-ddns` 目录。  
2. 以**管理员身份**运行该目录下的 `install-service.bat`，按提示安装并启动服务。  

详见 [NSSM服务安装说明.md](./NSSM服务安装说明.md)。

---

## 配置说明（config.env）参考

配置文件为 **`config.env`**，采用 `KEY=VALUE` 形式，等号两边不要空格，`#` 开头为注释。上面「第三步」已给出逐项说明与示例，此处为简要汇总。

### 阿里云短信

- 多个手机号用英文逗号分隔。  
- `SMS_COOLDOWN_SECONDS`：相同内容在此秒数内只发一次，避免刷屏。

### 域名监控

- **MONITOR_URLS**：必须与你在西部数码配置的子域名对应（如 `nas.example.com` 对应 `WESTCN_HOSTNAMES=nas` + `WESTCN_DOMAIN=example.com`）。  
- **MONITOR_CHECK_TYPE**：`http` 用网页可访问性检测，`ping` 仅检测主机是否可达。

### 西部数码 DDNS

- **WESTCN_HOSTNAMES**：只填主机名，多个用逗号，如 `nas,sci-z,www`。  
- ApiKey 与 A 记录设置详见：[西部数码DDNS说明.md](./西部数码DDNS说明.md)。

---

## 使用方式汇总

| 命令 | 说明 |
|------|------|
| `python ipScan.py --monitor` | 启动域名监控（循环检测 + 告警） |
| `python ipScan.py --check` | 立即检测一次所有配置的 URL |
| `python ipScan.py --phone 138xxx --code 1234` | 发送一条阿里云短信（测试/手动告警） |
| `python get_public_ip.py` | 仅查询当前公网 IP |
| `python westcn_ddns.py` | 仅执行一次西部数码 DDNS 更新（可由监控在 IP 变化时调用） |

---

## Windows 部署

### 方式一：Python 脚本 + NSSM 服务

将监控安装为 Windows 服务，开机自启：

1. 安装依赖：`pip install -r requirements.txt`  
2. 下载 [NSSM](https://nssm.cc/download)，将 `nssm.exe` 放到本目录或 PATH。  
3. 以管理员身份运行：`install-service.bat`  

详细步骤与卸载见：[NSSM服务安装说明.md](./NSSM服务安装说明.md)。

### 方式二：打包为 EXE 后运行或安装为服务

1. 打包：运行 `build-exe.bat`，在 `dist` 目录得到 `DomainMonitor.exe`。  
2. 将 **`config.env`** 与 EXE 放在同一目录。  
3. 直接运行：`DomainMonitor.exe --monitor` 或 `DomainMonitor.exe --check`。  
4. 安装为服务：将 EXE、config.env、nssm.exe、`install-service-exe.bat` 放到同一目录，以管理员运行 `install-service-exe.bat`。  

详见：[EXE使用说明.md](./EXE使用说明.md)。

---

## 项目结构

克隆后目录名为 `monitor-ddns`，结构如下：

```
monitor-ddns/
├── README.md                 # 本说明（GitHub 主页）
├── config.env.example        # 配置项示例（无密钥，可提交）
├── config.env                # 本地配置（需自行创建，勿提交）
├── requirements.txt         # Python 依赖
├── ipScan.py                 # 主程序：短信 + 监控 + 调用 DDNS
├── get_public_ip.py          # 公网 IP 查询
├── westcn_ddns.py            # 西部数码 DDNS 更新
├── 监控功能说明.md            # 域名监控详细说明
├── 西部数码DDNS说明.md        # 西部数码配置与 A 记录说明
├── NSSM服务安装说明.md        # Windows 服务安装步骤
├── EXE使用说明.md             # 打包与 EXE 部署说明
├── install-service.bat        # 使用 Python 脚本安装 NSSM 服务
├── install-service-exe.bat    # 使用 EXE 安装 NSSM 服务
├── uninstall-service.bat      # 卸载服务
├── start-monitor.bat / .sh    # 前台启动监控（测试用）
├── build-exe.bat             # 打包 EXE
└── clean-build.bat           # 清理打包缓存
```

---

## 安全与注意事项

1. **不要提交 `config.env`**：其中包含阿里云 AccessKey、西部数码 ApiKey、手机号等敏感信息，已通过 `.gitignore` 排除；仅使用本地 `config.env`，仓库内只保留无密钥的 `config.env.example`。  
2. **阿里云密钥**：建议使用 RAM 子账号并仅授予短信与必要权限，切勿写入代码或文档。  
3. **西部数码 ApiKey**：仅在控制台为该域名开通，仅保存在本地 config.env，并妥善保管。

---

## 更多文档

- [监控功能说明.md](./监控功能说明.md) — 域名监控配置与检测逻辑  
- [西部数码DDNS说明.md](./西部数码DDNS说明.md) — 西部数码 ApiKey、A 记录与 config.env 对应关系  
- [NSSM服务安装说明.md](./NSSM服务安装说明.md) — Windows 服务安装、启停与卸载  
- [EXE使用说明.md](./EXE使用说明.md) — 打包 EXE 与以服务方式运行 EXE  

---

## License

按项目仓库约定使用。
