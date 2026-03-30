# to-do

## User interface

### Measurement
- user holds down the trigger at point A and drags the controller to point B
- at A, B midpoint the distance (normalized to real life units) is displayed
- measured imperfection and surrounding area is possibly extracted for later inspection
- [geometry](https://aframe.io/docs/1.3.0/components/geometry.html#built-in-geometries)
- [text](https://aframe.io/docs/1.3.0/components/line.html#sidebar)

### Screenshoting

- user can perform a screenshot (not just the system one)
- screenshot will include all currently active measurement lines
- screenshot format allows for quick translation to on-thread position

## Detailed inspection
- REQUIRES NEW DATA SPECIFICATION
- selected portions of the image can be displayed in bigger detail
- user can adjust the vertical angle of the view

## Inspection video format
- currently the loader expects a single thread cut into individual layers
- suggested new formats include
    - single spiralling unroll
    - layer-split thread with larger ovelap (6mm overlap per 12mm layer)