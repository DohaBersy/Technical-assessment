## How to run locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the tests
```bash
python -m pytest tests/ -v
```
All 31 tests should pass. No live DataHub instance is required.

### 3. Run the ingestion script (Part 1)
```bash
# Dry run -- logs what would be sent, no network calls made.
# This is the path fully verified in this submission.
python -m ingestion.run_ingestion --dry-run
```

To run against a real DataHub instance:
```bash
python -m ingestion.run_ingestion --gms-server http://localhost:8080
```
See "Known limitations" below regarding live-instance verification in
this submission's environment.

### 4. Run the rules engine (Part 2)
```bash
python -m rules_engine.run_rules --dry-run
python -m rules_engine.run_rules --gms-server http://localhost:8080
```

### 5. Run with Docker
```bash
docker build -t datahub-assessment .

# Runs ingestion by default
docker run datahub-assessment

# Override to run the rules engine instead
docker run datahub-assessment python -m rules_engine.run_rules --dry-run
```

---

## Answers to assignment questions

### Part 1: Ingestion

**How do you handle schema evolution?**

Because ingestion is idempotent, re-running the script after a source
table's columns change simply re-emits a new `SchemaMetadataClass` aspect
for that URN — DataHub overwrites the previous version rather than
creating a duplicate entity. DataHub keeps a version history of each
aspect, so the old schema isn't lost, just superseded. 

**What happens if the source has 10,000 datasets?**

The current implementation reads the whole CSV into memory and loops
through tables one at a time, emitting synchronously. For 10,000 tables
this would still work correctly, but slowly, since each of ~30,000 emit
calls happens one after another over HTTP. Known limitations at scale:
- No batching — each aspect is a separate HTTP call; production would use
  DataHub's bulk ingestion APIs.
- No pagination on the read side — fine for a CSV, but a paginated REST
  API source would need a page-by-page generator instead of a full list.
- No concurrency — sequential emits; a thread pool or async emitter would
  substantially speed up large runs.
- Memory isn't a concern at 10,000 rows, but would become one at millions
  of rows, where streaming the CSV row-by-row would be the fix.

### Part 2: Governance Rules Engine

**How would you add a new rule type without changing the core engine?**

The engine uses a small registry (`PROPERTY_CHECKS` in `evaluator.py`)
mapping a property name string to a function that checks it. Two cases:
- A new rule checking a property we already support (e.g. a second rule
  checking `hasDescription`) needs **zero code changes** — just add a
  block to `rules.yaml`. This repo proves it: two working rules use the
  same `evaluate_rule()` function.
- A rule needing a brand-new property (e.g. `hasSchema`) needs one new
  line in `PROPERTY_CHECKS` plus a new field in `DatasetInfo`/`reader.py`.

  So `evaluate_rule()`, the YAML format, and `tagger.py` never change in this case — the
  registry isolates "what can be checked" from "how evaluation works."

**How do you test the rules engine without a live DataHub instance?**

1. Pure-logic unit tests with no network at all — `rule_loader.py` and
   `evaluator.py` operate on plain Python objects, so their tests run
   instantly with hand-constructed inputs.
2. Mocking for the two modules that touch the network — `reader.py`
   (queries DataHub) and `tagger.py` (writes to it) — using
   `unittest.mock.patch`/`MagicMock` to replace the real SDK clients with
   controlled fakes.
3. `run_rules.py --dry-run` runs the entire pipeline start to finish,
   using the same CSV data, and prints out what it would have sent to
   DataHub instead of actually sending it — letting the whole thing be
   watched working end-to-end, safely, with zero risk of touching a
   real system.

---

## Known limitations

- **Live DataHub verification**: this submission's dry-run path (both
  ingestion and rules engine) was fully tested end-to-end, and the real
  network code path is covered by mocked unit tests. Bringing up a full
  local DataHub instance via `datahub docker quickstart` in a GitHub
  Codespace hit an infrastructure constraint: `Total Docker disk space
  available 6.99GB is below the minimum threshold 13GB`. Working around
  this by invoking `docker compose` directly (bypassing the CLI's disk
  check) got MySQL and Kafka running, but the environment's available
  disk was insufficient to bring up the full stack (OpenSearch, GMS,
  frontend) reliably. As a result, the real `--gms-server` path was not
  verified against an actual live DataHub instance in this submission —
  it is implemented per the SDK's documented API and covered by mocked
  tests, but not end-to-end verified against a running server.
- **Discovering which datasets to check**: `run_rules.py` reuses the
  ingestion CSV as its dataset list, rather than querying DataHub's
  search/browse API for "all datasets." A production version would use
  DataHub's search API to discover datasets dynamically.