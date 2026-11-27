from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def _profile_text(profile):
    return " ".join(
        str(profile.get(key, "") or "")
        for key in ["major", "degree_level", "preferred_study_level", "english_level"]
    )

def _scholarship_text(scholarship):
    def flatten(value):
        if isinstance(value, list):
            return " ".join(str(item) for item in value)
        return str(value or "")
    fields = [
        "scholarship_name", "study_level", "eligible_majors",
        "description", "funding_type",
    ]
    return " ".join(flatten(scholarship.get(key, "")) for key in fields)

def similarity_scores(profile, scholarships):
    """
    Build a temporary TF-IDF representation from the current profile and
    scholarship descriptions. This is text similarity, not supervised model
    training and it does not use a student training dataset.
    """
    if not scholarships:
        return []
    documents = [_profile_text(profile)] + [
        _scholarship_text(item) for item in scholarships
    ]
    if not any(documents):
        return [0.0] * len(scholarships)
    try:
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            min_df=1,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform(documents)
        scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return [round(float(score) * 100, 2) for score in scores]
    except ValueError:
        return [0.0] * len(scholarships)
