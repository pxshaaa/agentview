# agentview

Run your Claude Code agents on a remote machine, and watch all of them from one
terminal dashboard.

## Why

Two problems show up the moment you start using headless agents seriously.

**Your own machine becomes unusable.** Spawning several `claude -p` agents
locally means several Claude Code processes, several test runs and several dev
servers, all fighting for CPU with whatever you were actually trying to do. So I
moved them onto a separate box over ssh. A cheap VPS, a spare Mac mini, an old
desktop, anything works. My laptop stays free while the agents grind.

**Then you can't see them any more.** Once they run somewhere else, and
especially once four or five run at once, keeping track becomes the new problem.
One Claude Code window per agent does not scale, and headless runs are worse than
that: `--output-format text` buffers everything, so a 50 minute agent is a zero
byte log file until the moment it finishes. You cannot tell a working agent from
a hung one, you cannot see what it is doing, and when it is done you have to go
and dig out its output yourself.

The last one is what actually costs time. More than once I have had an agent
finish real work and leave it uncommitted in a worktree while I moved on to
something else, and only found it when I went looking for something unrelated.

agentview puts every agent on one screen, live, shows you which ones finished
with work you never collected, and lets you send them a message while they run.

![agentview](demo/agentview.gif)


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
| `m` | ask about this run, answers in seconds |
| `M` | resume the agent's own session, slow but authoritative |
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

Three modes, and the difference matters.

**Live.** Agents launched by `mini-run` have the stdin pipe, so `m` sends a real
message to the running process. It arrives at the agent's next turn boundary. You
can add a constraint or redirect what it does next. You cannot interrupt work
already in flight.

**Observed.** For anything else, `m` spawns a small read-only agent, hands it the
same evidence the dashboard shows (recent narration, tool calls, changed files)
and asks it there. It answers in seconds and never goes near the running agent.
It knows what the log shows, not what the agent privately intended.

**Resumed.** `M` resumes a fork of the agent's own session instead. More
authoritative and much slower: replaying a 1 MB transcript at opus/high took over
nine minutes to answer "hi". Reach for it when the observer says the log does not
say.

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

There is nothing to tail. Text output buffers until the run ends. You can switch
to `--output-format stream-json` and tail that, which is roughly where this
started, but five tmux panes of raw JSON is not an improvement, and it still
cannot tell you which runs finished with work you never collected.

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
| `AGENTRUN_DIR` | where run metadata lives, default `~/.agentrun` |
| `AGENTRUN_NO_ADOPT` | set to skip picking up agents you did not launch |

## Known limits

* one remote host, local agents aren't shown
* messages queue to a turn boundary, there's no interrupt
* runs not launched by `mini-run` get adopted automatically but have no input
  channel and can't be given one afterwards. Adoption scans every `claude -p` on
  the machine, so set `AGENTRUN_NO_ADOPT=1` if you want a view of only your own
  runs.
* the duration estimate is a band from past runs, not a real projection. Agents
  aren't linear and I'd rather show a wide honest range than a fake percentage.

## Status

This is a personal tool that got useful enough to share. It does what I need and
I use it daily. Issues and PRs welcome, but it's shaped around one workflow:
agents in git worktrees on a remote box, one per task.

MIT.

## Regenerating the demo

The GIF is a real recording, not a mockup. Three segments are captured at
different font sizes (which is where the zoom comes from), then composed with
window chrome, a caption per segment and crossfades between them.

```sh
brew install vhs gifsicle
./demo/build.sh
```

`demo/seg/*.tape` drive the actual dashboard and set `AGENTRUN_DIR` and
`AGENTRUN_NO_ADOPT` themselves, so the recording only ever sees a sandbox
registry. `demo/compose.py` does the framing. You need a couple of agents
running against that sandbox for there to be anything to film.
