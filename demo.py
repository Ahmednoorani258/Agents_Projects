from setupconfig import config
from agents import Agent, Runner

demoagent = Agent(
    "Teacher_agent_sdk",
    instructions= "u r sdk teacher"
)

user_input = ""

runner = Runner.run_sync(demoagent,user_input,run_config=config)
print(runner.final_output)