import unittest
from pathlib import Path

import pandas as pd

from study_ml.utils import add_nutrients, parse_diary, search_products

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DIARY_PATH = DATA_DIR / "diet_diary.csv"
USDA_DIR = DATA_DIR / "FoodData_Central_csv_2026-04-30"
FINAL_PATH = DATA_DIR / "CompleteDietDiary.csv"

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


class FinalTableTest(unittest.TestCase):
    def test_build_and_save_final_table(self) -> None:
        parsed = parse_diary(DIARY_PATH)
        found = search_products(parsed, USDA_DIR)
        table = add_nutrients(parsed, found, USDA_DIR)

        table.to_csv(FINAL_PATH, index=False)

        self.assertTrue(FINAL_PATH.exists())
        self.assertEqual(len(table), len(parsed))
        self.assertTrue(set(NUTRIENT_COLUMNS) <= set(table.columns))

        reloaded = pd.read_csv(FINAL_PATH)
        self.assertEqual(list(reloaded.columns), list(table.columns))
        self.assertEqual(len(reloaded), len(table))

        print(f"Итоговая таблица: {table.shape} -> {FINAL_PATH}")
        for column in NUTRIENT_COLUMNS:
            print(f"  {column:16} filled {int(table[column].notna().sum())} of {len(table)}")


if __name__ == "__main__":
    unittest.main()
