# Regenerate with:  vhs demo/demo.tape
# Records a real session against a sandbox registry, never live work.
Output demo/agentview.gif

Set Shell "bash"
Set FontSize 14
Set Width 1180
Set Height 760
Set Padding 22
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set Framerate 12

Hide
Type "export AGENT_HOST=macmini AGENTRUN_DIR=/tmp/demoreg AGENTRUN_NO_ADOPT=1"
Enter
Type "export PATH=$HOME/Documents/agentview/bin:$PATH; clear"
Enter
Sleep 1s
Show

Type "mini"
Sleep 400ms
Enter
Sleep 4s

# move the selection, the highlight follows
Down
Sleep 2s
Up
Sleep 1500ms

# open a run
Enter
Sleep 5s

# the feed is a digest; f shows the full text
Type "f"
Sleep 3s
Type "f"
Sleep 2s

# message the running agent on its live channel
Type "m"
Sleep 1s
Type "when you finish, leave the tests in place"
Sleep 500ms
Enter
Sleep 4s

Escape
Sleep 1500ms
Left
Sleep 2500ms
Type "q"
Sleep 1s
