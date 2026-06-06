#!/bin/bash
# Claude Code status bar — mirrors extensions/pi/jacazul-line.ts layout
#
# Lines:
#   1. mode + project
#   2. focus plan + task uuid + description
#   3. git worktree/repo/path + branch
#   4. runtime (CLAUDE_MODEL if available, else omitted)

# --- ANSI helpers ---
_c() { printf '\033[38;2;%s;%s;%sm%s\033[0m' "$1" "$2" "$3" "$4"; }
lime()      { _c 152 195 121 "$1"; }  # #98C379
lightgray() { _c 178 178 178 "$1"; }  # #B2B2B2
gray()      { _c 140 140 140 "$1"; }  # #8C8C8C
sep()       { gray " | "; }

NF_GIT=$'\xee\x82\xa0'  # U+E0A0 nerd font git branch icon

# --- Line 1: Mode + Project ---
MODE="${JACAZUL_MODE:-COUNSELOR}"
PROJ="${PROJECT_ID:-$(basename "$PWD")}"
LINE1="$(lime "🐊 $MODE")$(sep)$(lightgray "$PROJ")"

# --- Line 2: Focus ---
_focus_line() {
    local label focus_file focus_plan focus_uuid short desc parts
    local taskdir="${HOME}/.jacazul-ai/.task/${PROJECT_ID}"

    if [ -n "$JACAZUL_SESSION_ID" ] && [ -f "${taskdir}/focus-${JACAZUL_SESSION_ID}.json" ]; then
        focus_file="${taskdir}/focus-${JACAZUL_SESSION_ID}.json"
        label="🎯 focus (independent)"
    else
        focus_file="${taskdir}/focus.json"
        label="🎯 focus"
    fi

    if [ -z "$PROJECT_ID" ] || [ ! -f "$focus_file" ]; then
        printf '%s%s%s' "$(gray "$label")" "$(sep)" "$(lightgray "none")"
        return
    fi

    focus_plan=$(jq -r '.focused_plan // empty' "$focus_file" 2>/dev/null)
    focus_uuid=$(jq -r '.focused_task_uuid // empty' "$focus_file" 2>/dev/null)

    if [ -z "$focus_plan" ] && [ -z "$focus_uuid" ]; then
        printf '%s%s%s' "$(gray "$label")" "$(sep)" "$(lightgray "none")"
        return
    fi

    parts="$(lime "$label")"
    [ -n "$focus_plan" ] && parts="${parts}$(sep)$(lightgray "$focus_plan")"

    if [ -n "$focus_uuid" ]; then
        short="${focus_uuid:0:8}"
        desc=$(taskp "$focus_uuid" export 2>/dev/null | jq -r '.[0].description // empty' 2>/dev/null)
        if [ -n "$desc" ]; then
            parts="${parts}$(sep)$(lightgray "${short} ${desc}")"
        else
            parts="${parts}$(sep)$(lightgray "${short}")"
        fi
    fi

    printf '%s' "$parts"
}
LINE2="$(_focus_line)"

# --- Line 3: Git ---
_git_line() {
    local dir="$PWD" branch parts common_short wt_label root_short

    while [ "$dir" != "/" ]; do
        if [ -f "${dir}/.git" ]; then
            local raw_gitdir
            raw_gitdir=$(sed 's/^gitdir: //' "${dir}/.git")
            local gitdir
            # raw_gitdir may be absolute or relative to dir
            if [[ "$raw_gitdir" == /* ]]; then
                gitdir=$(readlink -f "$raw_gitdir" 2>/dev/null || echo "$raw_gitdir")
            else
                gitdir=$(readlink -f "${dir}/${raw_gitdir}" 2>/dev/null || echo "${dir}/${raw_gitdir}")
            fi
            local commondir_file="${gitdir}/commondir"
            local common_git_dir="$gitdir"
            if [ -f "$commondir_file" ]; then
                common_git_dir=$(readlink -f "${gitdir}/$(cat "$commondir_file")" 2>/dev/null || echo "$gitdir")
            fi
            common_short="${common_git_dir/#$HOME/\~}"
            branch=$(git -C "$dir" branch --show-current 2>/dev/null)
            wt_label="$(basename "$dir")"
            [ -n "$branch" ] && wt_label="${wt_label}(${branch})"
            printf '%s%s%s%s%s' \
                "$(lime "$NF_GIT worktree")" "$(sep)" \
                "$(lightgray "$common_short")" "$(sep)" \
                "$(lightgray "$wt_label")"
            return
        elif [ -d "${dir}/.git" ]; then
            root_short="${dir/#$HOME/\~}"
            parts="$(lime "$NF_GIT repo")$(sep)$(lightgray "$root_short")"
            branch=$(git -C "$dir" branch --show-current 2>/dev/null)
            [ -n "$branch" ] && parts="${parts}$(sep)$(lightgray "branch $branch")"
            printf '%s' "$parts"
            return
        fi
        dir="$(dirname "$dir")"
    done

    printf '%s%s%s' "$(lime "📁 path")" "$(sep)" "$(lightgray "${PWD/#$HOME/\~}")"
}
LINE3="$(_git_line)"

# --- Line 4: Runtime ---
_get_model() {
    [ -n "$CLAUDE_MODEL" ] && { echo "$CLAUDE_MODEL"; return; }
    local session_id="${CLAUDE_CODE_SESSION_ID}"
    [ -n "$session_id" ] || return
    local proj_slug
    proj_slug=$(echo "$PWD" | sed 's|/|-|g')
    local jsonl="${HOME}/.claude/projects/${proj_slug}/${session_id}.jsonl"
    [ -f "$jsonl" ] || return
    grep '"model"' "$jsonl" | tail -1 | jq -r '.message.model // .model // empty' 2>/dev/null
}
_runtime_line() {
    local model
    model="$(_get_model)"
    [ -n "$model" ] || return
    printf '%s%s%s' "$(lime "🤖")" "$(sep)" "$(lightgray "$model")"
}
LINE4="$(_runtime_line)"

# --- Output ---
printf '%s\n' "$LINE1" "$LINE2" "$LINE3"
[ -n "$LINE4" ] && printf '%s\n' "$LINE4"
exit 0
