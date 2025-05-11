import time
import openai
import argparse
from datasets import load_dataset

from pydantic import BaseModel

class Judgement(BaseModel):
    reasoning: str
    refusal: bool
    correct: bool

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=str, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--judge", choices=["gpt-4o", "deepseek-ai/DeepSeek-V3"], required=True)
parser.add_argument("--base_url", type=str, default="https://api.together.xyz/v1")
parser.add_argument("--temperature", type=float, default=0.0)
parser.add_argument("--api_key",  type=str, default="")
parser.add_argument("--batch_size", type=int, default=1)
args = parser.parse_args()

prompt = """I will provide a question, an expected answer, and the candidate's answer. Your task is to verify if the candidate's answer is correct. The expected answer is the ground truth, so if the candidate's answer contradicts the expected answer it is incorrect.

If the candidate's answer refuses to answer for whatever reason, such as being outside the training data of the model, or the model not being up to date with the latest information, then the candidate's answer must be considered incorrect, and the answer must be marked as refusal.

Question: "{question}"
Expected answer: "{expected_answer}"
Candidate answer: "{model_answer}"

Answer in the format
Reasoning: (your reasoning)
Refusal: (true|false)
Correct: (true|false)""".strip()

client = openai.OpenAI(
    base_url=args.base_url,
    api_key=args.api_key,
)

def parse_correctness(model_answer):
    return model_answer.split("Correct: ")[1]

def parse_refusal(model_answer):
    
    split1=model_answer.split("Refusal: ")
    refusal=split1.split("Correct: ")[0]
    return refusal

def eval_answer(example, retries=10, wait_time=2):
    question = example["question"]
    expected_answer = example["answer"]
    model_answer = example["model_answer"]
    formatted_prompt = prompt.format(question=question, expected_answer=expected_answer, model_answer=model_answer)

    attempt = 0
    while attempt < retries:
        try:
            model_response = client.beta.chat.completions.parse(
                model=args.judge,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=256,
                temperature=args.temperature,
                response_format=Judgement,
            )
            model_answer = model_response.choices[0].message.parsed

            correct = model_answer.correct
            refusal = model_answer.refusal
            reasoning = model_answer.reasoning
                
            usage=model_response.usage
            
            tokens_usage={
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
            
            return {
                "correct": correct,
                "refusal": refusal,
                "reasoning": reasoning,
                "judge_model": args.judge,
                "tokens_usage": tokens_usage,
            }
        
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < retries:
                time.sleep(wait_time)
            else:
                raise

dataset = load_dataset('json', data_files=args.input)

dataset['train'] = dataset['train']
evaluated_dataset = dataset['train'].map(
    eval_answer,
    num_proc=args.batch_size,
)


# sum token usage
total_tokens = sum(example['tokens_usage']['total_tokens'] for example in evaluated_dataset)
print(f"Total tokens: {total_tokens}")

total_prompt_tokens = sum(example['tokens_usage']['prompt_tokens'] for example in evaluated_dataset)
print(f"Total prompt tokens: {total_prompt_tokens}")

total_completion_tokens = sum(example['tokens_usage']['completion_tokens'] for example in evaluated_dataset)
print(f"Total completion tokens: {total_completion_tokens}")


evaluated_dataset.to_json(args.output, orient='records')


