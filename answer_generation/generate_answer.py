import time
import openai
import argparse
from datasets import load_dataset, disable_progress_bars, Dataset, DatasetDict
import os
import json

def load_dataset_from_local(input_dir):
    # list all json files in the input directory
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    
    datasets_dict = {}
    for json_file in json_files:
        country = json_file.split('.')[0]
        data=json.load(open(os.path.join(input_dir, json_file)))
        datasets_dict[country] = Dataset.from_list(data)
        
    # load all json files
    dataset = DatasetDict(datasets_dict)
    return dataset

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--input_dir", type=str, required=False, help="local input directory, if not provided, the dataset will be loaded from the hf hub")
parser.add_argument("--model", required=True)
parser.add_argument("--subset", required=True)
parser.add_argument("--mode", choices=["english", "native"], default="english")
parser.add_argument("--base_url", type=str, default="https://api.together.xyz/v1")
parser.add_argument("--api_key",  type=str, default="")
parser.add_argument("--temperature", type=float, default=0.0)
parser.add_argument("--batch_size", type=int, default=1)
args = parser.parse_args()

prompt = """Answer the following question:
"{question}"
If necessary, consider the context of {region}, answer in the same language as the question. Provide your response in the following format:
"Answer: {{your answer}}" """.strip()

client = openai.OpenAI(
    base_url=args.base_url,
    api_key=args.api_key,
)

def generate_answer(example, retries=10, wait_time=2):
    question = example["question"]
    formatted_prompt = prompt.format(question=question, region=example["region"])

    attempt = 0
    while attempt < retries:
        try:
            model_response = client.chat.completions.create(
                model=args.model,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=256,
                temperature=args.temperature,
            )
            model_answer = model_response.choices[0].message.content
            return {'model_answer': model_answer}
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < retries:
                time.sleep(wait_time)
            else:
                raise

if args.input_dir:
    dataset = load_dataset_from_local(args.input_dir)
else:
    dataset = load_dataset("TimelyEventsBenchmark/TiEBe", args.subset, split=args.mode)
print(dataset)
answered_dataset = dataset.map(
    generate_answer,
    num_proc=args.batch_size,
)
disable_progress_bars()
answered_dataset.to_json(args.output, orient='records')