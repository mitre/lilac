# (C) 2025 The MITRE Corporation. All Rights Reserved.

from openai import OpenAI
from models.basemodel import BaseModel
import os

api_key = os.environ['OPENAI_API_KEY']

class OpenAIModel(BaseModel):
    """
    Represents an OpenAI-compatible chat model interface initialized via configuration dictionary, 
    supporting both standard and streaming completions. It is designed to be easily configurable 
    and extendable for different OpenAI endpoints and models.

    Users must specify at least model_name and base_url in the configuration dictionary.

    Attributes:
        model_name (str): Name of the OpenAI model to use.
        base_url (str): Base URL for the OpenAI API endpoint.
        system_prompt (str): System prompt prepended to all conversations. Defaults to: "You are a helpful assistant."
        client (OpenAI): Initialized OpenAI client for API requests.
    """
    # In the config_signature, specify what parameters are expected in the model_config dictionary.
    # Should be a mapping of parameter name to default value.
    _config_signature: dict[str, any] = {
        "model_name": None,
        "base_url": None,
        "system_prompt": "You are a helpful assistant."
    }

    @classmethod
    def describe_config(cls, model_config: dict[str, any]) -> str:
        """
        Returns a text description of the model configuration.

        Args:
            model_config (dict): Model configuration dictionary.

        Returns:
            str: Description of the model and its system prompt.
        """
        # Return a descriptive string for this model.
        return f"""OpenAI {model_config["model_name"]}: {model_config["system_prompt"]}"""
        
    def _init_from_config(self, model_config: dict[str, any]):
        """
        Initializes the model instance from the given configuration dictionary:

            Configuration Parameters:
                model_name (str): Name of the OpenAI model to use.
                base_url (str): Base URL for the OpenAI API endpoint.
                system_prompt (str): System prompt prepended to all conversations. Defaults to: "You are a helpful assistant."

        Configuration must specify at least 'model_name' and 'base_url'.

        Args:
            model_config (dict): Dictionary containing 'model_name', 'base_url', and 'system_prompt'.
        """
        # Set any class variables from the config
        self.model_name = model_config["model_name"]
        self.base_url = model_config["base_url"]
        self.system_prompt = model_config["system_prompt"]
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=api_key
        )

    def _predict(self, messages: list[dict[str, str]]) -> str:
        """
        Takes input messages and returns a prediction from the model.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries 
                representing the conversation history. Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Returns:
            str: The content of the model's response.
        """
        # Add the system prompt.
        messages = [{"role": "system", "content": self.system_prompt}] + messages
        chat_completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )
        return chat_completion.choices[0].message.content

    def _stream(self, messages: list[dict[str, str]]):
        """
        Takes input messages and streams the model's response.

        Args:
            messages (list[dict[str, str]]): List of message dictionaries 
            representing the conversation history. Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Yields:
            str: Chunks of the model's response as they are received.
        """
        # Add the system prompt.
        messages = \
            [{"role": "system", "content": self.system_prompt}] + messages
        print("STREAM MESSAGE")
        print(messages)
        print(self.model_name)
        print(self.base_url)
        chat_completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )
        # Iterate and print stream
        for chunk in chat_completion:
            yield chunk.choices[0].delta.content