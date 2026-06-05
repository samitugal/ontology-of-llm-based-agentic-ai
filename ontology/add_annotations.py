"""
P08 (OOPS! Minor) kapatma: Her owl:Class, owl:ObjectProperty ve
owl:DatatypeProperty deklarasyonuna eksik rdfs:label (en) ve
rdfs:comment (tr) annotation'lari enjekte eder.

Strateji:
- Dosya satir-satir RDF/XML olarak tarandiginda her deklarasyon
  acilis etiketi -> kapanis etiketi blogu olarak gorulur.
- Blok icinde rdfs:label varsa eklenmez; yoksa enjekte edilir.
- Cikti: agentic-ontology.rdf icinde guncellenir (in-place).

Calistirma:
    cd ontology && python3 add_annotations.py
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- Etiket/Yorum sozluk

CLASS_ANNOTATIONS = {
    # Cekirdek varliklar
    "Agent":              ("Agent",              "Karar veren, yonlendiren ve diger bilesenleri orkestre eden temel varlik. BDM tabanli etmenler bu sinifin alt veya birey ornekleridir."),
    "AgentGroup":         ("Agent Group",        "Ortak bir amac dogrultusunda birlikte calisan etmenlerin mantiksal organizasyonu (orn. arastirma takimi, kod inceleme takimi)."),
    "AgentTemplate":      ("Agent Template",     "Somut bir etmen ornegi olusturmak icin kullanilan soyut yapilandirma sablonu; rol, model ve kabiliyet on-tanimlarini iceren prototip."),
    "Role":               ("Role",               "Bir etmenin sistem icindeki islevsel konumunu ve sorumlulugunu belirleyen tanim (orn. Planner, Reviewer, Worker)."),
    "Policy":             ("Policy",             "Etmenin karar ve davranislarini kisitlayan veya yonlendiren kurallar butunu."),
    "ModelConfiguration": ("Model Configuration","Bir etmen icin kullanilacak LLM modeli ile parametrelerini (temperature, top_p, vb.) bir arada tanimlayan yapilandirma nesnesi."),

    # Etkilesim ve akis
    "Session":            ("Session",            "Bir kullanici ile etmen veya etmenler arasindaki belirli bir etkilesim surecini kapsayan baglam birimi."),
    "Message":            ("Message",            "Kullanicidan ya da etmenden gelen, role ve siraya sahip tekil iletisim birimi."),
    "AgentMessage":       ("Agent Message",      "Bir etmen tarafindan uretilmis Message alt tipi."),
    "UserMessage":        ("User Message",       "Kullanici (veya cagiran sistem) tarafindan uretilmis Message alt tipi."),
    "Observation":        ("Observation",        "Bir oturum sirasinda uretilen token kullanimi, gecikme ve hata gibi sistem duzeyindeki olcum kayitlari."),
    "Context":            ("Context",            "Etmenin karar uretirken degerlendirdigi anlik baglam penceresi."),
    "MessageRole":        ("Message Role",       "Bir mesajin sistemdeki rolunu belirleyen oneOf-tanimli sayilabilir tip (User, Assistant, System, ToolRole)."),

    # Yetenek
    "Tool":               ("Tool",               "Etmen tarafindan cagrilabilen, tanimli bir isi yerine getiren dissal fonksiyon veya sistem bileseni."),
    "ToolCall":           ("Tool Call",          "Etmenin bir araci belirli parametrelerle cagirma eylemi; argumanlari ve zaman damgasini kaydeder."),
    "ToolResult":         ("Tool Result",        "Bir arac cagrisinin urettigi cikti ya da hata durumu."),
    "Resource":           ("Resource",           "Etmenin erisebildigi dosya, veritabani veya harici servis gibi veri kaynaklari."),
    "Action":             ("Action",             "Etmenin bir karar sonucunda gerceklestirdigi somut islem."),
    "Capability":         ("Capability",         "Bir etmenin sahip oldugu yetenek kumesinin soyut tanimi; oasis:Behaviour ile hizalanir."),

    # Hafiza
    "Memory":             ("Memory",             "Etmenin gecmis etkilesimlere ve bilgiye erisimini saglayan genel hafiza altyapisi (tum hafiza turlerinin ust sinifi)."),
    "ShortTermMemory":    ("Short Term Memory",  "Aktif oturum suresince gecerli olan kisa vadeli baglam hafizasi."),
    "LongTermMemory":     ("Long Term Memory",   "Oturumlar arasinda kalici olarak saklanan uzun vadeli bilgi deposu."),
    "EpisodicMemory":     ("Episodic Memory",    "Gecmis etkilesimlere ait olaysal (zaman/yer baglamli) kayitlari saklayan hafiza turu."),
    "SemanticMemory":     ("Semantic Memory",    "Alan bilgisi ve olgusal bilgiyi (genellikle vektor temsiliyle) temsil eden yapilandirilmis bilgi tabani."),
    "MemoryStrategy":     ("Memory Strategy",    "Hangi bilginin ne zaman saklanacagini, gomulecegini veya geri cagrilacagini belirleyen soyut strateji."),
    "CompressionStrategy":("Compression Strategy","Baglam penceresinin token butcesine sigmasini saglayan ozetleme/sikistirma stratejisi (MemoryStrategy alt tipi)."),
    "EvictionStrategy":   ("Eviction Strategy",  "Hafizadan oge cikarma (LRU, FIFO vb.) stratejisi (MemoryStrategy alt tipi)."),
    "RetrievalStrategy":  ("Retrieval Strategy", "Hafizadan ilgili icerigi geri cagirma (vector-similarity, keyword vb.) stratejisi (MemoryStrategy alt tipi)."),
    "MemoryContent":      ("Memory Content",     "Hafizada saklanabilir icerigin birlesik ust tipi (Message ile Session'in unionu); hafiza katmaninin ortak range'i olarak kullanilir."),

    # Model ve yapilandirma
    "LLMModel":           ("LLM Model",          "Etmenin cikti uretmek icin kullandigi buyuk dil modeli (orn. GPT-4o, Claude Sonnet)."),
    "Prompt":             ("Prompt",             "Modele gonderilen ve davranisi yonlendiren girdi metni (System ve User alt tipleri vardir)."),
    "SystemPrompt":       ("System Prompt",      "Etmenin genel davranisini, rolunu ve kisitlamalarini tanimlayan sabit yonerge."),
    "UserPrompt":         ("User Prompt",        "Kullanici ya da cagiran sistem tarafindan saglanan, etmene yonlendirilen anlik talep veya soru."),
    "Parameter":          ("Parameter",          "Modelin sicaklik ve maksimum token gibi calisma zamani ayarlarini tanimlayan deger."),

    # Orkestrasyon
    "Task":               ("Task",               "Etmenin tamamlamasi beklenen, tanimli giris ve cikisa sahip is birimi."),
    "Subtask":            ("Subtask",            "Bir Task'in daha kucuk ve bagimsiz olarak yurutulebilir alt parcasi."),
    "Plan":               ("Plan",               "Bir gorevi tamamlamak icin belirlenen sirali adimlar dizisi."),
    "Workflow":           ("Workflow",           "Birden fazla etmen veya aracin koordineli bicimde yuruttugu surec akisi."),
    "Delegation":         ("Delegation",         "Bir etmenin gorevi baska bir etmene devretme iliskisi."),
    "ExecutionContext":   ("Execution Context",  "Bir gorevin calistirildigi ortam bilgisini ve durumunu kapsayan baglam nesnesi."),
    "ExecutableEntity":   ("Executable Entity",  "Yurutulebilir varliklarin birlesik ust tipi (Task ile Workflow'un unionu)."),
    "ExecutionMode":      ("Execution Mode",     "Bir Task'in calismasini niteleyen oneOf-tanimli sayilabilir tip (Sync, Async)."),
    "Channel":            ("Channel",            "Etmenler veya etmen ile kullanici arasindaki iletisim kanalinin soyut tanimi."),
    "Protocol":           ("Protocol",           "Etmenler arasi mesaj alisverisini duzenleyen iletisim kurallari butunu (orn. MCP, FIPA-ACL, JSON-RPC)."),

    # Reasoner-tanimli (Faz 4)
    "AutonomousAgent":      ("Autonomous Agent",      "Hem hafizaya hem de arac cagirma yetenegine sahip etmenleri kapsayan equivalentClass tanimli sinif."),
    "MemoryAugmentedAgent": ("Memory Augmented Agent","Uzun vadeli hafizaya sahip etmenleri kapsayan equivalentClass tanimli sinif."),
    "PlanningAgent":        ("Planning Agent",        "Plan ureten ancak dogrudan arac cagrisi yapmayan etmenleri kapsayan equivalentClass tanimli sinif."),
}

# Genel-amacli aciklama sablonlari property'ler icin
OBJECT_PROPERTY_ANNOTATIONS = {
    "accessesResource":  ("accesses resource",   "Bir Tool'un erisim sagladigi Resource'u belirten iliski."),
    "capabilityOf":      ("capability of",       "hasCapability'nin tersi: bir Capability'nin sahibi olan Agent'i isaret eden iliski."),
    "coordinatesVia":    ("coordinates via",     "Bir AgentGroup'un uzerinden koordine oldugu Workflow'u belirten iliski."),
    "createsPlan":       ("creates plan",        "Bir Agent'in urettigi Plan'i baglayan iliski; PlanningAgent tanimi icin kullanilir."),
    "delegatedBy":       ("delegated by",        "Bir Delegation kaydinin hangi Agent tarafindan baslatildigini belirten iliski."),
    "delegatedTask":     ("delegated task",      "Bir Delegation icinde devredilen Task'i isaret eden iliski (functional)."),
    "delegatesTo":       ("delegates to",        "Bir Agent'in gorev devrettigi diger Agent'i isaret eden iliski (asymmetric + irreflexive)."),
    "delegator":         ("delegator",           "Bir Delegation icindeki devreden Agent'i isaret eden iliski (functional)."),
    "followsProtocol":   ("follows protocol",    "Bir Channel'in uyguladigi Protocol'u belirten iliski."),
    "forRole":           ("for role",            "Bir AgentTemplate'in hangi Role icin tasarlandigini belirten iliski."),
    "generatedBy":       ("generated by",        "Bir Message'in uretildigi Session'i isaret eden iliski (functional)."),
    "hasAction":         ("has action",          "Bir Workflow veya Plan'in icerdigi Action'i baglayan iliski."),
    "hasCapability":     ("has capability",      "Bir Agent'in sahip oldugu Capability'i baglayan iliski (someValuesFrom kisitiyla zorunlu)."),
    "hasConfiguration":  ("has configuration",   "Bir Agent'in calistigi ModelConfiguration'i belirten iliski (functional + tam-1 kardinalite)."),
    "hasContext":        ("has context",         "Bir Agent veya Session'in aktif Context'ini baglayan iliski."),
    "hasMember":         ("has member",          "Bir AgentGroup'un icerdigi Agent'lari baglayan iliski."),
    "hasMemory":         ("has memory",          "Bir Agent'in sahip oldugu Memory'yi baglayan iliski; AutonomousAgent ve MemoryAugmentedAgent tanimlari icin kullanilir."),
    "hasMemoryStrategy": ("has memory strategy", "Bir Memory'nin uyguladigi MemoryStrategy'i belirten iliski."),
    "hasMessage":        ("has message",         "Bir Session'in icerdigi Message'lari baglayan iliski."),
    "hasMessageRole":    ("has message role",    "Bir Message'in MessageRole'unu belirten iliski (functional)."),
    "hasObservation":    ("has observation",     "Bir Session'in urettigi Observation kayitlarini baglayan iliski."),
    "hasParameter":      ("has parameter",       "Bir ModelConfiguration'in icerdigi Parameter'leri baglayan iliski."),
    "hasPlan":           ("has plan",            "Bir Task veya Workflow'un izledigi Plan'i belirten iliski."),
    "hasPolicy":         ("has policy",          "Bir Agent'in uyguladigi Policy'leri baglayan iliski."),
    "hasPrompt":         ("has prompt",          "Bir Agent veya AgentTemplate'in kullandigi Prompt'u baglayan iliski."),
    "hasRole":           ("has role",            "Bir Agent'in ustlendigi Role'u baglayan iliski."),
    "hasSession":        ("has session",         "Bir Agent'in dahil oldugu Session'lari baglayan iliski."),
    "hasSharedMemory":   ("has shared memory",   "Bir AgentGroup'un paylasilan Memory'sini belirten iliski."),
    "hasStep":           ("has step",            "Bir Plan'in icerdigi Task adimlarini baglayan iliski (allValuesFrom Task)."),
    "instantiates":      ("instantiates",        "Bir Agent'in hangi AgentTemplate'ten somutlastirildigini belirten iliski."),
    "invokedBy":         ("invoked by",          "invokesTool'un tersi: bir Tool'un hangi ToolCall tarafindan cagrildigini belirten iliski."),
    "invokesTool":       ("invokes tool",        "Bir ToolCall'in cagirdigi Tool'u belirten iliski."),
    "madeBy":            ("made by",             "Bir ToolCall'in hangi Agent tarafindan yapildigini belirten iliski."),
    "makesToolCall":     ("makes tool call",     "Bir Agent'in urettigi ToolCall'lari baglayan iliski; AutonomousAgent tanimi icin kullanilir."),
    "memberOf":          ("member of",           "hasMember'in tersi: bir Agent'in dahil oldugu AgentGroup'u belirten iliski."),
    "observedIn":        ("observed in",         "hasObservation'in tersi: bir Observation'in ait oldugu Session'i belirten iliski."),
    "partOfSession":     ("part of session",     "hasMessage'in tersi: bir Message'in ait oldugu Session'i belirten iliski."),
    "playedBy":          ("played by",           "hasRole'un tersi: bir Role'un hangi Agent tarafindan ustlenildigini belirten iliski."),
    "producesResult":    ("produces result",     "Bir ToolCall'in urettigi ToolResult'u belirten iliski."),
    "promptOf":          ("prompt of",           "hasPrompt'un tersi: bir Prompt'un hangi Agent veya AgentTemplate'e ait oldugunu belirten iliski."),
    "recordsSession":    ("records session",     "Bir Memory'nin kayit altinda tuttugu Session'i belirten iliski; hafiza katmaninda Session'i MemoryContent olarak baglar."),
    "resultOf":          ("result of",           "producesResult'un tersi: bir ToolResult'un hangi ToolCall'a ait oldugunu belirten iliski."),
    "runsIn":            ("runs in",             "Bir Task veya Workflow'un calistirildigi ExecutionContext'i belirten iliski."),
    "sessionOf":         ("session of",          "hasSession'in tersi: bir Session'in hangi Agent'a ait oldugunu belirten iliski."),
    "storesMessage":     ("stores message",      "Bir Memory'nin sakladigi Message'lari belirten iliski; hafiza katmaninda Message'i MemoryContent olarak baglar."),
    "subtaskOf":         ("subtask of",          "Bir Subtask'in hangi Task'a ait oldugunu belirten iliski (transitif olabilen alt-gorev iliskisi)."),
    "toolFor":           ("tool for",            "Bir Tool'un hangi Capability'i destekledigini belirten iliski."),
    "triggeredBy":       ("triggered by",        "Bir Action veya Workflow'un hangi Event/Agent tarafindan tetiklendigini belirten iliski."),
    "usesModel":         ("uses model",          "Bir ModelConfiguration'in basvurdugu LLMModel'i belirten iliski."),
    "usesTool":          ("uses tool",           "Bir Agent veya Capability'nin kullandigi Tool'u belirten iliski."),
    "viaChannel":        ("via channel",         "Bir Delegation veya Message'in iletildigi Channel'i belirten iliski."),
}

# Data property'ler icin etiket/aciklama. Buyuk bolumu otomatik turetilebilir
# olsa da once ozel olanlari elle yaziyoruz.
DATA_PROPERTY_ANNOTATIONS = {
    "accessMode":        ("access mode",         "Resource'un erisim modu (read, write, read-write)."),
    "actionName":        ("action name",         "Action ornegi icin insan-okur ad."),
    "agentId":           ("agent id",            "Agent ornegi icin essiz tanimlayici."),
    "agentName":         ("agent name",          "Agent ornegi icin insan-okur ad."),
    "agentVersion":      ("agent version",       "Agent yapilandirmasinin surum etiketi."),
    "callId":            ("call id",             "ToolCall ornegi icin essiz tanimlayici."),
    "callTimestamp":     ("call timestamp",      "ToolCall'in baslatildigi zaman damgasi (xsd:dateTime)."),
    "capabilityName":    ("capability name",     "Capability ornegi icin insan-okur ad."),
    "channelEndpoint":   ("channel endpoint",    "Channel'in baglandigi uc nokta (URI veya adres)."),
    "channelType":       ("channel type",        "Channel turu (http, websocket, in-process vb.)."),
    "contextId":         ("context id",          "Context ornegi icin essiz tanimlayici."),
    "contextLength":     ("context length",      "Aktif baglamdaki token sayisi."),
    "contextSnapshot":   ("context snapshot",    "Belirli bir andaki Context'in serilestirilmis temsili."),
    "contextWindowSize": ("context window size", "LLMModel'in destekledigi maksimum baglam pencere boyutu (token cinsinden)."),
    "cost":              ("cost",                "Bir cagri veya gorevin tahmini para birimi cinsinden maliyeti."),
    "createdAt":         ("created at",          "Olusturma zaman damgasi (xsd:dateTime)."),
    "delegatedAt":       ("delegated at",        "Delegation'in gerceklestigi zaman damgasi (xsd:dateTime)."),
    "delegationReason":  ("delegation reason",   "Devir kararinin gerekcesi (serbest metin)."),
    "dueDate":           ("due date",            "Task icin son teslim tarihi (xsd:dateTime)."),
    "embeddingModel":    ("embedding model",     "SemanticMemory'de kullanilan vektor gomme modelinin adi."),
    "endTime":           ("end time",            "Session veya Task icin bitis zaman damgasi (xsd:dateTime)."),
    "environmentVars":   ("environment vars",    "ExecutionContext'e tasinan ortam degiskenleri (JSON veya anahtar-deger)."),
    "errorCount":        ("error count",         "Session icinde gozlemlenen hata sayisi."),
    "errorMessage":      ("error message",       "ToolResult veya Observation icin hata aciklamasi."),
    "executionTimeMs":   ("execution time ms",   "Bir cagri veya gorevin milisaniye cinsinden suresi."),
    "groupName":         ("group name",          "AgentGroup ornegi icin insan-okur ad."),
    "hasDescription":    ("has description",     "Genel amacli serbest metin aciklama; alan-bagimsiz tutulmustur."),
    "inputJson":         ("input json",          "ToolCall'in JSON formatinda serilestirilmis girdi argumanlari."),
    "isActive":          ("is active",           "Bir Agent, Session veya Capability'nin aktif olup olmadigini gosteren bool deger."),
    "isAsync":           ("is async",            "Bir Task'in asenkron calisip calismadigini gosteren bool deger (ExecutionMode ile esgudum)."),
    "latencyMs":         ("latency ms",          "Bir cagri icin milisaniye cinsinden gecikme."),
    "maxEpisodes":       ("max episodes",        "EpisodicMemory'nin saklayabilecegi maksimum epizot sayisi."),
    "memoryCapacity":    ("memory capacity",     "Bir Memory ornegi icin token veya kayit kapasitesi."),
    "messageContent":    ("message content",     "Message govdesinin serbest metin icerigi."),
    "messageId":         ("message id",          "Message ornegi icin essiz tanimlayici."),
    "messageTimestamp":  ("message timestamp",   "Message'in olusturuldugu zaman damgasi (xsd:dateTime)."),
    "modelName":         ("model name",          "LLMModel'in adi (orn. gpt-4o, claude-sonnet-4-5)."),
    "modelProvider":     ("model provider",      "LLMModel'in saglayicisi (orn. OpenAI, Anthropic)."),
    "modelVersion":      ("model version",       "LLMModel'in surum etiketi."),
    "observedAt":        ("observed at",         "Observation'in kaydedildigi zaman damgasi (xsd:dateTime)."),
    "paramName":         ("param name",          "Parameter'in adi (orn. temperature)."),
    "paramType":         ("param type",          "Parameter'in tipi (orn. xsd:double)."),
    "paramValue":        ("param value",         "Parameter'in degeri (string olarak serilestirilmis)."),
    "persistenceBackend":("persistence backend", "LongTermMemory icin kullanilan kalici depolama arka ucu (orn. SQLite, Postgres, Redis)."),
    "planName":          ("plan name",           "Plan ornegi icin insan-okur ad."),
    "planVersion":       ("plan version",       "Plan'in surum etiketi."),
    "policyExpression":  ("policy expression",   "Policy'nin makine-okur ifadesi (orn. JSON kurali, DSL)."),
    "policyName":        ("policy name",         "Policy ornegi icin insan-okur ad."),
    "policyPriority":    ("policy priority",     "Policy'nin uygulanma onceligi (integer)."),
    "promptText":        ("prompt text",         "Prompt'un serbest metin govdesi."),
    "protocolName":      ("protocol name",       "Protocol ornegi icin insan-okur ad (orn. MCP)."),
    "protocolVersion":   ("protocol version",    "Protocol'un surum etiketi."),
    "resourceType":      ("resource type",       "Resource'un turu (orn. file, database, api)."),
    "resourceURI":       ("resource URI",        "Resource'a karsilik gelen kaynak URI'si."),
    "resultPayload":     ("result payload",      "ToolResult'in icerdigi serbest icerik (JSON veya metin)."),
    "resultStatus":      ("result status",       "ToolResult durumu (success, failure, partial)."),
    "roleName":          ("role name",           "Role ornegi icin insan-okur ad."),
    "sessionId":         ("session id",          "Session ornegi icin essiz tanimlayici."),
    "sessionStatus":     ("session status",      "Session durumu (active, paused, ended)."),
    "startTime":         ("start time",          "Session veya Task icin baslangic zaman damgasi (xsd:dateTime)."),
    "stepOrder":         ("step order",          "Bir Plan icindeki Task adiminin sira numarasi (integer)."),
    "strategyAlgorithm": ("strategy algorithm",  "MemoryStrategy icin kullanilan algoritmanin adi (orn. LRU, FIFO, top-k)."),
    "strategyName":      ("strategy name",       "MemoryStrategy ornegi icin insan-okur ad."),
    "supportsFunctionCalling": ("supports function calling", "LLMModel'in fonksiyon cagrisi/tool-use ozelligini destekleyip desteklemedigini gosteren bool deger."),
    "taskName":          ("task name",           "Task ornegi icin insan-okur ad."),
    "taskPriority":      ("task priority",       "Task'in onceligi (integer)."),
    "taskStatus":        ("task status",         "Task durumu (pending, running, completed, failed)."),
    "templateName":      ("template name",       "AgentTemplate veya PromptTemplate ornegi icin insan-okur ad."),
    "templateVariables": ("template variables",  "PromptTemplate'in bekledigi degiskenlerin listesi (JSON veya virgulle ayrilmis)."),
    "templateVersion":   ("template version",    "AgentTemplate veya PromptTemplate'in surum etiketi."),
    "tokenCount":        ("token count",         "Bir Message veya Context icin token sayisi."),
    "toolEndpoint":      ("tool endpoint",       "Tool'un cagrilabilecegi endpoint (URI)."),
    "toolName":          ("tool name",           "Tool ornegi icin insan-okur ad."),
    "toolVersion":       ("tool version",        "Tool'un surum etiketi."),
    "ttlSeconds":        ("ttl seconds",         "Memory icin saniye cinsinden yasam suresi (time-to-live)."),
    "updatedAt":         ("updated at",          "Son guncelleme zaman damgasi (xsd:dateTime)."),
    "vectorDimension":   ("vector dimension",    "SemanticMemory icin gomme vektor boyutu (orn. 1536)."),
    "workflowName":      ("workflow name",       "Workflow ornegi icin insan-okur ad."),
    "workflowStatus":    ("workflow status",     "Workflow durumu (running, completed, failed)."),
}


# ---------------------------------------------------------------- Enjeksiyon mantigi

INDENT = "        "

DECL_RE = re.compile(
    r'(<owl:(Class|ObjectProperty|DatatypeProperty)\s+rdf:about="[^"]*#([^"]+)">)'
    r'(.*?)'
    r'(</owl:\2>)',
    re.DOTALL,
)

# Kendinden-kapali (self-closing) deklarasyonlar; <owl:Class .../> formu
SELF_CLOSING_RE = re.compile(
    r'<owl:(Class|ObjectProperty|DatatypeProperty)\s+rdf:about="([^"]*#([^"]+))"/>'
)


def expand_self_closing(text: str) -> str:
    """Self-closing tag'leri <X></X> formuna acar ki ana regex yakalayabilsin."""
    def _expand(m: re.Match) -> str:
        kind, uri, _frag = m.groups()
        return f'<owl:{kind} rdf:about="{uri}">\n    </owl:{kind}>'
    return SELF_CLOSING_RE.sub(_expand, text)


