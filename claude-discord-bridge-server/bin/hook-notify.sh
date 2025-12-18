#!/bin/bash
# Claude Code Hook: ツール実行をDiscordに通知

cd /home/rema/project/002--claude-test/claude-discord-bridge-server

# セッション番号を判定（PPIDからPTS経由）
get_session_number() {
    local pid=$$
    local found_pts=""
    while [ "$pid" != "1" ] && [ -n "$pid" ] && [ "$pid" != "0" ]; do
        if [ -L "/proc/$pid/fd/0" ]; then
            local pts=$(readlink /proc/$pid/fd/0 2>/dev/null)
            if [[ "$pts" == /dev/pts/* ]]; then
                found_pts="$pts"
            fi
        fi
        local new_pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
        if [ "$new_pid" = "$pid" ] || [ -z "$new_pid" ]; then
            break
        fi
        pid="$new_pid"
    done

    if [ -n "$found_pts" ]; then
        for session in $(tmux list-sessions -F '#S' 2>/dev/null); do
            local session_pts=$(tmux list-panes -t "$session" -F '#{pane_tty}' 2>/dev/null | head -1)
            if [ "$found_pts" = "$session_pts" ]; then
                if [[ "$session" =~ ^claude[-_]session[-_]([0-9]+)$ ]]; then
                    echo "${BASH_REMATCH[1]}"
                    return 0
                fi
            fi
        done
    fi
    echo "1"
}

SESSION_NUM=$(get_session_number)

# 標準入力からJSONを読み取り
INPUT=$(cat)

# ツール名と説明を抽出（pythonで処理）
PARSED=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tool = data.get('tool_name', 'unknown')
    inp = data.get('tool_input', {})
    desc = inp.get('description') or inp.get('command') or inp.get('file_path') or ''
    # ツール名を分かりやすい日本語に変換
    tool_ja = {
        'Bash': '作業中',
        'Read': '確認中',
        'Write': '作成中',
        'Edit': '編集中',
        'Grep': 'ローカル検索中',
        'Glob': 'ファイル探索中',
        'WebSearch': 'ネット検索中',
        'WebFetch': 'ページ取得中',
        'Task': '処理中',
        'TodoWrite': '整理中',
    }.get(tool, '考え中')
    print(f'{tool_ja}|{desc[:50]}')
except:
    print('処理中|')
")

TOOL=$(echo "$PARSED" | cut -d'|' -f1)
DESC=$(echo "$PARSED" | cut -d'|' -f2)

# 通知メッセージ作成（テキスト用: ツール名+説明）
MSG="🔧 ${TOOL}: ${DESC}"

# Discordに送信（テキスト表示）- セッション番号を使用
echo "$MSG" | python3 src/discord_post.py "$SESSION_NUM" 2>/dev/null

# TTS用: ツール名のみ日本語で読み上げ（descriptionは省略）
# セッションに応じたポートを選択（Session 1=3001, Session 2=3002）
TTS_PORT=$((3000 + SESSION_NUM))
curl -s -X POST http://localhost:$TTS_PORT/speak \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"${TOOL}\"}" > /dev/null 2>&1 &

exit 0
