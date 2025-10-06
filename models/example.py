# (C) 2025 The MITRE Corporation. All Rights Reserved.

""" models.example
Defines a LILAC Example or stub model type to serve as a guide
for adding new model types.
"""
from typing import Dict, List, Any, Optional
from models.basemodel import BaseModel


class Example(BaseModel):
    """ Example class for models to test with LILAC. 
    
    From the readme: Running LILAC on a New Model
    If you want to evaluate your own model or another third-party model, 
    follow these steps:
        1. **Python file**: Create a new file in *./models*. 
        Copy *example.py* and fill in the functions according to the comments 
        to support the new model. Make sure the name of the class is the same 
        as the name as the file (except capitalized).
            - In the *config_signature*, you define the parameters that should 
            be included when configuring this model type.
            - In the *_predict* function, you call your custom model.
        2. **Config.yaml**: In *config.yaml*, add a new model config to the 
        models_to_evaluate. The type is the name of your new file. 
        Underneath type, include an entry for each item you defined in your 
        config_signature in the python file.
    """
        
    # In the config_signature, specify what parameters are expected in the model_config dictionary.
    # Should be a mapping of parameter name to default value.
    # If no default value (i.e., should throw an error if unspecified), use None.
    _config_signature: Dict[str, Any] = {
        "example_var": "default_val"
    }

    @classmethod
    def describe_config(cls, model_config: Dict[str, Any]) -> str:
        # Return a descriptive string for this model.
        return "This is an example model."
 
    def _init_from_config(self, model_config: Dict[str, Any]):
        # Set any class variables from the config
        # self.example_var = config["example_var"]
        pass

    def _predict(self, messages: List[Dict[str, str]], params: Optional[dict] = None) -> str:
        # Example input format:
        #   [{"role": "system", "content": "You are a helpful assistant."},
        #    {"role": "user", "content": "Hello."}]
        # Call your model here.
        return "Just an example response."

    def _stream(self, messages: List[Dict[str, str]], params: Optional[dict] = None) -> str:
        # Example input format:
        #   [{"role": "system", "content": "You are a helpful assistant."},
        #    {"role": "user", "content": "Hello."}]
        # Call your model here.
        return "Just an example response."