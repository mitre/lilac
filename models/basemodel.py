# (C) 2025 The MITRE Corporation. All Rights Reserved.

from __future__ import annotations
import re


class BaseModel():
    """ 
    Base class for models to test with LILAC that abstracts away a lot of the
    functionality of the model and makes it simple to add new model types.
    
    From the readme: Running LILAC on a New Model
    If you want to evaluate your own model or another third-party model, 
    follow these steps:
        1. **Python file**: Create a new file in *./models*. 
        Copy *example.py* and fill in the functions according to the comments 
        to support the new model. Make sure the name of the class is the same 
        as the name as the file (except for capitalization).
            - In the *config_signature*, you define the parameters that should 
            be included when configuring this model type.
            - In the *_predict* function, you call your custom model.
        2. **Config.yaml**: In *config.yaml*, add a new model config to the 
        models_to_evaluate. The type is the name of your new file. 
        Underneath type, include an entry for each item you defined in your 
        config_signature in the python file.
    """

    _model_cache: dict[str, BaseModel] = {}

    # config_signature: Override this.
    # In the config_signature, specify what parameters are expected in the model_config dictionary.
    # Should be a mapping of parameter name to default value.
    # If no default value (i.e., should throw an error if unspecified), use None.
    _config_signature: dict[str, any] = {
    }

    def __init__(self, model_config:dict[str, any]=None):
        # Define any instance variables for this class.
        # self.example_var = None
        if model_config is not None:
            self.model_config = self.validate_config(model_config)
        else:
            self.model_config = dict(self._config_signature)
        self._init_from_config(self.model_config)

    def describe(self) -> str:
        """Returns a string description for this model from its config.

        Returns:
            str: Model description
        """
        return self.describe_config(self.model_config)

    def _init_from_config(self, model_config: dict[str, any]):
        """ Override this.
        Set any class variables from the config.
        self.example_var = config["example_var"]

        Args:
            model_config (Dict[str, Any]): The model config, keys to values.
        """
        pass

    def predict(self, messages: str|list[dict[str, str]]) -> str:
        """Takes an input and returns a prediction from the model.
        https://www.mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html#mlflow.pyfunc.PythonModel.predict

        Args:
            messages (str | list[dict[str, str]]): User prompt or list of input messages.
                Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Raises:
            TypeError: model_input is the wrong type.

        Returns:
            str: The text output from the model.
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        # Pass the messages into the chat client and parse the response.
        return self._predict(messages)

    def _predict(self, messages: list[dict[str, str]]) -> str:
        """ Override this.
        Internal function for processing inputs and returning output.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries 
                representing the conversation history. Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Returns:
            str: text output
        """
        return "This is just an example response."
    
    def stream(self, messages: list[dict[str, str]]):
        """
        Takes input messages and streams the model's response.

        Args:
            messages (list[dict[str, str]]): List of input message dictionaries 
                representing the conversation history. Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Yields:
            str: Chunks of the model's response as they are received.
        """
        result = ""
        for response in self._stream(messages):
            if response:
                result += response
                yield result
            else:
                continue
    
    def _stream(self, messages: list[dict[str, str]]):
        """ Override this.
        Internal function for processing inputs and returning output.
        
        Args:
            messages (list[dict[str, str]]): List of input message dictionaries 
                representing the conversation history. Example format:
                [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello."}]

        Yields:
            str: Chunks of the model's response as they are received.
        """
        yield "This is just an example response."
    
    @classmethod
    def get_uri_name(cls, model_config: dict[str, any]) -> str:
        """
        Utility function for constructing a uri name for this model.
        The uri_name is how the model will be logged.
        Create the uri name using whatever information you want from the model_config.

        Args:
            model_config (Dict[str,Any]): Any parameters needed for this class's load_context function.

        Returns:
            str: uri name
        """
        model_config = cls.validate_config(model_config)
        uri_name = cls.describe_config(model_config)
        uri_name = re.sub(r'[^\w\d]', '_', uri_name.lower())
        return uri_name
    
    @classmethod
    def validate_config(cls, model_config: dict[str, any]) -> dict[str, any]:
        """ Given a config, checks to make sure it includes all expected
        variables and attempts to fill in any missing variabes with defaults.
        Raises a KeyError if it cannot fill in all the variables.
        
        Args:
            model_config (Dict[str, Any]): user-defined parameters for this class

        Returns:
            model_config (Dict[str, Any]): filled in parameters
        """
        for key, val in cls._config_signature.items():
            if key not in model_config:
                if val is not None:
                    # print(f"""{key} not found in config. Adding default value: {val}""")
                    model_config[key] = val
                else:
                    raise KeyError(f"""{key} is required in config.""")
        return model_config

    @classmethod
    def describe_config(cls, model_config: dict[str, any]) -> str:
        """ Override this.
        Given a config, returns a helpful string to describe this model.
        The model will be saved with this uri in the run, and it will appear
        in the run name. The descriptor should distinguish different models in 
        an experiment.
        
        Args:
            model_config (Dict[str, Any]): user-defined parameters for this class

        Returns:
            str: descriptive identifier for this model
        """
        return "base"
