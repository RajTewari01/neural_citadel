from fastapi import APIRouter
from infra.server.resource_manager import resource_manager

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
async def get_status():
    return {"status": resource_manager.get_status()}

@router.post("/unload")
async def unload_resources():
    """Kill any running heavy process to free VRAM."""
    await resource_manager.kill_current()
@router.get("/stats")
async def get_stats():
    import psutil
    disk = psutil.disk_usage('/')
    stats = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / (1024**3), 1),
        "disk_total": round(disk.total / (1024**3), 1),
    }
    
    # Try GPU
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            stats["gpu"] = gpus[0].name
            stats["vram_percent"] = (gpus[0].memoryUsed / gpus[0].memoryTotal) * 100
    except:
        pass
        
    return stats
