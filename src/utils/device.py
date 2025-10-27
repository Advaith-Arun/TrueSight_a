import torch
from loguru import logger
from typing import Union, List

def get_device(device_id: int = 0, force_cpu: bool = False) -> torch.device:
    # Gets the Best Available Device (GPU, if available. Else, CPU)

    if force_cpu:
        device = torch.device("cpu")
        logger.info("Forcing CPU usage")
        return device
    
    if torch.cuda.is_available():
        device = torch.device(f"cuda:{device_id}")
        gpu_name = torch.cuda.get_device_name(device_id)
        gpu_memory = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
        
        logger.info(f"✅ Using GPU: {gpu_name}")
        logger.info(f"   GPU Memory: {gpu_memory:.2f} GB")
        logger.info(f"   CUDA Version: {torch.version.cuda}")
        logger.info(f"   PyTorch Version: {torch.__version__}")
        
        # Enable cuDNN autotuner for better performance
        torch.backends.cudnn.benchmark = True
        logger.info("   cuDNN benchmark mode enabled")
        
    else:
        device = torch.device("cpu")
        logger.warning("⚠️  GPU not available, using CPU")
        logger.info("Install PyTorch with CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu124")
    
    return device

def get_gpu_memory_info(device_id: int = 0) -> dict:
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}
    
    allocated = torch.cuda.memory_allocated(device_id) / (1024**3)
    reserved = torch.cuda.memory_reserved(device_id) / (1024**3)
    total = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
    free = total - allocated
    
    return {
        "allocated_gb": round(allocated, 2),
        "reserved_gb": round(reserved, 2),
        "free_gb": round(free, 2),
        "total_gb": round(total, 2),
        "utilization_percent": round((allocated / total) * 100, 2)
    }

def clear_gpu_cache():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        logger.info("GPU cache cleared")

def move_to_device(data: Union[torch.Tensor, List, dict], device: torch.device) -> Union[torch.Tensor, List, dict]:

    if isinstance(data, (list, tuple)):
        return type(data)([move_to_device(x, device) for x in data])
    elif isinstance(data, dict):
        return {k: move_to_device(v, device) for k, v in data.items()}
    elif isinstance(data, torch.Tensor):
        return data.to(device, non_blocking=True)
    else:
        return data

def print_gpu_info():
    if not torch.cuda.is_available():
        print("❌ CUDA not available")
        return
    
    print("\n" + "="*60)
    print("GPU INFORMATION")
    print("="*60)
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Compute Capability: {props.major}.{props.minor}")
        print(f"  Total Memory: {props.total_memory / (1024**3):.2f} GB")
        print(f"  Multi-Processors: {props.multi_processor_count}")
        
        mem_info = get_gpu_memory_info(i)
        print(f"  Memory Allocated: {mem_info['allocated_gb']} GB")
        print(f"  Memory Free: {mem_info['free_gb']} GB")
        print(f"  Utilization: {mem_info['utilization_percent']}%")
    
    print(f"\nCUDA Version: {torch.version.cuda}")
    print(f"cuDNN Version: {torch.backends.cudnn.version()}")
    print(f"cuDNN Enabled: {torch.backends.cudnn.enabled}")
    print("="*60 + "\n")

# Test the setup when imported
if __name__ == "__main__":
    device = get_device()
    print_gpu_info()
