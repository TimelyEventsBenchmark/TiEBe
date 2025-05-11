from bs4 import BeautifulSoup
import re
import json
import calendar
import wikipedia
from datetime import datetime
from fuzzywuzzy import fuzz
import sys


def is_valid_date(date_string, format="%d/%m/%Y"):
    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False


def month_number(name):
    try:
        return f"{list(calendar.month_name).index(name.capitalize()):02d}"
    except ValueError:
        return None


def filter_text(text, month, next_month):
    # pattern = re.compile(rf'\b{month} (\d+)\b')
    pattern = re.compile(rf"\b(\d+) {month}\b")
    new_text = re.sub(pattern, "", text)
    new_text = re.sub(r"\[\d+\]", "", new_text)

    pattern = re.compile(rf"\b(\d+) {next_month}\b")
    new_text = re.sub(pattern, "", new_text)
    new_text = re.sub(r"\[\d+\]", "", new_text)

    pattern = re.compile(rf"\b{month} (\d+)\b")
    new_text = re.sub(pattern, "", text)
    new_text = re.sub(r"\[\d+\]", "", new_text)

    pattern = re.compile(rf"\b{next_month} (\d+)\b")
    new_text = re.sub(pattern, "", new_text)
    new_text = re.sub(r"\[\d+\]", "", new_text)

    new_text = new_text.replace("–", "", 2)
    new_text = new_text.replace(":", "", 2)
    return new_text.strip()


def add_or_append(events_array, new_data):
    if len(new_data["Data"]) == 0:
        return None
    for event in events_array:
        if event["Month"] == new_data["Month"]:
            for event_data in event["Data"]:
                nt = new_data["Data"][0]["event_text"]
                if event_data["event_text"] == nt:
                    return None
            event["Data"].append(new_data["Data"].pop())
            return None
    events_array.append(new_data)
    return None


def get_dates(frase, year, month, next_month):
    # Expressão regular para encontrar padrões de "[Mês] [Número]"
    # pattern = re.compile(rf'\b{month} (\d+)\b')
    # Expressão para "[numero] [Mes]"
    pattern = re.compile(rf"\b(\d+) {month}\b")
    matches = re.findall(pattern, frase)
    if len(matches) == 0:
        pattern = re.compile(rf"\b{month} (\d+)\b")
        matches = re.findall(pattern, frase)

    # Expressão regular para encontrar padrões de "[Mês] [Número]"
    # Eprint("oi")ncontrar todas as ocorrências na frase
    matches = [f"{str(i).zfill(2)}/{month_number(month)}/{year}" for i in matches]

    pattern = re.compile(rf"\b(\d+) {next_month}\b")
    # Encontrar todas as ocorrências na frase
    matches2 = re.findall(pattern, frase)
    if len(matches2) == 0:
        pattern = re.compile(rf"\b{next_month} (\d+)\b")
        matches2 = re.findall(pattern, frase)

    if (index_next_month) == 1:
        year = str(int(year) + 1)

    matches2 = [
        f"{str(i).zfill(2)}/{f'{index_next_month:02d}'}/{year}" for i in matches2
    ]

    matches.extend(matches2)

    maybeday = frase.split(":")[0]
    possdays = maybeday.split("-")
    if len(possdays) > 0:
        initPday = possdays[0]
        endPday = possdays[1] if len(possdays) > 1 else None
        if initPday.isnumeric() and (endPday is None or endPday.isnumeric()):
            initPday = int(initPday)
            if initPday > 0 and initPday < 32:
                initPday = f"{str(initPday).zfill(2)}/{month_number(month)}/{year}"
                matches = matches + [initPday]

                if endPday and endPday.isnumeric():
                    endPday = int(endPday)
                    if endPday > 0 and endPday < 32:
                        endPday = (
                            f"{str(endPday).zfill(2)}/{month_number(month)}/{year}"
                        )
                        matches.append(endPday)

    return [valid_date for valid_date in matches if is_valid_date(valid_date)]

def get_current_month(frase):
    for month in list(calendar.month_name):
        if month == "":
            continue
        pattern = re.compile(rf"\b(\d+) {month}\b")
        matches = re.findall(pattern, frase)
        if len(matches) == 0:
            pattern = re.compile(rf"\b{month} (\d+)\b")
            matches = re.findall(pattern, frase)

        if matches:
            return month

    return None


