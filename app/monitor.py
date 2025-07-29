import psutil
import time
import socket
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .models import TCPConnectionStats, ConnectionDetails, ProxyServerStats
from .config import settings
import logging

logger = logging.getLogger(__name__)

class TCPMonitor:
    def __init__(self):
        self.fix_server_ip = settings.FIX_SERVER_IP
        self.fix_server_port = settings.FIX_SERVER_PORT
        self.proxy_servers = settings.PROXY_SERVERS
        self.connection_history: Dict[str, List[Tuple[float, float]]] = {}
        # 初始化每个代理服务器的连接历史
        for proxy in self.proxy_servers.keys():
            self.connection_history[proxy] = []

    def get_proxy_server(self, local_addr: str) -> Optional[str]:
        """根据本地地址判断所属的代理服务器"""
        local_ip = local_addr.split(':')[0]
        for proxy_name, proxy_ip in self.proxy_servers.items():
            if local_ip == proxy_ip:
                return proxy_name
        return None

    def get_rtt(self, dest_ip: str, dest_port: int = 80) -> Optional[float]:
        """测量到目标服务器的RTT(毫秒)"""
        try:
            start_time = time.time()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((dest_ip, dest_port))
                end_time = time.time()
                return round((end_time - start_time) * 1000, 2)
        except (socket.timeout, ConnectionRefusedError, OSError):
            logger.warning(f"无法连接到 {dest_ip}:{dest_port} 以测量RTT")
            return None

    def get_tcp_connections(self) -> List[ConnectionDetails]:
        """获取所有TCP连接详情并关联到代理服务器"""
        connections = []
        for conn in psutil.net_connections(kind='tcp'):
            # 只关注与FIX服务器相关的连接
            if conn.raddr and conn.raddr[0] == self.fix_server_ip and conn.raddr[1] == self.fix_server_port:
                proxy_name = self.get_proxy_server(conn.laddr[0]) if conn.laddr else None
                if not proxy_name:
                    continue

                # 获取进程信息
                pid = conn.pid
                process_name = None
                if pid:
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "unknown"

                # 测量RTT
                rtt = self.get_rtt(self.fix_server_ip, self.fix_server_port)
                if rtt:
                    # 保存RTT历史用于统计
                    self.connection_history[proxy_name].append((time.time(), rtt))
                    # 只保留最近100个测量值
                    if len(self.connection_history[proxy_name]) > 100:
                        self.connection_history[proxy_name].pop(0)

                connections.append(ConnectionDetails(
                    local_address=f"{conn.laddr[0]}:{conn.laddr[1]}",
                    remote_address=f"{conn.raddr[0]}:{conn.raddr[1]}",
                    status=conn.status,
                    rtt=rtt,
                    pid=pid,
                    process_name=process_name,
                    created_at=datetime.now()
                ))
        return connections

    def calculate_rtt_stats(self, proxy_name: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算指定代理服务器的RTT统计数据"""
        if not self.connection_history[proxy_name]:
            return (None, None, None)

        rtt_values = [rtt for _, rtt in self.connection_history[proxy_name] if rtt is not None]
        if not rtt_values:
            return (None, None, None)

        avg_rtt = sum(rtt_values) / len(rtt_values)
        max_rtt = max(rtt_values)
        min_rtt = min(rtt_values)

        return (round(avg_rtt, 2), round(max_rtt, 2), round(min_rtt, 2))

    def aggregate_stats(self, connections: List[ConnectionDetails]) -> Dict[str, TCPConnectionStats]:
        """按代理服务器聚合TCP连接统计数据"""
        proxy_stats = {}

        # 按代理服务器分组连接
        proxy_connections: Dict[str, List[ConnectionDetails]] = {}
        for conn in connections:
            local_ip = conn.local_address.split(':')[0]
            proxy_name = self.get_proxy_server(local_ip)
            if not proxy_name:
                continue
            if proxy_name not in proxy_connections:
                proxy_connections[proxy_name] = []
            proxy_connections[proxy_name].append(conn)

        # 计算每个代理服务器的统计数据
        for proxy_name, conn_list in proxy_connections.items():
            total = len(conn_list)
            established = len([c for c in conn_list if c.status == psutil.CONN_ESTABLISHED])
            syn_sent = len([c for c in conn_list if c.status == psutil.CONN_SYN_SENT])
            time_wait = len([c for c in conn_list if c.status == psutil.CONN_TIME_WAIT])
            avg_rtt, max_rtt, min_rtt = self.calculate_rtt_stats(proxy_name)

            proxy_stats[proxy_name] = TCPConnectionStats(
                proxy_server=proxy_name,
                connection_count=total,
                established_count=established,
                syn_sent_count=syn_sent,
                time_wait_count=time_wait,
                average_rtt=avg_rtt,
                max_rtt=max_rtt,
                min_rtt=min_rtt,
                updated_at=datetime.now()
            )

        return proxy_stats

    def generate_report(self) -> Dict:
        """生成完整的监控报告"""
        connections = self.get_tcp_connections()
        stats = self.aggregate_stats(connections)

        # 按代理服务器组织连接详情
        proxy_details: Dict[str, List[ConnectionDetails]] = {}
        for conn in connections:
            local_ip = conn.local_address.split(':')[0]
            proxy_name = self.get_proxy_server(local_ip)
            if proxy_name not in proxy_details:
                proxy_details[proxy_name] = []
            proxy_details[proxy_name].append(conn)

        # 构建完整报告
        proxy_server_reports = []
        for proxy_name, ip_address in self.proxy_servers.items():
            proxy_connections = proxy_details.get(proxy_name, [])
            proxy_server_reports.append({
                "proxy_server": proxy_name,
                "ip_address": ip_address,
                "total_connections": len(proxy_connections),
                "connection_details": proxy_connections,
                "stats": stats.get(proxy_name, TCPConnectionStats(
                    proxy_server=proxy_name,
                    connection_count=0,
                    established_count=0,
                    syn_sent_count=0,
                    time_wait_count=0,
                    updated_at=datetime.now()
                ))
            })

        return {
            "timestamp": datetime.now(),
            "proxy_servers": proxy_server_reports,
            "summary": stats
        }