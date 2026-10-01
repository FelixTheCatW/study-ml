"""Поиск продуктов из дневника по справочнику USDA FoodData Central.

Три независимых поиска по разным источникам:

1. :func:`search_food_description` — названия generic-еды (``food.description``,
   ``data_type`` = foundation/sr_legacy).
2. :func:`search_branded_food` — краткие названия брендовых продуктов
   (``branded_food.short_description``).
3. :func:`search_food_category` — категории еды (``food_category.description``).

:func:`search_products` вызывает их по очереди: если продукт найден в первом
источнике, остальные не используются, иначе идёт переход к следующему.
"""

from __future__ import annotations

import re
from bisect import bisect_left
from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Union

import pandas as pd

DataInput = Union[pd.DataFrame, pd.Series, Iterable[str]]

FOODS_FILE = "food.csv"
FOOD_CATEGORY_FILE = "food_category.csv"
BRANDED_FOOD_FILE = "branded_food.csv"

GENERIC_DATA_TYPES = ("foundation_food", "sr_legacy_food")

NUTRIENT_FILE = "food_nutrient.csv"
NUTRIENTS = {
    1008: "energy_kcal",
    1003: "protein_g",
    1004: "fat_g",
    1005: "carbohydrates_g",
    1079: "fiber_g",
    2000: "sugars_g",
    1258: "saturated_fat_g",
    1253: "cholesterol_mg",
    1093: "sodium_mg",
    1092: "potassium_mg",
    1051: "water_g",
}

WORD_RE = re.compile(r"[a-z0-9_]+")

RESULT_COLUMNS = [
    "product",
    "source",
    "match",
    "fdc_id",
    "name",
    "data_type",
    "food_category_id",
    "brand_owner",
    "branded_food_category",
    "code",
]


def _as_path(data_dir: str | PathLike) -> Path:
    return Path(data_dir)


def _normalize(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _products(products: DataInput) -> list[str]:
    if isinstance(products, pd.DataFrame):
        series = products["product"]
    elif isinstance(products, pd.Series):
        series = products
    else:
        series = pd.Series(list(products))
    return [
        v
        for v in (_normalize(x) for x in series.dropna().unique())
        if v
    ]


def _match_products(
        tokens: Iterable[str],
        names: pd.Series,
        match: str,
) -> dict[str, list]:
    normalized = names.map(_normalize)

    matches: dict[str, list] = {}
    if match == "substring":
        for token in tokens:
            needle = _normalize(token).replace("_", " ")
            if not needle:
                matches[token] = []
                continue
            mask = normalized.str.contains(needle, regex=False, na=False)
            matches[token] = list(names.index[mask])
        return matches

    word_index: dict[str, list] = {}
    for position, name in normalized.items():
        for word in set(WORD_RE.findall(name)):
            word_index.setdefault(word, []).append(position)

    if match == "prefix":
        sorted_words = sorted(word_index)
        for token in tokens:
            prefix = _normalize(token)
            positions: list = []
            position = bisect_left(sorted_words, prefix)
            while position < len(sorted_words) and sorted_words[position].startswith(prefix):
                positions.extend(word_index[sorted_words[position]])
                position += 1
            matches[token] = sorted(positions)
    else:  # word
        for token in tokens:
            matches[token] = sorted(word_index.get(_normalize(token), []))
    return matches


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=RESULT_COLUMNS)


def _load_foods(data_dir: str | PathLike) -> pd.DataFrame:
    foods = pd.read_csv(
        _as_path(data_dir) / FOODS_FILE,
        dtype=str,
        usecols=["fdc_id", "data_type", "description", "food_category_id"],
    )
    foods = foods[foods["data_type"].isin(GENERIC_DATA_TYPES)]
    return foods.reset_index(drop=True)


def _load_branded(data_dir: str | PathLike) -> pd.DataFrame:
    foods = pd.read_csv(
        _as_path(data_dir) / FOODS_FILE,
        dtype=str,
        usecols=["fdc_id", "data_type", "description"],
    )
    foods = foods[foods["data_type"] == "branded_food"]

    branded = pd.read_csv(
        _as_path(data_dir) / BRANDED_FOOD_FILE,
        dtype=str,
        usecols=[
            "fdc_id",
            "short_description",
            "brand_owner",
            "branded_food_category",
        ],
    )
    branded = foods.merge(branded, on="fdc_id", how="left")
    branded = branded[branded["description"].notna()]
    return branded.reset_index(drop=True)


def _load_categories(data_dir: str | PathLike) -> pd.DataFrame:
    categories = pd.read_csv(
        _as_path(data_dir) / FOOD_CATEGORY_FILE, dtype=str
    )
    return categories.rename(
        columns={"id": "food_category_id", "description": "name"}
    ).reset_index(drop=True)


