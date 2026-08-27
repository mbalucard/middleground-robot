"""
FastAPI 主函数
"""
from fastapi import FastAPI
import uvicorn
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='fastapi_main')

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)