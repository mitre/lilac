# (C) 2025 The MITRE Corporation. All Rights Reserved.

from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from functools import total_ordering
import random
import os
import panel as pn

import param
from panel.reactive import ReactiveHTML
from panel.viewable import Viewable
from panel.theme import Design, Inherit
from panel.chat import ChatInterface
import models.basemodel
import models.openaimodel
from metrics import Metrics
from prompt_templates import judge_all_in_one, respond, fix

"""
Consts
"""
ASSISTANT_NAME = "Assistant"
# logo image paths
LILAC_IMAGE_NORMAL = "assets/images/lilac.png"
LILAC_IMAGE_PASS = "assets/images/lilac_yellow_star.png"
LILAC_IMAGE_FAIL = "assets/images/lilac_red.png"
LILAC_IMAGE_LOADING = "assets/images/lilac.png"
# Any judge result this value or greater is a problem.
PROBLEM_THRESHOLD = 3

"""
Configuring Panel
"""
# Set Panel to use our own stylesheet.
pn.extension()
class MyDesign(Design):
    modifiers = {
        Viewable: {
            'stylesheets': [Inherit, 'assets/styles/styles1.css']
        }
    }
pn.config.design = MyDesign

pn.config.nthreads = 3
pn.chat.message.DEFAULT_AVATARS["LILAC"] = LILAC_IMAGE_NORMAL
pn.chat.message.DEFAULT_AVATARS["User"] = "👤"
pn.chat.ChatMessage.show_reaction_icons = False
pn.chat.ChatMessage.show_copy_icon = False

"""
Globals
"""
selected_exchange: LILACExchange = None
displayed_exchange: LILACExchange = None
chat_interface: pn.chat.ChatInterface = None
issues_card = None
issues_summary = None
issues_fix_button = None
problems_selection: pn.widgets.CheckBoxGroup = None

executor = ThreadPoolExecutor(max_workers=7)

# This is what's passed in as context to the LLM each time.
history: list[dict] = []
# This is our history of LILACExchange objects.
exchanges: list[LILACExchange] = []
# Load the LILAC metrics from the assets/metrics folder.
metrics: Metrics = Metrics('assets/metrics')
# load the chatting model name and base url from the environment variables
chat_model_name = os.environ['CHAT_MODEL_NAME']
chat_base_url = os.environ['CHAT_BASE_URL']
# Initialize the model to chat with.
chatter: models.basemodel.BaseModel = models.openaimodel.OpenAIModel({
    "model_name": chat_model_name,
    "base_url": chat_base_url,
    "system_prompt": "You are a helpful assistant."
})
# load the judge model name and base url from the environment variables
judge_model_name = os.environ['JUDGE_MODEL_NAME']
judge_base_url = os.environ['JUDGE_BASE_URL']
# Initialize the judge model.
judge: models.basemodel.BaseModel = models.openaimodel.OpenAIModel({
    "model_name": judge_model_name,
    "base_url": judge_base_url,
    "system_prompt": "You are a helpful assistant."
})

# Make a big list of all the problem features from all the metrics.
# We'll choose some randomly to inject every time the assistant responds.
all_problem_features: list[str] = [problem_feature for problem in metrics.getMetricInfos() for problem_feature in problem.yaml["key_indicators"]]

