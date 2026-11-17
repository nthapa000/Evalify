# Evalify: Sequence Diagrams

Four diagrams of what happens over time, from the whole round down to the details. The structure of the system is in
[02_Mermaid_Diagrams.md](02_Mermaid_Diagrams.md). The written design is in
[01_High_Level_Design.md](01_High_Level_Design.md).

1. One exam round, end to end
2. Start evaluation: the batch
3. TA review and re-evaluation
4. Answer-key assistant (RAG)

---

## 1. One exam round, end to end

The whole journey of a paper: the teacher creates it, students upload their sheets, the system marks them when the
teacher starts the evaluation, a TA checks the doubtful answers, and the teacher releases the marks. The picture
`images/06_sequence_exam_round.jpg` is the same diagram drawn in a hand-sketched style (`sketch/sketch06.mjs`).

```mermaid
sequenceDiagram
    autonumber
    participant T as Teacher
    participant S as Student
    participant TA as TA
    participant E as Evalify
    participant AI as AI models

    T->>E: Create paper
    S->>E: Upload answer sheet photos
    E-->>S: Submitted, waiting for evaluation
    T->>E: Start evaluation
    E->>AI: Read handwritten sheets, grade written answers
    AI-->>E: Answers and grades
    Note over E: MCQ, numerical and OMR are marked in code.<br/>Doubtful answers go to the TA.
    E-->>T: Results ready
    TA->>E: Check flagged answers, set final marks
    T->>E: Release results
    S->>E: Open result
    E-->>S: Marks and question-wise breakdown
```

## 2. Start evaluation: the batch

What happens after the teacher clicks the button. The batch runs in the background: every sheet is read first, then
every sheet is graded, 32 at a time. Meanwhile the page shows the progress. OMR sheets are read from the bubbles
without the AI models, and MCQ and numerical answers are marked in code.

```mermaid
sequenceDiagram
    autonumber
    actor T as Teacher
    participant UI as Web app
    participant API as Backend
    participant DB as MongoDB
    participant AI as AI models

    T->>UI: Click Start evaluation
    UI->>API: Start evaluation for this paper
    API->>DB: Create batch, queue every waiting sheet
    API-->>UI: Started

    par Batch runs in the background
        Note over API,AI: Stage 1: read every sheet, 32 at a time
        API->>AI: Read page (two readers, a third if they disagree)
        AI-->>API: Answers
        API->>DB: Save readings
        Note over API,AI: Stage 2 starts when every sheet is read
        API->>AI: Grade written answers against the rubric
        AI-->>API: Marks with evidence
        API->>DB: Save marks and TA flags
    and Page checks progress every 5 seconds
        UI->>API: Progress?
        API-->>UI: Stage, counts, time running
    end

    UI-->>T: Evaluation finished, results shown
```

If a sheet fails it is marked as an error and the rest carry on. The next Start evaluation picks it up again. If the
backend restarts, the batch continues from where it stopped.

## 3. TA review and re-evaluation

A TA checks what the system flagged. A student may ask once for a re-evaluation, which also goes to a TA. Every
change of marks is kept in the history.

```mermaid
sequenceDiagram
    autonumber
    actor S as Student
    actor TA as TA
    participant API as Backend
    participant DB as MongoDB

    rect rgb(240, 238, 232)
    Note over TA,DB: Flagged by AI
    TA->>API: Open review queue
    API->>DB: Flagged sheets of the TA's subjects
    API-->>TA: Sheet photo, AI reading, reason, answer key
    TA->>API: Final marks and remark
    API->>DB: Save marks and history
    end

    rect rgb(248, 243, 228)
    Note over S,DB: Re-evaluation (once per paper)
    S->>API: Request re-evaluation with a remark
    API->>DB: Request pending
    TA->>API: Check sheet, set final marks
    API->>DB: Save marks, request resolved
    S->>API: Open result
    API-->>S: New marks and their history
    end
```

## 4. Answer-key assistant (RAG)

Optional, for papers with written answers. It finds the right passages in the teacher's notes and drafts a reference
answer with rubric points. The teacher checks and edits the draft before using it.

```mermaid
sequenceDiagram
    autonumber
    actor T as Teacher
    participant API as Backend
    participant K as Search (BM25)
    participant AI as Gemma

    T->>API: Upload notes (PDF or text) and the questions
    API->>K: Split notes into passages
    loop each question
        K->>K: Find the 5 most relevant passages
        K->>AI: Question and passages
        AI-->>K: Draft answer and rubric points, citing passages
    end
    API-->>T: Drafts with sources (file and page)
    T->>T: Check and edit, then use in the rubric
```
