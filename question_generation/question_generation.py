"""
Script to generate questions and answers from news articles and events.

note that you need to set the TOGETHER_API_KEY environment variable.
"""
import os
import re
import json
import openai
import random
import argparse
import threading
import concurrent.futures
import time
from tqdm import tqdm
from pathlib import Path
from datetime import datetime



prompt_template="""You are an assistant responsible for creating pairs of questions and answers based on news articles. These question-answer pairs will be used to construct a dataset for evaluating knowledge from the past. Your task is to create up to {{n_questions}} questions and their corresponding answers based on the information in the news article. The questions should be clear and understandable, even for those who have not read the article.

Avoid asking about information that is constantly changing or lacks a definitive answer, such as the current death toll of an event or the present status of a specific situation. Focus on questions that will remain relevant in the future.

Use the past tense in the questions. Avoid starting with "What is..." or referring to ongoing events or situations. Refrain from asking about the current status of a particular subject, such as an agreement or situation that may change over time. Also avoid questions with too general answers, such as "What were some of the consequences of X".


Try to focus on creating questions relevant to the specified period. Additionally, avoid overly specific questions. Instead, focus on broader and more meaningful information about significant events. Keep in mind that the reader will not have access to the article itself, so do not reference the article directly (e.g. "according to the article"). Emphasize the key information the article provides, and specify the point in time when an event occurred, if necessary. Write the questions and answers in English, regardless of the language of the article.

You must answer only with the questions and answers and nothing else. Follow this format:
Question: \{question\}
Answer: \{answer\}

{{metadata}}"""

parser = argparse.ArgumentParser(description="")
parser.add_argument('--input_dir', type=str, default='../data/wikipedia/filtered_2/2023')
parser.add_argument('--model', type=str, default='sabia-3')
parser.add_argument('--n_questions', type=int, default=3)
parser.add_argument('--output_dir', type=str, default='wiki_questions_v07/sabia-3/2023')
parser.add_argument('--subsample_ratio', type=float, default=1, help='Subsample the data by this ratio, if 1 no subsampling is done')
parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers for processing')
parser.add_argument('--max_retries', type=int, default=3, help='Maximum number of retries for API calls')
parser.add_argument('--base_wait', type=float, default=1.0, help='Base wait time for exponential backoff (seconds)')

args = parser.parse_args()

metadata_template = '''Event: {event}
Date: {date}
News title: {title}
News content:
{content}'''

def format_date(date):
    return datetime.strptime(date, '%d/%m/%Y').strftime('%m/%Y')

def format_event(date, event_text, title, extracted_text):
    date = format_date(date)
    return metadata_template.format(
        event=event_text,
        date=date,
        title=title,
        content=extracted_text,
    )

def request(prompt, temperature=0.0, max_tokens=1024):
    messages = [{"role": "user", "content": prompt}]
    # Create a client for each thread to avoid concurrency issues
    thread_client = openai.OpenAI(
        base_url='https://api.together.xyz/v1',
        api_key=os.getenv('TOGETHER_API_KEY')
    )
    
    # Implement retry with exponential backoff
    retry_count = 0
    while retry_count <= args.max_retries:
        try:
            response = thread_client.chat.completions.create(
                model=args.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # get tokens
            usage = response.usage
            with lock:
                print(f'Tokens: {usage}')
            
            return response.choices[0].message.content, usage
        except Exception as e:
            retry_count += 1
            if retry_count > args.max_retries:
                raise e
            
            # Exponential backoff
            wait_time = args.base_wait * (2 ** (retry_count - 1))
            with lock:
                print(f"API request failed, retrying in {wait_time:.2f} seconds... (Attempt {retry_count}/{args.max_retries})")
            time.sleep(wait_time)



def extract_pairs(text):
    text=text.replace("*", "")
    pattern = r"Question:\s*(.*?)(?:\n|$)Answer:\s*(.*?)(?=\nQuestion:|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    qa_pairs = [
        {
            'question': question.strip(),
            'answer': answer.strip(),
        }
        for question, answer in matches
    ]
    return qa_pairs



# together 
client= openai.OpenAI(
    base_url='https://api.together.xyz/v1',
    api_key=os.getenv('TOGETHER_API_KEY')
)

# Thread-safe counters and accumulators
lock = threading.Lock()
total_usage = {
    "completion_tokens": 0,
    "prompt_tokens": 0,
    "total_tokens": 0,
}
invalid_events = 0
total_events = 0
successful_events = 0
start_time = time.time()

