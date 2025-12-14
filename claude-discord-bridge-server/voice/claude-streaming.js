/**
 * Claude API Streaming Client
 *
 * Anthropic Claude APIをストリーミングモードで呼び出し、
 * 文が完成するたびにコールバックを呼び出す
 */

const config = require('./config');

// 会話履歴（コンテキスト維持用）
let conversationHistory = [];
const MAX_HISTORY_LENGTH = 10;  // 最大履歴数

// システムプロンプト
const SYSTEM_PROMPT = `あなたは音声アシスタントです。
ユーザーの質問に短く簡潔に答えてください。
長い説明は避け、要点だけを伝えてください。
一度に1〜3文程度で回答してください。`;

/**
 * Claude APIをストリーミングで呼び出す
 * @param {string} userMessage - ユーザーのメッセージ
 * @param {Function} onSentence - 文が完成したときのコールバック (sentence: string) => void
 * @param {Function} onComplete - 全体完了時のコールバック (fullResponse: string) => void
 * @param {Function} onError - エラー時のコールバック (error: Error) => void
 */
async function streamClaude(userMessage, onSentence, onComplete, onError) {
    if (!config.ANTHROPIC_API_KEY) {
        onError(new Error('ANTHROPIC_API_KEY is not set'));
        return;
    }

    // 履歴にユーザーメッセージを追加
    conversationHistory.push({
        role: 'user',
        content: userMessage
    });

    // 履歴が長すぎたら古いものを削除
    while (conversationHistory.length > MAX_HISTORY_LENGTH) {
        conversationHistory.shift();
    }

    try {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': config.ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: config.CLAUDE_MODEL,
                max_tokens: config.CLAUDE_MAX_TOKENS,
                system: SYSTEM_PROMPT,
                messages: conversationHistory,
                stream: true
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Claude API error: ${response.status} - ${errorText}`);
        }

        // ストリーミングレスポンスを処理
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let fullResponse = '';
        let currentSentence = '';
        const sentenceEnders = ['。', '！', '？', '!', '?', '\n'];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;

                const data = line.slice(6);
                if (data === '[DONE]') continue;

                try {
                    const parsed = JSON.parse(data);

                    // content_block_delta イベントからテキストを抽出
                    if (parsed.type === 'content_block_delta' &&
                        parsed.delta &&
                        parsed.delta.type === 'text_delta') {

                        const text = parsed.delta.text;
                        fullResponse += text;
                        currentSentence += text;

                        // 文末記号があれば文を送信
                        for (const ender of sentenceEnders) {
                            if (currentSentence.includes(ender)) {
                                const parts = currentSentence.split(new RegExp(`(${ender.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`));

                                for (let i = 0; i < parts.length - 1; i += 2) {
                                    const sentence = parts[i] + (parts[i + 1] || '');
                                    if (sentence.trim()) {
                                        console.log(`[Claude Stream] Sentence: "${sentence}"`);
                                        onSentence(sentence.trim());
                                    }
                                }

                                // 最後の部分を次の文として保持
                                currentSentence = parts[parts.length - 1] || '';
                                break;
                            }
                        }
                    }
                } catch (e) {
                    // JSONパースエラーは無視（不完全なチャンクの可能性）
                }
            }
        }

        // 残りの文があれば送信
        if (currentSentence.trim()) {
            console.log(`[Claude Stream] Final sentence: "${currentSentence}"`);
            onSentence(currentSentence.trim());
        }

        // 履歴にアシスタントの応答を追加
        conversationHistory.push({
            role: 'assistant',
            content: fullResponse
        });

        console.log(`[Claude Stream] Complete: "${fullResponse}"`);
        onComplete(fullResponse);

    } catch (error) {
        console.error('[Claude Stream] Error:', error.message);
        onError(error);
    }
}

/**
 * 会話履歴をクリア
 */
function clearHistory() {
    conversationHistory = [];
    console.log('[Claude] Conversation history cleared');
}

/**
 * 現在の会話履歴を取得
 */
function getHistory() {
    return [...conversationHistory];
}

module.exports = {
    streamClaude,
    clearHistory,
    getHistory
};
