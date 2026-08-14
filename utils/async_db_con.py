"""
异步数据库管理
    - read_sql_language: 读取sql文件内容
    - AsyncCallSQL: 异步数据库管理
        - __init__: 初始化数据库连接
        - get_data: 获取数据
        - implement: 执行语句
        - to_sql: 将数据插入数据库
        - update: 更新数据库
        - close: 关闭数据库连接
"""

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pd.set_option('display.unicode.east_asian_width', True)


def read_sql_language(sql_path: str) -> str:
    """
    读取路径下文件内容
    :param sql_path: 文件路径
    :return: 文本格式命令
    """
    with open(sql_path, 'r', encoding='utf-8') as open_file:
        sql_language = open_file.read()
    return sql_language


class AsyncCallSQL:
    """
    调用数据库 (异步版本)
    支持 MySQL (aiomysql) 和 PostgreSQL (asyncpg)
    """

    def __init__(self, server: object):
        """
        Args:
            server(object): 服务器连接对象，需包含 type, user, password, host, database 属性
        """
        self.sql = server
        self.server_type = getattr(self.sql, 'type', None)

        if self.server_type == 'MySQL':
            driver = 'mysql+aiomysql'
            use_charset = True
        elif self.server_type == 'PostgreSQL':
            driver = 'postgresql+asyncpg'
            use_charset = False
        else:
            raise ValueError(
                f"不支持的数据库类型: {self.server_type}。目前仅支持 'MySQL' 和 'PostgreSQL'")

        # 构建基础连接字符串
        base_url = f"{driver}://{self.sql.user}:{self.sql.password}@{self.sql.host}/{self.sql.database}"

        # 构建查询参数
        params = []
        if use_charset:
            params.append("charset=utf8")

        if params:
            self.conn_parameter = f"{base_url}?{'&'.join(params)}"
        else:
            self.conn_parameter = base_url

        self.engine = create_async_engine(self.conn_parameter, echo=False)

    async def get_data(self, sql_command: str) -> pd.DataFrame:
        """
        根据语句获取数据 (异步)
        Args:
            sql_command(str): 数据库执行命令
        Returns:
            DataFrame: 数据帧
        :return DataFrame
        """
        async with self.engine.connect() as conn:
            # 执行异步查询
            result = await conn.execute(text(sql_command))
            # 将结果转换为 DataFrame
            data = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        return data

    async def implement(self, sql_command: str) -> None:
        """
        根据语句对数据库进行操作 (异步)
        Args:
            sql_command(str): 数据库执行命令
        """
        async with self.engine.begin() as conn:
            await conn.execute(text(sql_command))
        print('Mission accomplished!')

    async def to_sql(self, data_frame: pd.DataFrame, table_name: str, exists: str = 'fail', size: int = None) -> None:
        """
        将DataFrame插入至数据库 (异步)
        注意: pandas 的 to_sql 本身是同步的，这里使用 run_sync 在异步引擎中运行它。
        Args:
            data_frame(pd.DataFrame): 数据帧
            table_name(str): 表名
            exists(str): 如果表存在，则替换，默认: 'fail', 可选: 'replace': 替换, 'append': 追加
            size(int): 每次插入的行数，可选: 每次插入的行数. 默认: None, 
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(
                lambda c: data_frame.to_sql(
                    table_name,
                    c,
                    index=False,
                    if_exists=exists,
                    chunksize=size
                )
            )
        print(f'数据已成功添加至 {self.sql.database}数据库的{table_name}表中！')

    async def update(self, table_name: str, values: dict, where_condition: str, params: dict = None):
        """
        更新数据库中的数据 (异步)。
        Args:
            table_name(str): 需要更新的表名
            values(dict): 一个字典，包含要更新的列和对应的新值
            where_condition(str): 更新条件的SQL字符串, e.g., "id = :id AND name = :name"。请使用命名参数（如 :id）来避免SQL注入。
            params(dict): 一个字典，为WHERE条件中的命名参数提供值, e.g., {"id": 1, "name": "NewName"}。
        """
        if not values:
            print("没有提供要更新的数据。")
            return

        set_clause = ", ".join([f"{key} = :{key}" for key in values.keys()])
        sql_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_condition}"

        all_params = values.copy()
        if params:
            all_params.update(params)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(sql_query), all_params)
            # print(f"表 {table_name} 的数据已成功更新。")
        except Exception as e:
            print(f"更新数据时出错: {e}")
            raise

    async def close(self):
        """关闭数据库连接池"""
        await self.engine.dispose()
