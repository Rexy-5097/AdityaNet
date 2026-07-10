# AgentOS Architecture — Engineering Diagrams

> **Version:** 1.0.0 | All diagrams render natively on GitHub using Mermaid.
>
> This document is the definitive visual reference for the AgentOS engineering platform.
> Reference it when onboarding, reviewing architecture, or explaining the system to teammates.

---

## 1. Repository Architecture

```mermaid
graph TD
    Root["🗂 AgentOS Repository Root"] --> AI["📄 AGENTOS.md\nAI Entrypoint"]
    Root --> README["📄 README.md\nProject Overview"]
    Root --> Config["⚙️ PROJECT_CONFIG.yaml\nActive Configuration"]

    Root --> Context["📁 context/\nLive Project State"]
    Root --> Workflows["📁 workflows/\nStandard SOPs"]
    Root --> Agents["📁 agents/\nSpecialist Contracts"]
    Root --> Tools["📁 tools/\nCLI + MCP"]
    Root --> Standards["📁 standards/\nQuality Definitions"]
    Root --> Checklists["📁 checklists/\nQuality Gates"]
    Root --> Runtime["📁 runtime/\nHarness + Loop + Kernel"]
    Root --> Profiles["📁 profiles/\nProject Templates"]
    Root --> Validation["📁 validation/\nSynthetic Suite"]
    Root --> Artifacts["📁 artifacts/\nGenerated Outputs"]
    Root --> Integrations["📁 integrations/\nVendor Adapters"]
    Root --> Examples["📁 examples/\nStarter Projects"]
    Root --> GH["📁 .github/\nGitHub Templates + CI"]

    style Root fill:#1e293b,color:#fff
    style AI fill:#7c3aed,color:#fff
    style Runtime fill:#0f766e,color:#fff
    style Agents fill:#1d4ed8,color:#fff
    style Validation fill:#b45309,color:#fff
```

---

## 2. WAT Architecture (Workflows → Agents → Tools)

```mermaid
graph LR
    subgraph L1["Layer 1 — Workflows (SOPs)"]
        W1[master.md]
        W2[feature_development.md]
        W3[bug_fix.md]
        W4[research.md]
        W5[release.md]
        W6[incident_response.md]
    end

    subgraph L2["Layer 2 — Agents (Decision Makers)"]
        A1[orchestrator]
        A2[chief-architect]
        A3[planner]
        A4[ai-reviewer]
        A5[security-reviewer]
        A6[qa-reviewer]
        A7[docs-reviewer]
        A8[release-reviewer]
    end

    subgraph L3["Layer 3 — Tools (Executors)"]
        T1[harness_engine.py]
        T2[validate_agentos.py]
        T3[bootstrap_project.py]
        T4[execute_suite.py]
        T5[MCP Integrations]
    end

    L1 -->|triggers| L2
    L2 -->|invokes| L3

    style L1 fill:#1e3a5f,color:#fff
    style L2 fill:#1a3a2a,color:#fff
    style L3 fill:#3b1a1a,color:#fff
```

---

## 3. Context Loading Flow

```mermaid
flowchart TD
    Start([Session Starts]) --> ReadAG[Read AGENTOS.md]
    ReadAG --> ReadState[Read context/state.md]
    ReadState --> ReadConfig[Read PROJECT_CONFIG.yaml]
    ReadConfig --> TaskCheck{Task Type?}

    TaskCheck -->|New Project| ReadVision[Read context/vision.md]
    TaskCheck -->|Architecture| ReadArch[Read context/architecture.md\n+ context/decisions.md]
    TaskCheck -->|Feature| ReadWorkflow[Read workflows/\nfeature_development.md]
    TaskCheck -->|Bug Fix| ReadBug[Read workflows/bug_fix.md]
    TaskCheck -->|Release| ReadRelease[Read workflows/release.md]

    ReadVision --> AgentLoad{Agent Needed?}
    ReadArch --> AgentLoad
    ReadWorkflow --> AgentLoad
    ReadBug --> AgentLoad
    ReadRelease --> AgentLoad

    AgentLoad -->|Yes| LoadAgent[Load agents/{agent}.md]
    AgentLoad -->|No| Implement
    LoadAgent --> LoadStd[Load standards/{domain}.md]
    LoadStd --> Implement[Implement Task]
    Implement --> ValidateEnd[Run validate_agentos.py]
    ValidateEnd --> UpdateState[Update context/state.md]

    style Start fill:#22c55e,color:#fff
    style ValidateEnd fill:#7c3aed,color:#fff
    style UpdateState fill:#0ea5e9,color:#fff
```

