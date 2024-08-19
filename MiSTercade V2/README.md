MiSTercade V2 builds on the venerable MiSTercade V1. This time, it uses Direct Video (HDMI DAC) to produce analog video.

There's an optional Analog DAC accessory to restore dual audio and video output (HDMI + analog video), that will be available in the future.

These INI files are designed for the standard Direct Video use, which requires the HDMI jumper and doesn't allow for simultaneous HDMI and analog audio and video output.

# Key Settings
* direct_video=1 ; This is required unless you're using the IO DAC modules for analog audio and video.
* composite_sync=1
* disable_autofire=0 ; If you're using the down + Start button combo for OSD, autofire isn't very useful. Set this to "1" if you use the remote to activate menu and unbind the menu button combo.
