MiSTercade V2 builds on the venerable MiSTercade V1. This time, it uses Direct Video (HDMI DAC) to produce analog video.

There's an optional Analog DAC accessory to restore dual audio and video output (HDMI + analog video), that will be available in the future.

These INI files are designed for the standard Direct Video use, which requires the HDMI jumper and doesn't allow for simultaneous HDMI and analog audio and video output.

## Key Settings
```ini
vga_mode=rgb 
direct_video=1 ; This is required unless you're using the IO DAC modules for analog audio and video.
composite_sync=1
player_1_controller=usb-1.3/input0 ; Ensures player 1 controls are always assigned to player 1
player_2_controller=usb-1.4/input0 ; Ensures player 2 controls are always assigned to player 2
```

## Recommended Settings
* disable_autofire=0 ; If you're using the down + Start button combo for OSD, autofire isn't very useful. Set this to "1" if you use the remote to activate menu and unbind the menu button combo.
* video_info=0 ; Disable resolution info at each resolution change
* controller_info=0 ; Disable controller mapping pop-up at each core launch

```ini
[Menu]
video_mode=320,240,60
vga_scaler=1
```
^ Add this to the bottom of your MiSTer.ini file if you want to see scripts and wallpaper at the main menu. NOTE: Disables HDMI video out at the main menu.