def search_food_description(
        products: list[str],
        data_dir: str | PathLike,
        match: str = "word",
) -> pd.DataFrame:
    """Ищет продукты по ``food.description`` (по умолчанию generic-еда)."""
    tokens = products

    foods = _load_foods(data_dir)

    records = []
    for token, positions in _match_products(tokens, foods["description"], match).items():
        for position in positions:
            row = foods.loc[position]
            records.append(
                {
                    "product": token,
                    "source": "food_description",
                    "match": match,
                    "fdc_id": row["fdc_id"],
                    "name": row["description"],
                    "data_type": row["data_type"],
                    "food_category_id": row["food_category_id"],
                }
            )
    return pd.DataFrame.from_records(records, columns=RESULT_COLUMNS)


def search_branded_food(
        products: list[str],
        data_dir: str | PathLike,
        match: str = "word",
) -> pd.DataFrame:
    """Ищет продукты по ``food.description`` брендовых записей."""
    branded = _load_branded(data_dir)

    records = []
    for token, positions in _match_products(
            products, branded["description"], "substring"
    ).items():
        for position in positions:
            row = branded.loc[position]
            records.append(
                {
                    "product": token,
                    "source": "branded_food",
                    "match": "substring",
                    "fdc_id": row["fdc_id"],
                    "name": row["description"],
                    "brand_owner": row["brand_owner"],
                    "branded_food_category": row["branded_food_category"],
                }
            )
    return pd.DataFrame.from_records(records, columns=RESULT_COLUMNS)


def search_food_category(
        products: list[str],
        data_dir: str | PathLike,
        match: str = "word",
) -> pd.DataFrame:
    """Ищет продукты по ``food_category.description`` (грубый поиск)."""
    categories = _load_categories(data_dir)

    records = []
    for token, positions in _match_products(
            products, categories["name"], match
    ).items():
        for position in positions:
            row = categories.loc[position]
            records.append(
                {
                    "product": token,
                    "source": "food_category",
                    "match": match,
                    "name": row["name"],
                    "food_category_id": row["food_category_id"],
                    "code": row.get("code"),
                }
            )
    return pd.DataFrame.from_records(records, columns=RESULT_COLUMNS)


sources = (search_food_description, search_branded_food, search_food_category)


def search_products(
        products: DataInput,
        data_dir: str | PathLike,
        *,
        match: str = "word",
) -> pd.DataFrame:
    """Ищет продукты по трём источникам по очереди с переходом к следующему.

    Сначала :func:`search_food_description`; продукты без совпадений идут в
    :func:`search_branded_food`; оставшиеся — в :func:`search_food_category`.
    Затем то же самое повторяется по подстроке для тех, кто не нашёлся по слову.
    Ненайденные продукты возвращаются строкой с пустым ``source``.
    """
    tokens = _products(products)
    if not tokens:
        return _empty()

    modes = [match] if match == "substring" else [match, "substring"]

    frames: list[pd.DataFrame] = []
    remaining = list(tokens)

    for mode in modes:
        for source in sources:
            if not remaining:
                break
            found = source(remaining, data_dir, mode)
            if not found.empty:
                frames.append(found)
                resolved = set(found["product"])
                remaining = [token for token in remaining if token not in resolved]
        if not remaining:
            break

    if frames:
        combined = pd.concat(frames, ignore_index=True)
    else:
        combined = _empty()

    if remaining:
        unmatched = pd.DataFrame({"product": remaining})
        combined = pd.concat([combined, unmatched], ignore_index=True)

    return combined[RESULT_COLUMNS].reset_index(drop=True)


def _load_nutrients(data_dir: str | PathLike) -> pd.DataFrame:
    nutrients = pd.read_csv(
        _as_path(data_dir) / NUTRIENT_FILE,
        usecols=["fdc_id", "nutrient_id", "amount"],
    )
    nutrients = nutrients[nutrients["nutrient_id"].isin(NUTRIENTS)]
    nutrients["nutrient_id"] = nutrients["nutrient_id"].map(NUTRIENTS)

    table = nutrients.pivot_table(
        index="fdc_id",
        columns="nutrient_id",
        values="amount",
        aggfunc="first",
    )
    table = table.reindex(columns=list(NUTRIENTS.values())).reset_index()
    table["fdc_id"] = table["fdc_id"].astype(str)
    return table


def add_nutrients(parsed: pd.DataFrame, found: pd.DataFrame, data_dir: str | PathLike) -> pd.DataFrame:
    """Добавляет к таблице дневника нутриенты USDA (на 100 г).

    Для каждого продукта берётся первое найденное соответствие из ``found``,
    по его ``fdc_id`` подтягиваются колонки: ``energy_kcal``, ``protein_g``,
    ``fat_g``, ``carbohydrates_g``, ``fiber_g``, ``sugars_g``,
    ``saturated_fat_g``, ``cholesterol_mg``, ``sodium_mg``, ``potassium_mg``,
    ``water_g``.
    """
    first_match = found.dropna(subset=["fdc_id"]).drop_duplicates(subset="product")[["product", "fdc_id"]]
    nutrients = _load_nutrients(data_dir)

    table = parsed.merge(first_match, on="product", how="left")
    table = table.merge(nutrients, on="fdc_id", how="left")
    return table
