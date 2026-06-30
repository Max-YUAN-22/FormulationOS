# FormulationOS — Paper

This directory contains the working draft of the FormulationOS paper.

## Status

🚧 **Skeleton only.** Sections are placeholders to be filled in as the implementation lands.

## Structure

```
paper/
├── README.md                 # this file
├── slogan.md                 # the paper's one-line message
├── outline.md                # section-by-section plan
├── abstracts/
│   └── v1.md                 # first version of the abstract
├── sections/
│   ├── 01_introduction.md
│   ├── 02_related_work.md
│   ├── 03_scientific_workflow_abstraction.md
│   ├── 04_formulationos_architecture.md
│   ├── 05_sts_extension_schema.md
│   ├── 06_implementation.md
│   ├── 07_evaluation.md
│   └── 08_discussion.md
├── figures/                  # tikz/fig placeholders + descriptions
└── experiments/
    └── plan.md               # 7 system evaluations
```

## Workflow

For each Task that lands in the codebase:

1. Update the relevant section file with prose reflecting what was built.
2. Add or update the corresponding figure description in `figures/`.
3. If the Task contributes an evaluation, update `experiments/plan.md`.
4. Note the commit hash that implements the Task in the section.

## Target venue

AI Systems venue (TBD). Targeting ~8 pages main + unlimited references and supplementary.