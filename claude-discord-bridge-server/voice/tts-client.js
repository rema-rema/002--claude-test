/**
 * TTS Client - VOICEVOX音声合成クライアント
 *
 * テキストを音声に変換し、WAVファイルとして返す
 */

const config = require('./config');

/**
 * テキストを音声に変換
 * @param {string} text - 変換するテキスト
 * @param {number} speakerId - VOICEVOXの話者ID（デフォルト: 1 = ずんだもん）
 * @returns {Promise<Buffer>} WAV音声データ
 */
async function textToSpeech(text, speakerId = config.VOICEVOX_SPEAKER_ID) {
    const host = config.VOICEVOX_HOST;
    const startTime = Date.now();

    // Step 1: audio_queryを取得
    const queryStart = Date.now();
    const queryResponse = await fetch(
        `${host}/audio_query?text=${encodeURIComponent(text)}&speaker=${speakerId}`,
        { method: 'POST' }
    );

    if (!queryResponse.ok) {
        throw new Error(`audio_query failed: ${queryResponse.status}`);
    }

    const query = await queryResponse.json();
    const queryTime = Date.now() - queryStart;

    // 話速（1.0がデフォルト、1.35で35%速い）
    query.speedScale = 1.35;

    // Step 2: 音声合成
    const synthesisStart = Date.now();
    const synthesisResponse = await fetch(
        `${host}/synthesis?speaker=${speakerId}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query)
        }
    );

    if (!synthesisResponse.ok) {
        throw new Error(`synthesis failed: ${synthesisResponse.status}`);
    }

    const audioBuffer = await synthesisResponse.arrayBuffer();
    const synthesisTime = Date.now() - synthesisStart;
    const totalTime = Date.now() - startTime;

    console.log(`[TTS] 合成完了: query=${queryTime}ms, synthesis=${synthesisTime}ms, total=${totalTime}ms (${text.substring(0, 20)}...)`);

    return Buffer.from(audioBuffer);
}

/**
 * 利用可能な話者一覧を取得
 * @returns {Promise<Array>} 話者情報の配列
 */
async function getSpeakers() {
    const response = await fetch(`${config.VOICEVOX_HOST}/speakers`);
    if (!response.ok) {
        throw new Error(`Failed to get speakers: ${response.status}`);
    }
    return response.json();
}

/**
 * VOICEVOXサーバーのヘルスチェック
 * @returns {Promise<boolean>} サーバーが稼働中かどうか
 */
async function healthCheck() {
    try {
        const response = await fetch(`${config.VOICEVOX_HOST}/version`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

module.exports = {
    textToSpeech,
    getSpeakers,
    healthCheck
};

// CLIテスト用
if (require.main === module) {
    const fs = require('fs');
    const text = process.argv[2] || 'こんにちは、音声テストです';

    console.log(`Testing TTS with: "${text}"`);

    textToSpeech(text)
        .then(buffer => {
            const outputPath = '/tmp/test-voice.wav';
            fs.writeFileSync(outputPath, buffer);
            console.log(`Audio saved to: ${outputPath} (${buffer.length} bytes)`);
        })
        .catch(err => {
            console.error('Error:', err.message);
            process.exit(1);
        });
}
