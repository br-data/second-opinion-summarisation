This repo provides the summarisation functionality for the second opinion demo.

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

## Evaluation
To run the evaluation simply run `python evaluate.py` after you've placed your results in the data folder.
The evaluation script calculates the accuracy - e.g. the percentage of correctly predicted samples.

The current 
