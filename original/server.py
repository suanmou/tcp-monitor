import http.server
import socketserver
import json
import urllib.parse
from .monitor import TCPMonitor
from .config import settings
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class TCPMonitorHandler(http.server.BaseHTTPRequestHandler):
    # 初始化监控器
    monitor = TCPMonitor(
        fix_server_ip=settings.FIX_SERVER_IP,
        fix_server_port=settings.FIX_SERVER_PORT,
        proxy_servers=settings.PROXY_SERVERS
    )

    def do_GET(self):
        # 解析URL路径和查询参数
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query_params = dict(urllib.parse.parse_qsl(parsed_path.query))

        # 处理不同的API端点
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            response = {
                'message': 'TCP连接监控系统API',
                'endpoints': [
                    '/api/tcp/stats - 获取所有代理服务器TCP统计数据',
                    '/api/tcp/stats/{proxy_server} - 获取特定代理服务器统计数据',
                    '/api/tcp/connections - 获取所有TCP连接详情',
                    '/api/proxy/health - 获取所有代理服务器的健康状况',
                    '/api/proxy/{proxy_name}/health - 获取特定代理服务器的健康状况'
                ]
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

        elif path == '/api/tcp/stats':
            try:
                report = self.monitor.generate_report()
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(report, ensure_ascii=False).encode())
            except Exception as e:
                self.send_error(500, f'获取统计数据失败: {str(e)}')

        elif path.startswith('/api/tcp/stats/'):
            try:
                proxy_server = path.split('/')[-1]
                report = self.monitor.generate_report()
                for proxy in report['proxy_servers']:
                    if proxy['proxy_server'] == proxy_server:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.end_headers()
                        self.wfile.write(json.dumps(proxy, ensure_ascii=False).encode())
                        return
                self.send_error(404, f'代理服务器 {proxy_server} 未找到')
            except Exception as e:
                self.send_error(500, f'获取统计数据失败: {str(e)}')

        elif path == '/api/tcp/connections':
            try:
                connections = self.monitor.get_tcp_connections()
                response = {
                    'timestamp': datetime.now().isoformat(),
                    'connections_count': len(connections),
                    'connections': connections
                }
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode())
            except Exception as e:
                self.send_error(500, f'获取连接数据失败: {str(e)}')

        elif path == '/api/proxy/health':
            try:
                # 获取查询参数
                rtt_threshold = float(query_params.get('rtt_threshold', 500.0))
                connection_threshold = int(query_params.get('connection_threshold', 100))

                health_results = self.monitor.check_proxy_health(rtt_threshold, connection_threshold)

                # 计算总体状态
                unhealthy_count = sum(1 for h in health_results if h['status'] == 'unhealthy')
                degraded_count = sum(1 for h in health_results if h['status'] == 'degraded')
                healthy_count = sum(1 for h in health_results if h['status'] == 'healthy')

                if unhealthy_count > 0:
                    overall_status = 'unhealthy'
                elif degraded_count > 0:
                    overall_status = 'degraded'
                else:
                    overall_status = 'healthy'

                response = {
                    'timestamp': datetime.now().isoformat(),
                    'proxies': health_results,
                    'overall_status': overall_status,
                    'unhealthy_count': unhealthy_count,
                    'degraded_count': degraded_count,
                    'healthy_count': healthy_count
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_error(500, f'健康检查失败: {str(e)}')

        elif path.startswith('/api/proxy/') and path.endswith('/health'):
            try:
                # 提取代理服务器名称
                parts = path.split('/')
                if len(parts) >= 4:
                    proxy_name = parts[3]
                    # 获取查询参数
                    rtt_threshold = float(query_params.get('rtt_threshold', 500.0))
                    connection_threshold = int(query_params.get('connection_threshold', 100))

                    health_results = self.monitor.check_proxy_health(rtt_threshold, connection_threshold)
                    for result in health_results:
                        if result['proxy_server'] == proxy_name:
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json; charset=utf-8')
                            self.end_headers()
                            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
                            return
                    self.send_error(404, f'代理服务器 {proxy_name} 未找到')
                else:
                    self.send_error(400, '无效的URL路径')
            except Exception as e:
                self.send_error(500, f'健康检查失败: {str(e)}')

        else:
            self.send_error(404, '未找到该端点')
   

def run_server(host='0.0.0.0', port=8000):
    server_address = (host, port)
    httpd = socketserver.TCPServer(server_address, TCPMonitorHandler)
    logger.info(f'Starting server on {host}:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server(host=settings.SERVER_HOST, port=settings.SERVER_PORT)