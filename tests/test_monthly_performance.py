import unittest

import pandas as pd

from dashboard_elements.monthly_performance import (
    COMPLETED_SERVICES,
    DELIVERED_REPORTS,
    MEDIAN_DELIVERY_DAYS,
    _comparison_value,
    _format_delta,
    build_monthly_metrics,
)
from dashboard_elements.filters import FilterSelection, apply_filters


class MonthlyPerformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = pd.DataFrame(
            {
                "data_conclusao": pd.to_datetime(
                    pd.Series(
                        ["2026-01-30", "2026-02-05", "2026-03-01", None],
                        dtype="string",
                    )
                ),
                "data_entrega": pd.to_datetime(
                    pd.Series(
                        ["2026-02-02", "2026-02-05", "2026-04-04", "2026-04-08"],
                        dtype="string",
                    )
                ),
                "status": ["Entregue", "Entregue", "Entregue", "Pendente"],
            }
        )
        self.months = pd.date_range("2026-01-01", "2026-04-01", freq="MS")

    def test_metrics_use_their_own_event_dates(self) -> None:
        metrics = build_monthly_metrics(self.data, self.months)

        self.assertEqual(
            metrics[COMPLETED_SERVICES].tolist(),
            [1, 1, 1, 0],
        )
        self.assertEqual(
            metrics[DELIVERED_REPORTS].tolist(),
            [0, 2, 0, 2],
        )
        self.assertTrue(
            pd.isna(
                metrics.at[
                    pd.Timestamp("2026-01-01"),
                    MEDIAN_DELIVERY_DAYS,
                ]
            )
        )
        self.assertEqual(
            metrics.at[pd.Timestamp("2026-02-01"), MEDIAN_DELIVERY_DAYS],
            1.5,
        )
        self.assertEqual(
            metrics.at[pd.Timestamp("2026-04-01"), MEDIAN_DELIVERY_DAYS],
            34,
        )

    def test_comparison_supports_previous_month_and_three_month_average(self) -> None:
        metrics = build_monthly_metrics(self.data, self.months)
        first_month = pd.Timestamp("2026-01-01")
        selected_month = pd.Timestamp("2026-04-01")

        previous = _comparison_value(
            metrics,
            selected_month,
            COMPLETED_SERVICES,
            "Mês anterior",
            first_month,
        )
        average = _comparison_value(
            metrics,
            selected_month,
            COMPLETED_SERVICES,
            "Média dos 3 meses anteriores",
            first_month,
        )

        self.assertEqual(previous, 1)
        self.assertEqual(average, 1)

    def test_comparison_is_unavailable_before_the_data_range(self) -> None:
        metrics = build_monthly_metrics(self.data, self.months)
        first_month = pd.Timestamp("2026-01-01")

        result = _comparison_value(
            metrics,
            first_month,
            COMPLETED_SERVICES,
            "Mês anterior",
            first_month,
        )

        self.assertIsNone(result)

    def test_delta_format_handles_zero_baseline(self) -> None:
        self.assertEqual(_format_delta(3, 0), "+3,0")
        self.assertEqual(_format_delta(6, 4), "+2,0 (+50,0%)")

    def test_date_filter_can_select_delivery_month(self) -> None:
        data = pd.DataFrame(
            {
                "status": ["Entregue", "Entregue"],
                "cliente": ["A", "B"],
                "tecnico": ["X", "Y"],
                "data_conclusao": pd.to_datetime(["2026-01-30", "2026-02-05"]),
                "data_entrega": pd.to_datetime(["2026-02-02", "2026-03-05"]),
            }
        )
        filters: FilterSelection = {
            "statuses": ["Entregue"],
            "clients": ["A", "B"],
            "technicians": ["X", "Y"],
            "date_column": "data_entrega",
            "date_range": (
                pd.Timestamp("2026-02-01").date(),
                pd.Timestamp("2026-02-28").date(),
            ),
        }

        filtered = apply_filters(data, filters)

        self.assertEqual(filtered["cliente"].tolist(), ["A"])


if __name__ == "__main__":
    unittest.main()