---

## 4. Harness Runtime Flow

```mermaid
flowchart LR
    Input[("Task\nDescription")] --> Classifier[Task Classifier]
    Classifier --> CtxOpt[Context Optimizer]
    CtxOpt --> Router[Agent Router]
    Router --> |routing.yaml| Policy[(Policy\nLoader)]
    Policy --> Router

    Router --> Planner[planner]
    Router --> Orchestrator[orchestrator]
    Router --> Reviewers[Specialist Reviewers]

    Orchestrator --> Loop[Loop Runtime]
    Planner --> Loop
    Reviewers --> Loop

    Loop --> Report[("Execution\nReport")]

    style Input fill:#1d4ed8,color:#fff
    style Loop fill:#0f766e,color:#fff
    style Report fill:#7c3aed,color:#fff
    style Policy fill:#b45309,color:#fff
```

---

## 5. Loop Runtime — Internal Architecture

```mermaid
flowchart TD
    Entry[("Task\n+ Plan")] --> IC[Iteration Controller]
    IC --> RE[Reflection Engine]
    RE --> IP[Improvement Planner]
    IP --> EM[Execution Monitor]
    EM --> QE[Quality Evaluator]
    QE --> TC{Termination\nCheck}

    TC -->|Below threshold| IC
    TC -->|Threshold met| Exit[("Loop\nReport")]
    TC -->|Max iterations| Escalate[Escalate to\nChief Architect]

    QE --> SM[(State\nMachine)]
    SM --> IC

    style Entry fill:#1d4ed8,color:#fff
    style QE fill:#b45309,color:#fff
    style Exit fill:#22c55e,color:#fff
    style Escalate fill:#dc2626,color:#fff
    style SM fill:#0f766e,color:#fff
```

---

## 6. Agent Routing Flow

```mermaid
flowchart TD
    Task[Task Arrives] --> Harness[Harness Classifier]
    Harness --> Domain{Domain?}

    Domain -->|AI/ML code| AIRev[ai-reviewer]
    Domain -->|Security/Auth| SecRev[security-reviewer]
    Domain -->|Frontend/UI| UIRev[ui-reviewer]
    Domain -->|Performance| PerfRev[performance-reviewer]
    Domain -->|Science/Research| SciRev[science-reviewer]
    Domain -->|QA/Testing| QARev[qa-reviewer]
    Domain -->|Documentation| DocsRev[docs-reviewer]
    Domain -->|Release| RelRev[release-reviewer]
    Domain -->|Cross-domain| Orch[orchestrator]

    AIRev --> Conflict{Conflict?}
    SecRev --> Conflict
    UIRev --> Conflict
    PerfRev --> Conflict
    SciRev --> Conflict
    QARev --> Conflict
    DocsRev --> Conflict
    RelRev --> Conflict
    Orch --> Conflict

    Conflict -->|Yes| CA[chief-architect\nADR logged]
    Conflict -->|No| Gate[Quality Gate]

    CA --> Gate
    Gate --> Done([Task Complete])

    style Task fill:#1d4ed8,color:#fff
    style CA fill:#dc2626,color:#fff
    style Done fill:#22c55e,color:#fff
    style Orch fill:#7c3aed,color:#fff
```

---

## 7. Quality Gate Pipeline

