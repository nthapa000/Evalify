# Architecture Diagram

Design documents of Evalify, written on 17 Nov 2026 for the branch `pipeline-v2`.

| File | Content |
|---|---|
| [01_High_Level_Design.md](01_High_Level_Design.md) | The detailed high level design: purpose, requirements, architecture, components, data design, marking pipeline, model serving and deployment, security, failure handling, performance, decisions and open items |
| [02_Mermaid_Diagrams.md](02_Mermaid_Diagrams.md) | 5 architecture diagrams: system architecture, marking pipeline, data model, answer sheet life cycle, deployment |
| [03_Sequence_Diagrams.md](03_Sequence_Diagrams.md) | 4 sequence diagrams: one exam round end to end, the evaluation batch, TA review and re-evaluation, answer-key assistant |

## Images (JPG)

The same diagrams as ready-made pictures, for slides and reports, in [images/](images/):

| Image | Diagram |
|---|---|
| `01_system_architecture.jpg` | System architecture |
| `02_marking_pipeline.jpg` | Marking pipeline |
| `03_data_model.jpg` | Data model |
| `04_answer_sheet_life_cycle.jpg` | Answer sheet life cycle |
| `05_deployment.jpg` | Deployment on the cluster |
| `06_sequence_exam_round.jpg` | Sequence: one exam round, end to end |
| `07_sequence_start_evaluation.jpg` | Sequence: Start evaluation, the batch |
| `08_sequence_ta_review_reevaluation.jpg` | Sequence: TA review and re-evaluation |
| `09_sequence_answer_key_assistant.jpg` | Sequence: answer-key assistant |
| `10_rag_architecture.jpg` | RAG answer-key assistant: pipeline blocks (hand-drawn style) |
| `11_rag_sequence.jpg` | RAG answer-key assistant: sequence (hand-drawn style) |

Images 01 to 05 and 07 to 09 were rendered from the Markdown files with the Mermaid CLI (3x scale, white background)
and converted to JPG. Images 06, 10 and 11 are drawn in a hand-sketched style by the scripts in [sketch/](sketch/).
After changing a diagram, render it again so the picture matches.

## Viewing the diagrams

The diagrams are Mermaid blocks inside Markdown files.

- GitHub and GitLab show them as pictures when you open the file.
- VS Code: install the extension "Markdown Preview Mermaid Support", then open the Markdown preview.
- To make image files: `npx @mermaid-js/mermaid-cli -i 02_Mermaid_Diagrams.md -o diagrams.md` writes each diagram as an image (needs a browser engine installed).

All diagrams were checked with the Mermaid parser (version 10.9) and parse without errors. Colours are the same in
every diagram: people grey, application blue, data yellow, AI models green.

## Keeping them up to date

The diagrams describe the code as it is on the date above. When a flow changes (for example the batch stages, the
model layout in `infra/models.yaml`, or a new router), update the matching diagram in the same change.
