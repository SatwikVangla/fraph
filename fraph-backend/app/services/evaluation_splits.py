from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

TIME_AWARE_TEST_RATIO = 0.25
MIN_TIME_AWARE_TRAIN_ROWS = 16
MIN_TIME_AWARE_TEST_ROWS = 8


@dataclass(frozen=True)
class TimeAwareSplit:
    train_indices: list[int]
    test_indices: list[int]
    metadata: dict[str, object]


def _sorted_indices(prepared: pd.DataFrame) -> list[int]:
    ordering = prepared.assign(
        __step_order=pd.to_numeric(prepared["step"], errors="coerce").fillna(0.0),
        __row_order=range(len(prepared)),
    ).sort_values(["__step_order", "__row_order"], kind="mergesort")
    return ordering.index.astype(int).tolist()


def _class_counts(values: pd.Series) -> dict[int, int]:
    return {int(label): int(count) for label, count in values.astype(int).value_counts().to_dict().items()}


def build_time_aware_holdout_split(
    prepared: pd.DataFrame,
    labels: pd.Series,
    test_ratio: float = TIME_AWARE_TEST_RATIO,
    min_train_rows: int = MIN_TIME_AWARE_TRAIN_ROWS,
    min_test_rows: int = MIN_TIME_AWARE_TEST_ROWS,
) -> TimeAwareSplit:
    if len(prepared) != len(labels):
        raise ValueError('Prepared rows and labels must be aligned for time-aware evaluation.')

    ordered_indices = _sorted_indices(prepared)
    total_rows = len(ordered_indices)
    if total_rows < (min_train_rows + min_test_rows):
        raise ValueError('Not enough labeled rows for chronological holdout evaluation.')

    ordered_labels = labels.loc[ordered_indices].astype(int)
    target_train_rows = max(min_train_rows, int(round(total_rows * (1.0 - test_ratio))))
    max_train_rows = total_rows - min_test_rows
    target_train_rows = min(max(target_train_rows, min_train_rows), max_train_rows)

    best_split_index: int | None = None
    best_score: tuple[int, int] | None = None
    for split_index in range(min_train_rows, total_rows - min_test_rows + 1):
        train_labels = ordered_labels.iloc[:split_index]
        test_labels = ordered_labels.iloc[split_index:]
        if train_labels.nunique() < 2 or test_labels.nunique() < 2:
            continue
        score = (abs(split_index - target_train_rows), -split_index)
        if best_score is None or score < best_score:
            best_score = score
            best_split_index = split_index

    fallback_used = False
    if best_split_index is None:
        best_split_index = target_train_rows
        fallback_used = True

    train_indices = [int(index) for index in ordered_indices[:best_split_index]]
    test_indices = [int(index) for index in ordered_indices[best_split_index:]]
    train_steps = pd.to_numeric(prepared.loc[train_indices, 'step'], errors='coerce').fillna(0.0)
    test_steps = pd.to_numeric(prepared.loc[test_indices, 'step'], errors='coerce').fillna(0.0)
    metadata = {
        'name': 'time_aware_holdout',
        'chronological': True,
        'fallback_used': fallback_used,
        'ordered_by': 'step',
        'train_rows': len(train_indices),
        'test_rows': len(test_indices),
        'train_class_counts': _class_counts(labels.loc[train_indices]),
        'test_class_counts': _class_counts(labels.loc[test_indices]),
        'train_step_min': round(float(train_steps.min()), 4) if len(train_steps) else None,
        'train_step_max': round(float(train_steps.max()), 4) if len(train_steps) else None,
        'test_step_min': round(float(test_steps.min()), 4) if len(test_steps) else None,
        'test_step_max': round(float(test_steps.max()), 4) if len(test_steps) else None,
    }
    return TimeAwareSplit(train_indices=train_indices, test_indices=test_indices, metadata=metadata)


def build_time_aware_folds(
    prepared: pd.DataFrame,
    labels: pd.Series,
    folds: int = 3,
    min_train_rows: int = MIN_TIME_AWARE_TRAIN_ROWS,
    min_test_rows: int = MIN_TIME_AWARE_TEST_ROWS,
) -> list[TimeAwareSplit]:
    if folds < 1:
        raise ValueError('folds must be at least 1')
    if len(prepared) != len(labels):
        raise ValueError('Prepared rows and labels must be aligned for time-aware evaluation.')

    ordered_indices = _sorted_indices(prepared)
    total_rows = len(ordered_indices)
    initial_train_rows = max(min_train_rows, int(math.floor(total_rows * 0.5)))
    remaining_rows = total_rows - initial_train_rows
    if remaining_rows < min_test_rows:
        holdout = build_time_aware_holdout_split(
            prepared=prepared,
            labels=labels,
            min_train_rows=min_train_rows,
            min_test_rows=min_test_rows,
        )
        return [holdout]

    test_window = max(min_test_rows, remaining_rows // folds)
    splits: list[TimeAwareSplit] = []
    start = initial_train_rows
    for fold_index in range(folds):
        stop = total_rows if fold_index == folds - 1 else min(total_rows, start + test_window)
        if stop - start < min_test_rows:
            break
        train_indices = [int(index) for index in ordered_indices[:start]]
        test_indices = [int(index) for index in ordered_indices[start:stop]]
        train_labels = labels.loc[train_indices].astype(int)
        test_labels = labels.loc[test_indices].astype(int)
        if train_labels.nunique() < 2 or test_labels.nunique() < 2:
            start = stop
            continue
        train_steps = pd.to_numeric(prepared.loc[train_indices, 'step'], errors='coerce').fillna(0.0)
        test_steps = pd.to_numeric(prepared.loc[test_indices, 'step'], errors='coerce').fillna(0.0)
        splits.append(
            TimeAwareSplit(
                train_indices=train_indices,
                test_indices=test_indices,
                metadata={
                    'name': 'time_aware_fold',
                    'chronological': True,
                    'ordered_by': 'step',
                    'fold_index': len(splits) + 1,
                    'train_rows': len(train_indices),
                    'test_rows': len(test_indices),
                    'train_class_counts': _class_counts(train_labels),
                    'test_class_counts': _class_counts(test_labels),
                    'train_step_min': round(float(train_steps.min()), 4) if len(train_steps) else None,
                    'train_step_max': round(float(train_steps.max()), 4) if len(train_steps) else None,
                    'test_step_min': round(float(test_steps.min()), 4) if len(test_steps) else None,
                    'test_step_max': round(float(test_steps.max()), 4) if len(test_steps) else None,
                },
            )
        )
        start = stop
        if start >= total_rows:
            break

    if splits:
        return splits

    holdout = build_time_aware_holdout_split(
        prepared=prepared,
        labels=labels,
        min_train_rows=min_train_rows,
        min_test_rows=min_test_rows,
    )
    return [holdout]
