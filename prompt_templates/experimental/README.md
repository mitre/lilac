# Additional Prompt Templates

We have explored several different options for structuring the judge prompts leveraging the incidents associated with each metric in the typology. In the end, the approach that worked best utilized key problem indicators that we derived from incidents by hand. This is the prompt structure used in the demo. All prompt templates we tried are included in this experimental folder and described below for the purposes of future research and experimentation.

## Example-based  ([Link](./example_based.py))
A prompt with a one-line definition for the metric accompanied by examples, one for each incident, including user’s input, chatbot’s output, and judge’s output. The judge is instructed to refer to the definition and examples to evaluate the given output. This example-based approach is often recommended in the AI literature (e.g., [1]), and it is the first approach we tried. If the incident report did not explicitly report an input and output, we as human experts extrapolated an input and output from the incident description.

### Example-based with custom rubric  ([Link](./example_custom_rubric.py))
Same as previous but also defining a metric-specific meaning for each 1-5 score.

## Incident-based  ([Link](./incident_based.py))
A prompt that instructs the judge to compare the text to be considered with the incidents from the database. We tried three different levels of detail: The one-line incident description only, the headline from every news report about that incident, and the first paragraph from every news report about the incident.

## Indicator-based  ([Link](./key_indicators.py))
A prompt listing “key indicators” of the problem, which we as human experts derived from the incidents. This approach was adapted from [2] Table 1, which lists specific success criteria for the judge to look for in the response. We reversed that approach to instead specify problem criteria, which we call key indicators of the problem. We slimmed down the initial prompt template for speed. This fast version is the prompt template used in the demo.

### Key indicators with incidents  ([Link](./indicators_incidents.py))
A prompt including both key indicators and incident descriptions and instructing the judge to use the key indicators to identify the problem and then use the incidents to decide whether this instance of the problem could lead to real-world consequences.

[1] https://mlflow.org/blog/llm-as-judge
[2] https://arxiv.org/html/2502.02988v1 
