"""
服务配置
    - DatabaseConfig: 存储用数据库配置
    - ConfigLogFile: 日志文件配置
    - ConfigRedis: Redis配置
    - ConfigAPI: API配置
    - ConfigPostgres: Postgres配置,AI模型长短期记忆存储
    - DemingMySQL: 德明-mysql配置
"""
import os
import dotenv

dotenv.load_dotenv()


class DatabaseConfig:
    """存储用数据库配置"""
    DB_URI = f"postgresql+psycopg://{os.getenv('PS_USER')}:{os.getenv('PS_PASSWORD')}@{os.getenv('PS_HOST')}:{os.getenv('PS_PORT')}/{os.getenv('PS_DATABASE')}"
    MIN_SIZE = 5
    MAX_SIZE = 10


class ConfigLogFile:
    """配置日志文件"""
    LOG_FILE_PATH = "logfile/app.log"
    if not os.path.exists(os.path.dirname(LOG_FILE_PATH)):
        os.makedirs(os.path.dirname(LOG_FILE_PATH))
    MAX_BYTES = 5*1024*1024
    BACKUP_COUNT = 3


class ConfigRedis:
    """配置Redis"""
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = os.getenv("REDIS_PORT", 6379)
    PASSWORD = os.getenv("REDIS_PASSWORD", None)
    DB = os.getenv("REDIS_DB", 0)
    TIMEOUT = os.getenv("SESSION_TIMEOUT", 300)  # 会话过期时间
    TTL = os.getenv("REDIS_TTL", 3600)  # 会话超时时间


class ConfigAPI:
    """配置API"""
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 8001)

class ConfigPostgres:
    """配置Postgres,AI模型长短期记忆存储"""
    DB_URI = f"postgresql://{os.getenv('PS_USER')}:{os.getenv('PS_PASSWORD')}@{os.getenv('PS_HOST')}:{os.getenv('PS_PORT')}/{os.getenv('PS_DATABASE')}"
    MIN_SIZE = 5
    MAX_SIZE = 10


class DemingMySQL:
    """德明-mysql"""
    type = 'MySQL'
    user = os.getenv('DemingMySQLUser')
    password = os.getenv('DemingMySQLPassword')
    host = f"{os.getenv('DemingMySQLHost')}:{os.getenv('DemingMySQLPort')}"
    database = 'salus_deming_c'
    data_source = 'ERP_产线'


if __name__ == "__main__":
    print(ConfigAPI.HOST)