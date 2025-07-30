import os
import socket  # 新增: 用于DNS查询
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
    RELOAD = os.getenv("RELOAD", "True").lower() == "true"
    
    # 监控配置
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 5))  # 监控间隔(秒)
    FIX_SERVER_IP = os.getenv("FIX_SERVER_IP", "127.0.0.1")  # FIX服务器IP
    FIX_SERVER_PORT = int(os.getenv("FIX_SERVER_PORT", 9876))  # FIX服务器端口
    
    # 代理服务器服务名配置(可在.env中配置多个) - 修改
    PROXY_SERVER_SERVICES = {
        "proxy-1": os.getenv("PROXY_1_SERVICE", "nginx-proxy-1"),
        "proxy-2": os.getenv("PROXY_2_SERVICE", "nginx-proxy-2"),
        "proxy-3": os.getenv("PROXY_3_SERVICE", "nginx-proxy-3")
    }
    
    # 代理服务器IP配置 - 改为动态解析
    PROXY_SERVERS = {}
    
    # 健康检查配置
    HEALTH_CHECK_RTT_THRESHOLD = float(os.getenv("HEALTH_CHECK_RTT_THRESHOLD", 500.0))  # 毫秒
    HEALTH_CHECK_CONNECTION_THRESHOLD = int(os.getenv("HEALTH_CHECK_CONNECTION_THRESHOLD", 100))
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 60))  # 秒
    
    # 新增: 初始化方法
    def __init__(self):
        # 解析服务名到IP
        self.PROXY_SERVERS = self.resolve_proxy_ips()
    
    # 新增: 通过服务名解析代理服务器IP地址的方法
    def resolve_proxy_ips(self):
        """通过服务名解析代理服务器IP地址"""
        proxy_ips = {}
        for proxy_name, service_name in self.PROXY_SERVER_SERVICES.items():
            try:
                # 使用socket进行DNS解析
                ip_address = socket.gethostbyname(service_name)
                proxy_ips[proxy_name] = ip_address
                print(f"解析服务名 {service_name} 到 IP {ip_address}")
            except socket.gaierror:
                # 如果解析失败，使用默认IP
                default_ip = os.getenv(f'PROXY_{proxy_name.split("-")[1]}_IP', f'10.0.0.{10 + int(proxy_name.split("-")[1])}')
                proxy_ips[proxy_name] = default_ip
                print(f"无法解析服务名 {service_name}，使用默认IP {default_ip}")
        return proxy_ips

settings = Settings()