def verificar_mes(mes):
    # Obtenha os nomes completos e abreviados dos meses
    meses_completos = list(calendar.month_name)
    meses_abreviados = list(calendar.month_abbr)

    # Verifica se o mês está em qualquer uma das listas (ignorando case)
    if mes.capitalize() in meses_completos or mes.capitalize() in meses_abreviados:
        return True
    return False


def split_ph_dt(frase):
    # Expressões regulares para os diferentes formatos de data
    padroes = [
        r"\b(\d{4})-(\d{2})-(\d{2})\b",  # Padrão ISO (YYYY-MM-DD)
        r"\b(\d{2})/(\d{2})/(\d{4})\b",  # Padrão europeu (DD/MM/YYYY)
        r"\b(\d{1,2})\s([A-Za-z]+)\s(\d{4})\b",  # Padrão textual (DD Month YYYY)
        r"\b([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})\b",  # Padrão textual invertido (Month DD, YYYY)
        r"\b([A-Za-z]{3})\.\s(\d{1,2}),?\s(\d{4})\b",  # Padrão abreviado com ponto (Jan. 1, 2023)
    ]

    datas_identificadas = []
    fragmentos = [frase]

    for padrao in padroes:
        i = 0
        tam = len(fragmentos)
        while i < tam:
            matches = re.split(padrao, fragmentos[i])
            matches = [i for i in matches if not i.isnumeric() and not verificar_mes(i)]
            fragmentos[i : i + 1] = matches
            i += 1

    return fragmentos

def identificar_datas(frase):
    # Expressões regulares para os diferentes formatos de data
    padroes = [
        r"\b(\d{4})-(\d{2})-(\d{2})\b",  # Padrão ISO (YYYY-MM-DD)
        r"\b(\d{2})/(\d{2})/(\d{4})\b",  # Padrão europeu (DD/MM/YYYY)
        r"\b(\d{1,2})\s([A-Za-z]+)\s(\d{4})\b",  # Padrão textual (DD Month YYYY)
        r"\b([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})\b",  # Padrão textual invertido (Month DD, YYYY)
        r"\b([A-Za-z]{3})\.\s(\d{1,2}),?\s(\d{4})\b",  # Padrão abreviado com ponto (Jan. 1, 2023)
    ]

    datas_identificadas = []

    for padrao in padroes:
        matches = re.findall(padrao, frase)
        for match in matches:
            try:
                if len(match) == 3:
                    if padrao == padroes[0]:  # Padrão ISO (YYYY-MM-DD)
                        if int(match[1]) > 12:
                            data = f"{match[0]}-{match[2]}-{match[1]}"
                        else:
                            data = f"{match[0]}-{match[1]}-{match[2]}"
                        data_obj = datetime.strptime(data, "%Y-%m-%d")

                    elif padrao == padroes[1]:  # Padrão europeu (DD/MM/YYYY)
                        if int(match[1]) > 12:
                            data = f"{match[2]}-{match[0]}-{match[1]}"
                        else:
                            data = f"{match[2]}-{match[1]}-{match[0]}"
                        data_obj = datetime.strptime(data, "%Y-%m-%d")
                    else:  # Padrão textual (DD Month YYYY) ou (Month DD, YYYY)
                        if padrao == padroes[2]:
                            data = f"{match[0]} {match[1]} {match[2]}"
                        else:
                            data = f"{match[1]} {match[0]} {match[2]}"
                        data_obj = datetime.strptime(data, "%d %B %Y")

                    # Adiciona a data formatada no array
                    datas_identificadas.append(data_obj.strftime("%Y-%m-%d"))
            except ValueError:
                continue  # Ignora datas inválidas

    return datas_identificadas


def classif_data(array, frase):
    return split_ph_dt(frase)


def check_word_in_phrase(word, phrase):
    words = phrase.split()
    for w in words:
        if fuzz.ratio(word.lower(), w.lower()) > 92:
            return True
    return False


def ret_dates(list_dates, list_phrases):
    ret_shape = {
        "Archieved": None,
        "Retrieved": None,
        "Created": None,
    }
    if len(list_dates) == 0:
        return ret_shape

    limiar = len(list_phrases)
    p = 0
    rest = []
    while len(list_phrases) > 0 and len(list_dates) > 0:
        if check_word_in_phrase("Retrieved", list_phrases[p]):
            ret_shape["Retrieved"] = list_dates[p]
            list_phrases.pop(p)
            list_dates.pop(p)
            limiar -= 1
            continue

        if check_word_in_phrase("Archieved", list_phrases[p]):
            ret_shape["Archieved"] = list_dates[p]
            list_phrases.pop(p)
            list_dates.pop(p)
            limiar -= 1
            continue
        list_phrases.pop(p)
        rest.append(list_dates.pop(p))
        limiar -= 1

    if len(rest) > 0:
        rest.sort()
        ret_shape["Created"] = rest[0]

    return ret_shape


