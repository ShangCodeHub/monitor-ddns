# -*- coding: utf-8 -*-
"""
西部数码（West.cn）动态 DNS 更新
当运营商分配的公网 IP 变化时，自动更新西部数码里的 URL/解析映射（A 记录）。
内置获取当前公网 IP，使用前需在西部数码获取域名 ApiKey。
"""

import os
import sys
import re
from datetime import datetime

# 西部数码 API（官方文档：https://www.west.cn/CustomerCenter/doc/domain_v2.html）
# 解析列表：GET + act=dnsrec.list；修改解析：GET + act=dnsrec.update（hostname 为完整子域名）
WESTCN_DNS_API = "https://api.west.cn/API/v2/domain/dns/"

# 获取公网 IP 的第三方服务（按优先级）
IP_SERVICES = [
    ("https://api.ipify.org?format=text", "text"),
    ("https://icanhazip.com", "text"),
    ("https://ifconfig.me/ip", "text"),
    ("https://ip.seeip.org", "text"),
    ("https://checkip.amazonaws.com", "text"),
    ("https://httpbin.org/ip", "json"),
]


def get_public_ip(timeout=10):
    """
    获取当前公网 IP（运营商分配的出口 IP）
    :param timeout: 每个请求超时时间（秒）
    :return: (ip_string or None, error_message)
    """
    try:
        import requests
    except ImportError:
        return None, "请安装 requests: pip install requests"

    for url, resp_type in IP_SERVICES:
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            text = r.text.strip()
            if resp_type == "text":
                ip = text.split("\n")[0].strip()
            else:
                data = r.json()
                ip = data.get("origin") or data.get("ip")
                if isinstance(ip, list):
                    ip = ip[0] if ip else None
            if ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip, None
        except Exception:
            continue
    return None, "所有 IP 服务均不可用"


def load_ddns_config(config_path=None):
    """从配置文件读取 DDNS 配置"""
    if config_path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base, "config.env")
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    return config


def _parse_api_response(r, raw_text):
    """解析西部数码 API 响应，返回 (code, msg)。"""
    data = {}
    if r.headers.get("content-type", "").startswith("application/json"):
        try:
            data = r.json()
        except Exception:
            pass
    # 兼容 message 在顶层或 body 内
    if isinstance(data.get("message"), dict):
        body = data["message"]
        code = body.get("code", data.get("code"))
        msg = body.get("msg", body.get("message", raw_text[:300]))
    else:
        code = data.get("code", data.get("status", data.get("Code")))
        msg = data.get("message", data.get("msg", data.get("Message", raw_text[:300])))
    return code, msg


def list_westcn_dns(domain, apidomainkey, timeout=15):
    """
    获取域名解析记录列表（用于拿到 record_id 再修改）
    :return: (success, data_or_error)
    """
    try:
        import requests
    except ImportError:
        return False, "请安装 requests: pip install requests"

    params = {
        "act": "dnsrec.list",
        "domain": domain.strip(),
        "apidomainkey": apidomainkey.strip(),
    }
    try:
        r = requests.get(WESTCN_DNS_API, params=params, timeout=timeout)
        raw_text = r.text.strip()
        # 始终尝试按 JSON 解析（西部数码可能未返回 Content-Type: application/json）
        data = {}
        try:
            import json as _json
            data = _json.loads(raw_text)
        except Exception:
            pass
        code = data.get("code", data.get("status"))
        msg = data.get("msg", data.get("message", raw_text[:300]))
        # 西部数码成功返回 code=200 或 0
        if code not in (0, "0", 200, "200"):
            return False, msg if msg else raw_text[:300]
        # 解析记录列表：西部数码在 body.items
        body = data.get("body", data)
        record_list = body.get("items", body.get("list", body.get("record_list", body.get("data", []))))
        if isinstance(record_list, dict):
            record_list = record_list.get("record", record_list.get("list", record_list.get("items", [])))
        return True, record_list if record_list else []
    except requests.exceptions.RequestException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def update_westcn_dns(domain, apidomainkey, hostname, record_value, timeout=15):
    """
    修改西部数码已有 A 记录（先查列表再按 record_id 修改，避免与 CNAME 冲突）。
    若该主机名当前是 CNAME，会提示先到控制台改为 A 记录后再用本脚本。
    """
    try:
        import requests
    except ImportError:
        return False, "请安装 requests: pip install requests"

    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", record_value):
        return False, f"无效 IP: {record_value}"

    domain = domain.strip()
    apidomainkey = apidomainkey.strip()
    hostname = hostname.strip()
    record_value = record_value.strip()

    # 1) 获取解析列表，找到该主机名对应的 A 记录及 record_id
    ok, list_result = list_westcn_dns(domain, apidomainkey, timeout)
    if not ok:
        return False, f"获取解析列表失败: {list_result}"

    record_list = list_result if isinstance(list_result, list) else []
    record_id = None
    for rec in record_list:
        if not isinstance(rec, dict):
            continue
        # 主机名可能字段：hostname / host / name / 主机记录
        h = (rec.get("hostname") or rec.get("host") or rec.get("name") or rec.get("主机记录") or "").strip()
        # 根域名可能返回 @ 或空
        if h == hostname or (hostname == "@" and (h == "" or h == "@")):
            rtype = (rec.get("type") or rec.get("record_type") or rec.get("类型") or "").upper()
            if rtype == "A":
                record_id = rec.get("record_id") or rec.get("id") or rec.get("记录ID")
                if record_id is not None:
                    break
            elif rtype == "CNAME":
                return False, "该主机名当前为 CNAME 记录，请先在西部数码控制台删除 CNAME 或改为 A 记录后，再用本脚本修改 IP。"

    if record_id is None:
        return False, "未找到该主机名的 A 记录，请先在西部数码控制台添加一条 A 记录（可填任意 IP），再用本脚本动态修改。"

    # 2) 调用 v2 修改解析：act=dnsrec.update，hostname 为完整子域名（如 nas.ritual-edu.com）
    full_hostname = domain if (hostname == "@" or hostname == "") else f"{hostname}.{domain}"
    try:
        params = {
            "act": "dnsrec.update",
            "domain": domain,
            "apidomainkey": apidomainkey,
            "hostname": full_hostname,
            "record_value": record_value,
        }
        r = requests.get(WESTCN_DNS_API, params=params, timeout=timeout)
        raw_text = r.text.strip()
        data = {}
        try:
            import json as _json
            data = _json.loads(raw_text)
        except Exception:
            pass
        code = data.get("result", data.get("code"))
        msg = data.get("msg", data.get("message", raw_text[:300]))
        api_confirm = f"HTTP {r.status_code}, result={code}, msg={msg}"
        if code in (0, "0", 200, "200"):
            return True, api_confirm
        if r.status_code != 200:
            return False, f"请求异常: {api_confirm}"
        return False, f"API 未返回成功: {api_confirm}"
    except requests.exceptions.RequestException as e:
        return False, f"请求失败: {e}"
    except Exception as e:
        return False, str(e)


