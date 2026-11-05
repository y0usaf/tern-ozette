#!/bin/bash
ENV=$1 CUE=$2
b() { ( . "$ENV"; c "$@" ) >/dev/null 2>&1; }
cue() { echo "$1:$RANDOM" > "$CUE"; }
z() { b wait "$(awk "BEGIN{print int($1*1000)}")"; }
NAME=$3
b record start "$NAME" fps 30
z 1.2
b move 100 198; z 0.6
b move 100 258; z 0.6
b click 100 198; z 1.1
b click 100 138; z 1.1
b click ".sf-editor"; z 0.9
cue type; z 2.0
cue sent; z 1.2
cue stream; z 5.2
cue ask; z 1.6
b hover "[data-role='omp.ask.options'] .sf-item:nth-child(1)"; z 0.6
b hover "[data-role='omp.ask.options'] .sf-item:nth-child(3)"; z 0.6
cue down; z 0.8
cue up; z 0.8
b hover "[data-role='omp.editor.ask'] .sf-act:nth-child(3)"; z 0.6
b hover "[data-role='omp.editor.ask'] .sf-act:last-child"; z 0.7
cue submit; z 1.3
b split right; z 0.8
b focus left; z 0.8
b palette split; z 1.0
b hover ".ck-list > .ck-item:nth-child(3)"; z 0.6
b key Down; z 0.6
b key Escape; z 0.8
b move 500 400; b wheel 0 -900; z 1.3
b hover ".tv-back"; z 0.7
b click ".tv-back"; z 1.2
b focus right; z 1.1
b focus left; z 1.1
b focus right; z 1.3
b record stop
b close
