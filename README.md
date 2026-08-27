# agentview

A terminal dashboard for headless Claude Code agents running on another machine.

You launch long-running `claude -p` agents on a workhorse box over ssh, and then
lose track of them: which are still working, what they are doing, which finished
with work you never collected. `agentview` gives you one screen for all of it —
and lets you talk to them.

```
AGENTS · 2 running · 1 needs review

 ● run121   29m · opus/high    task-b → feature/dropdown
   Does the onboarding conflict card actually fire?
   ▸ running  npx jest src/components/__tests__       5s ago
     "Now proving the tests were red before the fix."
   typical 16–33m across 24 past runs

 ✓ run118   52m · opus/high    task-a
   Rework the country filter
   9 files UNCOMMITTED
   SUMMARY: Fixed the filter and added a regression test; the sentinel
   string is still hardcoded in English, worth a follow-up.
```

## Why

Headless agents are opaque. `claude -p --output-format text` writes **nothing**
until the run ends, so a 50-minute agent is a zero-byte log file and a hope.
There is no way to tell working from hung, no way to see what it is doing, and
no record of what a finished run concluded.

`agentview` reads Claude Code's own session transcripts, which are written live
regardless of how the agent was launched. So every agent is visible — including
ones started by hand, by a script, or by another session entirely.

## Install

```sh
export AGENT_HOST=myserver     # the ssh host your agents run on
./install.sh
```

Client scripts go to `~/.local/bin`, host scripts to `$AGENT_HOST:~/bin`.
Requires `python3` on both ends and passwordless ssh to `$AGENT_HOST`.

## Use

```sh
mini                # the dashboard
mini once           # one plain snapshot, for scripts or scrollback
mini show <id>      # a run's full report and uncommitted diffstat
```

Inside the dashboard:

| key | |
|---|---|
| `↑` `↓` | move |
| `↵` `→` | open a run — live narration and every tool call |
| `←` `esc` | back |
| `m` | message the agent |
| `a` | show finished, already-collected runs |
| `q` | quit |

Launch a tracked agent:

```sh
TITLE="Fix the country dropdown filter" \
  mini-run /home/you/proj.worktrees/task-a ~/briefs/dropdown.md run1 opus high
```

`TITLE` is required — an untitled run is one you cannot identify later.
`mini-run` refuses to start on a dirty worktree, because a brief that begins
with `git reset --hard` will destroy whatever is sitting there.

## Talking to agents

Two modes, and the difference matters.

**Live** — agents launched by `mini-run` get a named pipe on stdin. Pressing `m`
writes a real message into the running agent. It arrives at the agent's **next
turn boundary**: you can add a constraint or redirect its next move, but you
cannot interrupt work already in flight.

**Forked** — for anything else (finished runs, or agents launched another way),
`m` resumes a *fork* of the agent's session and asks there. The answer is
accurate about its work, but nothing you say reaches the original process.

The dashboard tells you which one you are in.

## What it shows

- **live narration** — the agent's own words, straight from its transcript, no
  extra model call
- **phase** — reading, editing, running, searching, and the file or command
- **stall detection** — no events for 10 minutes on a running agent
- **`N files UNCOMMITTED`** — finished, but you never collected the work. This is
  the state that actually costs you something.
- **`worktree removed`** — cannot verify what was harvested, which is *not* the
  same as clean. A dashboard that reports a deleted worktree as tidy is worse
  than no dashboard.
- **duration bands** calibrated from your own past runs, shown only once a run is
  old enough for the comparison to mean anything

## Design notes

Ending every brief with a `SUMMARY:` line costs nothing and beats summarising a
report after the fact — the agent knows its own work better than a summariser
does. `mini-run` appends that instruction automatically.

Agents with an open input channel **do not exit on stdin EOF**. The launcher
watches for a `result` event, waits out a grace period in case you want a
follow-up question, then shuts the agent down explicitly. Without that, every
agent you ever launch stays resident forever.

`agentview` never kills, commits, or pushes. It writes only its own metadata
under `~/.agentrun`, and messages you deliberately send.

## Configuration

| variable | |
|---|---|
| `AGENT_HOST` | ssh host the agents run on (required) |
| `AGENT_IGNORE` | pattern excluded from the dirty-worktree check |
| `AGENTRUN_STALL` | seconds of silence before a run is flagged (default 600) |
| `AGENTRUN_GRACE` | seconds an idle agent stays reachable (default 120) |

## Limitations

- One remote host. Local agents and other machines are not shown.
- Messages queue to a turn boundary; there is no interrupt.
- Runs not launched by `mini-run` are adopted automatically but have no live
  input channel and cannot be given one after the fact.

## License

MIT
