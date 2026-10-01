import unittest

from tests.common import KEY_COLUMNS, NUMERIC_COLUMNS, load_final_table


class FinalTableStatisticsTest(unittest.TestCase):
    def test_final_table_statistics(self) -> None:
        table = load_final_table()

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
