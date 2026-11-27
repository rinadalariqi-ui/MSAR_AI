def validate_student(data):
    errors=[]
    try:
        gpa=float(data.get("gpa"))
        if not 0 <= gpa <= 4: errors.append("المعدل يجب أن يكون بين 0 و4 في هذا النموذج.")
    except (TypeError,ValueError): errors.append("أدخلي معدلًا رقميًا صحيحًا.")
    if not str(data.get("full_name","")).strip(): errors.append("اسم الطالب مطلوب.")
    if not str(data.get("major","")).strip(): errors.append("التخصص مطلوب.")
    return errors
