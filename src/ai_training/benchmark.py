import time
import numpy as np
import torch
from ultralytics import YOLO

# =========================
# Config
# =========================
MODEL_PATH = "./src/megajaw_brain/static/best_ncnn_model_real/"  # change to your model path
IMG_H = 288  # Gaussian noise image height
IMG_W = 352  # Gaussian noise image width
IMG_C = 3  # channels, usually 3 for RGB
WARMUP_RUNS = 2  # warmup iterations (not counted)
TEST_RUNS = 100  # measured iterations
CONF = 0.25
IOU = 0.7
TRACKER =  "botsort.yaml" # bytetrack.yaml | "botsort.yaml"
SEED = 42


# =========================
# Helpers
# =========================
def make_noise_image(h: int, w: int, c: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = rng.normal(loc=127, scale=40, size=(h, w, c))
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def sync_device():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


# =========================
# Load model and time it
# =========================
load_start = time.perf_counter()
model = YOLO(MODEL_PATH)
load_time_s = time.perf_counter() - load_start

device_str = 0 if torch.cuda.is_available() else "cpu"
print(f"Model loaded in: {load_time_s:.4f} s")
print(f"Device: {device_str}")

# =========================
# Dummy input
# =========================
frame = make_noise_image(IMG_H, IMG_W, IMG_C, seed=SEED)

# =========================
# Warmup
# =========================
for _ in range(WARMUP_RUNS):
    sync_device()
    _ = model.track(
        source=frame,
        persist=True,
        conf=CONF,
        iou=IOU,
        tracker=TRACKER,
        verbose=False,
        device=device_str,
    )
    sync_device()

# =========================
# Benchmark
# =========================
latencies_ms = []
fps_values = []

for _ in range(TEST_RUNS):
    sync_device()
    t0 = time.perf_counter()

    results = model.track(
        source=frame,
        persist=True,
        conf=CONF,
        iou=IOU,
        tracker=TRACKER,
        verbose=False,
        device=device_str,
    )

    sync_device()
    t1 = time.perf_counter()

    latency_ms = (t1 - t0) * 1000.0
    fps = 1.0 / (t1 - t0)

    latencies_ms.append(latency_ms)
    fps_values.append(fps)

# =========================
# Report
# =========================
latencies_ms = np.array(latencies_ms, dtype=np.float64)
fps_values = np.array(fps_values, dtype=np.float64)

print("\n==== Benchmark Results ====")
print(f"Runs: {TEST_RUNS}")
print(f"Image shape: ({IMG_H}, {IMG_W}, {IMG_C})")
print(f"Warmup runs: {WARMUP_RUNS}")
print(f"Load time: {load_time_s:.4f} s")
print(f"Latency min: {latencies_ms.min():.4f} ms")
print(f"Latency max: {latencies_ms.max():.4f} ms")
print(f"Latency avg: {latencies_ms.mean():.4f} ms")
print(f"FPS max:     {fps_values.max():.2f}")
print(f"FPS min:     {fps_values.min():.2f}")
print(f"FPS avg:     {fps_values.mean():.2f}")
