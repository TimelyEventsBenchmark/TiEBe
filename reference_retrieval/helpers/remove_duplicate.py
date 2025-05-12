import json

def get_content_size(text):
    return len(text)

def choose_larger_link(links):
    if len(links) <= 1:
        return links
    
    originals = []
    archived = []
    for link in links:
        if 'web.archive.org' in link.get('link', ''):
            archived.append(link)
        else:
            originals.append(link)
    
    if not archived:
        return links
    
    all_links = originals + archived
    sizes = {}
    for lnk in all_links:
        url = lnk['link']
        sizes[url] = get_content_size(lnk["extracted_text"])
    
    largest_url = max(sizes, key=lambda u: sizes[u])
    return [next(l for l in all_links if l['link'] == largest_url)]

def process_json(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    for event in events:
        links = event.get('links', [])
        if len(links) > 1:
            event['links'] = choose_larger_link(links)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    country = "Portugal"
    years = ["2024", "2025"]
    for year in years:
        input_path = f'extracted_events_{year}_{country}.json'
        output_path = f'new_extracted_events_{year}_{country}.json'
        process_json(input_path, output_path)