```mermaid
flowchart LR
    Dev[Development\nComplete] --> QG1[QG-001\nFeature Completion]
    QG1 --> QG2[QG-002\nPull Request]
    QG2 --> QG3[QG-003\nQA Signoff]

    QG3 --> Branch{Domain\nSpecific?}
    Branch -->|Research/AI| QG4[QG-004\nResearch Validation]
    Branch -->|Security/Data| QG5[QG-005\nSecurity Review]
    Branch -->|Production| QG6[QG-006\nDeployment]

    QG4 --> QG8
    QG5 --> QG8
    QG6 --> QG8[QG-008\nRelease]
    QG8 --> Released([Released ✅])

    QG1 -->|FAIL| Fix1[Fix & Retry]
    Fix1 --> QG1
    QG5 -->|FAIL| Fix5[Security Fix\n& Retry]
    Fix5 --> QG5

    style Dev fill:#1d4ed8,color:#fff
    style Released fill:#22c55e,color:#fff
    style Fix1 fill:#dc2626,color:#fff
    style Fix5 fill:#dc2626,color:#fff
```

---

## 8. Bootstrap Flow

```mermaid
flowchart TD
    Clone([git clone]) --> MakeBS[make bootstrap\nor\npython3 bootstrap_project.py]
    MakeBS --> Mode{Mode?}

    Mode -->|--interactive| Int[Prompt: Name, Profile,\nGoals, Stack, Deadline]
    Mode -->|--defaults| Def[Use default ai_project\nprofile + defaults]
    Mode -->|--profile X| Prof[Load profiles/X.yaml\n+ use defaults]
    Mode -->|--config file.yaml| Cfg[Parse provided YAML\nconfiguration file]
    Mode -->|--resume| Res[Resume from\nlast checkpoint]

    Int --> Verify[Verify repository\ndirectories]
    Def --> Verify
    Prof --> Verify
    Cfg --> Verify
    Res --> Verify

    Verify --> LoadProfile[Load profiles/{profile}.yaml]
    LoadProfile --> GenConfig[Generate\nPROJECT_CONFIG.yaml]
    GenConfig --> GenContext[Generate\ncontext/vision.md\ncontext/state.md]
    GenContext --> RunVal[Run\nvalidate_agentos.py]
    RunVal --> Check{Score\n= 100?}
    Check -->|YES| Done([Bootstrap\nComplete ✅])
    Check -->|NO| Warn[Surface warnings\nto engineer]

    style Clone fill:#1d4ed8,color:#fff
    style Done fill:#22c55e,color:#fff
    style Warn fill:#f59e0b,color:#fff
```

---

## 9. Runtime Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Uninitialized: git clone

    Uninitialized --> Bootstrapping: make bootstrap

    Bootstrapping --> Initialized: PROJECT_CONFIG.yaml generated\nValidator 100/100

    Initialized --> Active: Task assigned

    Active --> Running: Harness dispatches\nLoop executes

    Running --> UnderReview: Loop threshold met\nReviewer invoked

    UnderReview --> GateCheck: Reviewer PASS

    UnderReview --> Running: Reviewer FAIL\nLoop retries

    GateCheck --> Artifact: Quality Gate PASS\nArtifact generated

    GateCheck --> Running: Quality Gate FAIL

    Artifact --> Active: context/state.md updated

    Active --> Released: QG-008 PASS\nRelease tagged

    Released --> Active: New development cycle

    Active --> [*]: Project archived
```

---

## 10. Project Lifecycle

```mermaid
gantt
    title AgentOS Project Lifecycle
    dateFormat X
    axisFormat Phase %s

    section Foundation
    Bootstrap & Initialize    :done, a1, 0, 1
    Architecture Design       :done, a2, 1, 2

    section Development
    Feature Implementation    :active, b1, 2, 5
    Loop Runtime Iteration    :b2, 2, 5
    Specialist Review         :b3, 3, 5

    section Quality
    Quality Gate Pipeline     :c1, 5, 6
    Artifact Generation       :c2, 5, 6

    section Release
    Release Preparation       :d1, 6, 7
    Release Reviewer Signoff  :d2, 6, 7
    Tag & Publish             :d3, 7, 8
