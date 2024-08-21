This section is for any GPIO based analog video board, including IO Analog Pro as well as the official MiSTer FPGA IO boards. 

Sync-on-green IO board switch:
- YPbPr requires the Sync-on-green switch set to the ON position.
- All other analog video formats require the Sync-on-green switch set to the OFF position.

HDMI video is set to 1080p.

## Key Settings
* vga_mode=rgb ; Change this to "ypbpr" for component video, or "svideo" for S-video/composite video. 
* direct_video=0
* composite_sync=1

## Recommended Settings
* video_info=0 ; Disable resolution info at each resolution change
* controller_info=0 ; Disable controller mapping pop-up at each core launch

```
[Menu]
video_mode=320,240,60
vga_scaler=1
```
^ Add this to the bottom of your MiSTer.ini file if you want to see scripts and wallpaper at the main menu. NOTE: Disables HDMI video out at the main menu.
