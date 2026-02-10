# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import threading
import subprocess
import platform
from typing import List, Dict
from datetime import datetime
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

try:
    import requests
except ImportError:
    requests = None

try:
    import requests
except ImportError:
    print("警告: requests 模块未安装，域名监控功能将不可用")
    print("请安装: pip install requests")
    requests = None

# 西部数码 DDNS：ping 失败时自动更新解析，可选依赖
try:
    from westcn_ddns import run_ddns
    _westcn_available = True
except ImportError:
    run_ddns = None
    _westcn_available = False


class Sample:
    # 域名状态记录（避免重复发送短信）
    _url_status: Dict[str, bool] = {}
    # 上次发送短信的记录：{content_hash: timestamp}
    _last_sms_sent: Dict[str, float] = {}
    
    def __init__(self):
        pass
    
    @staticmethod
    def _get_exe_dir():
        """获取EXE或脚本所在目录"""
        if getattr(sys, 'frozen', False):
            # PyInstaller打包的EXE环境
            # sys.executable 是临时目录，需要使用 sys.argv[0] 获取实际EXE路径
            if hasattr(sys, '_MEIPASS'):
                # 这是临时解压目录，需要获取实际EXE路径
                exe_path = sys.argv[0]
                if os.path.isfile(exe_path):
                    return os.path.dirname(os.path.abspath(exe_path))
            # 备用方法：使用 sys.executable 的父目录
            exe_path = sys.executable
            if os.path.isfile(exe_path):
                return os.path.dirname(os.path.abspath(exe_path))
            return os.path.dirname(exe_path)
        else:
            # Python脚本环境
            return os.path.dirname(os.path.abspath(__file__))
    
    @staticmethod
    def load_config(file_path: str = None) -> dict:
        """从配置文件加载配置"""
        config = {}
        
        # 如果没有指定路径，查找config.env
        if file_path is None:
            # 优先使用EXE/脚本所在目录
            base_dir = Sample._get_exe_dir()
            file_path = os.path.join(base_dir, 'config.env')
            
            # 如果EXE/脚本目录没有，尝试当前工作目录（排除临时目录）
            if not os.path.exists(file_path):
                current_dir = os.getcwd()
                # 排除临时目录（PyInstaller解压目录）
                if '_MEI' not in current_dir and 'AppData\\Local\\Temp' not in current_dir:
                    file_path = os.path.join(current_dir, 'config.env')
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 处理数组格式（逗号分隔）
                        if key == 'MONITOR_URLS' and ',' in value:
                            config[key] = [url.strip() for url in value.split(',') if url.strip()]
                        else:
                            config[key] = value
        else:
            print(f"警告: 配置文件不存在: {file_path}")
            print(f"当前工作目录: {os.getcwd()}")
            if getattr(sys, 'frozen', False):
                print(f"EXE所在目录: {os.path.dirname(sys.executable)}")
            else:
                print(f"脚本所在目录: {os.path.dirname(os.path.abspath(__file__))}")
        
        return config
    
    @staticmethod
    def create_client() -> Dysmsapi20170525Client:
        """使用 AccessKey 初始化账号Client，从配置文件读取"""
        cfg = Sample.load_config()
        config = open_api_models.Config(
            access_key_id=cfg.get('SMS_ALIYUN_ACCESS_KEY_ID', ''),
            access_key_secret=cfg.get('SMS_ALIYUN_ACCESS_KEY_SECRET', '')
        )
        config.endpoint = 'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    @staticmethod
    def main(
        args: List[str],
        phone_numbers: str = None,
        template_param: dict = None
    ) -> None:
        """
        发送短信
        :param args: 命令行参数（保留兼容性）
        :param phone_numbers: 手机号码（如果为None，从配置文件读取）
        :param template_param: 模板参数字典（如果为None，使用默认值）
        """
        # 从配置文件读取所有配置
        cfg = Sample.load_config()
        
        # 手机号：参数 > 配置文件 > 默认值
        phone_numbers = phone_numbers or cfg.get('SMS_ALIYUN_PHONE_NUMBERS', '15114874206')
        if not phone_numbers:
            raise ValueError("手机号码不能为空")
        
        # 模板参数
        if template_param is None:
            param_name = cfg.get('SMS_ALIYUN_TEMPLATE_PARAM_NAME', 'code')
            template_param = {param_name: "1234"}
        
        # 签名和模板代码从配置文件读取
        sign_name = cfg.get('SMS_ALIYUN_SIGN_NAME', '上海中域工业互联网研究院')
        template_code = cfg.get('SMS_ALIYUN_TEMPLATE_CODE', 'SMS_502210001')
        
        client = Sample.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name=sign_name,
            template_code=template_code,
            phone_numbers=phone_numbers,
            template_param=json.dumps(template_param, ensure_ascii=False)
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.send_sms_with_options(send_sms_request, runtime)
            print(json.dumps(resp, default=str, indent=2))
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message（Python 3 中异常对象没有 message 属性）
            print(f"错误信息: {str(error)}")
            # 诊断地址（需要检查是否有 data 属性）
            if hasattr(error, 'data') and isinstance(error.data, dict):
                recommend = error.data.get("Recommend")
                if recommend:
                    print(f"诊断地址: {recommend}")
            # 打印完整的异常信息用于调试
            import traceback
            traceback.print_exc()

    @staticmethod
    async def main_async(
        args: List[str],
        phone_numbers: str = None,
        template_param: dict = None
    ) -> None:
        """
        异步发送短信
        :param args: 命令行参数（保留兼容性）
        :param phone_numbers: 手机号码（如果为None，从配置文件读取）
        :param template_param: 模板参数字典（如果为None，使用默认值）
        """
        # 从配置文件读取所有配置
        cfg = Sample.load_config()
        
        # 手机号：参数 > 配置文件 > 默认值
        phone_numbers = phone_numbers or cfg.get('SMS_ALIYUN_PHONE_NUMBERS', '15114874206')
        if not phone_numbers:
            raise ValueError("手机号码不能为空")
        
        # 模板参数
        if template_param is None:
            param_name = cfg.get('SMS_ALIYUN_TEMPLATE_PARAM_NAME', 'code')
            template_param = {param_name: "1234"}
        
        # 签名和模板代码从配置文件读取
        sign_name = cfg.get('SMS_ALIYUN_SIGN_NAME', '上海中域工业互联网研究院')
        template_code = cfg.get('SMS_ALIYUN_TEMPLATE_CODE', 'SMS_502210001')
        
        client = Sample.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name=sign_name,
            template_code=template_code,
            phone_numbers=phone_numbers,
            template_param=json.dumps(template_param, ensure_ascii=False)
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await client.send_sms_with_options_async(send_sms_request, runtime)
            print(json.dumps(resp, default=str, indent=2))
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message（Python 3 中异常对象没有 message 属性）
            print(f"错误信息: {str(error)}")
            # 诊断地址（需要检查是否有 data 属性）
            if hasattr(error, 'data') and isinstance(error.data, dict):
                recommend = error.data.get("Recommend")
                if recommend:
                    print(f"诊断地址: {recommend}")
            # 打印完整的异常信息用于调试
            import traceback
            traceback.print_exc()
    
    # 用于获取公网 IP 的多个服务（轮流尝试，提高可用性）
    _IP_SERVICES = [
        ('https://api.ipify.org', lambda r: r.text.strip()),
        ('https://icanhazip.com', lambda r: r.text.strip()),
        ('https://ip.seeip.org', lambda r: r.text.strip()),
        ('https://ifconfig.me/ip', lambda r: r.text.strip()),
        ('https://ipinfo.io/ip', lambda r: r.text.strip()),
    ]
    
    @staticmethod
    def get_public_ip(timeout: int = 5) -> str:
        """
        动态检测当前出口公网 IP（运营商分配）
        通过请求第三方服务获取访问者公网 IP
        :return: 公网 IP 字符串，失败返回空字符串
        """
        if requests is None:
            return ''
        import re
        for url, parse in Sample._IP_SERVICES:
            try:
                resp = requests.get(url, timeout=timeout)
                if resp.status_code == 200:
                    ip = parse(resp).strip()
                    if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                        return ip
            except Exception:
                continue
        return ''
    
    @staticmethod
    def check_ping(host: str, timeout: int = 10) -> tuple[bool, str, str]:
        """
        使用ping检测主机是否可达
        :param host: 主机名或IP地址（从URL中提取）
        :param timeout: 超时时间（秒）
        :return: (是否可达, 错误信息, IP地址)
        """
        try:
            import re
            # 从URL中提取主机名
            if host.startswith('http://'):
                host = host[7:]
            elif host.startswith('https://'):
                host = host[8:]
            if '/' in host:
                host = host.split('/')[0]
            if ':' in host:
                host = host.split(':')[0]
            
            # 根据操作系统选择ping命令参数
            is_windows = platform.system().lower() == 'windows'
            if is_windows:
                # Windows: ping -n 4 -w timeout*1000 host
                cmd = ['ping', '-n', '4', '-w', str(timeout * 1000), host]
            else:
                # Linux/Mac: ping -c 4 -W timeout host
                cmd = ['ping', '-c', '4', '-W', str(timeout), host]
            
            # 执行ping命令
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 2,
                encoding='utf-8',
                errors='ignore'
            )
            
            # 从ping输出中解析IP地址
            ip_address = ""
            output = result.stdout + result.stderr
            if output:
                # Windows格式: "正在 Ping nas.ritual-edu.com [1.2.3.4] 具有 32 字节的数据:"
                # 或 "Pinging nas.ritual-edu.com [1.2.3.4] with 32 bytes of data:"
                # Linux格式: "PING nas.ritual-edu.com (1.2.3.4) 56(84) bytes of data."
                ip_patterns = [
                    r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]',  # Windows [IP]
                    r'\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\)',  # Linux (IP)
                    r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',      # 通用IP格式
                ]
                for pattern in ip_patterns:
                    match = re.search(pattern, output)
                    if match:
                        ip_address = match.group(1)
                        break
            
            if result.returncode == 0:
                return True, "Ping成功", ip_address
            else:
                return False, f"Ping失败 (返回码: {result.returncode})", ip_address
        except subprocess.TimeoutExpired:
            # 超时时尝试通过DNS解析获取IP
            ip_address = ""
            try:
                import socket
                ip_address = socket.gethostbyname(host)
            except Exception:
                pass
            return False, "Ping超时", ip_address
        except Exception as e:
            return False, f"Ping错误: {str(e)}", ""
    
    @staticmethod
    def check_url(url: str, timeout: int = 10, check_type: str = 'http') -> tuple[bool, str, str]:
        """
        检测URL或主机是否可访问
        :param url: 要检测的URL或主机名
        :param timeout: 超时时间（秒）
        :param check_type: 检测类型 ('http' 或 'ping')
        :return: (是否可访问, 错误信息, IP地址)
        """
        if check_type.lower() == 'ping':
            return Sample.check_ping(url, timeout)
        
        # HTTP检测
        if requests is None:
            return False, "requests模块未安装", ""
        
        try:
            # 从URL中提取主机名用于解析IP
            host = url
            if host.startswith('http://'):
                host = host[7:]
            elif host.startswith('https://'):
                host = host[8:]
            if '/' in host:
                host = host.split('/')[0]
            if ':' in host:
                host = host.split(':')[0]
            
            # 尝试解析IP（通过socket）
            ip_address = ""
            try:
                import socket
                ip_address = socket.gethostbyname(host)
            except Exception:
                pass
            
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return True, "OK", ip_address
            else:
                return False, f"HTTP {response.status_code}", ip_address
        except requests.exceptions.Timeout:
            return False, "连接超时", ""
        except requests.exceptions.ConnectionError:
            return False, "连接失败", ""
        except Exception as e:
            return False, str(e), ""
    
    @staticmethod
    def send_alert_sms(url: str, error_msg: str) -> None:
        """
        发送告警短信（单个域名，保留兼容性）
        :param url: 不可访问的URL
        :param error_msg: 错误信息
        """
        Sample.send_alert_sms_batch([(url, error_msg)])
    
    @staticmethod
    def send_alert_sms_batch(failed_urls: List[tuple]) -> None:
        """
        发送告警短信（批量汇总）
        :param failed_urls: 失败的域名列表，格式: [(url, error_msg), ...]
        """
        if not failed_urls:
            return
        
        cfg = Sample.load_config()
        phone_numbers_str = cfg.get('SMS_ALIYUN_PHONE_NUMBERS', '15114874206')
        sign_name = cfg.get('SMS_ALIYUN_SIGN_NAME', '上海中域工业互联网研究院')
        template_code = cfg.get('SMS_ALIYUN_TEMPLATE_CODE', 'SMS_502210001')
        
        # 解析多个手机号（支持逗号分隔）
        phone_numbers_list = [phone.strip() for phone in phone_numbers_str.split(',') if phone.strip()]
        if not phone_numbers_list:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告: 未配置手机号码")
            return
        
        # 构建汇总告警内容（阿里云模板参数长度限制35字符）
        SMS_CONTENT_MAX_LEN = 35
        
        def _shorten_content(text: str, max_len: int = SMS_CONTENT_MAX_LEN) -> str:
            """截断为指定长度（按字符，中文算1字符）"""
            if len(text) <= max_len:
                return text
            return text[:max_len - 1] + "…"
        
        def _url_to_domain(url: str, short: bool = False) -> str:
            """从URL提取域名，short=True 时只取首段（如 nas.ritual-edu.com -> nas）"""
            u = url.strip()
            for p in ('http://', 'https://'):
                if u.startswith(p):
                    u = u[len(p):]
            if '/' in u:
                u = u.split('/')[0]
            if ':' in u:
                u = u.split(':')[0]
            if short and '.' in u:
                u = u.split('.')[0]
            return u or (url[:15] if not short else url[:8])
        
        # 收集未 ping/检测 成功的域名，拼成短信内容（35字内）
        domains = [_url_to_domain(url) for url, _ in failed_urls]
        if len(failed_urls) == 1:
            content = f"{domains[0]}异常"
        else:
            domains_str = ",".join(domains)
            content = f"{domains_str}异常"
            if len(content) > SMS_CONTENT_MAX_LEN:
                # 超长时用简短域名（首段）
                domains_short = [_url_to_domain(url, short=True) for url, _ in failed_urls]
                domains_str = ",".join(domains_short)
                content = f"{domains_str}异常"
        
        content = _shorten_content(content, SMS_CONTENT_MAX_LEN)
        
        # 生成内容哈希值用于防重复（基于失败域名列表）
        import hashlib
        raw_key = '|'.join(f"{url}" for url, _ in failed_urls)
        content_hash = hashlib.md5(raw_key.encode('utf-8')).hexdigest()
        current_time = time.time()
        
        # 检查是否在防重复时间窗口内（默认1小时）
        sms_cooldown = int(cfg.get('SMS_COOLDOWN_SECONDS', '3600'))  # 默认1小时
        if content_hash in Sample._last_sms_sent:
            last_sent_time = Sample._last_sms_sent[content_hash]
            elapsed = current_time - last_sent_time
            if elapsed < sms_cooldown:
                remaining_minutes = int((sms_cooldown - elapsed) / 60)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 跳过重复短信发送（{remaining_minutes}分钟后可再次发送）")
                return
        
        template_param = {
            "code": "告警",
            "content": content
        }
        
        # 给每个手机号发送短信
        success_count = 0
        fail_count = 0
        for phone in phone_numbers_list:
            try:
                client = Sample.create_client()
                send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
                    sign_name=sign_name,
                    template_code=template_code,
                    phone_numbers=phone,
                    template_param=json.dumps(template_param, ensure_ascii=False)
                )
                runtime = util_models.RuntimeOptions()
                resp = client.send_sms_with_options(send_sms_request, runtime)
                
                # 检查响应：body.Code/code 为 OK 才视为成功（阿里云API成功返回OK）
                body = resp.body if hasattr(resp, 'body') else resp
                body_code = getattr(body, 'code', None) or getattr(body, 'Code', None)
                body_msg = getattr(body, 'message', None) or getattr(body, 'Message', '')
                status_code = getattr(resp, 'status_code', None) or getattr(resp, 'statusCode', None)
                
                if body_code == 'OK':
                    success_count += 1
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 短信发送成功 [手机:{phone}] HTTP:{status_code} Code:OK")
                else:
                    fail_count += 1
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 短信发送失败 [手机:{phone}] HTTP:{status_code} Code:{body_code} Message:{body_msg}")
            except Exception as e:
                fail_count += 1
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 短信发送异常 [手机:{phone}] 错误: {str(e)}")
        
        # 记录发送时间（只有成功发送至少一条才记录）
        if success_count > 0:
            Sample._last_sms_sent[content_hash] = current_time
            # 清理过期的记录（超过24小时的记录）
            expired_keys = [k for k, v in Sample._last_sms_sent.items() if current_time - v > 86400]
            for k in expired_keys:
                del Sample._last_sms_sent[k]
        
        # 输出发送结果
        failed_count = len(failed_urls)
        if success_count > 0:
            if failed_count == 1:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 告警短信已发送到 {success_count} 个手机号: {failed_urls[0][0]}")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 告警短信已发送到 {success_count} 个手机号: 共{failed_count}个域名异常")
        if fail_count > 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告: {fail_count} 个手机号发送失败，请检查上方错误信息（Code/Message）")
    
    @staticmethod
    def send_notification_sms(content: str, cooldown_key: str = None, cooldown_seconds: int = 300) -> None:
        """
        发送单条通知短信（用于 DDNS 成功/失败等），内容截断为 35 字内。
        :param content: 短信内容
        :param cooldown_key: 防重复键，同键在 cooldown_seconds 内只发一次；None 则不校验
        :param cooldown_seconds: 防重复时间（秒）
        """
        cfg = Sample.load_config()
        phone_numbers_str = cfg.get('SMS_ALIYUN_PHONE_NUMBERS', '15114874206')
        sign_name = cfg.get('SMS_ALIYUN_SIGN_NAME', '上海中域工业互联网研究院')
        template_code = cfg.get('SMS_ALIYUN_TEMPLATE_CODE', 'SMS_502210001')
        SMS_CONTENT_MAX_LEN = 35
        content_short = content if len(content) <= SMS_CONTENT_MAX_LEN else content[:SMS_CONTENT_MAX_LEN - 1] + "…"
        phone_numbers_list = [p.strip() for p in phone_numbers_str.split(',') if p.strip()]
        if not phone_numbers_list:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告: 未配置手机号码，跳过通知短信")
            return
        if cooldown_key:
            import hashlib
            key = hashlib.md5(cooldown_key.encode('utf-8')).hexdigest()
            current_time = time.time()
            if key in Sample._last_sms_sent and (current_time - Sample._last_sms_sent[key]) < cooldown_seconds:
                return
        template_param = {"code": "通知", "content": content_short}
        for phone in phone_numbers_list:
            try:
                client = Sample.create_client()
                send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
                    sign_name=sign_name,
                    template_code=template_code,
                    phone_numbers=phone,
                    template_param=json.dumps(template_param, ensure_ascii=False)
                )
                runtime = util_models.RuntimeOptions()
                resp = client.send_sms_with_options(send_sms_request, runtime)
                body = resp.body if hasattr(resp, 'body') else resp
                body_code = getattr(body, 'code', None) or getattr(body, 'Code', None)
                if body_code == 'OK':
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 通知短信已发送 [手机:{phone}] 内容:{content_short}")
                else:
                    body_msg = getattr(body, 'message', None) or getattr(body, 'Message', '')
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 通知短信发送失败 [手机:{phone}] Code:{body_code} Message:{body_msg}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 通知短信异常 [手机:{phone}] 错误: {str(e)}")
        if cooldown_key:
            import hashlib
            key = hashlib.md5(cooldown_key.encode('utf-8')).hexdigest()
            Sample._last_sms_sent[key] = time.time()
    
    @staticmethod
    def monitor_urls() -> None:
        """监控所有配置的URL"""
        cfg = Sample.load_config()
        
        # 检查是否启用监控
        if cfg.get('MONITOR_ENABLED', 'true').lower() != 'true':
            return
        
        urls = cfg.get('MONITOR_URLS', [])
        if isinstance(urls, str):
            # 如果是字符串，转换为列表
            urls = [url.strip() for url in urls.split(',') if url.strip()]
        
        if not urls:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未配置监控URL")
            return
        
        timeout = int(cfg.get('MONITOR_TIMEOUT', '10'))
        check_type = cfg.get('MONITOR_CHECK_TYPE', 'http').lower()  # 'http' 或 'ping'
        
        check_type_name = 'HTTP请求' if check_type == 'http' else 'Ping检测'
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检测 {len(urls)} 个域名... (检测方式: {check_type_name})")
        
        # 收集失败的域名信息
        failed_urls = []
        has_status_change = False
        
        for url in urls:
            is_ok, error_msg, ip_address = Sample.check_url(url, timeout, check_type)
            previous_status = Sample._url_status.get(url, True)
            
            if is_ok:
                if ip_address:
                    print(f"✓ {url} - 正常 (IP: {ip_address})")
                else:
                    print(f"✓ {url} - 正常")
                Sample._url_status[url] = True
            else:
                if ip_address:
                    print(f"✗ {url} - 异常: {error_msg} (IP: {ip_address})")
                else:
                    print(f"✗ {url} - 异常: {error_msg}")
                # 记录失败的域名
                failed_urls.append((url, error_msg))
                # 如果状态从正常变为异常，标记需要发送短信
                if previous_status:
                    has_status_change = True
                Sample._url_status[url] = False
        
        # Ping/检测失败时：先尝试更新西部数码 DDNS（获取当前公网 IP 并修改解析）
        # 只有失败的域名对应的主机名在 WESTCN_HOSTNAMES 中时才更新
        # 只有 DDNS 更新失败时才发送短信，避免重复通知
        if failed_urls and _westcn_available and run_ddns is not None:
            domain = cfg.get('WESTCN_DOMAIN', '').strip()
            apikey = cfg.get('WESTCN_APIKEY', '').strip()
            hostnames_str = cfg.get('WESTCN_HOSTNAMES', '').strip()
            
            if domain and apikey and hostnames_str:
                # 从配置中获取要更新的主机名列表
                configured_hostnames = [h.strip() for h in hostnames_str.split(',') if h.strip()]
                
                # 从失败的 URL 中提取主机名，并检查是否在配置的主机名列表中
                target_hostnames = []
                for url, _ in failed_urls:
                    # 从 URL 中提取主机名（如 http://nas.ritual-edu.com/ -> nas）
                    host = url.strip()
                    if host.startswith('http://'):
                        host = host[7:]
                    elif host.startswith('https://'):
                        host = host[8:]
                    if '/' in host:
                        host = host.split('/')[0]
                    if ':' in host:
                        host = host.split(':')[0]
                    
                    # 提取子域名（如 nas.ritual-edu.com -> nas）
                    if domain and host.endswith('.' + domain):
                        hostname = host[:-len('.' + domain)]
                    elif host == domain:
                        hostname = '@'
                    else:
                        # 如果无法匹配，尝试直接使用主机名（可能是完整域名）
                        hostname = host.split('.')[0] if '.' in host else host
                    
                    # 检查该主机名是否在配置的主机名列表中
                    if hostname in configured_hostnames or (hostname == '@' and '@' in configured_hostnames):
                        if hostname not in target_hostnames:
                            target_hostnames.append(hostname)
                
                # 只有当有匹配的主机名需要更新时才执行 DDNS
                if target_hostnames:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检测失败，正在更新西部数码 DDNS (主机名: {','.join(target_hostnames)})...")
                    ddns_cooldown = int(cfg.get('DDNS_SMS_COOLDOWN', '300'))
                    try:
                        ok, msg = run_ddns(target_hostnames=target_hostnames)
                        if ok:
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DDNS 更新成功: {msg}")
                            # DDNS 成功时不发短信，避免重复通知
                        else:
                            # 只有 DDNS 更新失败时才发送短信
                            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DDNS 更新失败: {msg}")
                            Sample.send_notification_sms("DDNS失败:" + (msg or "")[:27], cooldown_key="ddns_fail", cooldown_seconds=ddns_cooldown)
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DDNS 执行异常: {e}")
                        Sample.send_notification_sms("DDNS异常:" + str(e)[:27], cooldown_key="ddns_fail", cooldown_seconds=ddns_cooldown)
                else:
                    # 失败的域名不在 WESTCN_HOSTNAMES 中，不更新 DDNS
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 失败的域名不在 WESTCN_HOSTNAMES 配置中，跳过 DDNS 更新")
        elif failed_urls and has_status_change:
            # 如果没有配置西部数码 DDNS，检测失败时仍发送告警短信
            Sample.send_alert_sms_batch(failed_urls)
    
    @staticmethod
    def start_monitor() -> None:
        """启动定时监控（持续运行）"""
        # 显示配置文件位置（用于调试）
        base_dir = Sample._get_exe_dir()
        config_path = os.path.join(base_dir, 'config.env')
        
        if not os.path.exists(config_path):
            current_dir = os.getcwd()
            if '_MEI' not in current_dir and 'AppData\\Local\\Temp' not in current_dir:
                config_path = os.path.join(current_dir, 'config.env')
        
        if os.path.exists(config_path):
            print(f"配置文件: {config_path}")
        else:
            print(f"警告: 未找到配置文件")
            print(f"请确保 config.env 与 {base_dir}\\DomainMonitor.exe 在同一目录")
            print(f"或放在当前工作目录: {os.getcwd()}")
        
        cfg = Sample.load_config()
        
        if cfg.get('MONITOR_ENABLED', 'true').lower() != 'true':
            print("监控功能未启用")
            return
        
        interval = int(cfg.get('MONITOR_INTERVAL', '600'))  # 默认10分钟
        
        # 计算监控域名数量
        urls = cfg.get('MONITOR_URLS', [])
        if isinstance(urls, str):
            urls = [url.strip() for url in urls.split(',') if url.strip()]
        url_count = len(urls) if isinstance(urls, list) else 0
        
        # 获取检测方式
        check_type = cfg.get('MONITOR_CHECK_TYPE', 'http').lower()
        check_type_name = 'HTTP请求' if check_type == 'http' else 'Ping检测'
        
        print(f"==========================================")
        print(f"  域名监控服务已启动")
        print(f"==========================================")
        print(f"检测间隔: {interval} 秒 ({interval // 60} 分钟)")
        print(f"检测方式: {check_type_name}")
        print(f"监控域名: {url_count} 个")
        if url_count > 0:
            print(f"监控列表:")
            for url in urls:
                print(f"  - {url}")
        else:
            print(f"⚠ 警告: 未配置监控URL，请检查config.env中的MONITOR_URLS配置")
        print(f"按 Ctrl+C 停止监控")
        print(f"==========================================")
        print()
        
        # 立即执行一次
        Sample.monitor_urls()
        
        # 持续运行监控循环
        try:
            while True:
                time.sleep(interval)
                try:
                    Sample.monitor_urls()
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监控出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 出错后继续运行，不退出
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 监控已停止")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 程序异常退出: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='阿里云短信发送工具')
    parser.add_argument('--phone', type=str, default=None, help='手机号码（默认从config.env读取）')
    parser.add_argument('--code', type=str, default='1234', help='验证码')
    parser.add_argument('--monitor', action='store_true', help='启动域名监控（定时检测）')
    parser.add_argument('--check', action='store_true', help='立即检测一次域名（不启动定时监控）')
    
    args = parser.parse_args()
    
    # 域名监控模式
    if args.monitor:
        Sample.start_monitor()
    elif args.check:
        Sample.monitor_urls()
    elif args.phone or args.code != '1234':
        # 发送短信模式（明确指定了手机号或验证码）
        cfg = Sample.load_config()
        param_name = cfg.get('SMS_ALIYUN_TEMPLATE_PARAM_NAME', 'code')
        Sample.main(
            sys.argv[1:],
            phone_numbers=args.phone,
            template_param={param_name: args.code}
        )
    else:
        # 默认行为：如果启用了监控，则启动监控；否则提示用法
        cfg = Sample.load_config()
        if cfg.get('MONITOR_ENABLED', 'true').lower() == 'true':
            print("未指定参数，自动启动域名监控...")
            print("提示: 使用 --monitor 启动监控，使用 --phone 和 --code 发送短信")
            print()
            Sample.start_monitor()
        else:
            print("用法:")
            print("  启动监控: python ipScan.py --monitor")
            print("  检测一次: python ipScan.py --check")
            print("  发送短信: python ipScan.py --phone 13800138000 --code 1234")