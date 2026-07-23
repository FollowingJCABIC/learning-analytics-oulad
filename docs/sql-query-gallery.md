# SQL query gallery

All complete executable queries are in
[`sql/gallery/queries.sql`](../sql/gallery/queries.sql).

| # | Analytical question | Concepts | Source/output | Interpretation and limitation |
| ---: | --- | --- | --- | --- |
| 1 | What are the verified row counts and grains? | `UNION ALL`, counts | `raw.*` | Establishes scale; counts do not establish quality. |
| 2 | How do people differ from attempt records? | distinct count | `core.student_attempts` | Prevents inflated unique-student claims. |
| 3 | How do outcomes vary by presentation? | conditional aggregation | `analytics.course_outcome_summary` | Descriptive; presentations differ in design and population. |
| 4 | How do registration, engagement, and outcomes join? | left join, aggregation | core plus weekly mart | Shows attempt-level integration; clicks do not explain outcomes. |
| 5 | Which quality checks fail or profile missingness? | persisted test results | `quality.latest_results` | Makes warnings visible; a pass does not prove semantic validity. |
| 6 | What assessment progress is observable? | `FILTER`, weighted sum | assessment mart | Missing records may have multiple causes. |
| 7 | What is the weekly engagement grain? | materialized mart | weekly engagement | Active weeks only; zero-activity weeks require snapshots. |
| 8 | How did activity change from the prior observed week? | `LAG` | weekly engagement | Prior observed week is not always the prior calendar week. |
| 9 | What was rolling fourteen-day activity? | window frame | weekly engagement | Uses current and previous weekly bucket. |
| 10 | Where did an attempt rank within its cohort-week? | `percent_rank` | weekly engagement | Relative rank depends on cohort composition. |
| 11 | What was the longest observed inactivity gap? | `LAG`, CTE | interaction fact | Boundary gaps before first and after last activity need separate handling. |
| 12 | How does activity align with withdrawal timing? | relative-time alignment | withdrawal mart | Association cannot identify withdrawal reasons. |
| 13 | How did weighted progress accumulate? | cumulative window | assessment mart | Assessment structures vary by module. |
| 14 | What enters a weekly model snapshot? | point-in-time features, lateral join | feature mart | The future label is excluded from features. |
| 15 | What plans were captured for optimization? | JSON plan extraction | performance runs | Timings are local and workload-specific. |
