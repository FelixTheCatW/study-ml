from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DIARY_PATH = DATA_DIR / "diet_diary.csv"
USDA_DIR = DATA_DIR / "FoodData_Central_csv_2026-04-30"
PARSED_PATH = DATA_DIR / "parsed_diary.csv"
RESULT_PATH = DATA_DIR / "usda_matches.csv"
FINAL_PATH = DATA_DIR / "CompleteDietDiary.csv"

KEY_COLUMNS = ["id", "date", "meal", "product"]

NUTRIENT_COLUMNS = [
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbohydrates_g",
    "fiber_g",
    "sugars_g",
    "saturated_fat_g",
    "cholesterol_mg",
    "sodium_mg",
    "potassium_mg",
    "water_g",
]

NUMERIC_COLUMNS = ["start_weight", "weight", *NUTRIENT_COLUMNS]


def load_final_table() -> pd.DataFrame:
    """Читает сохранённую итоговую таблицу или строит её заново."""
    if FINAL_PATH.exists():
        return pd.read_csv(FINAL_PATH)

    from study_ml.utils import add_nutrients, parse_diary, search_products

    parsed = parse_diary(DIARY_PATH)
    found = search_products(parsed, USDA_DIR)
    table = add_nutrients(parsed, found, USDA_DIR)
    table.to_csv(FINAL_PATH, index=False)
    return table


def summarize(series: pd.Series) -> dict[str, float]:
    """Возвращает mean/median/min/max для числового ряда."""
    return {
        "mean": round(float(series.mean()), 2),
        "median": round(float(series.median()), 2),
        "min": float(series.min()),
        "max": float(series.max()),
    }
