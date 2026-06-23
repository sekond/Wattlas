"""Offline unit tests for pipeline/build_fr_costs.py — no network.

Run: python -m pytest pipeline/test_fr_costs.py -v
or:  python pipeline/test_fr_costs.py
"""

from __future__ import annotations

import copy

from build_fr_costs import build_costs, validate


def test_real_data_validates():
    validate(build_costs())   # must not raise


def test_structure_and_symmetry():
    c = build_costs()
    assert c["unit"] == "EUR/MWh"
    assert [t["name"] for t in c["technologies"]] == [
        "Solar (utility)", "Wind (onshore)", "Nuclear — existing fleet", "Nuclear — new build (EPR2)"]
    keys = [comp["key"] for comp in c["components"]]
    assert keys == ["plant", "waste", "system", "support"]
    # symmetric: every technology carries every component (the hidden-cost lens for all)
    for t in c["technologies"]:
        assert all(k in t for k in keys)
        assert t["sources"]                       # every tech cited
        assert t["full_range"][0] <= t["full_range"][1]


def test_ranking_flips_with_what_you_count():
    by = {t["name"]: t for t in build_costs()["technologies"]}
    sticker = lambda t: t["plant"]
    full = lambda t: t["plant"] + t["waste"] + t["system"] + t["support"]
    # sticker: existing fleet ties the cheapest cluster, new build is ~2x renewables
    assert sticker(by["Nuclear — new build (EPR2)"]) >= 2 * sticker(by["Wind (onshore)"])
    # full cost: the amortised existing fleet becomes the cheapest of all four
    assert full(by["Nuclear — existing fleet"]) == min(full(t) for t in by.values())
    # existing vs new nuclear are clearly distinct (legacy much cheaper than EPR2)
    assert full(by["Nuclear — new build (EPR2)"]) > full(by["Nuclear — existing fleet"]) + 40


def test_validate_catches_out_of_range_full_cost():
    c = build_costs()
    bad = copy.deepcopy(c)
    bad["technologies"][0]["system"] = 500          # blow past the full_range
    try:
        validate(bad); assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_catches_missing_source():
    bad = copy.deepcopy(build_costs())
    bad["technologies"][1]["sources"] = []
    try:
        validate(bad); assert False, "expected ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
