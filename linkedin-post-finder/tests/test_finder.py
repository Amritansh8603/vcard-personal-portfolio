import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from finder import matches  # noqa: E402

CFG = {
    "roles": ["software engineer"],
    "hiring_keywords": ["hiring"],
    "locations": [],
    "experience": {"min_years": 2, "max_years": 4, "include_fresher": False},
}


def test_overlapping_range():
    assert matches("We are hiring Software Engineer, 3-5 years", CFG)


def test_plus_years():
    assert matches("Hiring software engineer with 3+ years", CFG)


def test_out_of_range():
    assert not matches("Hiring software engineer, 8-10 years", CFG)


def test_wrong_role():
    assert not matches("Hiring designer, 3 years", CFG)


def test_fresher_toggle():
    text = "Hiring software engineer fresher"
    assert not matches(text, CFG)
    cfg = {**CFG, "experience": {**CFG["experience"], "include_fresher": True}}
    assert matches(text, cfg)


def test_location_filter():
    cfg = {**CFG, "locations": ["bangalore"]}
    assert not matches("Hiring software engineer 3 years Pune", cfg)
    assert matches("Hiring software engineer 3 years Bangalore", cfg)
