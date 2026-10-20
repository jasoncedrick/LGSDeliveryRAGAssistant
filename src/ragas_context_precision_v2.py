"""Opt-in RAGAS 0.1.5 integration of the versioned offline evidence judge."""
import math
from ragas.metrics._context_precision import ContextPrecision
from ragas.llms.prompt import PromptValue
from src.context_precision_judge_v2 import build_prompt,FORMAT_RETRY_SUFFIX
from src.offline_judge_grounding import parse_grounded_verdict

class GroundedContextPrecision(ContextPrecision):
    format_retry_limit=0
    audit_sink=None
    def _context_precision_prompt(self,row):
        return [PromptValue(prompt_str=build_prompt(row['question'],row['ground_truth'],context)) for context in row['contexts']]

    async def _ascore(self,row,callbacks,is_async):
        assert self.llm is not None,'LLM is not set'
        parsed=[]
        for prompt,context in zip(self._context_precision_prompt(row),row['contexts']):
            result=await self.llm.generate(prompt,n=1,callbacks=callbacks,is_async=is_async)
            value,error=parse_grounded_verdict(result.generations[0][0].text,context)
            if error and self.audit_sink:self.audit_sink({'stage':'context_precision_contract','error':error,'retry_requested':bool(self.format_retry_limit)})
            if error and self.format_retry_limit:
                retry=PromptValue(prompt_str=prompt.to_string()+FORMAT_RETRY_SUFFIX)
                result=await self.llm.generate(retry,n=1,callbacks=callbacks,is_async=is_async)
                value,error=parse_grounded_verdict(result.generations[0][0].text,context)
                if error and self.audit_sink:self.audit_sink({'stage':'context_precision_contract_retry','error':error})
            if error:return math.nan
            parsed.append(value)
        # Delegate the numerical metric to installed RAGAS, not a substitute score.
        return self._calculate_average_precision(parsed)
