# Answer Generation

This module contains the code to generate answers for Tiebe. You can generate answers with any openai Compatible interface.

# Execution

```bash
python3 generate_answer.py --input_dir <path_for_input_folder> --output <path_for_output_file> --model <model_name> --subset <subset_name> --mode <mode_name>
```

parameters:
- input_dir: path to the input file containing the events of a given country ( note that this is the path for the file, not the folder), if not provided, the dataset will be loaded from the hf hub
- output: path to the output file containing the generated answers
- model: name of the model to use
- subset: name of the subset to use (normally the country name)
- mode: mode to use (english or native), only relevant if loading dataset from the hf hub
- base_url: base url of the api
- api_key: api key of the api
- temperature: temperature of the model
- batch_size: batch size that should be used for the requests


##  Tiebe tested models

In our work, we tested the following 9 models (presented alongside the model provider):

- Openai - GPT-4.1
- Openai - GPT-4.1-mini
- Openai - GPT-4o
- Maritaca AI - Sabia-3
- Maritaca AI - Sabiazinho-3
- Together.ai - Llama4 Maverick
- Together.ai - Qwen2.5-72B-Instruct
- Together.ai - Qwen2-72B-Instruct
- Mistral AI - Mistral-large



