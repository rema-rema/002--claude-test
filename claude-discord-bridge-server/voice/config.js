/**
 * Voice Bridge 設定ファイル
 *
 * 環境変数 VOICE_BOT_INSTANCE でインスタンス切り替え
 * - 未設定 or "A": デフォルト（Bot A）
 * - "B": Voice Bot B
 */

const instance = process.env.VOICE_BOT_INSTANCE || "A";

// インスタンス別設定（すべて環境変数から取得）
const instanceConfig = {
    A: {
        DISCORD_TOKEN: process.env.CC_DISCORD_TOKEN,
        VOICE_CHANNEL_ID: process.env.VOICE_CHANNEL_ID,
        TEXT_CHANNEL_ID: process.env.CC_DISCORD_CHANNEL_ID_002,
        VOICE_SERVER_PORT: 3001,
        SESSION_NUM: 1,
        VOICEVOX_SPEAKER_ID: 3,  // ずんだもん ノーマル
    },
    B: {
        DISCORD_TOKEN: process.env.VOICE_BOT_B_TOKEN,
        VOICE_CHANNEL_ID: process.env.VOICE_BOT_B_CHANNEL_ID,
        TEXT_CHANNEL_ID: process.env.CC_DISCORD_CHANNEL_ID_002_B,
        VOICE_SERVER_PORT: 3002,
        SESSION_NUM: 2,
        VOICEVOX_SPEAKER_ID: 8,  // 春日部つむぎ
    },
    C: {
        DISCORD_TOKEN: process.env.VOICE_BOT_C_TOKEN,
        VOICE_CHANNEL_ID: process.env.VOICE_BOT_C_CHANNEL_ID,
        TEXT_CHANNEL_ID: process.env.CC_DISCORD_CHANNEL_ID_002_C,
        VOICE_SERVER_PORT: 3003,
        SESSION_NUM: 3,
        VOICEVOX_SPEAKER_ID: 13,  // 青山龍星 (男性)
    },
    D: {
        DISCORD_TOKEN: process.env.VOICE_BOT_D_TOKEN,
        VOICE_CHANNEL_ID: process.env.VOICE_BOT_D_CHANNEL_ID,
        TEXT_CHANNEL_ID: process.env.CC_DISCORD_CHANNEL_ID_002_D,
        VOICE_SERVER_PORT: 3004,
        SESSION_NUM: 4,
        VOICEVOX_SPEAKER_ID: 14,  // 冥鳴ひまり
    }
};

const current = instanceConfig[instance] || instanceConfig.A;

module.exports = {
    // インスタンス識別
    INSTANCE: instance,
    SESSION_NUM: current.SESSION_NUM,

    // Discord設定
    DISCORD_TOKEN: current.DISCORD_TOKEN,
    VOICE_CHANNEL_ID: current.VOICE_CHANNEL_ID,
    TEXT_CHANNEL_ID: current.TEXT_CHANNEL_ID,

    // サーバー設定
    VOICE_SERVER_PORT: current.VOICE_SERVER_PORT,
    FLASK_SERVER_URL: "http://localhost:5001",

    // TTS設定 (VOICEVOX) - インスタンス別
    VOICEVOX_HOST: process.env.VOICEVOX_HOST || "http://localhost:50021",
    VOICEVOX_SPEAKER_ID: current.VOICEVOX_SPEAKER_ID || 3,

    // STT設定 (Whisper) - 共有
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,

    // Claude API設定（ストリーミング応答用）- 共有
    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
    CLAUDE_MODEL: process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514",
    CLAUDE_MAX_TOKENS: parseInt(process.env.CLAUDE_MAX_TOKENS) || 1024,

    // 音声処理設定
    AUDIO_SAMPLE_RATE: 48000,
    AUDIO_CHANNELS: 2
};
