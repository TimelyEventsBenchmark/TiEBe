import os
import re
import json
from collections import defaultdict, OrderedDict

# Diretórios
input_dir = "output_events"
output_path = "stats/results_from_linked_events.json"

# Garantir que o diretório de saída exista
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Estruturas de dados
years_by_country = defaultdict(list)
events_by_month_per_file = {}
total_events_by_month = defaultdict(int)
total_events_by_country = defaultdict(int)
total_events_overall = 0

# Caminhar recursivamente pelas pastas
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

        years_by_country[country].append(year)

        file_path = os.path.join(root, filename)

        # Abrir e processar o JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Contar eventos por mês
        month_counter = defaultdict(int)
        for month_entry in data.get("Events", []):
            month = month_entry.get("Month", "Unknown")
            events = month_entry.get("Data", [])

            # Filtrar eventos que possuem pelo menos um link
            valid_events = [
                event for event in events if event.get("links", [])
            ]
            count = len(valid_events)

            month_counter[month] += count
            total_events_by_month[month] += count
            total_events_by_country[country] += count
            total_events_overall += count

        # Adicionar o total ao final do dict
        month_counter["total"] = sum(month_counter.values())

        # Nome do arquivo relativo para identificar no resultado
        relative_path = os.path.relpath(file_path, input_dir)

        # Ordenar os meses dentro do arquivo
        events_by_month_per_file[relative_path] = dict(month_counter.items())

# Ordenar os anos por país
years_by_country = {
    country: sorted(years) for country, years in sorted(years_by_country.items())
}

# Ordenar os arquivos por nome
events_by_month_per_file = dict(sorted(events_by_month_per_file.items()))

# Ordenar total_events_by_month por mês
total_events_by_month = dict(total_events_by_month.items())

# Ordenar total_events_by_country por nome
total_events_by_country = dict(sorted(total_events_by_country.items()))

# Montar resultado final
result = {
    "years_by_country": years_by_country,
    "event_counts_by_file": events_by_month_per_file,
    "total_events_by_month": total_events_by_month,
    "total_events_by_country": total_events_by_country,
    "total_events_overall": total_events_overall,
}

# Salvar em JSON
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4, ensure_ascii=False)

print(f"Results saved: {output_path}")