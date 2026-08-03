# OBS setup

## Import
*Scene Collection -> Import...* -> `obs/Smile-Trading-Kit.json` -> select **Smile Trading Kit**. (Start the bridge FIRST - the JSON loads pages from localhost.)

## The two clicks
- **WEBCAM-1** -> pick camera. (Add WEBCAM-2/3/4 for duo/panel.)
- **chat** -> paste your StreamElements/Streamlabs chat-box URL.
To show `smile.co.ke/trading` in a frame instead of a cam: add a Browser source with that URL into the yellow frame.

## Hotkeys
Ctrl+Alt+F1 starting - F2 countdown - F3 live - F4 brb - F5 ending.

## Data on screen
Run `core/run-bridge.bat`. Status: http://localhost:8787. Indices update each minute in US hours, hold the close otherwise.

## Troubleshooting
| symptom | fix |
|---|---|
| blank pages | bridge not running - start run-bridge.bat |
| black box behind a screen | source Custom CSS must contain `body { background-color: rgba(0,0,0,0); }` |
| brand/edits not showing | right-click source -> Refresh cache; ensure bridge running |
| indices show - | expected outside US hours |
| cam doesn't fill frame | right-click WEBCAM -> Transform -> Fit bounds |
