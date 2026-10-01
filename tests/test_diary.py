import unittest
from pathlib import Path

import pandas as pd

from study_ml.utils import MEAL_COLUMNS, parse_diary

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DIARY_PATH = DATA_DIR / "diet_diary.csv"
PARSED_PATH = DATA_DIR / "parsed_diary.csv"


class ParseDiaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parsed = parse_diary(DIARY_PATH)

    @staticmethod
    def _summary(series: pd.Series) -> dict[str, float]:
        return {
            "mean": round(float(series.mean()), 2),
            "median": round(float(series.median()), 2),
            "min": float(series.min()),
            "max": float(series.max()),
        }

    def test_parse_diary_saves_result(self) -> None:
        self.parsed.to_csv(PARSED_PATH, index=False)

        self.assertTrue(PARSED_PATH.exists())
        reloaded = pd.read_csv(PARSED_PATH)
        self.assertEqual(list(reloaded.columns), list(self.parsed.columns))
        self.assertEqual(len(reloaded), len(self.parsed))

    def test_parse_diary_statistics(self) -> None:
        parsed = self.parsed
        by_user = parsed.groupby("id")

        dates_per_user = by_user["date"].nunique()
        meals_per_user = parsed.drop_duplicates(["id", "date", "meal"]).groupby("id").size()
        products_per_user = by_user.size()

        statistics = {
            "rows": len(parsed),
            "columns": list(parsed.columns),
            "unique_users": parsed["id"].nunique(),
            "unique_dates": parsed["date"].nunique(),
            "unique_products": parsed["product"].nunique(),
            "top_products": parsed["product"].value_counts().head(10).to_dict(),
            "meals": parsed["meal"].value_counts().to_dict(),
            "rows_without_product": int(parsed["product"].isna().sum()),
            "weight_mean": round(float(parsed["weight"].mean()), 3),
            "weight_min": float(parsed["weight"].min()),
            "weight_max": float(parsed["weight"].max()),
        }
        per_user = {
            "dates_per_user": self._summary(dates_per_user),
            "meals_per_user": self._summary(meals_per_user),
            "products_per_user": self._summary(products_per_user),
        }

        print("Статистика таблицы продуктов:")
        for name, value in statistics.items():
            print(f"  {name}: {value}")
        print("На одного пользователя:")
        for name, value in per_user.items():
            print(f"  {name}: {value}")

        self.assertGreater(statistics["rows"], 0)
        self.assertGreater(statistics["unique_users"], 0)
        self.assertGreater(statistics["unique_products"], 0)
        self.assertTrue(set(parsed["meal"].unique()) <= set(MEAL_COLUMNS))
        self.assertEqual(len(dates_per_user), statistics["unique_users"])

    @unittest.expectedFailure
    def test_photos_match_dishes(self) -> None:
        diary = pd.read_csv(DIARY_PATH)

        matched = 0
        mismatched = 0
        total_photos = 0
        total_dishes = 0
        examples: list[tuple] = []

        for meal in MEAL_COLUMNS:
            for cell in diary[meal]:
                text = "" if pd.isna(cell) else str(cell)
                images_part, _, dishes_part = text.partition("|||")
                photos = [image for image in images_part.split(";") if image.strip()]
                dishes = dishes_part.split()

                total_photos += len(photos)
                total_dishes += len(dishes)

                if len(photos) == len(dishes):
                    matched += 1
                else:
                    mismatched += 1
                    if len(examples) < 10:
                        examples.append((meal, len(photos), len(dishes), text))

        print("Проверка теории: фото == блюда")
        print(f"  приёмов пищи всего: {matched + mismatched}")
        print(f"  совпало: {matched}")
        print(f"  не совпало: {mismatched}")
        print(f"  фотографий всего: {total_photos}")
        print(f"  блюд/продуктов всего: {total_dishes}")
        print("  примеры расхождений (meal, photos, dishes, cell):")
        for example in examples:
            print(f"    {example}")

        self.assertEqual(
            total_photos,
            total_dishes,
            "количество фотографий не совпадает с количеством блюд",
        )


if __name__ == "__main__":
    unittest.main()
