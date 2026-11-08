# app/backend\visualization\video.py
from ultralytics import YOLO
from PyQt5.QtCore import QThread, pyqtSignal

import time
import subprocess
import cv2
import numpy as np
import threading
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "timeout;5000000|"              # nieudane połączenie kończy się po 5 s, nie po ~minucie
    "http_persistent;1|"            # ponowne użycie połączenia zamiast nowego TCP na każdy segment
    "multiple_requests;1|"
    "reconnect;1|reconnect_streamed;1|reconnect_delay_max;2"
)

import re
import urllib.request
from urllib.parse import urljoin, urlparse

_ATTR_RE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')


def _is_hls_url(source) -> bool:
    if not isinstance(source, str):
        return False
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https") and parsed.path.lower().endswith(".m3u8")


def _download_text(url: str, timeout: float = 10.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_variants(playlist_text: str):
    """Zwraca listę wariantów: {'uri', 'bandwidth', 'height'} z playlisty master."""
    variants = []
    lines = [l.strip() for l in playlist_text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue
        attrs = {k: v.strip('"') for k, v in _ATTR_RE.findall(line.split(":", 1)[1])}
        # URI wariantu to najbliższa kolejna linia niebędąca komentarzem
        uri = next((l for l in lines[i + 1:] if not l.startswith("#")), None)
        if uri is None:
            continue
        height = 0
        if "RESOLUTION" in attrs and "x" in attrs["RESOLUTION"]:
            try:
                height = int(attrs["RESOLUTION"].split("x")[1])
            except ValueError:
                pass
        codecs = attrs.get("CODECS", "")
        audio_only = bool(codecs) and "avc" not in codecs and "hvc" not in codecs \
            and "hev" not in codecs and "vp0" not in codecs and "av01" not in codecs
        if audio_only:
            continue
        variants.append({
            "uri": uri,
            "bandwidth": int(attrs.get("BANDWIDTH", 0) or 0),
            "height": height,
        })
    return variants


def resolve_hls_source(source, max_height=None, max_depth=3):
    """
    Dla linku master.m3u8 zwraca URL wybranego wariantu (media playlist).
    Dla index.m3u8, plików i kamer zwraca źródło bez zmian.
    max_height: preferowana maks. wysokość obrazu (None = najlepsza jakość).
    """
    if not _is_hls_url(source):
        return source

    url = source
    for _ in range(max_depth):
        text = _download_text(url)
        if "#EXT-X-STREAM-INF" not in text:
            return url                      # to już media playlist (index.m3u8)

        variants = _parse_variants(text)
        if not variants:
            return url

        if max_height:
            fitting = [v for v in variants if 0 < v["height"] <= max_height]
            pool = fitting or variants
        else:
            pool = variants
        best = max(pool, key=lambda v: (v["bandwidth"], v["height"]))

        next_url = urljoin(url, best["uri"])
        # token z zapytania master często jest wymagany także w wariancie
        if "?" not in best["uri"] and urlparse(url).query:
            next_url += "?" + urlparse(url).query
        print(f"[HLS] wariant: {best['height']}p, {best['bandwidth']} bps -> {next_url}")
        url = next_url
    return url


class Video(QThread):

    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.width = 1280
        self.height = 900

        self.source = None
        self.cap = None
        self.max_height = 720
        self.resolved_source = None

        self._is_running = True
        self.source_fps = 0.0
        self.pace_to_source_fps = True

        # Synchronizacja Video z FrameProcessor
        self._frame_processed = threading.Event()

        # Początkowo Video nie musi czekać
        self._frame_processed.set()

    def resize_video_to_dimensions(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def change_video_source(self, source):
        print(f"zmiana video na: {source}")
        if self.isRunning():
            self.stop()

        self.source = source
        return True
    
    def run(self):

        if self.source is None:
            self.error_occurred.emit("Nie wybrano źródła wideo")
            return

        self._is_running = True

        try:
            # Otwarcie źródła w wątku Video
            try:
                self.resolved_source = resolve_hls_source(self.source, self.max_height)
            except Exception as exc:
                self.error_occurred.emit(f"Nie udało się odczytać playlisty HLS: {exc}")
                self.resolved_source = self.source   # próba bezpośrednia

            self.cap = cv2.VideoCapture(self.resolved_source, cv2.CAP_FFMPEG)

            if not self.cap.isOpened():
                self.error_occurred.emit(
                    f"Nie można otworzyć źródła: {self.source}"
                )
                return
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            # strumienie czasem zwracają 0, NaN albo absurdalne wartości
            if not (1.0 <= fps <= 240.0):
                fps = 25.0
            self.source_fps = fps
            frame_interval = 1.0 / fps
            next_frame_time = time.perf_counter()

            print(f"fps zrodla: {self.source_fps}")
            meas_start = time.perf_counter()
            meas_count = 0
            fail_count = 0
            while self._is_running:
                ret, frame = self.cap.read()
                if not ret:
                    if _is_hls_url(self.source) and fail_count < 20:   # strumień na żywo: ponów
                        fail_count += 1
                        time.sleep(0.25)
                        continue
                    break
                fail_count = 0

                
                if not ret:
                    break
                meas_count += 1
                elapsed = time.perf_counter() - meas_start
                if elapsed >= 5.0:
                    print(f"[VIDEO] zmierzony FPS: {meas_count / elapsed:.1f} (deklarowany: {self.source_fps})")
                    meas_start, meas_count = time.perf_counter(), 0

                # Dopasowanie rozmiaru obrazu
                frame = cv2.resize(
                    frame,
                    (self.width, self.height)
                )

                # Przygotowanie oczekiwania na zakończenie
                # przetwarzania aktualnej klatki
                if self.pace_to_source_fps:
                    now = time.perf_counter()
                    wait = next_frame_time - now
                    if wait < -1.0:                 # jesteśmy spóźnieni o ponad sekundę
                        next_frame_time = now
                    if wait > 0:
                        # krótkie porcje, żeby stop() reagował od razu
                        end = now + wait
                        while self._is_running and time.perf_counter() < end:
                            time.sleep(min(0.005, max(0.0, end - time.perf_counter())))
                        next_frame_time += frame_interval
                    else:
                        # jesteśmy spóźnieni (model wolniejszy od źródła): nie nadganiaj
                        next_frame_time = now + frame_interval
                self._frame_processed.clear()

                # Przekazanie surowej klatki
                self.frame_ready.emit(frame)

                # Oczekiwanie na zakończenie analizy
                while self._is_running:

                    if self._frame_processed.wait(timeout=0.1):
                        break

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            self._is_running = False

            if self.cap is not None:
                self.cap.release()
                self.cap = None

    def processing_finished(self):
        """
        Wywoływane po zakończeniu analizy klatki.
        Event.set() jest bezpieczne do wywołania z innego wątku.
        """
        self._frame_processed.set()

    def stop(self):

        self._is_running = False

        # Odblokowanie Video, jeżeli oczekuje na przetworzenie
        self._frame_processed.set()

        if self.isRunning():
            self.wait()


