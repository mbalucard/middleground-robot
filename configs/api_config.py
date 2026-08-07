"""
API配置
    - QywxBotConfig: 企微机器人配置
"""
import os
import dotenv

dotenv.load_dotenv()


class QywxBotConfig:
    """企微机器人配置"""
    URL = os.getenv('QYWX_BOT_URL')
    ID = os.getenv('QYWX_BOT_ID')
    SECRET = os.getenv('QYWX_BOT_SECRET')


if __name__ == '__main__':
    print(QywxBotConfig.URL)
    