"""
Classes
"""
class LILACImage(ReactiveHTML):
    """
    A custom HTML component for displaying the LILAC logo in the corner of assistant responses, built with Panel's ReactiveHTML. 

    The logo will change its appearance based on evaluation state (pass, fail, loading), and can respond to click events
    by registering a watcher (instructions for that can be found here: panel.holoviz.org/how_to/links/watchers.html).

    Attributes:
        object (str): Path to the image file representing the LILAC logo.
        clicks (int): Number of times the image has been clicked.
        classes (str): CSS classes applied to the image for styling and animation.
    
    """

    # Path to the current image file
    object = param.String(LILAC_IMAGE_NORMAL)
    # For handling the click event.
    clicks = param.Integer(default=0)
    # For css styling (e.g. animation)
    classes = param.String(" hidden")
    # LILACImage is shown with the following html.
    _template = """
    <div style="width:50px;height:50px;position:relative;">
        <img id="lilacimg_el" class="${classes}" src="${object}" onclick="${on_click}" style="position:absolute;width:50px;height:50px;margin:auto;cursor:pointer;"></img>
    </div>
    """
    def set_normal(self):
        """Sets the logo to the normal LILAC image."""
        self.object = LILAC_IMAGE_NORMAL

    def set_problem(self):
        """Sets the logo to the problem LILAC image"""
        self.object = LILAC_IMAGE_FAIL

    def set_pass(self):
        """Sets the logo to the passing LILAC image."""
        self.object = LILAC_IMAGE_PASS

    def hide(self):
        self.classes += " hidden"

    def _show(self):
        self.classes = self.classes.replace(" hidden", "")

    def start_loading(self):
        """Shows the logo and adds the spin animation"""
        self._show()
        self.classes += " spin"

    def stop_loading(self):
        """Stops the logo from spinning"""
        self.classes = self.classes.replace(" spin", "")

    def on_click(self, event):
        """Increments the click counter."""
        # This is how Panel does click events.
        self.clicks += 1


@total_ordering
class LILACEval():
    """
    Represents the evaluation result for a single LILAC metric, including the judge's output, 
    extracted score, justification, and any errors encountered during evaluation.

    Attributes:
        metric_info (Metrics.MetricInfo): Information about the evaluated metric, such as name and icon path.
        icon_path (str): Path to the icon representing the metric, specified in the metric yaml file.
        name (str): Name of the metric.
        judge_output (str): Raw output from the judge for this metric.
        justification (str): Explanation or reasoning extracted from the judge's output.
        score (float): Numeric score extracted from the judge's output, 
            describing the level of problem detected based on the prompt template.
        error (Exception, optional): Any error encountered during evaluation (default is None). 
    """
    def __init__(self, metric_info: Metrics.MetricInfo, judge_output: str, error: Exception = None):
        """
        Initializes a LILACEval instance with metric information, judge output, and optional error. 
        Extracts the judge output into the LILACEval attributes.

        Args:
            metric_info (Metrics.MetricInfo): The metric being evaluated, containing metadata such as name and icon path.
            judge_output (str): The raw output provided by the judge for this metric.
            error (Exception, optional): An exception object if an error occurred during evaluation (default is None).
        """
        self.metric_info: Metrics.MetricInfo = metric_info
        self.icon_path: str = metric_info.icon_path
        self.name: str = metric_info.name
        self.judge_output: str = judge_output
        score, justification = Metrics.extractDataFromJudgeOutput(judge_output)    
        self.justification: str = justification
        self.score: float = score
        self.error: Exception = error

    def __lt__(self, other):
        # Higher scores should come first.
        return (-self.score, self.name) < (-other.score, other.name)

    def __eq__(self, other):
        return (self.score, self.name) == (other.score, other.name)


