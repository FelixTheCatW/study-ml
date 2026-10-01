from __future__ import annotations

from os import PathLike
from typing import Union

import pandas as pd

DataInput = Union[pd.DataFrame, str, PathLike]

MEAL_COLUMNS = ("breakfast", "lunch", "supper")
NON_MEAL_COLUMNS = ("ID", "date", "start_weight", "weight")
ALL_COLUMNS = NON_MEAL_COLUMNS + MEAL_COLUMNS

OUT_COLUMNS = ["id", "date", "meal", "product", "start_weight", "weight"]
IMAGES_MARKER = "|||"


def _read(data: DataInput) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    return pd.read_csv(data)


def _split_meal(cell: object) -> list[str]:
    text = "" if pd.isna(cell) else str(cell)
    images_part, _, products_part = text.partition(IMAGES_MARKER)
    images = images_part if images_part.strip() else None
    products = products_part.split()
    return products


def parse_diary(
        diary: DataInput
) -> pd.DataFrame:
    """Разворачивает дневник так, что каждая строка — один съеденный продукт. """
    frame = _read(diary)

    records: list[dict[str, object]] = []
    for row in frame.to_dict(orient="records"):
        base = {column: row[column] for column in NON_MEAL_COLUMNS}
        base["id"] = base.pop("ID")
        for meal in MEAL_COLUMNS:
            products = _split_meal(row[meal])
            if not products:
                continue
            for product in products or [None]:
                records.append(
                    {
                        **base,
                        "meal": meal,
                        "product": product,
                    }
                )

    return pd.DataFrame.from_records(records, columns=OUT_COLUMNS)
