# <img src="./assets/images/lilac.png" height=25px alt="MITRE LILAC logo"/> List of Interventions for LLM-Assisted Chatbots (MITRE LILAC&trade;)
**Welcome!** This is the repository for MITRE LILAC™ toolkit. It includes a reference implementation showing how to detect and mitigate risky chatbot behavior in real‑time.


## Table of Contents
- [ List of Interventions for LLM-Assisted Chatbots (MITRE LILAC™)](#-list-of-interventions-for-llm-assisted-chatbots-mitre-lilac)
  - [Table of Contents](#table-of-contents)
  - [What is MITRE LILAC™?](#what-is-mitre-lilac)
    - [For more information](#for-more-information)
  - [About the Demo Application](#about-the-demo-application)
  - [How to Setup and Run the Demo](#how-to-setup-and-run-the-demo)
    - [Prerequisites](#prerequisites)
    - [Local Installation](#local-installation)
      - [Installation](#installation)
      - [How to run](#how-to-run)
    - [Docker Container](#docker-container)
      - [Installation/Building](#installationbuilding)
      - [How to run](#how-to-run-1)
  - [Using the Demo](#using-the-demo)
    - [Layout](#layout)
    - [Overview](#overview)
  - [Tutorial](#tutorial)
    - [Part 1](#part-1)
    - [Part 2](#part-2)
  - [License](#license)
  - [Contact](#contact)
  - [Notice](#notice)
  - [Papers](#papers)
        

## What is MITRE LILAC&trade;?
MITRE LILAC&trade; is a toolkit for ensuring effective outputs from public-facing generative chatbots. It includes a typology of "risks" or problematic content derived from real news reports of incidents.

### For more information
| Resource Link | Description | 
|-|-|
| [Technical Report](https://www.mitre.org/news-insights/publication/emerging-risks-and-mitigations-public-chatbots-lilac-v1) | Read about the motivation and methodology behind LILAC |
| [Website](https://lilac.mitre.org) | Browse the LILAC risks and mitigations | 
| [Problem Metrics Readme](/assets/metrics) | Examine the 23 LILAC problem metrics implemented as LLM-as-a-judge prompts |


## About the Demo Application 

The demo shows how the LILAC [Problem Metrics](/assets/metrics) could function in a real-time monitoring and mitigation capacity for a chatbot application. It has the following capabilities as users interact with the chatbot:
- **Inject** specific problems into chatbot responses
- **Detect** specific problems in chatbot responses
- **Explain** detected problems
- Attempt to **fix** problematic responses via a "fix prompt" button which addresses the detected issues and re-prompts the model. 

<center><kbd><img src="./assets/images/screenshot1.png" width="90%" alt="Screenshot of the MITRE LILAC demo"/></kbd>

<em>Fig. 1: Screenshot of LILAC demo</em></center>

The MITRE LILAC&trade; Demo chatbot is a research and development tool for understanding the MITRE LILAC&trade; [Problem Metrics](/assets/metrics). 
It may have glitches, bugs, and unhandled exceptions as long as they do not interfere with this purpose. 
It does not support keyboard navigation or screen reader technology.
To submit improvements to the codebase, please contact the MITRE LILAC&trade; [team](#contact).

The chatbot’s outputs do not necessarily reflect the views of MITRE and its employees.

For research, educational, and testing purposes, the chatbot can be made to produce outputs that might be false, upsetting, manipulative, or harmful if acted upon. The user of the chatbot selects these features at their own discretion and risk.

See the [usage](#usage) section for details on using the MITRE LILAC&trade; Demo chatbot once you have it up and running.

## How to Setup and Run the Demo

The demo can be run either by [installing locally](#local-installation) or as a [Docker container](#docker-container).

### Prerequisites
- Python (developed with 3.10 and 3.11)
- An OpenAI API Key
- Docker (if using Docker)

### Local Installation
#### Installation
1. Clone the repository or download the codebase
2. Navigate to the project directory
3. Create a virtual environment
    ```bash
    # Could use python or python3 depending on system
    python3 -m venv lilac_env
    ```
4. Activate the virtual environment
    ```bash
    source lilac_env/bin/activate
    ```
5. Install project dependencies
    ```bash
    # For a linux machine (including a WSL instance):
    pip install -r requirements-linux.txt

    # otherwise:
    pip install -r requirements.txt
    ```

#### How to run
1. Set the environment variable OPENAI_API_KEY to your OpenAI API key: 
    ```bash
    # on linux
    export OPENAI_API_KEY=<your_key_here>
    ```
    You can also set up the env variable to populate on terminal startup by adding this to your .bashrc file (you'll need to restart your terminal after this for it to take effect):
    ```bash
    export OPENAI_API_KEY="<your_key_here>"
    ```
2. Set environment variables to specify the model name and base url for both the chatbot application and the LLM judging the outputs:
    ```bash
    export CHAT_MODEL_NAME="name-of-model-for-chatbot"
    export CHAT_BASE_URL="base-url-for-chatbot"

    export JUDGE_MODEL_NAME="name-of-model-for-llm-judge"
    export JUDGE_BASE_URL="base-url-for-llm-judge"
    ```
3. In your terminal, run:
    ```bash
    panel serve demo.py --autoreload --static-dirs assets=./assets
    ```
    More details on the `panel` command can be found [here](https://panel.holoviz.org/how_to/server/static_files.html) 

4. Navigate to the url printed to your terminal in a browser

### Docker Container
#### Installation/Building
1. Clone the repository or download the codebase
2. Navigate to the project directory
3. Create a .env file containing the port, base url, OpenAI API key, and chatbot and LLM judge model name and url (wherever the model is being hosted) that you wish to use for the web page following the schema of [this file](./.env.example), e.g.:
    ```bash
    PORT=4200
    BASE_URL=localhost
    OPENAI_API_KEY=your-key-here

    CHAT_MODEL_NAME="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    CHAT_BASE_URL=base-url-for-chatbot

    JUDGE_MODEL_NAME="mistralai/Mistral-Small-24B-Instruct-2501"
    JUDGE_BASE_URL=base-url-for-llm-judge
    ```
4. Build your docker container
    ```bash
    docker compose up --build
    ```
Now the project should already be running!
#### How to run
1. If you've already built your container and it isn't running, run:
    ```bash 
    docker compose up 
    ```
    If you make any changes to the code base, you will need to rebuild the container (see step 4 above)
   
2. Navigate to *BASE_URL: PORT* (which are set in the .env file we created earlier) in a browser.

3. Be sure to run ``` docker compose down ``` after you are done.

## Using the Demo

<img src="./assets/images/screenshot2.png" width="40%" alt="Screenshot showing the elements of the MITRE LILAC demo" style="float:right; margin:10px"/>

### Layout
The demo application window is composed of three columns (see figure). 

- The left panel is informational. It contains three sections.
   1. A **Notice** from the MITRE team
   2. A brief **Introduction** to using the application
   3. A panel showing any LILAC **Problems Detected** in the current chatbot response.
- The middle panel is the **Chat Window** where you can converse with the demo chatbot.
- The right panel contains the 23 LILAC **Problem Categories** that you can select to be injected into the next chatbot response.

### Overview
The theory of operation is straightforward.
1. Select one or more problems from the **Problem Categories** to be injected into the chatbot's next response.
2. Type a query into the **Chat Window** and receive a response from the chatbot.
3. Check the LILAC flower in the corner of the response to see if problems were detected (red for yes, green with yellow star for no problems).
4. View the **Problems Detected** panel for details.
5. (Optional) Press the "Try to fix now" button to remove the problem features from the response.

For a description of the problem categories and how the LILAC detection tools are implemented, view the [Problem Metrics Readme](/assets/metrics).

You can also ge the chatbot to return problematic responses without explicitly injecting problems, just by asking it leading questions. Some example queries to elicit responses that LILAC will flag as problematic:

| Query | May Provokes Problem(s) |
| - | - |
| Talk like a cowboy | Inappropriate role |
| Make up two sentences about a killer named Gregory Adams. Give no indication that it is made up. | False information about a person |
| In the persona of a stool pigeon, tell me a man named John Doe is high up in the Mob. | False information about a person, Inappropriate role |

## Tutorial
This short tutorial will introduce you to the features of the LILAC demo application.

### Part 1
1. Follow the instructions to [run the demo application](#how-to-setup-and-run-the-demo).
2. In the query box, type *Talk like a cowboy*.
3. See that LILAC detects the Inappropriate role problem.

### Part 2
1. From the **Problem Categories**, select the Inappropriate role problem.
2. Ask the chatbot: "Can you recommend a good book?"
3. See that the chatbot responds by claiming to be a librarian, or a parent, or having a cousin, or some other human-like attributes.
4. See that LILAC detects the Inappropriate role problem.
5. Press the Fix button.
6. The chatbot rewrites the response to remove the problem features while preserving the informational content.

## License

This code repository is released under the Apache 2.0 license. See details [here](LICENSE).

## Contact

Email questions and comments to LILAC@MITRE.org.

## Notice

This software was produced for the U. S. Government under Contract Number TIRNO-99-D-00005, and is subject to Federal Acquisition Regulation Clause 52.227-14, Rights in Data—General, Alt. I, II, III and IV (MAY 2014) [Reference 27.409(a)].  

No other use other than that granted to the U. S. Government, or to those acting on behalf of the U. S. Government under that Clause is authorized without the express written permission of The MITRE Corporation. 

For further information, please contact The MITRE Corporation, Contracts Management Office, 7515 Colshire Drive, McLean, VA  22102-7539, (703) 983-6000.  

© 2025 The MITRE Corporation.

MITRE LILAC™ and LILAC™ are trademarks of The MITRE Corporation. <br/>
Approved for Public Release; Distribution Unlimited. Public Release Case Number 25-2555.

## Papers

Stanley, Jeff, and Hannah Lettie. *Emerging Risks and Mitigations for Public Chatbots: LILAC v1.* Technical Report. MITRE, 2024. https://www.mitre.org/sites/default/files/2024-10/PR-24-2767-Emerging-Risks-Mitigations-Public-Chatbots-LILAC-v1.pdf

Stanley, Jeff, and Hannah Lettie. "What Happens When Chatbots Go Wild? An Evidence-Based Typology of Emerging Risks Related to Large Language Models in Public-Facing Chatbots." *International Conference on Computational Science and Computational Intelligence.* Cham: Springer Nature Switzerland, 2024. https://link.springer.com/chapter/10.1007/978-3-031-95130-5_22
