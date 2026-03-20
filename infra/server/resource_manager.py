import asyncio
import logging
from typing import Optional, Dict

logger = logging.getLogger("RESOURCE_MANAGER")

class ResourceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.active_process: Optional[asyncio.subprocess.Process] = None
        self.active_context: str = "None"
        self.lock = asyncio.Lock()
        
    async def request_execution(self, context_name: str, process_coro):
        """
        Request execution. Reuses active process if context matches.
        Otherwise kills current and starts new.
        """
        async with self.lock:
            # 1. Check if same context is already running
            if self.active_process and self.active_process.returncode is None and self.active_context == context_name:
                logger.info(f"Reusing active process for: {context_name}")
                return self.active_process

            # 2. Kill current process if exists
            if self.active_process and self.active_process.returncode is None:
                logger.info(f"Killing active process: {self.active_context} to start {context_name}")
                try:
                    self.active_process.terminate()
                    try:
                        # Wait briefly for graceful exit
                        await asyncio.wait_for(self.active_process.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        logger.warning(f"Force killing {self.active_context}")
                        self.active_process.kill()
                except Exception as e:
                    logger.error(f"Error killing process: {e}")
            
            # 3. Start new process
            logger.info(f"Starting exclusive process: {context_name}")
            try:
                self.active_process = await process_coro
                self.active_context = context_name
                return self.active_process
            except Exception as e:
                logger.error(f"Failed to start {context_name}: {e}")
                raise e

    async def kill_current(self):
        """Manually kill the currently running process."""
        async with self.lock:
            if self.active_process and self.active_process.returncode is None:
                logger.info(f"Manually stopping: {self.active_context}")
                try:
                    self.active_process.terminate()
                    await self.active_process.wait()
                except Exception as e:
                    logger.error(f"Error stopping process: {e}")
                finally:
                    self.active_process = None
                    self.active_context = "None"
                    
    def get_status(self) -> str:
        if self.active_process and self.active_process.returncode is None:
            return f"Running: {self.active_context}"
        return "Idle"

# Global Instance
resource_manager = ResourceManager()
