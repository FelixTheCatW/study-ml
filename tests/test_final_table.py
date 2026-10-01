import unittest

import pandas as pd

from study_ml.utils import add_nutrients, parse_diary, search_products
from tests.common import DIARY_PATH, FINAL_PATH, NUTRIENT_COLUMNS, USDA_DIR


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
