This section is for the Reflex Prism Digital Video to Analog Video Converter. On a MiSTer it will properly scale any 15khz video to be usable on your CRT Television, and scale any 31khz video to be used on a CRT Computer Monitor (**note:** this cannot be done at the same time).

## Key Settings
```ini
vga_mode=rgb ; The Prism will convert the MiSTer's RGB video to ypbpr or svideo, so keep this set to rgb 
direct_video=2 ; 2 is automatic HDMI/Direct video mode which means you can unplug from the Prism and plug into your HDTV without changing a setting
composite_sync=0 ; Prisms shipped after March 1st 2026 have a hardware sync combiner and don't need the mister to combine the sync.
```

## Recommended Settings
```ini
video_info=0 ; Disable resolution info at each resolution change
controller_info=0 ; Disable controller mapping pop-up at each core launch
```
