# placr
Script for /r/place, the reddit april fools experiment for 2017.

It can draw text on the canvas, and it automatically detects portions already drawn,
so you can start and stop it at will.  
You can also run it in a loop to protect text already drawn
(it will fix any corruptions without wasting time on repainting already correct pixels).

#### Pull requests welcome!

### Usage
0. Install requests (`pip3 install requests pillow toml`)
1. Edit `config.toml` with your credentials and drawing settings.
2. Run placr.py
### Requirements
`requests`, `pillow`, `toml`
### TODO
- [x] Text drawing
- [x] Multiple account support
- [ ] Color filling
- [ ] Image drawing

### Legal
The FontStruction “3 by 5 Pixel Font” (https://fontstruct.com/fontstructions/show/716744) by “asciimario” is licensed under a Creative Commons Attribution Non-commercial No Derivatives license (http://creativecommons.org/licenses/by-nc-nd/3.0/).
