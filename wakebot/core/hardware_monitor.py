"""
WakeBot Hardware Monitor
Isolated, read-only GPU telemetry using pynvml (Nvidia Management Library).

Completely decoupled from vision logic.
Thread-safe: NVML queries are stateless reads.
"""

from typing import Dict, Any

try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    pynvml = None
    _NVML_AVAILABLE = False


class HardwareMonitor:
    """
    Lightweight GPU telemetry wrapper.
    Initializes NVML once and exposes snapshot() for periodic polling.
    """

    def __init__(self, gpu_index: int = 0):
        self._gpu_index = gpu_index
        self._handle = None
        self._gpu_name = "N/A"
        self._initialized = False

        if _NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self._handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
                self._gpu_name = pynvml.nvmlDeviceGetName(self._handle)
                if isinstance(self._gpu_name, bytes):
                    self._gpu_name = self._gpu_name.decode("utf-8")
                self._initialized = True
            except Exception:
                self._initialized = False

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a dict of current GPU metrics.
        Returns zeroed values if NVML is unavailable.
        """
        if not self._initialized or self._handle is None:
            return {
                "gpu_name": "N/A",
                "gpu_vram_used_mb": 0,
                "gpu_vram_total_mb": 0,
                "gpu_util_percent": 0,
                "gpu_temp_c": 0,
            }

        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self._handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            temp = pynvml.nvmlDeviceGetTemperature(
                self._handle, pynvml.NVML_TEMPERATURE_GPU
            )

            return {
                "gpu_name": self._gpu_name,
                "gpu_vram_used_mb": round(mem_info.used / 1048576),
                "gpu_vram_total_mb": round(mem_info.total / 1048576),
                "gpu_util_percent": util.gpu,
                "gpu_temp_c": temp,
            }
        except Exception:
            return {
                "gpu_name": self._gpu_name,
                "gpu_vram_used_mb": 0,
                "gpu_vram_total_mb": 0,
                "gpu_util_percent": 0,
                "gpu_temp_c": 0,
            }

    def shutdown(self):
        """Clean NVML shutdown."""
        if self._initialized:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
