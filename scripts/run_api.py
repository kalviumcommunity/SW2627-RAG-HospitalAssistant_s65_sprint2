"""Run the educational FastAPI service locally."""

import sys
import os
from pathlib import Path

import uvicorn

# Allow this file to be executed directly from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )