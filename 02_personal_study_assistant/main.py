from setupconfig import config
from agents_file import scheduler_agent, research_agent, summarizer_agent
from agents import Runner


user_input = input("Please enter your study topics, deadlines, and available study hours per day: ")
async def main(input:str):
    print( await Runner.run_sync(research_agent, input, run_config=config,).final_output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main(user_input))