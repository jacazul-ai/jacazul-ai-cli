#!/bin/bash
# Claude Code status bar — mirrors extensions/pi/jacazul-line.ts layout
#
# Lines:
#   1. mode + project
#   2. focus plan + task uuid + description
#   3. git worktree/repo/path + branch
#   4. runtime (model, context usage, session cost — each omitted if unavailable)
#
# Claude Code pipes a JSON payload on stdin for every render; see
# https://code.claude.com/docs/en/statusline.md for the schema.

INPUT_JSON="$(cat)"

# --- ANSI helpers ---
_c() { printf '\033[38;2;%s;%s;%sm%s\033[0m' "$1" "$2" "$3" "$4"; }
lime()      { _c 152 195 121 "$1"; }  # #98C379
lightgray() { _c 178 178 178 "$1"; }  # #B2B2B2
gray()      { _c 140 140 140 "$1"; }  # #8C8C8C
amber()     { _c 229 192  21 "$1"; }  # #E5C015
red()       { _c 224 108 117 "$1"; }  # #E06C75
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
    local from_payload
    from_payload=$(printf '%s' "$INPUT_JSON" | jq -r '.model.display_name // .model.id // empty' 2>/dev/null)
    [ -n "$from_payload" ] && { echo "$from_payload"; return; }
    [ -n "$CLAUDE_MODEL" ] && { echo "$CLAUDE_MODEL"; return; }
    local session_id="${CLAUDE_CODE_SESSION_ID}"
    [ -n "$session_id" ] || return
    local proj_slug
    proj_slug=$(echo "$PWD" | sed 's|/|-|g')
    local jsonl="${HOME}/.claude/projects/${proj_slug}/${session_id}.jsonl"
    [ -f "$jsonl" ] || return
    grep '"model"' "$jsonl" | tail -1 | jq -r '.message.model // .model // empty' 2>/dev/null
}
_format_tokens() {
    local n="$1"
    if [ "$n" -lt 1000 ]; then
        printf '%d' "$n"
    elif [ "$n" -lt 10000 ]; then
        awk -v n="$n" 'BEGIN { printf "%.1fk", n / 1000 }'
    elif [ "$n" -lt 1000000 ]; then
        awk -v n="$n" 'BEGIN { printf "%dk", int(n / 1000 + 0.5) }'
    elif [ "$n" -lt 10000000 ]; then
        awk -v n="$n" 'BEGIN { printf "%.1fM", n / 1000000 }'
    else
        awk -v n="$n" 'BEGIN { printf "%dM", int(n / 1000000 + 0.5) }'
    fi
}

_ctx_part() {
    local pct pct_int color label
    pct=$(printf '%s' "$INPUT_JSON" | jq -r '.context_window.remaining_percentage // empty' 2>/dev/null)
    [ -n "$pct" ] || return
    pct_int=$(printf '%.0f' "$pct")
    if [ "$pct_int" -le 20 ]; then
        color=red
    elif [ "$pct_int" -le 50 ]; then
        color=amber
    else
        color=lime
    fi
    label="ctx ${pct_int}%"

    local input_tok output_tok window_size used
    input_tok=$(printf '%s' "$INPUT_JSON" | jq -r '.context_window.total_input_tokens // 0' 2>/dev/null)
    output_tok=$(printf '%s' "$INPUT_JSON" | jq -r '.context_window.total_output_tokens // 0' 2>/dev/null)
    window_size=$(printf '%s' "$INPUT_JSON" | jq -r '.context_window.context_window_size // empty' 2>/dev/null)
    if [ -n "$window_size" ] && [ "$window_size" -gt 0 ] 2>/dev/null; then
        used=$(( input_tok + output_tok ))
        label="${label} $(_format_tokens "$used")/$(_format_tokens "$window_size")"
    fi

    printf '%s' "$($color "$label")"
}

_cost_part() {
    local cost
    cost=$(printf '%s' "$INPUT_JSON" | jq -r '.cost.total_cost_usd // empty' 2>/dev/null)
    [ -n "$cost" ] || return
    printf '%s' "$(lightgray "$(printf '$%.4f' "$cost")")"
}

_runtime_line() {
    local model parts=()
    model="$(_get_model)"
    [ -n "$model" ] && parts+=("$(lime "🤖")$(sep)$(lightgray "$model")")

    local ctx cost
    ctx="$(_ctx_part)"
    [ -n "$ctx" ] && parts+=("$ctx")
    cost="$(_cost_part)"
    [ -n "$cost" ] && parts+=("$cost")

    [ ${#parts[@]} -eq 0 ] && return

    local out="${parts[0]}" i
    for ((i = 1; i < ${#parts[@]}; i++)); do
        out="${out}$(sep)${parts[i]}"
    done
    printf '%s' "$out"
}
LINE4="$(_runtime_line)"

# --- Output ---
printf '%s\n' "$LINE1" "$LINE2" "$LINE3"
[ -n "$LINE4" ] && printf '%s\n' "$LINE4"
exit 0
