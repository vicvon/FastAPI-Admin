from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    """
    统一响应模型
    """

    code: int = Field(default=0, description="业务状态码, 0表示成功, 非0表示失败")
    message: str = Field(default="success", description="提示信息")
    data: T | None = Field(default=None, description="数据内容")

    # 允许通过字段名填充
    model_config = ConfigDict(pop_populate_by_name=True)
