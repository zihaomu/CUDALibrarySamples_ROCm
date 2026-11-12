#!/usr/bin/env python3
"""Observe regional-minima priority flood against frozen original NPP products."""
import heapq
import json
from pathlib import Path
import numpy as np
from scipy import ndimage
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from image_watershed_research import NATIVE, SIZES

CASES = ['CT_skull_512x512_8u_Gray.raw', 'Lena_512x512_8u_Gray.raw']
REPORT = ROOT / 'migration/reports/image-watershed-immersion-research.json'


def regional_minima(image):
    h, w = image.shape; flat = image.ravel()
    lower = ndimage.minimum_filter(image, size=3, mode='constant', cval=255)
    seeds = np.full(h * w, -1, dtype=np.int32)
    for value in np.unique(image):
        labels, count = ndimage.label(image == value,
                                        structure=np.ones((3, 3), dtype=np.uint8))
        if not count:
            continue
        good = np.ones(count + 1, dtype=bool); good[0] = False
        bad = np.unique(labels[(labels > 0) & (lower < value)])
        good[bad] = False
        positions = np.flatnonzero(good[labels.ravel()])
        if not len(positions):
            continue
        min_index = np.full(count + 1, h * w, dtype=np.int32)
        np.minimum.at(min_index, labels.ravel()[positions], positions)
        seeds[positions] = min_index[labels.ravel()[positions]]
    return seeds


def priority_flood(image, seeds):
    h, w = image.shape; n = h * w; pixels = image.ravel()
    level = np.full(n, 256, dtype=np.int16)
    distance = np.full(n, np.iinfo(np.int32).max, dtype=np.int32)
    root = np.full(n, n, dtype=np.int32)
    queue = []
    for p in np.flatnonzero(seeds >= 0):
        r = int(seeds[p]); v = int(pixels[p])
        level[p] = v; distance[p] = 0; root[p] = r
        queue.append((v, 0, r, int(p)))
    heapq.heapify(queue)
    pops = 0; updates = 0
    while queue:
        lv, dist, r, p = heapq.heappop(queue); pops += 1
        if lv != level[p] or dist != distance[p] or r != root[p]:
            continue
        y, x = divmod(p, w)
        for dy in (-1, 0, 1):
            yy = y + dy
            if yy < 0 or yy >= h:
                continue
            for dx in (-1, 0, 1):
                xx = x + dx
                if (dx == 0 and dy == 0) or xx < 0 or xx >= w:
                    continue
                q = yy * w + xx
                next_level = max(lv, int(pixels[q]))
                next_distance = dist + 1 if next_level == lv else 0
                if (next_level, next_distance, r) < (int(level[q]), int(distance[q]), int(root[q])):
                    level[q] = next_level; distance[q] = next_distance; root[q] = r
                    heapq.heappush(queue, (next_level, next_distance, r, q))
                    updates += 1
    if np.any(root == n):
        raise ValueError('priority flood left unlabeled pixels')
    return root.reshape(h, w), pixels[root].reshape(h, w), dict(pops=pops, updates=updates,
        regional_minima_pixels=int(np.count_nonzero(seeds >= 0)),
        regional_minima_count=int(np.unique(seeds[seeds >= 0]).size))


def main():
    rows = []
    for name in CASES:
        w, h = SIZES[name]
        source = ROOT / 'NPP/watershedSegmentation/images' / name
        native_dir = ROOT / NATIVE['NPP']
        native_manifest = json.loads((native_dir / 'manifest.json').read_text())
        native = ROOT / native_manifest['raw_artifact_dir'] / 'outputs/images' / ('Segmented_' + name)
        e = Experiment('I3', 'watershed-regional-minima-priority-flood-vs-original',
                       'CPU-research', case=name,
                       sources=[__file__, ROOT / 'tools/moat/image_watershed_research.py',
                                source, native, native_dir / 'run.json'])
        image = np.fromfile(source, dtype=np.uint8).reshape(h, w)
        native_pixels = np.fromfile(native, dtype=np.uint8).reshape(h, w)
        seeds = regional_minima(image)
        roots, segmentation, stats = priority_flood(image, seeds)
        equal = segmentation == native_pixels
        metrics = dict(image=name, width=w, height=h, source_sha256=digest(source),
                       native_sha256=digest(native),
                       equal_fraction=float(np.mean(equal)),
                       mean_abs=float(np.mean(np.abs(segmentation.astype(np.int16) -
                                                     native_pixels.astype(np.int16)))),
                       mismatch_pixels=int(np.count_nonzero(~equal)), **stats)
        (e.path / 'segmentation.raw').write_bytes(segmentation.tobytes())
        (e.path / 'roots.u32').write_bytes(roots.astype('<u4').tobytes())
        write(e.path / 'research.json', metrics)
        metrics['evidence'] = e.finish('OBSERVED', dict(status='OBSERVED',
            checks=[dict(check='all-pixels-assigned', passed=True)]), metrics=metrics)
        rows.append(metrics); write(REPORT, dict(status='OBSERVED', rows=rows,
            scope='CPU research only; no HIP qualification or NPP equivalence'))
        record('I3', 'watershed 区域极小值+优先级浸没 CPU 候选 '+name+
               ' 对原生分割像素一致率 '+str(round(metrics['equal_fraction'], 5))+
               '；仅算法研究，未改GPU或状态。', [metrics['evidence']])
        print(name, metrics['equal_fraction'], stats, flush=True)


if __name__ == '__main__':
    main()
