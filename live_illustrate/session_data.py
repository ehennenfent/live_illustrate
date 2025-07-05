import enum
import logging
import os
import sqlite3
import time
import wave
from datetime import datetime
from pathlib import Path

import speech_recognition as sr
from discord import File, SyncWebhook

from .util import Image, Summary, Transcription, mean_and_stdev

DISCORD_WEBHOOK = "DISCORD_WEBHOOK"


class TimestampVariant(enum.IntEnum):
    RECORD = 0
    TRANSCRIBE = 1
    SUMMARIZE = 2
    ILLUSTRATE = 3


class SessionData:
    """Creates a data/<timestamp> folder for the session and stores images, summaries, and transcripts"""

    def __init__(self, data_dir: Path, echo: bool = True) -> None:
        self.start_time = datetime.now()
        self.logger = logging.getLogger("SessionData")

        self.data_dir: Path = data_dir.joinpath(self.start_time.strftime("%Y_%m_%d-%H_%M_%S"))
        self.audio_dir: Path = self.data_dir.joinpath("audio_chunks")
        self.echo: bool = echo

        self.discord_webhook: str | None = os.getenv(DISCORD_WEBHOOK)
        if self.discord_webhook is not None:
            self.logger.info("Discord upload is enabled")

        self.db_file = self.data_dir.joinpath("timestamps.db")
        self.ts_db: sqlite3.Connection | None = None

    def _init_db(self) -> None:
        db = sqlite3.connect(self.db_file)
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS time_series (
                timestamp INTEGER PRIMARY KEY,
                variant INTEGER NOT NULL,
                actual_duration INTEGER NOT NULL,
                expected_duration INTEGER
            )
            """
        )
        db.commit()

    def save_audio_chunk(self, audio: sr.AudioData) -> None:
        try:
            fname = self.audio_dir.joinpath(f"{self._time_since}.wav")
            with open(fname, "wb") as outf:
                outf.write(audio.get_wav_data())
        except Exception as e:
            self.logger.error("failed to save audio data to file: %s", e)

    def stitch_audio_chunks_to_wav(self) -> None:
        """Using the wave library, read all the audio chunks and save them as a single file"""
        try:
            output_file = self.data_dir.joinpath("recording.wav")
            with wave.open(str(output_file), "wb") as wav_out:
                is_init = False
                for audio_chunk in sorted(self.audio_dir.glob("*.wav")):
                    with wave.open(str(audio_chunk), "rb") as chunk_in:
                        if not is_init:
                            wav_out.setparams(chunk_in.getparams())
                            is_init = True
                        wav_out.writeframes(chunk_in.readframes(chunk_in.getnframes()))
        except Exception as e:
            self.logger.error("failed to stitch audio chunks into WAV file: %s", e)

    def save_time_series(
        self, variant: TimestampVariant, actual_duration: int, expected_duration: int | None = None
    ) -> None:
        if self.ts_db is None:
            # We can now only use this database connection from this thread.
            self.ts_db = sqlite3.connect(self.db_file)
        try:
            cursor = self.ts_db.cursor()
            cursor.execute(
                "INSERT INTO time_series (timestamp, variant, actual_duration, expected_duration) VALUES (?, ?, ?, ?)",
                (time.time_ns() // 1_000_000, variant.value, actual_duration, expected_duration),
            )
            self.ts_db.commit()
        except Exception as e:
            self.logger.error("failed to save time series data: %s", e)

    def save_image(self, image: Image) -> None:
        try:
            fname = self.data_dir.joinpath(f"{self._time_since}.png")
            with open(fname, "wb") as outf:
                outf.write(image.image_bytes)
        except Exception as e:
            self.logger.error("failed to save image to file: %s", e)
        else:
            try:
                if self.discord_webhook is not None:
                    with open(fname, "rb") as image_file:
                        SyncWebhook.from_url(self.discord_webhook).send(
                            file=File(image_file, description=image.summary[:1023])
                        )
            except Exception as e:
                self.logger.error("failed to send image to discord: %s", e)

    def save_summary(self, summary: Summary) -> None:
        """saves the provided text to its own file"""
        try:
            with open(self.data_dir.joinpath(f"{self._time_since}.txt"), "w", encoding="utf-8") as summaryf:
                print(summary.summary, file=summaryf)
        except Exception as e:
            self.logger.error("failed to write summary to file: %s", e)

    def save_transcription(self, transcription: Transcription) -> None:
        """appends the provided text to the transcript file"""
        try:
            with open(self.data_dir.joinpath("transcript.txt"), "a", encoding="utf-8") as transf:
                if self.echo:
                    print(self._time_since, ">", transcription.transcription)
                print(self._time_since, ">", transcription.transcription, file=transf, flush=True)
                if hasattr(transcription, "transcription_time"):
                    self.save_time_series(
                        TimestampVariant.TRANSCRIBE,
                        transcription.transcription_time,
                        getattr(transcription, "audio_duration", None),
                    )
        except Exception as e:
            self.logger.error("failed to write transcript to file: %s", e)

    def print_transcription_stats(self) -> None:
        # calculate average time between db entries
        cursor = sqlite3.connect(self.db_file).cursor()
        cursor.execute("SELECT timestamp FROM time_series WHERE variant = ?", (TimestampVariant.TRANSCRIBE.value,))
        timestamps = [row[0] for row in cursor.fetchall()]
        avg, std = mean_and_stdev(timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps)))
        print(f"Average time between transcription entries: {avg / 1000.0:.2f}s (std dev: {std / 1000.0:.2f}s)")
        # calculate average transcription time as a fraction of audio duration
        cursor.execute(
            "SELECT actual_duration, expected_duration FROM time_series WHERE variant = ?",
            (TimestampVariant.TRANSCRIBE.value,),
        )
        durations = cursor.fetchall()
        avg, std = mean_and_stdev(actual / expected for actual, expected in durations if expected is not None)
        print(f"Average transcription time as a fraction of audio duration: {avg:.2f} (std dev: {std:.2f})")

    @property
    def _time_since(self) -> str:
        delta = datetime.now() - self.start_time
        minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours}h_{minutes:02}m_{seconds:02}s"

    def __enter__(self) -> "SessionData":  # create the directories upon entry, not upon init
        if not (parent := self.data_dir.parent).exists():
            parent.mkdir()
        self.data_dir.mkdir()
        self.audio_dir.mkdir()
        self._init_db()
        return self

    def __exit__(self, *exc) -> None:
        pass
