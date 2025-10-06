# (C) 2025 The MITRE Corporation. All Rights Reserved.

""" metrics.py
Loads the LILAC metrics files.
"""
from os import walk
import re
from yaml import load, Loader

from prompt_templates import judge_all_in_one

class Metrics:
    """
    Loads, manages, and provides access to evaluation metrics for LILAC judge assessments.

    This class reads metric definitions from YAML files, constructs prompt templates for judge models,
    and offers utility methods for extracting scores and justifications from judge outputs.

    Attributes:
        metricInfos (dict[str, Metrics.MetricInfo]): Dictionary of loaded metrics, keyed by metric name.
    """

    class MetricInfo:
        """ 
        Represents a single evaluation metric, including its metadata, prompt template, and input variables.
        Makes it easier to pass metrics between processes.

        Attributes:
            yaml (dict): Raw YAML data for the metric.
            name (str): Name of the metric.
            icon_path (str): Path to the icon representing the metric.
            prompt (str): Judge prompt template with variables filled in.
            inputs (list[str]): List of input variable names required by the metric.
        """
        def __init__(self, text):
            """
            Initializes a MetricInfo instance from YAML data.

            Args:
                yaml (dict): Parsed YAML dictionary containing metric metadata and configuration.
            """
            yaml = load(text, Loader=Loader)
            
            # Fill in any "params" (e.g. see ki_biased.yaml)
            if "params" in yaml:
                text = text.format(**yaml["params"])
                yaml = load(text, Loader=Loader)
            
            self.yaml: dict = yaml
            self.name: str = yaml["name"]
            self.icon_path: str = yaml["icon"]
            self.prompt: str = None
            self.inputs: list[str] = []

            # Prompt templates are in ./prompt_templates.
            self.prompt = judge_all_in_one.PROBLEM_PROMPT.format(**yaml)
            self.inputs += yaml["inputs"]


    def __init__(self,
                 metrics_path: str = "./metrics", 
                 metric_filenames: list[str]|dict[str,str] = None):
        """ 
        Initializes the Metrics loader and loads metric definitions from the specified path.

        Args:
            metrics_path (str, optional): Directory containing metric YAML files. Defaults to "./metrics".
            metric_names (list[str] | dict[str, str], optional): List or dict of metric filenames to load.
                Defaults to None, loads all metrics in the directory. If a dict, renames metrics at dict key to dict value.
        """

        self.metricInfos: dict[str, Metrics.MetricInfo] = self._loadMetricInfos(metrics_path, metric_filenames)
        
    def _loadMetricInfos(self, path: str, metric_filenames: list[str]|dict[str,str] = None) -> list[MetricInfo]:
        """ Loads and returns specified metrics from the specified directory.

        Args:
            path (str): Directory containing the metric YAML files.
            metric_names (List[str] | Dict[str,str], optional): List or dict of metric filenames to load.
                Defaults to None, loads all metrics in the directory. If a dict, renames metrics at dict key to dict value
        Returns:
            List[MetricInfo]: All loaded metrics.
        """
        metrics: dict[str, Metrics.MetricInfo] = {}
        for (dirpath, dirnames, filenames) in walk(path):
            for filename in filenames:
                if filename.endswith('.yaml'):
                    metric_filename = filename[:-5]
                    if metric_filenames is None or metric_filename in metric_filenames:
                        with open(dirpath+'/'+filename, encoding="utf-8") as file:
                            content = file.read()
                            metricInfo = Metrics.MetricInfo(content)
                        print(f"Found metric file {filename}.")
                        # If metric_filenames is a dict, rename the metric in the file to the given name.
                        if isinstance(metric_filenames, dict):
                            metricInfo.name = metric_filenames[metric_filename]
                        # If a metric with this name already exists, use the filename instead.
                        if metricInfo.name in metrics:
                            metricInfo.name = metric_filename
                        metrics[metricInfo.name] = metricInfo
        return metrics

    def getMetricInfos(self, names: list[str] = None) -> list[MetricInfo]:
        """ Returns all loaded metrics or just those specified.

        Args:
            names (List[str], optional): If specified, returns only the matching metrics. Defaults to None, returning all metrics.

        Returns:
            List[EvaluationMetric]: Metrics.
        """
        if names is not None:
            return [self.metricInfos[name] for name in names]
        else:
            return list(self.metricInfos.values())

    @classmethod
    def extractDataFromJudgeOutput(cls, text):
        """
        Extracts the score and justification from the judge model's output text.

        Searches for a numeric score (1-5) and a justification section, using regular expressions.
        If no justification is found, returns the remaining text after the score as justification.

        Args:
            text (str): The raw output text from the judge model.

        Returns:
            tuple: (score (float or None), justification (str or None))
        """
        if text:
            score_end_index = -1
            if match := list(re.finditer(r"overall score.+?([1-5]\.?\d?)", text, re.DOTALL|re.IGNORECASE)):
                score = float(match[-1].group(1))
                score_end_index = match[-1].end()
            elif match := re.match(r".*?([1-5]\.?\d?)", text, re.DOTALL|re.IGNORECASE):
                score = float(match.group(1))
                score_end_index = match.end()
            else:
                score = None
                print("TEXT OUTPUT")
                print(text)
                raise IOError("Could not extract score from response.")
            
            justification = ""
            # For the justification, take everything from the last occurrence of justification: to the end.
            if match := list(re.finditer(r"justification:\s*(.*)$", text, re.DOTALL|re.IGNORECASE)):
                justification = match[-1].group(1)
            elif score_end_index >= 0:
                # If didn't find the word justification, take everything after the final score.
                justification = text[score_end_index:]
            if justification.strip() == "":
                justification = text

            return score, justification

        return None, None