def process_event(event, processed_events):
    global invalid_events, total_events, total_usage, successful_events
    
    # Skip if event was already processed
    if event['event_text'] in processed_events:
        return None
    
    event_idx = 0
    # Prefer web archive links
    for (idx, link) in enumerate(event['links']):
        if 'web.archive.org' in link['link']:
            event_idx = idx
    
    metadata = format_event(
        event['start_date'],
        event['event_text'],
        event['links'][event_idx]['title'],
        event['links'][event_idx]['extracted_text'],
    )
    prompt = (
        prompt_template
            .replace('{{metadata}}', metadata)
            .replace('{{n_questions}}', str(args.n_questions))
    )
    
    try:
        result, usage = request(prompt)
        
        with lock:
            total_usage['completion_tokens'] += usage.completion_tokens
            total_usage['prompt_tokens'] += usage.prompt_tokens
            total_usage['total_tokens'] += usage.total_tokens
            total_events += 1
        
        if result is None:
            print(f'Empty result: {event["event_text"]}')
            with lock:
                invalid_events += 1
            return None
        
        questions = extract_pairs(result)
        with lock:
            successful_events += 1
        return {
            'event_desc': event['event_text'],
            'text': event['links'][event_idx]['extracted_text'],
            'date': format_date(event['start_date']),
            'questions': questions,
        }
    except Exception as e:
        print(f"Error processing event '{event['event_text']}': {str(e)}")
        with lock:
            invalid_events += 1
        return None

data_files = list(Path(args.input_dir).rglob('*.json'))

for path in tqdm(data_files, desc='Files'):
    with open(path) as f:
        data = json.load(f)
        print(path, len(data))

    output_path = Path(args.output_dir) / f'{path.stem}.json'
    existing_events = []
    
    # Load existing events if output file exists
    if os.path.exists(output_path):
        with open(output_path) as f:
            existing_events = json.load(f)
            print(f'Loaded {len(existing_events)} existing events from {output_path}')
        
        # Create a set of already processed event descriptions for quick lookup
        processed_events = {event['event_desc'] for event in existing_events}
    else:
        processed_events = set()

    data_filtered = []
    for event in data:
        if len(event['links']) == 0:
            print('Empty event:', event['event_text'])
            continue
        data_filtered.append(event)

    # Apply subsampling if ratio < 1
    if args.subsample_ratio < 1:
        random.seed(42)  # For reproducibility
        num_samples = min(int(len(data_filtered) * args.subsample_ratio), 1)
        data_filtered = random.sample(data_filtered, int(len(data_filtered) * args.subsample_ratio))

    events = existing_events.copy()  # Start with existing events
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process events in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_event = {
            executor.submit(process_event, event, processed_events): event
            for event in data_filtered if event['event_text'] not in processed_events
        }
        
        # Process results as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_event), 
                          total=len(future_to_event),
                          desc='Generating'):
            event = future_to_event[future]
            try:
                result = future.result()
                if result:
                    with lock:
                        events.append(result)
                        # Save progress periodically (after every 5 completed events)
                        if len(events) % 5 == 0:
                            with open(output_path, 'w') as out:
                                json.dump(events, out, indent=4, ensure_ascii=False)
                            elapsed_time = time.time() - start_time
                            events_per_second = successful_events / elapsed_time if elapsed_time > 0 else 0
                            print(f"Progress: {successful_events}/{len(future_to_event)} events processed "
                                  f"({events_per_second:.2f} events/sec). "
                                  f"Success rate: {successful_events/total_events*100:.1f}% "
                                  f"Tokens used: {total_usage['total_tokens']}")
            except Exception as exc:
                print(f'Event {event["event_text"]} generated an exception: {exc}')
        
        # Final save after all events are processed
        with open(output_path, 'w') as out:
            json.dump(events, out, indent=4, ensure_ascii=False)

print(f'Total usage: {total_usage}')
print(f'Total events: {total_events}')
print(f'Successful events: {successful_events} ({successful_events/total_events*100:.1f}% success rate)')
print(f'Invalid events: {invalid_events}')
print(f'Total execution time: {time.time() - start_time:.2f} seconds')
print(f'Average processing time per event: {(time.time() - start_time)/total_events:.2f} seconds')