```

---

## 11. Validation Pipeline

```mermaid
flowchart TD
    Trigger([Push / PR\nor Manual]) --> Static[Static Validator\nvalidate_agentos.py]
    Static --> |18 categories| Score{Score\n= 100/100?}
    Score -->|YES| Suite[Synthetic Suite\nexecute_suite.py]
    Score -->|NO| Fail([❌ FAIL\nSurface warnings])

    Suite --> |21 scenarios| AllPass{All 21\nPASS?}
    AllPass -->|YES| Bootstrap[Bootstrap Self-Test\nbootstrap_project.py --self-test]
    AllPass -->|NO| Fail

    Bootstrap --> |8 profiles| SelfPass{Self-Test\nPASS?}
    SelfPass -->|YES| Pass([✅ ALL PASS\nReady])
    SelfPass -->|NO| Fail

    style Trigger fill:#1d4ed8,color:#fff
    style Pass fill:#22c55e,color:#fff
    style Fail fill:#dc2626,color:#fff
```

---

## 12. Artifact Lifecycle

```mermaid
flowchart LR
    Decision[Architectural\nDecision] -->|ADR template| ADR["artifacts/decisions/\nADR-XXXX-title.md"]
    Experiment[Experiment\nCompleted] -->|experiment template| Exp["artifacts/experiments/\nexp-name.md"]
    Incident[Production\nIncident] -->|post-mortem template| PM["artifacts/incidents/\nincident-name.md"]
    Release[Release\nCut] -->|release template| RN["artifacts/releases/\nrelease-notes.md"]
    Review[Architecture\nReview] -->|review template| AR["artifacts/reviews/\nreview-name.md"]

    ADR --> Index[context/decisions.md\nADR Index]
    ADR --> Manifest[.agentos/manifest.yml\nFile Inventory]

    style ADR fill:#7c3aed,color:#fff
    style Exp fill:#0f766e,color:#fff
    style PM fill:#dc2626,color:#fff
    style RN fill:#1d4ed8,color:#fff
    style AR fill:#b45309,color:#fff
```

---

## 13. Repository Directory Map

```mermaid
graph TD
    Root["/ (root)"] --> A["📄 AGENTOS.md"]
    Root --> R["📄 README.md"]
    Root --> D["📄 ARCHITECTURE.md"]
    Root --> PC["⚙️ PROJECT_CONFIG.yaml"]
    Root --> MK["🔧 Makefile"]

    Root --> ctx["📁 context/"]
    ctx --> cv["vision.md"]
    ctx --> cs["state.md"]
    ctx --> ca["architecture.md"]
    ctx --> cd["decisions.md"]

    Root --> wf["📁 workflows/"]
    wf --> wm["master.md"]
    wf --> wf2["feature_development.md"]

    Root --> ag["📁 agents/"]
    ag --> ao["orchestrator.md"]
    ag --> ac["chief-architect.md"]
    ag --> ar["*-reviewer.md ×8"]

    Root --> rt["📁 runtime/"]
    rt --> rh["harness/"]
    rt --> rl["loop/"]
    rt --> rk["kernel/"]

    Root --> vl["📁 validation/"]
    vl --> vs["scenarios/ ×21"]
    vl --> vr["runner/"]

    Root --> prof["📁 profiles/ ×8"]
    Root --> ex["📁 examples/ ×5"]
    Root --> int["📁 integrations/ ×4"]
    Root --> gh["📁 .github/"]
    gh --> ghw["workflows/ ×3"]
    gh --> ghi["ISSUE_TEMPLATE/ ×3"]

    style Root fill:#1e293b,color:#fff
    style rt fill:#0f766e,color:#fff
    style vl fill:#b45309,color:#fff