def annotation_block(label_en: str, comment_tr: str) -> str:
    return (
        f'\n{INDENT}<rdfs:label xml:lang="en">{label_en}</rdfs:label>'
        f'\n{INDENT}<rdfs:comment xml:lang="tr">{comment_tr}</rdfs:comment>'
    )


def inject(match: re.Match) -> str:
    open_tag, kind, fragment, body, close_tag = match.groups()
    if "<rdfs:label" in body and "<rdfs:comment" in body:
        return match.group(0)

    if kind == "Class":
        ann = CLASS_ANNOTATIONS.get(fragment)
    elif kind == "ObjectProperty":
        ann = OBJECT_PROPERTY_ANNOTATIONS.get(fragment)
    else:
        ann = DATA_PROPERTY_ANNOTATIONS.get(fragment)

    if ann is None:
        return match.group(0)

    label_en, comment_tr = ann
    inserted = annotation_block(label_en, comment_tr)
    return f"{open_tag}{inserted}{body}{close_tag}"


def main() -> int:
    path = Path(__file__).parent / "agentic-ontology.rdf"
    text = path.read_text(encoding="utf-8")
    text = expand_self_closing(text)
    new_text, n = DECL_RE.subn(inject, text)

    label_count = new_text.count("<rdfs:label")
    comment_count = new_text.count("<rdfs:comment")
    print(f"Iz dusumu: {n} deklarasyon islendi.")
    print(f"Toplam rdfs:label   : {label_count}")
    print(f"Toplam rdfs:comment : {comment_count}")

    expected = (
        len(CLASS_ANNOTATIONS)
        + len(OBJECT_PROPERTY_ANNOTATIONS)
        + len(DATA_PROPERTY_ANNOTATIONS)
    )
    print(f"Beklenen yeni annotation seti: {expected} entity")

    missing_classes = sorted(
        set(re.findall(r'owl:Class rdf:about="[^"]*#([^"]+)"', text))
        - set(CLASS_ANNOTATIONS)
    )
    missing_op = sorted(
        set(re.findall(r'owl:ObjectProperty rdf:about="[^"]*#([^"]+)"', text))
        - set(OBJECT_PROPERTY_ANNOTATIONS)
    )
    missing_dp = sorted(
        set(re.findall(r'owl:DatatypeProperty rdf:about="[^"]*#([^"]+)"', text))
        - set(DATA_PROPERTY_ANNOTATIONS)
    )
    if missing_classes:
        print("UYARI: aciklamasi yok (class):", missing_classes)
    if missing_op:
        print("UYARI: aciklamasi yok (obj prop):", missing_op)
    if missing_dp:
        print("UYARI: aciklamasi yok (data prop):", missing_dp)

    path.write_text(new_text, encoding="utf-8")
    print(f"Yazildi: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
