from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Sequence

import torch

from visuallm.elements.barchart_element import BarChartElement, PieceInfo
from visuallm.elements.plain_text_element import PlainTextElement
from visuallm.elements.selector_elements import ButtonElement, CheckBoxSubElement


@dataclass
class MetricDescription:
    format: str
    """Format of the value that should be displayed on the page, e.g.
    "{:.4f}" will display only 4 most significant digits of the value
    """
    scalable: bool
    """Whether the bar is also scalable, or should be kept at 100 for the
    metric number to be better visible
    """


@dataclass
class GeneratedTextMetric(MetricDescription):
    metric_calculation: Callable[[str, str], Any]
    """Function that given the text generated by the model and the target text
    will generate a value that can be displayed using `self.format`
    """


@dataclass
class ProbsMetric(MetricDescription):
    metric_calculation: Callable[[Any, Any], Any]
    """Function that given the probabilities vectors and target indices will
    generate a value that can be displayed using `self.format`"""


class MetricsMixin(ABC):
    """This mixin prepares two types of elements.

    1. the selectors, which allow to select which metrics should be computed on
    the particular input and expected output pairs
    2. the barchart elements which display the metrics"""

    def __init__(
        self,
        metrics_on_generated_text: Dict[str, GeneratedTextMetric] = {},
        metrics_on_probs: Dict[str, ProbsMetric] = {},
    ):
        self._ordering = self.create_ordering(
            metrics_on_generated_text, metrics_on_probs
        )
        self._prepare_metrics_selection_frontend(self._ordering)
        self._metrics_on_generated_text = metrics_on_generated_text
        self._metrics_on_probs = metrics_on_probs
        self._display_metrics_heading = PlainTextElement(
            content="Metrics on Generated Outputs", is_heading=True
        )
        self._display_metrics_on_predicted_element = BarChartElement(long_contexts=True)
        self._display_metrics_on_target_heading = PlainTextElement(
            content="Metrics on Target", is_heading=True
        )
        self._display_metrics_on_target_element = BarChartElement(long_contexts=True)

        self.metric_button_element = ButtonElement(
            subelements=list(self._select_metrics_elements.values()),
            button_text="Select Metrics to Display",
            processing_callback=self.metrics_processing_callback,
        )

    @staticmethod
    def create_ordering(
        metrics_on_generated_text: Dict[str, Any], metrics_on_probs: Dict[str, Any]
    ):
        """Create ordering of metrics in which the metrics would be displayed on the
        frontend.
        """
        return list(metrics_on_generated_text.keys()) + list(metrics_on_probs.keys())

    def _prepare_metrics_selection_frontend(self, ordering: List[str]):
        """Prepare frontend elements for metrics checkboxes which allow
        the user to select which metrics we should compute for any output
        of the model.
        """
        self._select_metrics_heading = PlainTextElement(
            content="Which Metrics to Display", is_heading=True
        )
        self._select_metrics_elements: Dict[str, CheckBoxSubElement] = {}

        for key in ordering:
            self._select_metrics_elements[key] = CheckBoxSubElement(key, True)

    @property
    def metrics_selection_elements(self):
        """Elements which allow the user to select which metrics should be
        displayed.
        """
        return [self._select_metrics_heading, self.metric_button_element]

    @property
    def metrics_display_elements(self):
        """Elements that display the metrics on the target and on the
        generated outputs.
        """
        return [
            self._display_metrics_on_target_heading,
            self._display_metrics_on_target_element,
            self._display_metrics_heading,
            self._display_metrics_on_predicted_element,
        ]

    def _compute_n_display_metrics_for_element(
        self,
        generated_text_list: Sequence[str],
        label_text: str,
        probs_encoded_list: Sequence[torch.Tensor],
        generated_encoded_list: Sequence[torch.Tensor],
        element: BarChartElement,
    ):
        """Calculate generation metrics for each element of `generated_text_list` and
        probability metrics for each element of `probs_encoded_list`.

        Args:
            generated_text_list (Sequence[str]): Sequence with generations of the model.
            label_text (str): Gold output.
            probs_encoded_list (Sequence[torch.Tensor]): Sequence of sequences of probabilities of each
                generated token.
            generated_encoded_list (Sequence[torch.Tensor]): Sequence of sequences of ids of each
                target token.
            element (BarChartElement): Element where to display computed metrics.
        """
        piece_infos: List[PieceInfo] = []
        for (
            generated_text,
            labels_encoded,
            generated_encoded,
        ) in zip(
            generated_text_list,
            probs_encoded_list,
            generated_encoded_list,
        ):
            bar_names: List[str] = []
            bar_annotations: List[str] = []
            bar_heights: List[float] = []
            for name in self._ordering:
                if not self._select_metrics_elements[name].selected:
                    continue
                bar_names.append(name)

                if name in self._metrics_on_generated_text:
                    metric_description = self._metrics_on_generated_text[name]
                    result = metric_description.metric_calculation(
                        generated_text, label_text
                    )
                else:
                    metric_description = self._metrics_on_probs[name]
                    result = metric_description.metric_calculation(
                        labels_encoded, generated_encoded
                    )

                if metric_description.scalable:
                    bar_heights.append(min(result * 100, 100))
                else:
                    bar_heights.append(100)
                bar_annotations.append(metric_description.format.format(result))

            piece_infos.append(
                PieceInfo(
                    pieceTitle=generated_text,
                    barHeights=bar_heights,
                    barAnnotations=bar_annotations,
                    barNames=bar_names,
                )
            )

        element.set_piece_infos(piece_infos)

    def compute_n_display_metrics_on_predicted(
        self,
        generated_text_list: Sequence[str],
        label_text: str,
        probs_encoded_list: Sequence[torch.Tensor],
        generated_encoded_list: Sequence[torch.Tensor],
    ):
        """Compute metrics on the predictions of the model and
        display them with `self._display_metrics_on_predicted_element`.

        Args:
            generated_text_list (Sequence[str]): list of generations of the model.
            label_text (str): gold output.
            probs_encoded_list (Sequence[torch.Tensor]): Sequence of sequences of probabilities of each
                generated token.
            generated_encoded_list (Sequence[torch.Tensor]): Sequence of sequences of ids of each
                target token.
        """
        self._compute_n_display_metrics_for_element(
            generated_text_list,
            label_text,
            probs_encoded_list,
            generated_encoded_list,
            self._display_metrics_on_predicted_element,
        )

    def compute_n_display_metrics_on_target(
        self,
        target: str,
        probs_target: Sequence[torch.Tensor],
        target_encoded: Sequence[torch.Tensor],
    ):
        """
        Compute metrics on the targets.

        Args:
            target (str): gold output.
            probs_target (Sequence[torch.Tensor]): Sequence of sequences of probabilities of each
                target token.
            generated_encoded_list (Sequence[torch.Tensor]): Sequence of sequences of ids of each
                target token.
        """
        self._compute_n_display_metrics_for_element(
            [target],
            target,
            probs_target,
            target_encoded,
            self._display_metrics_on_target_element,
        )

    @abstractmethod
    def metrics_processing_callback(self):
        """What to do right after the selection of which metrics to display is
        updated. (This mixin does not automatically calculate metrics as it may
        require e.g. non-trivial manipulation with the inputs. Hence you need to
        implement metrics computation in this method.)"""
        ...
