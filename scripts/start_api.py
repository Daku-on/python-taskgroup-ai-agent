#!/usr/bin/env python3
"""FastAPI サーバーを起動するスクリプト。"""

import os
import sys
import uvicorn

# プロジェクトのsrcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if __name__ == "__main__":
    # APIサーバーを起動
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )