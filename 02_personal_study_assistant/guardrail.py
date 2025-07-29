from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, TResponseInputItem, input_guardrail,output_guardrail,InputGuardrailTripwireTriggered
from pydantic import BaseModel
from typing import List

class SearchResult(BaseModel):
    title: str
    url: str
    content: str

class ResearchOutput(BaseModel):
    results: List[SearchResult]
    
class SummaryOutput(BaseModel):
    summary: str
    
@output_guardrail
async def summary_length_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: SummaryOutput
) -> GuardrailFunctionOutput:
    words = output.summary.split()
    trimmed = " ".join(words[:100]) + ("..." if len(words) > 100 else "")

    return GuardrailFunctionOutput(
        output_info=SummaryOutput(summary=trimmed),
        tripwire_triggered=False  # Safe fallback
    )


@output_guardrail
async def academic_filter_guardrail(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    output: ResearchOutput
) -> GuardrailFunctionOutput:
    academic_domains = ["edu", "arxiv.org", "researchgate.net", "khanacademy.org", "mit.edu"]
    
    filtered = [
        result for result in output.results
        if any(domain in result.url for domain in academic_domains)
    ]

    return GuardrailFunctionOutput(
        output_info=ResearchOutput(results=filtered),
        tripwire_triggered=False  # No refusal, just filtered output
    )
