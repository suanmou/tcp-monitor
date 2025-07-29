from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class TCPConnectionStats(BaseModel):
    proxy_server: str
    connection_count: int
    established_count: int
    syn_sent_count: int
    time_wait_count: int
    average_rtt: Optional[float] = None
    max_rtt: Optional[float] = None
    min_rtt: Optional[float] = None
    updated_at: datetime

class ConnectionDetails(BaseModel):
    local_address: str
    remote_address: str
    status: str
    rtt: Optional[float] = None
    pid: Optional[int] = None
    process_name: Optional[str] = None
    created_at: datetime

class ProxyServerStats(BaseModel):
    proxy_server: str
    ip_address: str
    total_connections: int
    connection_details: List[ConnectionDetails]
    stats: TCPConnectionStats

class MonitorResponse(BaseModel):
    timestamp: datetime
    proxy_servers: List[ProxyServerStats]
    summary: Dict[str, TCPConnectionStats]

class ProxyHealthStatus(BaseModel):
    status: Literal["healthy", "unhealthy", "degraded"]
    message: str
    rtt_threshold: float  # 健康RTT阈值(ms)
    connection_threshold: int  # 健康连接数阈值

class ProxyHealth(BaseModel):
    proxy_server: str
    ip_address: str
    status: str
    rtt: Optional[float] = None
    rtt_status: str
    connection_count: int
    connection_status: str
    last_checked: datetime
    health_score: int  # 0-100健康评分
    details: ProxyHealthStatus

class HealthCheckResponse(BaseModel):
    timestamp: datetime
    proxies: List[ProxyHealth]
    overall_status: Literal["healthy", "unhealthy", "degraded"]
    unhealthy_count: int
    degraded_count: int
    healthy_count: int