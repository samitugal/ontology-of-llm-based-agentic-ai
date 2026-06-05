"""
Canlı reflection ile LangChain ve CrewAI sınıf hiyerarşilerini çıkarıp
BDM-etmen ontolojisinin 37 terimine eşler.

Her ontoloji terimi için bir dizi aday import yolu denenir; ilk başarılı
import'un gerçek __module__, __qualname__ ve MRO (method resolution order)
bilgisi kaydedilir. Böylece eşleme uydurma değil, kurulu paketlerden
introspection ile elde edilmiş kanıta dayanır.

Çıktı:
  reflection.json  — yapısal ham veri
  reflection.txt   — insan-okur özet
"""

import importlib
import inspect
import json
import sys
from datetime import datetime, timezone


def resolve(path: str):
    """'modul.alt:Sinif' veya 'modul.alt.Sinif' yolundan sınıfı import et."""
    if ":" in path:
        mod_name, _, attr = path.partition(":")
    else:
        mod_name, _, attr = path.rpartition(".")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"
    obj = getattr(mod, attr, None)
    if obj is None:
        return None, f"AttributeError: {mod_name} icinde {attr} yok"
    return obj, None


def mro_names(obj):
    """Bir sınıfın (veya örnek/enum'un sınıfının) MRO'sundaki isimleri döndür."""
    cls = obj if inspect.isclass(obj) else type(obj)
    return [f"{c.__module__}.{c.__qualname__}" for c in cls.__mro__ if c is not object]


def probe(framework: str, mapping: list[tuple[str, list[str]]]):
    rows = []
    for term, candidates in mapping:
        found = None
        errors = []
        for cand in candidates:
            obj, err = resolve(cand)
            if obj is not None:
                found = (cand, obj)
                break
            errors.append(f"{cand} -> {err}")
        if found is None:
            rows.append({
                "ontology_term": term,
                "resolved": None,
                "tried": candidates,
                "errors": errors,
            })
            continue
        cand, obj = found
        cls = obj if inspect.isclass(obj) else type(obj)
        rows.append({
            "ontology_term": term,
            "resolved": cand,
            "module": cls.__module__,
            "qualname": cls.__qualname__,
            "kind": "class" if inspect.isclass(obj) else type(obj).__name__,
            "mro": mro_names(obj),
        })
    return {"framework": framework, "entries": rows}


# (ontoloji_terimi, [aday import yollari]) — ilk import edilen kazanir.
LANGCHAIN = [
    ("Agent", ["langchain.agents:AgentExecutor",
               "langgraph.prebuilt:create_react_agent",
               "langchain.agents:BaseSingleActionAgent"]),
    ("AgentGroup", ["langgraph.graph:StateGraph",
                    "langchain.agents:AgentExecutor"]),
    ("Role", ["langchain_core.messages:SystemMessage"]),
    ("LLMModel", ["langchain_core.language_models.chat_models:BaseChatModel",
                  "langchain_core.language_models:BaseLanguageModel"]),
    ("ModelConfiguration", ["langchain_core.runnables:RunnableConfig",
                            "langchain_core.runnables.config:RunnableConfig"]),
    ("Session", ["langgraph.checkpoint.base:Checkpoint",
                 "langchain_core.chat_history:BaseChatMessageHistory"]),
    ("Message", ["langchain_core.messages:BaseMessage"]),
    ("MessageRole", ["langchain_core.messages:AIMessage",
                     "langchain_core.messages:HumanMessage"]),
    ("Context", ["langchain_core.runnables:RunnableConfig"]),
    ("Tool", ["langchain_core.tools:BaseTool",
              "langchain_core.tools:StructuredTool"]),
    ("ToolCall", ["langchain_core.messages.tool:ToolCall",
                  "langchain_core.messages:ToolCall"]),
    ("ToolResult", ["langchain_core.messages:ToolMessage",
                    "langchain_core.messages.tool:ToolMessage"]),
    ("Resource", ["langchain_core.documents:Document"]),
    ("Action", ["langchain_core.agents:AgentAction"]),
    ("Capability", ["langchain_core.runnables:Runnable"]),
    ("Memory", ["langchain_core.memory:BaseMemory",
                "langgraph.store.base:BaseStore"]),
    ("ShortTermMemory", ["langgraph.checkpoint.memory:InMemorySaver",
                         "langgraph.checkpoint.memory:MemorySaver"]),
    ("LongTermMemory", ["langgraph.store.base:BaseStore",
                        "langgraph.store.memory:InMemoryStore"]),
    ("SemanticMemory", ["langchain_core.vectorstores:VectorStore"]),
    ("Prompt", ["langchain_core.prompts:BasePromptTemplate"]),
    ("SystemPrompt", ["langchain_core.prompts:SystemMessagePromptTemplate"]),
    ("PromptTemplate", ["langchain_core.prompts:ChatPromptTemplate",
                        "langchain_core.prompts:PromptTemplate"]),
    ("Parameter", ["langchain_core.runnables:RunnableConfig"]),
    ("Task", ["langchain_core.runnables:Runnable"]),
    ("Plan", ["langchain_core.agents:AgentAction"]),
    ("Workflow", ["langgraph.graph:StateGraph",
                  "langchain_core.runnables:RunnableSequence"]),
    ("Delegation", ["langgraph.types:Command",
                    "langgraph.types:Send"]),
    ("Channel", ["langgraph.channels.base:BaseChannel"]),
    ("ExecutionContext", ["langchain_core.runnables:RunnableConfig"]),
]