def run_ddns(config_path=None, dry_run=False, target_hostnames=None):
    """
    获取当前公网 IP 并更新西部数码解析。
    配置项（可在 config.env 或环境变量）：
      WESTCN_DOMAIN      主域名，如 ritual-edu.com
      WESTCN_APIKEY      域名 ApiKey
      WESTCN_HOSTNAMES   要更新的子域名，逗号分隔，如 nas,www 或 @（根域名）
    :param target_hostnames: 可选，指定要更新的主机名列表（如 ['nas', 'sci-z']），None 则使用配置文件
    """
    cfg = load_ddns_config(config_path)
    domain = cfg.get("WESTCN_DOMAIN") or os.environ.get("WESTCN_DOMAIN")
    apikey = cfg.get("WESTCN_APIKEY") or os.environ.get("WESTCN_APIKEY")
    
    if not domain or not apikey:
        return False, "未配置 WESTCN_DOMAIN 或 WESTCN_APIKEY（可在 config.env 或环境变量中设置）"

    # 如果指定了目标主机名，使用指定的；否则使用配置文件中的
    if target_hostnames is not None:
        hostnames = [h.strip() for h in target_hostnames if h.strip()]
    else:
        hostnames_str = cfg.get("WESTCN_HOSTNAMES") or os.environ.get("WESTCN_HOSTNAMES", "@")
        hostnames = [h.strip() for h in hostnames_str.split(",") if h.strip()]
    
    if not hostnames:
        return False, "未指定要更新的主机名"

    ip, err = get_public_ip(timeout=10)
    if err:
        return False, f"获取公网 IP 失败: {err}"

    # 打印当前公网IP
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 当前公网 IP: {ip}")

    if dry_run:
        print(f"[DRY-RUN] 将更新域名: {domain}, 主机名: {hostnames}")
        return True, "dry-run ok"

    all_ok = True
    messages = []
    for hostname in hostnames:
        ok, msg = update_westcn_dns(domain, apikey, hostname, ip)
        if ok:
            messages.append(f"{hostname} -> {ip} 成功 ({msg})")
        else:
            all_ok = False
            messages.append(f"{hostname} 失败: {msg}")

    return all_ok, "\n".join(messages)


def main():
    import argparse
    p = argparse.ArgumentParser(description="西部数码动态 DNS 更新（公网 IP 变化时更新解析）")
    p.add_argument("--dry-run", action="store_true", help="只获取 IP 并打印，不请求 API")
    p.add_argument("--config", default=None, help="配置文件路径，默认同目录 config.env")
    args = p.parse_args()

    ok, msg = run_ddns(config_path=args.config, dry_run=args.dry_run)
    if ok:
        print(msg)
        sys.exit(0)
    else:
        print(msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
