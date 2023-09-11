from typing import List

from visuallm.components.GenerationComponent import GenerationComponent
from visuallm.elements.element_base import ElementBase

from .input_display import PersonaChatVisualization


class Generation(GenerationComponent, PersonaChatVisualization):
    def __post_init__(self):
        self.on_model_change_callback()

    def init_model_input_display(self) -> List[ElementBase]:
        return PersonaChatVisualization.init_model_input_display(self)

    def update_model_input_display(self):
        PersonaChatVisualization.update_model_input_display(self, add_target=False)

    def create_model_inputs(self):
        return self._tokenizer(
            self.text_to_tokenizer_element.content, return_tensors="pt"
        )

    def create_target_encoding(self):
        target = self.get_target_str()
        return self._tokenizer(
            self.text_to_tokenizer_element.content + " " + target, return_tensors="pt"
        ).input_ids

    def get_target_str(self):
        return self.loaded_sample["candidates"][-1]
