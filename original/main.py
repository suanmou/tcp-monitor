import logging
from .server import run_server
from .config import settings
from datetime import datetime
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info(f'Starting: {settings.SERVER_HOST}:{settings.SERVER_PORT}')
    run_server(host=settings.SERVER_HOST, port=settings.SERVER_PORT)