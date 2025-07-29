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

@router.get("/proxy/health", response_model=HealthCheckResponse)
async def get_proxy_health(
    rtt_threshold: float = Query(500.0, description="健康RTT阈值(毫秒)"),
    connection_threshold: int = Query(100, description="健康连接数阈值")
):
    """获取所有代理服务器的健康状况"""
    try:
        health_results = monitor.check_proxy_health(rtt_threshold, connection_threshold)
        
        # 计算总体状态
        unhealthy_count = sum(1 for h in health_results if h.status == "unhealthy")
        degraded_count = sum(1 for h in health_results if h.status == "degraded")
        healthy_count = sum(1 for h in health_results if h.status == "healthy")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "timestamp": datetime.now(),
            "proxies": health_results,
            "overall_status": overall_status,
            "unhealthy_count": unhealthy_count,
            "degraded_count": degraded_count,
            "healthy_count": healthy_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.get("/proxy/{proxy_name}/health")
async def get_specific_proxy_health(
    proxy_name: str,
    rtt_threshold: float = Query(500.0, description="健康RTT阈值(毫秒)"),
    connection_threshold: int = Query(100, description="健康连接数阈值")
):
    """获取特定代理服务器的健康状况"""
    try:
        health_results = monitor.check_proxy_health(rtt_threshold, connection_threshold)
        for result in health_results:
            if result.proxy_server == proxy_name:
                return result
        raise HTTPException(status_code=404, detail=f"代理服务器 {proxy_name} 未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")