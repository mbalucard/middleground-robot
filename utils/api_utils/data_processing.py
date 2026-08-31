"""
数据处理工具
"""


def format_long_term_info_key(content: str) -> str:
    """
    格式化长期记忆信息键
    """
    return f"/{content.replace(' ', '_')}.md"



if __name__ == "__main__":
    print(format_long_term_info_key("2026-08-30"))