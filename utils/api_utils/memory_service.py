"""
记忆服务，用来处理记忆相关的业务逻辑
"""


from langgraph.store.postgres import AsyncPostgresStore
from fastapi import HTTPException
from utils.logger_manager import LoggerManager
from utils.date_time import get_current_datetime_with_zone


logger = LoggerManager.get_logger(name='memory_service')


class MemoryService:
    """记忆服务"""

    def __init__(self, store: AsyncPostgresStore):
        self.store = store

    async def list_namespaces(self):
        """
        列出所有命名空间
        Returns:
            list: 命名空间列表
        """
        try:
            namespaces = await self.store.alist_namespaces()
            return namespaces
        except Exception as e:
            logger.error(f"列出所有命名空间失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"列出所有命名空间失败: {e}")

    async def read_long_term_info(self, user_id: str):
        """
        读取指定用户的长期记忆信息详情
        Args:
            user_id: 用户ID
        Returns:
            dict: 长期记忆信息
        """
        try:
            namespace = (user_id, "memories")
            memories = await self.store.asearch(namespace)
            if memories is None:
                raise HTTPException(
                    status_code=500, detail="查询返回无效结果，可能是存储系统错误。")
            logger.info(f"成功获取用户{user_id}的长期记忆，查询到{len(memories)}条记忆记录。")
            return memories
        except Exception as e:
            logger.error(f"获取用户{user_id}的长期记忆失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"获取用户{user_id}的长期记忆失败: {e}")

    async def delete_long_term_info(self, user_id: str, key: str):
        """
        删除长期记忆信息
        Args:
            user_id: 用户ID
            key: 记忆键
        Returns:
            dict: 删除结果
        """
        try:
            namespace = (user_id, "memories")
            await self.store.adelete(namespace, key=key)
            return {"success": True, "message": "成功删除用户长期记忆"}
        except Exception as e:
            logger.error(f"删除用户{user_id}的长期记忆失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"删除用户{user_id}的长期记忆失败: {e}")

    async def get_long_term_info_by_key(self, user_id: str, key: str):
        """
        根据key获取长期记忆信息详情
        Args:
            user_id: 用户ID
            key: 记忆键
        Returns:
            dict: 长期记忆信息
        """
        try:
            namespace = (user_id, "memories")
            memory = await self.store.aget(namespace, key=key)
            return memory
        except Exception as e:
            logger.error(f"获取用户{user_id}的长期记忆失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"获取用户{user_id}的长期记忆失败: {e}")


    async def write_long_term_info(self, user_id: str, key: str, content: str):
        """
        写入长期记忆信息
        Args:
            user_id: 用户ID
            key: 记忆键
            content: 记忆内容
        Returns:
            dict: 写入结果
        """
        try:
            namespace = (user_id, "memories")
            now = get_current_datetime_with_zone()
            memories = await self.get_long_term_info_by_key(user_id, key)
            if memories:
                created_at = memories.value.get('created_at', now)
            else:
                created_at = now

            value = {
                "content": content,
                "encoding": "utf-8",
                "created_at": created_at,
                "modified_at": now,
            }
            await self.store.aput(namespace, key=key, value=value)
            message = "成功更新用户长期记忆" if memories else "成功创建用户长期记忆"
            return {"success": True, "message": message}
        except Exception as e:
            logger.error(f"写入用户{user_id}的长期记忆失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"写入用户{user_id}的长期记忆失败: {e}")


def get_memory_service(state):
    """
    获取记忆服务
    Args:
        state: 应用程序状态
    Returns:
        MemoryService: 记忆服务
    """
    try:
        store = state.store
        return MemoryService(store)
    except Exception as e:
        logger.error(f"获取记忆服务失败: {e}")
        raise RuntimeError(f"获取记忆服务失败: {str(e)}")
