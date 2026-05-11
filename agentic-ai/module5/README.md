# Module 5: Domain-Specific Agent Applications

Module 5 introduces the **Domain Adaptation Engine** — a lightweight framework that takes a general-purpose LangGraph agent and specializes it for any domain by applying four configurable levers: system prompt, knowledge corpus, tool scoping, and guardrails.

## Architecture

```
DomainConfig (declarative)
    │
    ▼
DomainAdapter.adapt(base_model, config)
    ├── PromptBuilder   → composes 4-layer system prompt
    ├── ToolScoper      → selects domain-scoped tools from registry
    ├── GuardrailConfig → creates Bedrock Guardrail (best-effort)
    └── create_react_agent(model, tools, prompt)
    │
    ▼
DomainAgent (specialized, ready to invoke)
```

## Three Domain Configurations

| Domain | Tools | PII Handling |
|--------|-------|-------------|
| `customer` | Algolia, Personalize, Lex, Connect | ANONYMIZE |
| `geospatial` | Location Service (4), Mapbox (4) | BLOCK |
| `voice` | Deepgram, Transcribe, Polly | ANONYMIZE |

## Quick Start

```python
from module5.agent import create_domain_agent

# Create a domain-specialized agent
agent = create_domain_agent("customer")

# Invoke it
result = agent.agent.invoke({
    "messages": [("user", "Find me a monitoring tool for AWS")]
})
print(result["messages"][-1].content)
```

## Mock Mode

All tools support mock mode — no ISV accounts or API keys required:

```bash
AGENT_MOCK_DOMAIN=true python demos/module5_demo.py
```

When `AGENT_MOCK_DOMAIN=true`:
- All tools return realistic static data from `mock/domain_mocks.py`
- Guardrails return mock IDs (`mock-guardrail-{domain_name}`)
- LLM calls via Bedrock are still live (requires AWS credentials)

## Custom Domain

```python
from module5.engine.domain_adapter import DomainConfig, PromptLayers, GuardrailPolicy
from module5.agent import create_domain_agent

my_domain = DomainConfig(
    name="my_domain",
    display_name="My Domain Specialist",
    prompt_layers=PromptLayers(
        role="You are a specialist for...",
        knowledge_context="You have access to...",
        constraints="Never...",
        communication="Concise, professional tone.",
    ),
    tool_names=["algolia_semantic_search"],  # must be in ALL_TOOLS registry
    guardrail_policy=GuardrailPolicy(pii_handling="ANONYMIZE"),
)

agent = create_domain_agent(my_domain)
```

## HTTP Server

```bash
MODULE5_PORT=8085 python module5/app.py
# POST /invoke  {"domain": "customer", "message": "..."}
# GET  /ping
```

## Demo

```bash
AGENT_MOCK_DOMAIN=true python demos/module5_demo.py           # all 11 sections
AGENT_MOCK_DOMAIN=true python demos/module5_demo.py --section 7  # customer showcase
```

## Evaluation

```python
from evaluation.pipelines.module5_eval import run_module5_evaluation

results = run_module5_evaluation(domain="all")
print(f"Quality delta: +{results['summary']['average_quality_delta']:.1f}")
```
