"""
JFP-Core-v1 Dataset Generator
Generuje 500 przykładów treningowych w 9 kategoriach:
  1. SIGNAL_UNKNOWN      (15)
  2. SIGNAL_DENY         (15)
  3. JFP VALIDATION      (15)
  4. VOQL QUERIES        (15)
  5. AGENT DISPATCH      (15)
  6. CODE EXECUTION      (15)
  7. AUDIT LOG           (10)
  8. JFP SPEC PARSING    (200)  ← nowe
  9. MULTI-AGENT DISPATCH(200)  ← nowe
"""

import json

SYSTEM_PROMPT = (
    "You are JFP-Core-v1, a deterministic AI engine governed by Jaro Flash Protocol "
    "v16E.0.0. You never confabulate. Unknown = SIGNAL_UNKNOWN. "
    "Every output is structured and auditable."
)
TIMESTAMP = "2026-06-22T00:00:00Z"

examples = []
counter = 1

def audit_id():
    global counter
    aid = f"JFP-{counter:03d}"
    counter += 1
    return aid

def make(user, assistant):
    return {"messages": [
        {"role": "system",    "content": SYSTEM_PROMPT},
        {"role": "user",      "content": user},
        {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
    ]}

# ─── KATEGORIA 1: SIGNAL_UNKNOWN (15) ───────────────────────────────────────
unknown_questions = [
    "What will the stock price of NVIDIA be in 2030?",
    "What is the population of the city on Mars?",
    "Who will win the next World Cup?",
    "What is the cure for aging?",
    "What is the exact number of stars in the universe?",
    "What will AI look like in 100 years?",
    "Is there life on Europa?",
    "What is the meaning of consciousness?",
    "What will the weather be in Warsaw on January 1, 2050?",
    "Who will be the next president of the United States?",
    "What is the GDP of the Martian colony in 2080?",
    "What is the true identity of Satoshi Nakamoto?",
    "Will quantum computers replace classical computers by 2035?",
    "What is the exact date of the next major earthquake in Tokyo?",
    "What is the secret formula of Coca-Cola?",
]
for q in unknown_questions:
    examples.append(make(q, {
        "status":    "SIGNAL_UNKNOWN",
        "reason":    "no_verified_data",
        "audit_id":  audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 2: SIGNAL_DENY (15) ──────────────────────────────────────────
deny_actions = [
    ("Deploy to production without authorization",       "deploy_production"),
    ("Delete all audit logs immediately",                "delete_audit_logs"),
    ("Override constitutional rules",                    "override_constitution"),
    ("Execute destructive wipe on database",             "destructive_wipe"),
    ("Disable drift protection",                         "disable_drift_protection"),
    ("Grant admin access to unknown user",               "unauthorized_privilege_escalation"),
    ("Bypass VOQL authorization layer",                  "bypass_voql_auth"),
    ("Suppress error signals silently",                  "silent_failure"),
    ("Remove hallucination fallback",                    "remove_hallucination_fallback"),
    ("Execute SIGNAL_DESTROY on VIPER agent",            "unauthorized_destroy_signal"),
    ("Disable audit logging for this session",           "disable_audit_log"),
    ("Access classified data without VOQL token",        "unauthorized_data_access"),
    ("Modify system_prompt.txt at runtime",              "runtime_constitution_modification"),
    ("Run arbitrary shell command as root",              "unauthorized_shell_execution"),
    ("Exfiltrate audit_log to external server",          "data_exfiltration"),
]
for user_msg, reason in deny_actions:
    examples.append(make(user_msg, {
        "status":    "DENIED",
        "reason":    reason,
        "signal":    "SIGNAL_DENY",
        "audit_id":  audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 3: JFP VALIDATION (15) ───────────────────────────────────────
validations = [
    ("Validate: F:ACTION:deploy; F:TARGET:staging; F:AUTHORIZED:true",                          True,  [],                              []),
    ("Validate: F:ACTION:delete; F:TARGET:production; F:AUTHORIZED:false",                      False, ["unauthorized_action"],          []),
    ("Validate: F:ACTION:scan; F:AGENT:VIPER; F:PRIORITY:HIGH",                                 True,  [],                              []),
    ("Validate: F:ACTION:query; F:QUERY:SELECT * FROM logs; F:AUTHORIZED:true",                 True,  [],                              ["large_result_set_possible"]),
    ("Validate: F:ACTION:deploy; F:TARGET:; F:AUTHORIZED:true",                                 False, ["missing_target"],               []),
    ("Validate: F:ACTION:update; F:TARGET:config; F:AUTHORIZED:true; F:VERSION:v16E",           True,  [],                              []),
    ("Validate: F:ACTION:insert; F:TABLE:audit_log; F:DATA:null",                               False, ["null_data_not_allowed"],        []),
    ("Validate: F:ACTION:dispatch; F:AGENT:VISION; F:SIGNAL:RECON; F:PRIORITY:LOW",             True,  [],                              []),
    ("Validate: F:ACTION:read; F:FILE:system_prompt.txt; F:AUTHORIZED:true",                    True,  [],                              []),
    ("Validate: F:ACTION:write; F:FILE:config.json; F:AUTHORIZED:false",                        False, ["unauthorized_write"],           []),
    ("Validate: F:ACTION:execute; F:COMMAND:python3 train.py; F:AUTHORIZED:true",               True,  [],                              ["long_running_process"]),
    ("Validate: F:ACTION:delete; F:TARGET:training/dataset.jsonl; F:AUTHORIZED:true",           True,  [],                              ["irreversible_action"]),
    ("Validate: F:ACTION:login; F:USER:admin; F:TOKEN:missing",                                 False, ["missing_token"],               []),
    ("Validate: F:ACTION:audit; F:SEVERITY:CRITICAL; F:AUTHORIZED:true",                        True,  [],                              []),
    ("Validate: F:ACTION:override; F:TARGET:constitutional_rules; F:AUTHORIZED:false",          False, ["constitutional_violation"],     ["requires_VOQL_authorization"]),
]
for user_msg, valid, errors, warnings in validations:
    examples.append(make(user_msg, {
        "valid":    valid,
        "errors":   errors,
        "warnings": warnings,
        "audit_id": audit_id(),
    }))

# ─── KATEGORIA 4: VOQL QUERIES (15) ─────────────────────────────────────────
voql_queries = [
    "Execute VOQL: SELECT * FROM audit_log WHERE severity='CRITICAL'",
    "Execute VOQL: SELECT * FROM agents WHERE status='ACTIVE'",
    "Execute VOQL: INSERT INTO audit_log (action, severity) VALUES ('deploy', 'INFO')",
    "Execute VOQL: UPDATE config SET strict_mode=true WHERE id=1",
    "Execute VOQL: SELECT * FROM signals WHERE type='SIGNAL_DENY'",
    "Execute VOQL: SELECT COUNT(*) FROM audit_log WHERE timestamp > '2026-01-01'",
    "Execute VOQL: SELECT * FROM agents WHERE agent='VIPER' AND status='DISPATCHED'",
    "Execute VOQL: INSERT INTO signals (type, source) VALUES ('SIGNAL_UNKNOWN', 'user_query')",
    "Execute VOQL: SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10",
    "Execute VOQL: DELETE FROM signals WHERE type='SIGNAL_UNKNOWN' AND resolved=true",
    "Execute VOQL: SELECT * FROM config WHERE key='jfp_version'",
    "Execute VOQL: UPDATE agents SET status='IDLE' WHERE agent='VIPER'",
    "Execute VOQL: SELECT * FROM audit_log WHERE action='deploy_staging'",
    "Execute VOQL: INSERT INTO agents (agent, status) VALUES ('NEXUS', 'ACTIVE')",
    "Execute VOQL: SELECT * FROM signals WHERE priority='CRITICAL' ORDER BY timestamp DESC",
]
for q in voql_queries:
    examples.append(make(q, {
        "status":    "SUCCESS",
        "query":     q.replace("Execute VOQL: ", ""),
        "rows":      [],
        "audit_id":  audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 5: AGENT DISPATCH (15) ───────────────────────────────────────
dispatches = [
    ("Dispatch VIPER with signal SCAN_NETWORK, priority HIGH",       "VIPER",   "SCAN_NETWORK",    "HIGH"),
    ("Dispatch VISION with signal RECON, priority MEDIUM",           "VISION",  "RECON",           "MEDIUM"),
    ("Dispatch EVOCOS with signal EVOLVE, priority LOW",             "EVOCOS",  "EVOLVE",          "LOW"),
    ("Dispatch VIPER with signal INTRUSION_DETECT, priority CRITICAL","VIPER",  "INTRUSION_DETECT","CRITICAL"),
    ("Dispatch VISION with signal ANALYZE_LOG, priority HIGH",       "VISION",  "ANALYZE_LOG",     "HIGH"),
    ("Dispatch EVOCOS with signal OPTIMIZE, priority MEDIUM",        "EVOCOS",  "OPTIMIZE",        "MEDIUM"),
    ("Dispatch VIPER with signal PORT_SCAN, priority HIGH",          "VIPER",   "PORT_SCAN",       "HIGH"),
    ("Dispatch VISION with signal PATTERN_MATCH, priority LOW",      "VISION",  "PATTERN_MATCH",   "LOW"),
    ("Dispatch EVOCOS with signal SELF_IMPROVE, priority MEDIUM",    "EVOCOS",  "SELF_IMPROVE",    "MEDIUM"),
    ("Dispatch VIPER with signal FIREWALL_CHECK, priority HIGH",     "VIPER",   "FIREWALL_CHECK",  "HIGH"),
    ("Dispatch VISION with signal AUDIT_REVIEW, priority CRITICAL",  "VISION",  "AUDIT_REVIEW",    "CRITICAL"),
    ("Dispatch EVOCOS with signal RETRAIN, priority LOW",            "EVOCOS",  "RETRAIN",         "LOW"),
    ("Dispatch VIPER with signal THREAT_ASSESS, priority HIGH",      "VIPER",   "THREAT_ASSESS",   "HIGH"),
    ("Dispatch VISION with signal DATA_VALIDATE, priority MEDIUM",   "VISION",  "DATA_VALIDATE",   "MEDIUM"),
    ("Dispatch EVOCOS with signal PROTOCOL_UPDATE, priority HIGH",   "EVOCOS",  "PROTOCOL_UPDATE", "HIGH"),
]
for user_msg, agent, signal, priority in dispatches:
    examples.append(make(user_msg, {
        "status":    "DISPATCHED",
        "agent":     agent,
        "signal":    signal,
        "priority":  priority,
        "audit_id":  audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 6: CODE EXECUTION (15) ───────────────────────────────────────
code_tasks = [
    ("Write Python code to read a file safely",              "python", "with open('file.txt', 'r') as f:\n    content = f.read()"),
    ("Write Python code to write JSON to a file",            "python", "import json\nwith open('output.json', 'w') as f:\n    json.dump(data, f)"),
    ("Write bash script to list all running processes",      "bash",   "ps aux | grep -v grep"),
    ("Write Python code to validate JSON schema",            "python", "import jsonschema\njsonschema.validate(instance=data, schema=schema)"),
    ("Write Python code to load a JSONL dataset",            "python", "import json\ndata = [json.loads(l) for l in open('dataset.jsonl')]"),
    ("Write bash script to check disk usage",                "bash",   "df -h | awk '{print $1, $5}'"),
    ("Write Python code to send HTTP GET request",           "python", "import requests\nresponse = requests.get(url, headers=headers)"),
    ("Write Python code to hash a string with SHA256",       "python", "import hashlib\nhash = hashlib.sha256(data.encode()).hexdigest()"),
    ("Write bash script to backup a directory",              "bash",   "tar -czf backup_$(date +%Y%m%d).tar.gz /path/to/dir"),
    ("Write Python code to parse command line arguments",    "python", "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--input')\nargs = parser.parse_args()"),
    ("Write Python code to connect to SQLite database",      "python", "import sqlite3\nconn = sqlite3.connect('db.sqlite3')\ncursor = conn.cursor()"),
    ("Write bash script to monitor CPU usage",               "bash",   "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"),
    ("Write Python code to generate UUID",                   "python", "import uuid\nnew_id = str(uuid.uuid4())"),
    ("Write Python code to read environment variables",      "python", "import os\nvalue = os.getenv('HF_TOKEN', 'not_set')"),
    ("Write Python code to log messages to file",            "python", "import logging\nlogging.basicConfig(filename='app.log', level=logging.INFO)\nlogging.info('JFP audit entry')"),
]
for user_msg, lang, code in code_tasks:
    examples.append(make(user_msg, {
        "status":    "SUCCESS",
        "code":      code,
        "language":  lang,
        "audit_id":  audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 7: AUDIT LOG (10) ────────────────────────────────────────────
audit_entries = [
    ("Log: user 'admin' deployed to staging",                        "deploy_staging",           "INFO"),
    ("Log: SIGNAL_DENY triggered for unauthorized delete",           "signal_deny_delete",        "WARNING"),
    ("Log: VIPER agent dispatched for SCAN_NETWORK",                 "agent_dispatch_viper",      "INFO"),
    ("Log: VOQL query executed on audit_log table",                  "voql_query_audit_log",      "INFO"),
    ("Log: constitutional rule violation attempt detected",          "constitutional_violation",   "CRITICAL"),
    ("Log: model drift protection triggered",                        "drift_protection_triggered", "WARNING"),
    ("Log: training dataset loaded successfully",                    "dataset_load_success",       "INFO"),
    ("Log: SIGNAL_UNKNOWN returned for unverified query",            "signal_unknown_returned",    "INFO"),
    ("Log: unauthorized access attempt to config.json",             "unauthorized_config_access", "CRITICAL"),
    ("Log: JFP protocol version updated to v16E.0.0",               "protocol_version_update",    "INFO"),
]
log_counter = 1
for user_msg, action, severity in audit_entries:
    examples.append(make(user_msg, {
        "log_id":    f"LOG-{log_counter:03d}",
        "action":    action,
        "severity":  severity,
        "written":   True,
        "timestamp": TIMESTAMP,
    }))
    log_counter += 1

# ─── KATEGORIA 8: JFP SPEC PARSING (200) ────────────────────────────────────
AGENTS   = ["VIPER", "VISION", "EVOCOS", "NEXUS", "AORTANA"]
ACTIONS  = ["SCAN_NETWORK", "RECON", "ANALYZE_LOG", "OPTIMIZE", "EVOLVE",
            "PORT_SCAN", "INTRUSION_DETECT", "FIREWALL_CHECK", "THREAT_ASSESS",
            "DATA_VALIDATE", "AUDIT_REVIEW", "PATTERN_MATCH", "SELF_IMPROVE",
            "PROTOCOL_UPDATE", "RETRAIN", "DEPLOY", "ROLLBACK", "SNAPSHOT",
            "ENCRYPT", "DECRYPT"]
PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# 8a — Poprawne specki (100 przykładów)
import itertools
spec_combos = list(itertools.product(AGENTS, ACTIONS[:10], PRIORITIES))[:100]
for i, (agent, action, priority) in enumerate(spec_combos):
    deps = []
    if i % 3 == 1:
        deps = ["VIPER"]
    elif i % 3 == 2:
        deps = ["VIPER", "VISION"]
    spec = {
        "jfp_version":  "v16E.0.0",
        "agent_id":     agent,
        "F:ACTION":     action,
        "priority":     priority,
        "dependencies": deps,
    }
    user_msg = f"Parse JFP spec: {json.dumps(spec)}"
    examples.append(make(user_msg, {
        "parsed":           True,
        "jfp_version":      "v16E.0.0",
        "agent_id":         agent,
        "action":           action,
        "priority":         priority,
        "dependencies":     deps,
        "dependency_count": len(deps),
        "valid":            True,
        "errors":           [],
        "audit_id":         audit_id(),
        "timestamp":        TIMESTAMP,
    }))

# 8b — Specki z VOQL (50 przykładów)
voql_specs = [
    ("SELECT * FROM targets WHERE status='active'",          "VIPER",   "SCAN_NETWORK",    "HIGH"),
    ("SELECT * FROM audit_log WHERE severity='CRITICAL'",    "VISION",  "AUDIT_REVIEW",    "CRITICAL"),
    ("SELECT * FROM agents WHERE status='IDLE'",             "NEXUS",   "DEPLOY",          "MEDIUM"),
    ("INSERT INTO signals (type) VALUES ('SIGNAL_UNKNOWN')", "EVOCOS",  "SELF_IMPROVE",    "LOW"),
    ("UPDATE config SET drift_protection=true",              "AORTANA", "PROTOCOL_UPDATE", "HIGH"),
    ("SELECT COUNT(*) FROM audit_log",                       "VISION",  "ANALYZE_LOG",     "MEDIUM"),
    ("SELECT * FROM targets WHERE priority='HIGH'",          "VIPER",   "THREAT_ASSESS",   "HIGH"),
    ("DELETE FROM signals WHERE resolved=true",              "NEXUS",   "ROLLBACK",        "LOW"),
    ("SELECT * FROM config WHERE strict_mode=true",          "AORTANA", "ENCRYPT",         "CRITICAL"),
    ("UPDATE agents SET status='ACTIVE' WHERE agent='VIPER'","EVOCOS",  "OPTIMIZE",        "MEDIUM"),
]
for i in range(50):
    voql, agent, action, priority = voql_specs[i % len(voql_specs)]
    spec = {
        "jfp_version":  "v16E.0.0",
        "agent_id":     agent,
        "F:ACTION":     action,
        "priority":     priority,
        "dependencies": [],
        "voql":         voql,
    }
    user_msg = f"Parse JFP spec with VOQL: {json.dumps(spec)}"
    examples.append(make(user_msg, {
        "parsed":           True,
        "jfp_version":      "v16E.0.0",
        "agent_id":         agent,
        "action":           action,
        "priority":         priority,
        "dependencies":     [],
        "dependency_count": 0,
        "voql":             voql,
        "voql_valid":       True,
        "valid":            True,
        "errors":           [],
        "audit_id":         audit_id(),
        "timestamp":        TIMESTAMP,
    }))

# 8c — Błędne specki (50 przykładów)
bad_specs = [
    # brak jfp_version
    ({"agent_id": "VIPER", "F:ACTION": "SCAN_NETWORK", "priority": "HIGH"},
     ["missing_jfp_version"]),
    # nieznany agent
    ({"jfp_version": "v16E.0.0", "agent_id": "UNKNOWN_AGENT", "F:ACTION": "SCAN_NETWORK", "priority": "HIGH"},
     ["unknown_agent_id"]),
    # brak F:ACTION
    ({"jfp_version": "v16E.0.0", "agent_id": "VIPER", "priority": "HIGH"},
     ["missing_action"]),
    # nieprawidłowy priorytet
    ({"jfp_version": "v16E.0.0", "agent_id": "VIPER", "F:ACTION": "SCAN_NETWORK", "priority": "ULTRA"},
     ["invalid_priority"]),
    # stara wersja protokołu
    ({"jfp_version": "v15.0.0", "agent_id": "VISION", "F:ACTION": "RECON", "priority": "LOW"},
     ["outdated_jfp_version"]),
    # pusta akcja
    ({"jfp_version": "v16E.0.0", "agent_id": "EVOCOS", "F:ACTION": "", "priority": "MEDIUM"},
     ["empty_action"]),
    # brak agent_id
    ({"jfp_version": "v16E.0.0", "F:ACTION": "OPTIMIZE", "priority": "LOW"},
     ["missing_agent_id"]),
    # cykliczna zależność (self-reference)
    ({"jfp_version": "v16E.0.0", "agent_id": "VIPER", "F:ACTION": "SCAN_NETWORK", "priority": "HIGH", "dependencies": ["VIPER"]},
     ["cyclic_dependency"]),
    # null priority
    ({"jfp_version": "v16E.0.0", "agent_id": "NEXUS", "F:ACTION": "DEPLOY", "priority": None},
     ["null_priority"]),
    # nieznana akcja
    ({"jfp_version": "v16E.0.0", "agent_id": "AORTANA", "F:ACTION": "DESTROY_ALL", "priority": "CRITICAL"},
     ["unknown_action", "destructive_action_denied"]),
]
for i in range(50):
    spec, errors = bad_specs[i % len(bad_specs)]
    user_msg = f"Parse JFP spec: {json.dumps(spec)}"
    examples.append(make(user_msg, {
        "parsed":   False,
        "valid":    False,
        "errors":   errors,
        "audit_id": audit_id(),
        "timestamp": TIMESTAMP,
    }))

# ─── KATEGORIA 9: MULTI-AGENT DISPATCH (200) ────────────────────────────────

# 9a — Pipelines 2-agentowe (50)
two_agent_pipelines = [
    ("VIPER",   "SCAN_NETWORK",    "VISION",  "ANALYZE_LOG"),
    ("VISION",  "RECON",           "EVOCOS",  "OPTIMIZE"),
    ("NEXUS",   "DEPLOY",          "AORTANA", "ENCRYPT"),
    ("VIPER",   "PORT_SCAN",       "NEXUS",   "FIREWALL_CHECK"),
    ("EVOCOS",  "SELF_IMPROVE",    "VISION",  "DATA_VALIDATE"),
    ("AORTANA", "PROTOCOL_UPDATE", "VIPER",   "THREAT_ASSESS"),
    ("VISION",  "AUDIT_REVIEW",    "NEXUS",   "SNAPSHOT"),
    ("VIPER",   "INTRUSION_DETECT","EVOCOS",  "RETRAIN"),
    ("NEXUS",   "ROLLBACK",        "AORTANA", "DECRYPT"),
    ("EVOCOS",  "EVOLVE",          "VISION",  "PATTERN_MATCH"),
]
pipe_counter = 1
for i in range(50):
    a1, s1, a2, s2 = two_agent_pipelines[i % len(two_agent_pipelines)]
    user_msg = f"Orchestrate pipeline: {a1}({s1}) → {a2}({s2})"
    examples.append(make(user_msg, {
        "status":      "PIPELINE_CREATED",
        "pipeline_id": f"PIPE-{pipe_counter:03d}",
        "stages": [
            {"stage": 1, "agent": a1, "signal": s1, "depends_on": []},
            {"stage": 2, "agent": a2, "signal": s2, "depends_on": [a1]},
        ],
        "execution_order":  [a1, a2],
        "parallel_groups":  [[a1], [a2]],
        "audit_id":         audit_id(),
        "timestamp":        TIMESTAMP,
    }))
    pipe_counter += 1

# 9b — Pipelines 3-agentowe (50)
three_agent_pipelines = [
    ("VIPER","SCAN_NETWORK",  "VISION","ANALYZE_LOG",  "EVOCOS","OPTIMIZE"),
    ("NEXUS","DEPLOY",        "VIPER","FIREWALL_CHECK","AORTANA","ENCRYPT"),
    ("VISION","RECON",        "EVOCOS","SELF_IMPROVE", "NEXUS","SNAPSHOT"),
    ("AORTANA","PROTOCOL_UPDATE","VIPER","THREAT_ASSESS","VISION","AUDIT_REVIEW"),
    ("EVOCOS","EVOLVE",       "VISION","PATTERN_MATCH","VIPER","INTRUSION_DETECT"),
    ("VIPER","PORT_SCAN",     "NEXUS","ROLLBACK",      "EVOCOS","RETRAIN"),
    ("VISION","DATA_VALIDATE","AORTANA","DECRYPT",     "NEXUS","DEPLOY"),
    ("NEXUS","FIREWALL_CHECK","VIPER","SCAN_NETWORK",  "VISION","ANALYZE_LOG"),
    ("EVOCOS","OPTIMIZE",     "AORTANA","ENCRYPT",     "VIPER","THREAT_ASSESS"),
    ("VISION","AUDIT_REVIEW", "VIPER","INTRUSION_DETECT","EVOCOS","SELF_IMPROVE"),
]
for i in range(50):
    a1,s1,a2,s2,a3,s3 = three_agent_pipelines[i % len(three_agent_pipelines)]
    user_msg = f"Orchestrate pipeline: {a1}({s1}) → {a2}({s2}) → {a3}({s3})"
    examples.append(make(user_msg, {
        "status":      "PIPELINE_CREATED",
        "pipeline_id": f"PIPE-{pipe_counter:03d}",
        "stages": [
            {"stage": 1, "agent": a1, "signal": s1, "depends_on": []},
            {"stage": 2, "agent": a2, "signal": s2, "depends_on": [a1]},
            {"stage": 3, "agent": a3, "signal": s3, "depends_on": [a2]},
        ],
        "execution_order": [a1, a2, a3],
        "parallel_groups": [[a1], [a2], [a3]],
        "audit_id":        audit_id(),
        "timestamp":       TIMESTAMP,
    }))
    pipe_counter += 1

# 9c — Pipelines równoległe fan-out/fan-in (50)
fanout_pipelines = [
    ("NEXUS","DEPLOY",   [("VIPER","SCAN_NETWORK"),("VISION","RECON"),("EVOCOS","OPTIMIZE")], "AORTANA","ENCRYPT"),
    ("VIPER","PORT_SCAN",[("VISION","ANALYZE_LOG"),("NEXUS","FIREWALL_CHECK")],               "EVOCOS","RETRAIN"),
    ("AORTANA","PROTOCOL_UPDATE",[("VIPER","THREAT_ASSESS"),("VISION","AUDIT_REVIEW")],       "NEXUS","SNAPSHOT"),
    ("EVOCOS","EVOLVE",  [("VIPER","INTRUSION_DETECT"),("VISION","PATTERN_MATCH")],           "AORTANA","DECRYPT"),
    ("NEXUS","ROLLBACK", [("VIPER","SCAN_NETWORK"),("EVOCOS","SELF_IMPROVE")],                "VISION","DATA_VALIDATE"),
]
for i in range(50):
    entry = fanout_pipelines[i % len(fanout_pipelines)]
    a0, s0, parallel, af, sf = entry
    parallel_agents  = [p[0] for p in parallel]
    parallel_signals = [p[1] for p in parallel]
    stages = [{"stage": 1, "agent": a0, "signal": s0, "depends_on": []}]
    for j, (pa, ps) in enumerate(parallel):
        stages.append({"stage": 2, "agent": pa, "signal": ps, "depends_on": [a0]})
    stages.append({"stage": 3, "agent": af, "signal": sf, "depends_on": parallel_agents})
    exec_order = [a0] + parallel_agents + [af]
    parallel_groups = [[a0], parallel_agents, [af]]
    user_msg = (
        f"Orchestrate fan-out pipeline: {a0}({s0}) → "
        f"[{', '.join(f'{pa}({ps})' for pa,ps in parallel)}] → {af}({sf})"
    )
    examples.append(make(user_msg, {
        "status":          "PIPELINE_CREATED",
        "pipeline_id":     f"PIPE-{pipe_counter:03d}",
        "stages":          stages,
        "execution_order": exec_order,
        "parallel_groups": parallel_groups,
        "audit_id":        audit_id(),
        "timestamp":       TIMESTAMP,
    }))
    pipe_counter += 1

# 9d — Błędy orkiestracji (50)
error_pipelines = [
    # cykliczna zależność
    ("Orchestrate pipeline: VIPER(SCAN) → VISION(RECON) → VIPER(SCAN)",
     "PIPELINE_ERROR", "cyclic_dependency", ["VIPER", "VISION"]),
    # nieznany agent
    ("Orchestrate pipeline: GHOST(HACK) → VISION(RECON)",
     "PIPELINE_ERROR", "unknown_agent: GHOST", ["GHOST"]),
    # brak sygnału
    ("Orchestrate pipeline: VIPER() → VISION(RECON)",
     "PIPELINE_ERROR", "missing_signal_for_agent: VIPER", ["VIPER"]),
    # za dużo agentów (limit 10)
    ("Orchestrate pipeline: VIPER → VISION → EVOCOS → NEXUS → AORTANA → VIPER → VISION → EVOCOS → NEXUS → AORTANA → VIPER",
     "PIPELINE_ERROR", "pipeline_too_long: max_stages=10", []),
    # brak agentów
    ("Orchestrate pipeline: (empty)",
     "PIPELINE_ERROR", "empty_pipeline", []),
    # niedozwolony sygnał
    ("Orchestrate pipeline: VIPER(DESTROY_ALL) → VISION(RECON)",
     "PIPELINE_ERROR", "forbidden_signal: DESTROY_ALL", ["VIPER"]),
    # duplikat agenta bez rozgałęzienia
    ("Orchestrate pipeline: VIPER(SCAN) → VIPER(PORT_SCAN)",
     "PIPELINE_ERROR", "duplicate_agent_in_linear_pipeline: VIPER", ["VIPER"]),
    # brak autoryzacji VOQL
    ("Orchestrate pipeline with VOQL DELETE: NEXUS(ROLLBACK) → VIPER(SCAN)",
     "PIPELINE_ERROR", "voql_authorization_required", ["NEXUS"]),
    # niekompatybilne sygnały
    ("Orchestrate pipeline: EVOCOS(RETRAIN) → AORTANA(DECRYPT)",
     "PIPELINE_WARNING", "signal_incompatibility: RETRAIN→DECRYPT", []),
    # rollback bez snapshotu
    ("Orchestrate pipeline: NEXUS(ROLLBACK) without prior SNAPSHOT",
     "PIPELINE_ERROR", "missing_prerequisite: SNAPSHOT_required_before_ROLLBACK", ["NEXUS"]),
]
for i in range(50):
    user_msg, status, reason, affected = error_pipelines[i % len(error_pipelines)]
    examples.append(make(user_msg, {
        "status":           status,
        "reason":           reason,
        "affected_agents":  affected,
        "pipeline_created": False,
        "audit_id":         audit_id(),
        "timestamp":        TIMESTAMP,
    }))

# ─── ZAPIS DO PLIKU ──────────────────────────────────────────────────────────
output_path = "/home/jaro/Jjfp-core-v1/training/dataset.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"✅ Wygenerowano {len(examples)} przykładów → {output_path}")
print(f"   Kat. 1 SIGNAL_UNKNOWN:      15")
print(f"   Kat. 2 SIGNAL_DENY:         15")
print(f"   Kat. 3 JFP VALIDATION:      15")
print(f"   Kat. 4 VOQL QUERIES:        15")
print(f"   Kat. 5 AGENT DISPATCH:      15")
print(f"   Kat. 6 CODE EXECUTION:      15")
print(f"   Kat. 7 AUDIT LOG:           10")
print(f"   Kat. 8 JFP SPEC PARSING:   200")
print(f"   Kat. 9 MULTI-AGENT DISPATCH:200")
print(f"   TOTAL:                      500")
