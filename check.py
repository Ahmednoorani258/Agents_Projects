from __future__ import annotations

import asyncio
import dataclasses
import inspect
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, cast

from openai.types.responses.response_prompt_param import ResponsePromptParam
from typing_extensions import NotRequired, TypeAlias, TypedDict

from .agent_output import AgentOutputSchemaBase
from .guardrail import InputGuardrail, OutputGuardrail
from .handoffs import Handoff
from .items import ItemHelpers
from .logger import logger
from .mcp import MCPUtil
from .model_settings import ModelSettings
from .models.interface import Model
from .prompts import DynamicPromptFunction, Prompt, PromptUtil
from .run_context import RunContextWrapper, TContext
from .tool import FunctionTool, FunctionToolResult, Tool, function_tool
from .util import _transforms
from .util._types import MaybeAwaitable

if TYPE_CHECKING:
    from .lifecycle import AgentHooks
    from .mcp import MCPServer
    from .result import RunResult


@dataclass
class ToolsToFinalOutputResult:
    is_final_output: bool
    """Whether this is the final output. If False, the LLM will run again and receive the tool call
    output.
    """

    final_output: Any | None = None
    """The final output. Can be None if `is_final_output` is False, otherwise must match the
    `output_type` of the agent.
    """


ToolsToFinalOutputFunction: TypeAlias = Callable[
    [RunContextWrapper[TContext], list[FunctionToolResult]],
    MaybeAwaitable[ToolsToFinalOutputResult],
]
"""A function that takes a run context and a list of tool results, and returns a
`ToolsToFinalOutputResult`.
"""


class StopAtTools(TypedDict):
    stop_at_tool_names: list[str]
    """A list of tool names, any of which will stop the agent from running further."""


class MCPConfig(TypedDict):
    """Configuration for MCP servers."""

    convert_schemas_to_strict: NotRequired[bool]
    """If True, we will attempt to convert the MCP schemas to strict-mode schemas. This is a
    best-effort conversion, so some schemas may not be convertible. Defaults to False.
    """


@dataclass
class AgentBase(Generic[TContext]):
    name: str
    handoff_description: str | None = None
    tools: list[Tool] = field(default_factory=list)
    mcp_servers: list[MCPServer] = field(default_factory=list)
    mcp_config: MCPConfig = field(default_factory=lambda: MCPConfig())

    async def get_mcp_tools(self, run_context: RunContextWrapper[TContext]) -> list[Tool]:
        """Fetches the available tools from the MCP servers."""
        convert_schemas_to_strict = self.mcp_config.get("convert_schemas_to_strict", False)
        return await MCPUtil.get_all_function_tools(
            self.mcp_servers, convert_schemas_to_strict, run_context, self
        )

    async def get_all_tools(self, run_context: RunContextWrapper[Any]) -> list[Tool]:
        """All agent tools, including MCP tools and function tools."""
        mcp_tools = await self.get_mcp_tools(run_context)

        async def _check_tool_enabled(tool: Tool) -> bool:
            if not isinstance(tool, FunctionTool):
                return True

            attr = tool.is_enabled
            if isinstance(attr, bool):
                return attr
            res = attr(run_context, self)
            if inspect.isawaitable(res):
                return bool(await res)
            return bool(res)

        results = await asyncio.gather(*(_check_tool_enabled(t) for t in self.tools))
        enabled: list[Tool] = [t for t, ok in zip(self.tools, results) if ok]
        return [*mcp_tools, *enabled]


