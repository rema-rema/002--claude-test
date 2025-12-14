#!/usr/bin/env node
/**
 * Streaming Claude + TTS テスト
 *
 * 合成音声でテキストを生成し、ストリーミングClaudeに送信、
 * 応答を文ごとにTTSで再生する
 */

require('dotenv').config();

const { streamClaude, clearHistory } = require('./claude-streaming');
const { textToSpeech, healthCheck } = require('./tts-client');
const { Readable } = require('stream');
const { createAudioPlayer, createAudioResource, StreamType, AudioPlayerStatus } = require('@discordjs/voice');

// テスト用メッセージ
const TEST_MESSAGES = [
    "今日の天気はどうですか？",
    "おすすめのプログラミング言語を教えてください。",
    "短い詩を作ってください。"
];

// TTS再生（コンソール出力のみ、音声なし）
async function testTTS(text) {
    console.log(`[TTS] Generating: "${text}"`);
    const startTime = Date.now();

    try {
        const audioBuffer = await textToSpeech(text);
        const elapsed = Date.now() - startTime;
        console.log(`[TTS] Generated ${audioBuffer.length} bytes in ${elapsed}ms`);
        return true;
    } catch (error) {
        console.error(`[TTS] Error: ${error.message}`);
        return false;
    }
}

// ストリーミングClaudeテスト
async function testStreamingClaude(message) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`[Test] User: "${message}"`);
    console.log('='.repeat(60));

    const startTime = Date.now();
    let firstSentenceTime = null;
    let sentenceCount = 0;

    return new Promise((resolve, reject) => {
        streamClaude(
            message,
            // 文完成コールバック
            async (sentence) => {
                const now = Date.now();
                if (firstSentenceTime === null) {
                    firstSentenceTime = now;
                    console.log(`[Timing] First sentence at ${firstSentenceTime - startTime}ms`);
                }
                sentenceCount++;
                console.log(`[Sentence ${sentenceCount}] "${sentence}"`);

                // TTSテスト
                await testTTS(sentence);
            },
            // 完了コールバック
            (fullResponse) => {
                const totalTime = Date.now() - startTime;
                const ttfs = firstSentenceTime ? firstSentenceTime - startTime : 0;

                console.log(`\n[Result]`);
                console.log(`  Total time: ${totalTime}ms`);
                console.log(`  Time to first sentence: ${ttfs}ms`);
                console.log(`  Sentence count: ${sentenceCount}`);
                console.log(`  Full response: "${fullResponse}"`);

                resolve({
                    totalTime,
                    ttfs,
                    sentenceCount,
                    fullResponse
                });
            },
            // エラーコールバック
            (error) => {
                console.error(`[Error] ${error.message}`);
                reject(error);
            }
        );
    });
}

// メイン
async function main() {
    console.log('='.repeat(60));
    console.log('Streaming Claude + TTS Test');
    console.log('='.repeat(60));

    // 設定確認
    console.log(`\n[Config]`);
    console.log(`  ANTHROPIC_API_KEY: ${process.env.ANTHROPIC_API_KEY ? 'Set' : 'NOT SET'}`);
    console.log(`  CLAUDE_MODEL: ${process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514'}`);

    if (!process.env.ANTHROPIC_API_KEY) {
        console.error('\n[Error] ANTHROPIC_API_KEY is not set');
        process.exit(1);
    }

    // VOICEVOXヘルスチェック
    console.log(`\n[VOICEVOX] Checking...`);
    const voicevoxOk = await healthCheck();
    if (!voicevoxOk) {
        console.error('[VOICEVOX] Server not available');
        process.exit(1);
    }
    console.log('[VOICEVOX] OK');

    // 履歴クリア
    clearHistory();

    // テスト実行
    const results = [];

    for (const message of TEST_MESSAGES) {
        try {
            const result = await testStreamingClaude(message);
            results.push({ message, ...result, success: true });
        } catch (error) {
            results.push({ message, error: error.message, success: false });
        }

        // 少し待機
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    // サマリー
    console.log(`\n${'='.repeat(60)}`);
    console.log('Summary');
    console.log('='.repeat(60));

    for (const result of results) {
        if (result.success) {
            console.log(`\n[${result.message}]`);
            console.log(`  TTFS: ${result.ttfs}ms (目標: 2000ms以下)`);
            console.log(`  Total: ${result.totalTime}ms`);
            console.log(`  Status: ${result.ttfs <= 2000 ? '✅ PASS' : '❌ SLOW'}`);
        } else {
            console.log(`\n[${result.message}]`);
            console.log(`  Error: ${result.error}`);
            console.log(`  Status: ❌ FAIL`);
        }
    }

    // 平均TTFS
    const successResults = results.filter(r => r.success);
    if (successResults.length > 0) {
        const avgTTFS = successResults.reduce((sum, r) => sum + r.ttfs, 0) / successResults.length;
        console.log(`\n[Average TTFS]: ${Math.round(avgTTFS)}ms`);
    }
}

main().catch(console.error);
