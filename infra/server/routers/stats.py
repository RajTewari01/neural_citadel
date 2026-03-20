import psutil
import shutil
import platform
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

# Try importing GPU libraries
try:
    import GPUtil
except ImportError:
    GPUtil = None

router = APIRouter(prefix="/system", tags=["System Stats"])

class GpuStats(BaseModel):
    id: int
    name: str
    load: float
    memory_used: float
    memory_total: float
    temperature: float

class SystemStats(BaseModel):
    # CPU
    cpu_percent: float
    cpu_cores: int
    cpu_freq: float
    
    # RAM
    memory_percent: float
    memory_used: float
    memory_total: float
    
    # Disk
    disk_percent: float
    disk_used: float
    disk_total: float
    
    # GPU
    gpus: List[GpuStats]
    
    # OS
    os_name: str
    uptime: int # seconds

@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    # CPU
    cpu_p = psutil.cpu_percent(interval=None)
    cpu_cores = psutil.cpu_count(logical=True)
    try:
        cpu_freq = psutil.cpu_freq().current
    except:
        cpu_freq = 0.0
    
    # RAM
    mem = psutil.virtual_memory()
    
    # Disk (Usage of drive where server runs)
    try:
        disk = shutil.disk_usage(".")
        d_percent = (disk.used / disk.total) * 100
        d_used = disk.used / (1024**3) # GB
        d_total = disk.total / (1024**3) # GB
    except:
        d_percent = 0.0
        d_used = 0.0
        d_total = 0.0

    # GPU
    gpu_list = []
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_list.append(GpuStats(
                    id=gpu.id,
                    name=gpu.name,
                    load=gpu.load * 100,
                    memory_used=gpu.memoryUsed,
                    memory_total=gpu.memoryTotal,
                    temperature=gpu.temperature
                ))
        except:
            pass
            
    # Platform
    os_name = f"{platform.system()} {platform.release()}"
    uptime = int(psutil.boot_time())

    return SystemStats(
        cpu_percent=cpu_p,
        cpu_cores=cpu_cores,
        cpu_freq=cpu_freq,
        
        memory_percent=mem.percent,
        memory_used=mem.used / (1024**3),
        memory_total=mem.total / (1024**3),
        
        disk_percent=d_percent,
        disk_used=d_used,
        disk_total=d_total,
        
        gpus=gpu_list,
        
        os_name=os_name,
        uptime=uptime
    )
