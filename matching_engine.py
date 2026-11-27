from datetime import date
def _list(v):
    if isinstance(v, list): return v
    if v is None: return []
    import json
    try: return json.loads(v)
    except Exception: return [x.strip() for x in str(v).split(",") if x.strip()]
def evaluate(student, scholarship):
    reasons, failed, missing = [], [], []
    degree = str(student.get("degree_level","")).strip()
    allowed_degrees = _list(scholarship.get("eligible_degrees"))
    if not degree: missing.append("المؤهل الدراسي غير محدد")
    elif allowed_degrees and degree not in allowed_degrees: failed.append(f"المؤهل {degree} غير مدرج ضمن المؤهلات المقبولة")
    else: reasons.append("المؤهل الدراسي متوافق")
    level = str(student.get("preferred_study_level","")).strip()
    target_level = str(scholarship.get("study_level","")).strip()
    if not level: missing.append("المرحلة الدراسية المطلوبة غير محددة")
    elif level.lower() != target_level.lower(): failed.append("المرحلة الدراسية المطلوبة غير متوافقة")
    else: reasons.append("المرحلة الدراسية متوافقة")
    major = str(student.get("major","")).strip()
    majors = _list(scholarship.get("eligible_majors"))
    if not major: missing.append("التخصص غير محدد")
    elif "All majors" in majors or major in majors: reasons.append("التخصص مقبول")
    else: failed.append(f"التخصص {major} غير موجود ضمن التخصصات المقبولة")
    try:
        gpa=float(student.get("gpa"))
        min_gpa=float(scholarship.get("min_gpa"))
        scale=str(student.get("gpa_scale","4.0"))
        sch_scale=str(scholarship.get("gpa_scale","4.0"))
        if scale != sch_scale:
            missing.append("مقياس المعدل مختلف ويحتاج إلى تحويل موثوق")
        elif gpa < min_gpa: failed.append(f"المعدل {gpa:g} أقل من الحد الأدنى {min_gpa:g}")
        else: reasons.append("المعدل يحقق الحد الأدنى")
    except (TypeError, ValueError): missing.append("المعدل أو مقياسه غير متوفر")
    required_test=str(scholarship.get("english_test") or "").strip()
    min_score=scholarship.get("min_english_score")
    if required_test and min_score not in (None,""):
        student_test=str(student.get("english_test") or "").strip()
        score=student.get("english_score")
        if not student_test or score in (None,""): missing.append(f"نتيجة {required_test} غير متوفرة")
        elif student_test.upper()!=required_test.upper(): failed.append(f"نوع الاختبار المطلوب {required_test} بينما المسجل {student_test}")
        else:
            try:
                if float(score)<float(min_score): failed.append(f"درجة {required_test} أقل من الحد الأدنى {min_score}")
                else: reasons.append("متطلب اللغة مستوفى")
            except (TypeError,ValueError): missing.append("درجة اختبار اللغة غير صالحة")
    elif not required_test: reasons.append("لا يوجد اختبار لغة محدد في البيانات")
    status = "Not Eligible" if failed else ("Needs Information" if missing else "Eligible")
    total=len(reasons)+len(failed)+len(missing)
    score=round((len(reasons)/total)*100) if total else 0
    return {"status":status,"rule_score":score,"reasons":reasons,"failed":failed,"missing":missing}
