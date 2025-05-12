import json
years = ["2015","2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
country = "Ukraine"
for year in years:
    with open(f'new_extracted_events_{year}_{country}.json', 'r', encoding='utf-8') as f:
        events = json.load(f)

    month_map = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro",
    }

    counts = {name: 0 for name in month_map.values()}

    for ev in events:
        sd = ev.get("start_date", "")
        if not sd:
            continue
        parts = sd.split("/")
        if len(parts) != 3:
            continue
        try:
            month_num = int(parts[1])
        except ValueError:
            continue

        links = ev.get("links", [])
        count = 0
        for link in links:
            if "extracted_text" not in link:
                continue
            if link["extracted_text"].strip() != "":
                count+=1
        counts[month_map[month_num]] += count

    print(counts)
