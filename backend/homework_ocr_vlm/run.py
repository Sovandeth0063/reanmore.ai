"""Convenience runner — sets PaddlePaddle environment flags before importing anything."""
import os

# Disable oneDNN (mkldnn) — causes ConvertPirAttribute crash on some Windows CPUs
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "False"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ.setdefault("FLAGS_call_stack_level", "2")

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        reload_dirs=["app"] if settings.debug else None,
        log_level="debug" if settings.debug else "info",
    )
