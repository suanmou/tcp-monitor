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