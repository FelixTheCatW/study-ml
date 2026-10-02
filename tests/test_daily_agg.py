import unittest

from tests.common import (
    DAILY_PATH,
    DROPNA_COLUMN,
    NUTRIENT_COLUMNS,
    aggregate_by_user_day,
    load_final_table,
)


class DailyAggregationTest(unittest.TestCase):
    def test_aggregate_by_user_day(self) -> None:
        table = load_final_table()
        daily = aggregate_by_user_day(table)

        daily.to_csv(DAILY_PATH, index=False)

        expected_rows = (
            table.dropna(subset=[DROPNA_COLUMN])[["id", "date"]].drop_duplicates().shape[0]
        )

        print("===== Агрегация по (id, date) =====")
        print(f"Строк в итоговой таблице: {len(table)}")
        print(f"Строк после dropna по '{DROPNA_COLUMN}': {len(table.dropna(subset=[DROPNA_COLUMN]))}")
        print(f"Агрегированная таблица: {daily.shape} -> {DAILY_PATH}")
        print(f"Колонки: {list(daily.columns)}")
        print(daily.head(5).to_string(index=False))

        self.assertTrue(DAILY_PATH.exists())
        self.assertEqual(len(daily), expected_rows)
        self.assertTrue(set(NUTRIENT_COLUMNS) <= set(daily.columns))
        self.assertTrue({"id", "date", "meals", "products", "weight"} <= set(daily.columns))
        self.assertEqual(
            len(daily),
            daily[["id", "date"]].drop_duplicates().shape[0],
        )


if __name__ == "__main__":
    unittest.main()
