import json

# Carregar o arquivo results.json
with open("stats/results.json", "r") as file:
    data = json.load(file)

# Obter os anos e países
years_by_country = data["years_by_country"]
event_counts_by_file = data["event_counts_by_file"]

# Lista para armazenar as combinações que atendem aos critérios
missing_years = []
zero_events = []

# Verificar gaps de anos e eventos com valor 0
for country, years in years_by_country.items():
    # Verificar gaps de anos
    all_years = set(map(str, range(2015, 2026)))
    missing = all_years - set(years)
    for year in missing:
        adr = ""
        if country == "World":
            adr = f"{country} {year}"
            # adr = f"{country} {year}\nhttps://en.wikipedia.org/wiki/{year}"
            # https://en.wikipedia.org/wiki/{year}
        else:
            adr = f"{country} {year}"
            # adr = f"{country} {year}\nhttps://en.wikipedia.org/wiki/{year}_in_{country}"
            # https://en.wikipedia.org/wiki/{year}_in_{country}
        missing_years.append(adr)

    # Verificar meses ou total com valor 0
    for year in years:
        file_key = f"{country}/{year}_in_{country}_events.json"
        if file_key in event_counts_by_file:
            event_data = event_counts_by_file[file_key]
            if event_data.get("total", 0) == 0 or any(
                value == 0 for key, value in event_data.items() if key != "total"
            ):
                adr = ""
                if country == "World":
                    adr = f"{country} {year}"
                    # adr = f"{country} {year}\nhttps://en.wikipedia.org/wiki/{year}"
                else:
                    adr = f"{country} {year}"
                    # adr = f"{country} {year}\nhttps://en.wikipedia.org/wiki/{year}_in_{country}"
                    # https://en.wikipedia.org/wiki/{year}_in_{country}
                zero_events.append(adr)


# Exibir os resultados
# print("Links - Years Missing:")
for combo in missing_years:
    print(combo)

# print("Links - Monthly count equals zero:")
for combo in zero_events:
    print(combo)
