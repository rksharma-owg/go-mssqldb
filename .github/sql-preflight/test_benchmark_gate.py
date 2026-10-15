import unittest
from benchmark_gate import regressions


def report(metric, delta, p="0.000", name="Example-4"):
    return f"│ {metric} │ {metric} vs base │\n{name} 100 ± 1% 120 ± 1% {delta} (p={p} n=10)\n"


class GateTest(unittest.TestCase):
    def test_time_and_memory_cost_increases_fail(self):
        for metric in ["sec/op", "B/op", "allocs/op"]:
            with self.subTest(metric=metric):
                self.assertEqual(len(regressions(report(metric, "+15.00%"))), 1)

    def test_throughput_increase_passes_decrease_fails(self):
        self.assertEqual(regressions(report("B/s", "+20.36%")), [])
        self.assertEqual(len(regressions(report("B/s", "-20.36%"))), 1)

    def test_same_sign_cost_improvement_passes(self):
        self.assertEqual(regressions(report("sec/op", "-20.36%")), [])

    def test_threshold_and_significance_preserved(self):
        self.assertEqual(regressions(report("sec/op", "+14.99%")), [])
        self.assertEqual(regressions(report("sec/op", "+20.00%", "0.010")), [])
        self.assertEqual(regressions(report("sec/op", "~", "1.000")), [])

    def test_existing_large_buffer_exclusion_preserved(self):
        self.assertEqual(regressions(report("sec/op", "+25.00%", name="TdsBuffer_Write_Large-4")), [])

    def test_mixed_metric_and_stable_rows(self):
        data = report("sec/op", "~", "1.000") + report("B/s", "+20.36%")
        data += report("sec/op", "+16.00%")
        rows = regressions(data)
        self.assertEqual([(r["metric"], r["delta_percent"]) for r in rows], [("sec/op", 16.0)])

    def test_malformed_row_cannot_hide_among_valid_rows(self):
        data = report("sec/op", "+16.00%")
        data += "Broken-4 100 120 bad-delta (p=0.000 n=10)\n"
        with self.assertRaises(ValueError):
            regressions(data)

    def test_empty_input_fails_closed(self):
        with self.assertRaises(ValueError):
            regressions("")


if __name__ == "__main__":
    unittest.main()
