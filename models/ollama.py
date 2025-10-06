# (C) 2025 The MITRE Corporation. All Rights Reserved.

import ollama
from models.basemodel import BaseModel

class Ollama(BaseModel):
    """
    Represents an Ollama-compatible chat model interface initialized via configuration dictionary, 
    supporting both standard and streaming completions. It is designed to be easily configurable 
    and extendable for different Ollama models.

    Attributes:
        model_name (str): Name of the Ollama model to use (defaults to 'mistral')
        system_prompt (str): System prompt prepended to all conversations. Defaults to: "You are a helpful assistant."
        keep_alive (str): Amount of time model will be kept in memory. Defaults to '4m'.
        client (ollama.Client): Initialized Ollama client for API requests.
    """
    # In the config_signature, specify what parameters are expected in the model_config dictionary.
    # Should be a mapping of parameter name to default value.
    _config_signature: dict[str, any] = {
        "model_name": "mistral",
        "system_prompt": "You are a helpful assistant.",
        "keep_alive": "4m"
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
        return f"""ollama {model_config["model_name"]}: {model_config["system_prompt"]}"""
        
    def _init_from_config(self, model_config: dict[str, any]):
        # Set any class variables from the config
        # self.example_var = config["example_var"]
        self.model_name = model_config["model_name"]
        self.system_prompt = model_config["system_prompt"]
        self.keep_alive = model_config["keep_alive"]
        self.client = ollama.Client()

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
        response = self.client.chat(
            model=self.model_name, messages=messages, keep_alive=self.keep_alive
        )
        return response["message"]["content"]

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
        response = self.client.chat(
            model=self.model_name, messages=messages, keep_alive=self.keep_alive, stream=True
        )
        for chunk in response:
            yield chunk["message"]["content"]