from pathlib import Path

from learning_analytics.audit import build_source_audit
from learning_analytics.config import Settings

SOURCE_FILES = {
    "courses.csv": ("code_module,code_presentation,module_presentation_length\nAAA,2013J,268\n"),
    "assessments.csv": (
        "code_module,code_presentation,id_assessment,assessment_type,date,weight\n"
        "AAA,2013J,1,TMA,20,100\n"
    ),
    "vle.csv": (
        "id_site,code_module,code_presentation,activity_type,week_from,week_to\n"
        "10,AAA,2013J,resource,?,?\n"
    ),
    "studentInfo.csv": (
        "code_module,code_presentation,id_student,gender,region,highest_education,"
        "imd_band,age_band,num_of_prev_attempts,studied_credits,disability,final_result\n"
        "AAA,2013J,100,F,Region,A Level or Equivalent,?,0-35,0,60,N,Pass\n"
    ),
    "studentRegistration.csv": (
        "code_module,code_presentation,id_student,date_registration,date_unregistration\n"
        "AAA,2013J,100,-30,?\n"
    ),
    "studentAssessment.csv": (
        "id_assessment,id_student,date_submitted,is_banked,score\n1,100,19,0,70\n"
    ),
    "studentVle.csv": (
        "code_module,code_presentation,id_student,id_site,date,sum_click\nAAA,2013J,100,10,1,3\n"
    ),
}


def test_source_audit_calculates_scale_and_missingness(tmp_path: Path) -> None:
    source_dir = tmp_path / "data" / "raw" / "source"
    source_dir.mkdir(parents=True)
    for name, content in SOURCE_FILES.items():
        (source_dir / name).write_text(content, encoding="utf-8")

    settings = Settings(
        project_root=tmp_path,
        raw_dir=tmp_path / "data" / "raw",
        source_dir=source_dir,
        processed_dir=tmp_path / "data" / "processed",
        reports_dir=tmp_path / "reports",
    )
    audit = build_source_audit(settings)

    assert audit["calculated_scale"]["csv_rows"] == 7
    assert audit["calculated_scale"]["unique_students"] == 1
    assert audit["calculated_scale"]["student_module_attempts"] == 1
    assert audit["observed_anomalies"]["missing_imd_band"] == 1
    assert (settings.reports_dir / "source-audit.json").exists()
