# Usage Guide

This guide walks through the full migration-factory workflow using the sample
inventory in [`../examples/inventory.json`](../examples/inventory.json).

## Inventory format

An inventory is a JSON array of server objects. Only `id`, `hostname`, `os`,
`cpu`, and `memory_gb` are required; `dependencies` defaults to an empty list.

```json
[
  {
    "id": "web-01",
    "hostname": "web-01.corp.local",
    "os": "Ubuntu 22.04",
    "cpu": 4,
    "memory_gb": 16,
    "dependencies": ["db-01"]
  }
]
```

## 1. Assess

```bash
migration-factory assess examples/inventory.json -o assessed.json
```

Each server is assigned a disposition (one of the 6 Rs) and a readiness score:

- **retire** — no allocated vCPU (idle/decommissioned).
- **refactor** — end-of-life OS, or more than five dependencies.
- **replatform** — the workload has a managed-service equivalent (databases).
- **rehost** — a standard workload suitable for lift-and-shift.

The readiness score starts at 100 and is reduced by dependency coupling,
migration effort per strategy, and end-of-life operating systems.

## 2. Plan waves

```bash
migration-factory plan-waves assessed.json --max-wave-size 5 -o planned.json
```

Servers are topologically sorted so dependencies migrate before their
dependents, then packed into waves no larger than `--max-wave-size`. Servers
marked `retire` or `retain` are excluded from the plan.

## 3. Orchestrate and check status

```bash
migration-factory status planned.json --advance-to testing
```

A task is created per server and advanced along the happy path
(`pending -> replicating -> testing -> cutover -> complete`). The command prints
the count of tasks in each state.

## 4. Report

```bash
migration-factory report examples/inventory.json
```

Prints a combined summary: number of servers, average readiness, number of
waves, and a breakdown of dispositions.