if len(sys.argv) < 3:
    print("Usage: python3 main.py <country> <year>")
    sys.exit(1)

country = sys.argv[1]
year = sys.argv[2]
wikipedia.set_lang("en")
if country == "World":
    subject = f"{year}"
else:
    subject = f"{year}_in_{country}"
content = wikipedia.WikipediaPage(subject).html()


html = content
soup = BeautifulSoup(html, "html.parser")

# Encontrar todas as tags <li> com ID no padrão "#cite_note-X"
cite_note_li_tags = soup.find_all("li", {"id": re.compile(r"cite_note-\d+")})
# print(cite_note_li_tags[0])
# Criar um vetor para armazenar todos os links dentro de cada <li>
links_por_id = {}

# Iterar sobre as tags identificadas
for li_tag in cite_note_li_tags:
    tag_id = li_tag["id"]
    # Encontrar todos os links dentro da tag <li> correspondente
    links = li_tag.find_all("a")

    text_ref = "-" + li_tag.find_all("span")[1].get_text() + "-"

    datas_ident = identificar_datas(text_ref)
    classif = classif_data(datas_ident, text_ref)

    imp_dates = ret_dates(datas_ident, classif)
    # Adicionar os links ao vetor
    links_por_id[tag_id.split("-")[1]] = [
        {"link": link.get("href"), "text": text_ref, "dates": imp_dates}
        for link in links
    ]

# Encontrando o próximo h2
start_tag = soup.find("h2", id="Events")
if start_tag is None:
    start_tag = soup.find("h2", id="Events_by_month")
    if start_tag is None:
        start_tag = soup.find("h2", id="Monthly_events")
        if start_tag is None:
            print(f"error in: https://en.wikipedia.org/wiki/{year}")
            sys.exit(1)
next_tag = start_tag.find_next("h2")

# Extraindo o conteúdo entre as tags start_tag e next_tag
content = ""
current_tag = start_tag.find_next()
while current_tag and current_tag != next_tag:
    content += str(current_tag)
    current_tag = current_tag.find_next()

soup = BeautifulSoup(content, "html.parser")

eventos_dict = {"Events": []}

_monthmixed = 0

# Encontrar todas as tags <h3>
h3_tags = soup.find_all("h3")

referencias = links_por_id

