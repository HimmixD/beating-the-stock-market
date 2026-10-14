# Graph Report - btsm  (2026-10-14)

## Corpus Check
- 29 files · ~5,937 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 4, .csv 1)

## Summary
- 182 nodes · 283 edges · 16 communities (10 shown, 6 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 55 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `10137e26`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SecProvider
- router.py
- 10 Identified Problems
- Fixes Applied to Pit-Aware Base Layer
- PitRouter
- test_pit_suit.py
- SQLiteStore
- sec_client.py
- GlobalProvider
- test_actions.py
- quant-project

## God Nodes (most connected - your core abstractions)
1. `SQLiteStore` - 18 edges
2. `PitRouter` - 15 edges
3. `GlobalProvider` - 14 edges
4. `SecProvider` - 13 edges
5. `2. Architecture Findings (source code unchanged)` - 12 edges
6. `10 Identified Problems` - 11 edges
7. `SecClient` - 11 edges
8. `BaseProvider` - 11 edges
9. `ActionsProvider` - 10 edges
10. `Fixes Applied to Pit-Aware Base Layer` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Fix 5: Improved Split Data Freshness` --references--> `ActionsProvider`  [INFERRED]
  docs/archive/FIXES_SUMMARY.md → src/pit_layer/providers/actions_provider.py
- `Data Flow` --references--> `GlobalProvider`  [INFERRED]
  ARCHITECTURE.md → src/pit_layer/providers/global_provider.py
- `Data Flow` --references--> `SecProvider`  [INFERRED]
  ARCHITECTURE.md → src/pit_layer/providers/sec_provider.py
- `2. Architecture Findings (source code unchanged)` --references--> `SQLiteStore`  [INFERRED]
  docs/ARCHITECTURE_REPORT.md → src/pit_layer/cache/sqlite_store.py
- `2. Architecture Findings (source code unchanged)` --references--> `ActionsProvider`  [INFERRED]
  docs/ARCHITECTURE_REPORT.md → src/pit_layer/providers/actions_provider.py

## Import Cycles
- None detected.

## Communities (16 total, 6 thin omitted)

### Community 0 - "SecProvider"
Cohesion: 0.15
Nodes (4): 2. Architecture Findings (source code unchanged), SecClient, BaseProvider, SecProvider

### Community 1 - "router.py"
Cohesion: 0.11
Nodes (4): PriceClient, price_client(), test_fetch_historical_prices_apple(), test_fetch_historical_prices_invalid_ticker()

### Community 2 - "10 Identified Problems"
Cohesion: 0.13
Nodes (14): 10 Identified Problems, 10. **No Data Versioning/Invalidation**, 1. **PIT Look-Ahead Bias Gaps**, 2. **Global Provider Missing PIT Filtering**, 3. **Limited Non-US Ticker Coverage**, 5. **Incomplete Concept Mapping**, 6. **Stale Split Data**, 8. **PIT Status Oversimplification** (+6 more)

### Community 3 - "Fixes Applied to Pit-Aware Base Layer"
Cohesion: 0.12
Nodes (14): 1. **PitRouter** (`router.py`), 2. **SQLiteStore** (`cache/sqlite_store.py`), 3. **Providers**, 4. **Concept Map** (`utils.py`), Core Architecture, Additional Notes, Fix 1: Global Provider PIT Filtering (Critical), Fix 3: Expanded Concept Mapping (+6 more)

### Community 4 - "PitRouter"
Cohesion: 0.12
Nodes (8): 1. Ghost Files / Redundancies, 3. Recommendations (out of scope for cleanup), Architecture Report, 4. **Oversimplified US/Non-US Routing**, Fix 2: Enhanced Ticker Routing, run_all_commands(), ActionsProvider, PitRouter

### Community 5 - "test_pit_suit.py"
Cohesion: 0.12
Nodes (7): router(), router(), test_global_provider_routing(), test_pit_time_travel_constraints(), test_router_routing_logic(), test_sec_provider_apple_revenue(), test_router_apple_revenue()

### Community 6 - "SQLiteStore"
Cohesion: 0.12
Nodes (6): Architecture Overview, Conventions, Data Flow, Directory Layout, Key Components, SQLiteStore

### Community 7 - "sec_client.py"
Cohesion: 0.17
Nodes (3): load_golden_cases(), router(), test_golden_case_from_csv()

### Community 8 - "GlobalProvider"
Cohesion: 0.17
Nodes (5): 7. **Missing Configuration Validation**, OpenBBClient, GlobalProvider, MockOpenBBClient, test_global_provider_saving_and_retrieval()

### Community 9 - "test_actions.py"
Cohesion: 0.29
Nodes (3): router(), test_apple_stock_splits(), test_no_split_stock()

## Knowledge Gaps
- **18 isolated node(s):** `Directory Layout`, `Key Components`, `Conventions`, `1. Ghost Files / Redundancies`, `Project Overview` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 77 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SQLiteStore` connect `SQLiteStore` to `SecProvider`, `router.py`, `Fixes Applied to Pit-Aware Base Layer`, `PitRouter`, `GlobalProvider`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `SQLiteStore` (e.g. with `Data Flow` and `2. Architecture Findings (source code unchanged)`) actually correct?**
  _`SQLiteStore` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Directory Layout`, `Key Components`, `Conventions` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `router.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Why does `PitRouter` connect `PitRouter` to `SecProvider`, `router.py`, `test_pit_suit.py`, `SQLiteStore`, `sec_client.py`, `GlobalProvider`, `test_actions.py`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `PitRouter` (e.g. with `2. Architecture Findings (source code unchanged)` and `run_all_commands()`) actually correct?**
  _`PitRouter` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Should `10 Identified Problems` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._