@dataclass
class Agent(AgentBase, Generic[TContext]):
    instructions: (str| Callable[[RunContextWrapper[TContext], Agent[TContext]],MaybeAwaitable[str],]| None ) = None

    prompt: Prompt | DynamicPromptFunction | None = None
   
    handoffs: list[Agent[Any] | Handoff[TContext, Any]] = field(default_factory=list)
   
    model: str | Model | None = None
   
    model_settings: ModelSettings = field(default_factory=ModelSettings)
   
    input_guardrails: list[InputGuardrail[TContext]] = field(default_factory=list)
   
    output_guardrails: list[OutputGuardrail[TContext]] = field(default_factory=list)
   
    output_type: type[Any] | AgentOutputSchemaBase | None = None
   
    hooks: AgentHooks[TContext] | None = None
   
    tool_use_behavior: (
        Literal["run_llm_again", "stop_on_first_tool"] | StopAtTools | ToolsToFinalOutputFunction
    ) = "run_llm_again"

    reset_tool_choice: bool = True

    def clone(self, **kwargs: Any) -> Agent[TContext]:
        
        return dataclasses.replace(self, **kwargs)

    def as_tool(
        self,
        tool_name: str | None,
        tool_description: str | None,
        custom_output_extractor: Callable[[RunResult], Awaitable[str]] | None = None,
    ) -> Tool:
        """Transform this agent into a tool, callable by other agents.

        This is different from handoffs in two ways:
        1. In handoffs, the new agent receives the conversation history. In this tool, the new agent
           receives generated input.
        2. In handoffs, the new agent takes over the conversation. In this tool, the new agent is
           called as a tool, and the conversation is continued by the original agent.

        Args:
            tool_name: The name of the tool. If not provided, the agent's name will be used.
            tool_description: The description of the tool, which should indicate what it does and
                when to use it.
            custom_output_extractor: A function that extracts the output from the agent. If not
                provided, the last message from the agent will be used.
        """

        @function_tool(
            name_override=tool_name or _transforms.transform_string_function_style(self.name),
            description_override=tool_description or "",
        )
        async def run_agent(context: RunContextWrapper, input: str) -> str:
            from .run import Runner

            output = await Runner.run(
                starting_agent=self,
                input=input,
                context=context.context,
            )
            if custom_output_extractor:
                return await custom_output_extractor(output)

            return ItemHelpers.text_message_outputs(output.new_items)

        return run_agent

    async def get_system_prompt(self, run_context: RunContextWrapper[TContext]) -> str | None:
        """Get the system prompt for the agent."""
        if isinstance(self.instructions, str):
            return self.instructions
        elif callable(self.instructions):
            if inspect.iscoroutinefunction(self.instructions):
                return await cast(Awaitable[str], self.instructions(run_context, self))
            else:
                return cast(str, self.instructions(run_context, self))
        elif self.instructions is not None:
            logger.error(f"Instructions must be a string or a function, got {self.instructions}")

        return None

    async def get_prompt(
        self, run_context: RunContextWrapper[TContext]
    ) -> ResponsePromptParam | None:
        """Get the prompt for the agent."""
        return await PromptUtil.to_model_input(self.prompt, run_context, self)

    async def get_mcp_tools(self, run_context: RunContextWrapper[TContext]) -> list[Tool]:
        """Fetches the available tools from the MCP servers."""
        convert_schemas_to_strict = self.mcp_config.get("convert_schemas_to_strict", False)
        return await MCPUtil.get_all_function_tools(
            self.mcp_servers, convert_schemas_to_strict, run_context, self
        )

    async def get_all_tools(self, run_context: RunContextWrapper[Any]) -> list[Tool]:
        """All agent tools, including MCP tools and function tools."""
        mcp_tools = await self.get_mcp_tools(run_context)

        async def _check_tool_enabled(tool: Tool) -> bool:
            if not isinstance(tool, FunctionTool):
                return True

            attr = tool.is_enabled
            if isinstance(attr, bool):
                return attr
            res = attr(run_context, self)
            if inspect.isawaitable(res):
                return bool(await res)
            return bool(res)

        results = await asyncio.gather(*(_check_tool_enabled(t) for t in self.tools))
        enabled: list[Tool] = [t for t, ok in zip(self.tools, results) if ok]
        return [*mcp_tools, *enabled]