for h3_tag in list(set(h3_tags)):
    # Inicializar um dicionário para cada grupo
    month = h3_tag.text.replace("[edit]", "")
    # remove all special characters and numbers from month
    month = re.sub(r"[^a-zA-Z]", " ", month)
    month = re.sub(r"\s+", " ", month).strip() 
    if len(month.split()) > 1:
        _monthmixed = 1
        continue
        
    see_m = any(d["Month"] == month for d in eventos_dict["Events"])

    if (month not in list(calendar.month_name)) or (see_m):
        continue

    # print(see_m, month)
    grupo_dict = {"Month": month, "Data": []}

    # Obtenha o índice do mês atual
    index_actual = list(calendar.month_name).index(month)
    # index_moprox mes
    index_next_month = (index_actual % 12) + 1
    # prox mes
    next_month = calendar.month_name[index_next_month]

    # Encontrar o próximo elemento <ul> após a tag <h3>
    ul_tag = h3_tag.find_next("ul")

    # Verificar se há elementos <li> dentro do <ul>
    if ul_tag:
        last_start_date = None
        # Extrair e adicionar o texto e as referências de cada elemento <li> ao dicionário do grupo
        for li_tag in ul_tag.find_all("li"):
            texto_li = li_tag.text
            referencias_li = []

            # Verificar se o texto contém a referência "[<n>]" e se há referências correspondentes no dicionário
            for match in re.finditer(r"\[(\d+)\]", texto_li):
                numero_referencia = match.group(1)
                if numero_referencia in referencias:
                    referencias_li.extend(
                        [
                            i
                            for i in referencias[numero_referencia]
                            if i["link"][0] not in ["#", "/"]
                        ]
                    )

            dates = get_dates(texto_li, year, month, next_month)

            if not len(dates):
                # print(texto_li, year, month, next_month)
                if last_start_date == None:
                    continue
                start_date = last_start_date
                end_date = last_end_date
            else:
                try:
                    start_date = dates[0]
                    end_date = dates[1]
                except IndexError:
                    end_date = None
                last_start_date = start_date
                last_end_date = end_date

            # Remove eventos duplicados
            if "\n" not in texto_li:
                # Adicionar ao dicionário do grupo
                grupo_dict["Data"].append(
                    {
                        "event_text": filter_text(texto_li, month, next_month),
                        "links": referencias_li,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )

    else:
        last_start_date = None
        p_tags = []
        tag = h3_tag.find_next("p")
        while tag:
            p_tags.append(tag)
            tag = tag.find_next()
            if tag.name != "p":
                break
        for p_tag in p_tags:
            texto_p = p_tag.text
            referencias_p = []
            for match in re.finditer(r"\[(\d+)\]", texto_p):

                numero_referencia = match.group(1)
                if numero_referencia in referencias:
                    referencias_p.extend(
                        [
                            i
                            for i in referencias[numero_referencia]
                            if i["link"][0] not in ["#", "/"]
                        ]
                    )
            dates = get_dates(texto_p, year, month, next_month)

            if not len(dates):
                if last_start_date == None:
                    continue
                start_date = last_start_date
                end_date = last_end_date
            else:
                try:
                    start_date = dates[0]
                    end_date = dates[1]
                except IndexError:
                    end_date = None
                last_start_date = start_date
                last_end_date = end_date

            grupo_dict["Data"].append(
                {
                    "event_text": filter_text(texto_p, month, next_month),
                    "links": referencias_p,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

            add_or_append(eventos_dict["Events"], grupo_dict)

    # Adicionar o dicionário do grupo ao dicionário de eventos
    eventos_dict["Events"].append(grupo_dict)


# Mega fallback
if eventos_dict["Events"] == [] or _monthmixed == 1:
    # Iterar sobre cada tag <li>
    for li_tag in soup.find_all("li"):
        texto_li = li_tag.text
        referencias_li = []

        # Verificar se o texto contém a referência "[<n>]" e se há referências correspondentes no dicionário
        for match in re.finditer(r"\[(\d+)\]", texto_li):
            numero_referencia = match.group(1)
            if numero_referencia in referencias:
                referencias_li.extend(
                    [
                        i
                        for i in referencias[numero_referencia]
                        if i["link"][0] not in ["#", "/"]
                    ]
                )

        month = get_current_month(texto_li)

        # print(month, texto_li)
        if not month:
            continue

        grupo_dict = {"Month": month, "Data": []}
        # Obtenha o índice do mês atual
        index_actual = list(calendar.month_name).index(month)
        # index_moprox mes
        index_next_month = (index_actual % 12) + 1
        # prox mes
        next_month = calendar.month_name[index_next_month]
        # pattern = re.compile(rf'\b{next_month} (\d+)\b')
        # pattern = re.compile(rf'\b(\d+) {month}\b')

        dates = get_dates(texto_li, year, month, next_month)
        if not len(dates):
            try:
                start_date = last_start_date
                end_date = last_end_date
            except:
                start_date = None
                end_date = None
        else:
            try:
                start_date = dates[0]
                end_date = dates[1]
            except IndexError:
                end_date = None
            last_start_date = start_date
            last_end_date = end_date

        # Remove eventos duplicados
        if "\n" not in texto_li:
            # Adicionar ao dicionário do grupo
            grupo_dict["Data"].append(
                {
                    "event_text": filter_text(texto_li, month, next_month),
                    "links": referencias_li,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

        # Adicionar o dicionário do grupo ao dicionário de eventos
        add_or_append(eventos_dict["Events"], grupo_dict)

# Sort data by month
eventos_dict["Events"] = sorted(
    eventos_dict["Events"], key=lambda x: list(calendar.month_name).index(x["Month"])
)

# Converter o dicionário em formato JSON
json_data = json.dumps(eventos_dict, ensure_ascii=False, indent=4)
with open(
    f"output_events/{country}/{year}_in_{country}_events.json", "w", encoding="utf-8"
) as arquivo_json:
    json.dump(eventos_dict, arquivo_json, ensure_ascii=False, indent=4)