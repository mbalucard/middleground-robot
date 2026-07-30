"""
代理后端
    - make_backend 用来创建代理后端
"""


from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends import CompositeBackend, StoreBackend

from configs.general_config import FilePath


def make_backend() -> CompositeBackend:
    """
    创建代理后端
    """
    # 文件系统后端
    file_backend = FilesystemBackend(
        root_dir=f"{FilePath.ROOT_PATH}/robot/workspace",
        virtual_mode=True,
        max_file_size_mb=10,
    )
    # 组合后端
    backend = CompositeBackend(
        default=file_backend,
        routes={
            # 长期记忆，使用Postgres store，并按 user_id 隔离
            "/memories/": StoreBackend(
                namespace=lambda rt: (str(rt.context.user_id).replace(".", "_"), "memories"),
            ),
        },
    )
    return backend