```

---

## 14. Context Loading Strategy

```mermaid
quadrantChart
    title Context Loading Priority (Load Frequency vs. Token Cost)
    x-axis Low Token Cost --> High Token Cost
    y-axis Low Load Frequency --> High Load Frequency
    quadrant-1 Always Load
    quadrant-2 Load Eagerly
    quadrant-3 Load On Demand
    quadrant-4 Load Sparingly

    AGENTOS.md: [0.1, 0.95]
    context/state.md: [0.15, 0.9]
    PROJECT_CONFIG.yaml: [0.05, 0.85]
    context/vision.md: [0.2, 0.5]
    agents/planner.md: [0.2, 0.55]
    agents/orchestrator.md: [0.2, 0.5]
    standards/code_quality.md: [0.3, 0.45]
    standards/security.md: [0.35, 0.35]
    context/decisions.md: [0.45, 0.4]
    artifacts/decisions: [0.85, 0.2]
    runtime/ internals: [0.9, 0.1]
    validation/scenarios: [0.8, 0.1]
```

---

## 15. Release Pipeline

```mermaid
flowchart LR
    Code[Feature\nComplete] --> QG1[QG-001] --> QG2[QG-002\nPR Review]
    QG2 --> QG3[QG-003\nQA]
    QG3 --> QG5[QG-005\nSecurity]
    QG5 --> RR[release-reviewer\nSignoff]
    RR --> QG8[QG-008\nRelease Gate]
    QG8 --> Bump[Bump VERSION\nUpdate CHANGELOG]
    Bump --> Tag["git tag v1.x.y"]
    Tag --> CI[GitHub Actions\nrelease.yml]
    CI --> Validate[Run Validator\n+ Suite]
    Validate --> |PASS| GH[GitHub Release\nPublished]
    Validate --> |FAIL| Block[❌ Release Blocked]

    style Code fill:#1d4ed8,color:#fff
    style GH fill:#22c55e,color:#fff
    style Block fill:#dc2626,color:#fff
```

---

## 16. AI Interaction Flow

```mermaid
sequenceDiagram
    participant H as Human Engineer
    participant AI as AI Assistant
    participant AG as AGENTOS.md
    participant CTX as context/
    participant HN as Harness
    participant LP as Loop Runtime
    participant REV as Reviewer Agent
    participant VAL as Validator

    H->>AI: Open repository
    AI->>AG: Discover & read AGENTOS.md
    AG-->>AI: Initialization protocol
    AI->>CTX: Load state.md + PROJECT_CONFIG.yaml
    CTX-->>AI: Project state
    AI->>H: "AgentOS initialized. Profile: [X]. Ready."

    H->>AI: "Build JWT authentication"
    AI->>HN: Dispatch task
    HN->>HN: Classify domain (security)
    HN->>LP: Execute loop (Balanced)
    LP->>REV: security-reviewer
    REV-->>LP: Iteration feedback
    LP->>LP: Iterate until threshold met
    LP-->>AI: Loop report (3 iterations, PASS)

    AI->>VAL: python3 validate_agentos.py
    VAL-->>AI: 100/100 PASS
    AI->>CTX: Update context/state.md
    AI->>H: "Task complete. Quality: 100/100. All gates: PASS."
```

---

## 17. Documentation Cross-References

```mermaid
graph LR
    AG["AGENTOS.md\n(entrypoint)"] -->|reads| README
    AG -->|reads| CTX["context/state.md"]
    AG -->|reads| PC["PROJECT_CONFIG.yaml"]
    AG -->|loads| BOOT["BOOTSTRAP.md"]

    README -->|links| ARCH["ARCHITECTURE.md"]
    README -->|links| TQ["TEAM_QUICKSTART.md"]
    README -->|links| EP["ENGINEERING_PRINCIPLES.md"]
    README -->|links| DOC["DOCUMENTATION_INDEX.md"]

    DOC -->|indexes| STD["standards/ ×9"]
    DOC -->|indexes| CL["checklists/ ×8"]
    DOC -->|indexes| PROF["profiles/ ×8"]
    DOC -->|indexes| EX["examples/ ×5"]
    DOC -->|indexes| INT["integrations/ ×4"]

    BOOT -->|triggers| TOOLS["tools/scripts/\nbootstrap_project.py"]
    TOOLS -->|generates| PC
    TOOLS -->|generates| CTX

    style AG fill:#7c3aed,color:#fff
    style ARCH fill:#0f766e,color:#fff
    style DOC fill:#1d4ed8,color:#fff