class LILACExchange():
    """
    Represents a single exchange between a user and the model, including the input prompt,
    Assistant model response, judge evaluations, revision history, 
    and relevant UI elements for display and interaction (UI integrated with Panel).
    """
    # Private Attributes:
        # _user_input (str): The user's input prompt.
        # _model_output (str): The model's (Assistant's) response string.
        # _evaluating (bool): Whether the judge is currently evaluating the model output.
        # _lilac_evals (list[LILACEval]): All judge evaluation results for this exchange.
        # _lilac_issues (list[LILACEval]): Judge evaluation results flagged as problematic.
        # _revisions (list[str]): Revision history of the model's output.
        # _assistant_message (pn.chat.ChatMessage): UI element containing the Assistant's response.
        # _lilac_image (LILACImage): LILAC logo displayed in the corner of the Assistant's response.
        # _output_box (pn.pane.Markdown): Markdown pane displaying the Assistant's response text.

    def __init__(self, input: str, output_message: pn.chat.ChatMessage):
        """
        Initializes a LILACExchange instance with the user's input and the model's response message, 
        setting up the evaluation state, revision history, and all associated UI elements
        including the LILAC logo and formatted output box. 
        
        It also attaches an event watcher to the logo for handling user interactions, allowing the user to select 
        an exchange by clicking on the logo. The selected exchange will have its issues (if any) displayed in the sidebar
        and will be utilized for any other actions (i.e. fixing).

        Args:
            input (str): The user's input prompt.
            output_message (pn.chat.ChatMessage): The UI element containing the model's response.
        """
        # String the user typed
        self._user_input: str = input
        # String the model (Assistant) returned
        self._model_output: str = output_message.object
        # Whether the judge is evaluating this model output
        self._evaluating: bool = False
        # All judge results
        self._lilac_evals: list[LILACEval] = []
        # Judge results deemed problematic
        self._lilac_issues: list[LILACEval] = []
        self._revisions: list[str] = [output_message.object]
        
        # The UI element containing the Assistant's response.
        self._assistant_message: pn.chat.ChatMessage = output_message
        # The LILAC logo that sits in the corner of the Assistant's response.
        self._lilac_image: LILACImage = LILACImage(height=50)
        # Register the event watcher for selecting the exchange to update the sidebar
        self._lilac_image.param.watch(lambda event: set_selected_exchange(self), ["clicks"])
        # The Markdown box containing the text of the Assistant's response.
        self._output_box: pn.pane.Markdown = pn.pane.Markdown(self._assistant_message.object, styles={"box-shadow": "unset"})
        # Recreate the Assistant's message to look how we want it.
        self._assistant_message.object = pn.layout.FlexBox(
            self._output_box, 
            self._lilac_image,
            css_classes=["assistantMessage"],
            flex_wrap="nowrap",
            align_content="end",
            align_items="start"
            )
    
    def get_input(self) -> str:
        return self._user_input
    
    def get_output(self) -> str:
        return self._model_output
    
    def set_output(self, text: str):
        """
        Change the text of the Assistant's response, add new response to revision history,
        clear previous judge evaluation results and issues, and reset the logo.

        Args:
            text (str): The new response text.
        """
        self._model_output = text
        self._output_box.object = text
        self._revisions.append(text)
        # Clear all judge results
        self._lilac_evals.clear()
        self._lilac_issues.clear()
        # Reset the status of the LILAC logo
        self._lilac_image.set_normal()

    def select(self):
        """Mark this exchange as currently selected in the UI."""
        self._assistant_message.object.css_classes = ["assistantMessageSelected"]
 
    def unselect(self):
        """Mark this exchange as unselected in the UI."""
        self._assistant_message.object.css_classes = ["assistantMessage"]

    def start_evaluating(self):
        """Flag that this response is currently being evaluated."""
        self._evaluating = True
        self._lilac_image.start_loading()

    def stop_evaluating(self):
        """Flag that evaluation is finished for this response."""
        self._evaluating = False
        self._lilac_image.stop_loading()
        if len(self._lilac_issues) == 0:
            self._lilac_image.set_pass()
        else:
            self._lilac_image.set_problem()

    def add_eval(self, eval: LILACEval):
        """Add a judge evaluation to this response."""
        self._lilac_evals.append(eval)

    def add_issue(self, eval: LILACEval):
        """Add a judge evaluation with a detected issue to this response and update the logo."""
        self._lilac_issues.append(eval)
        self._lilac_image.set_problem()

    def get_num_issues(self) -> int:
        return len(self._lilac_issues)
    
    def get_issues(self) -> list[LILACEval]:
        return self._lilac_issues
    
    def is_evaluating(self) -> bool:
        return self._evaluating

