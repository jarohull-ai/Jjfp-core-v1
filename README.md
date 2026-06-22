---
license: cc-by-nc-4.0
language:
- en
- pl
base_model: Qwen/Qwen2.5-7B-Instruct
pipeline_tag: text-generation
library_name: transformers
tags:
- jfp
- deterministic
- multi-agent
- governance
- auditable-ai
- protocol
- viki
- tool-use
- qwen2
---

# JFP-Core-v1 — Jaro Flash Protocol Aligned Model

## What is this?

JFP-Core-v1 is the first model configuration aligned with the **Jaro Flash Protocol (JFP) v16E.0.0** — a deterministic multi-agent AI execution framework developed by Jarosław Kuchta.

This is not a standard language model. It is a **protocol-governed AI engine** designed for auditable, traceable, and reproducible AI applications.

## Key Properties

- **Deterministic execution** — consistent outputs for structured inputs
- **JFP constitutional layer** — built-in rules that cannot be overridden by user prompts
- **Reduced hallucination** — refusal protocol replaces confabulation
- **Audit trail ready** — every output is traceable and explainable
- **Anti-drift design** — behavior stays within defined protocol boundaries
- **VOQL compatible** — native support for VIKI Operational Query Language

## Intended Use

- Auditable enterprise AI pipelines
- Multi-agent orchestration systems
- Compliance-sensitive applications (legal, medical, financial)
- JFP-standard compatible tooling

## Not Intended For

- General-purpose chat
- Creative/open-ended generation without protocol constraints
- Applications requiring unpredictable or exploratory outputs

## Base Model

Built as a fine-tune configuration for **Qwen/Qwen2.5-7B-Instruct**.

## Tools

This model includes a native tool specification. See `tools.json` in this repository.

Supported tools:
- `code_execution` — sandboxed Python/bash execution
- `file_operations` — read/write within JFP boundaries
- `voql_query` — VIKI Operational Query Language queries
- `agent_dispatch` — sub-agent communication within VIKI ecosystem
- `audit_log` — immutable action logging
- `api_call` — external REST API calls (whitelist only)
- `jfp_validate` — schema validation against JFP standard

## Limitations

- Requires JFP-compliant input format for optimal performance
- Not designed for open-ended creative tasks
- Commercial use requires separate licensing agreement

## Protocol

Built on **JFP v16E.0.0** — part of the VIKI ecosystem.
Author: Jarosław Kuchta | [GitHub](https://github.com/etechvictoria-ui)

## License

cc-by-nc-4.0 — Free for non-commercial use.
Commercial licensing: contact the author.

## Citation

```bibtex
@misc{kuchta2026jfp,
  author = {Jarosław Kuchta},
  title = {Jaro Flash Protocol (JFP) v16E.0.0},
  year = {2026},
  publisher = {Hugging Face},
  url = {https://huggingface.co/jarohullowicki/Jjfp-core-v1}
}
```