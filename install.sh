#!/bin/sh
# Install agentview: client scripts locally, host scripts on $AGENT_HOST.
set -e
: "${AGENT_HOST:?set AGENT_HOST to the ssh host your agents run on, e.g. export AGENT_HOST=myserver}"
BIN="${BIN:-$HOME/.local/bin}"
HERE=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$BIN"
install -m 755 "$HERE/bin/mini" "$HERE/bin/mini-run" "$BIN/"
echo "installed mini, mini-run -> $BIN"

ssh "$AGENT_HOST" 'mkdir -p ~/bin ~/.agentrun'
scp -q "$HERE"/host/agentrun-* "$AGENT_HOST:~/bin/"
ssh "$AGENT_HOST" 'chmod +x ~/bin/agentrun-*'
echo "installed agentrun-* -> $AGENT_HOST:~/bin"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo; echo "note: $BIN is not on your PATH — add it to your shell profile." ;;
esac
echo
echo "done. try:  mini"
