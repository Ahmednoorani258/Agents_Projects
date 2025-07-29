from setupconfig import config
from agents_file import scheduler_agent, research_agent, summarizer_agent
from agents import Runner
from hooks import ExampleHooks
from guardrail import academic_filter_guardrail


user_input = input("Please enter your study topics, deadlines, and available study hours per day: ")
# async def main(input:str):
#     print( await Runner.run_sync(research_agent, input, run_config=config,).final_output)

async def main(user_input):
    result = await Runner.run(
        scheduler_agent,
        user_input,
        hooks=hooks,
        run_config=config,
    )
    print(result.final_output)
if __name__ == "__main__":
    import asyncio
    hooks = ExampleHooks()
    asyncio.run(main(user_input))


# Don't call asyncio.run(main(...)) if you're in Streamlit, Jupyter, etc

