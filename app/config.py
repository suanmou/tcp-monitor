import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
    RELOAD = os.getenv("RELOAD", "True").lower() == "true"
    
    # 监控配置
    # MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 5))  # 监控间隔(秒)
    # FIX_SERVER_IP = os.getenv("FIX_SERVER_IP", "192.168.1.100")  # FIX服务器IP
    # FIX_SERVER_PORT = int(os.getenv("FIX_SERVER_PORT", 443))  # FIX服务器端口
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", 5))  # 监控间隔(秒)
    FIX_SERVER_IP = os.getenv("FIX_SERVER_IP", "127.0.0.1")  # FIX服务器IP
    FIX_SERVER_PORT = int(os.getenv("FIX_SERVER_PORT", 9876))  # FIX服务器端口
    
    # 代理服务器配置(可在.env中配置多个)
    PROXY_SERVERS = {
        "proxy-1": os.getenv("PROXY_1_IP", "10.0.0.10"),
        "proxy-2": os.getenv("PROXY_2_IP", "10.0.0.11"),
        "proxy-3": os.getenv("PROXY_3_IP", "127.0.0.1"),
        "proxy-3": os.getenv("PROXY_3_IP", "10.0.0.12")
    }

settings = Settings()