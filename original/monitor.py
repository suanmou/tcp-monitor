import subprocess
import re
import socket
import time
import platform  # 添加系统检测模块
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class TCPMonitor:
    def __init__(self, fix_server_ip, fix_server_port, proxy_servers):
        self.fix_server_ip = fix_server_ip
        self.fix_server_port = fix_server_port
        self.proxy_servers = proxy_servers
        self.connection_history: Dict[str, List[Tuple[float, float]]] = {}
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
            print(f"无法连接到 {dest_ip}:{dest_port} 以测量RTT")
            return None

    def get_tcp_connections(self, use_ss: bool = True) -> List[dict]:
        """获取所有TCP连接详情并关联到代理服务器（跨平台兼容版）"""
        connections = []
        # 根据操作系统选择不同命令
        os_type = platform.system()
        if os_type == "Windows":
            cmd = ['netstat', '-ano', '-p', 'tcp']
        elif os_type == "Linux":
            if use_ss:
                # 使用ss命令替代netstat
                cmd = ['ss', '-t', '-a', '-n', '-p']  # t:tcp, a:all, n:数字格式, p:进程信息
            else:
                cmd = ['netstat', '-tlnp']  # Linux专用参数
        else:
            raise NotImplementedError(f"不支持的操作系统: {os_type}")

        result = subprocess.run(cmd, capture_output=True, text=True).stdout

        # 解析逻辑适配不同系统输出
        for line in result.splitlines():
            # 统一过滤连接状态
            if 'ESTABLISHED' in line or 'SYN-SENT' in line or 'TIME-WAIT' in line:
                # Windows格式解析
                if os_type == "Windows":
                    parts = re.split(r'\s+', line.strip())
                    if len(parts) >= 5:
                        local_addr = parts[1]
                        remote_addr = parts[2]
                        status = parts[3]
                        pid = parts[4]
                # Linux格式解析
                else:
                    if use_ss:
                        # ss命令输出格式解析
                        parts = re.split(r'\s+', line.strip())
                        if len(parts) >= 6:
                            # ss输出格式: 状态 recv-q send-q 本地地址:端口 远程地址:端口 进程信息
                            status = parts[0]
                            local_addr = parts[3]
                            remote_addr = parts[4]
                            # 提取PID（格式: users:("user",pid=1234,fd=5)）
                            pid_info = parts[5]
                            pid_match = re.search(r'pid=(\d+)', pid_info)
                            pid = pid_match.group(1) if pid_match else None
                    else:
                        # 原netstat解析逻辑
                        parts = re.split(r'\s+', line.strip())
                        if len(parts) >= 7:
                            local_addr = parts[3]
                            remote_addr = parts[4]
                            status = parts[5]
                            # 提取PID（格式: 1234/process_name）
                            pid_info = parts[6]
                            pid = pid_info.split('/')[0] if '/' in pid_info else pid_info

                    # 检查是否是目标FIX服务器
                    if self.fix_server_ip in remote_addr and str(self.fix_server_port) in remote_addr:
                        proxy_name = self.get_proxy_server(local_addr)
                        if not proxy_name:
                            continue

                        # 获取进程名（简单实现）
                        process_name = f'process_{pid}' if pid else 'unknown'

                        # 测量RTT
                        rtt = self.get_rtt(self.fix_server_ip, self.fix_server_port)
                        if rtt:
                            # 保存RTT历史用于统计
                            self.connection_history[proxy_name].append((time.time(), rtt))
                            # 只保留最近100个测量值
                            if len(self.connection_history[proxy_name]) > 100:
                                self.connection_history[proxy_name].pop(0)

                        connections.append({
                            'local_address': local_addr,
                            'remote_address': remote_addr,
                            'status': status,
                            'rtt': rtt,
                            'pid': int(pid) if pid and pid.isdigit() else None,
                            'process_name': process_name,
                            'created_at': datetime.now().isoformat(),
                            'proxy_server': proxy_name
                        })
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

    def aggregate_stats(self, connections: List[dict]) -> Dict[str, dict]:
        """按代理服务器聚合TCP连接统计数据"""
        proxy_stats = {}

        # 初始化每个代理服务器的统计数据
        for proxy_name in self.proxy_servers.keys():
            proxy_stats[proxy_name] = {
                'proxy_server': proxy_name,
                'connection_count': 0,
                'established_count': 0,
                'syn_sent_count': 0,
                'time_wait_count': 0,
                'average_rtt': None,
                'max_rtt': None,
                'min_rtt': None,
                'updated_at': datetime.now().isoformat()
            }

        # 统计连接数据
        for conn in connections:
            proxy_name = conn['proxy_server']
            if proxy_name in proxy_stats:
                proxy_stats[proxy_name]['connection_count'] += 1
                if conn['status'] == 'ESTABLISHED':
                    proxy_stats[proxy_name]['established_count'] += 1
                elif conn['status'] == 'SYN_SENT':
                    proxy_stats[proxy_name]['syn_sent_count'] += 1
                elif conn['status'] == 'TIME_WAIT':
                    proxy_stats[proxy_name]['time_wait_count'] += 1

        # 计算RTT统计数据
        for proxy_name in proxy_stats.keys():
            avg_rtt, max_rtt, min_rtt = self.calculate_rtt_stats(proxy_name)
            proxy_stats[proxy_name]['average_rtt'] = avg_rtt
            proxy_stats[proxy_name]['max_rtt'] = max_rtt
            proxy_stats[proxy_name]['min_rtt'] = min_rtt

        return proxy_stats

    def generate_report(self) -> dict:
        """生成所有代理服务器的TCP连接统计报告"""
        connections = self.get_tcp_connections()
        stats = self.aggregate_stats(connections)

        # 按代理服务器分组连接
        connections_by_proxy = {proxy: [] for proxy in self.proxy_servers.keys()}
        for conn in connections:
            proxy_name = conn['proxy_server']
            if proxy_name in connections_by_proxy:
                connections_by_proxy[proxy_name].append(conn)

        # 构建响应
        proxy_servers = []
        for proxy_name, ip in self.proxy_servers.items():
            proxy_servers.append({
                'proxy_server': proxy_name,
                'ip_address': ip,
                'total_connections': stats[proxy_name]['connection_count'],
                'connection_details': connections_by_proxy[proxy_name],
                'stats': stats[proxy_name]
            })

        return {
            'timestamp': datetime.now().isoformat(),
            'proxy_servers': proxy_servers,
            'summary': stats
        }

    def check_proxy_health(self, rtt_threshold: float, connection_threshold: int) -> List[dict]:
        """检查所有代理服务器的健康状况"""
        connections = self.get_tcp_connections()
        stats = self.aggregate_stats(connections)

        health_results = []

        for proxy_name, ip in self.proxy_servers.items():
            proxy_stat = stats[proxy_name]
            connection_count = proxy_stat['connection_count']
            rtt = proxy_stat['average_rtt']

            # 评估RTT状态
            if rtt is None:
                rtt_status = 'unknown'
            elif rtt < rtt_threshold:
                rtt_status = 'good'
            else:
                rtt_status = 'poor'

            # 评估连接数状态
            if connection_count < connection_threshold:
                connection_status = 'normal'
            else:
                connection_status = 'high'

            # 确定总体状态和健康评分
            if rtt_status == 'poor' or connection_status == 'high':
                status = 'degraded'
                health_score = 60
            elif rtt_status == 'unknown':
                status = 'unhealthy'
                health_score = 30
            else:
                status = 'healthy'
                health_score = 90

            health_results.append({
                'proxy_server': proxy_name,
                'ip_address': ip,
                'status': status,
                'rtt': rtt,
                'rtt_status': rtt_status,
                'connection_count': connection_count,
                'connection_status': connection_status,
                'last_checked': datetime.now().isoformat(),
                'health_score': health_score,
                'details': {
                    'status': status,
                    'message': f'RTT: {rtt}ms, Connections: {connection_count}',
                    'rtt_threshold': rtt_threshold,
                    'connection_threshold': connection_threshold
                }
            })

        return health_results