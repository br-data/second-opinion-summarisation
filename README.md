![logo](assets/logoSecondOpinion.gif)

Detect hallucinated content in generated answers for any RAG system.

:warning: This is only a Proof of Concept and not ready for production use.

## Installation

This API is tested with Python version 3.11 on Debian but should run on most recent Python versions and operation systems.

1. Create virtual environment `pyenv virtualenv 3.11.7 NAME && pyenv activate NAME`
2. Install dependencies `pip install -r requirements.txt`
3. Add your OpenAI-API key as an environment variable `source OPENAI_API_KEY=your key`
4. Run `python3 app.py`

You can now view the Swagger documentation of the API in your browser under `localhost:3000`.

## Endpoints

### Summarisation
The endpoint `completion` returns a shortened version of the input text you provide as source.

You can access it with the following curl statement or via the Swagger docs.

```shell
curl -X 'POST' \
  'http://localhost:3000/completion?model=gpt-3.5-turbo&honest=true' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "string"
}'
```

Since this API is also designed for demonstration purposes it is possible to enforce hallucinations by setting the 
honest parameter to `false`. As models you can choose either `gpt-3.5-turbo` or `gpt-4-turbo`. 


## Fact check

The endpoint `check` performs a check if a `sentence` is contained in the `source`. 

If this test is passed, the endpoint returns a boolean value `result` as `true`. If the information from the sentence is
not contained in the source, it will return false.

Besides this boolean value, the endpoint returns an array `answers`, which spell out for each sentence in the source
why or why not it is contained in the source.

As an URL paramater you can pass the threshold, a lower threshold means higher latency and possibly better accuracy. 
The default value is 0.65.

```shell
curl -X 'POST' \
  'http://localhost:3000/check?semantic_similarity_threshold=0.65&model=gpt-3.5-turbo' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "source": "string",
  "sentence": "string"
}'
```

## Evaluation
This repository contains two scripts designed to evaluate and enhance the accuracy of our hallucination detection systems. 
The script `evaluation.py` aims to validate the effectiveness of the system by comparing its predictions with the
gold standard dataset, ultimately providing a measure of accuracy.

The script `predictor.py` focuses on processing the test data set using the provided API to create set to validate against. 

### Available Test- and Training Data

The test and training data ist purely synthetic. It is generated by a random dump from our vector store containing 
BR24 articles, split by `<p>`aragraphs. For the test set 150 of those paragraphs are randomly sampled and saved to
`data/test.csv`. 

This file is used by `create_training_data.py` to generate a question which can be answered given the paragraph.

Using this question and the paragraph, GPT 3.5 Turbo is used to generate answers to the questions. In some cases
the LLM is explicitly asked to add wrong but plausible content to the answer.

## Hypothesis data

Your hypothesis data should be placed in the data folder and be suffixed with `_result.jsonl`. Each row shall contain a 
JSON object with the structure as follows:

```json
{
  "id": "string",
  "hallucination": true,
  "prob": 0.01
}
```

## Evaluation
To run the evaluation simply run `python evaluate.py` after you've placed your results in the data folder.
The evaluation script calculates the accuracy - e.g. the percentage of correctly predicted samples.

The current 