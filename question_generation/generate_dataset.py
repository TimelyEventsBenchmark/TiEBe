from datasets import Dataset, DatasetDict
from pathlib import Path
import json
from collections import defaultdict
import random
import os
import argparse


def month_mapping(month):
    return {
        '01': 'January',
        '02': 'February',
        '03': 'March',
        '04': 'April',
        '05': 'May',
        '06': 'June',
        '07': 'July',
        '08': 'August',
        '09': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December',
    }[month]
    
def select_question(questions, date):
    month, year = date.split('/')
    month_str = month_mapping(month)
    scores=[0 for _ in range(len(questions))]
    
    # give preference to questions that contain the month or year in the question
    for i, qa in enumerate(questions):
        if month_str in qa['question'].lower() or year in qa['question'].lower():
            scores[i] += 1

        
    # give a point to the smaller answer length
    answer_lengths = [len(qa['answer']) for qa in questions]
    min_answer_length = min(answer_lengths)
    for i, qa in enumerate(questions):
        if len(qa['answer']) == min_answer_length:
            scores[i] += 1
            
    # give point to questions that contain numbers, as those tend to be more specific
    for i, qa in enumerate(questions):
        if any(char.isdigit() for char in qa['question']):
            scores[i] += 1
  
    # give minus 100 points if the question contains forbidden words
    forbidden_words = ['article', "some of"]
    for i, qa in enumerate(questions):
        if any(word in qa['question'].lower() for word in forbidden_words):
            scores[i] -= 100
    
    return questions[scores.index(max(scores))]

    
    

def get_region(file_path):
    # /data/thales/tiebe-wikip/tiebe_questions_candidates/Argentina/extracted_events_2017_Argentina.json-> Argentina
    return str(file_path).split('/')[-2]




parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", type=str, default="tiebe_questions_candidates")
parser.add_argument("--output_dir", type=str, default="tiebe_dataset")
parser.add_argument("--use_all_questions", type=bool, default=False)

args = parser.parse_args()
data_path = [args.input_dir]
output_dir = args.output_dir
random.seed(42)
use_all_questions=args.use_all_questions

all_data = defaultdict(list)
for path in data_path:
    files = Path(path).rglob("**/*.json")
    for file in files:
        with open(file,) as f:
            data = json.load(f)
            for item in data:
                month, year = item['date'].split('/')
                region = get_region(file)
                text=item['text']
                # just making sure that event with no text are not included
                if len(text) < 10:
                    continue
                if use_all_questions:
                    for qa in item['questions']:
                        all_data[region].append({
                            'year': year,
                            'month': month,
                            'event_desc': item['event_desc'],
                            'text': item['text'],
                            'question': qa['question'],
                                'answer': qa['answer'],
                                'region': region
                            })
                else:
                    qa = select_question(item['questions'], item['date'])
                    all_data[region].append({
                        'year': year,
                        'month': month,
                        'event_desc': item['event_desc'],
                        'text': item['text'],
                        'question': qa['question'],
                        'answer': qa['answer'],
                        'region': region
                    })

# Create a DatasetDict with a dataset for each region
datasets_dict = {}
dataset_data={}
for region, items in all_data.items():
    datasets_dict[region] = Dataset.from_list(items)
    dataset_data[region] = items
ds = DatasetDict(datasets_dict)

# convert to json
os.makedirs(output_dir, exist_ok=True)
for region, items in dataset_data.items():
    with open(f"{output_dir}/{region}.json", "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=4)


