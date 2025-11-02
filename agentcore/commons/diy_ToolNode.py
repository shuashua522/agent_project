import asyncio
import inspect
import json
from copy import copy, deepcopy
from dataclasses import replace
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
    get_type_hints,
)

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    ToolCall,
    ToolMessage,
    convert_to_messages,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.config import (
    get_config_list,
    get_executor_for_config,
)
from langchain_core.tools import BaseTool, InjectedToolArg
from langchain_core.tools import tool as create_tool
from langchain_core.tools.base import (
    TOOL_MESSAGE_BLOCK_TYPES,
    get_all_basemodel_annotations,
)
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from typing_extensions import Annotated, get_args, get_origin

from langgraph.errors import GraphBubbleUp
from langgraph.store.base import BaseStore
from langgraph.types import Command, Send
from langgraph.utils.runnable import RunnableCallable

INVALID_TOOL_NAME_ERROR_TEMPLATE = (
    "Error: {requested_tool} is not a valid tool, try one of [{available_tools}]."
)
TOOL_CALL_ERROR_TEMPLATE = "Error: {error}\n Please fix your mistakes."


class SerialToolNode(ToolNode):
    """继承原有ToolNode，重写并发逻辑为串行执行"""

    def __init__(
            self,
            tools: Sequence[Union[BaseTool, Callable]],
            *,
            name: str = "tools",
            tags: Optional[list[str]] = None,
            handle_tool_errors: Union[
                bool, str, Callable[..., str], tuple[type[Exception], ...]
            ] = True,
            messages_key: str = "messages",
    ) -> None:
        # 完全复用父类的初始化逻辑，不做修改
        super().__init__(
            tools=tools,
            name=name,
            tags=tags,
            handle_tool_errors=handle_tool_errors,
            messages_key=messages_key,
        )

    # 重写同步方法：将 executor.map（并行）改为 for 循环（串行）
    def _func(
            self,
            input: Union[list[AnyMessage], dict[str, Any], BaseModel],
            config: RunnableConfig,
            *,
            store: Optional[BaseStore],
    ) -> Any:
        tool_calls, input_type = self._parse_input(input, store)
        config_list = get_config_list(config, len(tool_calls))
        input_types = [input_type] * len(tool_calls)

        # 关键修改：去掉 executor.map，用 for 循环逐个执行 _run_one
        outputs = []
        for call, in_type, cfg in zip(tool_calls, input_types, config_list):
            outputs.append(self._run_one(call, in_type, cfg))

        return self._combine_tool_outputs(outputs, input_type)

    # 重写异步方法：将 asyncio.gather（并行）改为 for 循环 + 逐个 await
    async def _afunc(
            self,
            input: Union[list[AnyMessage], dict[str, Any], BaseModel],
            config: RunnableConfig,
            *,
            store: Optional[BaseStore],
    ) -> Any:
        tool_calls, input_type = self._parse_input(input, store)

        # 关键修改：去掉 asyncio.gather，用 for 循环逐个 await _arun_one
        outputs = []
        for call in tool_calls:
            output = await self._arun_one(call, input_type, config)
            outputs.append(output)

        return self._combine_tool_outputs(outputs, input_type)