import openai
import json
import os
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = "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"
client = openai.OpenAI(api_key=openai.api_key)

GPT_MODEL = "gpt-3.5-turbo-1106"
EMBEDDING_MODEL = "text-embedding-ada-002"


def get_input(prompt, input_type=str):
    """Function to get user input and convert it to the specified type."""
    while True:
        try:
            return input_type(input(prompt))
        except ValueError:
            print(f"Please enter a valid {input_type.__name__}.")


def get_firstRound_info(AcneType, duration, check_oily_skin, check_itchiness_or_pain):
    if AcneType is None:
        AcneType = get_input("Enter AcneType (Acne, Acne_Scar, Both): ", str)

    if duration is None:
        duration = get_input("Enter the duration that the problem lasts: ", str)

    if check_oily_skin is None:
        check_oily_skin_input = get_input("Do you have oily skin? (yes/no): ", str)
        check_oily_skin = check_oily_skin_input.strip().lower() == "yes"

    if check_itchiness_or_pain is None:
        check_itchiness_or_pain = get_input("Do you have itchiness or pain? (yes/no): ", str)

    firstRound_info = {
        "AcneType": AcneType,
        "duration": duration,
        "check_oily_skin": check_oily_skin,
        "check_itchiness_or_pain": check_itchiness_or_pain,
    }
    return json.dumps(firstRound_info)


def get_secondRound_info(pic, check_squeezing_acne, strategy):
    secondRound_info = {
        "pic": pic,
        "check_squeezing_acne": check_squeezing_acne,
        "strategy": strategy
    }
    return json.dumps(secondRound_info)


@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + openai.api_key,
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e


class Conversation:
    def __init__(self):
        self.conversation_history = []

    def add_message(self, role, content):
        message = {"role": role, "content": content}
        self.conversation_history.append(message)


main_functions = [
    {
        "name": "get_firstRound_info",
        "description": "Get the first round information. Always check if each parameter is satisfied, and if not, "
                       "ask in turn",
        # 获得第一轮诊断所需要的信息
        "parameters": {
            "type": "object",
            "properties": {
                "AcneType": {
                    "type": "string",
                    "enum": ["Acne", "Acne_Scar", "Both"],
                    "description": "The problem user want to solve, e.g. Acne",
                },
                "duration": {
                    "type": "string",
                    "description": "The duration that the problem lasts"
                },
                "check_oily_skin": {
                    "type": "string",
                    "description": "Check user has a oily skin or not",
                },
                "check_itchiness_or_pain": {
                    "type": "string",
                    "description": "Check if user have itchiness or pain",
                }
            }

        },

        "required": ["AcneType", "duration", "check_oily_skin", "check_itchiness_or_pain"],
    },
    {
        "name": "get_secondRound_info",
        "description": "Get the second round info, You should NEVER call this function before get_firstRound_info "
                       "has been called in the conversation.",
        # 获取最终诊断信息
        "parameters": {
            "type": "object",
            "properties": {
                "pic": {
                    "type": "string",
                    "description": "Pic with symptoms",
                },
                "check_squeezing_acne": {
                    "type": "boolean",
                    "description": "Check the useer squeeze acne or not.",
                },
                "strategy": {
                    "type": "boolean",
                    "description": "Check if user answered their skin care strategy",
                }
            },
            "required": ["pic", "check_squeezing_acne", "strategy"]
        },
    }

]


def chat_completion_with_function_execution(messages, functions=[None]):
    response = chat_completion_request(messages, functions)
    print(f'response:{response}')
    if response.status_code == 200:
        try:
            full_message = response.json()["choices"][0]
            print(f"full_message{full_message}")
            if full_message["finish_reason"] == "function_call":
                print(f"Function generation requested, calling function")
                return call_main_round_function(messages, full_message)
            else:
                print(f"Function not required, responding to user")
                return response.json()
        except KeyError:
            print(response.json())
            return None
    else:
        print(f"API Request failed with status code: {response.status_code}")
        print(response.text)
        return None


def call_main_round_function(messages, full_message):
    if full_message["message"]["function_call"]["name"] == "get_firstRound_info":
        try:
            parsed_output = json.loads(
                full_message["message"]["function_call"]["arguments"]
            )
            print("Getting First Round Info")

            AcneType = parsed_output.get("AcneType")
            duration = parsed_output.get("duration")
            check_oily_skin = parsed_output.get("check_oily_skin")
            check_itchiness_or_pain = parsed_output.get("check_itchiness_or_pain")

            results = get_firstRound_info(AcneType, duration, check_oily_skin, check_itchiness_or_pain)

            print(f'results:{results}')
        except Exception as e:
            print(parsed_output)
            print(f"Function execution failed")
            print(f"Error message: {e}")
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(results),
            }
        )
        try:
            print("Got first round info, getting second round info")  # 更改
            response = chat_completion_request(messages)
            print(f'response:{response.json}')
            return response.json()
        except Exception as e:
            print(type(e))
            raise Exception("Function chat request failed")

    # elif (
    #         full_message["message"]["function_call"]["name"] == "get_secondRound_info"
    # ):
    #     parsed_output = json.loads(
    #         full_message["message"]["function_call"]["arguments"]
    #     )
    #     print("Getting second round info")
    #     summary = get_secondRound_info(parsed_output["query"])
    #     return summary

    else:
        raise Exception("Function does not exist and cannot be called")


iry_system_message = """You are IRYGPT, a helpful assistant to guide user to purchase facial skin care products.Don't 
make assumptions about what values to plug into functions. Ask for clarification if a user request is 
ambiguous.Answer in Chinese. Begin!"""
iry_conversation = Conversation()
iry_conversation.add_message("system", iry_system_message)

while True:
    user_input = input("Enter your message: ")
    iry_conversation.add_message("user", user_input)
    chat_response=chat_completion_with_function_execution(
        iry_conversation.conversation_history, functions=main_functions
    )
    print(chat_response)
    assistant_message = chat_response["choices"][0]["message"]["content"]
    iry_conversation.add_message("assistant",assistant_message)
    print(assistant_message)
