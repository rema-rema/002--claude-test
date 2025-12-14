/**
 * Voice Bridge 設定ファイル
 */

module.exports = {
    // Discord設定
    DISCORD_TOKEN: process.env.CC_DISCORD_TOKEN,
    VOICE_CHANNEL_ID: "1448296280710451300",
    TEXT_CHANNEL_ID: "1424051227796307968",  // テキスト出力先（Plan B: このセッションのチャンネル）

    // サーバー設定
    VOICE_SERVER_PORT: 3001,
    FLASK_SERVER_URL: "http://localhost:5001",

    // TTS設定 (VOICEVOX)
    VOICEVOX_HOST: process.env.VOICEVOX_HOST || "http://localhost:50021",
    VOICEVOX_SPEAKER_ID: parseInt(process.env.VOICEVOX_SPEAKER_ID) || 23,  // 23 = WhiteCUL（ノーマル）

    // STT設定 (Whisper)
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,

    // Claude API設定（ストリーミング応答用）
    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
    CLAUDE_MODEL: process.env.CLAUDE_MODEL || "claude-sonnet-4-20250514",  // 速度重視でSonnet
    CLAUDE_MAX_TOKENS: parseInt(process.env.CLAUDE_MAX_TOKENS) || 1024,

    // 音声処理設定
    AUDIO_SAMPLE_RATE: 48000,
    AUDIO_CHANNELS: 2
};
