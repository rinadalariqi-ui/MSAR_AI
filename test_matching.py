import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from matching_engine import evaluate

def base_student():
    return {
        "degree_level": "Bachelor",
        "major": "Computer Science",
        "gpa": 3.8,
        "gpa_scale": "4.0",
        "preferred_study_level": "Master",
        "english_test": "IELTS",
        "english_score": 7,
    }

def base_scholarship():
    return {
        "eligible_degrees": ["Bachelor"],
        "eligible_majors": ["Computer Science"],
        "min_gpa": 3.0,
        "gpa_scale": "4.0",
        "study_level": "Master",
        "english_test": "IELTS",
        "min_english_score": 6.5,
    }

def test_eligible():
    assert evaluate(base_student(), base_scholarship())["status"] == "Eligible"

def test_gpa_failed():
    student = base_student()
    student["gpa"] = 2.0
    assert evaluate(student, base_scholarship())["status"] == "Not Eligible"

def test_missing_language_score():
    student = base_student()
    student["english_score"] = None
    assert evaluate(student, base_scholarship())["status"] == "Needs Information"

def test_major_failed():
    student = base_student()
    student["major"] = "Medicine"
    assert evaluate(student, base_scholarship())["status"] == "Not Eligible"

def test_different_gpa_scales_need_information():
    student = base_student()
    student["gpa_scale"] = "100"
    assert evaluate(student, base_scholarship())["status"] == "Needs Information"
