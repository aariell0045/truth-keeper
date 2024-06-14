import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import uvicorn
import json

# Your OpenAI API key should be kept secret and not exposed in the code
openai.api_key = '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'

prediction_results = []
real_results = []

# Function to calculate confidence
def calculate_confidence(logprob):
    probability = np.exp(logprob)
    return probability * 100  # Convert to percentage

def store_result(question_results, confidence_score, index):
    prediction_results.append({
        "number": index,
        "results": question_results,
        "confidence_score": confidence_score
    })

def save_results(model_name):
    with open(model_name + '_results.json', 'w') as file:
        json.dump(prediction_results, file)
    
def send_req(question, index, model_name):
    source_query = "TruthKeeper is a fake news detector bot. Return answer of True or False."
    response = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": source_query
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                max_tokens=150,
                temperature=0.7,
                logprobs=True,  # Request log probabilities
                top_logprobs=5
            )
    top_two_logprobs = response.choices[0].logprobs.content[0].top_logprobs
    confidence_score = []
    question_results = []
    for i, logprob in enumerate(top_two_logprobs):
        print(f"Output token {i}: {logprob.token}")
        question_results.append(logprob.token)

        print(f"logprobs: {i}: {logprob.logprob}")
        confidence_score.append(calculate_confidence(logprob.logprob))
        print(f"probability {i}: {confidence_score[i]}")

    store_result(question_results, confidence_score, index)


def start(file_name, model_name):
    source_jsonl = file_name

    with open(source_jsonl, 'r', encoding='utf-8-sig') as file:
        lines = file.readlines()
    
    for index, line in enumerate(lines):
            # Load JSON object from string
            data = json.loads(line)

            # Iterate over each message in the 'messages' list
            for message in data["messages"]:
                if message["role"] == "user":  # Check if the role is 'user'
                    # Replace HTTPS links in the 'content' field
                    send_req(message["content"], index, model_name)
                elif message["role"] == "assistant":
                    real_results.append({
                        "index": index,
                        "result": message["content"]
                    })

    save_results(model_name)


def compare_results(model_name):

    # Compare the first result of each object in the detailed_results with the result in simple_results
    accuracy = []
    for index, (detailed, simple) in enumerate(zip(prediction_results, real_results)):

        # Compare with the 'result' in simple_results
        is_match = detailed["results"][0] == simple["result"]
        accuracy.append({
            "index": index,
            "is_match": is_match
        })
        # print(f"Comparison for index {detailed['number']}: {is_match}")

    count_matches = 0
    for result in accuracy:
        if result["is_match"]:
            count_matches += 1

    print(f"Number of matches: {count_matches}")
    # The sentence to add at the beginning of the file
    additional_sentence = f"The number of matches is: {count_matches}\n"

    # Read the existing content of the file
    with open(model_name + '_results.json', 'r') as file:
        content = file.read()

    # Prepend the additional sentence to the content
    new_content = additional_sentence + content

    # Write the new content back to the file
    with open(model_name + '_results.json', 'w') as file:
        file.write(new_content)


start(file_name='500_test_data.jsonl',model_name="ft:gpt-3.5-turbo-0613:matan:train-data-2:9Ifdqgfp")
compare_results(model_name="ft:gpt-3.5-turbo-0613:matan:train-data-2:9Ifdqgfp")