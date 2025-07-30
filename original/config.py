import os
import socket  # 新增: 用于DNS查询

class Settings:
    def __init__(self):
        # 从环境变量加载配置
        self.SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
        self.SERVER_PORT = int(os.environ.get('SERVER_PORT', 8009))
        self.RELOAD = os.environ.get('RELOAD', 'True').lower() == 'true'

        # 监控配置
        self.MONITOR_INTERVAL = int(os.environ.get('MONITOR_INTERVAL', 5))
        self.FIX_SERVER_IP = os.environ.get('FIX_SERVER_IP', '127.0.0.1')
        self.FIX_SERVER_PORT = int(os.environ.get('FIX_SERVER_PORT', 9876))

        # 代理服务器服务名配置 - 新增
        self.PROXY_SERVER_SERVICES = {
            'proxy-1': os.environ.get('PROXY_1_SERVICE', 'nginx-proxy-1'),
            'proxy-2': os.environ.get('PROXY_2_SERVICE', 'nginx-proxy-2'),
            'proxy-3': os.environ.get('PROXY_3_SERVICE', 'nginx-proxy-3')
        }

        # 通过服务名解析IP - 新增
        self.PROXY_SERVERS = self.resolve_proxy_ips()

        # 加载.env文件（如果存在）
        self._load_dotenv()

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
                default_ip = os.environ.get(f'PROXY_{proxy_name.split("-")[1]}_IP', f'10.0.0.{10 + int(proxy_name.split("-")[1])}')
                proxy_ips[proxy_name] = default_ip
                print(f"无法解析服务名 {service_name}，使用默认IP {default_ip}")
        return proxy_ips

    def _load_dotenv(self):
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
                        # 更新已加载的配置
                        if hasattr(self, key):
                            setattr(self, key, type(getattr(self, key))(value))
            # 重新解析代理IP，因为.env文件可能包含新的服务名配置 - 新增
            self.PROXY_SERVERS = self.resolve_proxy_ips()
        except FileNotFoundError:
            pass

settings = Settings()