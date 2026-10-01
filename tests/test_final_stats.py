import unittest
from pathlib import Path

import pandas as pd

from study_ml.utils import add_nutrients, parse_diary, search_products

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DIARY_PATH = DATA_DIR / "diet_diary.csv"
USDA_DIR = DATA_DIR / "FoodData_Central_csv_2026-04-30"
FINAL_PATH = DATA_DIR / "final_table.csv"

NUMERIC_COLUMNS = [
    "start_weight",
    "weight",
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
KEY_COLUMNS = ["id", "date", "meal", "product"]


def _load_table() -> pd.DataFrame:
    if FINAL_PATH.exists():
        return pd.read_csv(FINAL_PATH)
    parsed = parse_diary(DIARY_PATH)
    found = search_products(parsed, USDA_DIR)
    return add_nutrients(parsed, found, USDA_DIR)


class FinalTableStatisticsTest(unittest.TestCase):
    def test_final_table_statistics(self) -> None:
        table = _load_table()

        print("===== Статистика итоговой таблицы =====")
        print(f"Строк: {len(table)}, колонок: {len(table.columns)}")
        print(f"Колонки: {list(table.columns)}")

        print("--- Пропуски ---")
        for column, missing in table.isna().sum().items():
            share = round(100 * missing / len(table), 2)
            print(f"  {column:16} {missing:6} ({share}%)")

        print("--- Дубликаты ---")
        print(f"  полных строк: {int(table.duplicated().sum())}")
        print(f"  по {KEY_COLUMNS}: {int(table.duplicated(subset=KEY_COLUMNS).sum())}")

        print("--- Уникальные значения ---")
        print(f"  пользователей: {table['id'].nunique()}")
        print(f"  дат: {table['date'].nunique()}")
        print(f"  продуктов: {table['product'].nunique()}")
        print(f"  приёмов пищи: {table['meal'].value_counts().to_dict()}")

        print("--- Числовые: разброс, среднее, медиана, выбросы (IQR) ---")
        for column in NUMERIC_COLUMNS:
            values = table[column].dropna()
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            low = q1 - 1.5 * iqr
            high = q3 + 1.5 * iqr
            outliers = int(((values < low) | (values > high)).sum())
            print(
                f"  {column:16} "
                f"mean={values.mean():10.3f} median={values.median():10.3f} "
                f"std={values.std():10.3f} min={values.min():10.3f} "
                f"q1={q1:10.3f} q3={q3:10.3f} max={values.max():10.3f} "
                f"outliers={outliers}"
            )

        self.assertGreater(len(table), 0)
        self.assertTrue(set(NUMERIC_COLUMNS) <= set(table.columns))
        self.assertTrue(set(KEY_COLUMNS) <= set(table.columns))


if __name__ == "__main__":
    unittest.main()
