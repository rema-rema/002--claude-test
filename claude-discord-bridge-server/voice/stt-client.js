/**
 * STT Client - whisper-server HTTP API クライアント
 *
 * whisper-serverに音声ファイルを送信してテキストに変換
 * モデルが常駐しているため、毎回の読み込み時間が不要で高速
 */

const fs = require('fs');
const path = require('path');
const { Blob } = require('buffer');

// whisper-server設定
const WHISPER_SERVER_URL = process.env.WHISPER_SERVER_URL || 'http://127.0.0.1:8080';
const INFERENCE_ENDPOINT = `${WHISPER_SERVER_URL}/inference`;

// 旧CLI設定（フォールバック用）
const WHISPER_CLI = path.join(__dirname, '../whisper.cpp/build/bin/whisper-cli');
const MODEL_PATH = path.join(__dirname, '../whisper.cpp/models/ggml-small.bin');

// サーバー状態
let serverAvailable = true;

/**
 * 音声ファイルをテキストに変換（HTTP API経由）
 * @param {string} audioPath - WAVファイルのパス
 * @param {string} language - 言語コード（デフォルト: ja）
 * @returns {Promise<string>} 認識されたテキスト
 */
async function speechToText(audioPath, language = 'ja') {
    // ファイル存在確認
    if (!fs.existsSync(audioPath)) {
        throw new Error(`Audio file not found: ${audioPath}`);
    }

    const startTime = Date.now();

    try {
        // Native FormDataを使用（Node.js 18+）
        const form = new FormData();
        const fileBuffer = fs.readFileSync(audioPath);
        const blob = new Blob([fileBuffer], { type: 'audio/wav' });
        form.append('file', blob, 'audio.wav');
        form.append('response_format', 'json');
        form.append('language', language);

        // HTTP POSTリクエスト
        const response = await fetch(INFERENCE_ENDPOINT, {
            method: 'POST',
            body: form
        });

        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        const elapsed = Date.now() - startTime;

        // テキスト抽出（改行を空白に変換）
        const text = (result.text || '')
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join(' ')
            .trim();

        console.log(`[STT] whisper-server response: ${elapsed}ms`);
        serverAvailable = true;
        return text;

    } catch (error) {
        console.error(`[STT] whisper-server error: ${error.message}`);
        serverAvailable = false;

        // フォールバック: CLIを使用
        console.log('[STT] Falling back to whisper-cli...');
        return speechToTextCLI(audioPath, language);
    }
}

/**
 * フォールバック: whisper-cli経由で音声認識
 */
async function speechToTextCLI(audioPath, language = 'ja') {
    const { spawn } = require('child_process');

    return new Promise((resolve, reject) => {
        const args = [
            '-m', MODEL_PATH,
            '-f', audioPath,
            '-l', language,
            '-t', '4',
            '-nt',
            '-np',
        ];

        const proc = spawn(WHISPER_CLI, args, {
            stdio: ['ignore', 'pipe', 'pipe']
        });

        let stdout = '';

        proc.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        proc.on('close', (code) => {
            if (code !== 0 && code !== null) {
                reject(new Error(`Whisper CLI exited with code ${code}`));
                return;
            }

            const text = stdout
                .split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0)
                .join(' ')
                .trim();

            resolve(text);
        });

        proc.on('error', (error) => {
            reject(new Error(`Whisper CLI error: ${error.message}`));
        });

        // タイムアウト
        setTimeout(() => {
            proc.kill('SIGKILL');
            reject(new Error('Whisper CLI timeout'));
        }, 30000);
    });
}

/**
 * Bufferから直接音声認識（一時ファイル経由）
 * @param {Buffer} audioBuffer - WAV音声データ
 * @param {string} language - 言語コード
 * @returns {Promise<string>} 認識されたテキスト
 */
async function speechToTextFromBuffer(audioBuffer, language = 'ja') {
    const tempPath = `/tmp/stt-${Date.now()}.wav`;

    try {
        fs.writeFileSync(tempPath, audioBuffer);
        const text = await speechToText(tempPath, language);
        return text;
    } finally {
        // 一時ファイル削除
        if (fs.existsSync(tempPath)) {
            fs.unlinkSync(tempPath);
        }
    }
}

/**
 * whisper-serverのヘルスチェック
 * @returns {Promise<boolean>}
 */
async function healthCheck() {
    try {
        const response = await fetch(WHISPER_SERVER_URL, {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
        });
        serverAvailable = response.ok;
        return serverAvailable;
    } catch {
        serverAvailable = false;
        // CLIが存在するかチェック
        return fs.existsSync(WHISPER_CLI) && fs.existsSync(MODEL_PATH);
    }
}

/**
 * サーバーが利用可能かどうか
 */
function isServerAvailable() {
    return serverAvailable;
}

/**
 * 全アクティブプロセスを強制終了（互換性のため残す）
 */
function killAllProcesses() {
    console.log('[STT] killAllProcesses called (no-op for server mode)');
}

/**
 * アクティブプロセス数を取得（互換性のため残す）
 */
function getActiveCount() {
    return 0;
}

module.exports = {
    speechToText,
    speechToTextFromBuffer,
    healthCheck,
    killAllProcesses,
    getActiveCount,
    isServerAvailable,
    WHISPER_CLI,
    MODEL_PATH,
    WHISPER_SERVER_URL
};

// CLIテスト用
if (require.main === module) {
    const audioPath = process.argv[2] || '/tmp/test-voice.wav';

    console.log(`Testing STT with: ${audioPath}`);
    console.log(`Server URL: ${WHISPER_SERVER_URL}`);

    speechToText(audioPath)
        .then(text => {
            console.log(`Result: "${text}"`);
        })
        .catch(err => {
            console.error('Error:', err.message);
            process.exit(1);
        });
}
