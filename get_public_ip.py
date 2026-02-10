# -*- coding: utf-8 -*-
"""
动态检测当前公网 IP（运营商分配的出口 IP）
通过请求第三方服务获取本机出口 IP，支持多个备用源。
"""

import sys
import re

# 国内可用的 IP 查询服务（按优先级）
IP_SERVICES = [
    ("https://api.ipify.org?format=text", "text"),
    ("https://icanhazip.com", "text"),
    ("https://ifconfig.me/ip", "text"),
    ("https://ip.seeip.org", "text"),
    ("https://checkip.amazonaws.com", "text"),
    ("https://httpbin.org/ip", "json"),  # {"origin": "x.x.x.x"}
]


def get_public_ip(timeout=10):
    """
    获取当前公网 IP
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
                # 纯文本，取第一行并去除空白
                ip = text.split("\n")[0].strip()
            else:
                # json
                data = r.json()
                ip = data.get("origin") or data.get("ip")
                if isinstance(ip, list):
                    ip = ip[0] if ip else None
            if ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip, None
        except Exception as e:
            continue

    return None, "所有 IP 服务均不可用"


def main():
    ip, err = get_public_ip()
    if err:
        print(f"获取失败: {err}", file=sys.stderr)
        sys.exit(1)
    print(ip)


if __name__ == "__main__":
    main()
