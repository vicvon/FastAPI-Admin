from typing import Annotated

from pydantic import BeforeValidator


def coerce_to_str(v: int | str) -> str:
    return str(v)


# SnowflakeId 会将输入(int 或 str)转换为字符串
# 主要用于 Response Schema 中, 确保前端接收到的 ID 是字符串格式, 避免精度丢失
SnowflakeId = Annotated[str, BeforeValidator(coerce_to_str)]
