from setupconfig import config
from agents import Agent, Runner,function_tool,FunctionTool
from typing import Any


# @function_tool
async def demofunction_tool(ctx: Any, input: str) -> str:
    return "demo function"

customtool = FunctionTool(
    name="demo",
    description="demo",
    params_json_schema={
        "type": "object"
    },
    on_invoke_tool=demofunction_tool,
)

demoagent = Agent(
    name="Teacher_agent_sdk",
    instructions= "u r sdk teacher",
    tools=[customtool]
)

user_input = "call a demo tool"

runner = Runner.run_sync(demoagent,user_input,run_config=config)
print(runner.final_output)