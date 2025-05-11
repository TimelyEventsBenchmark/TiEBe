# Question Generation

This module contains the code to generate questions and answers from news articles and events for TiEBe.

# execution

Assuming you already have retrieved the news articles for each event, you can generate the questions and answers with the following command:

```bash
python3 generate_questions.py --input_dir <path_for_country_folder> --model deepseek-ai/DeepSeek-V3 --n_questions <number_of_questions_per_event> --output_dir <path_for_output_folder> --subsample_ratio 1 --workers 8; 
```

- input_dir is the path to the folder containing the news articles for each event.
- output_dir is the path to the folder where the questions and answers will be saved.
- model is the name of the model to use (assuming you are using a model from together.ai)
- subsample_ratio is the ratio of the number of events to be used, useful for debugging.
- workers is the number of threads to use.

Additionaly you need to set the TOGETHER_API_KEY environment variable.

The script will generate in output_dir a json file containing the generated questions, we recommend generating more than 1 one question per event, because it increases the chance of finding a good question in the next step.


With the generated questions you can now create the dataset with the following command:

```bash
python3 generate_dataset.py --input_dir <path_for_output_folder> --output_dir <path_for_output_folder>
```

The script will generate in output_dir a json file for each country containing one question per event, the question is selected based on a set of simple heuristics.
Alternatively you can pass the flag --use_all_questions to use all the questions previosly generated, this means there would be more than one question per event in the dataset.








