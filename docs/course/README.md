# Learning Analytics Course Edition 0.1

This directory contains the standalone LaTeX course:

**Learning Analytics with OULAD: Working Through a Real Data Project Together**

Edition 0.1 fully teaches course orientation, learning analytics, the OULAD
source tables, relational foundations, PostgreSQL setup, raw-data import, data
validation, introductory SQL, exercises, and guided solutions. Later course
chapters are explicitly marked as forthcoming.

## Build

Requirements:

- A TeX distribution with `latexmk`, `pdflatex`, and `bibtex`
- The LaTeX packages used by `course-style.sty`

From the repository root, run this exact command:

```bash
cd docs/course && latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error -outdir=generated learning_analytics_course.tex
```

The generated PDF is:

```text
docs/course/generated/learning_analytics_course.pdf
```

To remove auxiliary build files while keeping the PDF:

```bash
cd docs/course && latexmk -c -outdir=generated learning_analytics_course.tex
```

## Structure

- `learning_analytics_course.tex`: master source
- `course-style.sty`: typography, code-listing, and instructional-box styles
- `chapters/`: completed chapters, exercises, solutions, glossary, and future architecture
- `figures/`: figures copied from verified project outputs for this course edition
- `references.bib`: bibliography
- `generated/`: compiled PDF and temporary LaTeX build files

## Scope

All new material is confined to `docs/course/`. The course explains the
existing implementation; it does not change SQL, Python, models, raw data,
database contents, analytical results, dashboard code, or production
configuration.
