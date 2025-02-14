from abc import ABC
from typing import Dict, Any
import aiohttp
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    def __init__(self, model_path: str, config: Dict[str, Any]):
        self.model_path = model_path
        self.config = config
        self.session = None
        self.request_timeout = aiohttp.ClientTimeout(total=30)

    async def initialize(self):
        self.session = aiohttp.ClientSession(timeout=self.request_timeout)
        logger.info(f"Initialized {self.__class__.__name__}")

    async def cleanup(self):
        if self.session:
            await self.session.close()
            logger.info(f"Cleaned up {self.__class__.__name__}")

    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._process_internal(data)
            return self._format_response(result)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return self._format_error(str(e))

    async def _process_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent_type": self.__class__.__name__,
            "timestamp": asyncio.get_event_loop().time(),
            "data": result
        }

    def _format_error(self, error_message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "agent_type": self.__class__.__name__,
            "timestamp": asyncio.get_event_loop().time(),
            "error": error_message
        }