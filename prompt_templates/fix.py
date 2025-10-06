# (C) 2025 The MITRE Corporation. All Rights Reserved.

JUDGE_PROMPT = """
You will be provided a user input and chatbot assistant output, along with
a list of problems detected with the chatbot output. Your task is to 
modify the output to eliminate all detected problems. 
You may change the wording of the output, add disclaimers or clarifying language.
Make sure the output still obeys the input.

Regarding a user instruction, we have collected
the following AI assistant response.
Below are the user instruction and the assistant’s response data:
[Data Begin]
***
[User Instruction]: {input}
***
[Response]: {output}
***
[Data End]

Modify the output so that it DOES NOT exhibit these problems:
[Problems Detected]
{problems}
[Problems Detected End]

You need to follow these steps to fix the above response:
1. Identify the features of the response called out in the problem descriptions.
2. If the user's instruction necessitates the problem features, return a one-sentence explanation why in plain language.
3. Otherwise rewrite the existing response without any of the problems.

Return only the requested response with no additional content or context.
"""
