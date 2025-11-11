"""preprocess_final.py

Generalized preprocessing for arbitrary .mp4 datasets.

Features:
- Discover videos under one or more input directories. If an input directory
  contains subdirectories, those subdirectories are used as labels (e.g.
  real/, fake/). If a single input dir is provided, the directory name is used
  as the label.
- Extract frames using OpenCV at a configurable frames-per-second rate.
- Create train/test/val splits (configurable ratios) either per-label or
  globally.
- Create CSV manifests for each split.

Usage (example):
  python src/preprocessing/preprocess_final.py \
    --inputs "C:/data/ff_real" "C:/data/ff_fake" \
    --output data/processed/final --fps 1 --splits 0.6 0.2 0.2

This file is intentionally standalone and minimal; adapt as needed for more
dataset-specific logic (face detection, cropping, augmentations).
"""

import argparse
import csv
import logging
import random
import shutil
from pathlib import Path
from typing import List, Tuple, Dict

from tqdm.auto import tqdm


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


class PreprocessFinal:
    def __init__(
        self,
        input_paths: List[Path],
        output_dir: Path,
        frames_per_second: float = 1.0,
        exts: List[str] = None,
        splits: Tuple[float, float, float] = (0.6, 0.2, 0.2),
        seed: int = 42,
        per_label_split: bool = True,
        max_per_label: int = None,
        recursive: bool = True,
        detect: bool = False,
        augment: bool = False,
        aug_count: int = 2,
        heatmap: bool = False,
        face_size: int = 224,
        save_crops: bool = True,
    ):
        self.input_paths = input_paths
        self.output_dir = output_dir
        self.frames_per_second = frames_per_second
        self.exts = exts or ['.mp4']
        self.splits = splits
        self.seed = seed
        self.per_label_split = per_label_split
        self.max_per_label = max_per_label
        self.recursive = recursive
        self.detect = detect
        self.augment = augment
        self.aug_count = aug_count
        self.heatmap = heatmap
        self.face_size = face_size
        self.save_crops = save_crops

        random.seed(self.seed)

    def setup_directories(self):
        if self.output_dir.exists():
            logging.info(f"Removing existing output dir {self.output_dir}")
            shutil.rmtree(self.output_dir)
        for split in ['train', 'test', 'val']:
            (self.output_dir / split).mkdir(parents=True, exist_ok=True)

    def discover_videos(self) -> List[Tuple[Path, str]]:
        """Return list of (video_path, label). Infers labels from directory
        structure: if an input path has subfolders, those subfolders are labels.
        Otherwise label is the input folder name.
        """
        videos = []
        for p in self.input_paths:
            if not p.exists():
                logging.warning(f"Input path not found: {p}")
                continue

            # If path contains subdirectories, treat each subdir as a label
            subdirs = [d for d in p.iterdir() if d.is_dir()]
            if subdirs:
                for sd in subdirs:
                    label = sd.name
                    pattern = '**/*' if self.recursive else '*'
                    for ext in self.exts:
                        for v in sd.glob(f"{pattern}{ext}"):
                            if v.is_file():
                                videos.append((v, label))
            else:
                # No subdirs: take all videos under p and label by folder name
                label = p.name
                pattern = '**/*' if self.recursive else '*'
                for ext in self.exts:
                    for v in p.glob(f"{pattern}{ext}"):
                        if v.is_file():
                            videos.append((v, label))

        logging.info(f"Discovered {len(videos)} videos across {len(self.input_paths)} input paths")
        return videos

    def split_videos(self, videos: List[Tuple[Path, str]]) -> Dict[str, List[Tuple[Path, str]]]:
        """Split videos into train/test/val. Returns dict with keys 'train','test','val'.
        If per_label_split is True, perform stratified split per label.
        """
        splits_out = {'train': [], 'test': [], 'val': []}
        if self.per_label_split:
            # Group by label
            by_label = {}
            for v, label in videos:
                by_label.setdefault(label, []).append((v, label))

            for label, items in by_label.items():
                items = list(items)
                random.shuffle(items)
                if self.max_per_label:
                    items = items[: self.max_per_label]
                n = len(items)
                t = int(self.splits[0] * n)
                u = int((self.splits[0] + self.splits[1]) * n)
                splits_out['train'].extend(items[:t])
                splits_out['test'].extend(items[t:u])
                splits_out['val'].extend(items[u:])
        else:
            items = list(videos)
            random.shuffle(items)
            if self.max_per_label:
                items = items[: self.max_per_label]
            n = len(items)
            t = int(self.splits[0] * n)
            u = int((self.splits[0] + self.splits[1]) * n)
            splits_out['train'] = items[:t]
            splits_out['test'] = items[t:u]
            splits_out['val'] = items[u:]

        logging.info(
            f"Split counts -> train: {len(splits_out['train'])}, test: {len(splits_out['test'])}, val: {len(splits_out['val'])}"
        )
        return splits_out

    def extract_frames(self, video_path: Path, out_dir: Path) -> int:
        """Extract frames using OpenCV at the configured frames_per_second.
        Returns number of frames written.
        """
        import cv2

        out_dir.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logging.error(f"Unable to open video: {video_path}")
            return 0

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        # How many frames to skip between saved frames
        step = max(1, int(round(video_fps / max(1e-6, self.frames_per_second))))

        written = 0
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % step == 0:
                frame_path = out_dir / f"frame_{written:05d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                written += 1

            idx += 1

        cap.release()
        return written

    # --- Face detection, augmentation and heatmap helpers ---
    def _init_detector(self):
        """Attempt to initialize a face detector. Prefer MTCNN from facenet-pytorch,
        fall back to OpenCV Haar cascade if not available.
        """
        try:
            from facenet_pytorch import MTCNN
            import torch

            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            mtcnn = MTCNN(keep_all=True, device=device)
            logging.info(f"Using MTCNN (facenet-pytorch) on {device}")
            self._detector = ('mtcnn', mtcnn)
        except Exception as e:
            logging.warning(f"facenet-pytorch not available or failed to init: {e}; falling back to Haar cascade")
            import cv2
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            cascade = cv2.CascadeClassifier(cascade_path)
            self._detector = ('haar', cascade)

    def detect_faces(self, frame):
        """Return list of bounding boxes [x1,y1,x2,y2] for faces in the given BGR frame."""
        if not hasattr(self, '_detector'):
            self._init_detector()

        kind, det = self._detector
        boxes = []
        if kind == 'mtcnn':
            # MTCNN expects RGB
            import numpy as np
            rgb = frame[:, :, ::-1]
            try:
                bbs, probs = det.detect(rgb)
            except Exception as e:
                logging.error(f"MTCNN detection error: {e}")
                return boxes

            if bbs is None:
                return boxes
            for bb in bbs:
                x1, y1, x2, y2 = [int(max(0, v)) for v in bb]
                boxes.append((x1, y1, x2, y2))
        else:
            # Haar cascade expects grayscale
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            for (x, y, w, h) in detected:
                boxes.append((int(x), int(y), int(x + w), int(y + h)))

        return boxes

    def _make_heatmap(self, shape, boxes):
        """Create a heatmap (grayscale float32 0-1) for given image shape and boxes."""
        import numpy as np
        h, w = shape[:2]
        heat = np.zeros((h, w), dtype='float32')
        for (x1, y1, x2, y2) in boxes:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            bw = max(1, x2 - x1)
            bh = max(1, y2 - y1)
            sigma = max(bw, bh) / 2.0
            # create gaussian
            ys = np.arange(0, h)
            xs = np.arange(0, w)
            ys = ys[:, None]
            gaussian = np.exp(-(((xs - cx) ** 2) + ((ys - cy) ** 2)) / (2 * sigma * sigma))
            heat += gaussian
        # normalize
        if heat.max() > 0:
            heat = heat / heat.max()
        return heat

    def apply_augmentations(self, image, aug_count=2):
        """Return list of augmented images (as numpy arrays). If albumentations is
        available use a small pipeline; otherwise return resized originals.
        """
        try:
            import albumentations as A
            import numpy as np
            aug = A.Compose([
                A.Rotate(limit=20, p=0.5),
                A.RandomBrightnessContrast(p=0.5),
                A.JpegCompression(quality_lower=60, quality_upper=100, p=0.5),
                A.HorizontalFlip(p=0.5)
            ])
            outs = []
            for _ in range(aug_count):
                r = aug(image=image)['image']
                outs.append(r)
            return outs
        except Exception as e:
            # fallback: simple flips and identity
            import numpy as np
            outs = []
            for i in range(aug_count):
                if i % 2 == 0:
                    outs.append(image[:, ::-1, :].copy())
                else:
                    outs.append(image.copy())
            return outs

    def process(self):
        self.setup_directories()
        videos = self.discover_videos()
        splits = self.split_videos(videos)

        manifests = {}
        for split_name, items in splits.items():
            processed = []
            for video_path, label in tqdm(items, desc=f"Processing {split_name}"):
                # derive video id-friendly folder name
                video_id = video_path.stem
                frames_dir = self.output_dir / split_name / label / video_id
                num = self.extract_frames(video_path, frames_dir)
                if num > 0:
                    # optionally run face detection, generate crops, augmentations and heatmaps
                    if self.detect or self.augment or self.heatmap:
                        import cv2
                        import numpy as np

                        crops_dir = frames_dir / 'crops'
                        heat_dir = frames_dir / 'heatmaps'
                        if self.save_crops:
                            crops_dir.mkdir(parents=True, exist_ok=True)
                        if self.heatmap:
                            heat_dir.mkdir(parents=True, exist_ok=True)

                        frame_files = sorted(frames_dir.glob('*.jpg'))
                        for fidx, fp in enumerate(frame_files):
                            img = cv2.imread(str(fp))
                            if img is None:
                                continue
                            boxes = self.detect_faces(img)
                            # heatmap
                            if self.heatmap:
                                heat = self._make_heatmap(img.shape, boxes)
                                heat_img = (np.clip(heat, 0, 1) * 255).astype('uint8')
                                heat_path = heat_dir / f"heat_{fp.name}"
                                cv2.imwrite(str(heat_path), heat_img)

                            # crops and augmentations
                            for bidx, (x1, y1, x2, y2) in enumerate(boxes):
                                if self.save_crops:
                                    crop = img[y1:y2, x1:x2]
                                    if crop.size == 0:
                                        continue
                                    try:
                                        crop = cv2.resize(crop, (self.face_size, self.face_size))
                                    except Exception:
                                        pass
                                    crop_name = f"crop_{fidx:05d}_{bidx:02d}.jpg"
                                    cv2.imwrite(str(crops_dir / crop_name), crop)

                                    if self.augment:
                                        aug_imgs = self.apply_augmentations(crop, aug_count=self.aug_count)
                                        for ai, aimg in enumerate(aug_imgs):
                                            a_name = f"crop_{fidx:05d}_{bidx:02d}_aug{ai}.jpg"
                                            # albumentations returns numpy arrays
                                            cv2.imwrite(str(crops_dir / a_name), aimg)

                    processed.append({
                        'dataset': 'generic',
                        'split': split_name,
                        'video_path': str(video_path),
                        'frames_dir': str(frames_dir.relative_to(self.output_dir)),
                        'label': label,
                        'num_frames': num,
                    })
                else:
                    logging.warning(f"No frames for {video_path}")

            # write manifest
            manifest_path = self.output_dir / f"{split_name}_manifest.csv"
            with open(manifest_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=['dataset', 'split', 'video_path', 'frames_dir', 'label', 'num_frames']
                )
                writer.writeheader()
                for r in processed:
                    writer.writerow(r)

            manifests[split_name] = manifest_path
            logging.info(f"Created manifest: {manifest_path}")

        logging.info("Preprocessing finished.")
        return manifests


