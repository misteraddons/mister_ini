MiSTercade is a love letter that bridges the magic of MiSTer with JAMMA arcade cabinets. These INI files option the basic setups for almost all cabinet types.

MiSTer doesn't offer an easy way to rotate analog video. Like original arcade PCBs, the monitor was intended to be rotated within the cabinet for each game.

You can try enabling vga_scaler and using the built-in core rotation features if you'd like.

## Key Settings
```ini
vga_mode=rgb 
direct_video=0 ; This is required unless you're using the IO DAC modules for analog audio and video.
composite_sync=1
player_1_controller=16D0:10BE.0001 ; Ensures player 1 controls are always assigned to player 1
osd_rotate=0 ; For horizontal monitors
osd_rotate=1 ; for clockwise rotated monitors (older games like Pac-Man)
osd_rotate=2 ; for counter-clockwise rotated monitors (newer games like DoDonPachi)
```

## Recommended Settings
```ini
disable_autofire=0 ; If you're using the down + Start button combo for OSD, autofire isn't very useful. Set this to "1" if you use the remote to activate menu and unbind the menu button combo.
video_info=0 ; Disable resolution info at each resolution change
controller_info=0 ; Disable controller mapping pop-up at each core launch
```

```
[Menu]
video_mode=320,240,60
vga_scaler=1
```
^ Add this to the bottom of your MiSTer.ini file if you want to see scripts and wallpaper at the main menu. NOTE: Disables HDMI video out at the main menu.
