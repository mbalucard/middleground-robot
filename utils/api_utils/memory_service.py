"""
记忆服务，用来处理记忆相关的业务逻辑
"""


from langgraph.store.postgres import AsyncPostgresStore
from fastapi import HTTPException
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name='memory_service')

class MemoryService:
    """记忆服务"""
    def __init__(self, store: AsyncPostgresStore):
        self.store = store

    async def read_long_term_info(self,user_id:str):
        """读取长期记忆信息"""
        try:
            namespace = (user_id,"memories")
            memories = await self.store.asearch(namespace)
            if memories is None:
                raise HTTPException(status_code=500, detail="查询返回无效结果，可能是存储系统错误。")
            logger.info(f"成功获取用户{user_id}的长期记忆，查询到{len(memories)}条记忆记录。")
            store_list = []
            for item in memories:
                store_dict = {}
                store_dict['user_id']=user_id
                store_dict['key'] = item.key
                store_dict['content'] = item.value.get('content','')
                store_dict['created_at'] = item.value.get('created_at','')
                store_dict['modified_at'] = item.value.get('modified_at','')
                store_dict['encoding'] = item.value.get('encoding','')
                store_list.append(store_dict)
            memories_response = {
                "success": True,
                "user_id": user_id,
                "data": store_list,
                "data_type": "long_term_info",
                "total": len(store_list),
                "message": "成功获取用户长期记忆" if store_list else "未找到用户长期记忆",
            }
            return memories_response
        except Exception as e:
            logger.error(f"获取用户{user_id}的长期记忆失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取用户{user_id}的长期记忆失败: {e}")



def get_memory_service(state):
    """获取记忆服务"""
    try:
        store = state.store
        return MemoryService(store)
    except Exception as e:
        logger.error(f"获取记忆服务失败: {e}")
        raise RuntimeError(f"获取记忆服务失败: {str(e)}")
