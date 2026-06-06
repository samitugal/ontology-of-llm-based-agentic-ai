# Ontology of LLM-Based Agentic AI

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20571345.svg)](https://doi.org/10.5281/zenodo.20571345)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An OWL 2 ontology that provides a **framework-independent, formally verifiable conceptual model** for Large Language Model (LLM) based agent systems.

Modern agent frameworks (LangChain, AutoGen, CrewAI, …) express similar
concepts — agents, tools, memory, sessions, orchestration — under different
names and abstractions, and no shared, reasoner-checkable model exists across
them. This ontology fills that gap: it captures the internal architecture of an
LLM agent in a single OWL 2 model, aligns it with the **OASIS 2** foundational
agent ontology, and validates the design with a reasoner, SPARQL competency
questions, a pitfall scanner, and an empirical mapping to real framework code.

> Base IRI: `http://www.ege.edu.tr/cs/ontology/llm-agent#`

## At a glance

| | |
|---|---|
| Classes | **47** |
| Object properties | **51** |
| Data properties | **79** |
| Layers | **6** |
| Foundational ontology | **OASIS 2** (`owl:imports` + `subClassOf` alignment) |
| Language / profile | OWL 2 (RDF/XML) |
| Reasoner | HermiT — consistent, 0 unsatisfiable classes |
| Design quality | OOPS! — **0 Critical** pitfalls |

## The six layers

1. **Core entities** — `Agent` (⊑ `oasis:Agent`), `AgentGroup`, `AgentTemplate`, `Role`, `Policy`, `ModelConfiguration`
2. **Interaction & flow** — `Session`, `Message` (`UserMessage`, `AgentMessage`), `MessageRole`, `Observation`, `Context`
3. **Capability layer** — `Capability` (⊑ `oasis:Behaviour`), `Tool`, `ToolCall`, `ToolResult`, `Resource`, `Action`
4. **Memory layer** — `Memory` → `ShortTermMemory`, `LongTermMemory`, `EpisodicMemory`, `SemanticMemory`; `MemoryStrategy` → `Retrieval`/`Compression`/`Eviction`
5. **Model & configuration** — `LLMModel`, `Parameter`, `Prompt` (`SystemPrompt`, `UserPrompt`), `PromptTemplate`
6. **Orchestration & communication** — `Task`/`Subtask`, `Plan`, `Workflow`, `Delegation`, `ExecutionContext`, `Channel`, `Protocol`

### Defined (inferred) agent types

Three OWL 2 equivalence classes let a reasoner classify agent individuals automatically:

- `AutonomousAgent ≡ Agent ⊓ ∃hasMemory.Memory ⊓ ∃makesToolCall.ToolCall`
- `MemoryAugmentedAgent ≡ Agent ⊓ ∃hasMemory.LongTermMemory`
- `PlanningAgent ≡ Agent ⊓ ∃createsPlan.Plan ⊓ ¬(∃makesToolCall.ToolCall)`

## Repository layout

```
ontology/              Source ontology (hand-authored)
  agentic-ontology.rdf   Primary OWL 2 ontology (RDF/XML)
  agentic-ontology.owl   Same ontology, OWL/XML serialization
  oasis2.owl             OASIS 2 reference terms
  oasis2-stub.owl        Minimal OASIS 2 stub for import resolution
  catalog-v001.xml       Protégé import catalog
  add_annotations.py     Generator script: injects rdfs:label/comment annotations
sparql/                Competency-question queries + result sets
  q1..q7 *.rq            SPARQL 1.1 queries (one per competency question)
  *_result.csv           Query results over the reasoned ontology
framework-mapping/     Empirical framework-independence check
  reflect.py             Extracts live class hierarchies via Python reflection (__mro__)
  reflection.json/.txt   Mapping of LangChain & CrewAI classes to ontology terms
paper/                 Academic paper describing the ontology
  main.tex / main.pdf
```

## Validation

The design is validated three independent ways:

1. **Reasoning (HermiT).** The ontology loaded with OASIS 2 is *consistent*; no
   class is unsatisfiable, all `AllDisjointClasses` axioms hold, and defined
   classes classify individuals as expected (e.g. `CodeExecutorAgent` →
   `AutonomousAgent` + `MemoryAugmentedAgent`).
2. **Competency questions (SPARQL 1.1).** Six questions (tool access, agent
   role, memory–agent relation, delegation, session messages, group
   coordination) are answered by the queries in [`sparql/`](sparql/).
3. **Design quality (OOPS!).** The OntOlogy Pitfall Scanner reports **0
   Critical** pitfalls.

In addition, the **framework-independence** claim is tested empirically: the
live class hierarchies of LangChain 1.3.2 and CrewAI 1.14.6 are extracted via
Python reflection and mapped to 37 ontology terms (see
[`framework-mapping/`](framework-mapping/)). No single framework exposes all
terms as first-class concepts, showing the ontology is not tied to any one
framework's abstraction.

## Getting started

**Open / reason in Protégé**

1. Open `ontology/agentic-ontology.rdf` in [Protégé](https://protege.stanford.edu/).
2. The OASIS 2 import resolves locally through `ontology/catalog-v001.xml`.
3. Start the HermiT reasoner to see inferred class memberships.

**Run a competency-question query**

Load the ontology into any SPARQL 1.1 engine (e.g. Apache Jena `arq`) and run a
query from `sparql/`, for example `q3_memory_by_agent.rq`.

**Reproduce the framework mapping**

```bash
pip install langchain langgraph crewai
python framework-mapping/reflect.py
```

**Build the paper**

```bash
cd paper
pdflatex main.tex && pdflatex main.tex
```

## Citation

If you use this ontology, please cite the archived release:

> Tugal, S. and Ünalır, M. O. (2026). *Ontology of LLM-Based Agentic AI
> (BDM Tabanlı Etmen Sistemleri Ontolojisi).* Zenodo.
> https://doi.org/10.5281/zenodo.20571345

See [`paper/main.pdf`](paper/main.pdf) for the full paper.

## Authors

- **Sami Tugal** — Ege University, Department of Computer Engineering, İzmir, Türkiye. ORCID: [0009-0008-6595-7053](https://orcid.org/0009-0008-6595-7053)
- **Prof. Dr. Murat Osman Ünalır** — Ege University, Department of Computer Engineering, İzmir, Türkiye. ORCID: [0000-0003-4531-0566](https://orcid.org/0000-0003-4531-0566)

## License

This work is licensed under the [Creative Commons Attribution 4.0 International
License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You are free
to share and adapt the material for any purpose, provided you give appropriate
credit. See [`LICENSE`](LICENSE) for the full text.
