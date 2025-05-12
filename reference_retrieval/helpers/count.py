import json

years = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
country = "Ukraine"
for year in years:
    with open(f'{year}_in_{country}_events.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    pt_months = {
        "January": "janeiro",
        "February": "fevereiro",
        "March": "março",
        "April": "abril",
        "May": "maio",
        "June": "junho",
        "July": "julho",
        "August": "agosto",
        "September": "setembro",
        "October": "outubro",
        "November": "novembro",
        "December": "dezembro"
    }

    counts = {pt: 0 for pt in pt_months.values()}

    for month_block in data.get("Events", []):
        eng = month_block.get("Month")
        pt = pt_months.get(eng)
        if pt:
            counts[pt] = len(month_block.get("Data", []))

    print(counts)
