# 西部数码动态 DNS 更新说明

当运营商分配的公网 IP 变化时，可用本脚本自动更新西部数码（West.cn）上的解析记录，实现“动态 URL 映射”。

## 两个配置在哪里找

### 1. WESTCN_DOMAIN（主域名）

- **是什么**：你在西部数码购买的、要做动态解析的**主域名**，不带 `www` 或子域名。
- **哪里填**：直接写你自己的域名即可。
- **示例**：`ritual-edu.com`、`example.com`。

### 2. WESTCN_APIKEY（域名 ApiKey）

- **是什么**：西部数码给**每个域名**单独配的一串密钥，用来调用“修改解析”的接口。
- **在哪里找**（按步骤）：
  1. 登录 [西部数码官网](https://www.west.cn) → 进入 **管理中心**。
  2. 左侧或顶部进入 **域名管理**。
  3. 在域名列表里 **点击你要做 DDNS 的那个域名**（点域名文字进入详情）。
  4. 在域名详情页右侧上方找到 **【ApiKey】** 或 **【API 密钥】**，点击 **复制**。
  5. 把复制出来的这一串粘贴到 `WESTCN_APIKEY` 里，不要有多余空格。

如果页面上没有看到 ApiKey：
- 看是否有“接口管理”“API”“动态解析”等入口，点进去找“域名 ApiKey”或“DDNS 密钥”。
- 或联系西部数码客服，说明要做“动态解析 / DDNS”，需要该域名的 ApiKey。

---

## A 记录在哪里加（西部数码控制台）

要做 DDNS 的主机名（如 nas、sci-z）必须是 **A 记录**。若当前是 CNAME 或还没有记录，需要先在西部数码里添加/改成 A 记录：

1. 登录 [西部数码](https://www.west.cn) → 进入 **管理中心**。
2. 左侧或顶部进入 **域名管理**。
3. 在列表里 **点击你的主域名**（如 `ritual-edu.com`）进入该域名的管理页。
4. 找到 **域名解析** / **解析设置** / **DNS 解析** 等入口并进入（通常在“解析记录”“解析列表”附近）。
5. 点击 **添加解析** / **新增记录**。
6. 填写：
   - **主机记录**：填子域名，例如 `nas` 或 `sci-z`（不要带域名后缀；根域名填 `@`）。
   - **记录类型**：选 **A**。
   - **记录值**：先随便填一个 IP，如 `1.1.1.1`（之后用 `westcn_ddns.py` 会自动改成你的公网 IP）。
   - **TTL**：默认即可（如 600）。
7. 保存。同样方式为 `sci-z` 再添加一条 A 记录（主机记录填 `sci-z`，类型 A，记录值先填 1.1.1.1）。

若该主机名之前是 **CNAME**：先**删除**这条 CNAME，再按上面步骤**新增**一条 **A** 记录（同一主机名不能同时存在 A 和 CNAME）。

## 在 config.env 里怎么写

在 `config.env` 中增加（或使用环境变量）：

```env
# 西部数码 DDNS（动态解析）
WESTCN_DOMAIN=ritual-edu.com
WESTCN_APIKEY=这里粘贴从西部数码复制的ApiKey
WESTCN_HOSTNAMES=nas,sci-z
```

- **WESTCN_DOMAIN**：上面第 1 条，你的主域名。
- **WESTCN_APIKEY**：上面第 2 条，从西部数码域名详情页复制的 ApiKey。
- **WESTCN_HOSTNAMES**：要更新 A 记录的主机名，多个用英文逗号分隔。  
  - `nas` 表示 `nas.ritual-edu.com`  
  - `@` 表示根域名 `ritual-edu.com`  
  - 例：`nas,sci-z,www` 会更新 nas、sci-z、www 三条 A 记录为当前公网 IP。

## 使用

```bash
# 获取当前公网 IP 并更新西部数码解析
python westcn_ddns.py

# 仅检测 IP 和配置，不请求 API
python westcn_ddns.py --dry-run
```

## 定时执行（IP 变化时自动更新）

- **Windows**：任务计划程序，每隔一段时间（如 10 分钟）执行一次 `python westcn_ddns.py`。
- **Linux/Mac**：cron，例如每 10 分钟：
  ```bash
  */10 * * * * cd /path/to/ipscan && python westcn_ddns.py >> /tmp/westcn_ddns.log 2>&1
  ```

## 说明

- 脚本内置获取当前公网 IP，再调用西部数码接口更新 A 记录。
- 官方 API 文档：<https://www.west.cn/CustomerCenter/doc/domain_v2.html>  
  接口：`act=dnsrec.update`，会更新/覆盖对应主机名的 A 记录。
