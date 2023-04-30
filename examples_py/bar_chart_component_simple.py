import heapq
import math
import random

import requests

from llm_generation_server.component_base import ComponentBase
from llm_generation_server.elements.barchart_element import BarChartElement
from llm_generation_server.elements.plain_text_element import PlainTextElement


class BarChartComponentSimple(ComponentBase):
    def __init__(self, long_contexts: bool = False, title="BarChart Component"):
        self.word_vocab, self.word_ids = download_word_vocabulary()
        self.barchart_element = BarChartElement(
            endpoint_callback=self.barchart_callback, long_contexts=long_contexts
        )
        self.text_element = PlainTextElement()
        self.update_barchart_component()

        super().__init__(
            name="barchart_component",
            title=title,
            elements=[self.barchart_element, self.text_element],
        )

    def update_barchart_component(self):
        probs = sample_ten_words(self.word_ids)
        ten_largest_probs = heapq.nlargest(10, zip(*zip(*probs), self.word_vocab))

        # bar height is the height of the bar, should be between 0 and 100
        bar_heights = [[x[0]] for x in ten_largest_probs]

        # bar annotation is the text displayed within the bar
        bar_annotations = [[f"{x[0]:.2f}%"] for x in ten_largest_probs]

        # annotation is the name of whole bar sub element
        annotations = [x[-1] for x in ten_largest_probs]

        self.barchart_element.set_possibilities(
            bar_heights, bar_annotations, annotations
        )

    def barchart_callback(self):
        self.barchart_element.default_callback(return_response=False)
        s: str = self.barchart_element.selected
        self.text_element.content = f"Last selected: {s}"
        self.update_barchart_component()
        return self.fetch_info(fetch_all=False)


def download_word_vocabulary():
    """Download MIT word list as a word vocab.

    Returns:
        Tuple[List[str], List[int]]: list of words and list of indices of the
            corresponding words
    """
    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    response = requests.get(word_site)
    word_vocab = [x.decode("utf-8") for x in response.content.splitlines()]
    word_ids = [i for i, _ in enumerate(word_vocab)]
    return word_vocab, word_ids


def sample_ten_words(word_ids):
    """Sample 10 random ids from word_ids and give them 10 random exponentialy
    distributed probabilities.
    """
    k = 10
    ten_samples = random.choices(word_ids, k=k)
    ten_numbers = [math.exp(i + random_noise()) for i in range(k)]
    ten_numbers_sum = sum(ten_numbers)
    ten_probs = [n / ten_numbers_sum for n in ten_numbers]

    probs = [[0.0] for _ in word_ids]
    for i, p in zip(ten_samples, ten_probs):
        probs[i][0] = p * 100
    return probs


def random_noise(lower_bound=-1, upper_bound=1):
    """Create random noise between lower_bound and upper bound."""
    if lower_bound >= upper_bound:
        raise ValueError()
    range_size = upper_bound - lower_bound
    noise = random.random() * range_size + lower_bound
    return noise
