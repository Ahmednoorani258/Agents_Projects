from setupconfig import config
from agents import Agent, Runner

def demofunction():
    return "demo function"

demoagent = Agent(
    name="Teacher_agent_sdk",
    instructions= "u r sdk teacher",
    tools=[demofunction]
)

user_input = ""

runner = Runner.run_sync(demoagent,user_input,run_config=config)
print(runner.final_output)