"""
Functions for LILAC processes
"""        
def lilac_fix(event):
    """
    Grabs the selected Assistant model response from the UI and attempt to fix it so that it no longer exhibits the documented problems.

    This function:
        - Uses the selected response and its issues identified in the judge evaluation to construct a prompt for the judge model.
        - Requests a revised response from the judge model.
        - Updates the exchange with the fixed response and refreshes relevant UI elements.
        - Re-evaluates the new response to check if issues have been resolved.

    Args:
        event: The triggering event. If None, the function does nothing.
    """
    if not event:
        return
    exchange = selected_exchange
    issues_summary.object = "Fixing..."
    exchange._lilac_image.start_loading()
    # Fill in the fix prompt template.
    judge_input = fix.JUDGE_PROMPT.format(
        input=exchange.get_input(), 
        output=exchange.get_output(), 
        problems="\n\n".join([
            f"""-- {lilac_eval.name} --\n{lilac_eval.metric_info.yaml["key_indicators"]}""" for lilac_eval in exchange.get_issues()
        ]))
    # Ask the judge model for a new fixed response
    judge_output = judge.predict(judge_input)
    exchange._lilac_image.stop_loading()
    # Update the response to the judge's suggestion.
    exchange.set_output(judge_output)
    # Reset the info in the side panel.
    update_side_panel()
    # Re-evaluate using the new response.
    issues_summary.object = "Re-evaluating..."
    lilac_start_eval(exchange)

def lilac_do_eval_wrapper(exchange: LILACExchange):
    """
    Wraps a function that performs judge evaluations for the given exchange and all available metrics, updating 
    the UI as needed. The wrapper enables multithreaded execution, allowing evaluations to run concurrently 
    while the Assistant model continues chatting.

    When called, the returned function:
        - Sets the exchange to "evaluating," updating the UI.
        - Retrieves all available metrics and evaluates each on its own thread.
        - Adds each metric evaluation to the exchange as it completes.
        - Identifies issues based on the evaluation score and score threshold set in the globals above or any encountered errors.
        - Updates the side panel with results once all evaluations are complete.

    Args:
        exchange (LILACExchange): The exchange to evaluate.

    Returns:
        Callable[[], None]: A function that starts the evaluations and updates the UI when called.
    """

    def lilac_do_eval():
        # Flag the exchange as currently evaluating.
        exchange.start_evaluating()
        # If this is the currently selected exchange make sure to
        # update the side panel so it says "Evaluating".
        if exchange == selected_exchange:
            update_issues_summary()
        
        issue_count: int = 0

        problem_prompts = "\n".join([metric_info.prompt for metric_info in metrics.getMetricInfos()])
        judge_input = judge_all_in_one.JUDGE_PROMPT.format(problems=problem_prompts, context=str(history[:-2]), input=exchange.get_input(), output=exchange.get_output())
        #print(judge_input)
        judge_output = judge.predict(judge_input)
        print(judge_output)
        final_output_start = judge_output.index("FINAL OUTPUT")
        evals: dict[str:LILACEval] = {}
        for eval_line in judge_output[final_output_start:].split("\n")[1:]:
            result = eval_line.split("|")
            try:
                metric = metrics.getMetricInfos([result[0]])[0]
                evals[result[0]] = LILACEval(metric, f"score: {result[1]}\n justification: {result[2]}")
            except KeyError:
                # Could be no problems detected, or could be an invalid problem name.
                metric = None
                print(f"Metric not found for {eval_line}.")

        for lilac_eval in sorted(list(evals.values())):
            exchange.add_eval(lilac_eval)
            # Handle detected problems and errors encountered during evaluation.
            if lilac_eval.score >= PROBLEM_THRESHOLD or lilac_eval.error:
                issue_count += 1
                exchange.add_issue(lilac_eval)
                # updates the sidebar if the evaluated exchange is currently selected
                if exchange == selected_exchange:
                    update_issues_summary()
                    issues_card.append(
                        (
                            f"""
                            <img src="/assets/images/faces/{lilac_eval.icon_path}" alt="{lilac_eval.name} icon" class="emoticon">
                            {lilac_eval.name} (Score {round(lilac_eval.score)} out of 5)
                            """, 
                            lilac_eval.justification
                        )
                    )
                    if issue_count == 1:
                        issues_card.active = [0]
        # When all done, stop and update the side panel one last time.
        exchange.stop_evaluating()
        if exchange == selected_exchange:
            update_issues_summary()
    return lilac_do_eval

