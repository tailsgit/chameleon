"""Regression for recall suites with only partial dev-CSV coverage."""
from eval.gen_budget_eval import summary


def test_summary_keeps_every_case_when_optional_baseline_is_missing():
    common = dict(cpu_s=1., wall_s=1., score=90., pool_distinct=2,
                  candidate_pass=True, gen_won=False, generator={}, passed=True,
                  operations={})
    rows = [dict(common, delta=-1.), dict(common, cpu_s=3.)]
    result = summary(rows)
    assert result["cases"] == 2
    assert result["cpu_s"]["mean"] == 2.
    assert "delta" not in result
    assert "regressions" not in result
    rows[1]["delta"] = -11.
    rows[0]["case"], rows[1]["case"] = "a", "b"
    result = summary(rows)
    assert result["delta"]["mean"] == -6.
    assert [r["case"] for r in result["regressions"]] == ["b"]
