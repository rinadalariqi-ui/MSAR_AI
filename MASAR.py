import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from ai_engine import similarity_scores
from data_manager import load_scholarships
from matching_engine import evaluate

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCHOLARSHIPS_PATH = DATA_DIR / "masar_scholarships_demo.csv"
PROFILE_PATH = DATA_DIR / "my_profile.json"

st.set_page_config(page_title="MASAR AI | مسار", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.stApp {background:#f7f9fc}
.hero {padding:24px 28px;border-radius:16px;background:linear-gradient(115deg,#10243d,#176b70);color:white;margin-bottom:18px}
.hero h1 {font-size:34px;margin:0}
.hero p {opacity:.92;margin:7px 0 0}
.small-note {color:#687386;font-size:13px}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>MASAR AI | مَسَار</h1>'
    '<p>منصة ذكية لاستكشاف المنح الدراسية وتحليل مدى توافقها مع ملفك الأكاديمي</p></div>',
    unsafe_allow_html=True,
)

REQUIRED_COLUMNS = {
    "scholarship_id", "scholarship_name", "university", "country",
    "study_level", "eligible_degrees", "eligible_majors", "min_gpa",
    "gpa_scale", "english_test", "min_english_score", "funding_type",
    "deadline", "description", "application_url"
}

@st.cache_data
def get_scholarships():
    return load_scholarships(SCHOLARSHIPS_PATH)

try:
    scholarships = get_scholarships()
except Exception as exc:
    st.error(f"تعذر تحميل ملف المنح: {exc}")
    st.stop()

missing_columns = REQUIRED_COLUMNS - set(scholarships.columns)
if missing_columns:
    st.error("ملف المنح لا يحتوي على الأعمدة المطلوبة: " + ", ".join(sorted(missing_columns)))
    st.stop()

def load_profile():
    if not PROFILE_PATH.exists():
        return None
    try:
        return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

def save_profile(profile):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def scholarship_card(s):
    st.markdown(f"### {s.get('scholarship_name', 'منحة بدون اسم')}")
    st.write(f"**الجامعة:** {s.get('university', 'غير محدد')}  |  **الدولة:** {s.get('country', 'غير محدد')}")
    st.write(f"**المرحلة:** {s.get('study_level', 'غير محدد')}  |  **التمويل:** {s.get('funding_type', 'غير محدد')}")
    st.write(f"**آخر موعد:** {s.get('deadline') or 'غير محدد'}")
    st.write(s.get("description") or "")
    url = str(s.get("application_url") or "").strip()
    if url:
        if "example.org" in url:
            st.caption("هذا رابط توضيحي تجريبي، وليس رابط تقديم حقيقي.")
        st.markdown(f"[زيارة صفحة المنحة / المصدر]({url})")

def profile_form(existing):
    old = existing or {}
    with st.form("profile_form"):
        st.subheader("بياناتك الأكاديمية")
        name = st.text_input("الاسم", value=old.get("full_name", ""))
        major = st.text_input("التخصص", value=old.get("major", ""), placeholder="مثال: Artificial Intelligence")
        current_degree_options = ["High School", "Diploma", "Bachelor", "Master", "PhD"]
        current_degree = st.selectbox(
            "المؤهل الدراسي الحالي",
            current_degree_options,
            index=current_degree_options.index(old.get("degree_level"))
            if old.get("degree_level") in current_degree_options else 2,
        )
        study_options = ["Bachelor", "Master", "PhD"]
        target_level = st.selectbox(
            "المرحلة التي تريد التقديم لها",
            study_options,
            index=study_options.index(old.get("preferred_study_level"))
            if old.get("preferred_study_level") in study_options else 1,
        )
        scale_options = ["4.0", "5.0", "100"]
        scale = st.selectbox(
            "مقياس المعدل",
            scale_options,
            index=scale_options.index(str(old.get("gpa_scale", "4.0")))
            if str(old.get("gpa_scale", "4.0")) in scale_options else 0,
        )
        max_gpa = {"4.0": 4.0, "5.0": 5.0, "100": 100.0}[scale]
        gpa = st.number_input(
            "المعدل الدراسي",
            min_value=0.0,
            max_value=max_gpa,
            value=min(float(old.get("gpa", 0.0) or 0.0), max_gpa),
            step=0.05 if scale != "100" else 1.0,
        )
        country_options = ["Any"] + sorted(scholarships["country"].dropna().astype(str).unique().tolist())
        previous_country = old.get("target_country", "Any")
        target_country = st.selectbox(
            "الدولة المفضلة (اختياري)",
            country_options,
            index=country_options.index(previous_country) if previous_country in country_options else 0,
        )
        english_options = ["Beginner", "Intermediate", "Advanced"]
        english_level = st.selectbox(
            "مستوى اللغة الإنجليزية",
            english_options,
            index=english_options.index(old.get("english_level"))
            if old.get("english_level") in english_options else 1,
        )
        test_options = ["لا يوجد", "IELTS", "TOEFL"]
        previous_test = old.get("english_test") or "لا يوجد"
        english_test = st.selectbox(
            "اختبار اللغة (إن وجد)",
            test_options,
            index=test_options.index(previous_test) if previous_test in test_options else 0,
        )
        score = st.number_input(
            "درجة اختبار اللغة (اتركها صفرًا إذا لم تختبر)",
            min_value=0.0,
            max_value=120.0,
            value=float(old.get("english_score") or 0.0),
            step=0.5,
        )
        submitted = st.form_submit_button("حفظ الملف الأكاديمي", type="primary")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("الاسم مطلوب.")
        if not major.strip():
            errors.append("التخصص مطلوب.")
        if errors:
            for error in errors:
                st.error(error)
        else:
            profile = {
                "full_name": name.strip(),
                "major": major.strip(),
                "degree_level": current_degree,
                "preferred_study_level": target_level,
                "gpa": float(gpa),
                "gpa_scale": scale,
                "target_country": target_country,
                "english_level": english_level,
                "english_test": "" if english_test == "لا يوجد" else english_test,
                "english_score": float(score) if english_test != "لا يوجد" and score > 0 else None,
            }
            save_profile(profile)
            st.session_state["masar_profile"] = profile
            st.success("تم حفظ ملفك على هذا الجهاز. انتقل إلى صفحة «المنح المناسبة لي» لبدء المطابقة.")

if "masar_profile" not in st.session_state:
    st.session_state["masar_profile"] = load_profile()

pages = [
    "الرئيسية",
    "إنشاء ملفي الأكاديمي",
    "استكشاف المنح",
    "المنح المناسبة لي",
    "مقارنة المنح",
    "مركز ذكاء MASAR",
]
page = st.sidebar.radio("القائمة الرئيسية", pages)
st.sidebar.divider()
st.sidebar.caption("نسخة أولية | ملفك الشخصي محلي على جهازك")
st.sidebar.caption(f"عدد المنح المحمّلة: {len(scholarships)}")

if page == "الرئيسية":
    st.subheader("لوحة المنصة")
    c1, c2, c3 = st.columns(3)
    c1.metric("المنح المسجلة", len(scholarships))
    c2.metric("الدول", scholarships["country"].nunique())
    c3.metric("أنواع التمويل", scholarships["funding_type"].nunique())
    left, right = st.columns(2)
    with left:
        st.markdown("#### المنح حسب الدولة")
        st.bar_chart(scholarships["country"].value_counts())
    with right:
        st.markdown("#### المنح حسب نوع التمويل")
        st.bar_chart(scholarships["funding_type"].value_counts())
    if st.session_state["masar_profile"]:
        st.success(f"ملفك محفوظ باسم: {st.session_state['masar_profile']['full_name']}")
    else:
        st.info("ابدأ بإنشاء ملفك الأكاديمي. سيستخدم MASAR بياناتك لمقارنتها بشروط المنح.")
    st.warning("بيانات المنح الموجودة حاليًا تجريبية للتأكد من عمل النموذج. لا تعتمد عليها للتقديم الفعلي.")

elif page == "إنشاء ملفي الأكاديمي":
    st.subheader("إنشاء ملفك الأكاديمي")
    st.write("أدخل بياناتك مرة واحدة. ستُستخدم هذه البيانات محليًا لتحليل مدى توافقك مع المنح.")
    profile_form(st.session_state["masar_profile"])
    if st.session_state["masar_profile"]:
        with st.expander("عرض البيانات المحفوظة"):
            st.json(st.session_state["masar_profile"])
        if st.button("حذف ملفي من هذا الجهاز"):
            if PROFILE_PATH.exists():
                PROFILE_PATH.unlink()
            st.session_state["masar_profile"] = None
            st.success("تم حذف الملف المحلي.")
            st.rerun()
        st.caption("ملفك محفوظ في data/my_profile.json داخل مجلد المشروع، ولا يُرسل إلى خادم خارجي.")

elif page == "استكشاف المنح":
    st.subheader("استكشاف قاعدة بيانات المنح")
    query = st.text_input("ابحث باسم المنحة أو الجامعة أو التخصص")
    countries = ["الكل"] + sorted(scholarships["country"].dropna().astype(str).unique().tolist())
    country = st.selectbox("الدولة", countries)
    funding_types = ["الكل"] + sorted(scholarships["funding_type"].dropna().astype(str).unique().tolist())
    funding = st.selectbox("نوع التمويل", funding_types)
    view = scholarships.copy()
    if query:
        searchable = view.astype(str).agg(" ".join, axis=1).str.contains(query, case=False, na=False)
        view = view[searchable]
    if country != "الكل":
        view = view[view["country"] == country]
    if funding != "الكل":
        view = view[view["funding_type"] == funding]
    st.write(f"عدد النتائج: {len(view)}")
    for _, row in view.iterrows():
        with st.expander(f"{row['scholarship_name']} | {row['country']}"):
            scholarship_card(row.to_dict())

elif page == "المنح المناسبة لي":
    st.subheader("نتائج المطابقة الشخصية")
    profile = st.session_state["masar_profile"]
    if not profile:
        st.warning("أنشئ ملفك الأكاديمي أولًا حتى يتمكن MASAR من تحليل المنح المناسبة.")
        st.stop()

    records = scholarships.to_dict(orient="records")
    similarities = similarity_scores(profile, records)
    results = []
    for scholarship, similarity in zip(records, similarities):
        result = evaluate(profile, scholarship)
        country_match = profile.get("target_country", "Any") in ("Any", scholarship.get("country"))
        results.append({
            **scholarship,
            **result,
            "ai_similarity": similarity,
            "country_preference": country_match,
        })

    results.sort(
        key=lambda item: (
            item["status"] == "Eligible",
            item["status"] == "Needs Information",
            item["country_preference"],
            item["ai_similarity"],
        ),
        reverse=True,
    )

    labels = {
        "Eligible": "مستوفٍ للشروط المسجلة مبدئيًا",
        "Needs Information": "تحتاج معلومات إضافية",
        "Not Eligible": "لا تستوفي شرطًا أو أكثر",
    }
    c1, c2, c3 = st.columns(3)
    c1.metric("مستوفٍ مبدئيًا", sum(x["status"] == "Eligible" for x in results))
    c2.metric("تحتاج معلومات", sum(x["status"] == "Needs Information" for x in results))
    c3.metric("غير مستوفٍ", sum(x["status"] == "Not Eligible" for x in results))
    st.caption("النتيجة تحليل أولي للشروط الموجودة في قاعدة البيانات، وليست ضمانًا للقبول أو قرارًا من الجهة المانحة.")

    filter_label = st.selectbox("تصفية النتائج", ["الكل", *labels.values()])
    for item in results:
        if filter_label != "الكل" and labels[item["status"]] != filter_label:
            continue
        with st.expander(
            f"{labels[item['status']]} | {item['scholarship_name']} | {item['country']} "
            f"| تشابه نصي {item['ai_similarity']}%"
        ):
            st.write(f"**الجامعة:** {item.get('university', 'غير محدد')}")
            st.write(f"**تقييم الشروط المعروفة:** {item['rule_score']}%")
            st.write(f"**تفضيل الدولة:** {'متوافق' if item['country_preference'] else 'ليست الدولة المفضلة'}")
            if item["reasons"]:
                st.success("شروط متوافقة: " + "؛ ".join(item["reasons"]))
            if item["missing"]:
                st.warning("معلومات ناقصة: " + "؛ ".join(item["missing"]))
            if item["failed"]:
                st.error("شروط غير مستوفاة: " + "؛ ".join(item["failed"]))
            st.write(f"**الموعد:** {item.get('deadline') or 'غير محدد'} | **التمويل:** {item.get('funding_type', 'غير محدد')}")
            if item.get("application_url"):
                st.markdown(f"[زيارة صفحة المنحة]({item['application_url']})")

    export = pd.DataFrame([{
        "scholarship_id": item.get("scholarship_id"),
        "scholarship_name": item.get("scholarship_name"),
        "country": item.get("country"),
        "status": labels[item["status"]],
        "rule_score": item["rule_score"],
        "ai_similarity": item["ai_similarity"],
        "deadline": item.get("deadline"),
    } for item in results])
    st.download_button(
        "تنزيل نتائج المطابقة CSV",
        export.to_csv(index=False).encode("utf-8-sig"),
        "masar_matching_results.csv",
        "text/csv",
    )

elif page == "مقارنة المنح":
    st.subheader("مقارنة المنح")
    choices = scholarships["scholarship_name"].astype(str).tolist()
    selected = st.multiselect("اختر منحتين أو أكثر", choices, default=choices[:2])
    if len(selected) >= 2:
        subset = scholarships[scholarships["scholarship_name"].isin(selected)].set_index("scholarship_name")
        fields = [
            "country", "university", "study_level", "eligible_degrees",
            "eligible_majors", "min_gpa", "gpa_scale", "english_test",
            "min_english_score", "funding_type", "deadline",
        ]
        fields = [field for field in fields if field in subset.columns]
        st.dataframe(subset[fields].T, use_container_width=True)
    else:
        st.info("اختر منحتين على الأقل حتى تظهر المقارنة.")

elif page == "مركز ذكاء MASAR":
    st.subheader("مركز الذكاء الاصطناعي")
    st.write(
        "يستخدم النموذج TF-IDF وCosine Similarity لتحويل النصوص إلى تمثيل رقمي "
        "ثم قياس التشابه بين تخصص المستخدم ووصف المنحة ومتطلباتها."
    )
    st.info(
        "لا ندرّب النموذج على قاعدة بيانات طلاب. تُحسب أوزان TF-IDF وقت المقارنة "
        "من ملف المستخدم ونصوص المنح المتاحة. ومحرك الأهلية المنفصل يتحقق من الشروط الصريحة."
    )
    profile = st.session_state["masar_profile"]
    if not profile:
        st.warning("أنشئ ملفك الأكاديمي أولًا لعرض تحليل مرتبط ببياناتك.")
    else:
        scores = similarity_scores(profile, scholarships.to_dict(orient="records"))
        chart = pd.DataFrame({
            "المنحة": scholarships["scholarship_name"].astype(str),
            "درجة التشابه النصي (%)": scores,
        }).sort_values("درجة التشابه النصي (%)", ascending=False).head(10)
        st.bar_chart(chart.set_index("المنحة"))
        st.caption("درجة التشابه مؤشر لغوي مساعد فقط، وليست نسبة قبول أو احتمال فوز بالمنحة.")

st.divider()
st.markdown(
    '<p class="small-note">MASAR AI Prototype | قاعدة بيانات منح تجريبية | '
    'تحقق دائمًا من المصدر الرسمي قبل إرسال أي طلب.</p>',
    unsafe_allow_html=True,
)