```

---

## 18. Decision Flow (Architectural Decision Records)

```mermaid
flowchart TD
    Event[Architectural\nDecision Needed] --> CA[chief-architect\nAgent Invoked]
    CA --> Template["Load\ntemplates/decision_record.md"]
    Template --> Draft[Draft ADR:\nContext, Options, Decision, Consequences]
    Draft --> Review{Reviewer\nConsensus?}
    Review -->|YES| Number["Assign ADR-XXXX\nNumber"]
    Review -->|NO| Iterate[Revise with\nreviewer feedback]
    Iterate --> Review

    Number --> Save["Save to\nartifacts/decisions/\nADR-XXXX-title.md"]
    Save --> Index["Update\ncontext/decisions.md"]
    Index --> Manifest["Update\n.agentos/manifest.yml"]
    Manifest --> Done([ADR Complete ✅])

    style Event fill:#1d4ed8,color:#fff
    style Done fill:#22c55e,color:#fff
    style CA fill:#b45309,color:#fff
```

---

## 19. Escalation Flow

```mermaid
flowchart TD
    Task[Task Assigned] --> Review[Specialist Review]
    Review --> Conflict{Reviewers\nConflict?}

    Conflict -->|No conflict| Gate[Quality Gate]
    Conflict -->|Conflict detected| Escalate[Escalate to\nchief-architect]

    Escalate --> CA[Chief Architect\nEvaluates options]
    CA --> ADR[Log ADR\nDocument rationale]
    ADR --> Decision[Binding\nDecision issued]
    Decision --> Gate

    Gate -->|PASS| Done([Task Complete ✅])
    Gate -->|FAIL| Retry[Loop retries]
    Retry --> Review

    style Escalate fill:#dc2626,color:#fff
    style CA fill:#b45309,color:#fff
    style Done fill:#22c55e,color:#fff
    style ADR fill:#7c3aed,color:#fff
```

---

## 20. Runtime State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE: System Ready

    IDLE --> CLASSIFYING: Task received

    CLASSIFYING --> ROUTING: Domain identified

    ROUTING --> PLANNING: Agents selected

    PLANNING --> EXECUTING: Plan approved

    EXECUTING --> REFLECTING: Iteration complete

    REFLECTING --> IMPROVING: Reflection done

    IMPROVING --> MONITORING: Plan updated

    MONITORING --> EVALUATING: Execution observed

    EVALUATING --> TERMINATING: Quality threshold met
    EVALUATING --> REFLECTING: Below threshold

    TERMINATING --> IDLE: Loop report generated\nContext updated

    EXECUTING --> ESCALATING: Error detected

    ESCALATING --> IDLE: Chief architect resolves
```

---

## 21. Synthetic Validation Flow

```mermaid
flowchart TD
    Start([execute_suite.py]) --> Manifest["Load\nvalidation/manifest.yaml"]
    Manifest --> Scenarios["21 Scenarios\nVS-001 to VS-021"]

    Scenarios --> Loop{For each\nscenario}
    Loop --> LoadScenario["Load scenario.md\ninput/ + assertions.yaml"]
    LoadScenario --> Execute["execute_scenario.py\nRun assertions"]
    Execute --> Assert{All assertions\nPASS?}

    Assert -->|YES| RecordPass["Record PASS\nScore: 100/100"]
    Assert -->|NO| RecordFail["Record FAIL\nLog reason"]

    RecordPass --> Loop
    RecordFail --> Loop

    Loop -->|Done| Report["Generate\nSuite Report"]
    Report --> Check{21/21\nPASS?}
    Check -->|YES| Success(["✅ SUCCESS\n100% coverage"])
    Check -->|NO| Failure(["❌ FAILURE\nSurface broken scenarios"])

    style Start fill:#1d4ed8,color:#fff
    style Success fill:#22c55e,color:#fff
    style Failure fill:#dc2626,color:#fff
```

---

*AgentOS v1.0.0 — Architecture diagrams. All diagrams render on GitHub using Mermaid.*