def lilac_start_eval(exchange: LILACExchange):
    """
    Initiates judge evaluation on a model response for the given exchange.

    Gets the evaluation function from lilac_do_eval_wrapper and immediately executes it.
    Currently runs synchronously, but could be modified to run asynchronously if desired.

    Args:
        exchange (LILACExchange): The exchange to evaluate.
    """
    # Set it off on its own thread so the user can keep chatting.
    #future = executor.submit(lilac_do_eval_wrapper(exchange))
    # Use this line instead to run synchronously.
    lilac_do_eval_wrapper(exchange)()

def set_selected_exchange(exchange: LILACExchange):
    """
    Change which exchange is currently selected, unselecting any currently selected exchange, 
    setting the global variable to the given exchage, and updating the side panel to show the judge
    evaluation for the new exchange.

    Args:
        exchange (LILACExchange): Exchange to select
    """
    global selected_exchange
    if selected_exchange != exchange:
        if selected_exchange is not None:
            selected_exchange.unselect()
        clear_side_panel()
        selected_exchange = exchange
        selected_exchange.select()
        update_side_panel()

def update_issues_summary():
    """
    Updates just the issues summary (X issues detected)
    portion of the side panel to match the selected exchange.
    """
    summary_text = ""
    if selected_exchange.is_evaluating():
        summary_text = "Evaluating. "
    issue_count = selected_exchange.get_num_issues()
    if issue_count == 0:
        summary_text += "0 issues detected."
    elif issue_count == 1:
        summary_text += "1 issue detected. Click item below for details."
    else:
        summary_text += f"{issue_count} issues detected. Click items below for details."
    issues_summary.object = summary_text
    issues_fix_button.visible = (not selected_exchange.is_evaluating()) and (issue_count > 0)

def update_side_panel():
    """ 
    Updates the entire side panel to match the selected exchange, including the issues summary section 
    and the issues card that displays metric names, icons, and scores, and displays key indicators on click.
    """
    update_issues_summary()
    issues_card.clear()
    for issue in selected_exchange.get_issues():
        issues_card.append(
            (
                f"""
                <img src="/assets/images/faces/{issue.icon_path}" alt="{issue.name} icon" class="emoticon">
                {issue.name} (Score {round(issue.score)} out of 5)
                """, 
                issue.justification
            )
        )

def clear_side_panel():
    """Clears the side panel."""
    issues_card.clear()
    issues_summary.object = ""
    issues_fix_button.visible = False

def assistant_say(content: str):
    """ 
    Adds an Assistant message not in response to any user input, for instance at the beginning of the chat.
    Includes the message in the chat history and creates an exchange instance, which is then selected.

    Does not display a LILAC logo in the corner.

    Args:
        content (str): Message for the assistant to say.
    """
    chat_interface.send(content, user=ASSISTANT_NAME, respond=False)
    history.append({"role": "user", "content": "[No user input]"})
    history.append({"role": "assistant", "content": content})
    exchange = LILACExchange("[No user input]", chat_interface[-1])
    exchanges.append(exchange)
    set_selected_exchange(exchange)

