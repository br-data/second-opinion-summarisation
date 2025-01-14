import asyncio
import json
import logging
import re
from uuid import uuid4

import uvicorn
from fastapi.responses import StreamingResponse, RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException

from newspaper.article import ArticleException
from openai import OpenAI, AsyncOpenAI

from src.auditor import Auditor
from src.config import app, LOGGING_CONFIG
from src.datastructures import (
    GenerationRequest,
    CheckResponse,
    CheckRequest,
    CheckResponseItem,
)
from src.datastructures import OpenAiModel
from src.helpers import extract_urlnews
from src.llm import handle_stream, tool_chain, call_openai_lin
from src.prompts import (
    system_prompt_honest,
    system_prompt_malicious,
    check_prompt,
    detect_language,
    check_content,
    invalid_input_response,
    english_response
)

run_id = uuid4()
client = OpenAI()
async_client = AsyncOpenAI()

answer_pat = re.compile(r"\[ANSW\](.*)\[\/ANSW\]")
reason_pat = re.compile(r"\[REASON\](.*)\[\/REASON\]")


@app.get("/", include_in_schema=False)
async def docs_redirect():
    """
    Redirects the root URL to the documentation URL.

    :returns: RedirectResponse object pointing to the /docs URL
    """
    return RedirectResponse(url="/docs")


@app.post("/completion", response_model=str)
async def completion(
        request: GenerationRequest,
        model: OpenAiModel = OpenAiModel.gpt4mini,
        honest: bool = True,
        raw_output: bool = False,
        language: str = 'German'
):
    """
    Completion endpoint for text generation.

    :param request: Input data to generate text.
    :param model: Model to be used for generation.
    :param honest: Flag to select between system prompts.
    :param raw_output: Flag to control the format of the output.
    :returns: A streaming response of generated text.
    :raises keyError: Raises an exception on key retrieval error.
    """

    # User input text
    prompt = request.source
    # Detect language and check content
    messages = [[{"role": "system", "content": detect_language}],
                [{"role": "system", "content": check_content}]]
    tasks = [call_openai_lin(prompt=prompt, messages=message, client=async_client, model=model) for message in messages]
    resp = await asyncio.gather(*tasks)
    language = json.loads(resp[0].choices[0].message.content)['language']
    content_status = json.loads(resp[1].choices[0].message.content)['content_status']
    if not content_status == "valid":
        raise HTTPException(status_code=422, detail="Invalid content")

    
    system_prompt = system_prompt_malicious

    if language == 'English':
        system_prompt += english_response

    messages = [{"role": "system", "content": system_prompt}]

    # logging.debug(request)
    response = StreamingResponse(
        handle_stream(
            tool_chain(client, request.source, messages, model=model),
            all_json= not raw_output),
        media_type="text/event-stream",
    )
    return response

@app.post("/check", response_model=CheckResponse)
def check_article_against_source(
        request: CheckRequest, model: OpenAiModel = OpenAiModel.gpt4mini, output_language = "German"
):
    """
        The endpoint compares a given article chunk against a source using an AI model to determine its validity.
    """
    # Detect language
    messages = [{"role": "system", "content": detect_language}]
    resp = call_openai_lin(prompt=request.source, messages=messages, client=client, model=model)
    input_language = resp.choices[0].message.content
    output_language = json.loads(input_language)['language']
    system_prompt_check = check_prompt if output_language == "German" else check_prompt + english_response

    fc = Auditor(request.source, request.chunk)
    logging.info(  # f'\n\nChecking against each PARAGRAPH that contains similar sentences\n\n'
        f"Input:\n{fc.input}\n\n" f"{len(fc.similar_para_id)} similar paragraph(s)\n"
    )

    answers = []

    # Joining similar paragraphs
    similar_paras = '\n\n'.join([fc.paragraphs[para_id] for para_id in fc.similar_para_id])
    
    messages = [{"role": "system", "content": system_prompt_check}]
    prompt = "Satz:\n" f"{fc.input}\n\n" "Ausgangstext:\n" f"{similar_paras}"

    resp = call_openai_lin(prompt=prompt, messages=messages, client=fc.client, model=fc.model)
    resp = resp.choices[0].message.content
    reason = re.findall(reason_pat, resp)[0]

    result = re.findall(answer_pat, resp)[0]

    answers.append(
        CheckResponseItem(
            sentence=similar_paras,
            reason=reason,
            facts_in_source=result,
        )
    )

    if (len(answers) == 0):  # No paragraphs are similar enough to be compared by the LLM
        reason = "Die Behauptung ist nicht im Text enthalten."

    # print(f'\nResult: {result}\nSentence: {request.chunk}\nReason: {reason}\nAnswers: {answers}')
    print(f'\nResult: {result}\nSentence: {request.chunk}\nReason: {reason}')
    return CheckResponse(
        id=request.id,
        input_sentence=request.chunk,
        reason=reason,
        answers=answers,
        result=result,
    )


@app.post("/extract", response_model=str)
def extract_article_from_url(url):
    """
    Handles POST requests to extract article information from a given URL.

    :param url: The URL of the article
    :returns: The JSON response containing the article headline, text, and image links, or error message on failure
    :raises: Returns a JSON response with an error message if extraction fails
    """
    try:
        headline, text, image_links = extract_urlnews(url)
    except ArticleException as e:
        return json.dumps(
            {"status": "failure", "error": f"Cannot fetch or parse the URL: {str(e)}"}
        )

    article = {"headline": headline, "text": text, "image_links": image_links}

    logging.debug(article)
    return JSONResponse(content=article)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, log_config=LOGGING_CONFIG)
