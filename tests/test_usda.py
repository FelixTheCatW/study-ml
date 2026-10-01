import unittest
from pathlib import Path

import pandas as pd

from study_ml.utils import parse_diary, search_products

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DIARY_PATH = DATA_DIR / "diet_diary.csv"
USDA_DIR = DATA_DIR / "FoodData_Central_csv_2026-04-30"
RESULT_PATH = DATA_DIR / "usda_matches.csv"


class SearchProductsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parsed = parse_diary(DIARY_PATH)
        cls.result = search_products(cls.parsed, USDA_DIR)

    def test_search_products_saves_result(self) -> None:
        self.result.to_csv(RESULT_PATH, index=False)

        self.assertTrue(RESULT_PATH.exists())
        reloaded = pd.read_csv(RESULT_PATH)
        self.assertEqual(list(reloaded.columns), list(self.result.columns))
        self.assertEqual(len(reloaded), len(self.result))

    def test_search_products_report(self) -> None:
        products = sorted(self.parsed["product"].dropna().unique())
        found = self.result[self.result["source"].notna()]
        found_products = sorted(found["product"].unique())
        not_found = [product for product in products if product not in set(found_products)]

        by_source = found["source"].value_counts().to_dict()
        by_match = found["match"].value_counts().to_dict()
        per_product = (
            found.groupby("product")
            .agg(
                source=("source", "first"),
                modes=("match", lambda values: ",".join(sorted(set(values)))),
                matches=("source", "size"),
            )
            .sort_index()
        )
        substring_only = per_product[per_product["modes"] == "substring"]
        word_found = per_product[per_product["modes"].str.contains("word")]

        print("===== Отчет о матчинге продуктов USDA =====")
        print(f"Всего уникальных продуктов: {len(products)}")
        print(f"Найдено: {len(found_products)} (по слову: {len(word_found)}, "
              f"дополнительно по подстроке: {len(substring_only)})")
        print(f"Не найдено: {len(not_found)}")
        print("Строк по источникам:")
        for source, count in by_source.items():
            print(f"  {source}: {count}")
        print("Строк по способу поиска:")
        for mode, count in by_match.items():
            print(f"  {mode}: {count}")
        print("Найденные продукты (product -> source, modes, matches):")
        for product, row in per_product.iterrows():
            print(f"  {product} -> {row['source']} [{row['modes']}] ({row['matches']})")
        print("Ненайденные продукты:")
        for product in not_found:
            print(f"  {product}")

        self.assertEqual(set(self.result["product"]), set(products))
        self.assertGreater(len(found_products), 0)


if __name__ == "__main__":
    unittest.main()