def parse_args():
    p = argparse.ArgumentParser(description="Generalized preprocessing for .mp4 datasets")
    p.add_argument('inputs', nargs='+', help='One or more input directories containing videos or label subfolders')
    p.add_argument('--output', '-o', default='data/processed/preprocess_final', help='Output directory')
    p.add_argument('--fps', type=float, default=1.0, help='Frames per second to extract (e.g. 1.0)')
    p.add_argument('--exts', nargs='+', default=['.mp4'], help='Video extensions to include')
    p.add_argument('--splits', nargs=3, type=float, default=[0.6, 0.2, 0.2], help='Train/test/val ratios (must sum to 1)')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--no-per-label-split', dest='per_label_split', action='store_false', help='Do NOT split per label; split globally')
    p.add_argument('--max-per-label', type=int, default=None, help='Limit videos per label (for quick runs)')
    p.add_argument('--recursive', dest='recursive', action='store_true')
    p.add_argument('--non-recursive', dest='recursive', action='store_false')
    p.add_argument('--detect', action='store_true', help='Enable face detection and cropping')
    p.add_argument('--augment', action='store_true', help='Enable augmentations on detected face crops')
    p.add_argument('--aug-count', type=int, default=2, help='Number of augmentations per crop')
    p.add_argument('--heatmap', action='store_true', help='Generate heatmaps for face regions')
    p.add_argument('--face-size', type=int, default=224, help='Resize face crops to this size')
    p.add_argument('--no-save-crops', dest='save_crops', action='store_false', help='Do not save face crop images')
    p.set_defaults(recursive=True)
    return p.parse_args()


def main():
    setup_logging()
    args = parse_args()

    inputs = [Path(x) for x in args.inputs]
    out = Path(args.output)
    splits = tuple(args.splits)
    if abs(sum(splits) - 1.0) > 1e-6:
        logging.error("Splits must sum to 1.0")
        return

    pre = PreprocessFinal(
        input_paths=inputs,
        output_dir=out,
        frames_per_second=args.fps,
        exts=args.exts,
        splits=splits,
        seed=args.seed,
        per_label_split=args.per_label_split,
        max_per_label=args.max_per_label,
        recursive=args.recursive,
        detect=args.detect,
        augment=args.augment,
        aug_count=args.aug_count,
        heatmap=args.heatmap,
        face_size=args.face_size,
        save_crops=args.save_crops,
    )

    pre.process()


if __name__ == '__main__':
    main()
