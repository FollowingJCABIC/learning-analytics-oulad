# Data dictionary

`availability` states when a field can be used in a weekly forecast.

| Source field | Transformed field | Type | Description | Null behavior | Target model | Availability |
| --- | --- | --- | --- | --- | --- | --- |
| `courses.code_module` | `code_module` | text | anonymized module code AAA-GGG | not null | categorical | registration |
| `courses.code_presentation` | `code_presentation` | text | year and B/J start term | not null | split/context | registration |
| `studentInfo.id_student` | `id_student` | integer | anonymized person identifier | not null | excluded identifier | registration |
| `studentInfo.final_result` | `final_result` | category | Distinction, Pass, Fail, Withdrawn | not null | excluded outcome | course end |
| `studentRegistration.date_registration` | `registration_day` | integer | day relative to presentation start | profile missing | eligibility only | recorded registration |
| `studentRegistration.date_unregistration` | `unregistration_day` | integer | recorded ending day | null means no recorded unregistration | eligibility, never feature | when recorded |
| `studentVle.date` | `activity_day` | integer | relative interaction day | not null | feature input | interaction day |
| `studentVle.sum_click` | `click_count` | integer | interactions for source row | nonnegative | feature input | interaction day |
| derived | `clicks_7d` | bigint | clicks in snapshot week | zero for no activity | numeric | snapshot |
| derived | `clicks_14d` | bigint | current and previous week clicks | zero for no activity | numeric | snapshot |
| derived | `days_since_activity` | numeric | snapshot minus latest observed day | null if none | numeric | snapshot |
| `assessments.date` | `due_day` | integer | expected submission day | exam dates may be null | eligibility | source schedule |
| `studentAssessment.date_submitted` | `submitted_day` | integer | recorded relative submission day | absent row means no submission | feature input | submission |
| `studentAssessment.score` | `score` | numeric | recorded 0-100 mark | may be null | feature input | submission recorded |
| derived | `mean_score_to_date` | numeric | mean score submitted by snapshot | median-imputed in pipeline | numeric | snapshot |
| derived | `missing_due_to_date` | integer | already-due assessments without submission | zero when none | numeric | snapshot |
| derived | `target_next_assessment_event` | binary | next assessment absent or below 40 | eligible snapshots only | target | after next due day |
| derived | `target_withdrawal_28d` | binary | recorded unregistration in the next 28 days | zero when no event is recorded | secondary target | after 28-day horizon |

Allowed values and constraints are implemented in `sql/03_core.sql`. The
complete feature timing registry is executable in
`features.availability_registry`.
