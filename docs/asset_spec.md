# Asset specification

## `single_layer.avi`
Original video of a single layer, rotation side-effect removed. Features the entire layer between two shifts.

## `intra.mp4`

Processed single layer, featuring intra frames only. Optimized for ~O(1) seek.


## Demuxed
Outputs of `scripts/preprocess.py`. Hierarchy thread->layer->frame. Individual frames are fully encoded. Load time ~6000 frames/second.

## Unrolled
Side-by-side video with "baked-in" delay between the two sections. Overlap is specified in pixels. The delay is specified in miliseconds. 

## Delayed

Side-by-side video with baked in delay between the two sections. No overlap included. 