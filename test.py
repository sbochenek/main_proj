import subprocess
import cv2
import numpy as np

# Twój aktualny adres strumienia z ważnym tokenem
stream_url = "https://s1.worldcam.live:8082/aleksandrow-lodzki-dmowskiego-konstantynowska/index.m3u8?token=2d2636dd4c39f34b95827a73c1df661595baffecc483dc479d69fd50c537547b"
# Pobierz parametry wideo (szerokość, wysokość) za pomocą ffprobe lub ustaw na sztywno, np. 1920x1080 lub 1280x720
# Dla Full HD (zgodnie z linkiem 1080):
width, height = 1920, 1080

# Komenda FFmpeg wypuszczająca surowe klatki w formacie BGR24 na standardowe wyjście (pipe)
ffmpeg_cmd = [
    "ffmpeg",
    "-i",
    stream_url,
    "-f",
    "image2pipe",
    "-pix_fmt",
    "bgr24",
    "-vcodec",
    "rawvideo",
    "-",
]

# Uruchomienie procesu FFmpeg
pipe = subprocess.Popen(
    ffmpeg_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,  # ukrywa logi FFmpeg, zmień na None jeśli chcesz debugować
    bufsize=10**8,
)

frame_size = width * height * 3

print("Otwieranie strumienia przez FFmpeg...")

try:
  while True:
    # Pobieramy dokładną liczbę bajtów odpowiadającą jednej klatce
    raw_frame = pipe.stdout.read(frame_size)

    if not raw_frame:
      print("Koniec strumienia lub brak danych.")
      break

    # Konwersja surowych bajtów na tablicę NumPy
    frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape(
        (height, width, 3)
    )

    cv2.imshow("Kamera live (FFmpeg Pipe)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
      break
finally:
  pipe.terminate()
  cv2.destroyAllWindows()