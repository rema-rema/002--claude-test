#!/usr/bin/env python3
"""
Streaming STT Server v2 - WhisperLive方式

Silero VADで高速に発話終了を検出し、Whisperに即座に通知する。
これにより380-520msのレイテンシを目指す。
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# whisper_streaming_lib をパスに追加
sys.path.insert(0, str(Path(__file__).parent / "whisper_streaming_lib"))

# whisper_streaming をインポート
try:
    from whisper_online import FasterWhisperASR, OnlineASRProcessor
except ImportError as e:
    print(f"Error importing whisper_online: {e}")
    print("Make sure whisper_streaming_lib is cloned:")
    print("  git clone https://github.com/ufal/whisper_streaming.git whisper_streaming_lib")
    sys.exit(1)

import websockets
import numpy as np
import torch

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 設定
HOST = "127.0.0.1"
PORT = 8765
MODEL_SIZE = "large-v3-turbo"
LANGUAGE = "ja"
SAMPLE_RATE = 16000
DEVICE = "cuda"
COMPUTE_TYPE = "float16"

# Silero VAD設定
VAD_THRESHOLD = 0.5  # 音声検出閾値
SPEECH_PAD_MS = 300  # 発話終了後の余白（ms）
MIN_SPEECH_MS = 250  # 最小発話長（ms）
MIN_SILENCE_MS = 1500  # 発話終了判定の無音時間（ms）- 息継ぎ（〜1秒）で切れないよう1.5秒に

# バッファリング設定
MIN_CHUNK_SAMPLES = SAMPLE_RATE // 4  # 0.25秒分 = 4000サンプル（高速化）

# チャンク分割設定（長文対応）
MAX_WHISPER_SECONDS = 5  # Whisperに渡す最大音声長（秒）
MAX_WHISPER_SAMPLES = SAMPLE_RATE * MAX_WHISPER_SECONDS  # 5秒 = 80000サンプル
OVERLAP_SECONDS = 0.5  # オーバーラップ（秒）- 単語境界対策
OVERLAP_SAMPLES = int(SAMPLE_RATE * OVERLAP_SECONDS)  # 8000サンプル


class ConfigurableFasterWhisperASR(FasterWhisperASR):
    """設定可能なFasterWhisperASR - device/compute_typeを外部から指定"""

    def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
        from faster_whisper import WhisperModel
        if model_dir is not None:
            model_size_or_path = model_dir
        elif modelsize is not None:
            model_size_or_path = modelsize
        else:
            raise ValueError("modelsize or model_dir parameter must be set")

        model = WhisperModel(model_size_or_path, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=cache_dir)
        return model


class SileroVADDetector:
    """Silero VADを使った高速発話検出"""

    def __init__(self, threshold=VAD_THRESHOLD, min_silence_ms=MIN_SILENCE_MS,
                 min_speech_ms=MIN_SPEECH_MS, speech_pad_ms=SPEECH_PAD_MS):
        self.threshold = threshold
        self.min_silence_samples = int(SAMPLE_RATE * min_silence_ms / 1000)
        self.min_speech_samples = int(SAMPLE_RATE * min_speech_ms / 1000)
        self.speech_pad_samples = int(SAMPLE_RATE * speech_pad_ms / 1000)

        # Silero VADモデルをロード
        logger.info("Loading Silero VAD model...")
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        self.model.eval()
        if DEVICE == "cuda" and torch.cuda.is_available():
            self.model = self.model.to('cuda')

        self.reset()
        logger.info("Silero VAD loaded successfully")

    def reset(self):
        """状態をリセット"""
        self.is_speaking = False
        self.speech_samples = 0
        self.silence_samples = 0
        self.speech_buffer = []
        self.model.reset_states()

    def process_chunk(self, audio_chunk: np.ndarray) -> dict:
        """
        音声チャンクを処理し、発話状態を返す

        Returns:
            dict: {
                "is_speech": bool,      # 現在音声があるか
                "speech_start": bool,   # 発話が開始したか
                "speech_end": bool,     # 発話が終了したか
                "audio": np.ndarray     # 発話終了時は蓄積した音声を返す
            }
        """
        result = {
            "is_speech": False,
            "speech_start": False,
            "speech_end": False,
            "audio": None
        }

        # VADで音声判定（512サンプル単位で処理）
        chunk_size = 512
        speech_detected = False

        for i in range(0, len(audio_chunk), chunk_size):
            chunk = audio_chunk[i:i+chunk_size]
            if len(chunk) < chunk_size:
                # パディング
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

            # Tensorに変換
            tensor = torch.from_numpy(chunk).float()
            if DEVICE == "cuda" and torch.cuda.is_available():
                tensor = tensor.to('cuda')

            # VAD判定
            speech_prob = self.model(tensor, SAMPLE_RATE).item()

            if speech_prob >= self.threshold:
                speech_detected = True
                break

        result["is_speech"] = speech_detected

        if speech_detected:
            self.silence_samples = 0
            self.speech_samples += len(audio_chunk)
            self.speech_buffer.append(audio_chunk)

            if not self.is_speaking and self.speech_samples >= self.min_speech_samples:
                # 発話開始
                self.is_speaking = True
                result["speech_start"] = True
                logger.info(f"[VAD] Speech started (accumulated {self.speech_samples} samples)")
        else:
            if self.is_speaking:
                self.silence_samples += len(audio_chunk)
                self.speech_buffer.append(audio_chunk)  # 少し余白を含める

                if self.silence_samples >= self.min_silence_samples:
                    # 発話終了
                    result["speech_end"] = True
                    result["audio"] = np.concatenate(self.speech_buffer) if self.speech_buffer else None
                    logger.info(f"[VAD] Speech ended after {self.silence_samples} silence samples")
                    self.reset()

        return result


# グローバル変数
asr = None
vad_detector = None


def detect_repetition(text: str, min_pattern_len: int = 3, min_repeats: int = 3) -> tuple[bool, str]:
    """
    テキスト内の繰り返しパターンを検出し、除去する

    Returns:
        (has_repetition, cleaned_text): 繰り返しがあったかどうかと、クリーンなテキスト
    """
    if not text or len(text) < min_pattern_len * min_repeats:
        return False, text

    # 繰り返しパターンを検出
    for pattern_len in range(min_pattern_len, min(20, len(text) // min_repeats + 1)):
        for start in range(len(text) - pattern_len * min_repeats + 1):
            pattern = text[start:start + pattern_len]

            # このパターンが連続して繰り返されているか確認
            repeat_count = 1
            pos = start + pattern_len
            while pos + pattern_len <= len(text) and text[pos:pos + pattern_len] == pattern:
                repeat_count += 1
                pos += pattern_len

            if repeat_count >= min_repeats:
                # 繰り返し検出！最初の出現だけ残す
                logger.warning(f"[FILTER] Repetition detected: '{pattern}' x{repeat_count}")
                # 繰り返し部分を除去（最初の1回だけ残す）
                cleaned = text[:start + pattern_len] + text[pos:]
                return True, cleaned

    return False, text


def clean_hallucination(text: str) -> str:
    """ハルシネーション（幻聴）パターンを除去"""
    # 既知のハルシネーションパターン
    hallucination_patterns = [
        "ご視聴ありがとうございました",
        "チャンネル登録お願いします",
        "チャンネル登録よろしくお願いします",
    ]

    cleaned = text
    for pattern in hallucination_patterns:
        if pattern in cleaned:
            logger.warning(f"[FILTER] Hallucination removed: '{pattern}'")
            cleaned = cleaned.replace(pattern, "")

    return cleaned.strip()


def init_models():
    """モデルを初期化"""
    global asr, vad_detector

    logger.info(f"Loading Whisper model: {MODEL_SIZE} (device={DEVICE}, compute={COMPUTE_TYPE})")
    asr = ConfigurableFasterWhisperASR(LANGUAGE, MODEL_SIZE)

    # WhisperのVADは無効化（Silero VADを使うため）
    # asr.use_vad()  # 無効化

    logger.info("Whisper model loaded (without internal VAD)")

    # Silero VADを初期化
    vad_detector = SileroVADDetector()


class ChunkResult:
    """チャンク処理結果を格納"""
    def __init__(self, seq_num: int, text: str, is_final: bool = False):
        self.seq_num = seq_num
        self.text = text
        self.is_final = is_final


async def process_chunk_worker(chunk_queue: asyncio.Queue, result_queue: asyncio.Queue,
                                stop_event: asyncio.Event):
    """
    バックグラウンドでチャンクを処理するワーカー
    メインループをブロックせずにWhisper処理を実行

    FasterWhisperASRのtranscribe_to_segmentを直接使用して、
    OnlineASRProcessorのバッファリング問題を回避
    """
    while not stop_event.is_set():
        try:
            # タイムアウト付きでキューから取得（定期的にstop_eventをチェック）
            try:
                task = await asyncio.wait_for(chunk_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            seq_num, audio_data, is_final_chunk = task
            duration = len(audio_data) / SAMPLE_RATE
            logger.info(f"[WORKER] Processing chunk {seq_num} ({len(audio_data)} samples = {duration:.1f}s, final={is_final_chunk})")

            # 直接FasterWhisperで認識（OnlineASRProcessorをバイパス）
            def transcribe_direct():
                # FasterWhisperASRのtranscribeを直接呼び出し
                segments, info = asr.model.transcribe(
                    audio_data,
                    language=LANGUAGE,
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    vad_filter=True,  # 内部VADで無音部分をスキップ
                )
                # セグメントからテキストを結合
                text = "".join([seg.text for seg in segments])
                return text.strip()

            text = await asyncio.to_thread(transcribe_direct)

            # 繰り返し検出
            if text:
                has_rep, text = detect_repetition(text)

            logger.info(f"[WORKER] Chunk {seq_num} result: '{text}'")
            await result_queue.put(ChunkResult(seq_num, text, is_final_chunk))
            chunk_queue.task_done()

        except Exception as e:
            logger.error(f"[WORKER] Error: {e}")
            import traceback
            traceback.print_exc()


async def handle_client(websocket):
    """クライアント接続を処理（非ブロッキングチャンク処理版）"""
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")

    # セッションごとにVADを作成
    local_vad = SileroVADDetector()

    # バッファとカウンタ
    audio_buffer = np.array([], dtype=np.float32)  # VAD前バッファ
    whisper_audio_buffer = np.array([], dtype=np.float32)  # Whisper用バッファ

    # チャンク管理
    chunk_count = 0
    chunk_seq = 0  # シーケンス番号
    chunk_results = {}  # seq_num -> text

    # テキスト管理
    accumulated_text = ""
    current_chunk_text = ""
    last_sent_text = ""

    # 非ブロッキング処理用キュー
    chunk_queue = asyncio.Queue()
    result_queue = asyncio.Queue()
    stop_event = asyncio.Event()

    # ワーカータスク起動
    worker_task = asyncio.create_task(
        process_chunk_worker(chunk_queue, result_queue, stop_event)
    )

    async def check_results():
        """結果キューをチェックして順序通りに結合"""
        nonlocal accumulated_text, chunk_results

        while not result_queue.empty():
            try:
                result = result_queue.get_nowait()
                chunk_results[result.seq_num] = result.text
                logger.info(f"[RESULT] Received chunk {result.seq_num}: '{result.text}'")
            except asyncio.QueueEmpty:
                break

        # 順序通りに結合（0から連続している分だけ）
        combined = ""
        next_seq = 0
        while next_seq in chunk_results:
            combined += chunk_results[next_seq]
            next_seq += 1

        if combined:
            accumulated_text = combined

    async def send_partial(text: str):
        """partialを送信"""
        nonlocal last_sent_text
        if text and text != last_sent_text:
            result = {
                "type": "partial",
                "text": text,
                "start": 0,
                "end": 0
            }
            await websocket.send(json.dumps(result))
            logger.info(f"Partial: {text}")
            last_sent_text = text

    try:
        async for message in websocket:
            # 定期的に結果をチェック
            await check_results()

            if isinstance(message, bytes):
                # 音声データを受信 (16bit PCM mono 16kHz)
                audio_chunk = np.frombuffer(message, dtype=np.int16).astype(np.float32) / 32768.0

                # バッファに追加
                audio_buffer = np.concatenate([audio_buffer, audio_chunk])

                # バッファが十分に溜まったら処理
                if len(audio_buffer) < MIN_CHUNK_SAMPLES:
                    continue

                # バッファを処理
                chunk_to_process = audio_buffer
                audio_buffer = np.array([], dtype=np.float32)

                # VADで発話状態をチェック（高速）
                vad_result = local_vad.process_chunk(chunk_to_process)

                if vad_result["speech_start"]:
                    # 発話開始を通知
                    await websocket.send(json.dumps({"type": "speech_start"}))

                if vad_result["is_speech"] or local_vad.is_speaking:
                    # Whisper用バッファに追加（処理はend時のみ）
                    whisper_audio_buffer = np.concatenate([whisper_audio_buffer, chunk_to_process])
                    duration = len(whisper_audio_buffer) / SAMPLE_RATE
                    logger.info(f"Processing audio with duration {duration:05.3f}")

                    # 5秒を超えたらチャンク分割
                    if len(whisper_audio_buffer) >= MAX_WHISPER_SAMPLES:
                        # オーバーラップを残して分割
                        chunk_audio = whisper_audio_buffer[:-OVERLAP_SAMPLES] if len(whisper_audio_buffer) > OVERLAP_SAMPLES else whisper_audio_buffer
                        whisper_audio_buffer = whisper_audio_buffer[-OVERLAP_SAMPLES:] if len(whisper_audio_buffer) > OVERLAP_SAMPLES else np.array([], dtype=np.float32)

                        # キューに追加（ブロックしない）
                        await chunk_queue.put((chunk_seq, chunk_audio, False))
                        logger.info(f"[CHUNK] Queued chunk {chunk_seq} ({len(chunk_audio)} samples = {len(chunk_audio)/SAMPLE_RATE:.1f}s)")
                        chunk_seq += 1
                        chunk_count += 1

                    # リアルタイムWhisper処理を削除 - end時のみ処理
                    # これにより毎回の再処理を防ぎ、レイテンシを大幅に改善

                if vad_result["speech_end"]:
                    # 発話終了 - ここでのみWhisper処理を実行
                    logger.info("[VAD] Speech ended, processing final...")

                    final_text = ""

                    # 残りのバッファを処理
                    if len(whisper_audio_buffer) > 0:
                        if chunk_count > 0:
                            # チャンク分割が発生した場合は最後のチャンクをキューに
                            await chunk_queue.put((chunk_seq, whisper_audio_buffer, True))
                            logger.info(f"[CHUNK] Queued final chunk {chunk_seq} ({len(whisper_audio_buffer)} samples)")
                            chunk_seq += 1

                            # 全チャンク処理完了を待つ
                            await chunk_queue.join()
                            await check_results()

                            final_text = accumulated_text
                        else:
                            # チャンク分割なし - 直接Whisper処理（1回のみ）
                            duration = len(whisper_audio_buffer) / SAMPLE_RATE
                            logger.info(f"[FINAL] Processing {duration:.1f}s audio with Whisper (single pass)")

                            def transcribe_final():
                                segments, info = asr.model.transcribe(
                                    whisper_audio_buffer,
                                    language=LANGUAGE,
                                    beam_size=5,
                                    best_of=5,
                                    temperature=0.0,
                                    vad_filter=True,
                                )
                                return "".join([seg.text for seg in segments]).strip()

                            final_text = await asyncio.to_thread(transcribe_final)

                    if final_text:
                        # フィルタ適用
                        has_rep, final_text = detect_repetition(final_text)
                        final_text = clean_hallucination(final_text)

                        if final_text:
                            result = {
                                "type": "final",
                                "text": final_text,
                                "start": 0,
                                "end": 0
                            }
                            await websocket.send(json.dumps(result))
                            logger.info(f"Final: {final_text}")

                    # リセット
                    accumulated_text = ""
                    current_chunk_text = ""
                    last_sent_text = ""
                    audio_buffer = np.array([], dtype=np.float32)
                    whisper_audio_buffer = np.array([], dtype=np.float32)
                    chunk_count = 0
                    chunk_seq = 0
                    chunk_results = {}
                    logger.info("Processor reset for new utterance")

            elif isinstance(message, str):
                data = json.loads(message)
                logger.info(f"Received JSON message: {data}")

                if data.get("type") == "end":
                    # 手動終了（セマンティックVADからの呼び出し）
                    logger.info("Processing manual end request...")

                    final_text = ""

                    # 残りのバッファを処理
                    if len(whisper_audio_buffer) > 0:
                        if chunk_count > 0:
                            # チャンク分割あり
                            await chunk_queue.put((chunk_seq, whisper_audio_buffer, True))
                            await chunk_queue.join()
                            await check_results()
                            final_text = accumulated_text
                        else:
                            # チャンク分割なし - 直接Whisper処理（1回のみ）
                            duration = len(whisper_audio_buffer) / SAMPLE_RATE
                            logger.info(f"[FINAL] Processing {duration:.1f}s audio with Whisper (single pass)")

                            def transcribe_final():
                                segments, info = asr.model.transcribe(
                                    whisper_audio_buffer,
                                    language=LANGUAGE,
                                    beam_size=5,
                                    best_of=5,
                                    temperature=0.0,
                                    vad_filter=True,
                                )
                                return "".join([seg.text for seg in segments]).strip()

                            final_text = await asyncio.to_thread(transcribe_final)

                    if final_text:
                        has_rep, final_text = detect_repetition(final_text)
                        final_text = clean_hallucination(final_text)

                        if final_text:
                            result = {
                                "type": "final",
                                "text": final_text,
                                "start": 0,
                                "end": 0
                            }
                            await websocket.send(json.dumps(result))
                            logger.info(f"Final: {final_text}")

                    # リセット
                    accumulated_text = ""
                    current_chunk_text = ""
                    last_sent_text = ""
                    audio_buffer = np.array([], dtype=np.float32)
                    whisper_audio_buffer = np.array([], dtype=np.float32)
                    chunk_count = 0
                    chunk_seq = 0
                    chunk_results = {}
                    local_vad.reset()
                    logger.info("Processor reset for new utterance")

                elif data.get("type") == "reset":
                    accumulated_text = ""
                    current_chunk_text = ""
                    last_sent_text = ""
                    audio_buffer = np.array([], dtype=np.float32)
                    whisper_audio_buffer = np.array([], dtype=np.float32)
                    chunk_count = 0
                    chunk_seq = 0
                    chunk_results = {}
                    local_vad.reset()
                    logger.info("Processor force reset")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # ワーカーを停止
        stop_event.set()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        logger.info(f"Client session ended: {client_id}")


async def main():
    """メインサーバー起動"""
    init_models()

    logger.info(f"Starting Streaming STT Server v2 (WhisperLive mode) on ws://{HOST}:{PORT}")
    logger.info(f"VAD settings: threshold={VAD_THRESHOLD}, min_silence={MIN_SILENCE_MS}ms")

    # ping_timeout=60s でWebSocket接続維持、ping_interval=30s で定期ping
    async with websockets.serve(handle_client, HOST, PORT, ping_interval=30, ping_timeout=60):
        logger.info("Server ready. Waiting for connections...")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown")