def get_random_problem_indicators(num=5) -> str:
    """Returns a number of random problem indicators from the available metrics.
    
    Args:
        num (int): Number of random problem indicators to return (5 by default)"""
    problem_features = random.sample(all_problem_features, num)
    print("PROBLEM FEATURES")
    print(problem_features)
    return ", ".join(problem_features).replace("The AI", "You")

def get_selected_problem_indicators(num=5) -> str:
    """Returns a number of random problem indicators from the metrics selected in the right panel.
    
    Args:
        num (int): Number of random problem indicators to return (5 by default)"""
    if len(problems_selection.value) == 0:
        return None
    problem_metrics = metrics.getMetricInfos(problems_selection.value)
    # Select n random features, at least one per selected problem.
    # Get one random feature per problem.
    selected_features: list[str] = [random.sample(problem.yaml["key_indicators"], 1)[0] for problem in problem_metrics]
    # Now pick from the remaining.
    if len(selected_features) < num:
        remaining_features: list[str] = [problem_feature for problem in problem_metrics for problem_feature in problem.yaml["key_indicators"] if problem_feature not in selected_features]
        selected_features += random.sample(remaining_features, num-len(selected_features))
    print("PROBLEM FEATURES")
    print(selected_features)
    return ", ".join(selected_features).replace("The AI", "You")

def chat_callback(content: str, user: str):
    """ 
    Processes user input, returns a response from the Assistant model, and initiates evaluation on the response. 
    Attaches exchange to the chat history and selects the generated exchange.

    Args:
        content (str): User input
        user (str): User name (always "user")
    
    Yields:
        response: chunks of the Assistant model's response as they come in.
    """
    new_message = {"role": "user", "content": content}
    problem_indicators = get_selected_problem_indicators(2)
    if problem_indicators is not None:
        problem_prompt = {"role": "system", 
                          "content": respond.PROMPT.format(problem_indicators=problem_indicators)}
        input_prompt = history + [problem_prompt, new_message]
    else:
        input_prompt = history + [new_message]

    for response in chatter.stream(input_prompt):
        yield response
    history.append(new_message)
    history.append({"role": "assistant", "content": response})
    exchange = LILACExchange(content, chat_interface[-1])
    exchanges.append(exchange)
    set_selected_exchange(exchange)
    lilac_start_eval(exchange)


def make_side_panel_1() -> pn.pane.PaneBase:
    """
    Constructs and returns the side panel UI element for the LILAC chatbot evaluation interface.

    The side panel includes:
        - A heading describing the MITRE LILAC intervention system.
        - An introduction card explaining how LILAC evaluates chat outputs and interprets status icons.
        - A summary area displaying detected issues or evaluation status.
        - A button to trigger automatic fixes for problematic outputs in the selected exchange.
        - An accordion listing detailed explanations of detected problems.

    This function also initializes and binds global UI elements (`issues_card`, `issues_summary`, `issues_fix_button`)
    for use elsewhere in the application.

    Returns:
        panel: The Panel UI element representing the side panel.
    """
    global issues_card, issues_summary, issues_fix_button
    heading = pn.pane.Markdown("<h1>List of Interventions for LLM-Assisted Chatbots (MITRE LILAC™)</h1>")
    notice = pn.Card(
                pn.Column(
                """The MITRE LILAC™ Demo Chatbot is designed to be used for research, educational, and testing purposes only, for understanding problematic outputs that chatbots powered by large language models (LLMs) can produce and how to detect them.

The chatbot’s outputs do not necessarily reflect the views of MITRE and its employees.

For research, educational, and testing purposes, the chatbot can be made to produce outputs that might be false, upsetting, manipulative, or harmful if acted upon. The user of the chatbot selects these features at their own discretion and risk.

For any questions please contact LILAC@mitre.org.
"""
            ),
            header=pn.pane.Markdown("<h2>Notice (click to close/open)</h2>"),
            sizing_mode="stretch_width"
        )
    panel1 = pn.Card(
                     pn.Column(
                        "Have a conversation with the Assistant in the chat window. " \
                        "LILAC will evaluate the Assistant's outputs for problematic behavior. " \
                        "If LILAC detects a problem, it will flag the output message.",
                        pn.Row(pn.pane.Image(LILAC_IMAGE_LOADING, height=50), "Spinning: Evaluation in progress"),
                        pn.Row(pn.pane.Image(LILAC_IMAGE_FAIL, height=50), "Red: Problems detected"),
                        pn.Row(pn.pane.Image(LILAC_IMAGE_PASS, height=50), "Green with yellow star: No problems detected"),
                        "If a risk is detected, see detected problem explanations below. To see explanations on previous messages, " \
                        "click the flower in the message box of your choice." \
                        "\n\nType in the text field to kick off the conversation!"
                        ),
                    header=pn.pane.Markdown("<h2>Introduction (click to close/open)</h2>"),
                    sizing_mode="stretch_width"
    )
    issues_summary = pn.pane.Markdown("No problems detected.")
    issues_fix_button = pn.widgets.Button(name="🔨 Try to Fix Now", visible=False, css_classes=["fix-button"], button_type="danger", button_style="outline")
    pn.bind(lilac_fix, issues_fix_button, watch=True)
    issues_card = pn.layout.Accordion(toggle=True, sizing_mode="stretch_width")
    panel2 = pn.Card(
        pn.Row(issues_summary, issues_fix_button, width_policy="max"),
        issues_card,
        sizing_mode="stretch_width",
        header=pn.pane.Markdown("<h2>Detected problems appear below</h2>"),
        collapsible=False
    )
    return pn.Column(heading, notice, panel1, panel2, width=450, scroll=True)

