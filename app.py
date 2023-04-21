from llm_generation_server.server import Server
from examples_py.next_token_prediction_example import (
    ExampleNextTokenPredictionComponent,
)
from examples_py.dialogue_connections_example import ExampleDialogueConnectionsComponent
from examples_py.sampling_example import ExampleSamplingComponent

next_token_component = ExampleNextTokenPredictionComponent()
next_token_component.initialize_vocab()
connections_component = ExampleDialogueConnectionsComponent()
sampling_component = ExampleSamplingComponent()
flask_app = Server(
    __name__, [next_token_component, connections_component, sampling_component]
)
app = flask_app.app
