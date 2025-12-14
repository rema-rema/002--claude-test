/**
 * Streaming STT Client - WebSocket経由でリアルタイム音声認識
 *
 * streaming_stt_server.py に接続して音声チャンクを送信し、
 * リアルタイムで認識結果を受け取る
 */

const WebSocket = require('ws');
const EventEmitter = require('events');

const STREAMING_STT_URL = process.env.STREAMING_STT_URL || 'ws://127.0.0.1:8765';

class StreamingSTTClient extends EventEmitter {
    constructor() {
        super();
        this.ws = null;
        this.connected = false;
        this.reconnectTimer = null;
        this.currentText = '';
    }

    /**
     * サーバーに接続
     */
    connect() {
        if (this.ws) {
            this.ws.close();
        }

        console.log(`[StreamingSTT] Connecting to ${STREAMING_STT_URL}...`);

        // サーバー側ping_interval=30s, ping_timeout=60sに対応
        this.ws = new WebSocket(STREAMING_STT_URL, {
            handshakeTimeout: 10000,  // 接続ハンドシェイクタイムアウト
        });

        this.ws.on('open', () => {
            console.log('[StreamingSTT] Connected');
            this.connected = true;
            this.emit('connected');
        });

        this.ws.on('message', (data) => {
            try {
                const result = JSON.parse(data.toString());

                if (result.type === 'partial') {
                    this.currentText = result.text;
                    this.emit('partial', result.text);
                    console.log(`[StreamingSTT] Partial: ${result.text}`);
                } else if (result.type === 'final') {
                    this.currentText = result.text;
                    this.emit('final', result.text);
                    console.log(`[StreamingSTT] Final: ${result.text}`);
                }
            } catch (e) {
                console.error('[StreamingSTT] Parse error:', e);
            }
        });

        this.ws.on('close', () => {
            console.log('[StreamingSTT] Disconnected');
            this.connected = false;
            this.emit('disconnected');

            // 自動再接続
            this.scheduleReconnect();
        });

        this.ws.on('error', (err) => {
            console.error('[StreamingSTT] Error:', err.message);
            this.emit('error', err);
        });
    }

    /**
     * 再接続をスケジュール
     */
    scheduleReconnect() {
        if (this.reconnectTimer) return;

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            console.log('[StreamingSTT] Attempting reconnect...');
            this.connect();
        }, 3000);
    }

    /**
     * 音声チャンクを送信
     * @param {Buffer} pcmData - 16bit PCM mono 16kHz データ
     */
    sendAudioChunk(pcmData) {
        if (!this.connected || !this.ws) {
            return false;
        }

        try {
            this.ws.send(pcmData);
            return true;
        } catch (e) {
            console.error('[StreamingSTT] Send error:', e);
            return false;
        }
    }

    /**
     * 発話終了を通知（最終結果を取得）
     */
    endUtterance() {
        if (!this.connected || !this.ws) {
            console.log('[StreamingSTT] endUtterance: not connected, skipping');
            return;
        }

        const endMsg = JSON.stringify({ type: 'end' });
        console.log(`[StreamingSTT] Sending end message to server: ${endMsg}`);
        this.ws.send(endMsg, (err) => {
            if (err) {
                console.error('[StreamingSTT] Error sending end message:', err);
            } else {
                console.log('[StreamingSTT] End message sent successfully');
            }
        });
    }

    /**
     * セッションをリセット
     */
    reset() {
        if (!this.connected || !this.ws) {
            return;
        }

        this.currentText = '';
        this.ws.send(JSON.stringify({ type: 'reset' }));
    }

    /**
     * 接続を閉じる
     */
    close() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.connected = false;
    }

    /**
     * 接続状態を取得
     */
    isConnected() {
        return this.connected;
    }

    /**
     * 現在の認識テキストを取得
     */
    getCurrentText() {
        return this.currentText;
    }
}

// シングルトンインスタンス
let instance = null;

function getStreamingSTTClient() {
    if (!instance) {
        instance = new StreamingSTTClient();
    }
    return instance;
}

module.exports = {
    StreamingSTTClient,
    getStreamingSTTClient,
    STREAMING_STT_URL
};

// CLIテスト用
if (require.main === module) {
    const client = new StreamingSTTClient();

    client.on('connected', () => {
        console.log('Ready for audio input');
    });

    client.on('partial', (text) => {
        console.log(`Partial: "${text}"`);
    });

    client.on('final', (text) => {
        console.log(`Final: "${text}"`);
    });

    client.connect();

    // Ctrl+Cで終了
    process.on('SIGINT', () => {
        client.close();
        process.exit(0);
    });
}
