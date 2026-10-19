"""The Crello case lists (ids and sizes only, so these run without the converted designs)."""

import json

from eval.crello_testset import QUICK, cases


def test_quick_suite_is_100_dev_cases_across_every_stratum():
    quick = cases("quick")
    dev = {c for c, _d, _t in cases("dev")}
    assert len(quick) == 100 and {c for c, _d, _t in quick} <= dev
    strata = json.loads(QUICK.read_text())["strata"]
    assert len(strata) == 16  # 4 aspect-change buckets x 4 element-count bands, each represented