CREWAI = [
    ("Agent", ["crewai:Agent", "crewai.agent:Agent"]),
    ("AgentGroup", ["crewai:Crew", "crewai.crew:Crew"]),
    ("AgentTemplate", ["crewai:Agent"]),
    ("Role", ["crewai:Agent"]),  # role bir alan; Agent.role
    ("LLMModel", ["crewai:LLM", "crewai.llm:LLM"]),
    ("ModelConfiguration", ["crewai:LLM"]),
    ("Session", ["crewai.memory.contextual.contextual_memory:ContextualMemory"]),
    ("Message", ["crewai.tasks.task_output:TaskOutput"]),
    ("Tool", ["crewai.tools:BaseTool", "crewai_tools:BaseTool",
              "crewai.tools.base_tool:BaseTool"]),
    ("ToolResult", ["crewai.tools.tool_usage:ToolUsage",
                    "crewai.tasks.task_output:TaskOutput"]),
    ("Resource", ["crewai.knowledge.knowledge:Knowledge",
                  "crewai.knowledge.source.base_knowledge_source:BaseKnowledgeSource"]),
    ("Memory", ["crewai.memory.memory:Memory"]),
    ("ShortTermMemory", ["crewai.memory.short_term.short_term_memory:ShortTermMemory",
                         "crewai.memory:ShortTermMemory"]),
    ("LongTermMemory", ["crewai.memory.long_term.long_term_memory:LongTermMemory",
                        "crewai.memory:LongTermMemory"]),
    ("EpisodicMemory", ["crewai.memory.external.external_memory:ExternalMemory"]),
    ("SemanticMemory", ["crewai.memory.entity.entity_memory:EntityMemory",
                        "crewai.memory:EntityMemory"]),
    ("Prompt", ["crewai.utilities.prompts:Prompts"]),
    ("Task", ["crewai:Task", "crewai.task:Task"]),
    ("Plan", ["crewai.utilities.planning_handler:CrewPlanner"]),
    ("Workflow", ["crewai:Process", "crewai.process:Process"]),
    ("Flow", ["crewai.flow.flow:Flow", "crewai.flow:Flow"]),
    ("Delegation", ["crewai.tools.agent_tools.agent_tools:AgentTools",
                    "crewai.tools.agent_tools:AgentTools"]),
    ("ExecutionContext", ["crewai.crews.crew_output:CrewOutput"]),
]


def main():
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "frameworks": {},
    }
    versions = {}
    for pkg in ("langchain", "langchain_core", "langgraph", "crewai"):
        try:
            m = importlib.import_module(pkg)
            versions[pkg] = getattr(m, "__version__", "?")
        except Exception as e:  # noqa: BLE001
            versions[pkg] = f"<not importable: {type(e).__name__}>"
    results["package_versions"] = versions

    results["frameworks"]["LangChain"] = probe("LangChain", LANGCHAIN)
    results["frameworks"]["CrewAI"] = probe("CrewAI", CREWAI)

    with open("reflection.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    lines = []
    lines.append(f"Python {results['python']}  |  {results['generated_at']}")
    lines.append("Paket surumleri: " + ", ".join(
        f"{k}={v}" for k, v in versions.items()))
    for fw, data in results["frameworks"].items():
        lines.append("")
        lines.append("=" * 72)
        lines.append(f"{fw}")
        lines.append("=" * 72)
        ok = sum(1 for e in data["entries"] if e["resolved"])
        total = len(data["entries"])
        lines.append(f"Cozumlenen: {ok}/{total}")
        for e in data["entries"]:
            if e["resolved"]:
                lines.append(f"\n[{e['ontology_term']}]  <- {e['resolved']}")
                lines.append(f"    sinif : {e['module']}.{e['qualname']}  ({e['kind']})")
                lines.append("    MRO   : " + " <- ".join(
                    n.split(".")[-1] for n in e["mro"]))
            else:
                lines.append(f"\n[{e['ontology_term']}]  <- COZUMLENEMEDI")
                for err in e["errors"]:
                    lines.append(f"    x {err}")
    text = "\n".join(lines)
    with open("reflection.txt", "w") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
