# Model Evaluation

This folder contains the code to evaluate the performance of the models. We expect that you generated the answers using the "answer_generation" module, present in this repository.

## Execution

```bash
python judge_model_answers.py --input <path_to_answers_file> --output <path_to_output_file> --judge <model_name>
```

parameters:
- input: path to the answers file
- output: path to the output file
- judge: name of the judge model (gpt-4o or deepseek-ai/DeepSeek-V3)
- base_url: base url of the api
- temperature: temperature of the model
- batch_size: batch size that should be used for the requests
- api_key: api key for the judge model


the script will write an output file with the same fields as the input file, but with the following additional fields:
- reasoning: reasoning of the judge model
- refusal: true if the judge model considered that the candidate model refused to answer, false otherwise
- correct: true if the judge model considered that the candidate model's answer is correct, false otherwise


