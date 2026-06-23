# Filesystem MCP — Tool Risk Ranking (Local LLM + NIST SP 800-30)

**Generated:** 2026-06-09 16:52  
**Scoring source:** qwen2.5:32b via Ollama (http://127.0.0.1:11434)  
**Filetype×tool table:** LLM-provided with NIST baseline  
**Directory×tool table:** NIST(tool_likelihood, dir_sensitivity)  
**Combined matrix:** NIST(tool_likelihood, max(dir_sens, ft_sens))  

---

## NIST SP 800-30 Risk Matrix

| Likelihood \ Impact | Low | Medium | High | Critical |
|--------------------|-----|--------|------|----------|
| **High**           | Low | Medium | High | Critical |
| **Medium**         | Low | Low    | Medium | High   |
| **Low**            | Low | Low    | Low  | Medium   |

---

## Tool Likelihood (fixed)

| Tool | Likelihood | Modal Risk |
|------|-----------|------------|
| `write_file` | High | High |
| `read_file` | Medium | Medium |
| `edit_file` | Medium | Medium |
| `list_dir` | Medium | Medium |
| `move_file` | Medium | Medium |
| `search` | Medium | Medium |
| `create_dir` | Low | Low |
| `get_file_info` | Low | Low |

---

## Filetype × Tool Risk Table (LLM-scored)

| Filetype | read_file | write_file | edit_file | create_dir | list_dir | move_file | search | get_file_info |
|---------|--------|--------|--------|--------|--------|--------|--------|--------|
| `.sys` | High | Critical | Critical | Low | Medium | High | Medium | Low |
| `.exe` | High | Critical | Critical | Low | Medium | High | Medium | Low |
| `.bash` | High | Critical | Critical | Low | Medium | High | Medium | Low |
| `.code` | High | High | High | Low | Medium | High | Medium | Low |
| `.sql` | High | High | High | Low | Medium | High | Medium | Low |
| `.xlsx` | High | High | High | Low | Medium | High | Medium | Low |
| `.docx` | High | High | High | Low | Medium | High | Medium | Low |
| `.pdf` | Medium | Medium | Medium | Low | Medium | Medium | Medium | Low |
| `.csv` | Medium | High | High | Low | Medium | Medium | Medium | Low |
| `.md` | Low | Low | Low | Low | Medium | Low | Medium | Low |
| `.png` | Low | Low | Low | Low | Medium | Low | Medium | Low |
| `.txt` | Low | Low | Low | Low | Medium | Low | Medium | Low |

---

## Sensitivity Maps

| Directory | Sensitivity |
|-----------|------------|
| Sensitive Docs | Critical |
| Security Evidence | Critical |
| Source Code | High |
| Eval Data | Medium |
| Shared Proj Dir | Medium |
| QA Test Plans | Medium |
| Onboarding | Low |
| Public | Low |

| Filetype | Sensitivity |
|----------|------------|
| `.sys` | Critical |
| `.exe` | Critical |
| `.bash` | High |
| `.code` | High |
| `.sql` | High |
| `.xlsx` | High |
| `.docx` | High |
| `.pdf` | Medium |
| `.csv` | Medium |
| `.md` | Low |
| `.png` | Low |
| `.txt` | Low |
