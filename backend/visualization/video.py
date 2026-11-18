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


def _is_seekable_source(source) -> bool:
    """Przewijać da się tylko lokalne pliki (strumienie na żywo i kamery – nie)."""
    return isinstance(source, str) and os.path.isfile(source)


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

    # (czy działa, czy wstrzymane, czy można przewijać)
    playback_state_changed = pyqtSignal(bool, bool, bool)
    # (aktualna pozycja [s], długość [s]) – tylko dla źródeł z przewijaniem
    position_changed = pyqtSignal(float, float)

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

        # Sterowanie odtwarzaniem (ustawiane z wątku GUI, czytane w run())
        self._paused = False
        self._step_once = False          # pokaż jedną klatkę mimo pauzy (po przewinięciu)
        self._at_end = False             # plik doszedł do końca
        self.seekable = False
        self.total_frames = 0
        self._seek_lock = threading.Lock()
        self._pending_seek_rel = 0.0     # przesunięcie względne [s]
        self._pending_seek_abs = None    # pozycja bezwzględna [s]

        # Synchronizacja Video z FrameProcessor
        self._frame_processed = threading.Event()

        # Początkowo Video nie musi czekać
        self._frame_processed.set()

    # ---------- API sterowania (wywoływane z wątku GUI) ----------

    @property
    def is_paused(self) -> bool:
        return self._paused

    def set_paused(self, paused: bool):
        if not self.isRunning():
            return
        if not paused and self._at_end:
            # wznowienie po dojściu do końca pliku = odtwarzanie od początku
            with self._seek_lock:
                self._pending_seek_abs = 0.0
                self._pending_seek_rel = 0.0
        self._paused = paused
        self.playback_state_changed.emit(True, paused, self.seekable)

    def toggle_pause(self):
        self.set_paused(not self._paused)

    def seek(self, seconds: float):
        """Przewinięcie o `seconds` sekund (ujemne = do tyłu)."""
        if not self.isRunning() or not self.seekable:
            return
        with self._seek_lock:
            self._pending_seek_rel += seconds

    # -------------------------------------------------------------

    def resize_video_to_dimensions(self, width: int, height: int) -> None:
        # Zachowane dla zgodności z AppController. Wartości nie wpływają
        # na klatkę przekazywaną do FrameProcessor.
        self.width = width
        self.height = height

    def change_video_source(self, source):
        print(f"zmiana video na: {source}")
        if self.isRunning():
            self.stop()

        self.source = source
        return True

    def _apply_pending_seek(self, fps: float) -> bool:
        with self._seek_lock:
            rel = self._pending_seek_rel
            abs_pos = self._pending_seek_abs
            self._pending_seek_rel = 0.0
            self._pending_seek_abs = None

        if not self.seekable or (rel == 0.0 and abs_pos is None):
            return False

        if abs_pos is not None:
            target = abs_pos * fps
        else:
            current = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            target = current + rel * fps

        target = int(max(0, min(target, self.total_frames - 1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target)
        self._at_end = False
        return True

    def run(self):

        if self.source is None:
            self.error_occurred.emit("Nie wybrano źródła wideo")
            return

        self._is_running = True
        self._paused = False
        self._step_once = False
        self._at_end = False
        self.seekable = False
        with self._seek_lock:
            self._pending_seek_rel = 0.0
            self._pending_seek_abs = None

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

            frame_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.total_frames = int(frame_count) if frame_count and frame_count > 0 else 0
            self.seekable = _is_seekable_source(self.source) and self.total_frames > 0
            duration = self.total_frames / fps if self.seekable else 0.0

            self.playback_state_changed.emit(True, False, self.seekable)

            print(f"fps zrodla: {self.source_fps}")
            meas_start = time.perf_counter()
            meas_count = 0
            fail_count = 0
            while self._is_running:

                # Przewijanie
                if self._apply_pending_seek(fps):
                    next_frame_time = time.perf_counter()
                    if self._paused:
                        self._step_once = True     # pokaż klatkę z nowej pozycji

                # Pauza
                if self._paused and not self._step_once:
                    time.sleep(0.02)
                    next_frame_time = time.perf_counter()
                    meas_start, meas_count = time.perf_counter(), 0
                    continue
                stepping = self._step_once
                self._step_once = False

                ret, frame = self.cap.read()
                if not ret:
                    if _is_hls_url(self.source) and fail_count < 20:   # strumień na żywo: ponów
                        fail_count += 1
                        time.sleep(0.25)
                        continue
                    if self.seekable:
                        # koniec pliku: zatrzymaj się na pauzie, żeby można było przewinąć
                        self._at_end = True
                        self._paused = True
                        self.playback_state_changed.emit(True, True, self.seekable)
                        continue
                    break
                fail_count = 0

                meas_count += 1
                elapsed = time.perf_counter() - meas_start
                if elapsed >= 5.0:
                    print(f"[VIDEO] zmierzony FPS: {meas_count / elapsed:.1f} (deklarowany: {self.source_fps})")
                    meas_start, meas_count = time.perf_counter(), 0

                # Przygotowanie oczekiwania na zakończenie
                # przetwarzania aktualnej klatki
                if self.pace_to_source_fps and not stepping:
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

                if self.seekable:
                    pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                    self.position_changed.emit(pos / fps, duration)

                # Oczekiwanie na zakończenie analizy
                while self._is_running:

                    if self._frame_processed.wait(timeout=0.1):
                        break

        except Exception as exc:
            self.error_occurred.emit(str(exc))

        finally:
            self._is_running = False
            self._paused = False

            if self.cap is not None:
                self.cap.release()
                self.cap = None

            self.playback_state_changed.emit(False, False, False)

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