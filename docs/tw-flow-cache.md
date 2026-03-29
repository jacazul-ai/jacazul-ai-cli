# tw-flow Output Cache

The cache system suppresses redundant output from `tw-flow status` and `tw-flow ponder`. When output hasn't changed since the last call, a short inline message is printed instead of the full output, keeping the agent's context window lean.

---

## How It Works

- Cache is **hash-based + TTL** — not purely time-based.
- On each call, tw-flow computes a hash of the real output and compares it to the stored hash.
- If hash matches AND TTL hasn't expired: print the cached signal instead of full output.
- If hash differs OR TTL expired: run full output, update cache.

**Cached signal example:**
```
🐊 [cached] Status unchanged since 12s ago. Use --force to refresh.
```

---

## Cache Storage

```
~/.jacazul-ai/.task/{PROJECT_ID}/cache/
  status.json
  status_{ini-name}.json
  ponder.json
  ponder_{ini-name}.json
```

One directory per project. One file per command + filter combination.

---

## Cache Key Schema

| Command | Cache file |
|---|---|
| `tw-flow status` | `status.json` |
| `tw-flow status flow-x` | `status_flow-x.json` |
| `tw-flow ponder` | `ponder.json` |
| `tw-flow ponder flow-x` | `ponder_flow-x.json` |

---

## TTL

| Command | TTL |
|---|---|
| `tw-flow status` (any filter) | 30s |
| `tw-flow ponder` (any filter) | 5min |

TTL is the same regardless of whether a filter is used.

---

## Cache Invalidation

### Write operation on ini X
Clears:
- `status.json` (unfiltered)
- `ponder.json` (unfiltered)
- `status_X.json` (filtered for affected ini)
- `ponder_X.json` (filtered for affected ini)

Other ini caches are untouched.

Write operations that trigger invalidation: `note`, `outcome`, `done`, `execute`, `discard`, `reopen`, `amend`, `ticket`.

### Focus change
Clears:
- `status.json` (unfiltered only)
- `ponder.json` (unfiltered only)

Filtered caches are untouched.

---

## Commands

```bash
# Bypass cache — always show full output
tw-flow status --force
tw-flow ponder --force

# Clear cache
tw-flow cache clear                # Clear everything
tw-flow cache clear status         # Clear only status cache entries
tw-flow cache clear ponder         # Clear only ponder cache entries

# Configure TTLs
tw-flow cache config

# Inspect cache state
tw-flow cache info                 # Show cached entries and expiry times
```

---

## Configuration

`tw-flow cache config` stores settings in `~/.jacazul-ai/.task/{PROJECT_ID}/cache/config.json`:

```json
{
  "status_ttl": 30,
  "ponder_ttl": 300
}
```

---

**Version:** 1.0.0
**Last Updated:** 2026-03-28
