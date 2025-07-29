from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..monitor import TCPMonitor
from ..models import MonitorResponse

router = APIRouter()
monitor = TCPMonitor()

@router.get("/tcp/stats", response_model=MonitorResponse)
async def get_tcp_stats():
    """获取所有代理服务器的TCP连接统计数据"""
    try:
        report = monitor.generate_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/tcp/stats/{proxy_server}")
async def get_proxy_stats(proxy_server: str):
    """获取特定代理服务器的TCP连接统计数据"""
    try:
        report = monitor.generate_report()
        for proxy in report["proxy_servers"]:
            if proxy["proxy_server"] == proxy_server:
                return proxy
        raise HTTPException(status_code=404, detail=f"代理服务器 {proxy_server} 未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/tcp/connections")
async def get_connections():
    """获取所有TCP连接详情"""
    try:
        connections = monitor.get_tcp_connections()
        return {
            "timestamp": datetime.now(),
            "connections_count": len(connections),
            "connections": connections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取连接数据失败: {str(e)}")