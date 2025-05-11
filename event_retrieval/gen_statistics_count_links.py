import os
import json
from collections import defaultdict

# Diretório de entrada e saída
input_dir = "output_events"
output_path = "stats/link_counts_by_country.json"

# Garantir que o diretório de saída exista
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Dicionários para armazenar as contagens
total_links_by_country = defaultdict(int)
links_by_country_year = defaultdict(lambda: defaultdict(int))

# Percorrer todos os arquivos JSON na pasta
for root, _, files in os.walk(input_dir):
    for filename in files:
        if not filename.endswith(".json"):
            continue

        try:
            year = filename.split("_")[0]
            country = filename.split("_events")[0].split("_in_")[1]
        except IndexError:
            print(f"Unexpected file name: {filename}")
            continue

        file_path = os.path.join(root, filename)

        # Abrir e processar o arquivo JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for month_entry in data.get("Events", []):
            for event in month_entry.get("Data", []):
                links = event.get("links", [])
                count = len(links)

                total_links_by_country[country] += count
                links_by_country_year[country][year] += count

# Ordenar resultados
total_links_by_country = dict(sorted(total_links_by_country.items()))
links_by_country_year = {
    country: dict(sorted(years.items()))
    for country, years in sorted(links_by_country_year.items())
}

# Salvar tudo em um único JSON
result = {
    "total_links_by_country": total_links_by_country,
    "links_by_country_and_year": links_by_country_year,
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4, ensure_ascii=False)

print(f"Link counts saved to: {output_path}")
