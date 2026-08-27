# agentview

A terminal dashboard for headless Claude Code agents running on another machine.

I run long `claude -p` jobs on a Mac mini over ssh, often four or five at once.
The problem is that they're completely opaque while they work. `--output-format
text` buffers everything, so a 50 minute agent is a zero byte log file until it
finishes. You can't tell a working agent from a hung one, you can't see what
it's doing, and when it's done you have to go find its output yourself.

This shows all of them on one screen, live, and lets you talk to them.

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
   SUMMARY: Fixed the filter and added a regression test. The sentinel
   string is still hardcoded in English, worth a follow-up.
```

## Requirements

* `python3` on both machines, no packages needed
* passwordless ssh to the host your agents run on
* Claude Code on the remote host
* macOS or Linux

## Install

```sh
git clone https://github.com/pxshaaa/agentview
cd agentview
export AGENT_HOST=myserver
./install.sh
```

Client scripts land in `~/.local/bin`, host scripts in `$AGENT_HOST:~/bin`.

## Use

```sh
mini                # dashboard
mini once           # plain snapshot, for scripts or scrollback
mini show <id>      # a run's full report and uncommitted diffstat
```

In the dashboard:

| key | |
|---|---|
| `↑` `↓` | move |
| `↵` `→` | open a run, see live narration and every tool call |
| `←` `esc` | back |
| `m` | message the agent |
| `a` | show finished runs you've already collected |
| `q` | quit |

Launching a tracked agent:

```sh
TITLE="Fix the country dropdown filter" \
  mini-run /home/you/proj.worktrees/task-a ~/briefs/dropdown.md run1 opus high
```

`TITLE` is required. An untitled run is one you won't be able to identify in two
hours. `mini-run` also refuses to start on a dirty worktree, because a brief that
opens with `git reset --hard` will happily destroy whatever is sitting there.

## How it works

Two things make this possible.

**Claude Code writes a full session transcript to `~/.claude/projects` while the
agent runs**, regardless of what `--output-format` you passed. So even an agent
started by hand with plain text output has a live, parseable record of every
message and tool call. agentview reads those. That's why it can show narration
for agents it didn't launch, including ones started by a different session.

**Agents launched by `mini-run` get a named pipe on stdin** via `--input-format
stream-json`. Writing a JSON message into that pipe delivers it to the running
agent. Pressing `m` does exactly that.

Two gotchas I hit building it, in case you go the same route. Opening a FIFO
read only blocks until a writer exists, so open it `O_RDWR` first or you
deadlock. And `claude --input-format stream-json` does not exit on stdin EOF, so
if you hold a pipe open you have to shut the agent down yourself or it sits
resident forever.

## Talking to agents

Two modes, and the difference matters.

**Live.** Agents launched by `mini-run` have the stdin pipe, so `m` sends a real
message to the running process. It arrives at the agent's next turn boundary. You
can add a constraint or redirect what it does next. You cannot interrupt work
already in flight.

**Forked.** For anything else, finished runs or agents launched some other way,
`m` resumes a fork of the agent's session and asks there. The answer is accurate
about its work, but nothing you say reaches the original process.

The dashboard tells you which mode you're in before you type.

## What it shows

* the agent's own narration, straight from the transcript, no extra model call
* current phase and the file or command it's on
* a stall warning after 10 minutes of silence
* `N files UNCOMMITTED` for finished runs, which is the state that actually
  costs you something
* `worktree removed` when it can't verify what was collected, which is not the
  same as clean
* duration bands calibrated from your own past runs, shown only once a run is
  old enough for the comparison to mean anything

## Why not just tail the logs

Because there's nothing to tail. Text output buffers until the run ends. You can
switch to `--output-format stream-json` and tail that, which is roughly where
this started, but you still end up wanting one screen instead of five tmux panes,
and you still can't answer "which of these finished with work I never collected",
which turns out to be the question that costs real time.

## Safety

agentview never kills, commits, or pushes. It writes its own metadata under
`~/.agentrun` and messages you deliberately send, nothing else.

`mini-run` launches agents with `--permission-mode bypassPermissions`, because a
headless agent has no way to answer a permission prompt. That is fine on a
machine you own and a worktree you're happy to lose. Don't point it at anything
you care about without a clean git state.

## Configuration

| variable | |
|---|---|
| `AGENT_HOST` | ssh host the agents run on, required |
| `AGENT_IGNORE` | pattern excluded from the dirty worktree check |
| `AGENTRUN_STALL` | seconds of silence before a run is flagged, default 600 |
| `AGENTRUN_GRACE` | seconds an idle agent stays reachable, default 120 |

## Known limits

* one remote host, local agents aren't shown
* messages queue to a turn boundary, there's no interrupt
* runs not launched by `mini-run` get adopted automatically but have no input
  channel and can't be given one afterwards
* the duration estimate is a band from past runs, not a real projection. Agents
  aren't linear and I'd rather show a wide honest range than a fake percentage.

## Status

This is a personal tool that got useful enough to share. It does what I need and
I use it daily. Issues and PRs welcome, but it's shaped around one workflow:
agents in git worktrees on a remote box, one per task.

MIT.
