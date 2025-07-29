import os

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

        # 代理服务器配置
        self.PROXY_SERVERS = {
            'proxy-1': os.environ.get('PROXY_1_IP', '10.0.0.10'),
            'proxy-2': os.environ.get('PROXY_2_IP', '10.0.0.11'),
            'proxy-3': os.environ.get('PROXY_3_IP', '10.0.0.12')
        }

        # 加载.env文件（如果存在）
        self._load_dotenv()

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
        except FileNotFoundError:
            pass

settings = Settings()