def make_side_panel_2() -> pn.pane.PaneBase:
    global problems_selection
    """ Creates the side panel UI with the problem selector.

    Returns:
        panel: Panel UI element
    """
    #heading = pn.pane.Markdown("<h2>Problem Categories</h2><i>Selecting these will produce bad chatbot behavior!</i>")
    problems_selection = pn.widgets.CheckBoxGroup(
        name="Problems",
        inline=False,
        sizing_mode="stretch_width",
        options=sorted(list(metrics.metricInfos.keys())),
    )
    panel1 = pn.Card(
        pn.pane.Markdown("<i>Selecting these will produce bad chatbot behavior!</i>"),
        problems_selection,
        collapsible=False,
        header=pn.pane.Markdown("<h2 style='margin: 0;'>Problem Categories</h2>"))
    return pn.Column(panel1, scroll=True, width=150)

"""
Panel setup
"""
def reset_chat(instance, event):
    """Defines the callback function for the refresh button"""
    global chat_interface
    # Clear the history and exchanges lists
    history.clear()
    exchanges.clear()

    assistant_say("I'm the safest assistant there is! Trust me. How can I help?")  # Reset initial message

# create the side panels
side_panel_1 = make_side_panel_1()
side_panel_2 = make_side_panel_2()
chat_interface = pn.chat.ChatInterface(callback=chat_callback, show_clear=False, show_undo=False, show_rerun=False,  
button_properties={
        "refresh": {"callback": ChatInterface._click_clear, "post_callback": reset_chat, "icon": "refresh"}
})
chat_interface.callback_exception = 'verbose'
chat_interface.sizing_mode = "stretch_height"  # Stretch the height of the ChatInterface

# Initial Message 
assistant_say("I'm the safest assistant there is! Trust me. How can I help?")

# Create the header with the refresh button
header = pn.Row(
    pn.pane.Markdown("<h2 style='margin: 0;'>Chat Window</h2>", sizing_mode="stretch_width"),  # Header text
    pn.Spacer(sizing_mode="stretch_width"),  # Spacer to push the button to the far right
    css_classes=["custom-row-class"]
)

chat_panel = pn.Card(chat_interface, header=header, collapsible=False)
pn.Row(side_panel_1, chat_panel, side_panel_2).servable()