# Source: https://github.com/RUC-NLPIR/FlashRAG/blob/main/flashrag/evaluator/metrics.py
# Copyright (c) 2024 Jiajie Jin.
# MIT License

import re
import warnings
from collections import Counter

from .utils import normalize_answer


class BaseMetric:
    """`BaseMetric` serves as the base object of all metrics. Implemented metric should
    inherit this class.
    """

    metric_name = "base"

    def __init__(self, config):
        self.config = config
        self.dataset_name = config["dataset_name"]

    def calculate_metric(self, data):
        """Get the total score of this metric and score for each sample.

        Args:
            data object: it contains basic information and generated information.

        Returns:
            (metric_score: dict, metric_score_list: list)
            metric_score: such as ``{'em': 0.53}``.
            metric_score_list: score for each sample.

        """
        return {}, []


class F1_Score(BaseMetric):
    """Token-level F1 score"""

    metric_name = "f1"

    def __init__(self, config):
        super().__init__(config)

    def token_level_scores(self, prediction: str, ground_truths: str):
        final_metric = {"f1": 0, "precision": 0, "recall": 0}
        if isinstance(ground_truths, str):
            ground_truths = [ground_truths]
        for ground_truth in ground_truths:
            normalized_prediction = normalize_answer(prediction)
            normalized_ground_truth = normalize_answer(ground_truth)

            if normalized_prediction in ["yes", "no", "noanswer"] and normalized_prediction != normalized_ground_truth:
                continue
            if (
                normalized_ground_truth in ["yes", "no", "noanswer"]
                and normalized_prediction != normalized_ground_truth
            ):
                continue
            prediction_tokens = normalized_prediction.split()
            ground_truth_tokens = normalized_ground_truth.split()
            common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                continue
            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(ground_truth_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            for k in ["f1", "precision", "recall"]:
                final_metric[k] = max(eval(k), final_metric[k])
        return final_metric

    def calculate_metric(self, data):
        pred_list = data.pred
        golden_answers_list = data.golden_answers
        metric_score_list = [
            self.token_level_scores(pred, golden_answers)["f1"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        f1 = sum(metric_score_list) / len(metric_score_list)
        return {"f1": f1}, metric_score_list


class Recall_Score(F1_Score):
    """Token-level Recall score"""

    metric_name = "recall"

    def __init__(self, config):
        super().__init__(config)

    def calculate_metric(self, data):
        pred_list = data.pred
        golden_answers_list = data.golden_answers
        metric_score_list = [
            self.token_level_scores(pred, golden_answers)["recall"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        precision = sum(metric_score_list) / len(metric_score_list)
        return {"recall": precision}, metric_score_list


class Precision_Score(F1_Score):
    """Token-level Precision score"""

    metric_name = "precision"

    def __init__(self, config):
        super().__init__(config)

    def calculate_metric(self, data):
        pred_list = data.pred
        golden_answers_list = data.golden_answers
        metric_score_list = [
            self.token_level_scores(pred, golden_answers)["precision"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        precision = sum(metric_score_list) / len(metric_score_list)
        return {"precision": precision}, metric_score_list


class ExactMatch(BaseMetric):
    r"""Exact match measure whether the predicted answer is completely consistent
    with the standard answer.

    """

    metric_name = "em"

    def __init__(self, config):
        super().__init__(config)
        self.is_regex = self.dataset_name == "curatedtrec"

    def calculate_em(self, prediction: str, golden_answers: list) -> float:
        if isinstance(golden_answers, str):
            golden_answers = [golden_answers]
        normalized_prediction = normalize_answer(prediction)
        score = 0.0
        for golden_answer in golden_answers:
            if self.is_regex:
                print("Consider answer as regex!")
                golden_answer = re.compile(golden_answer, re.IGNORECASE)
                match = re.fullmatch(golden_answer, normalized_prediction)
                if match is not None:
                    score = 1.0
                    break
            else:
                golden_answer = normalize_answer(golden_answer)
                if golden_answer == normalized_prediction:
                    score = 1.0
                    break
        return score

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        pred_list = data.pred

        metric_score_list = [
            self.calculate_em(pred, golden_answers)
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        em_score = sum(metric_score_list) / len(metric_score_list)

        return {"em": em_score}, metric_score_list


class Sub_ExactMatch(BaseMetric):
    r"""Sub-Exact match measure whether the predicted answer contains the standard answer."""

    metric_name = "sub_em"

    def __init__(self, config):
        super().__init__(config)
        self.is_regex = self.dataset_name == "curatedtrec"

    def calculate_sub_em(self, prediction: str, golden_answers: list) -> float:
        if isinstance(golden_answers, str):
            golden_answers = [golden_answers]
        normalized_prediction = normalize_answer(prediction)
        score = 0.0
        for golden_answer in golden_answers:
            if self.is_regex:
                print("Consider answer as regex!")
                golden_answer = re.compile(golden_answer, re.IGNORECASE)
                match = re.search(golden_answer, normalized_prediction)
                if match is not None:
                    score = 1.0
                    break
            else:
                golden_answer = normalize_answer(golden_answer)
                if golden_answer in normalized_prediction:
                    score = 1.0
                    break
        return score

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        pred_list = data.pred

        metric_score_list = [
            self.calculate_sub_em(pred, golden_answers)
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        sub_em_score = sum(metric_score_list) / len(metric_score_list)

        return {"sub_em": sub_em_score}, metric_score_list


class Retrieval_Recall(BaseMetric):
    r"""The recall of the top-k retreived passages, we measure if any of the passage contain the answer string."""

    metric_name = "retrieval_recall"

    def __init__(self, config):
        super().__init__(config)
        self.topk = config["metric_setting"]["retrieval_recall_topk"]

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        retrieve_docs = data.retrieval_result
        recall_score_list = []
        for doc_list, golden_answers in zip(retrieve_docs, golden_answers_list, strict=False):
            if len(doc_list) < self.topk:
                warnings.warn(f"Length of retrieved docs is smaller than topk ({self.topk})")  # noqa: B028
            doc_list = [doc["contents"] for doc in doc_list[: self.topk]]
            hit_list = []
            for doc in doc_list:
                for golden_answer in golden_answers:
                    if normalize_answer(golden_answer) in normalize_answer(doc):
                        hit_list.append(True)
                        break
                else:
                    hit_list.append(False)
            score = 1 if any(hit_list) else 0
            recall_score_list.append(score)
        recall_score = sum(recall_score_list) / len(recall_score_list)

        return {f"retrieval_recall_top{self.topk}": recall_score}, recall_score_list


class Retrieval_Precision(BaseMetric):
    r"""The precision of the top-k retreived passages, we measure if any of the passage contain the answer string."""

    metric_name = "retrieval_precision"

    def __init__(self, config):
        super().__init__(config)
        self.topk = config["metric_setting"]["retrieval_recall_topk"]

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        retrieve_docs = data.retrieval_result
        precision_score_list = []
        for doc_list, golden_answers in zip(retrieve_docs, golden_answers_list, strict=False):
            if len(doc_list) < self.topk:
                warnings.warn(f"Length of retrieved docs is smaller than topk ({self.topk})")  # noqa: B028
            doc_list = [doc["contents"] for doc in doc_list[: self.topk]]
            hit_list = []
            for doc in doc_list:
                for golden_answer in golden_answers:
                    if normalize_answer(golden_answer) in normalize_answer(doc):
                        hit_list.append(True)
                        break
                else:
                    hit_list.append(False)
            score = sum(hit_list) / len(hit_list)
            precision_score_list.append(score)
        precision_score = sum(precision_score_list) / len(precision_score_list)

        return {f"retrieval_precision_top{self.topk}": precision_score}, precision_score_list


class Rouge_Score(BaseMetric):
    metric_name = "rouge_score"

    def __init__(self, config):
        super().__init__(config)
        from rouge import Rouge

        self.scorer = Rouge()

    def calculate_rouge(self, pred, golden_answers):
        output = {}
        for answer in golden_answers:
            scores = self.scorer.get_scores(pred, answer)
            for key in ["rouge-1", "rouge-2", "rouge-l"]:
                if key not in output:
                    output[key] = []
                output[key].append(scores[0][key]["f"])
        for k, v in output.items():
            output[k] = max(v)

        return output


class Rouge_1(Rouge_Score):
    metric_name = "rouge-1"

    def __init__(self, config):
        super().__init__(config)

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        pred_list = data.pred

        metric_score_list = [
            self.calculate_rouge(pred, golden_answers)["rouge-1"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        score = sum(metric_score_list) / len(metric_score_list)

        return {"rouge-1": score}, metric_score_list


class Rouge_2(Rouge_Score):
    metric_name = "rouge-2"

    def __init__(self, config):
        super().__init__(config)

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        pred_list = data.pred

        metric_score_list = [
            self.calculate_rouge(pred, golden_answers)["rouge-2"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        score = sum(metric_score_list) / len(metric_score_list)

        return {"rouge-2": score}, metric_score_list


class Rouge_L(Rouge_Score):
    metric_name = "rouge-l"

    def __init__(self, config):
        super().__init__(config)

    def calculate_metric(self, data):
        golden_answers_list = data.golden_answers
        pred_list = data.pred

        metric_score_list = [
            self.calculate_rouge(pred, golden_answers)["rouge-l"]
            for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False)
        ]
        score = sum(metric_score_list) / len(metric_score_list)

        return {"rouge-l": score}, metric_score_list


class BLEU(BaseMetric):
    metric_name = "bleu"

    def __init__(self, config):
        super().__init__(config)
        from ._bleu import Tokenizer13a

        self.tokenizer = Tokenizer13a()
        self.max_order = config["metric_setting"].get("bleu_max_order", 4)
        self.smooth = config["metric_setting"].get("bleu_smooth", False)

    def calculate_metric(self, data):
        from ._bleu import compute_bleu

        golden_answers_list = data.golden_answers
        pred_list = data.pred

        pred_list = [self.tokenizer(pred) for pred in pred_list]
        golden_answers_list = [
            [self.tokenizer(ans) for ans in golden_answers] for golden_answers in golden_answers_list
        ]
        score = compute_bleu(
            reference_corpus=golden_answers_list,
            translation_corpus=pred_list,
            max_order=self.max_order,
            smooth=self.smooth,
        )
        (total_bleu, precisions, bp, ratio, translation_length, reference_length) = score

        score_list = []
        for pred, golden_answers in zip(pred_list, golden_answers_list, strict=False):
            pred = [pred]
            golden_answers = [golden_answers]
            score = compute_bleu(
                reference_corpus=golden_answers_list,
                translation_corpus=pred_list,
                max_order=self.max_order,
                smooth=self.smooth,
            )
            (bleu, precisions, bp, ratio, translation_length, reference_length) = score
            score_list.append(bleu)

        return {"bleu": total_bleu}, score_list
