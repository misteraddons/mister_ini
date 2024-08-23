This section is for IO Direct which uses a full-range 24-bit HDMI DAC to produce pristine and accurate 24-bit RGB video.

Note that you can't use HDMI output simultaneously when you use Direct Video.

Sync-on-green IO board switch:
- YPbPr requires the Sync-on-green switch set to the ON position.
- All other analog video formats require the Sync-on-green switch set to the OFF position.

VGA output is experimental. Most cores work great. Some cores don't have the scandoubler included due to space constraints (PSX, and N64). Still working on the native 480p cores (memtest, ao486, etc.) PC CRT usage via IO Direct requires a Saturn to HD15 cable, only offered on misteraddons.com

## Key Settings
```ini
vga_mode=rgb ; Change this to "ypbpr" for component video, or "svideo" for S-video/composite video.
direct_video=1 ; This is required unless you're using the IO DAC modules for analog audio and video.
composite_sync=1
```

## Recommended Settings
```ini
video_info=0 ; Disable resolution info at each resolution change
controller_info=0 ; Disable controller mapping pop-up at each core launch
```
