import unittest

from tests.common import load_final_table, aggregate_by_user_meal, MEAL_PATH, DROPNA_COLUMN, NUTRIENT_COLUMNS


class DailyMealAggregationTest(unittest.TestCase):
    def test_aggregate_by_user_meal(self) -> None:
        table = load_final_table()
        meal = aggregate_by_user_meal(table)

        meal.to_csv(MEAL_PATH, index=False)

        print("===== Агрегация по (id, date, meal) =====")
        print(f"Строк в итоговой таблице: {len(table)}")
        print(f"Строк после dropna по '{DROPNA_COLUMN}': {len(table.dropna(subset=[DROPNA_COLUMN]))}")
        print(f"Агрегированная таблица: {meal.shape} -> {MEAL_PATH}")
        print(f"Колонки: {list(meal.columns)}")
        print(meal.head(5).to_string(index=False))

        self.assertTrue(MEAL_PATH.exists())
        self.assertTrue(set(NUTRIENT_COLUMNS) <= set(meal.columns))
        self.assertTrue({"id", "date", "meal", "products"} <= set(meal.columns))
