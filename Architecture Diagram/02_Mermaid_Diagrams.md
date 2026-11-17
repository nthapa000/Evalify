# Evalify: Architecture Diagrams

Five diagrams that together explain the system. Sequence diagrams (what happens over time) are in
[03_Sequence_Diagrams.md](03_Sequence_Diagrams.md). The written design is in
[01_High_Level_Design.md](01_High_Level_Design.md).

Colours used in every diagram: people in grey, the application in blue, data in yellow, AI models in green.

1. System architecture
2. Marking pipeline
3. Data model
4. Answer sheet life cycle
5. Deployment

---

## 1. System architecture

The three users work in one web application. The backend stores everything in MongoDB and on disk, and asks the
AI models on the GPU node to read and grade.

```mermaid
flowchart LR
    subgraph USERS["Users"]
        T(["Teacher"]):::person
        TA(["TA"]):::person
        S(["Student"]):::person
    end

    subgraph APP["Evalify application"]
        FE["Web app<br/>React"]:::app
        BE["Backend API<br/>FastAPI"]:::app
        PL["Marking pipeline<br/>batch runner"]:::app
    end

    subgraph STORE["Storage"]
        DB[("MongoDB<br/>users, papers,<br/>submissions, batches")]:::data
        FS[("Files<br/>sheet photos, PDFs")]:::data
    end

    subgraph GPU["AI models on GPUs"]
        GM["Gemma<br/>reads, transcribes, grades"]:::model
        QW["Qwen<br/>second reader"]:::model
        GL["GLM-OCR<br/>tie-breaker"]:::model
    end

    USERS --> FE
    FE -->|"/api"| BE
    BE --> PL
    BE --> STORE
    PL --> GPU

    style USERS fill:#ffffff,stroke:#b9b6ab
    style APP fill:#f7f7f4,stroke:#b9b6ab
    style STORE fill:#f7f7f4,stroke:#b9b6ab
    style GPU fill:#f7f7f4,stroke:#b9b6ab
    classDef person fill:#eceae4,stroke:#6b6656,color:#1f1d18
    classDef app fill:#dfe8f3,stroke:#2f5d8a,color:#14273b
    classDef data fill:#f6ecd2,stroke:#9a7a2c,color:#3a2e10
    classDef model fill:#e1efe1,stroke:#3f7a45,color:#163018
```

## 2. Marking pipeline

How one answer sheet becomes marks. Numbers are marked by code, language by the model, and anything doubtful goes to
a TA.

```mermaid
flowchart TB
    IN["Sheet photos"]:::app --> QG["Quality check<br/>straighten, blur, glare"]:::app
    QG --> TYPE{"Sheet type"}

    TYPE -->|"OMR"| OMR["Read bubbles using the<br/>teacher's blank sheet"]:::app
    TYPE -->|"Handwritten"| RD["Two AI readers<br/>Gemma and Qwen"]:::model
    RD --> AG{"Same answer?"}
    AG -->|"Yes"| OK["Accept"]:::app
    AG -->|"No"| TB["Third reader decides<br/>GLM-OCR, 2 of 3"]:::model
    RD --> TX["Transcribe written answers"]:::model

    OMR --> SC["Mark MCQ and numerical<br/>in code, against the key"]:::app
    OK --> SC
    TB --> SC
    TX --> GR["Grade written answers<br/>Gemma, against the rubric"]:::model

    SC --> FL{"Unsure?"}
    GR --> FL
    FL -->|"No"| DONE["Marks saved"]:::data
    FL -->|"Yes"| TAQ["Sent to TA<br/>with one reason"]:::person

    class TYPE,AG,FL decision
    classDef decision fill:#ffffff,stroke:#6b6656,color:#1f1d18
    classDef person fill:#eceae4,stroke:#6b6656,color:#1f1d18
    classDef app fill:#dfe8f3,stroke:#2f5d8a,color:#14273b
    classDef data fill:#f6ecd2,stroke:#9a7a2c,color:#3a2e10
    classDef model fill:#e1efe1,stroke:#3f7a45,color:#163018
```

Reasons a question goes to the TA: a poor photo, the readers disagree, a half-filled bubble, every option looks
filled, the grader is unsure, or a random 5 % quality check.

## 3. Data model

Four collections in MongoDB. A teacher owns papers, a student owns submissions, and a batch groups the submissions of
one "Start evaluation".

```mermaid
erDiagram
    USER ||--o{ PAPER : "teacher creates"
    USER ||--o{ SUBMISSION : "student uploads"
    PAPER ||--o{ SUBMISSION : "receives"
    PAPER ||--o{ BATCH : "evaluated in"
    BATCH ||--o{ SUBMISSION : "processes"

    USER {
        string role "teacher, ta or student"
        string login "email or roll number"
        string name
        list subjects
    }
    PAPER {
        string name
        string subject
        string type "A, B or C"
        dict answer_keys
        list rubrics
        dict omr_template
        bool results_released
    }
    SUBMISSION {
        list page_photos
        string sheet_type "omr or handwritten"
        string status
        dict result "marks per question"
        list review "TA flags"
        list marks_history
    }
    BATCH {
        string status "running, done or failed"
        string stage "reading or grading"
        int total
    }
```

## 4. Answer sheet life cycle

Uploads wait until the teacher starts the evaluation. Every sheet is read first, then graded. A failed sheet can be
sent again.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Submitted: student uploads
    Submitted --> Reading: teacher clicks<br/>Start evaluation
    Reading --> Grading: all sheets read
    Grading --> Evaluated: marks saved
    Reading --> Error: failed
    Grading --> Error: failed
    Error --> Reading: start again
    Evaluated --> Released: teacher releases
    Released --> [*]
```

## 5. Deployment

Where each part runs on the IIT Jodhpur cluster. The user reaches the app through port forwarding.

```mermaid
flowchart LR
    U(["Browser on<br/>your computer"]):::person

    subgraph LN["Login node"]
        FE["Web app<br/>port 5173"]:::app
        BE["Backend API<br/>port 47823"]:::app
        DB[("MongoDB<br/>port 27027")]:::data
    end

    subgraph CN["GPU node cn07, Slurm job"]
        subgraph G1["RTX A6000, 48 GB"]
            GA["Gemma copy 1"]:::model
        end
        subgraph G2["RTX PRO 6000, 96 GB"]
            GB["Gemma copy 2"]:::model
            QW["Qwen"]:::model
            GL["GLM-OCR"]:::model
        end
    end

    U -->|"port forwarding"| FE
    FE --> BE
    BE --> DB
    BE -->|"model requests"| CN

    style LN fill:#f7f7f4,stroke:#b9b6ab
    style CN fill:#f7f7f4,stroke:#b9b6ab
    style G1 fill:#ffffff,stroke:#b9b6ab
    style G2 fill:#ffffff,stroke:#b9b6ab
    classDef person fill:#eceae4,stroke:#6b6656,color:#1f1d18
    classDef app fill:#dfe8f3,stroke:#2f5d8a,color:#14273b
    classDef data fill:#f6ecd2,stroke:#9a7a2c,color:#3a2e10
    classDef model fill:#e1efe1,stroke:#3f7a45,color:#163018
```

The GPU job writes the address of each model into an endpoints file, and the backend reads it, so nothing is
configured by hand. Two copies of Gemma share its work because it does the most: reading, transcribing and grading;
each request goes to the less busy copy.
