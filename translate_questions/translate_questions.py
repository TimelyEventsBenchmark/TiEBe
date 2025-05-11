import os
import json
import openai
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field

class TranslationResult(BaseModel):
    question_translated: str = Field(description="The translated question.")
    answer_translated: str = Field(description="The translated answer.")

countries_languages = {
    "Argentina": "Spanish",
    "Brazil": "Portuguese",
    "China": "Chinese",
    "Colombia": "Spanish",
    "Ethiopia": "Amharic",
    "France": "French",
    "Germany": "German",
    "India": "Hindi",
    "Indonesia": "Indonesian",
    "Mexico": "Spanish",
    "Papua New Guinea": "Tok Pisin",
    "Portugal": "Portuguese",
    "Russia": "Russian",
    "The Democratic Republic of the Congo": "French",
    "Turkey": "Turkish",
    "Ukraine": "Ukrainian"
}

def translate_content(
    country: str, language: str, question: str, answer: str, client: openai.OpenAI
) -> TranslationResult:
    prompt = f"""
    You are a professional translator.
    Translate the following question and answer from English to {language}, the primary language spoken in {country}.

    Original Question (English): "{question}"
    Original Answer (English): "{answer}"
    """

    try:
        translation_result = client.beta.chat.completions.parse(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in accurate translations."},
                {"role": "user", "content": prompt}
            ],
            response_format=TranslationResult,  # ← Uso direto do modelo pydantic
        )
        print(translation_result)
        return translation_result

    except Exception as e:
        print(f"[API Error] {country}: {str(e)}")
        return TranslationResult(question_translated="", answer_translated="")

def translate_dataset(input_dir: str, output_dir: str, api_key: str, max_workers: int = 20):
    client = openai.OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    for country, language in countries_languages.items():
        input_file = os.path.join(input_dir, f"{country.replace(' ', '_')}.json")
        output_file = os.path.join(output_dir, f"{country.replace(' ', '_')}.json")

        if os.path.exists(output_file):
            print(f"{country}.json already translated.")
            continue

        if not os.path.exists(input_file):
            print(f"{country}.json not found. Skipping.")
            continue

        with open(input_file, 'r', encoding='utf-8') as f:
            data: List[Dict[str, Any]] = json.load(f)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    translate_content, country, language,
                    entry.get("question", ""), entry.get("answer", ""), client
                ): entry
                for entry in data if entry.get("question") or entry.get("answer")
            }

            for future in as_completed(futures):
                entry = futures[future]
                try:
                    parsed_completion = future.result()
                    translation: TranslationResult = parsed_completion.choices[0].message.parsed

                    entry["question"] = translation.question_translated
                    entry["answer"] = translation.answer_translated

                except Exception as exc:
                    print(f"[Translation Exception] {exc}")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Translation for {country} saved to {output_file}.")

if __name__ == "__main__":
    INPUT_DIR = ""
    OUTPUT_DIR = "translated"
    API_KEY=""

    translate_dataset(INPUT_DIR, OUTPUT_DIR, API_KEY, max_workers=1)