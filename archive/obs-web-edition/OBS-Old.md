<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OBS Studio - Web Edition</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="three-container"></div>
    
    <div id="hiddenMediaContainer" style="display:none;"></div>

    <svg style="width:0;height:0;position:absolute;" aria-hidden="true" focusable="false">
        <filter id="chroma-key-white">
            <feColorMatrix in="SourceGraphic" type="matrix" values="
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 0 0
                -1 -1 -1 0 2.9" result="whiteMask" />
            <feComposite in="SourceGraphic" in2="whiteMask" operator="in" />
        </filter>
    </svg>

    <nav class="obs-menu" id="topNav">
        <div class="menu-item">
            <span class="menu-title">File</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Show Recordings</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Remux Recordings</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row" id="menuSettingsBtn"><span class="menu-icon"></span><span class="menu-text">Settings</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Show Settings Folder</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Show Profile Folder</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Exit</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Edit</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Undo Hide 'Window Capture' in 'Scene'</span><span class="menu-shortcut">Ctrl+Z</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Redo</span><span class="menu-shortcut">Ctrl+Shift+Z</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Copy</span><span class="menu-shortcut">Ctrl+C</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Paste (Reference)</span><span class="menu-shortcut">Ctrl+V</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Paste (Duplicate)</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Copy Filters</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Paste Filters</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Transform</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Order</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Preview Scaling</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Lock Preview</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Advanced Audio Properties</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">View</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Reset UI</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Fullscreen Interface</span><span class="menu-shortcut">F11</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Scene List Mode</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Dock Toolbars</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Source Toolbar</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Source Icons</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Status Bar</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row open-stats-btn"><span class="menu-icon"></span><span class="menu-text">Stats</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Open Multiview</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Always On Top</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Docks</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Lock Docks</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Full-Height Docks</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Reset Docks</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Custom Browser Docks</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Scenes</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Sources</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Audio Mixer</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Scene Transitions</span></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Controls</span></div>
                <div class="dropdown-row open-stats-btn"><span class="menu-icon"></span><span class="menu-text">Stats</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Profile</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">New...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Duplicate...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Rename...</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Remove</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Import...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Export...</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Untitled</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Scene Collection</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">New...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Duplicate...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Rename...</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Remove</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Import...</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Export...</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Check for Missing Files</span></div>
                <div class="dropdown-row disabled"><span class="menu-icon"></span><span class="menu-text">Reset Base Resolution</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"><i class="fas fa-check"></i></span><span class="menu-text">Untitled</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Tools</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Auto-Configuration Wizard</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Plugin Manager</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Captions (Experimental)</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Automatic Scene Switcher</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Output Timer</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Scripts</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">WebSocket Server Settings</span></div>
            </div>
        </div>

        <div class="menu-item">
            <span class="menu-title">Help</span>
            <div class="dropdown-content">
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Help Portal</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Visit Website</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Join Discord Server</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Log Files</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Crash Reports</span><span class="menu-arrow"><i class="fas fa-caret-right"></i></span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Check File Integrity</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Check For Updates</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Restart in Safe Mode</span></div>
                <div class="menu-separator"></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">What's New</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">Release Notes</span></div>
                <div class="dropdown-row"><span class="menu-icon"></span><span class="menu-text">About</span></div>
            </div>
        </div>
    </nav>

    <div class="obs-workspace">

        <div class="obs-preview-container">
            <div class="preview-layout-wrapper">
                
                <div class="studio-pane" id="previewPane">
                    <div class="studio-pane-header" id="previewPaneHeader" style="display:none;">PREVIEW</div>
                    <div class="preview-wrapper" id="previewWrapper" style="position: relative;">
                        <canvas id="liveRenderCanvas" width="1920" height="1080" style="display:none;"></canvas>
                        
                        <canvas id="obsCanvas" width="1920" height="1080"></canvas>
                        
                        <div id="domOverlayContainer" style="position: absolute; pointer-events: none; overflow: hidden; transform-origin: 0 0;"></div>
                        
                        <canvas id="obsCanvasTop" width="1920" height="1080"></canvas>
                        
                        <div class="preview-placeholder" id="previewPlaceholder">No Source Active</div>
                    </div>
                </div>

                <div class="studio-controls" id="studioControls" style="display: none;">
                    <button class="obs-btn" id="studioTransitionBtn" style="height: 40px; font-weight: bold; background-color: #1e50a0; font-size: 14px;">Transition</button>
                    <div class="studio-quick-transitions">
                        <button class="obs-btn" id="studioCutBtn">Cut</button>
                        <button class="obs-btn" id="studioFadeBtn">Fade</button>
                    </div>
                    <div class="studio-duration" style="text-align: center; color: #aaa; width: 100%;">
                        <span style="font-size:11px; display:block; margin-bottom:4px;">Duration</span>
                        <div style="display:flex; align-items:center; gap:5px; justify-content:center;">
                            <input type="number" id="studioDurationInput" value="300" class="obs-input-small" style="width:60px;"> ms
                        </div>
                    </div>
                    <div class="studio-tbar-container">
                         <div class="studio-tbar-track">
                             <input type="range" id="studioTBar" min="0" max="100" value="0" class="studio-tbar">
                         </div>
                    </div>
                </div>

                <div class="studio-pane" id="programPane" style="display: none;">
                    <div class="studio-pane-header">PROGRAM</div>
                    <div class="preview-wrapper" id="programWrapper" style="position: relative; background-color: #000;">
                        <canvas id="programCanvas" width="1920" height="1080" style="max-width: 100%; max-height: 100%; object-fit: contain; aspect-ratio: 16/9; background-color: transparent; box-shadow: 0 0 15px rgba(0,0,0,0.8); cursor: default; position: absolute;"></canvas>
                        <div class="preview-placeholder" id="programPlaceholder" style="display:none; z-index: 10;">Live Output</div>
                    </div>
                </div>

            </div>
            
            <div class="media-controls-bar" id="textControlsBar" style="display: none;">
                <span id="textSourceName" style="font-weight: 600; width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Text Source</span>
                <button class="text-icon-btn" id="textPropertiesBtn"><i class="fas fa-cog"></i> Properties</button>
                <button class="text-icon-btn" id="textFiltersBtn"><i class="fas fa-sliders-h"></i> Filters</button>
                <div class="media-divider"></div>
                <span style="color:#aaa;">Quick Edit:</span>
                <input type="text" id="textInputSource" placeholder="Enter text here..." class="obs-input" style="width: 140px;">
                <input type="color" id="textColorSource" value="#ffffff" class="obs-color">
                <select id="textFontSource" class="obs-select" style="width: 120px;">
                    <option value="Arial">Arial</option>
                    <option value="Courier New">Courier New</option>
                    <option value="Times New Roman">Times New Roman</option>
                    <option value="Impact">Impact</option>
                    <option value="Tahoma">Tahoma</option>
                    <option value="Verdana">Verdana</option>
                    <option value="Georgia">Georgia</option>
                    <option value="Comic Sans MS">Comic Sans MS</option>
                    <option value="Trebuchet MS">Trebuchet MS</option>
                    <option value="Arial Black">Arial Black</option>
                    <option value="Lucida Console">Lucida Console</option>
                </select>
                <input type="number" id="textSizeSource" value="48" class="obs-input-small"> px
            </div>

            <div class="media-controls-bar" id="mediaControlsBar" style="display: none;">
                <span id="mediaSourceName" style="font-weight: 600; width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Media Source</span>
                <button class="text-icon-btn" id="mediaPropertiesBtn"><i class="fas fa-cog"></i> Properties</button>
                <button class="text-icon-btn" id="mediaFiltersBtn"><i class="fas fa-sliders-h"></i> Filters</button>
                <div class="media-divider"></div>
                <button class="obs-btn-square" id="mediaPlayBtn"><i class="fas fa-play"></i></button>
                <button class="obs-btn-square" id="mediaPauseBtn"><i class="fas fa-pause"></i></button>
                <button class="obs-btn-square" id="mediaStopBtn"><i class="fas fa-stop"></i></button>
                <input type="range" id="mediaSeek" min="0" max="100" value="0" class="obs-slider" style="flex-grow: 1; margin: 0 15px;">
                <span id="mediaTime">00:00:00 / 00:00:00</span>
            </div>

            <div class="media-controls-bar" id="browserControlsBar" style="display: none;">
                <span id="browserSourceName" style="font-weight: 600; width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Browser Source</span>
                <button class="text-icon-btn" id="browserBarPropertiesBtn"><i class="fas fa-cog"></i> Properties</button>
                <button class="text-icon-btn" id="browserFiltersBtn"><i class="fas fa-sliders-h"></i> Filters</button>
                <button class="text-icon-btn" id="browserInteractBtn"><i class="fas fa-hand-pointer"></i> Interact</button>
                <div class="media-divider"></div>
                <button class="obs-btn-square" id="browserBackBtn"><i class="fas fa-arrow-left"></i></button>
                <button class="obs-btn-square" id="browserForwardBtn"><i class="fas fa-arrow-right"></i></button>
                <button class="obs-btn-square" id="browserRefreshBtn"><i class="fas fa-redo"></i></button>
                <div class="media-divider"></div>
                <label style="display: flex; align-items: center; gap: 4px; cursor: pointer; margin-left: 5px; color: #dfdfdf;">
                    <input type="checkbox" id="browserTransparentBarCheck" checked> Transparent
                </label>
                <span style="margin-left: 15px; font-weight: bold; color: #aaa;">Zoom:</span>
                <input type="range" id="browserZoomSlider" min="10" max="300" value="100" class="obs-slider" style="flex-grow: 1; margin: 0 15px;">
                <span id="browserZoomText" style="width: 40px;">100%</span>
            </div>

        </div>

        <div class="obs-docks" id="mainDocksContainer">
            <div class="dock" id="dock-scenes" data-order="1">
                <div class="dock-header">
                    <span>Scenes</span>
                    <span style="cursor: pointer; color: #888;" class="undock-btn"><i class="far fa-clone"></i></span>
                </div>
                <div class="dock-content list-box" id="scenesList">
                    </div>
                <div class="dock-toolbar">
                    <button class="icon-btn" id="addSceneBtn"><i class="fas fa-plus"></i></button>
                    <button class="icon-btn" id="removeSceneBtn"><i class="fas fa-trash-alt"></i></button>
                    <button class="icon-btn" id="openSceneTransitionsBtn"><i class="fas fa-magic"></i></button>
                    <button class="icon-btn" id="moveSceneUpBtn"><i class="fas fa-chevron-up"></i></button>
                    <button class="icon-btn" id="moveSceneDownBtn"><i class="fas fa-chevron-down"></i></button>
                </div>
            </div>

            <div class="dock" id="dock-sources" data-order="2">
                <div class="dock-header">
                    <span>Sources</span>
                    <span style="cursor: pointer; color: #888;" class="undock-btn"><i class="far fa-clone"></i></span>
                </div>
                <div class="dock-content list-box" id="sourcesList"></div>
                <div class="dock-toolbar" style="position: relative;">
                    <button class="icon-btn" id="addSourceBtn"><i class="fas fa-plus"></i></button>
                    <button class="icon-btn" id="removeSourceBtn"><i class="fas fa-trash-alt"></i></button>
                    <button class="icon-btn" id="openSourcePropertiesBtn"><i class="fas fa-cog"></i></button>
                    <button class="icon-btn" id="moveSourceUpBtn"><i class="fas fa-chevron-up"></i></button>
                    <button class="icon-btn" id="moveSourceDownBtn"><i class="fas fa-chevron-down"></i></button>
                    
                    <div class="context-menu" id="addSourceMenu">
                        <div class="context-item" data-action="audio-app"><i class="fas fa-volume-up" style="width:20px;"></i> Application Audio Capture (BETA)</div>
                        <div class="context-item" data-action="audio-in"><i class="fas fa-microphone" style="width:20px;"></i> Audio Input Capture</div>
                        <div class="context-item" data-action="audio-out"><i class="fas fa-headphones" style="width:20px;"></i> Audio Output Capture</div>
                        <div class="context-item" data-action="browser"><i class="fas fa-globe" style="width:20px;"></i> Browser</div>
                        <div class="context-item" data-action="color"><i class="fas fa-palette" style="width:20px;"></i> Color Source</div>
                        <div class="context-item" data-action="display"><i class="fas fa-desktop" style="width:20px;"></i> Display Capture</div>
                        <div class="context-item disabled"><i class="fas fa-gamepad" style="width:20px;"></i> Game Capture</div>
                        <div class="context-item" data-action="image"><i class="fas fa-image" style="width:20px;"></i> Image</div>
                        <div class="context-item" data-action="slideshow"><i class="fas fa-images" style="width:20px;"></i> Image Slide Show</div>
                        <div class="context-item" data-action="media"><i class="fas fa-play-circle" style="width:20px;"></i> Media Source</div>
                        <div class="context-item" data-action="scene"><i class="fas fa-film" style="width:20px;"></i> Scene</div>
                        <div class="context-item" data-action="text"><i class="fas fa-font" style="width:20px;"></i> Text (GDI+)</div>
                        <div class="context-item" data-action="video-device"><i class="fas fa-camera" style="width:20px;"></i> Video Capture Device</div>
                        <div class="context-item" data-action="vlc"><i class="fas fa-play-circle" style="width:20px;"></i> VLC Video Source</div>
                        <div class="context-item" data-action="window"><i class="far fa-window-maximize" style="width:20px;"></i> Window Capture</div>
                        <div class="context-separator"></div>
                        <div class="context-item disabled"><i class="fas fa-folder" style="width:20px;"></i> Group</div>
                        <div class="context-separator"></div>
                        <div class="context-item disabled">Deprecated <i class="fas fa-caret-right" style="margin-left:auto;"></i></div>
                    </div>
                </div>
            </div>

            <div class="dock dock-wide" id="dock-mixer" data-order="3">
                <div class="dock-header">
                    <span>Audio Mixer</span>
                    <span style="cursor: pointer; color: #888;" class="undock-btn"><i class="far fa-clone"></i></span>
                </div>
                <div class="dock-content audio-mixer" id="audioMixerContainer"></div>
                <div class="dock-toolbar">
                    <button class="icon-btn"><i class="fas fa-cog"></i></button>
                    <button class="icon-btn"><i class="fas fa-ellipsis-v"></i></button>
                </div>
            </div>

            <div class="dock" id="dock-transitions" data-order="4">
                <div class="dock-header">
                    <span>Scene Transitions</span>
                    <span style="cursor: pointer; color: #888;" class="undock-btn"><i class="far fa-clone"></i></span>
                </div>
                <div class="dock-content transitions-box">
                    <select class="obs-select" id="dockTransitionSelect">
                        <option value="none">Cut</option>
                        <option value="fade">Fade</option>
                        <option value="slide-left">Slide Left</option>
                        <option value="slide-right">Slide Right</option>
                        <option value="slide-up">Slide Up</option>
                        <option value="slide-down">Slide Down</option>
                        <option value="spin">Spin</option>
                        <option value="melt">Melt</option>
                        <option value="fall-apart">Fall Apart</option>
                        <option value="zoom-in">Zoom In</option>
                        <option value="circle-crop">Circle Reveal</option>
                    </select>
                    <div class="duration-box">
                        <span>Duration</span>
                        <div style="display:flex; align-items:center; gap: 5px;">
                            <input type="number" id="dockTransitionDuration" value="500" class="obs-input-small"> ms
                        </div>
                    </div>
                </div>
                <div class="dock-toolbar" style="justify-content: flex-end;">
                    <button class="icon-btn"><i class="fas fa-plus"></i></button>
                    <button class="icon-btn"><i class="fas fa-trash-alt"></i></button>
                    <button class="icon-btn"><i class="fas fa-ellipsis-v"></i></button>
                </div>
            </div>

            <div class="dock controls-dock" id="dock-controls" data-order="5">
                <div class="dock-header">
                    <span>Controls</span>
                    <span style="cursor: pointer; color: #888;" class="undock-btn"><i class="far fa-clone"></i></span>
                </div>
                <div class="dock-content controls-box">
                    <button class="obs-btn">Start Streaming</button>
                    <button class="obs-btn" id="startBtn">Start Recording</button>
                    <button class="obs-btn hidden" id="stopBtn">Stop Recording</button>
                    <div style="display: flex; gap: 4px;">
                        <button class="obs-btn" style="flex:1;" id="openEditorBtn">Recordings & Editor</button>
                        <button class="obs-btn" style="width: 26px; padding: 0; flex-shrink: 0;" id="downloadRecordingBtn" disabled title="Download Latest Recording"><i class="fas fa-download"></i></button>
                    </div>
                    <button class="obs-btn" id="studioModeToggleBtn">Studio Mode</button>
                    <button class="obs-btn" id="settingsBtn">Settings</button>
                </div>
            </div>
        </div>
    </div>

    <footer class="obs-status">
        <div class="status-left" id="statusBar">Ready</div>
        <div class="status-right">
            <span class="status-item"><i class="fas fa-signal"></i></span>
            <span class="status-item" id="recordingTime"><i class="fas fa-circle" style="color:#888;"></i> 00:00:00</span>
            <span class="status-item"><i class="fas fa-circle" style="color:#888;"></i> 00:00:00</span>
            <span class="status-item">CPU: <span id="footerCpu">0.8</span>%</span>
            <span class="status-item"><span id="footerFps">60.00</span> / 60.00 FPS</span>
        </div>
    </footer>

    <input type="file" id="imageInput" accept="image/*" style="display:none;">
    <input type="file" id="slideshowInput" accept="image/*" multiple style="display:none;">
    <input type="file" id="slideshowAddInput" accept="image/*" multiple style="display:none;">
    <input type="file" id="mediaInput" accept="video/*,audio/*" style="display:none;">
    <input type="file" id="propFileInput" accept="video/*,audio/*" style="display:none;">
    <input type="file" id="browserFileInput" accept=".html,.htm" style="display:none;">
    <input type="file" id="imageFileInput" accept="image/*" style="display:none;">
    <input type="file" id="advEditorMediaInput" accept="video/*,image/*,audio/*" multiple style="display:none;">

    <div class="context-menu" id="audioMixerContextMenu" style="z-index: 5000;">
        <div class="context-item" id="ctxLockVolume"><i class="fas fa-check" style="visibility:hidden; width: 16px;"></i> Lock Volume</div>
        <div class="context-item" id="ctxUnhideAll" style="padding-left: 38px;">Unhide All</div>
        <div class="context-item" id="ctxHide" style="padding-left: 38px;">Hide</div>
        <div class="context-item" id="ctxRename" style="padding-left: 38px;">Rename...</div>
        <div class="context-separator"></div>
        <div class="context-item" id="ctxCopyFilters" style="padding-left: 38px; color: #888;">Copy Filters</div>
        <div class="context-item" id="ctxPasteFilters" style="padding-left: 38px; color: #888;">Paste Filters</div>
        <div class="context-separator"></div>
        <div class="context-item" id="ctxVerticalLayout"><i class="fas fa-check" style="visibility:hidden; width: 16px;"></i> Vertical Layout</div>
        <div class="context-separator"></div>
        <div class="context-item" id="ctxFilters" style="padding-left: 38px;">Filters</div>
        <div class="context-item" id="ctxProperties" style="padding-left: 38px;">Properties</div>
        <div class="context-item" id="ctxAdvancedProperties" style="padding-left: 38px;">Advanced Audio Properties</div>
    </div>

    <div class="modal" id="audioFiltersModal">
        <div class="modal-content obs-window" style="width: 850px; max-width: 95vw; height: 600px;">
            <div class="window-header">
                <span id="audioFiltersTitle">Filters for 'Desktop Audio'</span>
                <button class="close-btn" id="closeAudioFiltersBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; gap: 0; padding: 0; height: calc(100% - 40px);">
                <div style="width: 250px; background-color: #1d1f26; border-right: 1px solid #3c404d; display: flex; flex-direction: column;">
                    <div style="padding: 10px; color: #dfdfdf; font-size: 13px;">Audio Filters</div>
                    <div class="list-box" id="audioFiltersList" style="flex: 1; overflow-y: auto; padding: 0 10px;">
                        </div>
                    <div class="dock-toolbar" style="border-top: 1px solid #3c404d; padding: 10px; background: #272a33; position: relative;">
                        <button class="icon-btn" id="addAudioFilterBtn"><i class="fas fa-plus"></i></button>
                        <button class="icon-btn" id="removeAudioFilterBtn"><i class="fas fa-trash-alt"></i></button>
                        <button class="icon-btn" id="moveAudioFilterUpBtn"><i class="fas fa-chevron-up"></i></button>
                        <button class="icon-btn" id="moveAudioFilterDownBtn"><i class="fas fa-chevron-down"></i></button>
                        
                        <div class="context-menu" id="addAudioFilterMenu" style="bottom: 100%; left: 10px;">
                            <div class="context-item" data-filter="3-Band Equalizer">3-Band Equalizer</div>
                            <div class="context-item" data-filter="Compressor">Compressor</div>
                            <div class="context-item" data-filter="Expander">Expander</div>
                            <div class="context-item" data-filter="Gain">Gain</div>
                            <div class="context-item" data-filter="Invert Polarity">Invert Polarity</div>
                            <div class="context-item" data-filter="Limiter">Limiter</div>
                            <div class="context-item" data-filter="Noise Gate">Noise Gate</div>
                            <div class="context-item" data-filter="Noise Suppression">Noise Suppression</div>
                            <div class="context-item" data-filter="Upward Compressor">Upward Compressor</div>
                        </div>
                    </div>
                </div>
                <div id="audioFilterSettingsContainer" style="flex: 1; padding: 20px; overflow-y: auto; background-color: #272a33;">
                    <div id="audioFilterSettingsContent">
                        <div id="noFilterSelected" style="color: #888; text-align: center; margin-top: 100px;">Please select a filter to view its properties.</div>
                        </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 10px; border-top: 1px solid #3c404d; background: #272a33;">
                <button class="obs-btn" id="audioFilterDefaultsBtn" style="width: 80px;">Defaults</button>
                <button class="obs-btn" id="audioFilterCloseBottomBtn" style="width: 80px;">Close</button>
            </div>
        </div>
    </div>

    <div class="modal" id="audioDevicePropertiesModal">
        <div class="modal-content obs-window" style="width: 450px;">
            <div class="window-header">
                <span id="audioDevicePropertiesTitle"><i class="fas fa-cog"></i> Properties</span>
                <button class="close-btn" id="closeAudioDevicePropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 15px;">
                <div class="prop-row">
                    <label class="prop-label">Device</label>
                    <div class="prop-input-container">
                        <select id="audioPropDeviceSelect" class="obs-select">
                            <option value="default">Default</option>
                            <option value="mic1">Microphone (High Definition Audio Device)</option>
                            <option value="line1">Line In (High Definition Audio Device)</option>
                        </select>
                    </div>
                </div>
                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="audioPropUseTimestamps" checked> Use Device Timestamps</label>
                    </div>
                </div>
                <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="audioPropOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="audioPropCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="customAlertModal" style="z-index: 9999;">
        <div class="modal-content obs-window" style="width: 400px; max-width: 90vw;">
            <div class="window-header">
                <span id="customAlertTitle"><i class="fas fa-info-circle"></i> Message</span>
                <button class="close-btn" onclick="document.getElementById('customAlertModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="text-align: center;">
                <p id="customAlertMessage" style="margin-bottom: 20px; line-height: 1.5; color: #dfdfdf;"></p>
                <button class="obs-btn" style="width: 80px; margin: 0 auto;" onclick="document.getElementById('customAlertModal').classList.remove('active')">OK</button>
            </div>
        </div>
    </div>

    <div class="modal" id="colorPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="colorPropertiesTitle"><i class="fas fa-palette"></i> Properties for 'Color Source'</span>
                <button class="close-btn" id="closeColorPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area" style="background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;">
                    <div id="colorPropertiesPreview" style="width: 100%; height: 100%;"></div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Color</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 5px; align-items: center;">
                        <input type="color" id="cpColor" value="#ffffff" class="obs-color" style="width: 100px; height: 26px;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Width</label>
                    <div class="prop-input-container">
                        <input type="number" id="cpWidth" value="1920" class="obs-input" style="width: 100%;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Height</label>
                    <div class="prop-input-container">
                        <input type="number" id="cpHeight" value="1080" class="obs-input" style="width: 100%;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Opacity (Alpha)</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="cpOpacitySlider" min="0" max="100" value="100" class="obs-slider" style="flex: 1;">
                        <input type="number" id="cpOpacityNum" min="0" max="100" value="100" class="obs-input-small"> %
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="cpDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="cpOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="cpCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="imagePropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="imagePropertiesTitle"><i class="fas fa-image"></i> Properties for 'Image'</span>
                <button class="close-btn" id="closeImagePropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area">
                    <img id="imagePropertiesPreview" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="ipLocalFile" checked> Local file</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label" id="ipFileLabel">Image File</label>
                    <div class="prop-input-container" style="display: flex; gap: 5px;">
                        <input type="text" id="ipFilePath" class="obs-input" style="flex: 1;" readonly>
                        <button class="obs-btn" id="ipFileActionBtn" style="width: 80px;">Browse</button>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="ipTransparent"> White to Transparent Background</label>
                        <label><input type="checkbox" id="ipFlipH"> Flip Horizontal</label>
                        <label><input type="checkbox" id="ipFlipV"> Flip Vertical</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Opacity</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="ipOpacitySlider" min="0" max="100" value="100" class="obs-slider" style="flex: 1;">
                        <input type="number" id="ipOpacityNum" min="0" max="100" value="100" class="obs-input-small"> %
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Blend Mode</label>
                    <div class="prop-input-container">
                        <select id="ipBlendMode" class="obs-select">
                            <option value="source-over">Normal</option>
                            <option value="lighter">Add</option>
                            <option value="multiply">Multiply</option>
                            <option value="screen">Screen</option>
                            <option value="overlay">Overlay</option>
                        </select>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="ipDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="ipOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="ipCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="textPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="textPropertiesTitle"><i class="fas fa-font"></i> Properties for 'Text (GDI+)'</span>
                <button class="close-btn" id="closeTextPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">

                <div class="prop-preview-area" style="background-color: #111; padding: 20px;">
                    <canvas id="textPropertiesPreview" style="width: 100%; height: 100%; object-fit: contain;"></canvas>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Font</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 5px;">
                        <select id="tpFont" class="obs-select" style="flex: 1;">
                            <option value="Arial">Arial</option>
                            <option value="Courier New">Courier New</option>
                            <option value="Times New Roman">Times New Roman</option>
                            <option value="Impact">Impact</option>
                            <option value="Tahoma">Tahoma</option>
                            <option value="Verdana">Verdana</option>
                            <option value="Georgia">Georgia</option>
                            <option value="Comic Sans MS">Comic Sans MS</option>
                            <option value="Trebuchet MS">Trebuchet MS</option>
                            <option value="Arial Black">Arial Black</option>
                            <option value="Lucida Console">Lucida Console</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="tpReadFile"> Read from file</label>
                        <input type="file" id="tpFileInput" accept=".txt" style="display: none;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Text</label>
                    <div class="prop-input-container">
                        <textarea id="tpText" class="obs-textarea" style="height: 80px;"></textarea>
                        <div id="tpFileDisplay" style="display:none; align-items:center; gap:5px; margin-top:5px;">
                            <input type="text" id="tpFilePath" class="obs-input" readonly style="flex:1;">
                            <button class="obs-btn" id="tpFileBrowseBtn" style="width:80px;">Browse</button>
                        </div>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="tpAntialiasing" checked> Enable Antialiasing</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Text Transform</label>
                    <div class="prop-input-container">
                        <select id="tpTransform" class="obs-select">
                            <option value="none">None</option>
                            <option value="uppercase">Uppercase</option>
                            <option value="lowercase">Lowercase</option>
                            <option value="startcase">Start Case</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="tpVertical"> Vertical</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Color</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 5px; align-items: center;">
                        <input type="color" id="tpColor" value="#ffffff" class="obs-color" style="width: 100px; height: 26px;">
                        <div id="tpGradientColorContainer" style="display: none; align-items: center; gap: 5px;">
                            <span style="color: #dfdfdf; margin-left: 10px;">Gradient Color:</span>
                            <input type="color" id="tpGradientColor" value="#0000ff" class="obs-color" style="width: 100px; height: 26px;">
                        </div>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Opacity</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="tpOpacitySlider" min="0" max="100" value="100" class="obs-slider" style="flex: 1;">
                        <input type="number" id="tpOpacityNum" min="0" max="100" value="100" class="obs-input-small"> %
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="tpGradient"> Gradient</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Background Color</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 5px; align-items: center;">
                        <input type="color" id="tpBgColor" value="#000000" class="obs-color" style="width: 100px; height: 26px;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Background Opacity</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="tpBgOpacitySlider" min="0" max="100" value="0" class="obs-slider" style="flex: 1;">
                        <input type="number" id="tpBgOpacityNum" min="0" max="100" value="0" class="obs-input-small"> %
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Alignment</label>
                    <div class="prop-input-container">
                        <select id="tpAlign" class="obs-select">
                            <option value="left">Left</option>
                            <option value="center">Center</option>
                            <option value="right">Right</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Vertical Alignment</label>
                    <div class="prop-input-container">
                        <select id="tpValign" class="obs-select">
                            <option value="top">Top</option>
                            <option value="center">Center</option>
                            <option value="bottom">Bottom</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="tpOutline"> Outline</label>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="tpDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="tpOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="tpCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <div class="modal" id="mediaPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="mediaPropertiesTitle"><i class="fas fa-cog"></i> Properties for 'Media Source'</span>
                <button class="close-btn" id="closeMediaPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area">
                    <video id="mediaPropertiesPreview" autoplay loop muted></video>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="propLocalFile" checked> Local File</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label" id="propFileLabel">Local File</label>
                    <div class="prop-input-container" style="display: flex; gap: 5px;">
                        <input type="text" id="propFilePath" class="obs-input" style="flex: 1;" readonly>
                        <button class="obs-btn" id="propFileActionBtn" style="width: 80px;">Browse</button>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="propLoop"> Loop</label>
                        <label><input type="checkbox" id="propRestartActive" checked> Restart playback when source becomes active</label>
                        <label><input type="checkbox" id="propHardwareDecode"> Use hardware decoding when available</label>
                        <label><input type="checkbox" id="propShowNothing" checked> Show nothing when playback ends</label>
                        <label><input type="checkbox" id="propCloseInactive"> Close file when inactive <i class="fas fa-question-circle" style="color: #888;"></i></label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Speed</label>
                    <div class="prop-input-container" style="display: flex; flex-direction: row; gap: 10px; align-items: center; flex-wrap: nowrap;">
                        <input type="range" id="propSpeedSlider" min="1" max="200" value="100" class="obs-slider" style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 4px; white-space: nowrap; flex-shrink: 0;">
                            <input type="number" id="propSpeedInput" value="100" min="1" max="200" class="obs-input-small"> %
                        </div>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">YUV Color Range</label>
                    <div class="prop-input-container">
                        <select id="propYuvRange" class="obs-select">
                            <option value="auto">Auto</option>
                            <option value="partial">Partial/Limited</option>
                            <option value="full">Full</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="propAlpha"> Apply alpha in linear space</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">FFmpeg Options <i class="fas fa-question-circle" style="color: #888;"></i></label>
                    <div class="prop-input-container">
                        <input type="text" id="propFfmpeg" class="obs-input" style="width: 100%;">
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="propDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="propOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="propCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="browserPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="browserPropertiesTitle"><i class="fas fa-globe"></i> Properties for 'Browser'</span>
                <button class="close-btn" id="closeBrowserPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area">
                    <iframe id="browserPropertiesPreview" style="width:100%; height:100%; border:none; pointer-events:none;"></iframe>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="bpLocalFile"> Local file</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label" id="bpFileLabel">URL</label>
                    <div class="prop-input-container" style="display: flex; gap: 5px;">
                        <input type="text" id="bpUrlInput" class="obs-input" style="flex: 1;" value="https://shorturl.at/6QyYn">
                        <button class="obs-btn" id="bpFileActionBtn" style="width: 80px;">Paste</button>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Width</label>
                    <div class="prop-input-container">
                        <input type="number" id="bpWidth" value="800" class="obs-input" style="width: 100%;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Height</label>
                    <div class="prop-input-container">
                        <input type="number" id="bpHeight" value="600" class="obs-input" style="width: 100%;">
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="bpTransparent" checked> White to Transparent background</label>
                        <label><input type="checkbox" id="bpControlAudio"> Control audio via OBS</label>
                        <label><input type="checkbox" id="bpCustomFps"> Use custom frame rate</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Custom CSS</label>
                    <div class="prop-input-container">
                        <textarea id="bpCustomCss" class="obs-textarea">body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }</textarea>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="bpShutdownInactive"> Shutdown source when not visible</label>
                        <label><input type="checkbox" id="bpRefreshActive"> Refresh browser when scene becomes active</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Page permissions</label>
                    <div class="prop-input-container">
                        <select id="bpPermissions" class="obs-select">
                            <option value="read_status">Read access to OBS status information</option>
                            <option value="none">No access to OBS</option>
                            <option value="read_user">Read access to user information</option>
                            <option value="basic">Basic access to OBS (Save replay buffer, etc.)</option>
                            <option value="advanced">Advanced access to OBS</option>
                            <option value="full">Full access to OBS</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <button class="obs-btn" id="bpRefreshCacheBtn" style="width: 200px;">Refresh cache of current page</button>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="bpDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="bpOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="bpCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="slideshowPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="slideshowPropertiesTitle"><i class="fas fa-images"></i> Properties for 'Slide Show'</span>
                <button class="close-btn" id="closeSlideshowPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area">
                    <canvas id="slideshowPropertiesPreview" style="max-width: 100%; max-height: 100%;"></canvas>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Visibility Behavior</label>
                    <div class="prop-input-container">
                        <select id="ssPropVisibility" class="obs-select">
                            <option value="always">Always play even when not visible</option>
                            <option value="stop">Stop when not visible, restart when visible</option>
                            <option value="pause">Pause when not visible, unpause when visible</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Slide Mode</label>
                    <div class="prop-input-container">
                        <select id="ssPropMode" class="obs-select">
                            <option value="auto">Automatic</option>
                            <option value="manual">Manual (Use hotkeys to control slideshow)</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Transition</label>
                    <div class="prop-input-container">
                        <select id="ssPropTransition" class="obs-select">
                            <option value="cut">Cut</option>
                            <option value="fade">Fade</option>
                            <option value="slide">Slide</option>
                            <option value="swipe">Swipe</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Time Between Slides</label>
                    <div class="prop-input-container" style="flex-direction: row; align-items: center; gap: 5px;">
                        <input type="number" id="ssPropTimeBetween" value="2000" class="obs-input" style="flex: 1; width: 100%;"> ms
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Transition Speed</label>
                    <div class="prop-input-container" style="flex-direction: row; align-items: center; gap: 5px;">
                        <input type="number" id="ssPropTransitionSpeed" value="700" class="obs-input" style="flex: 1; width: 100%;"> ms
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Playback Mode</label>
                    <div class="prop-input-container">
                        <select id="ssPropPlaybackMode" class="obs-select">
                            <option value="loop">Loop</option>
                            <option value="once">Once</option>
                            <option value="random">Random</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container">
                        <label><input type="checkbox" id="ssPropHideWhenDone"> Hide when slideshow is done</label>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Bounding Size/Aspect Ratio</label>
                    <div class="prop-input-container">
                        <select id="ssPropBounding" class="obs-select">
                            <option value="auto">Automatic</option>
                            <option value="1920x1080">1920x1080</option>
                            <option value="1280x720">1280x720</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row" style="align-items: stretch; height: 150px;">
                    <label class="prop-label">Image Files</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px;">
                        <div class="list-box" id="ssPropImageList" style="flex: 1; border: 1px solid #3c404d; background: #1d1f26; overflow-y: auto;">
                            </div>
                        <div style="display: flex; flex-direction: column; gap: 5px;">
                            <button class="icon-btn" id="ssBtnAdd"><i class="fas fa-plus"></i></button>
                            <button class="icon-btn" id="ssBtnRemove"><i class="fas fa-trash-alt"></i></button>
                            <button class="icon-btn" id="ssBtnSettings"><i class="fas fa-cog"></i></button>
                            <button class="icon-btn" id="ssBtnUp"><i class="fas fa-chevron-up"></i></button>
                            <button class="icon-btn" id="ssBtnDown"><i class="fas fa-chevron-down"></i></button>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="ssPropDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="ssPropOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="ssPropCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>


    <div class="modal" id="advancedEditorModal">
        <div class="modal-content obs-window" style="width: 1500px; max-width: 98vw; height: 90vh;">
            <div class="window-header">
                <span><i class="fas fa-film"></i> Advanced Video Editor</span>
                <button class="close-btn" id="closeAdvEditorBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body nle-layout">
                
                <div class="nle-panel nle-media-pool">
                    <div class="nle-panel-header">Project Media</div>
                    <div class="nle-pool-grid" id="advVideoLibrary"></div>
                    <div style="padding: 10px;">
                        <button class="obs-btn" id="advInsertBtn"><i class="fas fa-plus"></i> Add Files</button>
                    </div>
                </div>
                
                <div class="nle-panel nle-preview">
                    <div class="adv-preview-wrapper" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #000; overflow: hidden; position: relative;">
                        <canvas id="advEditorPreviewCanvas" width="1920" height="1080" style="max-width: 100%; max-height: 100%; object-fit: contain;"></canvas>
                        <div id="advCropOverlay" class="crop-area hidden" style="position: absolute;">
                            <div class="crop-handle tl"></div><div class="crop-handle tr"></div>
                            <div class="crop-handle bl"></div><div class="crop-handle br"></div>
                        </div>
                    </div>
                </div>

                <div class="nle-panel nle-properties">
                    <div class="nle-panel-header">Clip Properties</div>
                    <div class="nle-props-body" id="advClipProps" style="padding: 10px; display: none;">
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Position X</label><input type="number" id="advPropX" class="obs-input-small"></div>
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Position Y</label><input type="number" id="advPropY" class="obs-input-small"></div>
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Scale</label><input type="range" id="advPropScale" min="10" max="300" value="100" class="obs-slider" style="flex:1;"></div>
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Opacity</label><input type="range" id="advPropOpacity" min="0" max="100" value="100" class="obs-slider" style="flex:1;"></div>
                        <hr style="border: 0; border-top: 1px solid #3c404d; margin: 15px 0;">
                        <button class="obs-btn" id="advToggleCropBtn"><i class="fas fa-crop"></i> Toggle Crop Tool</button>
                    </div>
                    <div id="advNoClipSelected" style="padding: 20px; text-align: center; color: #888;">Select a clip on the timeline to edit properties.</div>
                </div>
                
                <div class="nle-panel nle-timeline-area">
                    <div class="nle-timeline-toolbar">
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <button class="obs-btn" id="advEditorPlayBtn" style="width: auto; padding: 0 15px;"><i class="fas fa-play"></i></button>
                            <span id="advTimeDisplay" style="font-family: monospace; font-size: 14px; margin-left: 10px;">00:00.00</span>
                            <div class="media-divider" style="height: 16px;"></div>
                            <button class="icon-btn" id="advSplitBtn" title="Split Clip (S)"><i class="fas fa-cut"></i></button>
                            <button class="icon-btn" id="advDuplicateBtn" title="Duplicate Clip (Ctrl+D)"><i class="fas fa-copy"></i></button>
                            <button class="icon-btn" id="advDeleteBtn" title="Delete Clip (Del)"><i class="fas fa-trash"></i></button>
                            <div class="media-divider" style="height: 16px;"></div>
                            <input type="range" id="advZoomSlider" min="5" max="100" value="20" title="Zoom Timeline">
                        </div>
                        <div class="editor-actions">
                            <button class="obs-btn" id="advExportBtn" style="background-color: #1e50a0;"><i class="fas fa-file-export"></i> Render & Export</button>
                        </div>
                    </div>
                    
                    <div class="nle-timeline-container" id="advTimeline">
                        <div class="nle-timeline-ruler" id="advTimelineRuler"></div>
                        <div class="nle-playhead" id="advPlayhead"></div>
                        <div class="nle-tracks-wrapper" id="advTracksWrapper">
                            <div class="nle-track" data-track="1"><div class="nle-track-header">V2</div><div class="nle-track-content"></div></div>
                            <div class="nle-track" data-track="0"><div class="nle-track-header">V1</div><div class="nle-track-content"></div></div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

   <div class="modal" id="settingsModal">
        <div class="modal-content obs-window settings-window" style="width: 900px; height: 680px; max-width: 95vw;">
            <div class="window-header">
                <span><i class="fas fa-cog"></i> Settings</span>
                <button class="close-btn" id="closeSettingsBtn"><i class="fas fa-times"></i></button>
            </div>
            
            <div class="settings-body">
                <div class="settings-sidebar">
                    <div class="settings-tab active" data-target="set-general"><i class="fas fa-cog"></i> General</div>
                    <div class="settings-tab" data-target="set-appearance"><i class="fas fa-paint-brush"></i> Appearance</div>
                    <div class="settings-tab" data-target="set-stream"><i class="fas fa-signal"></i> Stream</div>
                    <div class="settings-tab" data-target="set-output"><i class="fas fa-sign-out-alt"></i> Output</div>
                    <div class="settings-tab" data-target="set-audio"><i class="fas fa-volume-up"></i> Audio</div>
                    <div class="settings-tab" data-target="set-video"><i class="fas fa-desktop"></i> Video</div>
                    <div class="settings-tab" data-target="set-hotkeys"><i class="fas fa-keyboard"></i> Hotkeys</div>
                    <div class="settings-tab" data-target="set-accessibility"><i class="fas fa-universal-access"></i> Accessibility</div>
                    <div class="settings-tab" data-target="set-advanced"><i class="fas fa-sliders-h"></i> Advanced</div>
                </div>
                
                <div class="settings-main">
                    
                    <div class="settings-section active" id="set-general">
                        <div class="settings-group">
                            <div class="settings-group-title">General</div>
                            <div class="settings-row"><label>Language</label><select class="obs-select"><option>English</option></select></div>
                            <div class="settings-row"><label></label><label class="chk-label"><input type="checkbox"> Open stats dialog on startup</label></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-appearance">
                        <div class="settings-group">
                            <div class="settings-group-title">Appearance</div>
                            <div class="settings-row"><label>Theme</label><select class="obs-select"><option>Yami</option></select></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-stream">
                        <div class="settings-group">
                            <div class="settings-group-title">Destination</div>
                            <div class="settings-row"><label>Service</label><select class="obs-select" id="streamServiceDropdown"><option>Twitch</option><option>YouTube</option></select></div>
                            <div class="settings-row"><label>Server</label><select class="obs-select"><option>Auto (Recommended)</option></select></div>
                            <div class="settings-row"><label>Stream Key</label><input type="password" class="obs-input" id="streamKeyInput" value="live_123456789_xxxxxxxx" style="flex:1;"></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-output">
                        <div class="settings-group">
                            <div class="settings-group-title">Streaming Output</div>
                            <div class="settings-row"><label>Video Bitrate</label><input type="number" class="obs-input" value="6000"> Kbps</div>
                            <div class="settings-row"><label>Audio Bitrate</label><select class="obs-select"><option>160</option></select></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-audio">
                        <div class="settings-group">
                            <div class="settings-group-title">Global Audio Devices</div>
                            <div class="settings-row"><label>Desktop Audio</label><select class="obs-select"><option>Default</option></select></div>
                            <div class="settings-row"><label>Mic/Auxiliary Audio</label><select class="obs-select"><option>Default</option></select></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-video">
                        <div class="settings-group">
                            <div class="settings-group-title">Video Settings</div>
                            <div class="settings-row"><label>Base (Canvas) Resolution</label><select class="obs-select" id="videoBaseRes"><option value="1920x1080">1920x1080</option><option value="1280x720">1280x720</option></select></div>
                            <div class="settings-row"><label>Output (Scaled) Resolution</label><select class="obs-select"><option value="1920x1080">1920x1080</option></select></div>
                            <div class="settings-row"><label>Common FPS Values</label><select class="obs-select" id="videoFps"><option value="60">60</option><option value="30">30</option></select></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-hotkeys">
                        <div class="settings-group">
                            <div class="settings-group-title">Hotkeys</div>
                            <div class="settings-row"><label>Start Streaming</label><div class="hotkey-box"></div></div>
                            <div class="settings-row"><label>Stop Streaming</label><div class="hotkey-box"></div></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-accessibility">
                        <div class="settings-group">
                            <div class="settings-group-title">Accessibility Colors</div>
                            <div class="settings-row"><label>Source Border (Selection)</label><input type="color" value="#ff0000" class="obs-color" disabled></div>
                        </div>
                    </div>

                    <div class="settings-section" id="set-advanced">
                        <div class="settings-group">
                            <div class="settings-group-title">Advanced</div>
                            <div class="settings-row"><label>Process Priority</label><select class="obs-select"><option>Normal</option><option>High</option></select></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="settings-footer">
                <button class="obs-btn" id="settingsOkBtn" style="width: 80px;">OK</button>
                <button class="obs-btn" id="settingsCancelBtn" style="width: 80px;">Cancel</button>
                <button class="obs-btn" id="settingsApplyBtn" style="width: 80px;">Apply</button>
            </div>
        </div>
    </div>

    <div style="display:none;" id="legacy-settings-elements">
        <select id="captureMode"></select>
        <select id="canvasResolution"></select>
        <select id="frameRate"></select>
        <input type="checkbox" id="audioToggle" checked>
        <button id="saveSettingsBtn"></button>
    </div>

    <div class="modal" id="statsModal">
        <div class="modal-content obs-window" style="width: 750px; max-width: 95vw;">
            <div class="window-header">
                <span><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23dfdfdf' width='16' height='16'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z'/></svg>" style="vertical-align: middle; margin-right: 5px;"> Stats</span>
                <button class="close-btn" id="closeStatsHeaderBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body stats-body">
                <div class="stats-top-grid">
                    <div class="stats-col">
                        <div class="stat-row"><span>CPU Usage</span><span id="statCpu">3.3%</span></div>
                        <div class="stat-row"><span>Disk space available</span><span id="statDisk">53.2 GB</span></div>
                        <div class="stat-row"><span>Disk full in (approx.)</span><span id="statDiskTime">-</span></div>
                        <div class="stat-row"><span>Memory Usage</span><span id="statMemory">145.4 MB</span></div>
                    </div>
                    <div class="stats-col">
                        <div class="stat-row"><span>FPS</span><span id="statFps">60.00</span></div>
                        <div class="stat-row"><span>Average time to render frame</span><span id="statRenderTime">0.8 ms</span></div>
                        <div class="stat-row"><span>Frames missed due to rendering lag</span><span id="statMissedFrames">0 / 0 (0.0%)</span></div>
                        <div class="stat-row"><span>Skipped frames due to encoding lag</span><span id="statSkippedFrames">0 / 0 (0.0%)</span></div>
                    </div>
                </div>
                
                <div class="stats-table-container">
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Output</th>
                                <th>Status</th>
                                <th>Dropped Frames (Network)</th>
                                <th>Total Data Output</th>
                                <th>Bitrate</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Stream</td>
                                <td>Inactive</td>
                                <td>0 / 0 (0.0%)</td>
                                <td>0.0 MiB</td>
                                <td>0 kb/s</td>
                            </tr>
                            <tr>
                                <td>Recording</td>
                                <td id="statRecStatus">Inactive</td>
                                <td>0 / 0 (0.0%)</td>
                                <td id="statRecData">0.0 MiB</td>
                                <td id="statRecBitrate">0 kb/s</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="stats-footer">
                    <button class="obs-btn" style="width: 80px;" id="resetStatsBtn">Reset</button>
                    <button class="obs-btn" style="width: 80px;" id="closeStatsBtn">Close</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="audioInputPropertiesModal">
        <div class="modal-content obs-window" style="width: 600px; max-width: 95vw;">
            <div class="window-header">
                <span id="audioInputPropertiesTitle"><i class="fas fa-microphone"></i> Properties for 'Audio Input Capture'</span>
                <button class="close-btn" id="closeAudioInputPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px;">
                
                <div class="prop-row">
                    <label class="prop-label">Device</label>
                    <div class="prop-input-container">
                        <select id="micDeviceSelect" class="obs-select">
                            <option value="default">Default</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Input Gain</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="micGainSlider" min="0" max="200" value="100" class="obs-slider" style="flex: 1;">
                        <input type="number" id="micGainNum" min="0" max="200" value="100" class="obs-input-small"> %
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="micNoiseSuppression" checked> Enable Noise Suppression</label>
                        <label><input type="checkbox" id="micEchoCancellation" checked> Enable Echo Cancellation</label>
                        <label><input type="checkbox" id="micAutoGain"> Enable Auto Gain Control</label>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="micDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="micOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="micCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="audioWarningModal">
        <div class="modal-content obs-window" style="width: 500px;">
            <div class="window-header">
                <span id="audioWarningTitle"><i class="fas fa-info-circle"></i> Audio Capture Limitation</span>
                <button class="close-btn" onclick="document.getElementById('audioWarningModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body flex-col">
                <p style="line-height: 1.5;"><strong>Browser Security Limitation:</strong></p>
                <p style="line-height: 1.5; color: #bbb;">Web browsers do not allow websites to directly capture your system's speaker output for privacy and security reasons.</p>
                <p style="line-height: 1.5; color: #bbb;">To capture desktop audio, please add a <strong>Display Capture</strong> source instead, and ensure you check the box that says <em>"Share system audio"</em> or <em>"Also share tab audio"</em> when the browser prompt appears.</p>
                <div style="display: flex; justify-content: flex-end; margin-top: 15px;">
                    <button class="obs-btn" style="width:80px;" onclick="document.getElementById('audioWarningModal').classList.remove('active')">OK</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="addSceneModal">
        <div class="modal-content obs-window" style="width: 400px;">
            <div class="window-header">
                <span><img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23dfdfdf' width='16' height='16'><path d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z'/></svg>" style="vertical-align: middle; margin-right: 5px;"> Add Scene</span>
                <button class="close-btn" onclick="document.getElementById('addSceneModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body">
                <label style="display:block; margin-bottom:10px;">Please enter the name of the scene</label>
                <input type="text" id="sceneNameInput" class="obs-input" style="width:100%; margin-bottom: 20px;" autofocus>
                <div style="display: flex; justify-content: center; gap: 10px;">
                    <button class="obs-btn" id="confirmAddSceneBtn" style="width:80px;">OK</button>
                    <button class="obs-btn" id="cancelAddSceneBtn" style="width:80px;" onclick="document.getElementById('addSceneModal').classList.remove('active')">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="addNestedSceneModal">
        <div class="modal-content obs-window" style="width: 400px;">
            <div class="window-header">
                <span><i class="fas fa-film"></i> Add Scene</span>
                <button class="close-btn" onclick="document.getElementById('addNestedSceneModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body">
                <label style="display:block; margin-bottom:10px;">Select existing scene to add:</label>
                <select id="nestedSceneSelect" class="obs-select" style="width:100%; margin-bottom: 20px;"></select>
                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="obs-btn" id="confirmAddNestedSceneBtn" style="width:80px;">OK</button>
                    <button class="obs-btn" onclick="document.getElementById('addNestedSceneModal').classList.remove('active')" style="width:80px;">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="addBrowserSourceModal">
        <div class="modal-content obs-window" style="width: 450px;">
            <div class="window-header">
                <span><i class="fas fa-globe"></i> Create/Select Source</span>
                <button class="close-btn" onclick="document.getElementById('addBrowserSourceModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body">
                <label style="display:block; margin-bottom:10px;">Please enter the URL for the Browser Source:</label>
                <p style="font-size: 11px; color:#bbb; margin-bottom: 10px;">(Note: Major sites like Google/YouTube use security headers that block embedding in iframes)</p>
                <input type="text" id="browserAddUrlInput" class="obs-input" value="https://shorturl.at/6QyYn" style="width:100%; margin-bottom: 20px;" autofocus>
                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                    <button class="obs-btn" id="confirmAddBrowserBtn" style="width:80px;">OK</button>
                    <button class="obs-btn" id="cancelAddBrowserBtn" style="width:80px;" onclick="document.getElementById('addBrowserSourceModal').classList.remove('active')">Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="sceneTransitionsModal">
        <div class="modal-content obs-window" style="width: 600px;">
            <div class="window-header">
                <span><i class="fas fa-magic"></i> Scene Transitions</span>
                <button class="close-btn" onclick="document.getElementById('sceneTransitionsModal').classList.remove('active')"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; gap: 15px; height: 350px; padding-bottom: 0;">
                <div style="width: 200px; border: 1px solid #3c404d; background: #1d1f26; overflow-y: auto; border-radius: 4px;">
                    <div class="list-item transition-item" data-effect="none">Cut (None)</div>
                    <div class="list-item transition-item" data-effect="fade">Fade</div>
                    <div class="list-item transition-item" data-effect="slide-left">Slide Left</div>
                    <div class="list-item transition-item" data-effect="slide-right">Slide Right</div>
                    <div class="list-item transition-item" data-effect="slide-up">Slide Up</div>
                    <div class="list-item transition-item" data-effect="slide-down">Slide Down</div>
                    <div class="list-item transition-item" data-effect="spin">Spin</div>
                    <div class="list-item transition-item" data-effect="melt">Melt</div>
                    <div class="list-item transition-item" data-effect="fall-apart">Fall Apart</div>
                    <div class="list-item transition-item" data-effect="zoom-in">Zoom In</div>
                    <div class="list-item transition-item" data-effect="circle-crop">Circle Reveal</div>
                </div>
                <div style="flex: 1; display: flex; flex-direction: column; gap: 10px;">
                    <div style="flex: 1; background: #000; border: 1px solid #3c404d; border-radius: 4px; overflow: hidden; display: flex; justify-content: center; align-items: center;">
                        <canvas id="transitionPreviewCanvas" width="360" height="200" style="max-width:100%; max-height:100%;"></canvas>
                    </div>
                    <div id="transitionDescription" style="height: 40px; font-size: 13px; color: #bbb;">Instantly switches between scenes with no visual effect.</div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                        <label>Duration:</label>
                        <input type="number" id="transitionDurationInput" value="500" class="obs-input-small" style="width: 80px;"> ms
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end; padding: 15px; border-top: 1px solid #3c404d;">
                <button class="obs-btn" id="applyTransitionBtn" style="width: 80px;">OK</button>
            </div>
        </div>
    </div>

    <div class="modal" id="universalFiltersModal">
        <div class="modal-content obs-window" style="width: 500px;">
            <div class="window-header">
                <span id="filtersModalTitle"><i class="fas fa-sliders-h"></i> Filters for Source</span>
                <button class="close-btn" id="closeFiltersBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body flex-col">
                <div class="prop-row">
                    <label class="prop-label">Opacity</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="filterOpacity" min="0" max="100" value="100" class="obs-slider" style="flex: 1;">
                        <span id="filterOpacityVal" style="width: 40px; text-align: right;">100%</span>
                    </div>
                </div>
                <div class="prop-row">
                    <label class="prop-label">Brightness</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="filterBrightness" min="0" max="200" value="100" class="obs-slider" style="flex: 1;">
                        <span id="filterBrightnessVal" style="width: 40px; text-align: right;">100%</span>
                    </div>
                </div>
                <div class="prop-row">
                    <label class="prop-label">Contrast</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="filterContrast" min="0" max="200" value="100" class="obs-slider" style="flex: 1;">
                        <span id="filterContrastVal" style="width: 40px; text-align: right;">100%</span>
                    </div>
                </div>
                <div class="prop-row">
                    <label class="prop-label">Saturation</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="filterSaturation" min="0" max="200" value="100" class="obs-slider" style="flex: 1;">
                        <span id="filterSaturationVal" style="width: 40px; text-align: right;">100%</span>
                    </div>
                </div>
                <div class="prop-row">
                    <label class="prop-label">Hue Shift</label>
                    <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                        <input type="range" id="filterHue" min="-180" max="180" value="0" class="obs-slider" style="flex: 1;">
                        <span id="filterHueVal" style="width: 40px; text-align: right;">0°</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="filterDefaultsBtn" style="width: 80px;">Defaults</button>
                    <button class="obs-btn" id="filterCloseBtn" style="width: 80px;">Close</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="displayPropertiesModal">
        <div class="modal-content obs-window" style="width: 700px; max-width: 95vw;">
            <div class="window-header">
                <span id="displayPropertiesTitle"><i class="fas fa-desktop"></i> Properties for 'Display Capture'</span>
                <button class="close-btn" id="closeDisplayPropertiesBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body" style="display: flex; flex-direction: column; gap: 10px; max-height: 80vh; overflow-y: auto;">
                
                <div class="prop-preview-area">
                    <video id="displayPropertiesPreview" autoplay muted playsinline></video>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Capture Method</label>
                    <div class="prop-input-container">
                        <select id="dpCaptureMethod" class="obs-select">
                            <option value="auto">Automatic</option>
                            <option value="dxgi">DXGI Desktop Duplication</option>
                            <option value="wgc">Windows 10 (1903 and up)</option>
                            <option value="bitblt">BitBlt</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label">Display</label>
                    <div class="prop-input-container">
                        <select id="dpDisplaySelect" class="obs-select">
                            <option value="current">Current Screen/Window</option>
                            <option value="reselect">... Click to select new display ...</option>
                        </select>
                    </div>
                </div>

                <div class="prop-row">
                    <label class="prop-label"></label>
                    <div class="prop-input-container" style="display: flex; flex-direction: column; gap: 5px;">
                        <label><input type="checkbox" id="dpCaptureCursor" checked> Capture Cursor</label>
                        <label><input type="checkbox" id="dpForceSDR"> Force SDR</label>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3c404d;">
                    <button class="obs-btn" id="dpDefaultsBtn" style="width: 80px;">Defaults</button>
                    <div style="display: flex; gap: 10px;">
                        <button class="obs-btn" id="dpOkBtn" style="width: 80px;">OK</button>
                        <button class="obs-btn" id="dpCancelBtn" style="width: 80px;">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div style="display:none;" id="legacy-dummy-elements">
        <button id="openEditorBtn"></button>
        <button id="closeEditorBtn"></button>
        <div id="editorModal"></div>
        <video id="editorPreview"></video>
        <div id="videoLibrary"></div>
        <div id="timeline"></div>
        <div id="timelineTrack"></div>
        <div id="timelineRuler"></div>
        <div id="playhead"></div>
        <button id="cropBtn"></button>
        <button id="exportBtn"></button>
        <button id="insertBtn"></button>
        <div id="cropModal"></div>
        <video id="cropPreview"></video>
        <div id="cropArea"></div>
        <button id="applyCropBtn"></button>
        <button id="cancelCropBtn"></button>
        <div id="cropBoundsContainer"></div>
        <button id="editorPlayBtn"></button>
        <button id="editorPauseBtn"></button>
        <button id="editorSplitBtn"></button>
        <button id="editorDeleteBtn"></button>
    </div>
    <div class="modal" id="advancedEditorModal">
        <div class="modal-content obs-window" style="width: 1400px; max-width: 98vw; height: 90vh;">
            <div class="window-header">
                <span><i class="fas fa-film"></i> Advanced Video Editor</span>
                <button class="close-btn" id="closeAdvEditorBtn"><i class="fas fa-times"></i></button>
            </div>
            <div class="window-body nle-layout">
                <div class="nle-panel nle-media-pool">
                    <div class="nle-panel-header">Project Media</div>
                    <div class="nle-pool-grid" id="advVideoLibrary"></div>
                    <div style="padding: 10px;"><button class="obs-btn" id="advInsertBtn"><i class="fas fa-plus"></i> Import Files</button></div>
                </div>
                <div class="nle-panel nle-preview">
                    <canvas id="advEditorPreviewCanvas" width="1920" height="1080" style="max-width: 100%; max-height: 100%; object-fit: contain;"></canvas>
                </div>
                <div class="nle-panel nle-properties">
                    <div class="nle-panel-header">Clip Properties</div>
                    <div id="advClipProps" style="padding: 15px; display: none; color: #dfdfdf;">
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Scale</label><input type="range" id="advPropScale" min="10" max="300" value="100" class="obs-slider" style="flex:1;"></div>
                        <div class="prop-row"><label class="prop-label" style="width: 80px;">Opacity</label><input type="range" id="advPropOpacity" min="0" max="100" value="100" class="obs-slider" style="flex:1;"></div>
                        <div style="margin-top: 10px; font-size: 11px; color:#888;">Drag clips in the preview window to reposition them.</div>
                    </div>
                    <div id="advNoClipSelected" style="padding: 20px; text-align: center; color: #888;">Select a clip to edit properties.</div>
                </div>
                <div class="nle-panel nle-timeline-area">
                    <div class="nle-timeline-toolbar">
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <button class="obs-btn" id="advEditorPlayBtn" style="width: 40px; padding: 0;"><i class="fas fa-play"></i></button>
                            <span id="advTimeDisplay" style="font-family: monospace; font-size: 14px; margin-left: 10px; color:white;">00:00.00</span>
                            <div style="width:1px; height:16px; background:#3c404d; margin: 0 10px;"></div>
                            <button class="icon-btn" id="advSplitBtn" title="Split Clip (S)"><i class="fas fa-cut"></i></button>
                            <button class="icon-btn" id="advDeleteBtn" title="Delete Clip (Del)"><i class="fas fa-trash"></i></button>
                        </div>
                        <button class="obs-btn" id="advExportBtn" style="background-color: #1e50a0; width: 150px;"><i class="fas fa-file-export"></i> Render Video</button>
                    </div>
                    <div class="nle-timeline-container" id="advTimeline">
                        <div class="nle-timeline-ruler" id="advTimelineRuler"></div>
                        <div class="nle-playhead" id="advPlayhead"></div>
                        <div class="nle-tracks-wrapper" id="advTracksWrapper">
                            <div class="nle-track" data-track="1"><div class="nle-track-header">V2</div><div class="nle-track-content"></div></div>
                            <div class="nle-track" data-track="0"><div class="nle-track-header">V1</div><div class="nle-track-content"></div></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <input type="file" id="advEditorMediaInput" accept="video/*,image/*" multiple style="display:none;">

    <script src="script.js"></script>
</body>
</html>

/* --- BASE RESET & THEME --- */
* { 
    margin: 0; 
    padding: 0; 
    box-sizing: border-box; 
}

body { 
    font-family: "Segoe UI", Arial, sans-serif; 
    background-color: #1d1f26; 
    color: #dfdfdf; 
    height: 100vh; 
    display: flex; 
    flex-direction: column; 
    overflow: hidden; 
    font-size: 13px; 
}

::-webkit-scrollbar { 
    width: 12px; 
    height: 12px; 
}

::-webkit-scrollbar-track { 
    background: #1d1f26; 
}

::-webkit-scrollbar-thumb { 
    background: #3c404d; 
    border: 3px solid #1d1f26; 
    border-radius: 6px; 
}

::-webkit-scrollbar-thumb:hover { 
    background: #555555; 
}

/* Restored 3D background wrapper */
#three-container { 
    position: fixed; 
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 100%; 
    z-index: -1; 
    opacity: 0.15; 
    pointer-events: none; 
}

/* Font Awesome Reset */
.fa, .fas, .far, .fab { 
    color: #dfdfdf; 
}

/* --- TOP MENU BAR --- */
.obs-menu { 
    background-color: #1c1c1c; 
    display: flex; 
    border-bottom: 1px solid #111; 
    z-index: 2000; 
    position: relative; 
}

.menu-item { 
    position: relative; 
}

.menu-title { 
    cursor: default; 
    padding: 6px 10px; 
    display: inline-block; 
}

.menu-item.active .menu-title, .menu-title:hover { 
    background-color: #1e50a0; 
    color: white; 
}

.dropdown-content { 
    display: none; 
    position: absolute; 
    top: 100%; 
    left: 0; 
    background-color: #1c1c1c; 
    border: 1px solid #333; 
    box-shadow: 2px 2px 10px rgba(0,0,0,0.7); 
    min-width: 220px; 
    padding: 4px 0; 
    z-index: 2000; 
}

.menu-item.active .dropdown-content { 
    display: block; 
}

.dropdown-row { 
    display: flex; 
    align-items: center; 
    padding: 4px 10px 4px 5px; 
    cursor: default; 
    color: #dfdfdf; 
}

.dropdown-row:hover { 
    background-color: #383838; 
}

.dropdown-row.disabled { 
    color: #666; 
    pointer-events: none; 
}

.menu-icon { 
    width: 20px; 
    text-align: center; 
    font-size: 11px; 
    color: #dfdfdf; 
    display: inline-block; 
}

.menu-text { 
    flex-grow: 1; 
    white-space: nowrap; 
}

.menu-shortcut { 
    margin-left: 20px; 
    color: #999; 
    font-size: 11px; 
}

.menu-arrow { 
    margin-left: 15px; 
    font-size: 10px; 
    color: #999; 
}

.menu-separator { 
    height: 1px; 
    background-color: #333; 
    margin: 4px 0; 
}

/* --- WORKSPACE & CANVAS --- */
.obs-workspace { 
    flex: 1; 
    display: flex; 
    flex-direction: column; 
    padding: 5px; 
    gap: 5px; 
    overflow: hidden; 
}

.obs-preview-container { 
    flex: 1; 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    border-radius: 8px; 
    display: flex; 
    flex-direction: column; 
    min-height: 0; 
    overflow: hidden; 
    padding: 5px;
}

.preview-header { 
    background-color: #3c404d; 
    padding: 4px 8px; 
    text-align: center; 
    border-bottom: 1px solid #3c404d; 
    font-weight: 600; 
    display: none; 
}

.preview-wrapper { 
    flex: 1; 
    position: relative; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    background-color: #1d1f26; 
    overflow: hidden; 
    min-height: 0; 
    min-width: 0; 
    border: 1px solid #3c404d; 
    border-radius: 4px;
}

/* UPDATED CANVAS LAYERING CSS */
#obsCanvas, #obsCanvasTop { 
    max-width: 100%; 
    max-height: 100%; 
    object-fit: contain; 
    background-color: transparent; 
    aspect-ratio: 16/9; 
    cursor: default; 
    position: absolute;
}

#obsCanvas { 
    box-shadow: 0 0 15px rgba(0,0,0,0.8); 
    z-index: 1; 
}

#obsCanvasTop { 
    z-index: 3; 
    pointer-events: none; 
}

#domOverlayContainer { 
    z-index: 2; 
}

.preview-placeholder { 
    position: absolute; 
    color: #666; 
    font-size: 24px; 
    z-index: 4; 
    pointer-events: none; 
}

/* --- DOCKS & LISTS --- */
.obs-docks { 
    height: 250px; 
    display: flex; 
    gap: 5px; 
}

.dock { 
    flex: 1; 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    border-radius: 8px; 
    display: flex; 
    flex-direction: column; 
}

.dock-wide { 
    flex: 1.5; 
}

.controls-dock { 
    flex: 1.2; 
}

.dock-header { 
    background-color: #3c404d; 
    padding: 6px 10px; 
    font-weight: 600; 
    font-size: 13px; 
    color: #e0e0e0; 
    border-top-left-radius: 7px; 
    border-top-right-radius: 7px; 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
}

.dock-content { 
    flex: 1; 
    padding: 5px; 
    overflow-y: auto; 
    overflow-x: hidden; 
    background: #272a33; 
    border-top: 1px solid #3c404d;
}

.dock-toolbar { 
    background-color: #272a33; 
    padding: 4px 6px; 
    display: flex; 
    gap: 4px; 
    align-items: center; 
    border-top: 1px solid #3c404d; 
    border-bottom-left-radius: 7px; 
    border-bottom-right-radius: 7px;
}

/* CSS for Popped-Out Docks */
.dock.popped-out {
    position: absolute;
    z-index: 5000;
    width: 300px;
    height: 400px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    border: 1px solid #555;
    border-radius: 8px;
    resize: both;
    overflow: hidden;
}

.dock.popped-out .dock-header {
    cursor: move;
}

/* --- SOURCES & SCENES LIST UI --- */
.list-box { 
    padding: 4px; 
}

.list-item { 
    padding: 4px 8px; 
    cursor: default; 
    border: 1px solid transparent; 
    color: #dfdfdf; 
    margin-bottom: 2px; 
}

.list-item:hover { 
    background-color: #3c404d; 
    border-radius: 4px; 
}

.list-item.active { 
    background-color: #1a50a1; 
    color: white; 
    border-radius: 4px; 
}

.source-list-item { 
    display: flex; 
    align-items: center; 
    justify-content: space-between; 
    padding: 4px 8px; 
    cursor: pointer; 
    border: 1px solid transparent; 
    color: #dfdfdf; 
    margin-bottom: 2px; 
    user-select: none;
}

.source-list-item:hover { 
    background-color: #3c404d; 
    border-radius: 4px; 
}

.source-list-item.active { 
    background-color: #1a50a1; 
    color: white; 
    border-radius: 4px; 
}

.source-list-item.dragging { 
    opacity: 0.4; 
    border: 1px dashed #dfdfdf; 
}

.source-list-item.drag-over { 
    border-top: 2px solid #1e50a0; 
}

.source-icon { 
    width: 24px; 
    text-align: center; 
    font-size: 14px;
}

.source-name { 
    flex: 1; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    padding: 0 8px; 
}

.source-actions { 
    display: flex; 
    gap: 6px; 
}

.source-action-btn { 
    background: none; 
    border: none; 
    color: #999; 
    cursor: pointer; 
    font-size: 14px; 
    width: 18px; 
    text-align: center;
}

.source-action-btn:hover { 
    color: #fff; 
}

.source-action-btn .fa, .source-action-btn .fas { 
    color: inherit; 
    pointer-events: none; 
}

/* Audio Filters List Specific */
.audio-filter-item {
    display: flex; 
    align-items: center; 
    padding: 6px 10px; 
    cursor: pointer; 
    color: #dfdfdf; 
    border-radius: 4px; 
    margin-bottom: 2px;
}

.audio-filter-item:hover { 
    background-color: #3c404d; 
}

.audio-filter-item.active { 
    background-color: #1e50a0; 
    color: white; 
}

.audio-filter-item .fa-eye, .audio-filter-item .fa-eye-slash { 
    margin-right: 10px; 
    width: 16px; 
    text-align: center; 
    color: #dfdfdf; 
}

.audio-filter-item.active .fa-eye { 
    color: white; 
}

/* --- DUAL AUDIO MIXER UI --- */
.audio-mixer { 
    display: flex; 
    flex-direction: column; 
    gap: 5px; 
    padding: 0 !important; 
}

.audio-track { 
    background: #272a33; 
    padding: 8px 12px; 
    display: flex; 
    flex-direction: column; 
    gap: 4px; 
    border-bottom: 1px solid #3c404d; 
}

.audio-header { 
    display: flex; 
    justify-content: space-between; 
    font-size: 12px; 
    font-weight: 500; 
    color: #dfdfdf; 
    margin-bottom: 4px;
}

.audio-body { 
    display: flex; 
    align-items: center; 
    gap: 8px; 
}

.audio-left-icons { 
    display: flex; 
    flex-direction: column; 
    gap: 4px; 
    justify-content: center; 
}

.audio-menu-btn { 
    cursor: pointer; 
    padding: 2px 4px; 
    font-weight: bold; 
    background: #3c404d; 
    border-radius: 3px; 
    height: 22px; 
    display: flex; 
    align-items: center; 
    justify-content: center;
}

.audio-speaker-btn { 
    cursor: pointer; 
    font-size: 16px; 
    height: 22px; 
    display: flex; 
    align-items: center; 
    justify-content: center;
}

.audio-controls { 
    flex: 1; 
    display: flex; 
    flex-direction: column; 
    justify-content: center; 
}

.audio-meter-container { 
    display: flex; 
    flex-direction: column; 
    width: 100%; 
    margin-bottom: 2px;
}

.audio-meter { 
    height: 8px; 
    background: #1d1f26; 
    border-radius: 2px; 
    overflow: hidden; 
    display: block; 
}

.audio-meter-spacer { 
    height: 2px; 
    background: transparent; 
}

.audio-meter-fill { 
    height: 100%; 
    background: linear-gradient(90deg, #4caf50 60%, #ffeb3b 85%, #f44336 100%); 
    width: 0%; 
    transition: width 0.1s linear; 
}

.audio-ticks { 
    display: flex; 
    justify-content: space-between; 
    font-size: 9px; 
    color: #888; 
    font-family: monospace; 
    margin-top: 1px; 
    letter-spacing: normal;
}

.audio-slider { 
    width: 100%; 
    margin-top: 4px; 
    cursor: pointer; 
    accent-color: #1e50a0; 
}

/* --- BUTTONS & CONTROLS --- */
.controls-box { 
    display: flex; 
    flex-direction: column; 
    gap: 4px; 
    padding: 8px; 
    background: #272a33; 
    border-top: 1px solid #3c404d;
}

.obs-btn { 
    background-color: #3c404d; 
    color: #dfdfdf; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    padding: 0 10px; 
    cursor: pointer; 
    width: 100%; 
    text-align: center;
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    font-size: 12px;
    height: 26px; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    gap: 6px;
}

.obs-btn:hover:not(:disabled) { 
    background-color: #4b4e50; 
}

.obs-btn:disabled { 
    opacity: 0.5; 
    cursor: not-allowed; 
}

.obs-btn.hidden { 
    display: none; 
}

.controls-divider { 
    height: 1px; 
    background: #3c404d; 
    margin: 2px 0; 
}

.icon-btn { 
    background-color: #2b2e38; 
    border: 1px solid #3c404d; 
    color: #dfdfdf; 
    width: 24px; 
    height: 24px; 
    cursor: pointer; 
    border-radius: 4px; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
}

.icon-btn:hover { 
    background-color: #3c404d; 
}

.icon-btn i { 
    pointer-events: none; 
}

.text-icon-btn {
    background-color: #3c404d; 
    color: #dfdfdf; 
    border: 1px solid #3c404d; 
    border-radius: 4px;
    padding: 4px 10px; 
    cursor: pointer; 
    display: flex; 
    align-items: center; 
    gap: 6px;
    height: 28px; 
    white-space: nowrap;
}
/* --- SQUARE MEDIA BUTTONS --- */
.obs-btn-square {
    background-color: #3c404d; 
    color: #dfdfdf; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    width: 28px; 
    height: 28px; 
    cursor: pointer; 
    display: flex; 
    align-items: center; 
    justify-content: center;
    flex-shrink: 0;
}

.obs-btn-square:hover {
    background-color: #4b4e50; 
}

.obs-btn-square i {
    pointer-events: none;
}

/* --- MEDIA TOOLBAR DIVIDER --- */
.media-divider {
    width: 1px;
    height: 20px;
    background-color: #3c404d;
    margin: 0 5px;
}
.text-icon-btn:hover { 
    background-color: #4b4e50; 
}

.text-icon-btn.active { 
    background-color: #1e50a0; 
    border-color: #1e50a0; 
    color: white; 
}

.transitions-box { 
    display: flex; 
    flex-direction: column; 
    gap: 10px; 
    padding: 10px;
}

.obs-select, .obs-input { 
    background-color: #1d1f26; 
    color: white; 
    border: 1px solid #3c404d; 
    padding: 4px; 
    width: 100%; 
    border-radius: 3px; 
}

.obs-input-small { 
    background-color: #1d1f26; 
    color: white; 
    border: 1px solid #3c404d; 
    padding: 4px; 
    border-radius: 3px; 
    width: 60px; 
}

.obs-select:disabled, .obs-input:disabled { 
    opacity: 0.5; 
    cursor: not-allowed; 
}

.obs-textarea { 
    background-color: #1d1f26; 
    color: white; 
    border: 1px solid #3c404d; 
    padding: 6px; 
    width: 100%; 
    border-radius: 3px; 
    font-family: monospace; 
    height: 120px; 
    resize: vertical;
}

.duration-box { 
    display: flex; 
    align-items: center; 
    justify-content: space-between; 
}

input[type="number"] { 
    color-scheme: dark; 
}

.chk-label { 
    display: flex; 
    align-items: center; 
    gap: 6px; 
    cursor: pointer; 
    color: #dfdfdf; 
}

.chk-label.disabled { 
    opacity: 0.5; 
    cursor: not-allowed; 
}

/* --- CONTEXT MENUS & PROPERTIES --- */
.context-menu { 
    display: none; 
    position: absolute; 
    bottom: 100%; 
    left: 0; 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    box-shadow: 2px 2px 10px rgba(0,0,0,0.7); 
    min-width: 250px; 
    padding: 4px 0; 
    z-index: 3000; 
    border-radius: 4px;
}

.context-menu.active { 
    display: block; 
}

.context-item { 
    padding: 6px 15px; 
    cursor: pointer; 
    color: #dfdfdf; 
    display: flex; 
    align-items: center;
}

.context-item i { 
    width: 20px; 
    text-align: center; 
    margin-right: 8px; 
    pointer-events: none; 
}

.context-item:hover:not(.disabled) { 
    background-color: #1e50a0; 
    color: white; 
}

.context-item.disabled { 
    color: #666; 
    cursor: default; 
}

.context-separator { 
    height: 1px; 
    background-color: #3c404d; 
    margin: 4px 0; 
}

.properties-bar { 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    border-radius: 8px; 
    padding: 8px 12px; 
    display: flex; 
    align-items: center; 
    gap: 10px; 
    margin-top: 5px;
}

.obs-color { 
    width: 30px; 
    height: 24px; 
    padding: 0; 
    cursor: pointer; 
    border-radius: 3px; 
    border: 1px solid #3c404d;
}

.obs-color.disabled { 
    opacity: 0.5; 
    cursor: not-allowed; 
}

.media-controls-bar { 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    padding: 8px 12px; 
    display: flex; 
    align-items: center; 
    gap: 8px; 
    margin-top: 5px; 
    flex-shrink: 0;
}

.prop-row { 
    display: flex; 
    margin-bottom: 8px; 
    align-items: flex-start;
}

.prop-label { 
    width: 140px; 
    text-align: right; 
    margin-right: 15px; 
    color: #dfdfdf; 
    font-size: 13px; 
    padding-top: 3px; 
    flex-shrink: 0;
}

.prop-input-container { 
    flex: 1; 
    display: flex; 
    flex-direction: column; 
    justify-content: center; 
}

.prop-input-container label { 
    display: flex; 
    align-items: center; 
    gap: 6px; 
    cursor: pointer; 
    color: #dfdfdf;
}

.prop-preview-area { 
    background: #000; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    height: 300px; 
    min-height: 300px; 
    flex-shrink: 0; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    margin-bottom: 15px; 
    overflow: hidden; 
}

.prop-preview-area video, .prop-preview-area canvas, .prop-preview-area img, .prop-preview-area div { 
    max-width: 100%; 
    max-height: 100%; 
    object-fit: contain; 
}

/* --- DRAGGABLE MODALS --- */
.modal { 
    display: none; 
    position: fixed; 
    top: 0; 
    left: 0; 
    width: 100%; 
    height: 100%; 
    background: rgba(0,0,0,0.6); 
    z-index: 4000; 
}

.modal.active { 
    display: block; 
}

.obs-window { 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
    width: 800px; 
    max-width: 95%; 
    display: flex; 
    flex-direction: column; 
    border-radius: 8px; 
    position: absolute; 
    resize: both; 
    overflow: auto; 
    max-height: 95vh; 
}

.window-header { 
    background-color: #3c404d; 
    padding: 8px 12px; 
    display: flex; 
    justify-content: space-between; 
    border-bottom: 1px solid #3c404d; 
    font-weight: 600; 
    cursor: move; 
}

.close-btn { 
    background: none; 
    border: none; 
    color: white; 
    cursor: pointer; 
}

.close-btn:hover { 
    color: #f44336; 
}

.window-body { 
    padding: 15px; 
}

.flex-col { 
    display: flex; 
    flex-direction: column; 
    gap: 15px; 
}

/* --- NLE STYLES --- */
.nle-layout { 
    display: grid; 
    grid-template-columns: 250px 1fr 280px; 
    grid-template-rows: 1fr 250px; 
    gap: 10px; 
    height: 100%; 
    padding: 10px; 
}

.nle-panel { 
    background: #1d1f26; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    display: flex; 
    flex-direction: column; 
    overflow: hidden; 
}

.nle-panel-header { 
    background: #3c404d; 
    padding: 6px 10px; 
    font-weight: 600; 
    font-size: 12px; 
    color: #dfdfdf; 
}

.nle-media-pool { 
    grid-column: 1; 
    grid-row: 1; 
}

.nle-pool-grid { 
    display: grid; 
    grid-template-columns: repeat(2, 1fr); 
    gap: 8px; 
    overflow-y: auto; 
    padding: 10px; 
    flex: 1; 
}

.video-thumbnail { 
    aspect-ratio: 16/9; 
    background: #000; 
    border: 2px solid transparent; 
    cursor: pointer; 
    position: relative; 
    border-radius: 4px; 
    overflow: hidden; 
}

.video-thumbnail video, .video-thumbnail img { 
    width: 100%; 
    height: 100%; 
    object-fit: cover; 
    pointer-events: none; 
}

.duration-badge { 
    position: absolute; 
    bottom: 2px; 
    right: 2px; 
    background: rgba(0,0,0,0.7); 
    padding: 2px 4px; 
    font-size: 10px; 
    border-radius: 2px; 
    color: white; 
}

.nle-preview { 
    grid-column: 2; 
    grid-row: 1; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    background: #000; 
    position: relative;
}

.nle-properties { 
    grid-column: 3; 
    grid-row: 1 / span 2; 
}

.nle-timeline-area { 
    grid-column: 1 / span 2; 
    grid-row: 2; 
    display: flex; 
    flex-direction: column; 
}

.nle-timeline-toolbar { 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
    background: #272a33; 
    padding: 6px 10px; 
    border-bottom: 1px solid #3c404d; 
}

.nle-timeline-container { 
    flex: 1; 
    background: #16181d; 
    position: relative; 
    overflow-x: auto; 
    overflow-y: auto; 
}

.nle-timeline-ruler { 
    height: 24px; 
    background: #272a33; 
    border-bottom: 1px solid #3c404d; 
    position: sticky; 
    top: 0; 
    z-index: 50; 
}

.nle-tracks-wrapper { 
    display: flex; 
    flex-direction: column; 
    gap: 2px; 
    padding: 10px 0; 
}

.nle-track { 
    position: relative; 
    height: 60px; 
    background: #1d1f26; 
    border-top: 1px solid #3c404d; 
    border-bottom: 1px solid #3c404d; 
    min-width: 100%; 
    display: flex; 
}

.nle-track-header { 
    width: 60px; 
    background: #272a33; 
    border-right: 1px solid #3c404d; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    font-weight: bold; 
    color: #888; 
    position: sticky; 
    left: 0; 
    z-index: 40; 
}

.nle-track-content { 
    flex: 1; 
    position: relative; 
}

.nle-playhead { 
    position: absolute; 
    top: 0; 
    bottom: 0; 
    width: 1px; 
    background: red; 
    z-index: 60; 
    pointer-events: none; 
    left: 60px; 
}

.nle-playhead::before { 
    content: ''; 
    position: absolute; 
    top: 0; 
    left: -5px; 
    width: 11px; 
    height: 11px; 
    background: red; 
    clip-path: polygon(0 0, 100% 0, 50% 100%); 
}

.nle-clip { 
    position: absolute; 
    height: 100%; 
    top: 0; 
    background: #1e50a0; 
    border: 1px solid #4daafc; 
    color: white; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    cursor: move; 
    font-size: 11px; 
    overflow: hidden; 
    user-select: none; 
    border-radius: 4px; 
    z-index: 10; 
}

.nle-clip.selected-clip { 
    background: #0078d7; 
    border: 2px solid #fff; 
    box-shadow: 0 0 8px rgba(255,255,255,0.5); 
    z-index: 15; 
}

.nle-trim-handle { 
    position: absolute; 
    width: 8px; 
    height: 100%; 
    background: rgba(255,255,255,0.2); 
    cursor: ew-resize; 
    top: 0; 
    z-index: 15; 
}

.nle-trim-handle:hover { 
    background: #4daafc; 
}

.nle-trim-handle.left { 
    left: 0; 
    border-right: 1px solid rgba(255,255,255,0.5); 
}

.nle-trim-handle.right { 
    right: 0; 
    border-left: 1px solid rgba(255,255,255,0.5); 
}

/* --- STATUS BAR --- */
.obs-status { 
    background-color: #3c404d; 
    color: #a0a0a0; 
    padding: 4px 10px; 
    display: flex; 
    justify-content: space-between; 
    font-size: 12px; 
    border-top: 1px solid #3c404d;
}

.status-right { 
    display: flex; 
    gap: 20px; 
    align-items: center;
}

/* --- STATS WINDOW STYLES --- */
.stats-body { 
    display: flex; 
    flex-direction: column; 
    gap: 15px; 
    background-color: #272a33; 
    padding: 15px; 
}

.stats-top-grid { 
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 40px; 
    margin-bottom: 5px; 
}

.stats-col { 
    display: flex; 
    flex-direction: column; 
    gap: 10px; 
}

.stat-row { 
    display: flex; 
    justify-content: space-between; 
    font-size: 13px; 
}

.stat-row span:first-child { 
    color: #dfdfdf; 
}

.stat-row span:last-child { 
    color: #fff; 
    text-align: right; 
}

.stats-table-container { 
    background-color: #1d1f26; 
    border-radius: 4px; 
    overflow: hidden; 
}

.stats-table { 
    width: 100%; 
    border-collapse: collapse; 
    text-align: left; 
    font-size: 13px; 
}

.stats-table th { 
    font-weight: 700; 
    padding: 10px; 
    color: #dfdfdf; 
    border-bottom: 1px solid #3c404d; 
}

.stats-table td { 
    padding: 10px; 
    color: #fff; 
}

.stats-footer { 
    display: flex; 
    justify-content: flex-end; 
    gap: 10px; 
    margin-top: 10px; 
}

/* --- SCENE TRANSITION UI --- */
.transition-item { 
    padding: 8px 15px; 
    cursor: pointer; 
    border-bottom: 1px solid #2a2d36; 
    color: #dfdfdf; 
}

.transition-item:hover { 
    background-color: #3c404d; 
}

.transition-item.active { 
    background-color: #1e50a0; 
    color: white; 
}

/* --- STUDIO MODE STYLES --- */
.preview-layout-wrapper { 
    display: flex; 
    flex: 1; 
    min-height: 0; 
    overflow: hidden; 
    width: 100%; 
}

.studio-pane { 
    flex: 1; 
    display: flex; 
    flex-direction: column; 
    min-width: 0; 
    min-height: 0; 
}

.studio-pane-header { 
    background: #1d1f26; 
    text-align: center; 
    padding: 6px; 
    font-weight: 600; 
    font-size: 13px; 
    letter-spacing: 1px; 
    color: #dfdfdf; 
    border-bottom: 1px solid #3c404d; 
}

.studio-controls { 
    width: 140px; 
    background: #272a33; 
    border-left: 1px solid #3c404d; 
    border-right: 1px solid #3c404d; 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    padding: 15px 10px; 
    gap: 15px; 
}

.studio-quick-transitions { 
    display: flex; 
    flex-direction: column; 
    gap: 8px; 
    width: 100%; 
    border-top: 1px solid #3c404d; 
    border-bottom: 1px solid #3c404d; 
    padding: 15px 0; 
}

.studio-tbar-container { 
    flex: 1; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    position: relative; 
    width: 100%; 
    min-height: 150px; 
}

.studio-tbar-track { 
    width: 4px; 
    height: 150px; 
    background: #1d1f26; 
    border-radius: 2px; 
    position: relative; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
}

.studio-tbar { 
    -webkit-appearance: slider-vertical; 
    appearance: slider-vertical; 
    width: 30px; 
    height: 150px; 
    margin: 0; 
    cursor: grab; 
    background: transparent; 
    outline: none; 
}

@supports not (appearance: slider-vertical) {
    .studio-tbar { 
        appearance: auto; 
        width: 150px; 
        height: 30px; 
        position: absolute; 
        transform: rotate(270deg); 
    }
}

/* ========================================================================= */
/* ==================== NEW FULL SETTINGS MODAL UI ========================= */
/* ========================================================================= */

.settings-window { 
    display: flex; 
    flex-direction: column; 
}

.settings-body { 
    display: flex; 
    flex: 1; 
    overflow: hidden; 
}

/* Sidebar Menu */
.settings-sidebar { 
    width: 200px; 
    background-color: #272a33; 
    border-right: 1px solid #3c404d; 
    display: flex; 
    flex-direction: column; 
    padding-top: 10px; 
}

.settings-tab { 
    padding: 10px 20px; 
    cursor: pointer; 
    font-size: 14px; 
    color: #dfdfdf; 
    display: flex; 
    align-items: center; 
    gap: 10px; 
    border-left: 3px solid transparent; 
}

.settings-tab i { 
    width: 20px; 
    text-align: center; 
}

.settings-tab:hover { 
    background-color: #3c404d; 
}

.settings-tab.active { 
    background-color: #1e50a0; 
    color: white; 
    border-left: 3px solid #4daafc; 
}

/* Main Content Area */
.settings-main { 
    flex: 1; 
    background-color: #1d1f26; 
    overflow-y: auto; 
    padding: 20px; 
}

.settings-section { 
    display: none; 
    flex-direction: column; 
    gap: 20px; 
}

.settings-section.active { 
    display: flex; 
}

.settings-group { 
    background-color: #272a33; 
    border: 1px solid #3c404d; 
    border-radius: 6px; 
    padding: 15px; 
    display: flex; 
    flex-direction: column; 
    gap: 10px; 
}

.settings-group-title { 
    font-size: 16px; 
    font-weight: 600; 
    color: white; 
    margin-bottom: 10px; 
    border-bottom: 1px solid #3c404d; 
    padding-bottom: 5px; 
}

.settings-row { 
    display: flex; 
    align-items: center; 
    margin-bottom: 5px; 
}

.settings-row label:first-child { 
    width: 160px; 
    text-align: left; 
    flex-shrink: 0; 
    color: #dfdfdf; 
}

/* Footer Buttons */
.settings-footer { 
    display: flex; 
    justify-content: flex-end; 
    gap: 10px; 
    padding: 15px; 
    background-color: #272a33; 
    border-top: 1px solid #3c404d; 
}

.hotkey-box { 
    flex: 1; 
    height: 26px; 
    background: #16181d; 
    border: 1px solid #3c404d; 
    border-radius: 4px; 
    display: flex; 
    align-items: center; 
    padding: 0 10px; 
    color: #888; 
}

.hotkey-box:empty::before { 
    content: ''; 
}

// --- AUDIO ENGINE SETUP ---
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
const audioDest = audioCtx.createMediaStreamDestination();
const masterGain = audioCtx.createGain(); // Master mix for global output

// Cleanly route the master sum directly to the final outputs
masterGain.connect(audioDest);
masterGain.connect(audioCtx.destination);

// --- STATE & SCENE MANAGEMENT ---
class ObsScene {
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.sources = [];
        this.transition = 'fade';
        this.transitionDuration = 500;
    }
}

// Global scene state
let scenes = [new ObsScene(Date.now(), 'Scene 1')];
let activeScene = scenes[0];
let sources = activeScene.sources; // Reference array points directly to the active scene's sources
let selectedSource = null;

// Transitions Engine State
let activeTransition = 'fade';
let activeTransitionDuration = 500;
let isTransitioning = false;
let transitionStartTime = 0;
const outgoingCanvas = document.createElement('canvas');
outgoingCanvas.width = 1920;
outgoingCanvas.height = 1080;

let mediaRecorder;
let recordedChunks = [];
let recordingStartTime;
let recordingInterval;
let latestRecordingUrl = null;

// Editor Variables
let videoLibrary = [];
let timelineClips = [];
let currentEditingVideo = null;
let selectedClipElement = null; 
const TIMELINE_SCALE = 20; // 20px per second

// Interaction logic
const GRID_SIZE = 20;
const ROTATE_SNAP = Math.PI / 12; // 15 degrees

// --- DOM ELEMENTS ---
const obsCanvas = document.getElementById('obsCanvas');
const ctx = obsCanvas.getContext('2d');
const obsCanvasTop = document.getElementById('obsCanvasTop');
const topCtx = obsCanvasTop.getContext('2d');
const liveRenderCanvas = document.getElementById('liveRenderCanvas'); 
const liveCtx = liveRenderCanvas.getContext('2d');
const previewPlaceholder = document.getElementById('previewPlaceholder');
const scenesListEl = document.getElementById('scenesList');
const sourcesList = document.getElementById('sourcesList');
const audioMixerContainer = document.getElementById('audioMixerContainer');
const mainDocksContainer = document.getElementById('mainDocksContainer');
const hiddenMediaContainer = document.getElementById('hiddenMediaContainer');

const addSceneBtn = document.getElementById('addSceneBtn');
const removeSceneBtn = document.getElementById('removeSceneBtn');
const moveSceneUpBtn = document.getElementById('moveSceneUpBtn');
const moveSceneDownBtn = document.getElementById('moveSceneDownBtn');
const openSceneTransitionsBtn = document.getElementById('openSceneTransitionsBtn');
const dockTransitionSelect = document.getElementById('dockTransitionSelect');
const dockTransitionDuration = document.getElementById('dockTransitionDuration');

const addSourceBtn = document.getElementById('addSourceBtn');
const removeSourceBtn = document.getElementById('removeSourceBtn');
const openSourcePropertiesBtn = document.getElementById('openSourcePropertiesBtn');
const addSourceMenu = document.getElementById('addSourceMenu');
const imageInput = document.getElementById('imageInput');
const slideshowInput = document.getElementById('slideshowInput');
const slideshowAddInput = document.getElementById('slideshowAddInput');
const mediaInput = document.getElementById('mediaInput');
const propFileInput = document.getElementById('propFileInput');
const browserFileInput = document.getElementById('browserFileInput');
const imageFileInput = document.getElementById('imageFileInput');

// Controls Bars
const textControlsBar = document.getElementById('textControlsBar');
const mediaControlsBar = document.getElementById('mediaControlsBar');
const browserControlsBar = document.getElementById('browserControlsBar');

const textPropertiesBtn = document.getElementById('textPropertiesBtn');
const mediaPropertiesBtn = document.getElementById('mediaPropertiesBtn'); 
const browserBarPropertiesBtn = document.getElementById('browserBarPropertiesBtn'); 
const browserTransparentBarCheck = document.getElementById('browserTransparentBarCheck');

// Filters Elements
const textFiltersBtn = document.getElementById('textFiltersBtn');
const mediaFiltersBtn = document.getElementById('mediaFiltersBtn');
const browserFiltersBtn = document.getElementById('browserFiltersBtn');
const universalFiltersModal = document.getElementById('universalFiltersModal');
const closeFiltersBtn = document.getElementById('closeFiltersBtn');
const filterCloseBtn = document.getElementById('filterCloseBtn');
const filterDefaultsBtn = document.getElementById('filterDefaultsBtn');
const filterOpacity = document.getElementById('filterOpacity');
const filterBrightness = document.getElementById('filterBrightness');
const filterContrast = document.getElementById('filterContrast');
const filterSaturation = document.getElementById('filterSaturation');
const filterHue = document.getElementById('filterHue');
const filterOpacityVal = document.getElementById('filterOpacityVal');
const filterBrightnessVal = document.getElementById('filterBrightnessVal');
const filterContrastVal = document.getElementById('filterContrastVal');
const filterSaturationVal = document.getElementById('filterSaturationVal');
const filterHueVal = document.getElementById('filterHueVal');

// Text Properties Elements
const textPropertiesModal = document.getElementById('textPropertiesModal');
const closeTextPropertiesBtn = document.getElementById('closeTextPropertiesBtn');
const textPropertiesPreview = document.getElementById('textPropertiesPreview');
const tpText = document.getElementById('tpText');
const tpFont = document.getElementById('tpFont');
const tpReadFile = document.getElementById('tpReadFile');
const tpFileInput = document.getElementById('tpFileInput');
const tpFileDisplay = document.getElementById('tpFileDisplay');
const tpFilePath = document.getElementById('tpFilePath');
const tpFileBrowseBtn = document.getElementById('tpFileBrowseBtn');
const tpAntialiasing = document.getElementById('tpAntialiasing');
const tpTransform = document.getElementById('tpTransform');
const tpVertical = document.getElementById('tpVertical');
const tpColor = document.getElementById('tpColor');
const tpOpacitySlider = document.getElementById('tpOpacitySlider');
const tpOpacityNum = document.getElementById('tpOpacityNum');
const tpGradient = document.getElementById('tpGradient');
const tpGradientColorContainer = document.getElementById('tpGradientColorContainer');
const tpGradientColor = document.getElementById('tpGradientColor');
const tpBgColor = document.getElementById('tpBgColor');
const tpBgOpacitySlider = document.getElementById('tpBgOpacitySlider');
const tpBgOpacityNum = document.getElementById('tpBgOpacityNum');
const tpAlign = document.getElementById('tpAlign');
const tpValign = document.getElementById('tpValign');
const tpOutline = document.getElementById('tpOutline');

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const downloadRecordingBtn = document.getElementById('downloadRecordingBtn');

const openEditorBtn = document.getElementById('openEditorBtn');
const closeEditorBtn = document.getElementById('closeEditorBtn');
const editorModal = document.getElementById('editorModal');
const editorPreview = document.getElementById('editorPreview');
const videoLibraryEl = document.getElementById('videoLibrary');
const timeline = document.getElementById('timeline');
const timelineTrack = document.getElementById('timelineTrack');
const timelineRuler = document.getElementById('timelineRuler');
const playhead = document.getElementById('playhead');
const cropBtn = document.getElementById('cropBtn');
const exportBtn = document.getElementById('exportBtn');
const insertBtn = document.getElementById('insertBtn'); 

// --- TOP MENU LOGIC ---
let isMenuModeActive = false;
const menuItems = document.querySelectorAll('.menu-item');

menuItems.forEach(item => {
    item.addEventListener('mousedown', (e) => {
        e.stopPropagation(); 
        if (item.classList.contains('active')) {
            closeAllMenus();
        } else {
            closeAllMenus();
            item.classList.add('active');
            isMenuModeActive = true;
        }
    });

    item.addEventListener('mouseenter', () => {
        if (isMenuModeActive && !item.classList.contains('active')) {
            closeAllMenus();
            item.classList.add('active');
        }
    });
});

function closeAllMenus() {
    menuItems.forEach(i => i.classList.remove('active'));
    isMenuModeActive = false;
}

document.addEventListener('mousedown', (e) => {
    if (!e.target.closest('.obs-menu')) closeAllMenus();
});

// --- CUSTOM ALERT LOGIC ---
function showCustomAlert(message) {
    document.getElementById('customAlertMessage').textContent = message;
    openModalCenter('customAlertModal');
}

// --- DRAGGABLE MODALS ---
function makeWindowDraggable(win) {
    const header = win.querySelector('.window-header');
    if (!header) return;
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    header.onmousedown = (e) => {
        if(e.target.tagName === 'BUTTON' || e.target.closest('.close-btn') || e.target.closest('.undock-btn')) return;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDrag;
        document.onmousemove = elementDrag;
        
        if (win.style.transform.includes('translate')) {
            const rect = win.getBoundingClientRect();
            win.style.transform = 'none';
            win.style.left = rect.left + 'px';
            win.style.top = rect.top + 'px';
        }
    };
    
    function elementDrag(e) {
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        win.style.top = (win.offsetTop - pos2) + "px";
        win.style.left = (win.offsetLeft - pos1) + "px";
    }
    
    function closeDrag() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

document.querySelectorAll('.obs-window').forEach(makeWindowDraggable);

function openModalCenter(modalId) {
    closeAllMenus();
    const m = document.getElementById(modalId);
    m.classList.add('active');
    const win = m.querySelector('.obs-window');
    if (win) {
        win.style.transform = 'translate(-50%, -50%)';
        win.style.left = '50%';
        win.style.top = '50%';
    }
}

// --- DOCK UNDOCKING LOGIC ---
const docks = document.querySelectorAll('.dock');
docks.forEach(dock => {
    const undockBtn = dock.querySelector('.undock-btn');
    if (!undockBtn) return;
    
    const header = dock.querySelector('.dock-header');
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    function dragDockMouseDown(e) {
        if (!dock.classList.contains('popped-out')) return;
        if (e.target.closest('.undock-btn')) return;
        
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDockDrag;
        document.onmousemove = dockDrag;
    }

    function dockDrag(e) {
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        dock.style.top = (dock.offsetTop - pos2) + "px";
        dock.style.left = (dock.offsetLeft - pos1) + "px";
    }

    function closeDockDrag() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
    
    header.addEventListener('mousedown', dragDockMouseDown);

    undockBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (dock.classList.contains('popped-out')) {
            // Return to dock
            dock.classList.remove('popped-out');
            dock.style.position = '';
            dock.style.top = '';
            dock.style.left = '';
            dock.style.zIndex = '';
            dock.style.width = '';
            dock.style.height = '';
            undockBtn.innerHTML = '<i class="far fa-clone"></i>';
            
            // Re-insert in specific order based on data-order attribute
            const order = parseInt(dock.dataset.order);
            const siblings = Array.from(mainDocksContainer.children);
            let inserted = false;
            for (let i = 0; i < siblings.length; i++) {
                const sibOrder = parseInt(siblings[i].dataset.order);
                if (sibOrder > order) {
                    mainDocksContainer.insertBefore(dock, siblings[i]);
                    inserted = true;
                    break;
                }
            }
            if (!inserted) mainDocksContainer.appendChild(dock);
            
        } else {
            // Pop out
            const rect = dock.getBoundingClientRect();
            dock.classList.add('popped-out');
            dock.style.left = rect.left + 'px';
            dock.style.top = rect.top + 'px';
            dock.style.width = rect.width + 'px';
            dock.style.height = rect.height + 'px';
            document.body.appendChild(dock); 
            undockBtn.innerHTML = '<i class="fas fa-window-restore"></i>';
        }
    });
});


// --- MODAL EVENT LISTENERS ---
document.getElementById('menuSettingsBtn').addEventListener('click', () => openModalCenter('settingsModal'));
document.getElementById('closeSettingsBtn').addEventListener('click', () => document.getElementById('settingsModal').classList.remove('active'));
document.getElementById('saveSettingsBtn').addEventListener('click', () => document.getElementById('settingsModal').classList.remove('active'));
document.getElementById('canvasResolution').addEventListener('change', (e) => {
    const res = e.target.value.split('x');
    const w = parseInt(res[0]);
    const h = parseInt(res[1]);
    obsCanvas.width = w;
    obsCanvas.height = h;
    obsCanvasTop.width = w;
    obsCanvasTop.height = h;
    liveRenderCanvas.width = w;
    liveRenderCanvas.height = h;
});

// Stats Modal Logic
document.querySelectorAll('.open-stats-btn').forEach(btn => {
    btn.addEventListener('click', () => openModalCenter('statsModal'));
});
document.getElementById('closeStatsHeaderBtn').addEventListener('click', () => document.getElementById('statsModal').classList.remove('active'));
document.getElementById('closeStatsBtn').addEventListener('click', () => document.getElementById('statsModal').classList.remove('active'));
document.getElementById('resetStatsBtn').addEventListener('click', () => {
    document.getElementById('statMissedFrames').textContent = '0 / 0 (0.0%)';
    document.getElementById('statSkippedFrames').textContent = '0 / 0 (0.0%)';
    document.getElementById('statRecData').textContent = '0.0 MiB';
    document.getElementById('statRecBitrate').textContent = '0 kb/s';
});

// --- SOURCE CLASSES ---
class ObsSource {
    constructor(id, name, type) {
        this.id = id;
        this.name = name;
        this.type = type; 
        this.x = 0;
        this.y = 0;
        this.width = 400; 
        this.height = 300; 
        this.rotation = 0; 
        this.element = null; 
        this.aspectRatio = 16/9;
        this.isAudioOnly = false;
        this.isVisible = true; 
        this.isLocked = false; 
        this.gainNode = null;  
        this.analyserL = null; 
        this.analyserR = null; 
        this.audioMerger = null; // Used for universal dynamic audio routing
        
        // Universal Source Filters
        this.filters = {
            opacity: 100,
            brightness: 100,
            contrast: 100,
            saturation: 100,
            hue: 0
        };

        // Text Source Properties
        this.text = "Sample Text";
        this.fontSize = 72;
        this.textProps = {
            font: "Arial",
            readFile: false,
            filePath: "",
            antialiasing: true,
            transform: "none",
            vertical: false,
            color: "#ffffff",
            opacity: 100,
            gradient: false,
            gradientColor: "#0000ff",
            bgColor: "#000000",
            bgOpacity: 0,
            align: "left",
            valign: "top",
            outline: false
        };

        // Audio Input Properties
        this.audioProps = {
            gain: 100,
            noiseSuppression: true,
            echoCancellation: true,
            autoGain: false
        };

        // Image Source Properties
        this.imageProps = {
            localFile: true,
            filePath: '',
            transparent: false,
            flipH: false,
            flipV: false,
            opacity: 100,
            blendMode: 'source-over'
        };

        // Media Properties Storage
        this.mediaProps = {
            localFile: true,
            filePath: '',
            loop: false,
            restartActive: true,
            hardwareDecode: false,
            showNothing: true,
            closeInactive: false,
            speed: 100,
            yuvRange: 'auto',
            alpha: false,
            ffmpeg: ''
        };

        // Slideshow Properties Storage
        this.slideProps = {
            visibility: 'always',
            mode: 'auto',
            transition: 'cut',
            timeBetween: 2000,
            transitionSpeed: 700,
            playbackMode: 'loop',
            hideWhenDone: false,
            boundingSize: '1920x1080'
        };
        this.images = [];
        this.imageNames = [];
        this.currentSlide = 0;
        this.lastSlideTime = performance.now();
        this.isFinished = false;
        this.isSlideTransitioning = false;
        this.slideTransitionStartTime = 0;
        this.prevSlide = 0;

        // Browser Properties Storage
        this.browserProps = {
            localFile: false,
            url: 'https://shorturl.at/6QyYn',
            width: 800,
            height: 600,
            transparent: true,
            controlAudio: false,
            customFPS: false,
            customCSS: 'body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }',
            shutdownNotVisible: false,
            refreshOnActive: false,
            permissions: 'read_status',
            zoom: 0.8
        };
        
        // Nested Scene Properties
        this.targetSceneId = null;
        this.offscreenCanvas = null;

        // Color Source Properties
        this.colorProps = {
            color: '#ffffff',
            width: 1920,
            height: 1080,
            opacity: 100
        };

        // Display Capture Properties
        this.displayProps = {
            captureMethod: 'auto',
            captureCursor: true,
            forceSDR: false
        };
    }
}

function snap(value) { return Math.round(value / GRID_SIZE) * GRID_SIZE; }

function updateAudioMeters() {
    sources.forEach(src => {
        if (src.analyserL && document.getElementById(`meter-L-${src.id}`)) {
            const dataArrayL = new Float32Array(src.analyserL.fftSize);
            src.analyserL.getFloatTimeDomainData(dataArrayL);
            let sumSquaresL = 0.0;
            for (let i = 0; i < dataArrayL.length; i++) sumSquaresL += dataArrayL[i] * dataArrayL[i];
            const rmsL = Math.sqrt(sumSquaresL / dataArrayL.length);
            let dbL = 20 * Math.log10(rmsL);
            let widthL = dbL > -60 ? ((dbL + 60) / 60) * 100 : 0;
            document.getElementById(`meter-L-${src.id}`).style.width = `${Math.min(100, Math.max(0, widthL))}%`;
        }

        if (src.analyserR && document.getElementById(`meter-R-${src.id}`)) {
            const dataArrayR = new Float32Array(src.analyserR.fftSize);
            src.analyserR.getFloatTimeDomainData(dataArrayR);
            let sumSquaresR = 0.0;
            for (let i = 0; i < dataArrayR.length; i++) sumSquaresR += dataArrayR[i] * dataArrayR[i];
            const rmsR = Math.sqrt(sumSquaresR / dataArrayR.length);
            let dbR = 20 * Math.log10(rmsR);
            let widthR = dbR > -60 ? ((dbR + 60) / 60) * 100 : 0;
            document.getElementById(`meter-R-${src.id}`).style.width = `${Math.min(100, Math.max(0, widthR))}%`;
        }
    });
}

// Generate CSS Filter String for Canvas/DOM Elements
function getUniversalFilterString(src) {
    if (!src || !src.filters) return 'none';
    const f = src.filters;
    let filterString = '';
    
    // For browser specifically, inject chroma key if transparent is checked
    if (src.type === 'browser' && src.browserProps.transparent) {
        filterString += 'url(#chroma-key-white) ';
    }
    
    // For Image Source specifically, inject chroma key if transparent is checked
    if (src.type === 'image' && src.imageProps && src.imageProps.transparent) {
        filterString += 'url(#chroma-key-white) ';
    }
    
    filterString += `opacity(${f.opacity}%) `;
    filterString += `brightness(${f.brightness}%) `;
    filterString += `contrast(${f.contrast}%) `;
    filterString += `saturate(${f.saturation}%) `;
    filterString += `hue-rotate(${f.hue}deg) `;
    return filterString.trim() || 'none';
}

function applyDOMFilters(src) {
    if (!src) return;
    if (src.type === 'browser' && src.iframe) {
        src.iframe.style.filter = getUniversalFilterString(src);
    }
}


// --- GDI+ TEXT RENDERING ENGINE ---
function hexToRgba(hex, opacity) {
    let r = 0, g = 0, b = 0;
    if (hex.length === 4) {
        r = parseInt(hex[1] + hex[1], 16);
        g = parseInt(hex[2] + hex[2], 16);
        b = parseInt(hex[3] + hex[3], 16);
    } else if (hex.length === 7) {
        r = parseInt(hex.substring(1, 3), 16);
        g = parseInt(hex.substring(3, 5), 16);
        b = parseInt(hex.substring(5, 7), 16);
    }
    return `rgba(${r}, ${g}, ${b}, ${opacity / 100})`;
}

function drawObsText(targetCtx, src, drawWidth, drawHeight) {
    let txt = src.text;
    const props = src.textProps;
    
    // Handle Transforms
    if (props.transform === 'uppercase') txt = txt.toUpperCase();
    else if (props.transform === 'lowercase') txt = txt.toLowerCase();
    else if (props.transform === 'startcase') txt = txt.replace(/\w\S*/g, w => (w.replace(/^\w/, c => c.toUpperCase())));

    targetCtx.font = `${src.fontSize}px ${props.font}`;
    
    // Measure bounding box safely
    const lines = txt.split('\n');
    let maxLineWidth = 0;
    const lineHeight = src.fontSize * 1.2;
    
    lines.forEach(line => {
        let width = 0;
        if (props.vertical) {
            for(let i=0; i<line.length; i++) {
                width = Math.max(width, targetCtx.measureText(line[i]).width);
            }
        } else {
            width = targetCtx.measureText(line).width;
        }
        maxLineWidth = Math.max(maxLineWidth, width);
    });

    const totalHeight = props.vertical ? (lines[0].length * lineHeight) : (lines.length * lineHeight);
    const totalWidth = props.vertical ? (lines.length * lineHeight) : maxLineWidth;

    // Apply Background
    if (props.bgOpacity > 0) {
        targetCtx.fillStyle = hexToRgba(props.bgColor, props.bgOpacity);
        targetCtx.fillRect(-drawWidth/2, -drawHeight/2, drawWidth, drawHeight);
    }

    // Apply Gradients and Color
    let textFillStyle = hexToRgba(props.color, props.opacity);
    if (props.gradient) {
        const grad = targetCtx.createLinearGradient(-totalWidth/2, -totalHeight/2, totalWidth/2, totalHeight/2);
        grad.addColorStop(0, hexToRgba(props.color, props.opacity));
        grad.addColorStop(1, hexToRgba(props.gradientColor, props.opacity));
        textFillStyle = grad;
    }
    
    targetCtx.fillStyle = textFillStyle;
    targetCtx.textBaseline = 'top';

    // Anti-aliasing hack (slight blur if disabled, canvas is inherently AA'd)
    if (!props.antialiasing) targetCtx.imageSmoothingEnabled = false;

    // Alignment offsets
    let startX = -drawWidth / 2;
    let startY = -drawHeight / 2;

    if (props.align === 'center') {
        startX = 0;
        targetCtx.textAlign = 'center';
    } else if (props.align === 'right') {
        startX = drawWidth / 2;
        targetCtx.textAlign = 'right';
    } else {
        targetCtx.textAlign = 'left';
    }

    if (props.valign === 'center') {
        startY = -totalHeight / 2;
    } else if (props.valign === 'bottom') {
        startY = drawHeight / 2 - totalHeight;
    }

    // Render Text
    lines.forEach((line, index) => {
        if (props.vertical) {
            targetCtx.textAlign = 'center';
            for(let i=0; i<line.length; i++) {
                const charX = startX + (index * lineHeight) + (lineHeight/2);
                const charY = startY + (i * lineHeight);
                
                if (props.outline) {
                    targetCtx.strokeStyle = 'black';
                    targetCtx.lineWidth = 2;
                    targetCtx.strokeText(line[i], charX, charY);
                }
                targetCtx.fillText(line[i], charX, charY);
            }
        } else {
            const lineY = startY + (index * lineHeight);
            
            if (props.outline) {
                targetCtx.strokeStyle = 'black';
                targetCtx.lineWidth = 2;
                targetCtx.strokeText(line, startX, lineY);
            }
            targetCtx.fillText(line, startX, lineY);
        }
    });

    targetCtx.imageSmoothingEnabled = true; // reset
}

// Draw a placeholder block for Browser Sources that can be captured securely by standard Canvas renderings
function drawBrowserPlaceholder(targetCtx, src) {
    targetCtx.fillStyle = '#1d1f26';
    targetCtx.fillRect(-src.width / 2, -src.height / 2, src.width, src.height);
    targetCtx.strokeStyle = '#3c404d';
    targetCtx.lineWidth = 4;
    targetCtx.strokeRect(-src.width / 2, -src.height / 2, src.width, src.height);
    targetCtx.fillStyle = '#dfdfdf';
    targetCtx.font = `bold ${Math.max(16, src.height/15)}px sans-serif`;
    targetCtx.textAlign = 'center';
    targetCtx.textBaseline = 'middle';
    targetCtx.fillText('🌐 Browser Source', 0, -src.height/15);
    targetCtx.font = `${Math.max(12, src.height/25)}px monospace`;
    targetCtx.fillStyle = '#888888';
    let u = src.browserProps.url;
    if (u.length > 40) u = u.substring(0,37) + '...';
    targetCtx.fillText(u, 0, src.height/15);
}


// --- 1. COMPOSITING DUAL-CANVAS RENDER LOOP ---
let frameCount = 0;
let lastTime = performance.now();
let currentFps = 60;
let currentRenderTime = 0.8;

function updateStatsUI() {
    document.getElementById('footerFps').textContent = currentFps.toFixed(2);
    const mockCpu = (2.0 + Math.random() * 1.5).toFixed(1);
    document.getElementById('footerCpu').textContent = mockCpu;

    if (document.getElementById('statsModal').classList.contains('active')) {
        document.getElementById('statFps').textContent = currentFps.toFixed(2);
        document.getElementById('statRenderTime').textContent = currentRenderTime.toFixed(1) + ' ms';
        document.getElementById('statMemory').textContent = (140 + Math.random() * 10).toFixed(1) + ' MB';
        document.getElementById('statCpu').textContent = mockCpu + '%';
    }
}
setInterval(updateStatsUI, 1000);

// Visual Core Rendering engine for Transitions
function drawTransition(tCtx, w, h, progress, effect, canvasA, canvasB) {
    tCtx.clearRect(0, 0, w, h);
    if (effect === 'none' || effect === 'cut') {
        tCtx.drawImage(canvasB, 0, 0, w, h);
        return;
    }

    if (effect === 'fade') {
        tCtx.drawImage(canvasB, 0, 0, w, h);
        tCtx.globalAlpha = 1 - progress;
        tCtx.drawImage(canvasA, 0, 0, w, h);
        tCtx.globalAlpha = 1.0;
    } else if (effect === 'slide-left' || effect === 'slide' || effect === 'swipe') {
        tCtx.drawImage(canvasA, -progress * w, 0, w, h);
        tCtx.drawImage(canvasB, w - progress * w, 0, w, h);
    } else if (effect === 'slide-right') {
        tCtx.drawImage(canvasA, progress * w, 0, w, h);
        tCtx.drawImage(canvasB, -w + progress * w, 0, w, h);
    } else if (effect === 'slide-up') {
        tCtx.drawImage(canvasA, 0, -progress * h, w, h);
        tCtx.drawImage(canvasB, 0, h - progress * h, w, h);
    } else if (effect === 'slide-down') {
        tCtx.drawImage(canvasA, 0, progress * h, w, h);
        tCtx.drawImage(canvasB, 0, -h + progress * h, w, h);
    } else if (effect === 'zoom-in') {
        tCtx.drawImage(canvasA, 0, 0, w, h);
        tCtx.save();
        tCtx.translate(w/2, h/2);
        tCtx.scale(progress, progress);
        tCtx.globalAlpha = progress;
        tCtx.drawImage(canvasB, -w/2, -h/2, w, h);
        tCtx.restore();
    } else if (effect === 'circle-crop') {
        tCtx.drawImage(canvasA, 0, 0, w, h);
        tCtx.save();
        tCtx.beginPath();
        tCtx.arc(w/2, h/2, progress * Math.max(w,h), 0, Math.PI*2);
        tCtx.clip();
        tCtx.drawImage(canvasB, 0, 0, w, h);
        tCtx.restore();
    } else if (effect === 'spin') {
        tCtx.save();
        tCtx.translate(w/2, h/2);
        tCtx.rotate(progress * Math.PI * 2);
        tCtx.scale(progress, progress);
        tCtx.drawImage(canvasB, -w/2, -h/2, w, h);
        tCtx.restore();

        tCtx.save();
        tCtx.globalAlpha = 1 - progress;
        tCtx.translate(w/2, h/2);
        tCtx.rotate(progress * Math.PI * 2);
        tCtx.scale(1-progress, 1-progress);
        tCtx.drawImage(canvasA, -w/2, -h/2, w, h);
        tCtx.restore();
    } else if (effect === 'melt') {
        tCtx.drawImage(canvasB, 0, 0, w, h);
        const slices = 40;
        const sliceW = w / slices;
        for(let i=0; i<slices; i++) {
            const speed = 1 + ((i * 17) % 5) * 0.5;
            const drop = progress * h * speed;
            if (drop < h) {
                tCtx.drawImage(canvasA, i*sliceW, 0, sliceW, h, i*sliceW, drop, sliceW, h);
            }
        }
    } else if (effect === 'fall-apart') {
        tCtx.drawImage(canvasB, 0, 0, w, h);
        const cols = 10;
        const rows = 10;
        const cellW = w/cols;
        const cellH = h/rows;
        for(let c=0; c<cols; c++){
            for(let r=0; r<rows; r++){
                const rand = ((c*7 + r*11) % 10) / 10; 
                const delay = rand * 0.5;
                let cellP = (progress - delay) / (1 - delay);
                if(cellP < 0) cellP = 0;
                if(cellP > 1) cellP = 1;
                
                if (cellP < 1) {
                    const fallY = cellP * cellP * h;
                    const rot = cellP * rand * Math.PI;
                    tCtx.save();
                    tCtx.translate(c*cellW + cellW/2, r*cellH + cellH/2 + fallY);
                    tCtx.rotate(rot);
                    tCtx.globalAlpha = 1 - cellP;
                    tCtx.drawImage(canvasA, c*cellW, r*cellH, cellW, cellH, -cellW/2, -cellH/2, cellW, cellH);
                    tCtx.restore();
                }
            }
        }
    }
}


function renderLoop() {
    const renderStartTime = performance.now();
    const now = performance.now();
    
    // Fill the hidden live composite canvas with black to prevent transparent drop-shadow bugs on exports/transitions
    liveCtx.fillStyle = '#000';
    liveCtx.fillRect(0, 0, liveRenderCanvas.width, liveRenderCanvas.height);
    
    // Fill Base UI canvas with black (acting as the physical background behind all iframes/overlays)
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, obsCanvas.width, obsCanvas.height);
    
    // Clear the completely transparent Top Canvas Sandwich layer
    topCtx.clearRect(0, 0, obsCanvasTop.width, obsCanvasTop.height);

    let hasVisibleSource = false;
    let highestBrowserIndex = -1;

    // Determine our split layer threshold
    for (let i = 0; i < sources.length; i++) {
        if (sources[i].type === 'browser' && sources[i].isVisible) {
            highestBrowserIndex = i;
        }
    }

    for (let i = 0; i < sources.length; i++) {
        const src = sources[i];
        if (!src.isVisible) continue;
        if (!src.isAudioOnly && src.type !== 'browser') hasVisibleSource = true;

        // ======================================================
        // 1. LIVE RENDER PASS (Updates internal visual states & creates single flattened composite)
        // ======================================================
        liveCtx.save(); 
        const cx = src.x + src.width / 2;
        const cy = src.y + src.height / 2;
        liveCtx.translate(cx, cy);
        liveCtx.rotate(src.rotation);
        liveCtx.filter = getUniversalFilterString(src); // APPLY FILTERS
        
        if (src.type === 'text') {
            // Update physical bounds dynamically before drawing
            liveCtx.font = `${src.fontSize}px ${src.textProps.font}`;
            const lines = src.text.split('\n');
            let maxW = 0;
            lines.forEach(l => { maxW = Math.max(maxW, liveCtx.measureText(l).width); });
            const lineH = src.fontSize * 1.2;
            
            if (src.textProps.vertical) {
                src.width = lines.length * lineH;
                src.height = (lines[0] ? lines[0].length : 1) * lineH;
            } else {
                src.width = maxW;
                src.height = lines.length * lineH;
            }
            
            drawObsText(liveCtx, src, src.width, src.height);
        } 
        else if (src.type === 'color') {
            liveCtx.fillStyle = hexToRgba(src.colorProps.color, src.colorProps.opacity);
            liveCtx.fillRect(-src.width / 2, -src.height / 2, src.width, src.height);
        }
        else if (src.type === 'browser') {
            drawBrowserPlaceholder(liveCtx, src);
        }
        else if (src.type === 'slideshow' && src.images && src.images.length > 0) {
            let drawW = src.width;
            let drawH = src.height;
            let timeInSlide = now - src.lastSlideTime;

            if (src.slideProps.mode === 'auto' && !src.isFinished) {
                if (!src.isSlideTransitioning && timeInSlide > src.slideProps.timeBetween) {
                    src.prevSlide = src.currentSlide;
                    
                    if (src.slideProps.playbackMode === 'random') {
                        src.currentSlide = Math.floor(Math.random() * src.images.length);
                    } else {
                        src.currentSlide = src.currentSlide + 1;
                    }

                    if (src.currentSlide >= src.images.length) {
                        if (src.slideProps.playbackMode === 'once') {
                            src.currentSlide = src.images.length - 1;
                            src.isFinished = true;
                        } else {
                            src.currentSlide = 0;
                        }
                    }

                    if (!src.isFinished) {
                        if (src.slideProps.transition === 'none' || src.slideProps.transition === 'cut') {
                            src.lastSlideTime = now;
                        } else {
                            src.isSlideTransitioning = true;
                            src.slideTransitionStartTime = now;
                        }
                    }
                }
            }

            if (src.slideProps.hideWhenDone && src.isFinished) {
                // draw nothing
            } else {
                if (src.isSlideTransitioning) {
                    let p = (now - src.slideTransitionStartTime) / src.slideProps.transitionSpeed;
                    if (p >= 1) {
                        p = 1;
                        src.isSlideTransitioning = false;
                        src.lastSlideTime = now;
                    }
                    const imgA = src.images[src.prevSlide];
                    const imgB = src.images[src.currentSlide];

                    // Clip bounds to prevent transition bleed outside the slideshow border
                    liveCtx.save();
                    liveCtx.beginPath();
                    liveCtx.rect(-drawW / 2, -drawH / 2, drawW, drawH);
                    liveCtx.clip();

                    // Embedded mini-transition renderer for slideshows
                    if (src.slideProps.transition === 'fade') {
                        if (imgB) liveCtx.drawImage(imgB, -drawW/2, -drawH/2, drawW, drawH);
                        liveCtx.globalAlpha = 1 - p;
                        if (imgA) liveCtx.drawImage(imgA, -drawW/2, -drawH/2, drawW, drawH);
                        liveCtx.globalAlpha = 1;
                    } else if (src.slideProps.transition === 'slide' || src.slideProps.transition === 'swipe') {
                        if (imgA) liveCtx.drawImage(imgA, -drawW/2 - (drawW * p), -drawH/2, drawW, drawH);
                        if (imgB) liveCtx.drawImage(imgB, -drawW/2 + drawW - (drawW * p), -drawH/2, drawW, drawH);
                    } else {
                        if (imgB) liveCtx.drawImage(imgB, -drawW/2, -drawH/2, drawW, drawH);
                    }
                    
                    liveCtx.restore();

                } else {
                    const img = src.images[src.currentSlide];
                    if (img && img.complete) {
                        liveCtx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH);
                    }
                }
            }
        }
        else if (src.type === 'scene' && src.targetSceneId) {
            // Nested Scene Render Logic
            const targetScene = scenes.find(s => s.id === src.targetSceneId);
            if (targetScene && src.offscreenCanvas) {
                const oCtx = src.offscreenCanvas.getContext('2d');
                oCtx.clearRect(0, 0, src.offscreenCanvas.width, src.offscreenCanvas.height);
                
                targetScene.sources.forEach(nSrc => {
                    if (!nSrc.isVisible || nSrc.isAudioOnly) return; 
                    
                    oCtx.save();
                    const ncx = nSrc.x + nSrc.width / 2;
                    const ncy = nSrc.y + nSrc.height / 2;
                    oCtx.translate(ncx, ncy);
                    oCtx.rotate(nSrc.rotation);
                    oCtx.filter = getUniversalFilterString(nSrc);
                    
                    if (nSrc.type === 'text') {
                        oCtx.font = `${nSrc.fontSize}px ${nSrc.textProps.font}`;
                        const lines = nSrc.text.split('\n');
                        let maxW = 0;
                        lines.forEach(l => { maxW = Math.max(maxW, oCtx.measureText(l).width); });
                        const lineH = nSrc.fontSize * 1.2;
                        if (nSrc.textProps.vertical) {
                            nSrc.width = lines.length * lineH;
                            nSrc.height = (lines[0] ? lines[0].length : 1) * lineH;
                        } else {
                            nSrc.width = maxW;
                            nSrc.height = lines.length * lineH;
                        }
                        drawObsText(oCtx, nSrc, nSrc.width, nSrc.height);
                    } else if (nSrc.type === 'color') {
                        oCtx.fillStyle = hexToRgba(nSrc.colorProps.color, nSrc.colorProps.opacity);
                        oCtx.fillRect(-nSrc.width / 2, -nSrc.height / 2, nSrc.width, nSrc.height);
                    } else if (nSrc.type === 'browser') {
                        drawBrowserPlaceholder(oCtx, nSrc);
                    } else if (nSrc.type === 'slideshow' && nSrc.images && nSrc.images.length > 0) {
                        const img = nSrc.images[nSrc.currentSlide];
                        if (img && img.complete) oCtx.drawImage(img, -nSrc.width/2, -nSrc.height/2, nSrc.width, nSrc.height);
                    } else if (nSrc.element) {
                        try {
                            if (nSrc.type === 'image' && nSrc.imageProps) {
                                oCtx.globalAlpha = (nSrc.imageProps.opacity / 100) * (nSrc.filters.opacity / 100);
                                oCtx.globalCompositeOperation = nSrc.imageProps.blendMode;
                                oCtx.scale(nSrc.imageProps.flipH ? -1 : 1, nSrc.imageProps.flipV ? -1 : 1);
                            }
                            oCtx.drawImage(nSrc.element, -nSrc.width/2, -nSrc.height/2, nSrc.width, nSrc.height); 
                        } catch(e){}
                    }
                    oCtx.restore();
                });
                liveCtx.drawImage(src.offscreenCanvas, -src.width/2, -src.height/2, src.width, src.height);
            }
        }
        else if (src.element && !src.isAudioOnly) {
            try { 
                // Draw normal media, canvas handles playing videos fine without DOM attachment if we step the frames
                if (src.element instanceof HTMLImageElement || src.element.readyState >= 2) {
                    
                    if (src.type === 'image' && src.imageProps) {
                        liveCtx.globalAlpha = (src.imageProps.opacity / 100) * (src.filters.opacity / 100);
                        liveCtx.globalCompositeOperation = src.imageProps.blendMode;
                        liveCtx.scale(src.imageProps.flipH ? -1 : 1, src.imageProps.flipV ? -1 : 1);
                    }
                    
                    liveCtx.drawImage(src.element, -src.width / 2, -src.height / 2, src.width, src.height); 
                }
            } catch (e) { }
        }
        liveCtx.restore(); 
        
        // ======================================================
        // 2. LAYERED PREVIEW PASS (Z-Index Sandwiching for the User UI)
        // ======================================================
        
        // Pick the correct split canvas (Behind the Iframe vs In Front of the Iframe)
        let displayCtx = (i > highestBrowserIndex) ? topCtx : ctx;
        
        displayCtx.save();
        displayCtx.translate(cx, cy);
        displayCtx.rotate(src.rotation);
        displayCtx.filter = getUniversalFilterString(src); // APPLY FILTERS
        
        if (src.type === 'text') {
            drawObsText(displayCtx, src, src.width, src.height);
        } else if (src.type === 'color') {
            displayCtx.fillStyle = hexToRgba(src.colorProps.color, src.colorProps.opacity);
            displayCtx.fillRect(-src.width / 2, -src.height / 2, src.width, src.height);
        } else if (src.type === 'slideshow' && src.images && src.images.length > 0) {
            let drawW = src.width;
            let drawH = src.height;
            // Note: states (p, times) were safely advanced in liveCtx loop just above. 
            if (src.isSlideTransitioning) {
                let p = (now - src.slideTransitionStartTime) / src.slideProps.transitionSpeed;
                if (p > 1) p = 1;
                const imgA = src.images[src.prevSlide];
                const imgB = src.images[src.currentSlide];

                displayCtx.save();
                displayCtx.beginPath();
                displayCtx.rect(-drawW / 2, -drawH / 2, drawW, drawH);
                displayCtx.clip();

                if (src.slideProps.transition === 'fade') {
                    if (imgB) displayCtx.drawImage(imgB, -drawW/2, -drawH/2, drawW, drawH);
                    displayCtx.globalAlpha = 1 - p;
                    if (imgA) displayCtx.drawImage(imgA, -drawW/2, -drawH/2, drawW, drawH);
                    displayCtx.globalAlpha = 1;
                } else if (src.slideProps.transition === 'slide' || src.slideProps.transition === 'swipe') {
                    if (imgA) displayCtx.drawImage(imgA, -drawW/2 - (drawW * p), -drawH/2, drawW, drawH);
                    if (imgB) displayCtx.drawImage(imgB, -drawW/2 + drawW - (drawW * p), -drawH/2, drawW, drawH);
                } else {
                    if (imgB) displayCtx.drawImage(imgB, -drawW/2, -drawH/2, drawW, drawH);
                }
                displayCtx.restore();
            } else {
                const img = src.images[src.currentSlide];
                if (img && img.complete) {
                    displayCtx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH);
                }
            }
        } 
        else if (src.type === 'scene' && src.targetSceneId) {
            // Read from the offscreen canvas already built by liveCtx
            if (src.offscreenCanvas) {
                displayCtx.drawImage(src.offscreenCanvas, -src.width/2, -src.height/2, src.width, src.height);
            }
        }
        else if (src.element && !src.isAudioOnly) {
            try { 
                if (src.element instanceof HTMLImageElement || src.element.readyState >= 2) {
                    if (src.type === 'image' && src.imageProps) {
                        displayCtx.globalAlpha = (src.imageProps.opacity / 100) * (src.filters.opacity / 100);
                        displayCtx.globalCompositeOperation = src.imageProps.blendMode;
                        displayCtx.scale(src.imageProps.flipH ? -1 : 1, src.imageProps.flipV ? -1 : 1);
                    }
                    displayCtx.drawImage(src.element, -src.width / 2, -src.height / 2, src.width, src.height); 
                }
            } catch (e) { }
        }
        displayCtx.restore();
    }

    // MAIN COMPOSITING TRANSITION ENGINE
    if (isTransitioning) {
        const elapsed = now - transitionStartTime;
        let progress = elapsed / activeTransitionDuration;
        if (progress >= 1) {
            progress = 1;
            isTransitioning = false;
        }
        
        // Hide overlay canvases entirely during transitions to show the smooth canvas melt/slide logic
        obsCanvasTop.style.opacity = '0';
        document.getElementById('domOverlayContainer').style.opacity = '0';
        drawTransition(ctx, obsCanvas.width, obsCanvas.height, progress, activeTransition, outgoingCanvas, liveRenderCanvas);
    } else {
        obsCanvasTop.style.opacity = '1';
        document.getElementById('domOverlayContainer').style.opacity = '1';
        // Base layers were manually built inside the `for` loop, so we don't draw `liveRenderCanvas` over them.
    }

    // DRAW OVERLAYS & SELECTION HANDLES TO THE TOP CANVAS ONLY (Ensures they are NEVER hidden behind iframes)
    for (let i = 0; i < sources.length; i++) {
        const src = sources[i];
        if (!src.isVisible || src.isAudioOnly || src.isLocked) continue;

        if (selectedSource === src && !isTransitioning) {
            topCtx.save();
            const cx = src.x + src.width / 2;
            const cy = src.y + src.height / 2;
            topCtx.translate(cx, cy);
            topCtx.rotate(src.rotation);

            topCtx.strokeStyle = '#ff0000';
            topCtx.lineWidth = 8; 
            
            // Draw main bounding box
            topCtx.strokeRect(-src.width / 2, -src.height / 2, src.width, src.height);

            topCtx.fillStyle = '#ff0000';
            const hw = 16; 
            
            // Draw corner handles
            topCtx.fillRect(-src.width / 2 - hw/2, -src.height / 2 - hw/2, hw, hw); 
            topCtx.fillRect(src.width / 2 - hw/2, -src.height / 2 - hw/2, hw, hw); 
            topCtx.fillRect(-src.width / 2 - hw/2, src.height / 2 - hw/2, hw, hw); 
            topCtx.fillRect(src.width / 2 - hw/2, src.height / 2 - hw/2, hw, hw); 

            // Draw middle edge handles
            topCtx.fillRect(-hw/2, -src.height / 2 - hw/2, hw, hw); 
            topCtx.fillRect(-hw/2, src.height / 2 - hw/2, hw, hw); 
            topCtx.fillRect(-src.width / 2 - hw/2, -hw/2, hw, hw); 
            topCtx.fillRect(src.width / 2 - hw/2, -hw/2, hw, hw); 

            // Draw rotation stick
            topCtx.beginPath();
            topCtx.moveTo(0, -src.height / 2);
            topCtx.lineTo(0, -src.height / 2 - 40);
            topCtx.lineWidth = 2;
            topCtx.strokeStyle = '#ff0000';
            topCtx.stroke();
            
            topCtx.fillStyle = '#ff0000';
            topCtx.beginPath();
            topCtx.arc(0, -src.height / 2 - 40, 10, 0, Math.PI * 2);
            topCtx.fill();
            
            topCtx.restore();
        }
    }

    previewPlaceholder.style.display = hasVisibleSource ? 'none' : 'block';
    
    if (selectedSource && selectedSource.type === 'media' && selectedSource.element) {
        const el = selectedSource.element;
        document.getElementById('mediaSeek').value = (el.currentTime / el.duration) * 100 || 0;
        document.getElementById('mediaTime').textContent = `${formatTime(el.currentTime)} / ${formatTime(el.duration)}`;
    }

    updateAudioMeters();
    
    const renderEndTime = performance.now();
    frameCount++;
    if (renderEndTime >= lastTime + 1000) {
        currentFps = (frameCount * 1000) / (renderEndTime - lastTime);
        currentRenderTime = renderEndTime - renderStartTime; 
        frameCount = 0;
        lastTime = renderEndTime;
    }

    // UPDATE BROWSER DOM OVERLAYS TO MATCH CANVAS EXACTLY
    const wrapperRect = document.getElementById('previewWrapper').getBoundingClientRect();
    const rect = obsCanvas.getBoundingClientRect();
    const scale = Math.min(rect.width / obsCanvas.width, rect.height / obsCanvas.height);
    const actualW = obsCanvas.width * scale;
    const actualH = obsCanvas.height * scale;
    const offsetX = rect.left - wrapperRect.left + (rect.width - actualW) / 2;
    const offsetY = rect.top - wrapperRect.top + (rect.height - actualH) / 2;
    
    const overlayContainer = document.getElementById('domOverlayContainer');
    overlayContainer.style.left = offsetX + 'px';
    overlayContainer.style.top = offsetY + 'px';
    overlayContainer.style.width = actualW + 'px';
    overlayContainer.style.height = actualH + 'px';

    sources.forEach(src => {
        if (src.type === 'browser' && src.iframe) {
            if (!src.isVisible || isTransitioning) {
                src.iframe.style.display = 'none';
            } else {
                src.iframe.style.display = 'block';
                
                // Calculate internal CSS width/height utilizing the independent Zoom modifier
                const internalW = src.browserProps.width / src.browserProps.zoom;
                const internalH = src.browserProps.height / src.browserProps.zoom;
                
                // Calculate position scaling precisely from unscaled center to prevent offset drift
                const scaleX = (src.width * scale) / internalW;
                const scaleY = (src.height * scale) / internalH;
                const cx = src.x + src.width / 2;
                const cy = src.y + src.height / 2;

                src.iframe.style.width = internalW + 'px';
                src.iframe.style.height = internalH + 'px';
                
                // Align unscaled layout box dead center, then scale it purely from its own center
                src.iframe.style.left = (cx * scale - internalW / 2) + 'px';
                src.iframe.style.top = (cy * scale - internalH / 2) + 'px';
                
                src.iframe.style.transformOrigin = 'center center';
                src.iframe.style.transform = `rotate(${src.rotation}rad) scale(${scaleX}, ${scaleY})`;
            }
        }
    });

    requestAnimationFrame(renderLoop);
}
renderLoop();

// --- 2. SMART CANVAS INTERACTION ---
let isDragging = false, isResizing = false, isRotating = false;
let dragStartX, dragStartY, resizeHandle = '';
const SNAP_DIST = 15; 

function getCanvasCoords(e) {
    const rect = obsCanvas.getBoundingClientRect();
    const scale = Math.min(rect.width / obsCanvas.width, rect.height / obsCanvas.height);
    const actualW = obsCanvas.width * scale;
    const actualH = obsCanvas.height * scale;
    const offsetX = (rect.width - actualW) / 2;
    const offsetY = (rect.height - actualH) / 2;
    return { 
        x: (e.clientX - rect.left - offsetX) / scale, 
        y: (e.clientY - rect.top - offsetY) / scale 
    };
}

function getLocalCoords(x, y, src) {
    const cx = src.x + src.width / 2;
    const cy = src.y + src.height / 2;
    const dx = x - cx;
    const dy = y - cy;
    const angle = -src.rotation; 
    return {
        lx: dx * Math.cos(angle) - dy * Math.sin(angle) + cx,
        ly: dx * Math.sin(angle) + dy * Math.cos(angle) + cy
    };
}

obsCanvas.addEventListener('mousedown', (e) => {
    const { x, y } = getCanvasCoords(e);
    
    if (selectedSource && !selectedSource.isAudioOnly && !selectedSource.isLocked) {
        const s = selectedSource;
        const { lx, ly } = getLocalCoords(x, y, s);
        const hw = 20; 
        
        if (Math.abs(lx - (s.x + s.width/2)) < hw && Math.abs(ly - (s.y - 40)) < hw) {
            isRotating = true; return;
        }
        
        // Detect corner handles
        if (Math.abs(lx - s.x) < hw && Math.abs(ly - s.y) < hw) { isResizing = true; resizeHandle = 'tl'; return; }
        if (Math.abs(lx - (s.x + s.width)) < hw && Math.abs(ly - s.y) < hw) { isResizing = true; resizeHandle = 'tr'; return; }
        if (Math.abs(lx - s.x) < hw && Math.abs(ly - (s.y + s.height)) < hw) { isResizing = true; resizeHandle = 'bl'; return; }
        if (Math.abs(lx - (s.x + s.width)) < hw && Math.abs(ly - (s.y + s.height)) < hw) { isResizing = true; resizeHandle = 'br'; return; }
        
        // Detect middle handles for independent resizing
        if (Math.abs(lx - (s.x + s.width/2)) < hw && Math.abs(ly - s.y) < hw) { isResizing = true; resizeHandle = 't'; return; }
        if (Math.abs(lx - (s.x + s.width/2)) < hw && Math.abs(ly - (s.y + s.height)) < hw) { isResizing = true; resizeHandle = 'b'; return; }
        if (Math.abs(lx - s.x) < hw && Math.abs(ly - (s.y + s.height/2)) < hw) { isResizing = true; resizeHandle = 'l'; return; }
        if (Math.abs(lx - (s.x + s.width)) < hw && Math.abs(ly - (s.y + s.height/2)) < hw) { isResizing = true; resizeHandle = 'r'; return; }
    }

    let clickedSource = null;
    
    // Create a tiny hidden canvas to do pixel-perfect alpha testing
    const hitCanvas = document.createElement('canvas');
    hitCanvas.width = 1;
    hitCanvas.height = 1;
    const hitCtx = hitCanvas.getContext('2d', { willReadFrequently: true });
    
    for (let i = sources.length - 1; i >= 0; i--) {
        const s = sources[i];
        if (!s.isAudioOnly && s.isVisible && !s.isLocked) {
            const { lx, ly } = getLocalCoords(x, y, s);
            if (lx >= s.x && lx <= s.x + s.width && ly >= s.y && ly <= s.y + s.height) {
                
                let hit = true;
                
                // Pixel perfect hit test for images to allow clicking through 100% transparent areas
                if (s.type === 'image' && s.element) {
                    try {
                        hitCtx.clearRect(0, 0, 1, 1);
                        const localX = lx - s.x;
                        const localY = ly - s.y;
                        hitCtx.drawImage(s.element, -localX, -localY, s.width, s.height);
                        const pixel = hitCtx.getImageData(0, 0, 1, 1).data;
                        if (pixel[3] === 0) hit = false;
                    } catch(e) {}
                } else if (s.type === 'slideshow' && s.images && s.images[s.currentSlide]) {
                    try {
                        hitCtx.clearRect(0, 0, 1, 1);
                        const localX = lx - s.x;
                        const localY = ly - s.y;
                        hitCtx.drawImage(s.images[s.currentSlide], -localX, -localY, s.width, s.height);
                        const pixel = hitCtx.getImageData(0, 0, 1, 1).data;
                        if (pixel[3] === 0) hit = false;
                    } catch(e) {}
                } else if (s.type === 'scene' && s.offscreenCanvas) {
                    try {
                        hitCtx.clearRect(0, 0, 1, 1);
                        const localX = lx - s.x;
                        const localY = ly - s.y;
                        hitCtx.drawImage(s.offscreenCanvas, -localX, -localY, s.width, s.height);
                        const pixel = hitCtx.getImageData(0, 0, 1, 1).data;
                        if (pixel[3] === 0) hit = false;
                    } catch(e) {}
                }
                
                if (hit) {
                    clickedSource = s; 
                    break;
                }
            }
        }
    }

    selectSource(clickedSource);

    if (clickedSource) {
        isDragging = true;
        dragStartX = x - clickedSource.x;
        dragStartY = y - clickedSource.y;
    }
});

window.addEventListener('mousemove', (e) => {
    if (!selectedSource || selectedSource.isLocked) return;
    const { x, y } = getCanvasCoords(e);
    const s = selectedSource;

    if (isDragging) {
        let newX = x - dragStartX;
        let newY = y - dragStartY;

        if (Math.abs(newX) < SNAP_DIST) newX = 0;
        if (Math.abs(newY) < SNAP_DIST) newY = 0;
        if (Math.abs(newX + s.width - obsCanvas.width) < SNAP_DIST) newX = obsCanvas.width - s.width;
        if (Math.abs(newY + s.height - obsCanvas.height) < SNAP_DIST) newY = obsCanvas.height - s.height;

        sources.forEach(other => {
            if (other !== s && other.isVisible && !other.isAudioOnly) {
                if (Math.abs(newX - other.x) < SNAP_DIST) newX = other.x;
                if (Math.abs(newX - (other.x + other.width)) < SNAP_DIST) newX = other.x + other.width;
                if (Math.abs(newX + s.width - other.x) < SNAP_DIST) newX = other.x - s.width;
                if (Math.abs(newX + s.width - (other.x + other.width)) < SNAP_DIST) newX = other.x + other.width - s.width;
                
                if (Math.abs(newY - other.y) < SNAP_DIST) newY = other.y;
                if (Math.abs(newY - (other.y + other.height)) < SNAP_DIST) newY = other.y + other.height; 
                if (Math.abs(newY + s.height - other.y) < SNAP_DIST) newY = other.y - s.height;
                if (Math.abs(newY + s.height - (other.y + other.height)) < SNAP_DIST) newY = other.y + other.height - s.height;
            }
        });

        s.x = newX;
        s.y = newY;
    } 
    else if (isRotating) {
        const cx = s.x + s.width / 2;
        const cy = s.y + s.height / 2;
        let angle = Math.atan2(y - cy, x - cx) + Math.PI / 2; 
        s.rotation = angle; 
    }
    else if (isResizing) {
        const { lx, ly } = getLocalCoords(x, y, s);
        
        let targetX = lx;
        let targetY = ly;

        if (s.rotation === 0) {
            if (Math.abs(targetX) < SNAP_DIST) targetX = 0;
            if (Math.abs(targetX - obsCanvas.width) < SNAP_DIST) targetX = obsCanvas.width;
            if (Math.abs(targetY) < SNAP_DIST) targetY = 0;
            if (Math.abs(targetY - obsCanvas.height) < SNAP_DIST) targetY = obsCanvas.height;
        }
        
        if (s.type === 'text') {
            const oldRight = s.x + s.width;
            const oldBottom = s.y + s.height;
            const oldWidth = s.width;

            let newWidth;
            if (resizeHandle === 'br' || resizeHandle === 'tr') {
                newWidth = Math.max(10, targetX - s.x);
            } else {
                newWidth = Math.max(10, oldRight - targetX);
            }
            
            const scaleRatio = newWidth / oldWidth;
            s.fontSize = Math.max(10, Math.round(s.fontSize * scaleRatio));
            
            // Note: Bounds generation happens in render pass for accurate multiline, 
            // Here we just scale the root fontSize variable.

            if (resizeHandle === 'tr' || resizeHandle === 'tl') {
                s.y = oldBottom - s.height;
            }
            if (resizeHandle === 'bl' || resizeHandle === 'tl') {
                s.x = oldRight - s.width;
            }

            if (selectedSource === s) document.getElementById('textSizeSource').value = s.fontSize;
        } else {
            // Unlock aspect ratio automatically for generic resizeable containers
            let lockAspect = (s.type !== 'slideshow' && s.type !== 'browser' && s.type !== 'scene' && s.type !== 'color' && s.type !== 'display'); 
            
            if (resizeHandle === 'br') {
                s.width = Math.max(10, targetX - s.x);
                if (lockAspect) s.height = s.width / s.aspectRatio;
                else s.height = Math.max(10, targetY - s.y);
            } else if (resizeHandle === 'tr') {
                s.width = Math.max(10, targetX - s.x);
                const oldBottom = s.y + s.height;
                if (lockAspect) s.height = s.width / s.aspectRatio;
                else s.height = Math.max(10, oldBottom - targetY);
                s.y = oldBottom - s.height;
            } else if (resizeHandle === 'bl') {
                const oldRight = s.x + s.width;
                s.width = Math.max(10, oldRight - targetX);
                s.x = oldRight - s.width;
                if (lockAspect) s.height = s.width / s.aspectRatio;
                else s.height = Math.max(10, targetY - s.y);
            } else if (resizeHandle === 'tl') {
                const oldRight = s.x + s.width;
                const oldBottom = s.y + s.height;
                s.width = Math.max(10, oldRight - targetX);
                s.x = oldRight - s.width;
                if (lockAspect) s.height = s.width / s.aspectRatio;
                else s.height = Math.max(10, oldBottom - targetY);
                s.y = oldBottom - s.height;
            } else if (resizeHandle === 't') {
                const oldBottom = s.y + s.height;
                s.height = Math.max(10, oldBottom - targetY);
                s.y = oldBottom - s.height;
            } else if (resizeHandle === 'b') {
                s.height = Math.max(10, targetY - s.y);
            } else if (resizeHandle === 'l') {
                const oldRight = s.x + s.width;
                s.width = Math.max(10, oldRight - targetX);
                s.x = oldRight - s.width;
            } else if (resizeHandle === 'r') {
                s.width = Math.max(10, targetX - s.x);
            }
            
            if (!lockAspect) {
                s.aspectRatio = s.width / s.height;
            }
        }
    }
});

window.addEventListener('mouseup', () => { isDragging = false; isResizing = false; isRotating = false; });

// --- 3. SCENE, TRANSITIONS & SOURCE MANAGEMENT ---

function updateDockTransitions() {
    dockTransitionSelect.value = activeScene.transition;
    dockTransitionDuration.value = activeScene.transitionDuration;
}

dockTransitionSelect.addEventListener('change', (e) => {
    activeScene.transition = e.target.value;
});

dockTransitionDuration.addEventListener('input', (e) => {
    activeScene.transitionDuration = parseInt(e.target.value) || 500;
});


function updateScenesList() {
    scenesListEl.innerHTML = '';
    scenes.forEach(scene => {
        const div = document.createElement('div');
        div.className = `list-item ${activeScene === scene ? 'active' : ''}`;
        div.textContent = scene.name;
        div.onclick = () => switchScene(scene.id);
        scenesListEl.appendChild(div);
    });
}

function updateActiveMediaPlayback() {
    // 1. Collect all active sources (including those hidden deep inside nested scenes)
    let activeSources = [];
    function collectActive(scene) {
        if (!scene) return;
        scene.sources.forEach(src => {
            activeSources.push(src);
            if (src.type === 'scene' && src.targetSceneId) {
                const targetScene = scenes.find(s => s.id === src.targetSceneId);
                collectActive(targetScene);
            }
        });
    }
    collectActive(activeScene);
    
    // 2. Iterate all scenes, pause videos not active on screen, play those that are!
    scenes.forEach(s => {
        s.sources.forEach(src => {
            if (src.element && typeof src.element.pause === 'function') {
                if (activeSources.includes(src)) {
                    if (src.element.paused) {
                        src.element.play().catch(e => console.warn(e));
                    }
                } else {
                    if (!src.element.paused) {
                        src.element.pause();
                    }
                }
            }
        });
    });
}


function switchScene(sceneId) {
    if (activeScene.id === sceneId) return;
    
    const incomingScene = scenes.find(s => s.id === sceneId);
    
    // Process transition buffer using the INCOMING scene's settings
    if (incomingScene.transition !== 'none' && !isTransitioning) {
        outgoingCanvas.getContext('2d').drawImage(liveRenderCanvas, 0, 0, liveRenderCanvas.width, liveRenderCanvas.height);
        activeTransition = incomingScene.transition;
        activeTransitionDuration = incomingScene.transitionDuration;
        isTransitioning = true;
        transitionStartTime = performance.now();
    }
    
    // Switch state pointers
    activeScene = incomingScene;
    sources = activeScene.sources; 
    selectedSource = null;
    
    // Trigger the smart nested playback logic
    updateActiveMediaPlayback();
    
    // Mount iframes for the incoming scene directly
    document.getElementById('domOverlayContainer').innerHTML = '';
    sources.forEach(src => {
        if (src.type === 'browser' && src.iframe) {
            document.getElementById('domOverlayContainer').appendChild(src.iframe);
        }
    });
    
    // Refresh UI
    updateDockTransitions();
    updateScenesList();
    updateSourcesList();
    selectSource(null);
    
    // Re-render audio mixer elements for the new scene
    audioMixerContainer.innerHTML = '';
    sources.forEach(src => {
       if (src.gainNode) renderMixerUI(src);
    });
    
    updateAudioRouting();
}

// Scene Listeners
addSceneBtn.addEventListener('click', () => {
    document.getElementById('sceneNameInput').value = `Scene ${scenes.length + 1}`;
    openModalCenter('addSceneModal');
});

document.getElementById('confirmAddSceneBtn').addEventListener('click', () => {
    const name = document.getElementById('sceneNameInput').value;
    const newScene = new ObsScene(Date.now(), name || 'Unnamed Scene');
    scenes.push(newScene);
    document.getElementById('addSceneModal').classList.remove('active');
    switchScene(newScene.id);
});

removeSceneBtn.addEventListener('click', () => {
    if (scenes.length <= 1) {
        showCustomAlert("You must have at least one scene.");
        return;
    }
    const idx = scenes.indexOf(activeScene);
    scenes.splice(idx, 1);
    const nextScene = scenes[Math.max(0, idx - 1)];
    // Force the switch to re-run, with fixed sources array to prevent crash
    activeScene = { id: 'temp', sources: [], transition: 'none', transitionDuration: 0 }; 
    switchScene(nextScene.id);
});

if (moveSceneUpBtn) {
    moveSceneUpBtn.onclick = () => {
        if (!activeScene) return;
        const idx = scenes.indexOf(activeScene);
        if (idx > 0) { 
            scenes.splice(idx, 1);
            scenes.splice(idx - 1, 0, activeScene);
            updateScenesList();
        }
    };
}

if (moveSceneDownBtn) {
    moveSceneDownBtn.onclick = () => {
        if (!activeScene) return;
        const idx = scenes.indexOf(activeScene);
        if (idx < scenes.length - 1) { 
            scenes.splice(idx, 1);
            scenes.splice(idx + 1, 0, activeScene);
            updateScenesList();
        }
    };
}

// --- SCENE TRANSITIONS MODAL LOGIC ---
let previewAnimationFrame;
let previewCanvasA = document.createElement('canvas');
let previewCanvasB = document.createElement('canvas');
previewCanvasA.width = 360; previewCanvasA.height = 200;
let pCtx = previewCanvasA.getContext('2d');
pCtx.fillStyle = '#2c3e50'; pCtx.fillRect(0,0,360,200);
pCtx.fillStyle = '#ecf0f1'; pCtx.font = '30px Arial'; pCtx.textAlign='center'; pCtx.fillText('Scene A', 180, 110);

previewCanvasB.width = 360; previewCanvasB.height = 200;
pCtx = previewCanvasB.getContext('2d');
pCtx.fillStyle = '#8e44ad'; pCtx.fillRect(0,0,360,200);
pCtx.fillStyle = '#ecf0f1'; pCtx.font = '30px Arial'; pCtx.textAlign='center'; pCtx.fillText('Scene B', 180, 110);

function startTransitionPreview() {
    const canvas = document.getElementById('transitionPreviewCanvas');
    const tCtx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    
    let lastT = performance.now();
    let phase = 0; 
    let progress = 0;

    function animate() {
        const now = performance.now();
        const dt = now - lastT;
        lastT = now;
        
        const dur = parseInt(document.getElementById('transitionDurationInput').value) || 500;
        const effect = document.querySelector('.transition-item.active').dataset.effect;
        
        if (phase === 0) {
            progress += dt / dur;
            if (progress >= 1) { progress = 1; phase = 1; setTimeout(()=>{ phase = 2; lastT = performance.now(); progress = 0; }, 1000); }
            drawTransition(tCtx, w, h, progress, effect, previewCanvasA, previewCanvasB);
        } else if (phase === 2) {
            progress += dt / dur;
            if (progress >= 1) { progress = 1; phase = 3; setTimeout(()=>{ phase = 0; lastT = performance.now(); progress = 0; }, 1000); }
            drawTransition(tCtx, w, h, progress, effect, previewCanvasB, previewCanvasA);
        }

        if(document.getElementById('sceneTransitionsModal').classList.contains('active')) {
            previewAnimationFrame = requestAnimationFrame(animate);
        }
    }
    
    cancelAnimationFrame(previewAnimationFrame);
    lastT = performance.now();
    phase = 0;
    progress = 0;
    animate();
}

function updateTransitionDescription() {
    const effect = document.querySelector('.transition-item.active').dataset.effect;
    const desc = document.getElementById('transitionDescription');
    if(effect === 'none') desc.textContent = "Instantly switches between scenes with no visual effect.";
    if(effect === 'fade') desc.textContent = "Smoothly fades the old scene out while fading the new scene in.";
    if(effect === 'slide-left') desc.textContent = "Pushes the old scene out to the left as the new scene slides in from the right.";
    if(effect === 'slide-right') desc.textContent = "Pushes the old scene out to the right as the new scene slides in from the left.";
    if(effect === 'slide-up') desc.textContent = "Pushes the old scene upwards as the new scene slides in from the bottom.";
    if(effect === 'slide-down') desc.textContent = "Pushes the old scene downwards as the new scene slides in from the top.";
    if(effect === 'zoom-in') desc.textContent = "Zooms directly into the center of the new scene.";
    if(effect === 'circle-crop') desc.textContent = "Reveals the new scene through an expanding circular iris.";
    if(effect === 'spin') desc.textContent = "Spins and zooms out the old scene while the new scene spins and zooms in.";
    if(effect === 'melt') desc.textContent = "Slices the old scene vertically and melts it downwards.";
    if(effect === 'fall-apart') desc.textContent = "Shatters the old scene into falling tiles to reveal the new scene underneath.";
}

document.getElementById('openSceneTransitionsBtn').addEventListener('click', () => {
    openModalCenter('sceneTransitionsModal');
    document.querySelectorAll('.transition-item').forEach(i => i.classList.remove('active'));
    // Select the current scene's effect in the modal list
    const effectItem = document.querySelector(`.transition-item[data-effect="${activeScene.transition}"]`);
    if(effectItem) effectItem.classList.add('active');
    
    document.getElementById('transitionDurationInput').value = activeScene.transitionDuration;
    updateTransitionDescription();
    startTransitionPreview();
});

document.querySelectorAll('.transition-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.transition-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        updateTransitionDescription();
        startTransitionPreview(); 
    });
});

document.getElementById('applyTransitionBtn').addEventListener('click', () => {
    activeScene.transition = document.querySelector('.transition-item.active').dataset.effect;
    activeScene.transitionDuration = parseInt(document.getElementById('transitionDurationInput').value) || 500;
    updateDockTransitions(); // Update the visual dock selector
    document.getElementById('sceneTransitionsModal').classList.remove('active');
});

updateDockTransitions();
updateScenesList(); // Initial render


if (moveSourceUpBtn) {
    moveSourceUpBtn.onclick = () => {
        if (!selectedSource) return;
        const idx = sources.indexOf(selectedSource);
        if (idx < sources.length - 1) { 
            sources.splice(idx, 1);
            sources.splice(idx + 1, 0, selectedSource);
            updateSourcesList();
        }
    };
}

if (moveSourceDownBtn) {
    moveSourceDownBtn.onclick = () => {
        if (!selectedSource) return;
        const idx = sources.indexOf(selectedSource);
        if (idx > 0) { 
            sources.splice(idx, 1);
            sources.splice(idx - 1, 0, selectedSource);
            updateSourcesList();
        }
    };
}

function addSource(type, name) {
    const src = new ObsSource(Date.now(), name, type);
    sources.push(src); 
    updateSourcesList();
    selectSource(src);
    return src;
}

function selectSource(source) {
    selectedSource = source;
    updateSourcesList();
    
    textControlsBar.style.display = 'none';
    mediaControlsBar.style.display = 'none';
    browserControlsBar.style.display = 'none';

    if (source && source.type === 'text') {
        textControlsBar.style.display = 'flex';
        document.getElementById('textInputSource').value = source.text;
        document.getElementById('textColorSource').value = source.textProps.color;
        document.getElementById('textFontSource').value = source.textProps.font;
        document.getElementById('textSizeSource').value = source.fontSize;
    } else if (source && (source.type === 'media' || source.type === 'vlc' || source.type === 'slideshow')) {
        mediaControlsBar.style.display = 'flex';
        document.getElementById('mediaSourceName').textContent = source.name;
    } else if (source && source.type === 'browser') {
        browserControlsBar.style.display = 'flex';
        document.getElementById('browserSourceName').textContent = source.name;
        document.getElementById('browserZoomSlider').value = source.browserProps.zoom * 100;
        document.getElementById('browserZoomText').textContent = Math.round(source.browserProps.zoom * 100) + '%';
        browserTransparentBarCheck.checked = source.browserProps.transparent;
        
        if (source.iframe && source.iframe.style.pointerEvents === 'auto') {
            document.getElementById('browserInteractBtn').classList.add('active');
            document.getElementById('browserInteractBtn').innerHTML = '<i class="fas fa-hand-pointer"></i> End Interact';
        } else {
            document.getElementById('browserInteractBtn').classList.remove('active');
            document.getElementById('browserInteractBtn').innerHTML = '<i class="fas fa-hand-pointer"></i> Interact';
        }
    }
}

// BROWSER CONTROLS & FILTERS BINDING
document.getElementById('browserZoomSlider').addEventListener('input', (e) => {
    if (selectedSource && selectedSource.type === 'browser') {
        const z = e.target.value / 100;
        selectedSource.browserProps.zoom = z;
        document.getElementById('browserZoomText').textContent = e.target.value + '%';
    }
});

browserTransparentBarCheck.addEventListener('change', (e) => {
    if (selectedSource && selectedSource.type === 'browser') {
        const isTransparent = e.target.checked;
        selectedSource.browserProps.transparent = isTransparent;
        
        if (selectedSource.iframe) {
            selectedSource.iframe.style.background = isTransparent ? 'transparent' : '#ffffff';
            applyDOMFilters(selectedSource);
        }
    }
});

// UNIVERSAL FILTERS MODAL BINDING
function openUniversalFiltersModal() {
    if (!selectedSource) return;
    
    document.getElementById('filtersModalTitle').innerHTML = `<i class="fas fa-sliders-h"></i> Filters for '${selectedSource.name}'`;
    
    const f = selectedSource.filters;
    filterOpacity.value = f.opacity; filterOpacityVal.textContent = f.opacity + '%';
    filterBrightness.value = f.brightness; filterBrightnessVal.textContent = f.brightness + '%';
    filterContrast.value = f.contrast; filterContrastVal.textContent = f.contrast + '%';
    filterSaturation.value = f.saturation; filterSaturationVal.textContent = f.saturation + '%';
    filterHue.value = f.hue; filterHueVal.textContent = f.hue + '°';

    openModalCenter('universalFiltersModal');
}

textFiltersBtn.addEventListener('click', openUniversalFiltersModal);
mediaFiltersBtn.addEventListener('click', openUniversalFiltersModal);
browserFiltersBtn.addEventListener('click', openUniversalFiltersModal);

function updateLiveFilters(type, slider, valDisplay, suffix) {
    slider.addEventListener('input', (e) => {
        const val = e.target.value;
        valDisplay.textContent = val + suffix;
        if (selectedSource) {
            selectedSource.filters[type] = parseInt(val);
            if (selectedSource.type === 'browser') {
                applyDOMFilters(selectedSource);
            }
            // Other sources auto-update in renderLoop via getUniversalFilterString
        }
    });
}

updateLiveFilters('opacity', filterOpacity, filterOpacityVal, '%');
updateLiveFilters('brightness', filterBrightness, filterBrightnessVal, '%');
updateLiveFilters('contrast', filterContrast, filterContrastVal, '%');
updateLiveFilters('saturation', filterSaturation, filterSaturationVal, '%');
updateLiveFilters('hue', filterHue, filterHueVal, '°');

closeFiltersBtn.addEventListener('click', () => universalFiltersModal.classList.remove('active'));
filterCloseBtn.addEventListener('click', () => universalFiltersModal.classList.remove('active'));

filterDefaultsBtn.addEventListener('click', () => {
    if (selectedSource) {
        selectedSource.filters = { opacity: 100, brightness: 100, contrast: 100, saturation: 100, hue: 0 };
        filterOpacity.value = 100; filterOpacityVal.textContent = '100%';
        filterBrightness.value = 100; filterBrightnessVal.textContent = '100%';
        filterContrast.value = 100; filterContrastVal.textContent = '100%';
        filterSaturation.value = 100; filterSaturationVal.textContent = '100%';
        filterHue.value = 0; filterHueVal.textContent = '0°';
        if (selectedSource.type === 'browser') {
            applyDOMFilters(selectedSource);
        }
    }
});


let isInteracting = false;
document.getElementById('browserInteractBtn').addEventListener('click', () => {
    if (!selectedSource || selectedSource.type !== 'browser' || !selectedSource.iframe) return;
    
    // Toggle pointer events
    if (selectedSource.iframe.style.pointerEvents === 'none') {
        selectedSource.iframe.style.pointerEvents = 'auto';
        document.getElementById('browserInteractBtn').classList.add('active');
        document.getElementById('browserInteractBtn').innerHTML = '<i class="fas fa-hand-pointer"></i> End Interact';
    } else {
        selectedSource.iframe.style.pointerEvents = 'none';
        document.getElementById('browserInteractBtn').classList.remove('active');
        document.getElementById('browserInteractBtn').innerHTML = '<i class="fas fa-hand-pointer"></i> Interact';
    }
});

document.getElementById('browserBackBtn').addEventListener('click', () => {
    if (selectedSource && selectedSource.iframe) {
        try { selectedSource.iframe.contentWindow.history.back(); } catch(e) { console.warn("Cross-origin blocks iframe back history."); }
    }
});

document.getElementById('browserForwardBtn').addEventListener('click', () => {
    if (selectedSource && selectedSource.iframe) {
        try { selectedSource.iframe.contentWindow.history.forward(); } catch(e) { console.warn("Cross-origin blocks iframe forward history."); }
    }
});

document.getElementById('browserRefreshBtn').addEventListener('click', () => {
    if (selectedSource && selectedSource.iframe) {
        selectedSource.iframe.src = selectedSource.iframe.src;
    }
});

document.getElementById('browserBarPropertiesBtn').addEventListener('click', () => {
    if (selectedSource && selectedSource.type === 'browser') openBrowserProperties(selectedSource);
});


function getIconForType(type) {
    switch(type) {
        case 'display': return '<i class="fas fa-desktop"></i>';
        case 'window': return '<i class="far fa-window-maximize"></i>';
        case 'camera': return '<i class="fas fa-camera"></i>';
        case 'audio': return '<i class="fas fa-microphone"></i>';
        case 'audio-in': return '<i class="fas fa-microphone"></i>';
        case 'image': return '<i class="fas fa-image"></i>';
        case 'slideshow': return '<i class="fas fa-images"></i>';
        case 'media': return '<i class="fas fa-play-circle"></i>';
        case 'vlc': return '<i class="fas fa-play-circle"></i>';
        case 'text': return '<i class="fas fa-font"></i>';
        case 'browser': return '<i class="fas fa-globe"></i>';
        case 'scene': return '<i class="fas fa-film"></i>';
        case 'color': return '<i class="fas fa-palette"></i>';
        default: return '<i class="fas fa-file"></i>';
    }
}

// DRAG AND DROP LIST REORDERING
let draggedSourceId = null;
let globalLastClickTime = 0;
let globalLastClickedSourceId = null;

function updateSourcesList() {
    sourcesList.innerHTML = '';
    for (let i = sources.length - 1; i >= 0; i--) {
        const src = sources[i];

        const div = document.createElement('div');
        div.className = `source-list-item ${selectedSource === src ? 'active' : ''}`;
        div.draggable = true; 
        
        div.innerHTML = `
            <div class="source-icon">${getIconForType(src.type)}</div>
            <div class="source-name">${src.name}</div>
            <div class="source-actions">
                <button class="source-action-btn eye-btn"><i class="fas fa-eye${src.isVisible ? '' : '-slash'}"></i></button>
                <button class="source-action-btn lock-btn"><i class="fas fa-${src.isLocked ? 'lock' : 'unlock'}"></i></button>
            </div>
        `;
        
        // --- RELIABLE DOUBLE CLICK IMPLEMENTATION ---
        div.addEventListener('mousedown', (e) => {
            if (!e.target.closest('.source-action-btn')) {
                const currentTime = Date.now();
                const isDoubleClick = (src.id === globalLastClickedSourceId && currentTime - globalLastClickTime < 300);
                
                globalLastClickTime = currentTime;
                globalLastClickedSourceId = src.id;
                
                selectSource(src);
                
                if (isDoubleClick) { 
                    if (src.type === 'media' || src.type === 'vlc') {
                        openMediaProperties(src);
                    } else if (src.type === 'slideshow') {
                        openSlideshowProperties(src);
                    } else if (src.type === 'browser') {
                        openBrowserProperties(src);
                    } else if (src.type === 'text') {
                        openTextProperties(src);
                    } else if (src.type === 'image') {
                        openImageProperties(src);
                    } else if (src.type === 'color') {
                        openColorProperties(src);
                    } else if (src.type === 'audio' || src.type === 'audio-in') {
                        openAudioProperties(src);
                    } else if (src.type === 'display') {
                        openDisplayProperties(src);
                    }
                }
            }
        });

        div.querySelector('.eye-btn').addEventListener('mousedown', () => {
            src.isVisible = !src.isVisible;
            updateSourcesList();
        });
        div.querySelector('.lock-btn').addEventListener('mousedown', () => {
            src.isLocked = !src.isLocked;
            updateSourcesList();
        });

        div.addEventListener('dragstart', (e) => {
            draggedSourceId = src.id;
            e.dataTransfer.effectAllowed = 'move';
            setTimeout(() => div.classList.add('dragging'), 0);
        });
        div.addEventListener('dragend', () => {
            div.classList.remove('dragging');
            document.querySelectorAll('.source-list-item').forEach(el => el.classList.remove('drag-over'));
        });
        div.addEventListener('dragenter', (e) => { e.preventDefault(); });
        div.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            div.classList.add('drag-over');
        });
        div.addEventListener('dragleave', () => {
            div.classList.remove('drag-over');
        });
        div.addEventListener('drop', (e) => {
            e.preventDefault();
            div.classList.remove('drag-over');
            if (draggedSourceId && draggedSourceId !== src.id) {
                const fromIdx = sources.findIndex(s => s.id === draggedSourceId);
                const toIdx = sources.findIndex(s => s.id === src.id);
                if (fromIdx !== -1 && toIdx !== -1) {
                    const moved = sources.splice(fromIdx, 1)[0];
                    sources.splice(toIdx, 0, moved);
                    updateSourcesList();
                }
            }
        });

        sourcesList.appendChild(div);
    }
}

// SETUP DYNAMIC AUDIO ROUTING ENGINE
function updateAudioRouting() {
    // 1. Disconnect all mergers globally to ensure clean slate
    scenes.forEach(s => {
        s.sources.forEach(src => {
            if (src.audioMerger) {
                try { src.audioMerger.disconnect(); } catch(e){}
            }
        });
    });

    if (!activeScene) return;

    // 2. Recursively connect active scene hierarchy to the correct mixer target
    function routeSceneSources(sceneToRoute, destinationNode) {
        sceneToRoute.sources.forEach(src => {
            if (src.audioMerger) {
                src.audioMerger.connect(destinationNode);
            }
            // If this is a nested scene, funnel its children into THIS scene's gainNode
            if (src.type === 'scene' && src.targetSceneId && src.gainNode) {
                const targetScene = scenes.find(s => s.id === src.targetSceneId);
                if (targetScene) {
                    routeSceneSources(targetScene, src.gainNode);
                }
            }
        });
    }

    routeSceneSources(activeScene, masterGain);
}


function renderMixerUI(src) {
    if(document.getElementById(`mix-${src.id}`)) return; // Already rendered
    
    const mixerHtml = `
        <div class="audio-track" id="mix-${src.id}">
            <div class="audio-header">
                <span>${src.name}</span>
                <span id="db-${src.id}">0.0 dB</span>
            </div>
            <div class="audio-body">
                <div class="audio-left-icons">
                    <div class="audio-menu-btn"><i class="fas fa-ellipsis-v"></i></div>
                    <div class="audio-speaker-btn"><i class="fas fa-volume-up"></i></div>
                </div>
                <div class="audio-controls">
                    <div class="audio-meter-container">
                        <div class="audio-meter">
                            <div class="audio-meter-fill" id="meter-L-${src.id}" style="width: 0%;"></div>
                        </div>
                        <div class="audio-meter-spacer"></div>
                        <div class="audio-meter">
                            <div class="audio-meter-fill" id="meter-R-${src.id}" style="width: 0%;"></div>
                        </div>
                    </div>
                    <div class="audio-ticks">
                        <span>-60</span><span>-55</span><span>-50</span><span>-45</span><span>-40</span><span>-35</span><span>-30</span><span>-25</span><span>-20</span><span>-15</span><span>-10</span><span>-5</span><span>0</span>
                    </div>
                    <input type="range" min="0" max="100" value="100" class="audio-slider" id="vol-${src.id}">
                </div>
            </div>
        </div>`;
    
    audioMixerContainer.insertAdjacentHTML('beforeend', mixerHtml);
    
    // Bind logic
    document.getElementById(`vol-${src.id}`).addEventListener('input', (e) => {
        const val = e.target.value / 100;
        src.gainNode.gain.value = val;
        
        let db = 20 * Math.log10(val);
        if (val === 0) db = -Infinity;
        document.getElementById(`db-${src.id}`).textContent = val === 0 ? '-inf dB' : `${db.toFixed(1)} dB`;
    });
    
    // Visually restore volume node state if we just switched scenes
    const currentVal = src.gainNode.gain.value;
    document.getElementById(`vol-${src.id}`).value = currentVal * 100;
    let db = 20 * Math.log10(currentVal);
    if (currentVal === 0) db = -Infinity;
    document.getElementById(`db-${src.id}`).textContent = currentVal === 0 ? '-inf dB' : `${db.toFixed(1)} dB`;
}

function setupAudioNode(mediaElement, src) {
    if(audioCtx.state === 'suspended') audioCtx.resume();
    
    const gainNode = audioCtx.createGain();
    src.gainNode = gainNode;
    
    const analyserL = audioCtx.createAnalyser();
    analyserL.fftSize = 512;
    src.analyserL = analyserL;

    const analyserR = audioCtx.createAnalyser();
    analyserR.fftSize = 512;
    src.analyserR = analyserR;

    const splitter = audioCtx.createChannelSplitter(2);
    const merger = audioCtx.createChannelMerger(2);

    gainNode.connect(splitter);
    
    splitter.connect(analyserL, 0);
    try { splitter.connect(analyserR, 1); } catch(e) { splitter.connect(analyserR, 0); }

    analyserL.connect(merger, 0, 0);
    analyserR.connect(merger, 0, 1);

    src.audioMerger = merger;

    if (mediaElement) {
        try {
            let track;
            if (mediaElement instanceof MediaStream) {
                track = audioCtx.createMediaStreamSource(mediaElement);
            } else {
                track = audioCtx.createMediaElementSource(mediaElement);
            }
            track.connect(gainNode);
        } catch(e) { console.warn(e); }
    }
    
    renderMixerUI(src);
    updateAudioRouting();
}

// COG ICON BINDING
if (openSourcePropertiesBtn) {
    openSourcePropertiesBtn.addEventListener('click', () => {
        if (selectedSource && (selectedSource.type === 'media' || selectedSource.type === 'vlc')) {
            openMediaProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'slideshow') {
            openSlideshowProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'browser') {
            openBrowserProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'text') {
            openTextProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'image') {
            openImageProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'color') {
            openColorProperties(selectedSource);
        } else if (selectedSource && (selectedSource.type === 'audio' || selectedSource.type === 'audio-in')) {
            openAudioProperties(selectedSource);
        } else if (selectedSource && selectedSource.type === 'display') {
            openDisplayProperties(selectedSource);
        }
    });
}


// --- AUDIO INPUT PROPERTIES LOGIC ---
let editingAudioSource = null;
const audioInputPropertiesModal = document.getElementById('audioInputPropertiesModal');

function openAudioProperties(src) {
    if (!src || (src.type !== 'audio' && src.type !== 'audio-in')) return;
    editingAudioSource = src;
    
    document.getElementById('audioInputPropertiesTitle').innerHTML = `<i class="fas fa-microphone"></i> Properties for '${src.name}'`;
    
    document.getElementById('micGainSlider').value = src.audioProps.gain;
    document.getElementById('micGainNum').value = src.audioProps.gain;
    document.getElementById('micNoiseSuppression').checked = src.audioProps.noiseSuppression;
    document.getElementById('micEchoCancellation').checked = src.audioProps.echoCancellation;
    document.getElementById('micAutoGain').checked = src.audioProps.autoGain;
    
    openModalCenter('audioInputPropertiesModal');
}

document.getElementById('micGainSlider').addEventListener('input', e => { 
    document.getElementById('micGainNum').value = e.target.value; 
    updateAudioSourceGain(); 
});
document.getElementById('micGainNum').addEventListener('input', e => { 
    document.getElementById('micGainSlider').value = e.target.value; 
    updateAudioSourceGain(); 
});

function updateAudioSourceGain() {
    if (editingAudioSource && editingAudioSource.gainNode) {
        const val = document.getElementById('micGainSlider').value / 100;
        editingAudioSource.gainNode.gain.value = val;
        
        // Sync the main mixer slider to reflect these settings live
        const mixerSlider = document.getElementById(`vol-${editingAudioSource.id}`);
        if (mixerSlider) {
            mixerSlider.value = val * 100;
            let db = 20 * Math.log10(val);
            if (val === 0) db = -Infinity;
            document.getElementById(`db-${editingAudioSource.id}`).textContent = val === 0 ? '-inf dB' : `${db.toFixed(1)} dB`;
        }
    }
}

document.getElementById('closeAudioInputPropertiesBtn').addEventListener('click', closeAudioPropertiesModal);
document.getElementById('micCancelBtn').addEventListener('click', closeAudioPropertiesModal);

document.getElementById('micDefaultsBtn').addEventListener('click', () => {
    document.getElementById('micGainSlider').value = 100;
    document.getElementById('micGainNum').value = 100;
    document.getElementById('micNoiseSuppression').checked = true;
    document.getElementById('micEchoCancellation').checked = true;
    document.getElementById('micAutoGain').checked = false;
    updateAudioSourceGain();
});

document.getElementById('micOkBtn').addEventListener('click', () => {
    if (editingAudioSource) {
        editingAudioSource.audioProps.gain = parseInt(document.getElementById('micGainSlider').value) || 100;
        editingAudioSource.audioProps.noiseSuppression = document.getElementById('micNoiseSuppression').checked;
        editingAudioSource.audioProps.echoCancellation = document.getElementById('micEchoCancellation').checked;
        editingAudioSource.audioProps.autoGain = document.getElementById('micAutoGain').checked;
    }
    closeAudioPropertiesModal();
});

function closeAudioPropertiesModal() {
    audioInputPropertiesModal.classList.remove('active');
    editingAudioSource = null;
}


// --- COLOR PROPERTIES LOGIC ---
let editingColorSource = null;
const colorPropertiesModal = document.getElementById('colorPropertiesModal');
const cpColor = document.getElementById('cpColor');
const cpWidth = document.getElementById('cpWidth');
const cpHeight = document.getElementById('cpHeight');
const cpOpacitySlider = document.getElementById('cpOpacitySlider');
const cpOpacityNum = document.getElementById('cpOpacityNum');
const colorPropertiesPreview = document.getElementById('colorPropertiesPreview');

function openColorProperties(src) {
    if (!src || src.type !== 'color') return;
    editingColorSource = src;
    
    document.getElementById('colorPropertiesTitle').innerHTML = `<i class="fas fa-palette"></i> Properties for '${src.name}'`;
    
    cpColor.value = src.colorProps.color;
    cpWidth.value = src.colorProps.width;
    cpHeight.value = src.colorProps.height;
    cpOpacitySlider.value = src.colorProps.opacity;
    cpOpacityNum.value = src.colorProps.opacity;
    
    updateColorPreview();
    openModalCenter('colorPropertiesModal');
}

function updateColorPreview() {
    if(!editingColorSource) return;
    colorPropertiesPreview.style.backgroundColor = hexToRgba(cpColor.value, cpOpacitySlider.value);
}

cpColor.addEventListener('input', updateColorPreview);
cpOpacitySlider.addEventListener('input', e => { cpOpacityNum.value = e.target.value; updateColorPreview(); });
cpOpacityNum.addEventListener('input', e => { cpOpacitySlider.value = e.target.value; updateColorPreview(); });

document.getElementById('closeColorPropertiesBtn').addEventListener('click', closeColorPropertiesModal);
document.getElementById('cpCancelBtn').addEventListener('click', closeColorPropertiesModal);

document.getElementById('cpDefaultsBtn').addEventListener('click', () => {
    cpColor.value = '#ffffff';
    cpWidth.value = 1920;
    cpHeight.value = 1080;
    cpOpacitySlider.value = 100;
    cpOpacityNum.value = 100;
    updateColorPreview();
});

document.getElementById('cpOkBtn').addEventListener('click', () => {
    if (editingColorSource) {
        editingColorSource.colorProps.color = cpColor.value;
        editingColorSource.colorProps.width = parseInt(cpWidth.value) || 1920;
        editingColorSource.colorProps.height = parseInt(cpHeight.value) || 1080;
        editingColorSource.colorProps.opacity = parseInt(cpOpacitySlider.value) || 100;
        
        // Push dimensions physically to the source
        editingColorSource.width = editingColorSource.colorProps.width;
        editingColorSource.height = editingColorSource.colorProps.height;
    }
    closeColorPropertiesModal();
});

function closeColorPropertiesModal() {
    colorPropertiesModal.classList.remove('active');
    editingColorSource = null;
}


// --- IMAGE PROPERTIES LOGIC ---
let editingImageSource = null;
const imagePropertiesModal = document.getElementById('imagePropertiesModal');
const imagePropertiesPreview = document.getElementById('imagePropertiesPreview');
const ipLocalFile = document.getElementById('ipLocalFile');
const ipFilePath = document.getElementById('ipFilePath');
const ipTransparent = document.getElementById('ipTransparent');
const ipFlipH = document.getElementById('ipFlipH');
const ipFlipV = document.getElementById('ipFlipV');
const ipOpacitySlider = document.getElementById('ipOpacitySlider');
const ipOpacityNum = document.getElementById('ipOpacityNum');
const ipBlendMode = document.getElementById('ipBlendMode');

function openImageProperties(src) {
    if (!src || src.type !== 'image') return;
    editingImageSource = src;
    document.getElementById('imagePropertiesTitle').innerHTML = `<i class="fas fa-image"></i> Properties for '${src.name}'`;
    
    ipLocalFile.checked = src.imageProps.localFile;
    document.getElementById('ipFileLabel').textContent = ipLocalFile.checked ? "Local file path" : "URL";
    document.getElementById('ipFileActionBtn').textContent = ipLocalFile.checked ? "Browse" : "Paste";
    ipFilePath.value = src.imageProps.filePath || src.element?.src || '';
    ipTransparent.checked = src.imageProps.transparent;
    ipFlipH.checked = src.imageProps.flipH;
    ipFlipV.checked = src.imageProps.flipV;
    ipOpacitySlider.value = src.imageProps.opacity;
    ipOpacityNum.value = src.imageProps.opacity;
    ipBlendMode.value = src.imageProps.blendMode;

    updateImagePreview();
    openModalCenter('imagePropertiesModal');
}

function updateImagePreview() {
    if(!editingImageSource) return;
    imagePropertiesPreview.src = editingImageSource.tempNewUrl ? editingImageSource.tempNewUrl : (editingImageSource.element ? editingImageSource.element.src : '');
    imagePropertiesPreview.style.opacity = ipOpacitySlider.value / 100;
    imagePropertiesPreview.style.transform = `scale(${ipFlipH.checked ? -1 : 1}, ${ipFlipV.checked ? -1 : 1})`;
    imagePropertiesPreview.style.mixBlendMode = ipBlendMode.value;
    imagePropertiesPreview.style.filter = ipTransparent.checked ? 'url(#chroma-key-white)' : 'none';
}

ipLocalFile.addEventListener('change', (e) => {
    document.getElementById('ipFileLabel').textContent = e.target.checked ? "Local file path" : "URL";
    document.getElementById('ipFileActionBtn').textContent = e.target.checked ? "Browse" : "Paste";
});

document.getElementById('ipFileActionBtn').addEventListener('click', async () => {
    if (ipLocalFile.checked) {
        document.getElementById('imageFileInput').click();
    } else {
        try {
            const text = await navigator.clipboard.readText();
            ipFilePath.value = text;
            if(editingImageSource) {
                editingImageSource.tempNewUrl = text;
                updateImagePreview();
            }
        } catch(e) {}
    }
});

document.getElementById('imageFileInput').addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        ipFilePath.value = file.name;
        const url = URL.createObjectURL(file);
        if (editingImageSource) editingImageSource.tempNewUrl = url;
        updateImagePreview();
    }
});

ipTransparent.addEventListener('change', updateImagePreview);
ipFlipH.addEventListener('change', updateImagePreview);
ipFlipV.addEventListener('change', updateImagePreview);
ipBlendMode.addEventListener('change', updateImagePreview);
ipOpacitySlider.addEventListener('input', e => { ipOpacityNum.value = e.target.value; updateImagePreview(); });
ipOpacityNum.addEventListener('input', e => { ipOpacitySlider.value = e.target.value; updateImagePreview(); });

document.getElementById('closeImagePropertiesBtn').addEventListener('click', closeImagePropertiesModal);
document.getElementById('ipCancelBtn').addEventListener('click', () => {
    if (editingImageSource) delete editingImageSource.tempNewUrl;
    closeImagePropertiesModal();
});

document.getElementById('ipOkBtn').addEventListener('click', () => {
    if (editingImageSource) {
        editingImageSource.imageProps.localFile = ipLocalFile.checked;
        editingImageSource.imageProps.filePath = ipFilePath.value;
        editingImageSource.imageProps.transparent = ipTransparent.checked;
        editingImageSource.imageProps.flipH = ipFlipH.checked;
        editingImageSource.imageProps.flipV = ipFlipV.checked;
        editingImageSource.imageProps.opacity = parseInt(ipOpacitySlider.value) || 100;
        editingImageSource.imageProps.blendMode = ipBlendMode.value;

        if (editingImageSource.tempNewUrl) {
            if(!editingImageSource.element) editingImageSource.element = new Image();
            editingImageSource.element.src = editingImageSource.tempNewUrl;
            editingImageSource.name = ipFilePath.value || "Image Source";
            delete editingImageSource.tempNewUrl;
            updateSourcesList();
        }
    }
    closeImagePropertiesModal();
});

function closeImagePropertiesModal() {
    imagePropertiesModal.classList.remove('active');
    editingImageSource = null;
}

document.getElementById('ipDefaultsBtn').addEventListener('click', () => {
    ipLocalFile.checked = true;
    document.getElementById('ipFileLabel').textContent = "Local file path";
    document.getElementById('ipFileActionBtn').textContent = "Browse";
    ipTransparent.checked = false;
    ipFlipH.checked = false;
    ipFlipV.checked = false;
    ipOpacitySlider.value = 100;
    ipOpacityNum.value = 100;
    ipBlendMode.value = 'source-over';
    updateImagePreview();
});


// --- GDI+ TEXT PROPERTIES LOGIC ---
let editingTextSource = null;
let textPreviewAnimFrame;

textPropertiesBtn.addEventListener('click', () => {
    if (selectedSource && selectedSource.type === 'text') {
        openTextProperties(selectedSource);
    }
});

function openTextProperties(src) {
    if (!src || src.type !== 'text') return;
    editingTextSource = src;

    document.getElementById('textPropertiesTitle').innerHTML = `<i class="fas fa-font"></i> Properties for '${src.name}'`;

    tpFont.value = src.textProps.font;
    tpReadFile.checked = src.textProps.readFile;
    tpFileDisplay.style.display = src.textProps.readFile ? 'flex' : 'none';
    tpText.style.display = src.textProps.readFile ? 'none' : 'block';
    tpFilePath.value = src.textProps.filePath;
    tpText.value = src.text;
    tpAntialiasing.checked = src.textProps.antialiasing;
    tpTransform.value = src.textProps.transform;
    tpVertical.checked = src.textProps.vertical;
    tpColor.value = src.textProps.color;
    tpOpacitySlider.value = src.textProps.opacity;
    tpOpacityNum.value = src.textProps.opacity;
    tpGradient.checked = src.textProps.gradient;
    tpGradientColorContainer.style.display = src.textProps.gradient ? 'flex' : 'none';
    tpGradientColor.value = src.textProps.gradientColor;
    tpBgColor.value = src.textProps.bgColor;
    tpBgOpacitySlider.value = src.textProps.bgOpacity;
    tpBgOpacityNum.value = src.textProps.bgOpacity;
    tpAlign.value = src.textProps.align;
    tpValign.value = src.textProps.valign;
    tpOutline.checked = src.textProps.outline;

    openModalCenter('textPropertiesModal');
    startTextPreviewLoop();
}

tpReadFile.addEventListener('change', (e) => {
    tpFileDisplay.style.display = e.target.checked ? 'flex' : 'none';
    tpText.style.display = e.target.checked ? 'none' : 'block';
});

tpFileBrowseBtn.addEventListener('click', () => tpFileInput.click());

tpFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        tpFilePath.value = file.name;
        const reader = new FileReader();
        reader.onload = (evt) => { tpText.value = evt.target.result; };
        reader.readAsText(file);
    }
});

tpOpacitySlider.addEventListener('input', e => tpOpacityNum.value = e.target.value);
tpOpacityNum.addEventListener('input', e => tpOpacitySlider.value = e.target.value);
tpBgOpacitySlider.addEventListener('input', e => tpBgOpacityNum.value = e.target.value);
tpBgOpacityNum.addEventListener('input', e => tpBgOpacitySlider.value = e.target.value);

tpGradient.addEventListener('change', e => {
    tpGradientColorContainer.style.display = e.target.checked ? 'flex' : 'none';
});

document.getElementById('tpDefaultsBtn').addEventListener('click', () => {
    tpFont.value = 'Arial';
    tpReadFile.checked = false;
    tpFileDisplay.style.display = 'none';
    tpText.style.display = 'block';
    tpFilePath.value = '';
    tpAntialiasing.checked = true;
    tpTransform.value = 'none';
    tpVertical.checked = false;
    tpColor.value = '#ffffff';
    tpOpacitySlider.value = 100; tpOpacityNum.value = 100;
    tpGradient.checked = false;
    tpGradientColorContainer.style.display = 'none';
    tpGradientColor.value = '#0000ff';
    tpBgColor.value = '#000000';
    tpBgOpacitySlider.value = 0; tpBgOpacityNum.value = 0;
    tpAlign.value = 'left';
    tpValign.value = 'top';
    tpOutline.checked = false;
});

closeTextPropertiesBtn.addEventListener('click', closeTextPropertiesModal);
document.getElementById('tpCancelBtn').addEventListener('click', closeTextPropertiesModal);

document.getElementById('tpOkBtn').addEventListener('click', () => {
    if (editingTextSource) {
        editingTextSource.text = tpText.value;
        editingTextSource.textProps.font = tpFont.value;
        editingTextSource.textProps.readFile = tpReadFile.checked;
        editingTextSource.textProps.filePath = tpFilePath.value;
        editingTextSource.textProps.antialiasing = tpAntialiasing.checked;
        editingTextSource.textProps.transform = tpTransform.value;
        editingTextSource.textProps.vertical = tpVertical.checked;
        editingTextSource.textProps.color = tpColor.value;
        editingTextSource.textProps.opacity = parseInt(tpOpacityNum.value) || 100;
        editingTextSource.textProps.gradient = tpGradient.checked;
        editingTextSource.textProps.gradientColor = tpGradientColor.value;
        editingTextSource.textProps.bgColor = tpBgColor.value;
        editingTextSource.textProps.bgOpacity = parseInt(tpBgOpacityNum.value) || 0;
        editingTextSource.textProps.align = tpAlign.value;
        editingTextSource.textProps.valign = tpValign.value;
        editingTextSource.textProps.outline = tpOutline.checked;

        // Keep quick-edit bar synced
        if (selectedSource === editingTextSource) {
            document.getElementById('textInputSource').value = editingTextSource.text;
            document.getElementById('textColorSource').value = editingTextSource.textProps.color;
            document.getElementById('textFontSource').value = editingTextSource.textProps.font;
        }
    }
    closeTextPropertiesModal();
});

function closeTextPropertiesModal() {
    textPropertiesModal.classList.remove('active');
    cancelAnimationFrame(textPreviewAnimFrame);
    editingTextSource = null;
}

function startTextPreviewLoop() {
    const canvas = textPropertiesPreview;
    const pCtx = canvas.getContext('2d');
    
    function draw() {
        if (!textPropertiesModal.classList.contains('active')) return;
        
        // Auto-scale canvas resolution to match its CSS display size for crispness
        if (canvas.width !== canvas.clientWidth || canvas.height !== canvas.clientHeight) {
            canvas.width = canvas.clientWidth;
            canvas.height = canvas.clientHeight;
        }
        
        pCtx.clearRect(0, 0, canvas.width, canvas.height);

        // Build a temporary dummy source object reflecting the UI state instantly
        const dummySrc = {
            text: tpText.value || " ",
            fontSize: editingTextSource ? editingTextSource.fontSize : 72,
            textProps: {
                font: tpFont.value,
                antialiasing: tpAntialiasing.checked,
                transform: tpTransform.value,
                vertical: tpVertical.checked,
                color: tpColor.value,
                opacity: parseInt(tpOpacityNum.value) || 100,
                gradient: tpGradient.checked,
                gradientColor: tpGradientColor.value,
                bgColor: tpBgColor.value,
                bgOpacity: parseInt(tpBgOpacityNum.value) || 0,
                align: tpAlign.value,
                valign: tpValign.value,
                outline: tpOutline.checked
            }
        };

        // Measure bounds locally to fit in preview center
        pCtx.font = `${dummySrc.fontSize}px ${dummySrc.textProps.font}`;
        const lines = dummySrc.text.split('\n');
        let maxW = 0;
        lines.forEach(l => { maxW = Math.max(maxW, pCtx.measureText(l).width); });
        const lineH = dummySrc.fontSize * 1.2;
        
        let drawW, drawH;
        if (dummySrc.textProps.vertical) {
            drawW = lines.length * lineH;
            drawH = (lines[0] ? lines[0].length : 1) * lineH;
        } else {
            drawW = maxW;
            drawH = lines.length * lineH;
        }

        // Draw it centered
        pCtx.save();
        pCtx.translate(canvas.width / 2, canvas.height / 2);
        drawObsText(pCtx, dummySrc, drawW, drawH);
        pCtx.restore();

        textPreviewAnimFrame = requestAnimationFrame(draw);
    }
    draw();
}



// --- BROWSER PROPERTIES LOGIC ---
let editingBrowserSource = null;

function openBrowserProperties(src) {
    if (!src || src.type !== 'browser') return;
    editingBrowserSource = src;

    document.getElementById('browserPropertiesTitle').innerHTML = `<i class="fas fa-globe"></i> Properties for '${src.name}'`;

    document.getElementById('bpLocalFile').checked = src.browserProps.localFile;
    updateBrowserFileUI(src.browserProps.localFile);
    document.getElementById('bpUrlInput').value = src.browserProps.url;
    document.getElementById('bpWidth').value = src.browserProps.width;
    document.getElementById('bpHeight').value = src.browserProps.height;
    document.getElementById('bpTransparent').checked = src.browserProps.transparent;
    document.getElementById('bpControlAudio').checked = src.browserProps.controlAudio;
    document.getElementById('bpCustomFps').checked = src.browserProps.customFPS;
    document.getElementById('bpCustomCss').value = src.browserProps.customCSS;
    document.getElementById('bpShutdownInactive').checked = src.browserProps.shutdownNotVisible;
    document.getElementById('bpRefreshActive').checked = src.browserProps.refreshOnActive;
    document.getElementById('bpPermissions').value = src.browserProps.permissions;

    const preview = document.getElementById('browserPropertiesPreview');
    preview.src = src.browserProps.url;
    
    // Apply styling to preview window
    preview.style.background = src.browserProps.transparent ? 'transparent' : '#ffffff';
    
    // Duplicate the filter application for the preview window so it matches exactly
    let previewFilter = src.browserProps.transparent ? 'url(#chroma-key-white) ' : '';
    const f = src.filters;
    previewFilter += `opacity(${f.opacity}%) brightness(${f.brightness}%) contrast(${f.contrast}%) saturate(${f.saturation}%) hue-rotate(${f.hue}deg)`;
    preview.style.filter = previewFilter;

    openModalCenter('browserPropertiesModal');
}

function updateBrowserFileUI(isLocal) {
    const label = document.getElementById('bpFileLabel');
    const btn = document.getElementById('bpFileActionBtn');
    if (isLocal) {
        label.textContent = "Local file path";
        btn.textContent = "Browse";
    } else {
        label.textContent = "URL";
        btn.textContent = "Paste";
    }
}

document.getElementById('bpLocalFile').addEventListener('change', (e) => {
    updateBrowserFileUI(e.target.checked);
});

document.getElementById('bpFileActionBtn').addEventListener('click', async () => {
    if (document.getElementById('bpLocalFile').checked) {
        document.getElementById('browserFileInput').click();
    } else {
        try {
            const text = await navigator.clipboard.readText();
            document.getElementById('bpUrlInput').value = text;
            document.getElementById('browserPropertiesPreview').src = text;
        } catch (err) {
            document.getElementById('bpUrlInput').focus();
        }
    }
});

document.getElementById('bpUrlInput').addEventListener('input', (e) => {
    document.getElementById('browserPropertiesPreview').src = e.target.value;
});

document.getElementById('browserFileInput').addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        const url = URL.createObjectURL(file);
        document.getElementById('bpUrlInput').value = url;
        document.getElementById('browserPropertiesPreview').src = url;
    }
});

document.getElementById('bpTransparent').addEventListener('change', (e) => {
    const preview = document.getElementById('browserPropertiesPreview');
    preview.style.background = e.target.checked ? 'transparent' : '#ffffff';
    
    let previewFilter = e.target.checked ? 'url(#chroma-key-white) ' : '';
    if (editingBrowserSource) {
        const f = editingBrowserSource.filters;
        previewFilter += `opacity(${f.opacity}%) brightness(${f.brightness}%) contrast(${f.contrast}%) saturate(${f.saturation}%) hue-rotate(${f.hue}deg)`;
    }
    preview.style.filter = previewFilter;
});

document.getElementById('bpRefreshCacheBtn').addEventListener('click', () => {
    const preview = document.getElementById('browserPropertiesPreview');
    preview.src = preview.src; 
});

document.getElementById('bpDefaultsBtn').addEventListener('click', () => {
    document.getElementById('bpLocalFile').checked = false;
    updateBrowserFileUI(false);
    document.getElementById('bpUrlInput').value = 'https://shorturl.at/6QyYn';
    document.getElementById('bpWidth').value = 800;
    document.getElementById('bpHeight').value = 600;
    document.getElementById('bpTransparent').checked = true;
    document.getElementById('bpControlAudio').checked = false;
    document.getElementById('bpCustomFps').checked = false;
    document.getElementById('bpCustomCss').value = 'body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }';
    document.getElementById('bpShutdownInactive').checked = false;
    document.getElementById('bpRefreshActive').checked = false;
    document.getElementById('bpPermissions').value = 'read_status';
    
    const preview = document.getElementById('browserPropertiesPreview');
    preview.src = 'https://shorturl.at/6QyYn';
    preview.style.background = 'transparent';
    
    let previewFilter = 'url(#chroma-key-white) ';
    if (editingBrowserSource) {
        const f = editingBrowserSource.filters;
        previewFilter += `opacity(${f.opacity}%) brightness(${f.brightness}%) contrast(${f.contrast}%) saturate(${f.saturation}%) hue-rotate(${f.hue}deg)`;
    }
    preview.style.filter = previewFilter;
});

document.getElementById('closeBrowserPropertiesBtn').addEventListener('click', closeBrowserPropertiesModal);
document.getElementById('bpCancelBtn').addEventListener('click', closeBrowserPropertiesModal);

document.getElementById('bpOkBtn').addEventListener('click', () => {
    if (editingBrowserSource) {
        editingBrowserSource.browserProps.localFile = document.getElementById('bpLocalFile').checked;
        editingBrowserSource.browserProps.url = document.getElementById('bpUrlInput').value;
        editingBrowserSource.browserProps.width = parseInt(document.getElementById('bpWidth').value) || 800;
        editingBrowserSource.browserProps.height = parseInt(document.getElementById('bpHeight').value) || 600;
        editingBrowserSource.browserProps.transparent = document.getElementById('bpTransparent').checked;
        editingBrowserSource.browserProps.controlAudio = document.getElementById('bpControlAudio').checked;
        editingBrowserSource.browserProps.customFPS = document.getElementById('bpCustomFps').checked;
        editingBrowserSource.browserProps.customCSS = document.getElementById('bpCustomCss').value;
        editingBrowserSource.browserProps.shutdownNotVisible = document.getElementById('bpShutdownInactive').checked;
        editingBrowserSource.browserProps.refreshOnActive = document.getElementById('bpRefreshActive').checked;
        editingBrowserSource.browserProps.permissions = document.getElementById('bpPermissions').value;

        // Apply physical updates
        editingBrowserSource.url = editingBrowserSource.browserProps.url;

        // Optionally adjust the canvas bounding box aspect ratio to match the new settings
        editingBrowserSource.aspectRatio = editingBrowserSource.browserProps.width / editingBrowserSource.browserProps.height;
        editingBrowserSource.height = editingBrowserSource.width / editingBrowserSource.aspectRatio;

        if (editingBrowserSource.iframe) {
            editingBrowserSource.iframe.src = editingBrowserSource.url;
            editingBrowserSource.iframe.style.background = editingBrowserSource.browserProps.transparent ? 'transparent' : '#ffffff';
            applyDOMFilters(editingBrowserSource);
        }

        // Keep the control bar checkbox synced if this source is currently selected
        if (selectedSource === editingBrowserSource) {
            browserTransparentBarCheck.checked = editingBrowserSource.browserProps.transparent;
        }
    }
    closeBrowserPropertiesModal();
});

function closeBrowserPropertiesModal() {
    document.getElementById('browserPropertiesModal').classList.remove('active');
    document.getElementById('browserPropertiesPreview').src = '';
    editingBrowserSource = null;
}

// --- DISPLAY CAPTURE PROPERTIES LOGIC ---
let editingDisplaySource = null;

function openDisplayProperties(src) {
    if (!src || src.type !== 'display') return;
    editingDisplaySource = src;
    
    document.getElementById('displayPropertiesTitle').innerHTML = `<i class="fas fa-desktop"></i> Properties for '${src.name}'`;
    
    document.getElementById('dpCaptureMethod').value = src.displayProps.captureMethod;
    document.getElementById('dpCaptureCursor').checked = src.displayProps.captureCursor;
    document.getElementById('dpForceSDR').checked = src.displayProps.forceSDR;
    document.getElementById('dpDisplaySelect').value = 'current';

    const preview = document.getElementById('displayPropertiesPreview');
    if (src.element) {
        preview.srcObject = src.element.srcObject;
    }

    openModalCenter('displayPropertiesModal');
}

// Add a mock visual update to the preview when Capture Method changes
document.getElementById('dpCaptureMethod').addEventListener('change', () => {
    const preview = document.getElementById('displayPropertiesPreview');
    if (preview) {
        preview.style.opacity = '0.5';
        setTimeout(() => { preview.style.opacity = '1'; }, 200);
    }
});

document.getElementById('dpDisplaySelect').addEventListener('change', async (e) => {
    if (e.target.value === 'reselect' && editingDisplaySource) {
        try {
            const audioEnabled = document.getElementById('audioToggle') ? document.getElementById('audioToggle').checked : true;
            
            // To prevent the browser blocking a new screen-share prompt while one is currently active, 
            // we completely halt the existing media stream track before requesting a new one.
            if (editingDisplaySource.element && editingDisplaySource.element.srcObject) {
                const oldStream = editingDisplaySource.element.srcObject;
                oldStream.getTracks().forEach(track => track.stop());
                editingDisplaySource.element.srcObject = null;
            }
            
            const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: audioEnabled });
            
            if (editingDisplaySource.element) {
                editingDisplaySource.element.srcObject = stream;
            }
            const preview = document.getElementById('displayPropertiesPreview');
            preview.srcObject = stream;
            
        } catch(err) {
            console.warn("User cancelled screen share re-selection or prompt blocked.");
        }
        e.target.value = 'current'; // reset dropdown back to 'current' display mapping
    }
});

document.getElementById('closeDisplayPropertiesBtn').addEventListener('click', closeDisplayPropertiesModal);
document.getElementById('dpCancelBtn').addEventListener('click', closeDisplayPropertiesModal);

document.getElementById('dpDefaultsBtn').addEventListener('click', () => {
    document.getElementById('dpCaptureMethod').value = 'auto';
    document.getElementById('dpDisplaySelect').value = 'current';
    document.getElementById('dpCaptureCursor').checked = true;
    document.getElementById('dpForceSDR').checked = false;
    
    // Trigger visual refresh
    const preview = document.getElementById('displayPropertiesPreview');
    if (preview) {
        preview.style.opacity = '0.5';
        setTimeout(() => { preview.style.opacity = '1'; }, 200);
    }
});

document.getElementById('dpOkBtn').addEventListener('click', () => {
    if (editingDisplaySource) {
        editingDisplaySource.displayProps.captureMethod = document.getElementById('dpCaptureMethod').value;
        editingDisplaySource.displayProps.captureCursor = document.getElementById('dpCaptureCursor').checked;
        editingDisplaySource.displayProps.forceSDR = document.getElementById('dpForceSDR').checked;
    }
    closeDisplayPropertiesModal();
});

function closeDisplayPropertiesModal() {
    document.getElementById('displayPropertiesModal').classList.remove('active');
    document.getElementById('displayPropertiesPreview').srcObject = null;
    editingDisplaySource = null;
}


slideshowInput.onchange = (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const src = addSource('slideshow', 'Slide Show');
    
    const files = Array.from(e.target.files);
    let loadedCount = 0;
    
    files.forEach((file) => {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        img.onload = () => {
            loadedCount++;
            if (loadedCount === 1) { 
                src.width = snap(600);
                src.aspectRatio = img.width / img.height;
                src.height = src.width / src.aspectRatio;
            }
        };
        src.images.push(img);
        src.imageNames.push(file.name);
    });
};

imageInput.onchange = (e) => {
    if (!e.target.files[0]) return;
    const url = URL.createObjectURL(e.target.files[0]);
    const src = addSource('image', e.target.files[0].name);
    src.imageProps.filePath = e.target.files[0].name;
    const img = new Image();
    img.src = url;
    img.onload = () => {
        src.element = img;
        src.width = snap(600);
        src.aspectRatio = img.width / img.height;
        src.height = src.width / src.aspectRatio;
    };
};

mediaInput.onchange = (e) => {
    if (!e.target.files[0]) return;
    const file = e.target.files[0];
    const isAudio = file.type.startsWith('audio');
    const src = addSource('media', file.name);
    src.mediaProps.filePath = file.name;
    
    const media = document.createElement(isAudio ? 'audio' : 'video');
    media.src = URL.createObjectURL(file);
    media.loop = src.mediaProps.loop; 
    media.autoplay = true; 
    
    if (!isAudio) {
        // Appending the video to a hidden div forces the browser to decode frames!
        hiddenMediaContainer.appendChild(media);
        
        media.onloadedmetadata = () => {
            src.element = media;
            src.width = snap(600);
            src.aspectRatio = media.videoWidth / media.videoHeight;
            src.height = src.width / src.aspectRatio;
            media.play(); 
            updateActiveMediaPlayback();
        };
    } else {
        src.isAudioOnly = true;
        src.element = media;
        media.play();
    }
    setupAudioNode(media, src);
};

// --- MEDIA PROPERTIES WINDOW LOGIC ---
let editingMediaSource = null;

function openMediaProperties(src) {
    if (!src || (src.type !== 'media' && src.type !== 'vlc')) return;
    editingMediaSource = src;

    document.getElementById('mediaPropertiesTitle').innerHTML = `<i class="fas fa-cog"></i> Properties for '${src.name}'`;

    document.getElementById('propLocalFile').checked = src.mediaProps.localFile;
    updateLocalFileUI(src.mediaProps.localFile);
    document.getElementById('propFilePath').value = src.mediaProps.filePath || src.element?.src || '';
    document.getElementById('propLoop').checked = src.mediaProps.loop;
    document.getElementById('propRestartActive').checked = src.mediaProps.restartActive;
    document.getElementById('propHardwareDecode').checked = src.mediaProps.hardwareDecode;
    document.getElementById('propShowNothing').checked = src.mediaProps.showNothing;
    document.getElementById('propCloseInactive').checked = src.mediaProps.closeInactive;

    document.getElementById('propSpeedSlider').value = src.mediaProps.speed;
    document.getElementById('propSpeedInput').value = src.mediaProps.speed;

    document.getElementById('propYuvRange').value = src.mediaProps.yuvRange;
    document.getElementById('propAlpha').checked = src.mediaProps.alpha;
    document.getElementById('propFfmpeg').value = src.mediaProps.ffmpeg;

    const preview = document.getElementById('mediaPropertiesPreview');
    if (src.element) {
        preview.src = src.element.src;
        preview.loop = src.mediaProps.loop;
        preview.currentTime = src.element.currentTime;
        preview.playbackRate = src.mediaProps.speed / 100;
    }

    openModalCenter('mediaPropertiesModal');
}

function updateLocalFileUI(isLocal) {
    const label = document.getElementById('propFileLabel');
    const btn = document.getElementById('propFileActionBtn');
    if (isLocal) {
        label.textContent = "Local File";
        btn.textContent = "Browse";
    } else {
        label.textContent = "URL";
        btn.textContent = "Paste";
    }
}

document.getElementById('propLocalFile').addEventListener('change', (e) => {
    updateLocalFileUI(e.target.checked);
});

document.getElementById('propFileActionBtn').addEventListener('click', async () => {
    if (document.getElementById('propLocalFile').checked) {
        propFileInput.click();
    } else {
        try {
            const text = await navigator.clipboard.readText();
            document.getElementById('propFilePath').value = text;
        } catch (err) {
            document.getElementById('propFilePath').focus();
        }
    }
});

propFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        document.getElementById('propFilePath').value = file.name;
        const url = URL.createObjectURL(file);
        document.getElementById('mediaPropertiesPreview').src = url;
        if (editingMediaSource) {
            editingMediaSource.tempNewUrl = url;
        }
    }
});

document.getElementById('propSpeedSlider').addEventListener('input', (e) => {
    document.getElementById('propSpeedInput').value = e.target.value;
    const rate = e.target.value / 100;
    if (editingMediaSource && editingMediaSource.element) {
        editingMediaSource.element.playbackRate = rate;
    }
    document.getElementById('mediaPropertiesPreview').playbackRate = rate;
});

document.getElementById('propSpeedInput').addEventListener('input', (e) => {
    document.getElementById('propSpeedSlider').value = e.target.value;
    const rate = e.target.value / 100;
    if (editingMediaSource && editingMediaSource.element) {
        editingMediaSource.element.playbackRate = rate;
    }
    document.getElementById('mediaPropertiesPreview').playbackRate = rate;
});

document.getElementById('propLoop').addEventListener('change', (e) => {
    document.getElementById('mediaPropertiesPreview').loop = e.target.checked;
});

document.getElementById('propDefaultsBtn').addEventListener('click', () => {
    document.getElementById('propLocalFile').checked = true;
    updateLocalFileUI(true);
    document.getElementById('propLoop').checked = false; 
    document.getElementById('propRestartActive').checked = true;
    document.getElementById('propHardwareDecode').checked = false;
    document.getElementById('propShowNothing').checked = true;
    document.getElementById('propCloseInactive').checked = false;
    document.getElementById('propSpeedSlider').value = 100;
    document.getElementById('propSpeedInput').value = 100;
    document.getElementById('propYuvRange').value = 'auto';
    document.getElementById('propAlpha').checked = false;
    document.getElementById('propFfmpeg').value = '';
    
    if (editingMediaSource && editingMediaSource.element) {
        editingMediaSource.element.playbackRate = 1.0;
    }
    document.getElementById('mediaPropertiesPreview').playbackRate = 1.0;
});

document.getElementById('closeMediaPropertiesBtn').addEventListener('click', closeMediaPropertiesModal);
document.getElementById('propCancelBtn').addEventListener('click', () => {
    if (editingMediaSource && editingMediaSource.element) {
        editingMediaSource.element.playbackRate = editingMediaSource.mediaProps.speed / 100;
    }
    if (editingMediaSource) delete editingMediaSource.tempNewUrl;
    closeMediaPropertiesModal();
});

document.getElementById('propOkBtn').addEventListener('click', () => {
    if (editingMediaSource) {
        editingMediaSource.mediaProps.localFile = document.getElementById('propLocalFile').checked;
        editingMediaSource.mediaProps.filePath = document.getElementById('propFilePath').value;
        editingMediaSource.mediaProps.loop = document.getElementById('propLoop').checked;
        editingMediaSource.mediaProps.restartActive = document.getElementById('propRestartActive').checked;
        editingMediaSource.mediaProps.hardwareDecode = document.getElementById('propHardwareDecode').checked;
        editingMediaSource.mediaProps.showNothing = document.getElementById('propShowNothing').checked;
        editingMediaSource.mediaProps.closeInactive = document.getElementById('propCloseInactive').checked;
        editingMediaSource.mediaProps.speed = parseInt(document.getElementById('propSpeedSlider').value);
        editingMediaSource.mediaProps.yuvRange = document.getElementById('propYuvRange').value;
        editingMediaSource.mediaProps.alpha = document.getElementById('propAlpha').checked;
        editingMediaSource.mediaProps.ffmpeg = document.getElementById('propFfmpeg').value;

        if (editingMediaSource.tempNewUrl) {
            editingMediaSource.element.src = editingMediaSource.tempNewUrl;
            editingMediaSource.name = document.getElementById('propFilePath').value;
            document.getElementById('mediaSourceName').textContent = editingMediaSource.name;
            delete editingMediaSource.tempNewUrl;
            updateSourcesList(); 
        }

        if (editingMediaSource.element) {
            editingMediaSource.element.loop = editingMediaSource.mediaProps.loop;
            editingMediaSource.element.playbackRate = editingMediaSource.mediaProps.speed / 100;
        }
    }
    closeMediaPropertiesModal();
});

function closeMediaPropertiesModal() {
    document.getElementById('mediaPropertiesModal').classList.remove('active');
    const preview = document.getElementById('mediaPropertiesPreview');
    preview.pause();
    preview.src = '';
    editingMediaSource = null;
}

// --- SLIDESHOW PROPERTIES LOGIC ---
let editingSlideSource = null;
let editingSlideImages = [];
let selectedSlideIndex = -1;
let ssPreviewAnimFrame;

function openSlideshowProperties(src) {
    if (!src || src.type !== 'slideshow') return;
    editingSlideSource = src;
    
    // Copy references for editing isolated from main rendering
    editingSlideImages = src.images.map((img, i) => ({
        img: img,
        name: src.imageNames[i] || `Image ${i+1}`
    }));
    selectedSlideIndex = editingSlideImages.length > 0 ? 0 : -1;

    document.getElementById('slideshowPropertiesTitle').innerHTML = `<i class="fas fa-images"></i> Properties for '${src.name}'`;
    
    document.getElementById('ssPropVisibility').value = src.slideProps.visibility;
    document.getElementById('ssPropMode').value = src.slideProps.mode;
    document.getElementById('ssPropTransition').value = src.slideProps.transition;
    document.getElementById('ssPropTimeBetween').value = src.slideProps.timeBetween;
    document.getElementById('ssPropTransitionSpeed').value = src.slideProps.transitionSpeed;
    document.getElementById('ssPropPlaybackMode').value = src.slideProps.playbackMode;
    document.getElementById('ssPropHideWhenDone').checked = src.slideProps.hideWhenDone;
    document.getElementById('ssPropBounding').value = src.slideProps.boundingSize;

    renderSlideshowPropList();
    openModalCenter('slideshowPropertiesModal');
    startSlideshowPreviewLoop();
}

function renderSlideshowPropList() {
    const list = document.getElementById('ssPropImageList');
    list.innerHTML = '';
    editingSlideImages.forEach((item, idx) => {
        const div = document.createElement('div');
        div.className = `list-item ${selectedSlideIndex === idx ? 'active' : ''}`;
        div.textContent = item.name;
        div.onclick = () => {
            selectedSlideIndex = idx;
            renderSlideshowPropList();
        };
        list.appendChild(div);
    });
}

function startSlideshowPreviewLoop() {
    const canvas = document.getElementById('slideshowPropertiesPreview');
    const pCtx = canvas.getContext('2d');
    
    function draw() {
        if (!document.getElementById('slideshowPropertiesModal').classList.contains('active')) return;
        
        pCtx.clearRect(0,0,canvas.width,canvas.height);
        if (selectedSlideIndex >= 0 && selectedSlideIndex < editingSlideImages.length) {
            const item = editingSlideImages[selectedSlideIndex];
            if (item && item.img && item.img.complete) {
                // Ensure crisp preview matching layout box
                canvas.width = canvas.clientWidth;
                canvas.height = canvas.clientHeight;
                
                const iw = item.img.width;
                const ch = item.img.height;
                const scale = Math.min(canvas.width / iw, canvas.height / ch);
                const nw = iw * scale;
                const nh = ch * scale;
                const ox = (canvas.width - nw) / 2;
                const oy = (canvas.height - nh) / 2;
                
                pCtx.drawImage(item.img, ox, oy, nw, nh);
            }
        }
        
        ssPreviewAnimFrame = requestAnimationFrame(draw);
    }
    draw();
}

document.getElementById('ssBtnAdd').onclick = () => slideshowAddInput.click();
slideshowAddInput.onchange = (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    files.forEach((file) => {
        const img = new Image();
        img.src = URL.createObjectURL(file);
        editingSlideImages.push({ img: img, name: file.name });
    });
    if (selectedSlideIndex === -1) selectedSlideIndex = 0;
    renderSlideshowPropList();
};

document.getElementById('ssBtnRemove').onclick = () => {
    if(selectedSlideIndex > -1) {
        editingSlideImages.splice(selectedSlideIndex, 1);
        selectedSlideIndex = Math.max(0, selectedSlideIndex - 1);
        if(editingSlideImages.length === 0) selectedSlideIndex = -1;
        renderSlideshowPropList();
    }
};

document.getElementById('ssBtnUp').onclick = () => {
    if(selectedSlideIndex > 0) {
        const temp = editingSlideImages[selectedSlideIndex];
        editingSlideImages[selectedSlideIndex] = editingSlideImages[selectedSlideIndex - 1];
        editingSlideImages[selectedSlideIndex - 1] = temp;
        selectedSlideIndex--;
        renderSlideshowPropList();
    }
};

document.getElementById('ssBtnDown').onclick = () => {
    if(selectedSlideIndex < editingSlideImages.length - 1 && selectedSlideIndex > -1) {
        const temp = editingSlideImages[selectedSlideIndex];
        editingSlideImages[selectedSlideIndex] = editingSlideImages[selectedSlideIndex + 1];
        editingSlideImages[selectedSlideIndex + 1] = temp;
        selectedSlideIndex++;
        renderSlideshowPropList();
    }
};

document.getElementById('ssPropDefaultsBtn').addEventListener('click', () => {
    document.getElementById('ssPropVisibility').value = 'always';
    document.getElementById('ssPropMode').value = 'auto';
    document.getElementById('ssPropTransition').value = 'cut';
    document.getElementById('ssPropTimeBetween').value = 2000;
    document.getElementById('ssPropTransitionSpeed').value = 700;
    document.getElementById('ssPropPlaybackMode').value = 'loop';
    document.getElementById('ssPropHideWhenDone').checked = false;
    document.getElementById('ssPropBounding').value = '1920x1080';
});

document.getElementById('closeSlideshowPropertiesBtn').addEventListener('click', closeSlideshowPropertiesModal);
document.getElementById('ssPropCancelBtn').addEventListener('click', closeSlideshowPropertiesModal);

document.getElementById('ssPropOkBtn').addEventListener('click', () => {
    if (editingSlideSource) {
        editingSlideSource.slideProps.visibility = document.getElementById('ssPropVisibility').value;
        editingSlideSource.slideProps.mode = document.getElementById('ssPropMode').value;
        editingSlideSource.slideProps.transition = document.getElementById('ssPropTransition').value;
        editingSlideSource.slideProps.timeBetween = parseInt(document.getElementById('ssPropTimeBetween').value) || 2000;
        editingSlideSource.slideProps.transitionSpeed = parseInt(document.getElementById('ssPropTransitionSpeed').value) || 700;
        editingSlideSource.slideProps.playbackMode = document.getElementById('ssPropPlaybackMode').value;
        editingSlideSource.slideProps.hideWhenDone = document.getElementById('ssPropHideWhenDone').checked;
        editingSlideSource.slideProps.boundingSize = document.getElementById('ssPropBounding').value;

        // Apply updated array
        editingSlideSource.images = editingSlideImages.map(item => item.img);
        editingSlideSource.imageNames = editingSlideImages.map(item => item.name);
        
        // Reset playback loop logic safely
        editingSlideSource.currentSlide = 0;
        editingSlideSource.isFinished = false;
        editingSlideSource.lastSlideTime = performance.now();
    }
    closeSlideshowPropertiesModal();
});

function closeSlideshowPropertiesModal() {
    document.getElementById('slideshowPropertiesModal').classList.remove('active');
    cancelAnimationFrame(ssPreviewAnimFrame);
    editingSlideSource = null;
    editingSlideImages = [];
}

// --- 5. UI CONTROLS ---
document.getElementById('textInputSource').oninput = (e) => { if(selectedSource) selectedSource.text = e.target.value; };
document.getElementById('textColorSource').oninput = (e) => { if(selectedSource) selectedSource.textProps.color = e.target.value; };
document.getElementById('textFontSource').onchange = (e) => { if(selectedSource) selectedSource.textProps.font = e.target.value; };
document.getElementById('textSizeSource').oninput = (e) => { if(selectedSource) selectedSource.fontSize = parseInt(e.target.value); };

document.getElementById('mediaPlayBtn').onclick = () => { if(selectedSource && selectedSource.element) selectedSource.element.play(); };
document.getElementById('mediaPauseBtn').onclick = () => { if(selectedSource && selectedSource.element) selectedSource.element.pause(); };
document.getElementById('mediaStopBtn').onclick = () => { 
    if(selectedSource && selectedSource.element) { 
        selectedSource.element.pause(); 
        selectedSource.element.currentTime = 0; 
    } 
};
document.getElementById('mediaSeek').oninput = (e) => {
    if(selectedSource && selectedSource.element) {
        selectedSource.element.currentTime = (e.target.value / 100) * selectedSource.element.duration;
    }
};

removeSourceBtn.onclick = () => {
    if (selectedSource) {
        // CLEANUP MEDIA RESOURCES
        if(selectedSource.element && typeof selectedSource.element.pause === 'function') {
            selectedSource.element.pause();
            if (selectedSource.element.parentNode === hiddenMediaContainer) {
                hiddenMediaContainer.removeChild(selectedSource.element);
            }
        }
        
        const mixUi = document.getElementById(`mix-${selectedSource.id}`);
        if(mixUi) mixUi.remove();
        
        if (selectedSource.iframe) {
            selectedSource.iframe.remove();
        }
        
        const idx = sources.indexOf(selectedSource);
        sources.splice(idx, 1);
        selectSource(null);
        
        // Refresh routing and playback recursively in case the deleted item was affecting hierarchy
        updateActiveMediaPlayback();
        updateAudioRouting();
    }
};

function formatTime(seconds) {
    if (isNaN(seconds)) return "00:00:00";
    const h = Math.floor(seconds / 3600), m = Math.floor((seconds % 3600) / 60), s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// --- 4. ADD SOURCE MENU LOGIC ---
addSourceBtn.onclick = () => addSourceMenu.classList.toggle('active');
document.addEventListener('click', (e) => { if (e.target !== addSourceBtn) addSourceMenu.classList.remove('active'); });

document.querySelectorAll('.context-item:not(.disabled)').forEach(item => {
    item.onclick = async () => {
        const action = item.dataset.action;
        const audioEnabled = document.getElementById('audioToggle') ? document.getElementById('audioToggle').checked : true;
        
        // INTERCEPT AUDIO OUTPUT CAPTURE
        if (action === 'audio-out' || action === 'audio-app') {
            openModalCenter('audioWarningModal');
            return; 
        }
        
        // COLOR SOURCE LOGIC
        if (action === 'color') {
            const src = addSource('color', 'Color Source');
            src.width = 1920; 
            src.height = 1080;
            src.aspectRatio = 16/9;
            openColorProperties(src); 
            return;
        }

        // NESTED SCENE LOGIC
        if (action === 'scene') {
            const select = document.getElementById('nestedSceneSelect');
            select.innerHTML = '';
            let validScenes = 0;
            scenes.forEach(s => {
                if (s.id !== activeScene.id) { // Prevent self-nesting
                    const opt = document.createElement('option');
                    opt.value = s.id;
                    opt.textContent = s.name;
                    select.appendChild(opt);
                    validScenes++;
                }
            });
            if (validScenes === 0) {
                showCustomAlert("There are no other scenes available to add. Create a new scene first!");
                return;
            }
            openModalCenter('addNestedSceneModal');
            return;
        }
        
        // ADD BROWSER SOURCE MODAL
        if (action === 'browser') {
            document.getElementById('browserAddUrlInput').value = "https://shorturl.at/6QyYn";
            openModalCenter('addBrowserSourceModal');
            return;
        }

        if (action === 'display' || action === 'window') {
            try {
                const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: audioEnabled });
                const src = addSource('display', 'Screen Capture');
                const video = document.createElement('video');
                video.autoplay = true;
                video.muted = true; 
                video.playsInline = true;
                
                video.onloadedmetadata = () => {
                    src.width = snap(obsCanvas.width * 0.8);
                    src.aspectRatio = video.videoWidth / video.videoHeight;
                    src.height = src.width / src.aspectRatio;
                    src.x = snap((obsCanvas.width - src.width)/2);
                    src.y = snap((obsCanvas.height - src.height)/2);
                    src.element = video;
                    video.play(); 
                    
                    if (audioEnabled && stream.getAudioTracks().length > 0) {
                        // Create a dedicated audio source for the screen share if audio is captured
                        const audioSrc = addSource('audio', 'Screen Capture Audio');
                        audioSrc.isAudioOnly = true;
                        setupAudioNode(stream, audioSrc);
                    }
                };
                video.srcObject = stream;
            } catch (e) { console.error(e); }
        }
        else if (action === 'video-device') {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const src = addSource('camera', 'Webcam');
                const video = document.createElement('video');
                video.autoplay = true;
                video.muted = true;
                video.playsInline = true;
                
                video.onloadedmetadata = () => {
                    src.element = video;
                    src.width = snap(400);
                    src.aspectRatio = video.videoWidth / video.videoHeight;
                    src.height = src.width / src.aspectRatio;
                    video.play(); 
                };
                video.srcObject = stream;
            } catch (e) { console.error(e); }
        }
        else if (action === 'audio-in') {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const src = addSource('audio-in', 'Microphone');
                src.isAudioOnly = true;
                setupAudioNode(stream, src);
            } catch (e) { console.error(e); }
        }
        else if (action === 'text') {
            const src = addSource('text', 'GDI+ Text');
            src.text = "Sample Text";
            src.x = 100; src.y = 100;
        }
        else if (action === 'image') imageInput.click();
        else if (action === 'slideshow') slideshowInput.click();
        else if (action === 'media' || action === 'vlc') mediaInput.click();
    };
});

// NESTED SCENE CONFIRMATION
document.getElementById('confirmAddNestedSceneBtn').onclick = () => {
    const select = document.getElementById('nestedSceneSelect');
    const targetSceneId = parseInt(select.value);
    const targetScene = scenes.find(s => s.id === targetSceneId);

    if (targetScene) {
        const src = addSource('scene', targetScene.name);
        src.targetSceneId = targetSceneId;
        src.width = 1920; 
        src.height = 1080;
        src.aspectRatio = 16/9;
        
        // Create an isolated canvas buffer to render this nested scene into cleanly
        src.offscreenCanvas = document.createElement('canvas');
        src.offscreenCanvas.width = 1920;
        src.offscreenCanvas.height = 1080;
        
        setupAudioNode(null, src); 
        updateActiveMediaPlayback();
    }
    document.getElementById('addNestedSceneModal').classList.remove('active');
};

// BROWSER SOURCE CREATION CONFIRM
document.getElementById('confirmAddBrowserBtn').onclick = () => {
    let url = document.getElementById('browserAddUrlInput').value;
    if (url) {
        if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('file://')) {
            url = 'https://' + url;
        }
        const src = addSource('browser', 'Browser Source');
        src.browserProps.url = url;
        
        src.browserProps.width = 800;
        src.browserProps.height = 600;
        src.browserProps.zoom = 0.8; // Set default zoom to 80% as requested
        src.browserProps.transparent = true;
        
        // Setup initial bounding box natively scaled to the 80% zoom
        src.width = src.browserProps.width * src.browserProps.zoom;
        src.height = src.browserProps.height * src.browserProps.zoom;
        src.aspectRatio = src.browserProps.width / src.browserProps.height;
        src.url = url;
        
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.style.position = 'absolute';
        iframe.style.border = 'none';
        iframe.style.pointerEvents = 'none'; 
        iframe.style.background = 'transparent';
        
        document.getElementById('domOverlayContainer').appendChild(iframe);
        src.iframe = iframe;
        
        // Trigger initial filter assignment
        applyDOMFilters(src);
        
        // Bind the new Browser Source visually to the Audio Mixer
        setupAudioNode(null, src); 
        
        document.getElementById('addBrowserSourceModal').classList.remove('active');
    }
};

// --- 6. RECORDING ENGINE ---
startBtn.addEventListener('click', async () => {
    if (sources.length === 0) { showCustomAlert("Please add at least one source!"); return; }

    recordedChunks = [];
    if (audioCtx.state === 'suspended') await audioCtx.resume();
    
    try {
        const canvasStream = liveRenderCanvas.captureStream(30); 
        if (audioDest.stream.getAudioTracks().length > 0) {
            canvasStream.addTrack(audioDest.stream.getAudioTracks()[0]);
        }

        let options = { mimeType: 'video/webm;codecs=vp9,opus' };
        if (!MediaRecorder.isTypeSupported(options.mimeType)) options.mimeType = 'video/webm;codecs=vp8,opus';
        if (!MediaRecorder.isTypeSupported(options.mimeType)) options.mimeType = 'video/webm';

        mediaRecorder = new MediaRecorder(canvasStream, options);
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) recordedChunks.push(e.data); };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            latestRecordingUrl = URL.createObjectURL(blob);
            const duration = (Date.now() - recordingStartTime) / 1000;

            const video = {
                id: Date.now(),
                url: latestRecordingUrl,
                blob: blob,
                duration: duration,
                name: `REC_${new Date().getTime()}`,
                trimStart: 0,
                trimEnd: duration,
                crop: null
            };

            videoLibrary.push(video);
            addVideoToLibrary(video);
            addVideoToTimeline(video);

            currentEditingVideo = video;
            editorPreview.src = video.url;
            enableEditorButtons();
            
            downloadRecordingBtn.disabled = false;
        };
        
        mediaRecorder.start(100);
        recordingStartTime = Date.now();
        
        recordingInterval = setInterval(() => {
            const elapsed = Date.now() - recordingStartTime;
            document.getElementById('recordingTime').innerHTML = `<i class="fas fa-circle" style="color:#ff4d4d;"></i> ${formatTime(elapsed/1000)}`;
            document.getElementById('statusBar').style.color = (Math.floor(elapsed/1000) % 2 === 0) ? '#ff4d4d' : '#a0a0a0';
            
            // Mock recording stat data
            if(document.getElementById('statsModal').classList.contains('active')) {
                const mb = (elapsed / 1000) * 0.8; // mock 0.8 MB/s
                document.getElementById('statRecData').textContent = mb.toFixed(1) + ' MiB';
                document.getElementById('statRecBitrate').textContent = (6000 + Math.random() * 500).toFixed(0) + ' kb/s';
            }

        }, 1000);

        startBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        document.getElementById('statusBar').textContent = 'Recording';
        document.getElementById('statRecStatus').textContent = 'Recording';
    } catch (err) {
        console.error(err);
        showCustomAlert("Failed to start recording. A media source might be preventing capture: " + err.message);
    }
});

stopBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearInterval(recordingInterval);
    }
    startBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    document.getElementById('statusBar').textContent = 'Ready';
    document.getElementById('statusBar').style.color = '#a0a0a0';
    document.getElementById('recordingTime').innerHTML = `<i class="fas fa-circle" style="color:#888;"></i> 00:00:00`;
    document.getElementById('statRecStatus').textContent = 'Inactive';
    document.getElementById('statRecBitrate').textContent = '0 kb/s';
});

downloadRecordingBtn.addEventListener('click', () => {
    if (latestRecordingUrl) {
        const a = document.createElement('a');
        a.href = latestRecordingUrl;
        a.download = `OBS_Web_Recording_${Date.now()}.webm`;
        a.click();
    }
});

// --- 7. PROFESSIONAL RECORDINGS & EDITOR ENGINE ---
openEditorBtn.addEventListener('click', () => openModalCenter('editorModal'));
closeEditorBtn.addEventListener('click', () => {
    document.getElementById('editorModal').classList.remove('active');
    editorPreview.pause();
});

exportBtn.addEventListener('click', exportVideo);

insertBtn.addEventListener('click', () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'video/*,audio/*';
    
    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const url = URL.createObjectURL(file);
            const videoEl = document.createElement('video');
            videoEl.src = url;
            
            videoEl.onloadedmetadata = () => {
                const video = {
                    id: Date.now(),
                    url: url,
                    blob: file,
                    duration: videoEl.duration,
                    name: file.name,
                    trimStart: 0,
                    trimEnd: videoEl.duration,
                    crop: null
                };
                
                videoLibrary.push(video);
                addVideoToLibrary(video);
                addVideoToTimeline(video);
            };
        }
    };
    fileInput.click();
});

function addVideoToLibrary(video) {
    const thumbnail = document.createElement('div');
    thumbnail.className = 'video-thumbnail';
    thumbnail.dataset.videoId = video.id;

    const videoEl = document.createElement('video');
    videoEl.src = video.url;
    videoEl.muted = true;
    thumbnail.appendChild(videoEl);

    thumbnail.addEventListener('click', () => {
        document.querySelectorAll('.video-thumbnail').forEach(t => t.classList.remove('selected'));
        thumbnail.classList.add('selected');
        currentEditingVideo = video;
        editorPreview.src = video.url;
        enableEditorButtons();
    });

    videoLibraryEl.appendChild(thumbnail);
}

// EDITOR PLAYBACK CONTROLS
let editorPlaying = false;
let editorPlayInterval;

document.getElementById('editorPlayBtn').onclick = () => {
    editorPreview.play();
    editorPlaying = true;
    editorPlayInterval = setInterval(() => {
        const px = editorPreview.currentTime * TIMELINE_SCALE;
        playhead.style.left = px + 'px';
    }, 33);
};

document.getElementById('editorPauseBtn').onclick = () => {
    editorPreview.pause();
    editorPlaying = false;
    clearInterval(editorPlayInterval);
};

// SPLIT LOGIC
document.getElementById('editorSplitBtn').onclick = () => {
    if (!selectedClipElement || !currentEditingVideo) return;
    const currentTime = editorPreview.currentTime;
    
    const clipIdx = timelineClips.findIndex(c => c.clip === selectedClipElement);
    if(clipIdx === -1) return;
    
    const clipData = timelineClips[clipIdx];
    const vid = clipData.video;
    
    if (currentTime > vid.trimStart && currentTime < vid.trimEnd) {
        const newVid = { ...vid, id: Date.now(), trimStart: currentTime };
        vid.trimEnd = currentTime;
        
        const width = (vid.trimEnd - vid.trimStart) * TIMELINE_SCALE;
        clipData.clip.style.width = Math.max(10, width) + 'px';
        
        const position = clipData.clip.offsetLeft + width;
        addVideoToTimeline(newVid, position);
    }
};

// DELETE LOGIC
document.getElementById('editorDeleteBtn').onclick = () => {
    if (!selectedClipElement) return;
    const idx = timelineClips.findIndex(c => c.clip === selectedClipElement);
    if (idx !== -1) {
        timelineClips.splice(idx, 1);
        selectedClipElement.remove();
        selectedClipElement = null;
    }
};

// EDITOR TIMELINE SCRUBBING
editorPreview.addEventListener('timeupdate', () => {
    if (!editorPlaying) {
        const px = editorPreview.currentTime * TIMELINE_SCALE;
        playhead.style.left = px + 'px';
    }
});

timeline.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('trim-handle') || e.target.classList.contains('video-clip')) return;
    const rect = timelineTrack.getBoundingClientRect();
    const clickX = e.clientX - rect.left + timeline.scrollLeft;
    if (clickX >= 0 && editorPreview.duration) {
        editorPreview.currentTime = clickX / TIMELINE_SCALE;
    }
});

function addVideoToTimeline(video, position = null) {
    const clip = document.createElement('div');
    clip.className = 'video-clip';
    clip.dataset.videoId = video.id;
    clip.textContent = video.name;
    
    const width = (video.trimEnd - video.trimStart) * TIMELINE_SCALE;
    clip.style.width = Math.max(30, width) + 'px';
    clip.style.left = (position !== null ? position : timelineClips.length * 10) + 'px';

    const leftHandle = document.createElement('div');
    leftHandle.className = 'trim-handle left';
    const rightHandle = document.createElement('div');
    rightHandle.className = 'trim-handle right';

    clip.appendChild(leftHandle);
    clip.appendChild(rightHandle);

    // Clip Selection Logic
    clip.addEventListener('mousedown', (e) => {
        document.querySelectorAll('.video-clip').forEach(c => c.classList.remove('selected-clip'));
        clip.classList.add('selected-clip');
        selectedClipElement = clip;
        currentEditingVideo = video;
    });

    makeTimelineDraggable(clip);
    makeTrimmable(clip, leftHandle, rightHandle, video, TIMELINE_SCALE);
    
    timelineTrack.appendChild(clip);
    timelineClips.push({ clip, video });
}

function makeTimelineDraggable(element) {
    let p1 = 0, p3 = 0;
    element.onmousedown = (e) => {
        if (e.target.classList.contains('trim-handle')) return;
        
        document.querySelectorAll('.video-clip').forEach(c => c.classList.remove('selected-clip'));
        element.classList.add('selected-clip');
        selectedClipElement = element;

        e.preventDefault();
        p3 = e.clientX;
        document.onmouseup = () => { document.onmouseup = null; document.onmousemove = null; };
        document.onmousemove = (e) => {
            e.preventDefault();
            p1 = p3 - e.clientX;
            p3 = e.clientX;
            element.style.left = Math.max(0, element.offsetLeft - p1) + 'px';
        };
    };
}

function makeTrimmable(clip, leftHandle, rightHandle, video, scale) {
    leftHandle.onmousedown = (e) => { e.stopPropagation(); handleTrim(e, clip, video, 'left', scale); };
    rightHandle.onmousedown = (e) => { e.stopPropagation(); handleTrim(e, clip, video, 'right', scale); };
}

function handleTrim(e, clip, video, side, scale) {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = clip.offsetWidth;
    const startLeft = clip.offsetLeft;

    function onMouseMove(e) {
        const delta = e.clientX - startX;
        if (side === 'left') {
            const newLeft = Math.max(0, startLeft + delta);
            const newWidth = Math.max(20, startWidth - delta);
            clip.style.left = newLeft + 'px';
            clip.style.width = newWidth + 'px';
            video.trimStart = Math.max(0, video.trimStart + (delta / scale)); 
            editorPreview.currentTime = video.trimStart; 
        } else {
            const newWidth = Math.max(20, startWidth + delta);
            clip.style.width = newWidth + 'px';
            video.trimEnd = Math.min(video.duration, video.trimStart + (newWidth / scale)); 
            editorPreview.currentTime = video.trimEnd; 
        }
    }

    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
}


// --- 8. CROP EDITOR LOGIC ---
const cropArea = document.getElementById('cropArea');
const cropBoundsContainer = document.getElementById('cropBoundsContainer');
let isDraggingCrop = false, isResizingCrop = false, currentCropHandle = '';
let cropStartX, cropStartY, cropStartRect;

cropBtn.addEventListener('click', () => {
    if (!currentEditingVideo) return;
    const cropPreview = document.getElementById('cropPreview');
    cropPreview.src = currentEditingVideo.url;
    openModalCenter('cropModal');
    
    // Wait for metadata to load so the boundaries are perfectly scaled to the video
    cropPreview.onloadedmetadata = () => {
        if (!currentEditingVideo.crop) {
            cropArea.style.left = '10%';
            cropArea.style.top = '10%';
            cropArea.style.width = '80%';
            cropArea.style.height = '80%';
        } else {
            const c = currentEditingVideo.crop;
            cropArea.style.left = (c.x * 100) + '%';
            cropArea.style.top = (c.y * 100) + '%';
            cropArea.style.width = (c.width * 100) + '%';
            cropArea.style.height = (c.height * 100) + '%';
        }
    };
});

cropArea.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('crop-handle')) {
        isResizingCrop = true;
        if(e.target.classList.contains('tl')) currentCropHandle = 'tl';
        else if(e.target.classList.contains('tr')) currentCropHandle = 'tr';
        else if(e.target.classList.contains('bl')) currentCropHandle = 'bl';
        else if(e.target.classList.contains('br')) currentCropHandle = 'br';
    } else {
        isDraggingCrop = true;
    }
    cropStartX = e.clientX;
    cropStartY = e.clientY;
    cropStartRect = cropArea.getBoundingClientRect();
    e.preventDefault();
    e.stopPropagation();
});

window.addEventListener('mousemove', (e) => {
    if (!isDraggingCrop && !isResizingCrop) return;
    const containerRect = cropBoundsContainer.getBoundingClientRect();
    const deltaX = e.clientX - cropStartX;
    const deltaY = e.clientY - cropStartY;

    let newL = cropStartRect.left - containerRect.left;
    let newT = cropStartRect.top - containerRect.top;
    let newW = cropStartRect.width;
    let newH = cropStartRect.height;

    if (isDraggingCrop) {
        newL += deltaX;
        newT += deltaY;
    } else if (isResizingCrop) {
        if (currentCropHandle.includes('l')) { newL += deltaX; newW -= deltaX; }
        if (currentCropHandle.includes('r')) { newW += deltaX; }
        if (currentCropHandle.includes('t')) { newT += deltaY; newH -= deltaY; }
        if (currentCropHandle.includes('b')) { newH += deltaY; }
    }

    // Minimum size limits
    if (newW < 20) { newW = 20; if(currentCropHandle.includes('l')) newL = cropStartRect.left - containerRect.left + cropStartRect.width - 20; }
    if (newH < 20) { newH = 20; if(currentCropHandle.includes('t')) newT = cropStartRect.top - containerRect.top + cropStartRect.height - 20; }

    // Outer boundary limits
    newL = Math.max(0, newL);
    newT = Math.max(0, newT);
    if (newL + newW > containerRect.width) {
        if (isDraggingCrop) newL = containerRect.width - newW;
        else newW = containerRect.width - newL;
    }
    if (newT + newH > containerRect.height) {
        if (isDraggingCrop) newT = containerRect.height - newH;
        else newH = containerRect.height - newT;
    }

    cropArea.style.left = (newL / containerRect.width * 100) + '%';
    cropArea.style.top = (newT / containerRect.height * 100) + '%';
    cropArea.style.width = (newW / containerRect.width * 100) + '%';
    cropArea.style.height = (newH / containerRect.height * 100) + '%';
});

window.addEventListener('mouseup', () => {
    isDraggingCrop = false;
    isResizingCrop = false;
});

// Calculate and apply visual crop logic
document.getElementById('applyCropBtn').onclick = () => {
    const containerRect = cropBoundsContainer.getBoundingClientRect();
    const cropRect = cropArea.getBoundingClientRect();
    
    currentEditingVideo.crop = {
        x: (cropRect.left - containerRect.left) / containerRect.width,
        y: (cropRect.top - containerRect.top) / containerRect.height,
        width: cropRect.width / containerRect.width,
        height: cropRect.height / containerRect.height
    };
    
    const cp = currentEditingVideo.crop;
    const top = cp.y * 100;
    const left = cp.x * 100;
    const right = 100 - ((cp.x + cp.width) * 100);
    const bottom = 100 - ((cp.y + cp.height) * 100);
    editorPreview.style.clipPath = `inset(${top}% ${right}% ${bottom}% ${left}%)`;
    
    document.getElementById('cropModal').classList.remove('active');
};

document.getElementById('cancelCropBtn').onclick = () => {
    document.getElementById('cropModal').classList.remove('active');
};

async function exportVideo() {
    if (timelineClips.length === 0) return;
    
    document.getElementById('statusBar').textContent = 'Rendering Export... Please wait.';
    exportBtn.disabled = true;
    exportBtn.textContent = "Rendering...";

    const sortedClips = timelineClips.slice().sort((a, b) => a.clip.offsetLeft - b.clip.offsetLeft);
    
    const renderCanvas = document.createElement('canvas');
    renderCanvas.width = liveRenderCanvas.width; 
    renderCanvas.height = liveRenderCanvas.height;
    const renderCtx = renderCanvas.getContext('2d');
    
    const exportStream = renderCanvas.captureStream(30);
    const exportRecorder = new MediaRecorder(exportStream, { mimeType: 'video/webm;codecs=vp8' });
    const exportChunks = [];
    
    exportRecorder.ondataavailable = e => { if (e.data.size > 0) exportChunks.push(e.data); };
    
    const exportPromise = new Promise(resolve => {
        exportRecorder.onstop = () => {
            const blob = new Blob(exportChunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `obs_edited_${Date.now()}.webm`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            resolve();
        };
    });

    exportRecorder.start();

    const hiddenVideo = document.createElement('video');
    hiddenVideo.muted = true; 

    for (const clipData of sortedClips) {
        const vid = clipData.video;
        hiddenVideo.src = vid.url;
        await new Promise(r => hiddenVideo.onloadedmetadata = r);
        
        hiddenVideo.currentTime = vid.trimStart;
        await new Promise(r => hiddenVideo.onseeked = r);
        hiddenVideo.play();
        
        const durationMs = (vid.trimEnd - vid.trimStart) * 1000;
        const startTime = Date.now();
        
        await new Promise(resolveClip => {
            function renderFrame() {
                const elapsed = Date.now() - startTime;
                
                if (elapsed >= durationMs || hiddenVideo.currentTime >= vid.trimEnd) {
                    hiddenVideo.pause();
                    resolveClip();
                    return;
                }
                
                renderCtx.clearRect(0, 0, renderCanvas.width, renderCanvas.height);
                
                if (vid.crop) {
                    const sx = vid.crop.x * hiddenVideo.videoWidth;
                    const sy = vid.crop.y * hiddenVideo.videoHeight;
                    const sw = vid.crop.width * hiddenVideo.videoWidth;
                    const sh = vid.crop.height * hiddenVideo.videoHeight;
                    renderCtx.drawImage(hiddenVideo, sx, sy, sw, sh, 0, 0, renderCanvas.width, renderCanvas.height);
                } else {
                    renderCtx.drawImage(hiddenVideo, 0, 0, renderCanvas.width, renderCanvas.height);
                }
                
                requestAnimationFrame(renderFrame);
            }
            renderFrame();
        });
    }

    exportRecorder.stop();
    await exportPromise;
    
    document.getElementById('statusBar').textContent = 'Export Complete!';
    exportBtn.innerHTML = '<i class="fas fa-file-export"></i> Export Final Video';
    exportBtn.disabled = false;
}

function enableEditorButtons() {
    cropBtn.disabled = false;
    exportBtn.disabled = false;
}
// =========================================================================
// ===================== NEW AUDIO UI FEATURES ADDON =======================
// =========================================================================

// --- 1. AUDIO MIXER CONTEXT MENU LOGIC ---
let activeAudioMixerSource = null;
const audioMixerContextMenu = document.getElementById('audioMixerContextMenu');

// Overwrite the renderMixerUI function to include the triple dot menu bindings
function renderMixerUI(src) {
    if(document.getElementById(`mix-${src.id}`)) return; // Already rendered
    
    const mixerHtml = `
        <div class="audio-track" id="mix-${src.id}">
            <div class="audio-header">
                <span>${src.name}</span>
                <span id="db-${src.id}">0.0 dB</span>
            </div>
            <div class="audio-body">
                <div class="audio-left-icons">
                    <div class="audio-menu-btn" data-source-id="${src.id}"><i class="fas fa-ellipsis-v"></i></div>
                    <div class="audio-speaker-btn"><i class="fas fa-volume-up"></i></div>
                </div>
                <div class="audio-controls">
                    <div class="audio-meter-container">
                        <div class="audio-meter">
                            <div class="audio-meter-fill" id="meter-L-${src.id}" style="width: 0%;"></div>
                        </div>
                        <div class="audio-meter-spacer"></div>
                        <div class="audio-meter">
                            <div class="audio-meter-fill" id="meter-R-${src.id}" style="width: 0%;"></div>
                        </div>
                    </div>
                    <div class="audio-ticks">
                        <span>-60</span><span>-55</span><span>-50</span><span>-45</span><span>-40</span><span>-35</span><span>-30</span><span>-25</span><span>-20</span><span>-15</span><span>-10</span><span>-5</span><span>0</span>
                    </div>
                    <input type="range" min="0" max="100" value="100" class="audio-slider" id="vol-${src.id}">
                </div>
            </div>
        </div>`;
    
    audioMixerContainer.insertAdjacentHTML('beforeend', mixerHtml);
    
    // Bind volume slider
    document.getElementById(`vol-${src.id}`).addEventListener('input', (e) => {
        const val = e.target.value / 100;
        if(src.gainNode) src.gainNode.gain.value = val;
        
        let db = 20 * Math.log10(val);
        if (val === 0) db = -Infinity;
        document.getElementById(`db-${src.id}`).textContent = val === 0 ? '-inf dB' : `${db.toFixed(1)} dB`;
    });
    
    // Visually restore volume node state
    if (src.gainNode) {
        const currentVal = src.gainNode.gain.value;
        document.getElementById(`vol-${src.id}`).value = currentVal * 100;
        let db = 20 * Math.log10(currentVal);
        if (currentVal === 0) db = -Infinity;
        document.getElementById(`db-${src.id}`).textContent = currentVal === 0 ? '-inf dB' : `${db.toFixed(1)} dB`;
    }

    // Bind triple dot menu
    const menuBtn = document.querySelector(`#mix-${src.id} .audio-menu-btn`);
    menuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        activeAudioMixerSource = src;
        const rect = menuBtn.getBoundingClientRect();
        audioMixerContextMenu.style.left = rect.left + 'px';
        
        // Ensure menu doesn't clip below the screen
        if (window.innerHeight - rect.bottom < 300) {
            audioMixerContextMenu.style.top = 'auto';
            audioMixerContextMenu.style.bottom = (window.innerHeight - rect.top) + 'px';
        } else {
            audioMixerContextMenu.style.top = rect.bottom + 'px';
            audioMixerContextMenu.style.bottom = 'auto';
        }
        audioMixerContextMenu.classList.add('active');
    });
}

// Global click to close the context menu
document.addEventListener('click', (e) => {
    if (!e.target.closest('#audioMixerContextMenu') && !e.target.closest('.audio-menu-btn')) {
        audioMixerContextMenu.classList.remove('active');
    }
});

// Context Menu Action Bindings
document.getElementById('ctxFilters').addEventListener('click', () => {
    audioMixerContextMenu.classList.remove('active');
    if (activeAudioMixerSource) openAudioFiltersModal(activeAudioMixerSource);
});

document.getElementById('ctxProperties').addEventListener('click', () => {
    audioMixerContextMenu.classList.remove('active');
    if (activeAudioMixerSource) openAudioDeviceProperties(activeAudioMixerSource);
});

document.getElementById('ctxAdvancedProperties').addEventListener('click', () => {
    audioMixerContextMenu.classList.remove('active');
    // Open filters as requested for advanced properties
    if (activeAudioMixerSource) openAudioFiltersModal(activeAudioMixerSource);
});

document.getElementById('ctxHide').addEventListener('click', () => {
    audioMixerContextMenu.classList.remove('active');
    if (activeAudioMixerSource) {
        document.getElementById(`mix-${activeAudioMixerSource.id}`).style.display = 'none';
    }
});

document.getElementById('ctxUnhideAll').addEventListener('click', () => {
    audioMixerContextMenu.classList.remove('active');
    document.querySelectorAll('.audio-track').forEach(el => el.style.display = 'flex');
});


// --- 2. AUDIO FILTERS MODAL LOGIC ---
const audioFiltersModal = document.getElementById('audioFiltersModal');
let currentAudioFiltersSource = null;
let selectedAudioFilterId = null;

function openAudioFiltersModal(src) {
    currentAudioFiltersSource = src;
    if (!src.audioFilters) src.audioFilters = []; // Initialize array if missing
    
    document.getElementById('audioFiltersTitle').textContent = `Filters for '${src.name}'`;
    refreshAudioFiltersList();
    openModalCenter('audioFiltersModal');
}

function refreshAudioFiltersList() {
    const list = document.getElementById('audioFiltersList');
    list.innerHTML = '';
    const filters = currentAudioFiltersSource.audioFilters;
    
    if (filters.length === 0) {
        selectedAudioFilterId = null;
        renderAudioFilterSettings(null);
        return;
    }

    filters.forEach(f => {
        const div = document.createElement('div');
        div.className = `audio-filter-item ${f.id === selectedAudioFilterId ? 'active' : ''}`;
        div.innerHTML = `<i class="fas fa-eye"></i> ${f.name}`;
        div.onclick = () => {
            selectedAudioFilterId = f.id;
            refreshAudioFiltersList();
            renderAudioFilterSettings(f);
        };
        list.appendChild(div);
    });

    if (!selectedAudioFilterId && filters.length > 0) {
        selectedAudioFilterId = filters[0].id;
        refreshAudioFiltersList();
        renderAudioFilterSettings(filters[0]);
    }
}

const addAudioFilterBtn = document.getElementById('addAudioFilterBtn');
const addAudioFilterMenu = document.getElementById('addAudioFilterMenu');

addAudioFilterBtn.onclick = (e) => {
    e.stopPropagation();
    addAudioFilterMenu.classList.toggle('active');
};

document.addEventListener('click', (e) => {
    if (!e.target.closest('#addAudioFilterBtn')) addAudioFilterMenu.classList.remove('active');
});

document.querySelectorAll('#addAudioFilterMenu .context-item').forEach(item => {
    item.onclick = () => {
        const filterType = item.dataset.filter;
        const newFilter = {
            id: Date.now(),
            type: filterType,
            name: filterType,
            settings: getDefaultSettingsForAudioFilter(filterType)
        };
        currentAudioFiltersSource.audioFilters.push(newFilter);
        selectedAudioFilterId = newFilter.id;
        refreshAudioFiltersList();
    };
});

document.getElementById('removeAudioFilterBtn').onclick = () => {
    if (selectedAudioFilterId && currentAudioFiltersSource) {
        currentAudioFiltersSource.audioFilters = currentAudioFiltersSource.audioFilters.filter(f => f.id !== selectedAudioFilterId);
        selectedAudioFilterId = null;
        refreshAudioFiltersList();
    }
};

document.getElementById('moveAudioFilterUpBtn').onclick = () => {
    if (!selectedAudioFilterId || !currentAudioFiltersSource) return;
    const filters = currentAudioFiltersSource.audioFilters;
    const idx = filters.findIndex(f => f.id === selectedAudioFilterId);
    if (idx > 0) {
        const temp = filters[idx];
        filters[idx] = filters[idx - 1];
        filters[idx - 1] = temp;
        refreshAudioFiltersList();
    }
};

document.getElementById('moveAudioFilterDownBtn').onclick = () => {
    if (!selectedAudioFilterId || !currentAudioFiltersSource) return;
    const filters = currentAudioFiltersSource.audioFilters;
    const idx = filters.findIndex(f => f.id === selectedAudioFilterId);
    if (idx < filters.length - 1 && idx > -1) {
        const temp = filters[idx];
        filters[idx] = filters[idx + 1];
        filters[idx + 1] = temp;
        refreshAudioFiltersList();
    }
};

function renderAudioFilterSettings(filter) {
    const container = document.getElementById('audioFilterSettingsContent');
    if (!filter) {
        container.innerHTML = '<div id="noFilterSelected" style="color: #888; text-align: center; margin-top: 100px;">Please select a filter to view its properties.</div>';
        return;
    }

    let html = `<div style="font-size: 18px; font-weight: bold; margin-bottom: 20px; color: #fff;">${filter.name}</div>`;
    
    const makeSlider = (label, key, min, max, val, unit='') => `
        <div class="prop-row" style="margin-bottom: 15px; align-items: center;">
            <label class="prop-label" style="width: 120px;">${label}</label>
            <div class="prop-input-container" style="flex-direction: row; gap: 10px; align-items: center;">
                <input type="range" class="obs-slider audio-filter-slider" data-key="${key}" min="${min}" max="${max}" step="0.1" value="${val}" style="flex: 1;">
                <input type="number" class="obs-input-small audio-filter-num" data-key="${key}" value="${val}" step="0.1"> ${unit}
            </div>
        </div>
    `;

    if (filter.type === 'Gain') {
        html += makeSlider('Gain', 'gain', -30, 30, filter.settings.gain, 'dB');
    } else if (filter.type === 'Compressor') {
        html += makeSlider('Ratio', 'ratio', 1, 32, filter.settings.ratio, ':1');
        html += makeSlider('Threshold', 'threshold', -60, 0, filter.settings.threshold, 'dB');
        html += makeSlider('Attack', 'attack', 1, 500, filter.settings.attack, 'ms');
        html += makeSlider('Release', 'release', 1, 1000, filter.settings.release, 'ms');
        html += makeSlider('Output Gain', 'outputGain', -32, 32, filter.settings.outputGain, 'dB');
    } else if (filter.type === 'Noise Gate') {
        html += makeSlider('Close Threshold', 'closeThreshold', -100, 0, filter.settings.closeThreshold, 'dB');
        html += makeSlider('Open Threshold', 'openThreshold', -100, 0, filter.settings.openThreshold, 'dB');
        html += makeSlider('Attack time', 'attack', 1, 50, filter.settings.attack, 'ms');
        html += makeSlider('Hold time', 'hold', 1, 1000, filter.settings.hold, 'ms');
        html += makeSlider('Release time', 'release', 1, 1000, filter.settings.release, 'ms');
    } else if (filter.type === 'Noise Suppression') {
        html += `
        <div class="prop-row" style="margin-bottom: 15px;">
            <label class="prop-label" style="width: 120px;">Method</label>
            <div class="prop-input-container">
                <select class="obs-select audio-filter-select" data-key="method">
                    <option value="speex" ${filter.settings.method === 'speex' ? 'selected' : ''}>Speex (low CPU usage, low quality)</option>
                    <option value="rnnoise" ${filter.settings.method === 'rnnoise' ? 'selected' : ''}>RNNoise (good quality, more CPU usage)</option>
                </select>
            </div>
        </div>
        `;
        if(filter.settings.method === 'speex') {
             html += makeSlider('Suppression Level', 'level', -60, 0, filter.settings.level, 'dB');
        }
    } else if (filter.type === 'Limiter') {
        html += makeSlider('Threshold', 'threshold', -60, 0, filter.settings.threshold, 'dB');
        html += makeSlider('Release', 'release', 1, 1000, filter.settings.release, 'ms');
    } else {
        html += `<div style="color: #bbb; margin-bottom: 10px;">Settings for ${filter.type} are standard parameters.</div>`;
        html += makeSlider('Amount', 'amount', 0, 100, filter.settings.amount || 50, '%');
    }

    container.innerHTML = html;

    container.querySelectorAll('.audio-filter-slider').forEach(slider => {
        slider.addEventListener('input', (e) => {
            const key = e.target.dataset.key;
            filter.settings[key] = parseFloat(e.target.value);
            container.querySelector(`.audio-filter-num[data-key="${key}"]`).value = e.target.value;
        });
    });
    container.querySelectorAll('.audio-filter-num').forEach(num => {
        num.addEventListener('input', (e) => {
            const key = e.target.dataset.key;
            filter.settings[key] = parseFloat(e.target.value);
            container.querySelector(`.audio-filter-slider[data-key="${key}"]`).value = e.target.value;
        });
    });
    container.querySelectorAll('.audio-filter-select').forEach(sel => {
        sel.addEventListener('change', (e) => {
            const key = e.target.dataset.key;
            filter.settings[key] = e.target.value;
            renderAudioFilterSettings(filter);
        });
    });
}

function getDefaultSettingsForAudioFilter(type) {
    switch(type) {
        case 'Gain': return { gain: 0 };
        case 'Compressor': return { ratio: 10, threshold: -18, attack: 2, release: 100, outputGain: 0 };
        case 'Noise Gate': return { closeThreshold: -32, openThreshold: -26, attack: 25, hold: 200, release: 150 };
        case 'Noise Suppression': return { method: 'rnnoise', level: -30 };
        case 'Limiter': return { threshold: -6, release: 60 };
        default: return { amount: 50 };
    }
}

document.getElementById('closeAudioFiltersBtn').addEventListener('click', () => audioFiltersModal.classList.remove('active'));
document.getElementById('audioFilterCloseBottomBtn').addEventListener('click', () => audioFiltersModal.classList.remove('active'));
document.getElementById('audioFilterDefaultsBtn').addEventListener('click', () => {
    if (selectedAudioFilterId && currentAudioFiltersSource) {
        const filter = currentAudioFiltersSource.audioFilters.find(f => f.id === selectedAudioFilterId);
        if (filter) {
            filter.settings = getDefaultSettingsForAudioFilter(filter.type);
            renderAudioFilterSettings(filter);
        }
    }
});


// --- 3. AUDIO DEVICE PROPERTIES MODAL LOGIC ---
const audioDevicePropertiesModal = document.getElementById('audioDevicePropertiesModal');
let currentAudioDeviceSource = null;

function openAudioDeviceProperties(src) {
    currentAudioDeviceSource = src;
    
    if (!src.deviceProps) {
        src.deviceProps = { device: 'default', useTimestamps: true };
    }

    document.getElementById('audioPropDeviceSelect').value = src.deviceProps.device;
    document.getElementById('audioPropUseTimestamps').checked = src.deviceProps.useTimestamps;
    
    openModalCenter('audioDevicePropertiesModal');
}

document.getElementById('closeAudioDevicePropertiesBtn').addEventListener('click', () => audioDevicePropertiesModal.classList.remove('active'));
document.getElementById('audioPropCancelBtn').addEventListener('click', () => audioDevicePropertiesModal.classList.remove('active'));

document.getElementById('audioPropOkBtn').addEventListener('click', () => {
    if (currentAudioDeviceSource) {
        currentAudioDeviceSource.deviceProps = {
            device: document.getElementById('audioPropDeviceSelect').value,
            useTimestamps: document.getElementById('audioPropUseTimestamps').checked
        };
    }
    audioDevicePropertiesModal.classList.remove('active');
});

// Re-render audio mixers globally initially to ensure triple dot hooks apply to pre-existing sources
audioMixerContainer.innerHTML = '';
scenes.forEach(s => {
    s.sources.forEach(src => {
        if (src.gainNode) renderMixerUI(src);
    });
});
// // =========================================================================
// =========================================================================
// =================== ADVANCED NLE PLUGIN (V69 - PLAYBACK ENGINE FIXED) ===
// =========================================================================

(function initAdvancedEditorPlugin() {
    try {
        // --- 0. THE MEDIA VAULT (GPU TRICK) ---
        let mediaVault = document.getElementById('nleMediaVault');
        if (!mediaVault) {
            mediaVault = document.createElement('div');
            mediaVault.id = 'nleMediaVault';
            mediaVault.style.position = 'fixed';
            mediaVault.style.top = '0px';
            mediaVault.style.left = '0px';
            mediaVault.style.width = '1920px';
            mediaVault.style.height = '1080px';
            mediaVault.style.opacity = '0.01'; 
            mediaVault.style.pointerEvents = 'none';
            mediaVault.style.zIndex = '-2147483648'; 
            mediaVault.style.overflow = 'hidden';
            document.body.appendChild(mediaVault);
        }

        // --- 1. UX: EDITOR NOTES & BROWSER WARNING MODAL ---
        let audioNoticeModal = document.getElementById('nleAudioNoticeModal');
        if (!audioNoticeModal) {
            const modalHTML = `
                <div id="nleAudioNoticeModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.85); z-index:2147483647; justify-content:center; align-items:center; font-family:sans-serif;">
                    <div style="background:#222; color:#fff; padding:30px; border-radius:8px; max-width:480px; text-align:center; border:1px solid #4daafc; box-shadow: 0 10px 40px rgba(0,0,0,0.7);">
                        <h2 style="margin-top:0; color:#4daafc; font-size: 22px; display:flex; align-items:center; justify-content:center; gap:10px;">
                            <i class="fas fa-info-circle"></i> Editor Notes
                        </h2>
                        
                        <div style="text-align: left;">
                            <p style="font-size:15px; line-height:1.6; color:#fff; margin-bottom:20px; padding: 0 5px;">
                                This basic editor allows you to arrange multiple video and image clips on a multitrack timeline. You can trim clips, layer them on top of one another, and spatially arrange or crop them in the preview canvas.
                            </p>

                            <p style="font-size:14px; line-height:1.6; color:#e74c3c; margin-bottom:12px; background: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 4px;">
                                <b>1. Audio is Muted:</b> To ensure smooth scrubbing, audio preview is disabled in the timeline. It will be fully synced in your final export.
                            </p>
                            
                            <p style="font-size:14px; line-height:1.6; color:#f39c12; margin-bottom:12px; background: rgba(243, 156, 18, 0.1); padding: 10px; border-radius: 4px;">
                                <b>2. Browser Compatibility:</b> For the best timeline performance, we strongly recommend <b>Google Chrome</b>. Firefox struggles with hardware video rendering and may flicker during playback, though you can safely use it to manage your project.
                            </p>

                            <p style="font-size:14px; line-height:1.6; color:#2ecc71; margin-bottom:25px; background: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 4px;">
                                <b>3. Invisible Downloader:</b> To download any source clip from your library, simply hold the <b>SHIFT key</b> and <b>Click</b> on its thumbnail!
                            </p>
                        </div>

                        <div style="margin-bottom:20px; display:flex; align-items:center; justify-content:center; gap:10px;">
                            <input type="checkbox" id="nleAudioNoticeHide" style="cursor:pointer; width:16px; height:16px;">
                            <label for="nleAudioNoticeHide" style="font-size:14px; cursor:pointer; color:#ccc;">Don't show this again this session</label>
                        </div>
                        <button id="nleAudioNoticeBtn" style="background:#4daafc; color:#fff; border:none; padding:12px 24px; border-radius:4px; cursor:pointer; font-weight:bold; font-size:16px; width:100%; transition: background 0.2s;">Okay, I understand</button>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            audioNoticeModal = document.getElementById('nleAudioNoticeModal');

            document.getElementById('nleAudioNoticeBtn').addEventListener('click', () => {
                if (document.getElementById('nleAudioNoticeHide').checked) {
                    sessionStorage.setItem('nleHideAudioNotice', 'true');
                }
                audioNoticeModal.style.display = 'none';
            });
        }

        // --- 2. ENGINE STATE & SETUP ---
        const advModal = document.getElementById('advancedEditorModal');
        const advCanvas = document.getElementById('advEditorPreviewCanvas');
        if (!advCanvas || !advModal) return; 
        
        const advCtx = advCanvas.getContext('2d', { alpha: false });
        const bufferCanvas = document.createElement('canvas');
        const bufferCtx = bufferCanvas.getContext('2d', { alpha: false });

        let project = { duration: 300, width: 1920, height: 1080, mediaPool: [], tracks: [{ id: 1, clips: [] }, { id: 0, clips: [] }] };
        let state = { playing: false, time: 0, scale: 20, selectedClip: null, dragAction: null, lastClickedPoolItem: null };

        const editorObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class' && advModal.classList.contains('active')) {
                    if (!sessionStorage.getItem('nleHideAudioNotice')) {
                        audioNoticeModal.style.display = 'flex';
                    }
                    updateTimelineWidth(); 
                }
            });
        });
        editorObserver.observe(advModal, { attributes: true });

        const closeBtn = document.getElementById('closeAdvEditorBtn');
        if (closeBtn) {
            const freshClose = closeBtn.cloneNode(true);
            closeBtn.parentNode.replaceChild(freshClose, closeBtn);
            freshClose.addEventListener('click', () => {
                advModal.classList.remove('active');
                pausePlayback();
            });
        }

        // --- 3. HARDENED PIXEL SCROLLBAR LOGIC ---
        const advTimelineWrapper = document.getElementById('advTimeline');
        if (advTimelineWrapper) {
            advTimelineWrapper.style.overflowX = 'auto';
            advTimelineWrapper.style.overflowY = 'hidden';
            advTimelineWrapper.style.position = 'relative';
        }

        function updateTimelineWidth() {
            let minWidth = advTimelineWrapper ? advTimelineWrapper.clientWidth : 800;
            const pxWidth = Math.max(minWidth, (project.duration * state.scale) + 200) + 'px';
            
            document.querySelectorAll('.nle-track-content').forEach(t => {
                t.style.width = pxWidth;
                t.style.position = 'relative'; 
                t.style.display = 'block'; 
                t.style.height = '46px'; 
                t.style.minHeight = '46px';
                t.style.boxSizing = 'border-box';
            });
            
            const header = document.querySelector('.nle-timeline-header');
            if (header) header.style.width = pxWidth;
        }

        // --- 4. THE GLOBAL CAPTURE-PHASE DOWNLOADER ---
        if (!window._nleCaptureListenerInstalled) {
            window.addEventListener('mousedown', (e) => {
                if (e.shiftKey) {
                    const targetThumb = e.target.closest('.video-thumbnail');
                    if (targetThumb) {
                        e.preventDefault();   
                        e.stopPropagation();  
                        
                        const mediaElement = targetThumb.querySelector('video, img');
                        if (mediaElement && mediaElement.src) {
                            const a = document.createElement('a');
                            a.href = mediaElement.src;
                            a.download = `media_${Date.now()}.webm`;
                            document.body.appendChild(a); 
                            a.click();
                            document.body.removeChild(a);
                            
                            const oldBorder = targetThumb.style.border;
                            targetThumb.style.border = '4px solid white';
                            setTimeout(() => { targetThumb.style.border = oldBorder; }, 200);
                        }
                    }
                }
            }, true); 
            window._nleCaptureListenerInstalled = true;
        }

        // --- 5. MEDIA HANDLING ---
        window.addVideoToLibrary = function(video) {
            const el = document.createElement('video');
            el.src = video.url; 
            el.muted = true; el.defaultMuted = true; el.setAttribute('muted', 'muted');
            el.controls = false; el.setAttribute('playsinline', ''); 
            el.style.width = '100%'; el.style.height = '100%'; el.style.position = 'absolute'; el.preload = 'auto';
            
            // CRITICAL FIX: Ensure canvas redraws perfectly when scrubbing finishes seeking
            el.addEventListener('seeked', () => {
                if (!state.playing) drawCanvas();
            });

            mediaVault.appendChild(el); 

            el.onloadedmetadata = () => {
                project.mediaPool.push({ id: 'pool_'+Date.now(), name: video.name || 'Recording', url: video.url, type: 'video', duration: el.duration, element: el, w: el.videoWidth, h: el.videoHeight });
                renderPool();
            };
        };

        window.addVideoToTimeline = function(video) {
            setTimeout(() => {
                const item = project.mediaPool.find(p => p.url === video.url);
                if (item) addClipToTrack(0, item, 0); 
            }, 500); 
        };

        function renderPool() {
            const grid = document.getElementById('advVideoLibrary');
            if(!grid) return;
            grid.innerHTML = '';

            project.mediaPool.forEach(item => {
                const div = document.createElement('div');
                div.className = 'video-thumbnail';
                div.draggable = true; 
                div.style.border = (state.lastClickedPoolItem?.id === item.id) ? '3px solid #2ecc71' : 'none';
                div.style.boxSizing = 'border-box';
                div.style.cursor = 'pointer';
                div.style.position = 'relative';

                div.innerHTML = `
                    <${item.type === 'video' ? 'video' : 'img'} src="${item.url}" style="width:100%; height:100%; object-fit:cover; pointer-events:none;"></${item.type === 'video' ? 'video' : 'img'}>
                    <div class="duration-badge">${Math.floor(item.duration)}s</div>
                `;

                div.addEventListener('click', (e) => {
                    if (e.shiftKey) return; 
                    state.lastClickedPoolItem = item;
                    renderPool(); 
                });

                div.addEventListener('dragstart', (e) => {
                    if (e.shiftKey) { e.preventDefault(); return; }
                    e.dataTransfer.setData('text/plain', item.id);
                });

                grid.appendChild(div);
            });
        }

        // --- 6. UI INJECTIONS (ZOOM & CROP) ---
        let zoomSlider = document.getElementById('advZoomSlider');
        if (!zoomSlider) {
            const toolbar = document.querySelector('.nle-timeline-toolbar');
            if (toolbar) {
                toolbar.insertAdjacentHTML('afterbegin', `
                    <div style="display:flex; align-items:center; margin-right:15px;">
                        <i id="zoomIconFlag" class="fas fa-search-plus" style="color:#dfdfdf; margin-right:6px;" title="Zoom Timeline"></i>
                        <input type="range" id="advZoomSlider" min="5" max="100" value="20" class="obs-slider" style="width: 100px;">
                    </div>
                `);
                zoomSlider = document.getElementById('advZoomSlider');
            }
        }

        if (zoomSlider) {
            const freshSlider = zoomSlider.cloneNode(true);
            zoomSlider.parentNode.replaceChild(freshSlider, zoomSlider);
            freshSlider.addEventListener('input', (e) => {
                state.scale = parseInt(e.target.value) || 20;
                updateTimelineWidth();
                updateClipsUI(); 
                updateTime();
            });
        }

        let cropOverlay = document.getElementById('advCropOverlay');
        if (!cropOverlay) {
            const wrapper = advCanvas.parentNode;
            wrapper.style.position = 'relative';
            wrapper.insertAdjacentHTML('beforeend', `
                <div id="advCropOverlay" style="display:none; position:absolute; border:2px dashed #4daafc; background:rgba(77,170,252,0.1); z-index:100;">
                    <div class="crop-handle tl" style="position:absolute; width:12px; height:12px; background:#4daafc; top:-6px; left:-6px; cursor:nwse-resize;"></div>
                    <div class="crop-handle tr" style="position:absolute; width:12px; height:12px; background:#4daafc; top:-6px; right:-6px; cursor:nesw-resize;"></div>
                    <div class="crop-handle bl" style="position:absolute; width:12px; height:12px; background:#4daafc; bottom:-6px; left:-6px; cursor:nesw-resize;"></div>
                    <div class="crop-handle br" style="position:absolute; width:12px; height:12px; background:#4daafc; bottom:-6px; right:-6px; cursor:nwse-resize;"></div>
                </div>
            `);
            cropOverlay = document.getElementById('advCropOverlay');
        }

        const toggleCropBtn = document.getElementById('advToggleCropBtn');
        let isCropActive = false;
        
        if (toggleCropBtn) {
            const freshToggleBtn = toggleCropBtn.cloneNode(true);
            toggleCropBtn.parentNode.replaceChild(freshToggleBtn, toggleCropBtn);
            freshToggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (!state.selectedClip) return;
                isCropActive = !isCropActive;
                if (isCropActive) {
                    cropOverlay.style.display = 'block';
                    cropOverlay.style.width = '80%'; cropOverlay.style.height = '80%';
                    cropOverlay.style.left = '10%'; cropOverlay.style.top = '10%';
                    freshToggleBtn.style.backgroundColor = '#1e50a0'; 
                    freshToggleBtn.innerHTML = '<i class="fas fa-check"></i> Apply Crop';
                } else {
                    cropOverlay.style.display = 'none';
                    freshToggleBtn.style.backgroundColor = '#4caf50';
                    freshToggleBtn.innerHTML = '<i class="fas fa-check-double"></i> Cropped!';
                    const canvasRect = advCanvas.getBoundingClientRect();
                    const overlayRect = cropOverlay.getBoundingClientRect();
                    state.selectedClip.crop = {
                        x: Math.max(0, (overlayRect.left - canvasRect.left) / canvasRect.width),
                        y: Math.max(0, (overlayRect.top - canvasRect.top) / canvasRect.height),
                        w: Math.min(1, overlayRect.width / canvasRect.width),
                        h: Math.min(1, overlayRect.height / canvasRect.height)
                    };
                    drawCanvas();
                    setTimeout(() => {
                        freshToggleBtn.style.backgroundColor = '';
                        freshToggleBtn.innerHTML = '<i class="fas fa-crop"></i> Toggle Crop Tool';
                    }, 1500);
                }
            });
        }

        let cropDragMode = null, startX, startY, startRect;
        cropOverlay.addEventListener('mousedown', (e) => {
            startX = e.clientX; startY = e.clientY;
            startRect = { left: cropOverlay.offsetLeft, top: cropOverlay.offsetTop, width: cropOverlay.offsetWidth, height: cropOverlay.offsetHeight };
            if (e.target.classList.contains('tl')) cropDragMode = 'tl';
            else if (e.target.classList.contains('tr')) cropDragMode = 'tr';
            else if (e.target.classList.contains('bl')) cropDragMode = 'bl';
            else if (e.target.classList.contains('br')) cropDragMode = 'br';
            else cropDragMode = 'move';
            e.stopPropagation();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!cropDragMode) return;
            const dx = e.clientX - startX, dy = e.clientY - startY;
            if (cropDragMode === 'move') {
                cropOverlay.style.left = (startRect.left + dx) + 'px'; cropOverlay.style.top = (startRect.top + dy) + 'px';
            } else if (cropDragMode === 'br') {
                cropOverlay.style.width = Math.max(20, startRect.width + dx) + 'px'; cropOverlay.style.height = Math.max(20, startRect.height + dy) + 'px';
            } else if (cropDragMode === 'tr') {
                cropOverlay.style.width = Math.max(20, startRect.width + dx) + 'px'; cropOverlay.style.height = Math.max(20, startRect.height - dy) + 'px'; cropOverlay.style.top = (startRect.top + dy) + 'px';
            } else if (cropDragMode === 'bl') {
                cropOverlay.style.width = Math.max(20, startRect.width - dx) + 'px'; cropOverlay.style.left = (startRect.left + dx) + 'px'; cropOverlay.style.height = Math.max(20, startRect.height + dy) + 'px';
            } else if (cropDragMode === 'tl') {
                cropOverlay.style.width = Math.max(20, startRect.width - dx) + 'px'; cropOverlay.style.height = Math.max(20, startRect.height - dy) + 'px'; cropOverlay.style.left = (startRect.left + dx) + 'px'; cropOverlay.style.top = (startRect.top + dy) + 'px';
            }
        });
        document.addEventListener('mouseup', () => cropDragMode = null);

        // --- 7. TIMELINE CORE ---
        let advInsertBtn = document.getElementById('advInsertBtn');
        let advInput = document.getElementById('advEditorMediaInput');
        if (advInsertBtn && advInput) {
            const freshInsert = advInsertBtn.cloneNode(true);
            const freshInput = advInput.cloneNode(true);
            advInsertBtn.parentNode.replaceChild(freshInsert, advInsertBtn);
            advInput.parentNode.replaceChild(freshInput, advInput);
            
            freshInsert.addEventListener('click', () => freshInput.click());
            freshInput.addEventListener('change', (e) => {
                Array.from(e.target.files).forEach(file => {
                    const url = URL.createObjectURL(file);
                    const isVideo = file.type.startsWith('video');
                    const el = document.createElement(isVideo ? 'video' : 'img');
                    el.src = url;
                    
                    if (isVideo) {
                        el.muted = true; el.defaultMuted = true; el.setAttribute('muted', 'muted');
                        el.controls = false; el.setAttribute('playsinline', ''); 
                        el.style.width = '100%'; el.style.height = '100%'; el.style.position = 'absolute'; el.preload = 'auto';
                        
                        el.addEventListener('seeked', () => { if (!state.playing) drawCanvas(); });
                        
                        mediaVault.appendChild(el);
                        el.onloadedmetadata = () => { project.mediaPool.push({ id: 'pool_'+Date.now(), name: file.name, url, type: 'video', duration: el.duration, element: el, w: el.videoWidth, h: el.videoHeight }); renderPool(); };
                    } else {
                        mediaVault.appendChild(el);
                        el.onload = () => { project.mediaPool.push({ id: 'pool_'+Date.now(), name: file.name, url, type: 'image', duration: 5, element: el, w: el.width, h: el.height }); renderPool(); };
                    }
                });
            });
        }

        let advTimeline = document.getElementById('advTimeline');
        if (advTimeline) {
            const freshTimeline = advTimeline.cloneNode(true);
            advTimeline.parentNode.replaceChild(freshTimeline, advTimeline);
            advTimeline = freshTimeline;
            
            advTimeline.addEventListener('mousedown', e => {
                if (e.target.closest('.nle-clip') || e.target.closest('.nle-track-header')) return;
                const update = evt => { 
                    pausePlayback(); 
                    state.time = Math.max(0, (evt.clientX - document.getElementById('advTracksWrapper').getBoundingClientRect().left + advTimeline.scrollLeft - 60) / state.scale); 
                    project.tracks.forEach(t => t.clips.forEach(c => {
                        if (c.type === 'video' && c.element) {
                            if (state.time >= c.start && state.time <= c.start + (c.trimEnd - c.trimStart)) {
                                // This causes the video to seek. The 'seeked' listener we added earlier guarantees the canvas redraws smoothly without black flashes.
                                c.element.currentTime = c.trimStart + (state.time - c.start);
                            }
                        }
                    }));
                    updateTime(); 
                };
                update(e); 
                document.addEventListener('mousemove', update);
                document.addEventListener('mouseup', () => document.removeEventListener('mousemove', update), {once: true});
            });

            advTimeline.addEventListener('dragover', e => e.preventDefault());
            advTimeline.addEventListener('drop', e => {
                e.preventDefault();
                const item = project.mediaPool.find(p => p.id === e.dataTransfer.getData('text/plain'));
                const targetTrack = e.target.closest('.nle-track');
                
                if (item && targetTrack) {
                    const trackId = parseInt(targetTrack.dataset.track);
                    const trackContent = targetTrack.querySelector('.nle-track-content');
                    if (trackContent) {
                        const dropX = e.clientX - trackContent.getBoundingClientRect().left;
                        addClipToTrack(isNaN(trackId) ? 0 : trackId, item, Math.max(0, dropX / state.scale));
                    }
                }
            });
        }

        function addClipToTrack(trackId, item, start) {
            const el = document.createElement(item.type === 'video' ? 'video' : 'img');
            el.src = item.url;
            if (item.type === 'video') {
                el.muted = true; el.defaultMuted = true; el.setAttribute('muted', 'muted');
                el.controls = false; el.setAttribute('playsinline', '');
                el.style.width = '100%'; el.style.height = '100%'; el.style.position = 'absolute'; el.preload = 'auto';
                el.addEventListener('seeked', () => { if (!state.playing) drawCanvas(); });
            }
            mediaVault.appendChild(el); 

            project.tracks.find(t => t.id === trackId).clips.push({ 
                id: 'clip_'+Date.now(), poolId: item.id, name: item.name, type: item.type, trackId, 
                start, duration: item.duration, trimStart: 0, trimEnd: item.duration, element: el, 
                x: 0, y: 0, scale: 1, opacity: 1, crop: null, _isActive: false 
            });
            
            if (start + item.duration > project.duration) {
                project.duration = Math.ceil(start + item.duration + 10);
            }
            updateTimelineWidth();
            renderTimeline(); 
            drawCanvas();
        }

        function renderTimeline() {
            project.tracks.forEach(t => {
                const row = document.querySelector(`.nle-track[data-track="${t.id}"] .nle-track-content`);
                if (!row) return;
                row.innerHTML = '';
                t.clips.forEach(clip => {
                    const div = document.createElement('div');
                    div.id = clip.id; 
                    div.className = `nle-clip ${state.selectedClip?.id === clip.id ? 'selected-clip' : ''}`;
                    div.textContent = clip.name;
                    
                    div.style.left = (clip.start * state.scale) + 'px';
                    div.style.width = Math.max(10, (clip.trimEnd - clip.trimStart) * state.scale) + 'px';
                    div.style.position = 'absolute'; 
                    div.style.top = '4px'; 
                    div.style.height = '38px'; 
                    div.style.boxSizing = 'border-box';
                    
                    div.innerHTML += `<div class="nle-trim-handle left"></div><div class="nle-trim-handle right"></div>`;
                    
                    div.addEventListener('mousedown', e => {
                        if (e.target.classList.contains('nle-trim-handle')) return;
                        selectClip(clip); initDrag(e, clip, 'move');
                    });
                    div.querySelector('.left').addEventListener('mousedown', e => { selectClip(clip); initDrag(e, clip, 'trim-left'); });
                    div.querySelector('.right').addEventListener('mousedown', e => { selectClip(clip); initDrag(e, clip, 'trim-right'); });
                    row.appendChild(div);
                });
            });
        }

        function updateClipsUI() {
            project.tracks.forEach(t => {
                t.clips.forEach(clip => {
                    const el = document.getElementById(clip.id);
                    if (el) {
                        el.style.left = (clip.start * state.scale) + 'px';
                        el.style.width = Math.max(10, (clip.trimEnd - clip.trimStart) * state.scale) + 'px';
                    }
                });
            });
        }

        let clipDragStartX, dragStartClipX, dragStartTrim;
        function initDrag(e, clip, action) {
            e.stopPropagation(); state.dragAction = action;
            clipDragStartX = e.clientX; dragStartClipX = clip.start;
            dragStartTrim = action === 'trim-left' ? clip.trimStart : clip.trimEnd;
            document.onmousemove = handleDrag;
            document.onmouseup = () => { document.onmousemove = document.onmouseup = null; state.dragAction = null; };
        }
        
        function handleDrag(e) {
            const dt = (e.clientX - clipDragStartX) / state.scale;
            const c = state.selectedClip;
            if (state.dragAction === 'move') c.start = Math.max(0, dragStartClipX + dt);
            else if (state.dragAction === 'trim-left') { const nt = Math.max(0, Math.min(c.trimEnd - 0.5, dragStartTrim + dt)); c.trimStart = nt; c.start = dragStartClipX + (nt - dragStartTrim); }
            else if (state.dragAction === 'trim-right') c.trimEnd = Math.max(c.trimStart + 0.5, Math.min(c.duration, dragStartTrim + dt));
            
            if (c.start + c.duration > project.duration) {
                project.duration = Math.ceil(c.start + c.duration + 10);
                updateTimelineWidth();
            }
            updateClipsUI(); 
            drawCanvas();
        }

        function selectClip(clip) {
            state.selectedClip = clip; 
            document.querySelectorAll('.nle-clip').forEach(el => el.classList.remove('selected-clip'));
            if (clip) {
                const el = document.getElementById(clip.id);
                if (el) el.classList.add('selected-clip');
            }
            
            const props = document.getElementById('advClipProps');
            const noClip = document.getElementById('advNoClipSelected');
            
            if (clip) {
                if (props) props.style.display = 'block'; 
                if (noClip) noClip.style.display = 'none';
                
                const scaleIn = document.getElementById('advPropScale');
                const opacIn = document.getElementById('advPropOpacity');
                if (scaleIn) scaleIn.value = clip.scale * 100;
                if (opacIn) opacIn.value = clip.opacity * 100;
                
                if(isCropActive) document.getElementById('advToggleCropBtn').click(); 
            } else { 
                if (props) props.style.display = 'none'; 
                if (noClip) noClip.style.display = 'block'; 
                if(isCropActive) document.getElementById('advToggleCropBtn').click();
            }
        }

        ['advPropScale', 'advPropOpacity'].forEach(id => {
            let el = document.getElementById(id);
            if (el) {
                const freshEl = el.cloneNode(true);
                el.parentNode.replaceChild(freshEl, el);
                freshEl.addEventListener('input', e => {
                    if (state.selectedClip) { 
                        const val = parseInt(e.target.value) / 100;
                        if (id === 'advPropScale') state.selectedClip.scale = val;
                        else if (id === 'advPropOpacity') state.selectedClip.opacity = val;
                        drawCanvas(); 
                    }
                });
            }
        });

        // --- 8. CANVAS RENDERER ---
        let isDraggingCanvas = false;
        advCanvas.addEventListener('mousedown', e => { if(state.selectedClip) isDraggingCanvas = true; });
        advCanvas.addEventListener('mousemove', e => {
            if(!isDraggingCanvas || !state.selectedClip) return;
            const rect = advCanvas.getBoundingClientRect();
            state.selectedClip.x += e.movementX * (advCanvas.width / rect.width);
            state.selectedClip.y += e.movementY * (advCanvas.height / rect.height);
            drawCanvas();
        });
        advCanvas.addEventListener('mouseup', () => isDraggingCanvas = false);
        advCanvas.addEventListener('mouseleave', () => isDraggingCanvas = false);

        function drawCanvas() {
            if (bufferCanvas.width !== project.width || bufferCanvas.height !== project.height) {
                bufferCanvas.width = project.width;
                bufferCanvas.height = project.height;
            }

            bufferCtx.fillStyle = '#000'; 
            bufferCtx.fillRect(0, 0, project.width, project.height);
            
            [...project.tracks].sort((a,b)=>a.id-b.id).forEach(t => t.clips.forEach(c => {
                const clipEnd = c.start + (c.trimEnd - c.trimStart);
                const isPhysicallyActive = state.time >= c.start && state.time <= clipEnd;

                if (isPhysicallyActive) {
                    bufferCtx.save(); bufferCtx.globalAlpha = c.opacity;
                    let w = project.width, h = project.height;
                    const p = project.mediaPool.find(x => x.id === c.poolId);
                    if (p) { const asp = p.w / p.h; if (w/h > asp) w = h * asp; else h = w / asp; }
                    bufferCtx.translate(w/2 + c.x, h/2 + c.y); bufferCtx.scale(c.scale, c.scale);
                    
                    if (c.element) {
                        try {
                            if (c.type === 'video') {
                                if (c.element.readyState >= 2) {
                                    if (c.crop) {
                                        const cx = c.crop.x * c.element.videoWidth, cy = c.crop.y * c.element.videoHeight;
                                        const cw = c.crop.w * c.element.videoWidth, ch = c.crop.h * c.element.videoHeight;
                                        bufferCtx.drawImage(c.element, cx, cy, cw, ch, -w/2 + (c.crop.x*w), -h/2 + (c.crop.y*h), c.crop.w*w, c.crop.h*h);
                                    } else {
                                        bufferCtx.drawImage(c.element, -w/2, -h/2, w, h);
                                    }
                                }
                            } else {
                                if (c.crop) {
                                    const cx = c.crop.x * p.w, cy = c.crop.y * p.h, cw = c.crop.w * p.w, ch = c.crop.h * p.h;
                                    bufferCtx.drawImage(c.element, cx, cy, cw, ch, -w/2 + (c.crop.x*w), -h/2 + (c.crop.y*h), c.crop.w*w, c.crop.h*h);
                                } else { bufferCtx.drawImage(c.element, -w/2, -h/2, w, h); }
                            }
                            
                            if (state.selectedClip?.id === c.id && !state.playing && !isCropActive) {
                                bufferCtx.strokeStyle = '#4daafc'; bufferCtx.lineWidth = 4/c.scale; 
                                if (c.crop) bufferCtx.strokeRect(-w/2 + (c.crop.x*w), -h/2 + (c.crop.y*h), c.crop.w*w, c.crop.h*h);
                                else bufferCtx.strokeRect(-w/2, -h/2, w, h);
                            }
                        } catch(e){}
                    }
                    bufferCtx.restore();
                }
            }));

            advCtx.drawImage(bufferCanvas, 0, 0, advCanvas.width, advCanvas.height);
        }

        // --- 9. NATIVE PLAYBACK LOOP (REBUILT & FIXED) ---
        let advPlayBtn = document.getElementById('advEditorPlayBtn');
        if (advPlayBtn) {
            const freshPlay = advPlayBtn.cloneNode(true);
            advPlayBtn.parentNode.replaceChild(freshPlay, advPlayBtn);
            advPlayBtn = freshPlay;
        }
        
        let playbackLoopId;
        let lastTime = 0;
        
        function play() {
            state.playing = true; advPlayBtn.innerHTML = '<i class="fas fa-pause"></i>';
            lastTime = performance.now();
            
            // Initial sync on play button press
            project.tracks.forEach(t => t.clips.forEach(c => {
                if (c.type === 'video' && c.element) {
                    const clipEnd = c.start + (c.trimEnd - c.trimStart);
                    if (state.time >= c.start && state.time < clipEnd) {
                        c._isActive = true;
                        c.element.currentTime = c.trimStart + (state.time - c.start);
                        c.element.play().catch(()=>{});
                    }
                }
            }));
            
            function loop() {
                if (!state.playing) return;
                
                const now = performance.now();
                state.time += (now - lastTime) / 1000; 
                lastTime = now;
                
                if (state.time > project.duration) {
                    state.time = 0;
                    project.tracks.forEach(t => t.clips.forEach(c => {
                        if (c.type === 'video' && c.element) { c._isActive = false; c.element.pause(); }
                    }));
                }
                
                project.tracks.forEach(t => t.clips.forEach(c => {
                    if (c.type === 'video' && c.element) {
                        const clipEnd = c.start + (c.trimEnd - c.trimStart);
                        const isActive = state.time >= c.start && state.time < clipEnd;
                        
                        // CRITICAL FIX: Removed continuous drift correction. We now trust the browser to play smoothly.
                        if (isActive && !c._isActive) {
                            c._isActive = true;
                            c.element.currentTime = c.trimStart + (state.time - c.start);
                            c.element.play().catch(()=>{});
                        } else if (!isActive && c._isActive) {
                            c._isActive = false;
                            c.element.pause();
                        }
                    }
                }));

                updateTime(); drawCanvas(); 
                playbackLoopId = requestAnimationFrame(loop);
            }
            playbackLoopId = requestAnimationFrame(loop);
        }
        
        function pausePlayback() {
            state.playing = false; advPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
            cancelAnimationFrame(playbackLoopId);
            project.tracks.forEach(t => t.clips.forEach(c => {
                if (c.type === 'video' && c.element) { c._isActive = false; c.element.pause(); }
            }));
            drawCanvas();
        }

        if (advPlayBtn) {
            advPlayBtn.addEventListener('click', () => state.playing ? pausePlayback() : play());
        }
        
        function updateTime() {
            const head = document.getElementById('advPlayhead');
            if (head) head.style.left = (60 + state.time * state.scale) + 'px';
            const disp = document.getElementById('advTimeDisplay');
            if (disp) disp.textContent = `${Math.floor(state.time/60).toString().padStart(2,'0')}:${Math.floor(state.time%60).toString().padStart(2,'0')}`;
        }

        // Delete & Split
        let advDeleteBtn = document.getElementById('advDeleteBtn');
        if (advDeleteBtn) {
            const freshDel = advDeleteBtn.cloneNode(true);
            advDeleteBtn.parentNode.replaceChild(freshDel, advDeleteBtn);
            freshDel.addEventListener('click', () => {
                if(state.selectedClip) project.tracks.forEach(t => t.clips = t.clips.filter(c => c.id !== state.selectedClip.id));
                selectClip(null); renderTimeline(); drawCanvas();
            });
        }

        let advSplitBtn = document.getElementById('advSplitBtn');
        if (advSplitBtn) {
            const freshSplit = advSplitBtn.cloneNode(true);
            advSplitBtn.parentNode.replaceChild(freshSplit, advSplitBtn);
            freshSplit.addEventListener('click', () => {
                const c = state.selectedClip;
                if (c && state.time > c.start && state.time < c.start + (c.trimEnd - c.trimStart)) {
                    pausePlayback();
                    const cut = c.trimStart + (state.time - c.start);
                    const el = document.createElement(c.type === 'video' ? 'video' : 'img');
                    el.src = project.mediaPool.find(p => p.id === c.poolId).url; 
                    
                    if(c.type==='video') {
                        el.muted = true; el.defaultMuted = true; el.setAttribute('muted', 'muted');
                        el.controls = false; el.setAttribute('playsinline', ''); 
                        el.style.width = '100%'; el.style.height = '100%'; el.style.position = 'absolute'; el.preload = 'auto';
                    }
                    if (mediaVault) mediaVault.appendChild(el); 

                    project.tracks.find(t=>t.id===c.trackId).clips.push({ 
                        ...c, id: 'clip_'+Date.now(), start: state.time, trimStart: cut, element: el, _isActive: false
                    });
                    c.trimEnd = cut; updateTimelineWidth(); renderTimeline(); drawCanvas();
                }
            });
        }

        // --- 10. REAL-TIME EXPORT ROUTINE ---
        let advExportBtn = document.getElementById('advExportBtn');
        if (advExportBtn) {
            const freshExport = advExportBtn.cloneNode(true);
            advExportBtn.parentNode.replaceChild(freshExport, advExportBtn);
            advExportBtn = freshExport;
        }

        let isRendering = false;
        let renderLoopId;
        
        if (advExportBtn) {
            advExportBtn.addEventListener('click', async () => {
                if (project.tracks.every(t => t.clips.length === 0)) return;
                pausePlayback();
                
                let maxTime = 0; 
                project.tracks.forEach(t => t.clips.forEach(c => {
                    const clipEndTime = c.start + (c.trimEnd - c.trimStart);
                    if (clipEndTime > maxTime) maxTime = clipEndTime;
                }));
                
                if (maxTime === 0) return; 

                isRendering = true;
                const renderOverlay = document.getElementById('nleRenderOverlay');
                const progressText = document.getElementById('nleRenderProgressText');
                const progressBar = document.getElementById('nleRenderBarFill');
                const cancelBtn = document.getElementById('nleRenderCancelBtn');
                
                renderOverlay.style.display = 'flex';
                progressText.innerText = '0%';
                progressBar.style.width = '0%';
                
                cancelBtn.onclick = () => { isRendering = false; };
                
                state.time = 0;
                
                // Pre-seek to start and pause to allow buffers to fill
                project.tracks.forEach(t => t.clips.forEach(c => {
                    if (c.type === 'video' && c.element) {
                        c._isActive = false;
                        c.element.pause();
                        c.element.currentTime = c.trimStart;
                    }
                }));

                await new Promise(r => setTimeout(r, 800)); 

                const stream = advCanvas.captureStream(30);
                
                const recorder = new MediaRecorder(stream, { 
                    mimeType: 'video/webm;codecs=vp8',
                    videoBitsPerSecond: 8000000 
                });
                
                const chunks = []; 
                recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
                
                const p = new Promise(res => recorder.onstop = () => {
                    if (chunks.length > 0 && isRendering !== null) { 
                        const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(chunks, { type: 'video/webm' }));
                        a.download = `Render_${Date.now()}.webm`; a.click(); 
                    }
                    res();
                });

                recorder.start();
                let lastRenderTime = performance.now();

                function renderLoop() {
                    if (!isRendering) { recorder.stop(); cleanupRender(); return; }
                    
                    const now = performance.now();
                    state.time += (now - lastRenderTime) / 1000;
                    lastRenderTime = now;

                    const percent = Math.min(100, Math.floor((state.time / maxTime) * 100));
                    progressText.innerText = percent + '%';
                    progressBar.style.width = percent + '%';

                    if (state.time >= maxTime) {
                        recorder.stop(); cleanupRender(); return;
                    }

                    project.tracks.forEach(t => t.clips.forEach(c => {
                        if (c.type === 'video' && c.element) {
                            const clipEnd = c.start + (c.trimEnd - c.trimStart);
                            const isActive = state.time >= c.start && state.time < clipEnd;
                            
                            if (isActive) {
                                if (c.element.paused || !c._isActive) {
                                    c._isActive = true;
                                    c.element.currentTime = c.trimStart + (state.time - c.start);
                                    c.element.play().catch(()=>{});
                                }
                            } else if (!isActive && c._isActive) {
                                c._isActive = false;
                                c.element.pause();
                            }
                        }
                    }));

                    drawCanvas(); 
                    
                    renderLoopId = requestAnimationFrame(renderLoop);
                }

                renderLoopId = requestAnimationFrame(renderLoop);
                
                function cleanupRender() {
                    isRendering = null; 
                    cancelAnimationFrame(renderLoopId);
                    project.tracks.forEach(t => t.clips.forEach(c => { if (c.element) c.element.pause(); }));
                    renderOverlay.style.display = 'none';
                    state.time = 0; updateTime(); drawCanvas();
                }

                await p;
            });
        }

        updateTimelineWidth();
        console.log("✅ V69: Playback restored. Infinite buffer loops terminated.");
    } catch (error) { console.error("❌ NLE Plugin Error.", error); }
})();
// =========================================================================
// =================== OBS STUDIO MODE ADDON PATCH =========================
// =========================================================================

(function initStudioModeAddon() {
    try {
        // --- 1. Element Binding ---
        const toggleBtn = document.getElementById('studioModeToggleBtn');
        const previewHeader = document.getElementById('previewPaneHeader');
        const programPane = document.getElementById('programPane');
        const studioControls = document.getElementById('studioControls');
        const programWrapper = document.getElementById('programWrapper');
        const programPlaceholder = document.getElementById('programPlaceholder');
        
        // Grab the active renderer (liveRenderCanvas is flattened, obsCanvas is fallback)
        const cleanLiveFeedCanvas = document.getElementById('liveRenderCanvas') || document.getElementById('obsCanvas'); 
        const programCanvas = document.getElementById('programCanvas'); 
        
        if (!cleanLiveFeedCanvas || !programCanvas || !toggleBtn) {
            console.warn("Studio Mode Addon: Required canvases or buttons not found.");
            return;
        }

        // Fix the "Black Void" camouflage issue
        if (programWrapper) {
            programWrapper.style.backgroundColor = '#1d1f26';
        }
        
        const programCtx = programCanvas.getContext('2d', { alpha: false });
        
        // --- 2. The Display List Proxy Engine ---
        // This intercepts the main engine's draw calls so we can reconstruct a "Live" independent Program feed.
        let currentFrameCommands = [];
        let liveProgramCommands = []; // Saved state of the Program feed
        
        const targetCtx = cleanLiveFeedCanvas.getContext('2d');
        
        // Hook clear methods to identify the start of a new frame
        const origClearRect = targetCtx.clearRect;
        targetCtx.clearRect = function(x, y, w, h) {
            if (x === 0 && y === 0 && w >= this.canvas.width && h >= this.canvas.height) {
                currentFrameCommands = []; // Wipe the list for the new frame
            }
            currentFrameCommands.push({ type: 'clearRect', args: [x, y, w, h], transform: this.getTransform() });
            return origClearRect.apply(this, [x, y, w, h]);
        };

        const origFillRect = targetCtx.fillRect;
        targetCtx.fillRect = function(x, y, w, h) {
            if (x === 0 && y === 0 && w >= this.canvas.width && h >= this.canvas.height) {
                currentFrameCommands = []; // Some engines use fillRect to clear
            }
            currentFrameCommands.push({ 
                type: 'fillRect', args: [x, y, w, h], transform: this.getTransform(), 
                fillStyle: this.fillStyle, alpha: this.globalAlpha, composite: this.globalCompositeOperation, filter: this.filter 
            });
            return origFillRect.apply(this, [x, y, w, h]);
        };

        // Hook all core drawing methods
        const methods = ['drawImage', 'fillText', 'strokeRect', 'strokeText', 'beginPath', 'moveTo', 'lineTo', 'rect', 'arc', 'fill', 'stroke', 'clip'];
        methods.forEach(method => {
            if (!targetCtx[method]) return;
            const orig = targetCtx[method];
            targetCtx[method] = function(...args) {
                currentFrameCommands.push({
                    type: method,
                    args: args,
                    transform: this.getTransform(),
                    alpha: this.globalAlpha,
                    filter: this.filter,
                    composite: this.globalCompositeOperation,
                    fillStyle: this.fillStyle,
                    strokeStyle: this.strokeStyle,
                    font: this.font,
                    textAlign: this.textAlign,
                    textBaseline: this.textBaseline
                });
                return orig.apply(this, args);
            };
        });

        // The Mini-Renderer: Executes the intercepted display list on the Program Canvas
        function renderDisplayList(ctx, commands) {
            ctx.save();
            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);

            if (commands.length === 0) {
                // Default Waiting Text
                ctx.fillStyle = '#666';
                ctx.font = '48px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('Waiting for Transition...', ctx.canvas.width / 2, ctx.canvas.height / 2);
            }

            commands.forEach(cmd => {
                ctx.setTransform(cmd.transform);
                if(cmd.alpha !== undefined) ctx.globalAlpha = cmd.alpha;
                if(cmd.filter !== undefined) ctx.filter = cmd.filter;
                if(cmd.composite !== undefined) ctx.globalCompositeOperation = cmd.composite;
                if(cmd.fillStyle !== undefined) ctx.fillStyle = cmd.fillStyle;
                if(cmd.strokeStyle !== undefined) ctx.strokeStyle = cmd.strokeStyle;
                if(cmd.font !== undefined) ctx.font = cmd.font;
                if(cmd.textAlign !== undefined) ctx.textAlign = cmd.textAlign;
                if(cmd.textBaseline !== undefined) ctx.textBaseline = cmd.textBaseline;
                
                if (ctx[cmd.type]) {
                    try { 
                        // Because cmd.args retains the active HTMLVideoElement reference, 
                        // calling drawImage here grabs the newest, live frame of the video automatically!
                        ctx[cmd.type](...cmd.args); 
                    } catch(e) {} // Failsafe for detached media elements
                }
            });
            ctx.restore();
        }
        
        // --- 3. Engine State ---
        let isStudioMode = false;
        let tBarValue = 0; 
        let isTransitioning = false;
        let transitionRafId = null;

        const tBarSlider = document.getElementById('studioTBar');
        const cutBtn = document.getElementById('studioCutBtn');
        const fadeBtn = document.getElementById('studioFadeBtn');
        const transitionBtn = document.getElementById('studioTransitionBtn');
        const durationInput = document.getElementById('studioDurationInput');

        // --- 4. Toggle Studio Mode Logic ---
        toggleBtn.addEventListener('click', () => {
            isStudioMode = !isStudioMode;
            if (isStudioMode) {
                toggleBtn.style.backgroundColor = '#1e50a0';
                toggleBtn.style.color = '#fff';
                previewHeader.style.display = 'block';
                programPane.style.display = 'flex';
                studioControls.style.display = 'flex';
                if (programPlaceholder) programPlaceholder.style.display = 'none';

                // Initial setup: Program matches Preview perfectly
                liveProgramCommands = [...currentFrameCommands];

                tBarValue = 0;
                if(tBarSlider) tBarSlider.value = 0;
                
                startProgramRenderLoop();
            } else {
                toggleBtn.style.backgroundColor = '';
                toggleBtn.style.color = '';
                previewHeader.style.display = 'none';
                programPane.style.display = 'none';
                studioControls.style.display = 'none';
                
                stopProgramRenderLoop();
            }
        });

        // --- 5. Dual-Render Engine ---
        let programLoopId;
        function startProgramRenderLoop() {
            function loop() {
                if (!isStudioMode) return;
                
                // Step A: Continuously execute the frozen display list to keep media playing safely
                programCtx.globalAlpha = 1.0;
                renderDisplayList(programCtx, liveProgramCommands);
                
                // Step B: Blend the live Preview over top during transitions
                if (tBarValue > 0) {
                    programCtx.globalAlpha = tBarValue;
                    programCtx.drawImage(cleanLiveFeedCanvas, 0, 0);
                }
                
                programCtx.globalAlpha = 1.0;
                programLoopId = requestAnimationFrame(loop);
            }
            loop();
        }

        function stopProgramRenderLoop() {
            cancelAnimationFrame(programLoopId);
        }

        // --- 6. Transition Actions ---
        function performCut() {
            if (!isStudioMode || isTransitioning) return;
            // Lock in the new state by copying the current display list
            liveProgramCommands = [...currentFrameCommands];
            tBarValue = 0;
            if(tBarSlider) tBarSlider.value = 0;
        }

        function performFade() {
            if (!isStudioMode || isTransitioning) return;
            
            const duration = parseInt(durationInput ? durationInput.value : 300) || 300;
            const startTime = performance.now();
            const startTBar = tBarValue; 
            isTransitioning = true;
            
            function animateFade(now) {
                const elapsed = now - startTime;
                let progress = elapsed / duration;
                
                if (progress >= 1.0) {
                    progress = 1.0;
                    isTransitioning = false;
                    
                    // Finalize the transition
                    liveProgramCommands = [...currentFrameCommands];
                    
                    tBarValue = 0; 
                    if(tBarSlider) tBarSlider.value = 0;
                } else {
                    tBarValue = startTBar + ( (1.0 - startTBar) * progress );
                    if(tBarSlider) tBarSlider.value = tBarValue * 100;
                    transitionRafId = requestAnimationFrame(animateFade);
                }
            }
            transitionRafId = requestAnimationFrame(animateFade);
        }

        // --- 7. Event Listeners ---
        if (cutBtn) cutBtn.addEventListener('click', performCut);
        if (transitionBtn) transitionBtn.addEventListener('click', performFade);
        if (fadeBtn) fadeBtn.addEventListener('click', performFade);

        if (tBarSlider) {
            tBarSlider.addEventListener('input', (e) => {
                if (isTransitioning) {
                    cancelAnimationFrame(transitionRafId);
                    isTransitioning = false;
                }
                tBarValue = parseInt(e.target.value) / 100;
            });
            
            tBarSlider.addEventListener('change', (e) => {
                if (parseInt(e.target.value) === 100) {
                    liveProgramCommands = [...currentFrameCommands];
                    tBarValue = 0; 
                    tBarSlider.value = 0;
                }
            });
        }

        console.log("✅ Studio Mode Addon Successfully Initialized (Display List Proxy Active).");
    } catch (e) {
        console.error("❌ Studio Mode Addon Error:", e);
    }
})();
// =========================================================================
// ================= ADVANCED NLE & BUG FIX PLUGIN (SAFE) ==================
// =========================================================================

(function initAdvancedEditorPlugin() {
    try {
        // --- 1. SAFE MEDIA PROPERTIES BUTTON FIX ---
        const oldMediaBtn = document.getElementById('mediaPropertiesBtn');
        if (oldMediaBtn) {
            const safeMediaBtn = oldMediaBtn.cloneNode(true);
            oldMediaBtn.parentNode.replaceChild(safeMediaBtn, oldMediaBtn);
            
            safeMediaBtn.addEventListener('click', () => {
                if (typeof selectedSource !== 'undefined' && selectedSource && (selectedSource.type === 'media' || selectedSource.type === 'vlc')) {
                    if (typeof openMediaProperties === 'function') openMediaProperties(selectedSource);
                }
            });
        }

        // --- 2. ENGINE STATE & SETUP ---
        const advModal = document.getElementById('advancedEditorModal');
        const advCanvas = document.getElementById('advEditorPreviewCanvas');
        if (!advCanvas) return; // Wait for HTML to be added
        
        const advCtx = advCanvas.getContext('2d', { alpha: false });
        
        let project = { duration: 300, width: 1920, height: 1080, mediaPool: [], tracks: [{ id: 1, clips: [] }, { id: 0, clips: [] }] };
        let state = { playing: false, time: 0, scale: 20, selectedClip: null, dragAction: null };

        // HIJACK OLD BUTTON: Automatically remap "Recordings & Editor" button to the new NLE
        const oldOpenBtn = document.getElementById('openEditorBtn');
        if (oldOpenBtn) {
            const newOpenBtn = oldOpenBtn.cloneNode(true);
            oldOpenBtn.parentNode.replaceChild(newOpenBtn, oldOpenBtn);
            newOpenBtn.addEventListener('click', () => {
                if (typeof closeAllMenus === 'function') closeAllMenus();
                advModal.classList.add('active');
                const win = advModal.querySelector('.obs-window');
                if (win) { win.style.transform = 'translate(-50%, -50%)'; win.style.left = '50%'; win.style.top = '50%'; }
            });
        }

        document.getElementById('closeAdvEditorBtn').addEventListener('click', () => {
            advModal.classList.remove('active');
            pausePlayback();
        });

        // HIJACK RECORDING FUNCTION: Pipe original recordings directly into the New NLE
        window.addVideoToLibrary = function(video) {
            const el = document.createElement('video');
            el.src = video.url;
            el.muted = true;
            el.onloadedmetadata = () => {
                project.mediaPool.push({ id: 'pool_'+Date.now(), name: video.name || 'Recording', url: video.url, type: 'video', duration: el.duration, element: el, w: el.videoWidth, h: el.videoHeight });
                renderPool();
            };
        };

        window.addVideoToTimeline = function(video) {
            setTimeout(() => {
                const item = project.mediaPool.find(p => p.url === video.url);
                if (item) addClipToTrack(0, item, 0); 
            }, 500); 
        };

        // --- 3. LOGIC CORE ---
        document.getElementById('advInsertBtn').addEventListener('click', () => document.getElementById('advEditorMediaInput').click());
        document.getElementById('advEditorMediaInput').addEventListener('change', (e) => {
            Array.from(e.target.files).forEach(file => {
                const url = URL.createObjectURL(file);
                const isVideo = file.type.startsWith('video');
                const el = document.createElement(isVideo ? 'video' : 'img');
                el.src = url;
                if (isVideo) {
                    el.muted = true;
                    el.onloadedmetadata = () => { project.mediaPool.push({ id: 'pool_'+Date.now(), name: file.name, url, type: 'video', duration: el.duration, element: el, w: el.videoWidth, h: el.videoHeight }); renderPool(); };
                } else {
                    el.onload = () => { project.mediaPool.push({ id: 'pool_'+Date.now(), name: file.name, url, type: 'image', duration: 5, element: el, w: el.width, h: el.height }); renderPool(); };
                }
            });
        });

        function renderPool() {
            const grid = document.getElementById('advVideoLibrary');
            grid.innerHTML = '';
            project.mediaPool.forEach(item => {
                const div = document.createElement('div');
                div.className = 'video-thumbnail';
                div.draggable = true;
                div.innerHTML = `<${item.type === 'video' ? 'video' : 'img'} src="${item.url}"></${item.type === 'video' ? 'video' : 'img'}><div class="duration-badge">${Math.floor(item.duration)}s</div>`;
                div.addEventListener('dragstart', (e) => e.dataTransfer.setData('text/plain', item.id));
                grid.appendChild(div);
            });
        }

        document.querySelectorAll('.nle-track-content').forEach(track => {
            track.addEventListener('dragover', e => e.preventDefault());
            track.addEventListener('drop', e => {
                e.preventDefault();
                const item = project.mediaPool.find(p => p.id === e.dataTransfer.getData('text/plain'));
                if (item) addClipToTrack(parseInt(e.target.closest('.nle-track').dataset.track), item, (e.clientX - track.getBoundingClientRect().left + document.getElementById('advTimeline').scrollLeft) / state.scale);
            });
        });

        function addClipToTrack(trackId, item, start) {
            const el = document.createElement(item.type === 'video' ? 'video' : 'img');
            el.src = item.url;
            if (item.type === 'video') el.muted = true;
            project.tracks.find(t => t.id === trackId).clips.push({ id: 'clip_'+Date.now(), poolId: item.id, name: item.name, type: item.type, trackId, start, duration: item.duration, trimStart: 0, trimEnd: item.duration, element: el, x: 0, y: 0, scale: 1, opacity: 1 });
            renderTimeline();
            updatePreview();
        }

        function renderTimeline() {
            project.tracks.forEach(t => {
                const row = document.querySelector(`.nle-track[data-track="${t.id}"] .nle-track-content`);
                row.innerHTML = '';
                t.clips.forEach(clip => {
                    const div = document.createElement('div');
                    div.className = `nle-clip ${state.selectedClip?.id === clip.id ? 'selected-clip' : ''}`;
                    div.textContent = clip.name;
                    div.style.left = (clip.start * state.scale) + 'px';
                    div.style.width = Math.max(10, (clip.trimEnd - clip.trimStart) * state.scale) + 'px';
                    
                    div.innerHTML += `<div class="nle-trim-handle left"></div><div class="nle-trim-handle right"></div>`;
                    
                    div.addEventListener('mousedown', e => {
                        if (e.target.classList.contains('nle-trim-handle')) return;
                        selectClip(clip); initDrag(e, clip, 'move');
                    });
                    div.querySelector('.left').addEventListener('mousedown', e => { selectClip(clip); initDrag(e, clip, 'trim-left'); });
                    div.querySelector('.right').addEventListener('mousedown', e => { selectClip(clip); initDrag(e, clip, 'trim-right'); });
                    row.appendChild(div);
                });
            });
        }

        let dragStartX, dragStartClipX, dragStartTrim;
        function initDrag(e, clip, action) {
            e.stopPropagation(); state.dragAction = action;
            dragStartX = e.clientX; dragStartClipX = clip.start;
            dragStartTrim = action === 'trim-left' ? clip.trimStart : clip.trimEnd;
            document.onmousemove = handleDrag;
            document.onmouseup = () => { document.onmousemove = document.onmouseup = null; state.dragAction = null; };
        }
        
        function handleDrag(e) {
            const dt = (e.clientX - dragStartX) / state.scale;
            const c = state.selectedClip;
            if (state.dragAction === 'move') c.start = Math.max(0, dragStartClipX + dt);
            else if (state.dragAction === 'trim-left') { const nt = Math.max(0, Math.min(c.trimEnd - 0.5, dragStartTrim + dt)); c.trimStart = nt; c.start = dragStartClipX + (nt - dragStartTrim); }
            else if (state.dragAction === 'trim-right') c.trimEnd = Math.max(c.trimStart + 0.5, Math.min(c.duration, dragStartTrim + dt));
            renderTimeline(); updatePreview();
        }

        function selectClip(clip) {
            state.selectedClip = clip; renderTimeline();
            const props = document.getElementById('advClipProps');
            const noClip = document.getElementById('advNoClipSelected');
            if (clip) {
                props.style.display = 'block'; noClip.style.display = 'none';
                document.getElementById('advPropScale').value = clip.scale * 100;
                document.getElementById('advPropOpacity').value = clip.opacity * 100;
            } else { props.style.display = 'none'; noClip.style.display = 'block'; }
        }

        ['advPropScale', 'advPropOpacity'].forEach(id => {
            document.getElementById(id).addEventListener('input', e => {
                if (state.selectedClip) {
                    state.selectedClip[id === 'advPropScale' ? 'scale' : 'opacity'] = parseInt(e.target.value) / 100;
                    updatePreview();
                }
            });
        });

        let isDraggingCanvas = false;
        advCanvas.addEventListener('mousedown', e => { if(state.selectedClip) isDraggingCanvas = true; });
        advCanvas.addEventListener('mousemove', e => {
            if(!isDraggingCanvas || !state.selectedClip) return;
            const rect = advCanvas.getBoundingClientRect();
            state.selectedClip.x += e.movementX * (advCanvas.width / rect.width);
            state.selectedClip.y += e.movementY * (advCanvas.height / rect.height);
            updatePreview();
        });
        advCanvas.addEventListener('mouseup', () => isDraggingCanvas = false);
        advCanvas.addEventListener('mouseleave', () => isDraggingCanvas = false);

        function updatePreview() {
            advCtx.fillStyle = '#000'; advCtx.fillRect(0, 0, project.width, project.height);
            [...project.tracks].sort((a,b)=>a.id-b.id).forEach(t => t.clips.forEach(c => {
                if (state.time >= c.start && state.time <= c.start + (c.trimEnd - c.trimStart)) {
                    const pt = c.trimStart + (state.time - c.start);
                    advCtx.save(); advCtx.globalAlpha = c.opacity;
                    let w = project.width, h = project.height;
                    const p = project.mediaPool.find(x => x.id === c.poolId);
                    if (p) { const asp = p.w / p.h; if (w/h > asp) w = h * asp; else h = w / asp; }
                    
                    advCtx.translate(w/2 + c.x, h/2 + c.y); advCtx.scale(c.scale, c.scale);
                    if (c.element) {
                        try {
                            if (c.type === 'video' && Math.abs(c.element.currentTime - pt) > 0.1) c.element.currentTime = pt;
                            advCtx.drawImage(c.element, -w/2, -h/2, w, h);
                            if (state.selectedClip?.id === c.id && !state.playing) {
                                advCtx.strokeStyle = '#4daafc'; advCtx.lineWidth = 4/c.scale; advCtx.strokeRect(-w/2, -h/2, w, h);
                            }
                        } catch(e){}
                    }
                    advCtx.restore();
                }
            }));
        }

        function play() {
            state.playing = true; document.getElementById('advEditorPlayBtn').innerHTML = '<i class="fas fa-pause"></i>';
            project.tracks.forEach(t => t.clips.forEach(c => { if(c.type==='video'&&c.element) c.element.play().catch(()=>{}); }));
            let lt = performance.now();
            function loop() {
                if (!state.playing) return;
                state.time += (performance.now() - lt) / 1000; lt = performance.now();
                if(state.time > project.duration) state.time = 0;
                updateTime(); updatePreview(); requestAnimationFrame(loop);
            }
            requestAnimationFrame(loop);
        }
        function pausePlayback() {
            state.playing = false; document.getElementById('advEditorPlayBtn').innerHTML = '<i class="fas fa-play"></i>';
            project.tracks.forEach(t => t.clips.forEach(c => { if(c.type==='video'&&c.element) c.element.pause(); }));
        }

        document.getElementById('advEditorPlayBtn').addEventListener('click', () => state.playing ? pausePlayback() : play());
        
        function updateTime() {
            document.getElementById('advPlayhead').style.left = (60 + state.time * state.scale) + 'px';
            document.getElementById('advTimeDisplay').textContent = `${Math.floor(state.time/60).toString().padStart(2,'0')}:${Math.floor(state.time%60).toString().padStart(2,'0')}`;
        }

        document.getElementById('advTimeline').addEventListener('mousedown', e => {
            if (e.target.closest('.nle-clip') || e.target.closest('.nle-track-header')) return;
            const update = evt => { state.time = Math.max(0, (evt.clientX - document.getElementById('advTracksWrapper').getBoundingClientRect().left + document.getElementById('advTimeline').scrollLeft - 60) / state.scale); pausePlayback(); updateTime(); updatePreview(); };
            update(e); document.addEventListener('mousemove', update);
            document.addEventListener('mouseup', () => document.removeEventListener('mousemove', update), {once: true});
        });

        document.getElementById('advDeleteBtn').addEventListener('click', () => {
            if(state.selectedClip) project.tracks.forEach(t => t.clips = t.clips.filter(c => c.id !== state.selectedClip.id));
            selectClip(null); updatePreview();
        });

        document.getElementById('advSplitBtn').addEventListener('click', () => {
            const c = state.selectedClip;
            if (c && state.time > c.start && state.time < c.start + (c.trimEnd - c.trimStart)) {
                const cut = c.trimStart + (state.time - c.start);
                const el = document.createElement(c.type === 'video' ? 'video' : 'img');
                el.src = project.mediaPool.find(p => p.id === c.poolId).url; if(c.type==='video') el.muted = true;
                project.tracks.find(t=>t.id===c.trackId).clips.push({ ...c, id: 'clip_'+Date.now(), start: state.time, trimStart: cut, element: el });
                c.trimEnd = cut; renderTimeline(); updatePreview();
            }
        });

        document.getElementById('advExportBtn').addEventListener('click', async () => {
            if (project.tracks.every(t => t.clips.length === 0)) return;
            pausePlayback();
            const btn = document.getElementById('advExportBtn'); btn.disabled = true; btn.innerHTML = 'Rendering...';
            
            let maxTime = 0;
            project.tracks.forEach(t => t.clips.forEach(c => maxTime = Math.max(maxTime, c.start + (c.trimEnd - c.trimStart))));
            
            const stream = advCanvas.captureStream(30);
            const recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8' });
            const chunks = []; recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
            
            const p = new Promise(res => recorder.onstop = () => {
                const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(chunks, { type: 'video/webm' }));
                a.download = `Render_${Date.now()}.webm`; a.click(); res();
            });

            recorder.start();
            let curFrame = 0, totFrames = Math.floor(maxTime * 30);
            
            function step() {
                if (curFrame > totFrames) { recorder.stop(); return; }
                state.time = curFrame / 30; updateTime(); updatePreview(); curFrame++;
                requestAnimationFrame(() => setTimeout(step, 10));
            }
            step(); await p;
            btn.disabled = false; btn.innerHTML = '<i class="fas fa-file-export"></i> Render Video';
            state.time = 0; updateTime(); updatePreview();
        });

        console.log("✅ Advanced NLE Plugin safely initialized.");
    } catch (error) {
        console.error("❌ Critical Error initializing NLE Plugin.", error);
    }
})();
/* ========================================================================================= 
   OBS WEB - SPLASH SCREEN ADD-ON PATCH (WEBM VERSION)
========================================================================================= */

(function initSplashScreen() {
    // 1. Create the Splash Screen DOM Elements dynamically
    const splash = document.createElement('div');
    splash.id = 'obs-splash-screen';
    Object.assign(splash.style, {
        position: 'fixed',
        top: '0', left: '0', 
        width: '100%', height: '100%',
        // Using a radial gradient to create a vignette effect, making the center stand out
        background: 'radial-gradient(circle, #2a2d36 0%, #0a0a0c 100%)', 
        zIndex: '9999999', // Ensure it sits on top of absolutely everything
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        transition: 'opacity 0.4s ease-out'
    });

    // 2. Add the WebM Video
    const video = document.createElement('video');
    video.src = 'https://saw.floydcraft.co.uk/Obs2-Basic.webm'; // Updated to your custom WebM
    video.autoplay = true;
    video.loop = true;
    video.muted = true; // Required by modern browsers for autoplay
    video.playsInline = true;
    
    // Styling for the video to make it pop
    video.style.maxWidth = '550px';
    video.style.width = '90%'; // Responsive fallback for smaller screens
    video.style.marginBottom = '40px'; 
    video.style.borderRadius = '12px'; 
    video.style.boxShadow = '0 25px 60px rgba(0,0,0,0.9)'; 

    // 3. Add the Progress Bar Container 
    const barContainer = document.createElement('div');
    Object.assign(barContainer.style, {
        width: '480px',  
        maxWidth: '85%', 
        height: '10px',  
        backgroundColor: '#0a0a0c',
        border: '1px solid #3c404d',
        borderRadius: '5px',
        overflow: 'hidden',
        boxShadow: '0 5px 15px rgba(0,0,0,0.7)' 
    });

    // 4. Add the Fill Bar 
    const bar = document.createElement('div');
    Object.assign(bar.style, {
        width: '0%', height: '100%',
        backgroundColor: '#1e50a0', // OBS Blue
        boxShadow: '0 0 15px rgba(30, 80, 160, 0.9)' // Neon glow effect
    });

    barContainer.appendChild(bar);
    splash.appendChild(video); // Append the video element instead of an image
    splash.appendChild(barContainer);
    document.body.appendChild(splash);

    // 5. Authentic "Stuttering" Animation Logic
    const duration = 2900; // Exact 2.9 seconds requirement
    const startTime = performance.now();
    let nextStutterTime = startTime;

    function animateSplash() {
        const now = performance.now();
        const elapsed = now - startTime;

        // Finish sequence
        if (elapsed >= duration) {
            bar.style.width = '100%';
            
            // Hold for a split second to show 100%, then fade out
            setTimeout(() => {
                splash.style.opacity = '0';
                setTimeout(() => {
                    splash.remove();
                    // Cleanup the video resource properly to free memory
                    video.pause();
                    video.removeAttribute('src'); 
                    video.load();
                }, 400); 
            }, 150);
            return;
        }

        // Stutter Trigger
        if (now >= nextStutterTime) {
            // Calculate true linear progress
            let baseProgress = (elapsed / duration) * 100;
            
            // Mock software chunk load (randomly overshoot or lag, capped at 98%)
            let stutterProgress = Math.min(baseProgress + (Math.random() * 15 - 5), 98);
            
            // Instantly snap the width to simulate a hard software load stutter
            bar.style.width = Math.max(0, stutterProgress) + '%';
            
            // Randomize the next freeze duration (between 50ms and 350ms freeze)
            nextStutterTime = now + Math.random() * 300 + 50;
        }

        requestAnimationFrame(animateSplash);
    }

    // Start the loading animation immediately
    requestAnimationFrame(animateSplash);
})();
// =========================================================================
// ================== OBS WEBAPP - FINAL TOUCHES ADDON =====================
// =========================================================================

function initOBSFinalTouches() {
    try {
        const primaryColor = '#1e50a0';
        const bgDark = '#1d1f26';
        const bgPanel = '#272a33';
        const borderCol = '#3c404d';

        // --- 1. MOBILE & NARROW SCREEN SHIELD ---
        const mobileShieldHTML = `
            <div id="mobileShield" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: ${bgDark}; z-index: 999999; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 20px; color: #dfdfdf; font-family: sans-serif;">
                <i class="fas fa-desktop" style="font-size: 64px; color: ${primaryColor}; margin-bottom: 20px;"></i>
                <h2 style="margin-bottom: 15px;">Bigger Display Required</h2>
                <p style="color: #999; max-width: 400px; line-height: 1.5;">OBS WebApp is a complex interface that requires a wider screen. Please maximize / stretch your window or open this app on a desktop computer.</p>
            </div>
            <style>
                @media screen and (max-width: 730px) { #mobileShield { display: flex !important; } }
            </style>
        `;
        document.body.insertAdjacentHTML('beforeend', mobileShieldHTML);
        // --- 4. CUSTOM TOOLTIPS ---
        const tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: absolute; display: none; background: #111; color: #fff; padding: 5px 8px;
            border-radius: 4px; font-size: 11px; z-index: 999999; pointer-events: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5); border: 1px solid ${borderCol}; white-space: nowrap;
        `;
        document.body.appendChild(tooltip);

        // Convert native titles to custom tooltips
        function bindTooltips() {
            document.querySelectorAll('[title]').forEach(el => {
                const titleText = el.getAttribute('title');
                if (!titleText) return;
                
                el.removeAttribute('title'); // Kill native tooltip
                el.dataset.customTooltip = titleText;

                el.addEventListener('mouseenter', (e) => {
                    tooltip.textContent = titleText;
                    tooltip.style.display = 'block';
                });
                
                el.addEventListener('mousemove', (e) => {
                    // Position slightly below and right of cursor
                    tooltip.style.left = (e.pageX + 10) + 'px';
                    tooltip.style.top = (e.pageY + 15) + 'px';
                });

                el.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
                el.addEventListener('mousedown', () => { tooltip.style.display = 'none'; }); // Hide on click
            });
        }
        
        // Bind initially and re-bind if UI updates
        setTimeout(bindTooltips, 500);


        // --- 5. NATIVE RIGHT-CLICK CONTEXT MENU ---
        const ctxMenuHTML = `
            <div id="obsContextMenu" style="display: none; position: absolute; background-color: ${bgPanel}; border: 1px solid ${borderCol}; border-radius: 4px; box-shadow: 0 5px 15px rgba(0,0,0,0.6); z-index: 100000; padding: 5px 0; min-width: 160px; font-family: 'Segoe UI', sans-serif;">
                <div class="ctx-item" data-action="New..." style="padding: 6px 15px; cursor: pointer; color: #dfdfdf; font-size: 13px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-plus" style="color: #888;"></i> Add New Scene</div>
                <div style="height: 1px; background: ${borderCol}; margin: 5px 0;"></div>
                <div class="ctx-item" data-action="Rename..." style="padding: 6px 15px; cursor: pointer; color: #dfdfdf; font-size: 13px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-edit" style="color: #888;"></i> Rename</div>
                <div class="ctx-item" data-action="Duplicate..." style="padding: 6px 15px; cursor: pointer; color: #dfdfdf; font-size: 13px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-copy" style="color: #888;"></i> Duplicate</div>
                <div style="height: 1px; background: ${borderCol}; margin: 5px 0;"></div>
                <div class="ctx-item" data-action="Remove" style="padding: 6px 15px; cursor: pointer; color: #ff4a4a; font-size: 13px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-trash" style="color: #ff4a4a;"></i> Remove</div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', ctxMenuHTML);
        
        const ctxMenu = document.getElementById('obsContextMenu');

        // Add hover styles dynamically
        const ctxItems = ctxMenu.querySelectorAll('.ctx-item');
        ctxItems.forEach(item => {
            item.addEventListener('mouseenter', () => item.style.backgroundColor = primaryColor);
            item.addEventListener('mouseleave', () => item.style.backgroundColor = 'transparent');
            
            // Map context clicks to the Top Menu logic we already built
            item.addEventListener('click', (e) => {
                const action = item.getAttribute('data-action');
                ctxMenu.style.display = 'none';
                
                // Find and click the matching menu item in the top nav secretly
                const navRows = document.querySelectorAll('.dropdown-row .menu-text');
                for (let i = 0; i < navRows.length; i++) {
                    if (navRows[i].textContent.trim() === action) {
                        navRows[i].parentElement.click();
                        break;
                    }
                }
            });
        });

        // Trigger right-click menu
        document.addEventListener('contextmenu', (e) => {
            // Only hijack right-click if clicking within the app bounds (docks, scenes, sources, preview)
            // Ignore standard inputs to allow default text copy/paste
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                
                // Keep menu within screen bounds
                let x = e.pageX;
                let y = e.pageY;
                ctxMenu.style.display = 'block';
                
                if (x + ctxMenu.offsetWidth > window.innerWidth) x = window.innerWidth - ctxMenu.offsetWidth;
                if (y + ctxMenu.offsetHeight > window.innerHeight) y = window.innerHeight - ctxMenu.offsetHeight;
                
                ctxMenu.style.left = x + 'px';
                ctxMenu.style.top = y + 'px';
            }
        });

        // Hide on normal click anywhere
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#obsContextMenu')) {
                ctxMenu.style.display = 'none';
            }
        });

        console.log("✅ Final Touch Addon Loaded: Auto-save, Context Menus, Tooltips, and Protection active.");
    } catch (e) {
        console.error("❌ Final Touch Addon Error:", e);
    }
}

// Run after everything else has settled
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(initOBSFinalTouches, 500));
} else {
    setTimeout(initOBSFinalTouches, 500);
}
// =========================================================================
// =================== MASSIVE SETTINGS & STREAMING ENGINE =================
// =========================================================================

(function initAdvancedSettingsAndStreaming() {
    try {
        // --- 1. Settings Modal Navigation ---
        const tabs = document.querySelectorAll('.settings-tab');
        const sections = document.querySelectorAll('.settings-section');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all
                tabs.forEach(t => t.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active'));
                
                // Set active to clicked
                tab.classList.add('active');
                const targetId = tab.dataset.target;
                const targetSection = document.getElementById(targetId);
                if (targetSection) targetSection.classList.add('active');
            });
        });

        // --- 2. Video Settings Binding (Canvas Resolution Mapping) ---
        const videoBaseRes = document.getElementById('videoBaseRes');
        
        // This bridges the new UI inputs to the physical canvas properties
        function applyVideoSettings() {
            if (videoBaseRes) {
                const res = videoBaseRes.value.split('x');
                const w = parseInt(res[0]);
                const h = parseInt(res[1]);
                
                const obsCanvas = document.getElementById('obsCanvas');
                const obsCanvasTop = document.getElementById('obsCanvasTop');
                const liveRenderCanvas = document.getElementById('liveRenderCanvas');
                
                if (obsCanvas) { obsCanvas.width = w; obsCanvas.height = h; }
                if (obsCanvasTop) { obsCanvasTop.width = w; obsCanvasTop.height = h; }
                if (liveRenderCanvas) { liveRenderCanvas.width = w; liveRenderCanvas.height = h; }
            }
        }

        // --- 3. Buttons (Apply, OK, Cancel) ---
        const settingsModal = document.getElementById('settingsModal');
        const applyBtn = document.getElementById('settingsApplyBtn');
        const okBtn = document.getElementById('settingsOkBtn');
        const cancelBtn = document.getElementById('settingsCancelBtn');
        const closeTopBtn = document.getElementById('closeSettingsBtn');

        function closeSettings() {
            if (settingsModal) settingsModal.classList.remove('active');
        }

        if (applyBtn) applyBtn.addEventListener('click', applyVideoSettings);
        if (okBtn) {
            okBtn.addEventListener('click', () => {
                applyVideoSettings();
                closeSettings();
            });
        }
        if (cancelBtn) cancelBtn.addEventListener('click', closeSettings);
        
        // Overwrite existing close button to ensure it uses the new logic
        if (closeTopBtn) {
            const freshClose = closeTopBtn.cloneNode(true);
            closeTopBtn.parentNode.replaceChild(freshClose, closeTopBtn);
            freshClose.addEventListener('click', closeSettings);
        }

        // --- 4. THE MOCK STREAMING ENGINE ---
        // This fully mocks the connection phase, visual UI updates, and bitrate generation.
        const mockStreamBtn = document.getElementById('mockStreamBtn');
        const mockStopStreamBtn = document.getElementById('mockStopStreamBtn');
        const streamStatusUI = document.getElementById('streamingTime');
        const statusBar = document.getElementById('statusBar');
        const statStreamStatus = document.getElementById('statStreamStatus');
        const statStreamData = document.getElementById('statStreamData');
        const statStreamBitrate = document.getElementById('statStreamBitrate');
        
        let isStreaming = false;
        let streamStartTime = 0;
        let streamInterval = null;
        let totalStreamBytes = 0;

        function formatStreamTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }

        if (mockStreamBtn && mockStopStreamBtn) {
            mockStreamBtn.addEventListener('click', () => {
                // 1. Fetch target from the Settings Stream Panel
                const serviceDropdown = document.getElementById('streamServiceDropdown');
                const serviceName = serviceDropdown ? serviceDropdown.value : "Custom Server";
                const streamKeyInput = document.getElementById('streamKeyInput');
                
                if (streamKeyInput && streamKeyInput.value === "") {
                    if (typeof showCustomAlert === 'function') {
                        showCustomAlert("Please enter a valid Stream Key in Settings -> Stream.");
                    } else {
                        alert("Please enter a Stream Key in Settings.");
                    }
                    return;
                }

                // 2. Mock Connection Phase
                mockStreamBtn.disabled = true;
                mockStreamBtn.textContent = "Connecting...";
                statusBar.textContent = `Connecting to ${serviceName}...`;
                statusBar.style.color = '#f39c12'; // Amber

                setTimeout(() => {
                    // 3. Connection Established
                    isStreaming = true;
                    streamStartTime = Date.now();
                    totalStreamBytes = 0;
                    
                    mockStreamBtn.classList.add('hidden');
                    mockStreamBtn.disabled = false;
                    mockStreamBtn.textContent = "Start Streaming";
                    
                    mockStopStreamBtn.classList.remove('hidden');
                    
                    streamStatusUI.style.display = 'inline-block';
                    statusBar.textContent = `Streaming to ${serviceName}`;
                    statusBar.style.color = '#2ecc71'; // Green
                    
                    if(statStreamStatus) statStreamStatus.textContent = 'Active';

                    // 4. Fire the Network Telemetry Loop
                    streamInterval = setInterval(() => {
                        const elapsedSecs = (Date.now() - streamStartTime) / 1000;
                        streamStatusUI.innerHTML = `<i class="fas fa-square" style="color:#e74c3c;"></i> LIVE: ${formatStreamTime(elapsedSecs)}`;
                        
                        // Mock slightly fluctuating Bitrate (e.g. 5800 - 6200 kbps)
                        const currentKbps = 5800 + Math.floor(Math.random() * 400);
                        
                        // Add to total data (Bytes = Kbps * 1024 / 8)
                        totalStreamBytes += (currentKbps * 1024 / 8);
                        const totalMiB = totalStreamBytes / (1024 * 1024);

                        if (statStreamData) statStreamData.textContent = totalMiB.toFixed(1) + ' MiB';
                        if (statStreamBitrate) statStreamBitrate.textContent = currentKbps + ' kb/s';
                        
                        // Pulse the green square on the bottom left for UI activity
                        const sq = streamStatusUI.querySelector('i');
                        if (sq) sq.style.opacity = (Math.floor(elapsedSecs) % 2 === 0) ? '1' : '0.5';

                    }, 1000);

                }, 1500); // 1.5 seconds artificial network handshake delay
            });

            mockStopStreamBtn.addEventListener('click', () => {
                // 1. Mock Disconnection
                mockStopStreamBtn.disabled = true;
                mockStopStreamBtn.textContent = "Stopping...";
                statusBar.textContent = "Disconnecting...";
                statusBar.style.color = '#f39c12';

                setTimeout(() => {
                    // 2. Fully Stopped
                    isStreaming = false;
                    clearInterval(streamInterval);
                    
                    mockStopStreamBtn.classList.add('hidden');
                    mockStopStreamBtn.disabled = false;
                    mockStopStreamBtn.textContent = "Stop Streaming";
                    
                    mockStreamBtn.classList.remove('hidden');
                    
                    streamStatusUI.style.display = 'none';
                    statusBar.textContent = "Ready";
                    statusBar.style.color = '#a0a0a0'; // Grey

                    if(statStreamStatus) statStreamStatus.textContent = 'Inactive';
                    if(statStreamBitrate) statStreamBitrate.textContent = '0 kb/s';

                }, 800); // 0.8s artificial teardown delay
            });
        }

        console.log("✅ Massive Settings Menu and Mock Stream Engine successfully injected.");
    } catch (e) {
        console.error("❌ Addon Injection Error:", e);
    }
})();
// =========================================================================
// ================= OBS WEBAPP - MASTER ADDON SCRIPT ======================
// =========================================================================

function initOBSMasterAddon() {
    try {
        const topNav = document.getElementById('topNav');
        if (!topNav) return;

        // --- 0. HISTORY ENGINE (UNDO/REDO) ---
        let historyStack = [];
        let historyIndex = -1;
        const MAX_HISTORY = 30;

        function saveHistoryState() {
            try {
                if (typeof scenes === 'undefined' || !scenes) return;
                const stateSnapshot = JSON.stringify(scenes);
                if (historyIndex >= 0 && historyStack[historyIndex] === stateSnapshot) return;
                if (historyIndex < historyStack.length - 1) { historyStack = historyStack.slice(0, historyIndex + 1); }
                historyStack.push(stateSnapshot);
                if (historyStack.length > MAX_HISTORY) historyStack.shift(); else historyIndex++;
            } catch(e) {}
        }

        function restoreHistoryState(index) {
            try {
                if (index < 0 || index >= historyStack.length) return;
                const parsedScenes = JSON.parse(historyStack[index]);
                scenes = parsedScenes.map(s => {
                    let newScene = new ObsScene(s.id, s.name);
                    newScene.sources = s.sources || [];
                    newScene.transition = s.transition || 'fade';
                    newScene.transitionDuration = s.transitionDuration || 500;
                    return newScene;
                });
                let currentActiveId = activeScene ? activeScene.id : null;
                activeScene = scenes.find(s => s.id === currentActiveId) || scenes[0];
                sources = activeScene ? activeScene.sources : [];
                if (typeof updateScenesList === 'function') updateScenesList();
                if (typeof switchScene === 'function' && activeScene) switchScene(activeScene.id);
                historyIndex = index;
            } catch(e) {}
        }

        function triggerUndo() { if (historyIndex > 0) restoreHistoryState(historyIndex - 1); }
        function triggerRedo() { if (historyIndex < historyStack.length - 1) restoreHistoryState(historyIndex + 1); }

        setTimeout(saveHistoryState, 1000);

        let historyDebounce;
        const handleInteraction = () => {
            clearTimeout(historyDebounce);
            historyDebounce = setTimeout(saveHistoryState, 400);
        };
        document.addEventListener('mouseup', handleInteraction);
        document.addEventListener('keyup', handleInteraction);

        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'z') { e.preventDefault(); triggerUndo(); }
            if (e.ctrlKey && e.key.toLowerCase() === 'y') { e.preventDefault(); triggerRedo(); }
        });

        // --- 1. GUARANTEE MENU CLICKABILITY & CLEANUP ---
        topNav.style.position = 'relative';
        topNav.style.zIndex = '100000';

        ['desktopFeatureModal', 'customInputModal', 'customConfirmModal', 'customAboutModal'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.remove();
        });

        // --- 2. INJECT CUSTOM MODALS ---
        const customModalsHTML = `
            <div id="desktopFeatureModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 99999; justify-content: center; align-items: center; font-family: 'Segoe UI', Arial, sans-serif;">
                <div class="draggable-modal-box" style="background-color: #272a33; border: 1px solid #3c404d; border-radius: 8px; width: 450px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; position: relative;">
                    <div class="draggable-modal-header" style="background-color: #1d1f26; padding: 15px 20px; border-bottom: 1px solid #3c404d; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; cursor: grab;">
                        <h3 style="margin: 0; color: #dfdfdf; font-size: 16px; font-weight: 600; pointer-events: none;" id="dfmTitle">Feature Unavailable</h3>
                        <button id="dfmCloseIcon" style="background: none; border: none; color: #888; cursor: pointer; font-size: 16px;"><i class="fas fa-times"></i></button>
                    </div>
                    <div style="padding: 20px; color: #cccccc; font-size: 14px; line-height: 1.5;" id="dfmBody"></div>
                    <div style="padding: 15px 20px; border-top: 1px solid #3c404d; display: flex; justify-content: flex-end; gap: 10px; background-color: #1d1f26; border-radius: 0 0 8px 8px;">
                        <button id="dfmCloseBtn" style="padding: 8px 16px; background-color: #3c404d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;">Close</button>
                        <button id="dfmGetObsBtn" style="padding: 8px 16px; background-color: #1e50a0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;"><i class="fas fa-download" style="margin-right: 5px;"></i> Get OBS Studio</button>
                    </div>
                </div>
            </div>

            <div id="customInputModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 99999; justify-content: center; align-items: center; font-family: 'Segoe UI', Arial, sans-serif;">
                <div class="draggable-modal-box" style="background-color: #272a33; border: 1px solid #3c404d; border-radius: 8px; width: 350px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; position: relative;">
                    <div class="draggable-modal-header" style="background-color: #1d1f26; padding: 15px 20px; border-bottom: 1px solid #3c404d; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; cursor: grab;">
                        <h3 style="margin: 0; color: #dfdfdf; font-size: 16px; font-weight: 600; pointer-events: none;" id="cimTitle">Input Required</h3>
                        <button id="cimCloseIcon" style="background: none; border: none; color: #888; cursor: pointer; font-size: 16px;"><i class="fas fa-times"></i></button>
                    </div>
                    <div style="padding: 20px; display: flex; flex-direction: column; gap: 10px;">
                        <label id="cimLabel" style="color: #cccccc; font-size: 14px;">Enter value:</label>
                        <input type="text" id="cimInput" style="background-color: #1d1f26; border: 1px solid #3c404d; color: #fff; padding: 8px 12px; border-radius: 4px; outline: none; font-size: 14px; width: 100%; box-sizing: border-box;">
                    </div>
                    <div style="padding: 15px 20px; border-top: 1px solid #3c404d; display: flex; justify-content: flex-end; gap: 10px; background-color: #1d1f26; border-radius: 0 0 8px 8px;">
                        <button id="cimCancelBtn" style="padding: 8px 16px; background-color: #3c404d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;">Cancel</button>
                        <button id="cimSubmitBtn" style="padding: 8px 16px; background-color: #1e50a0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;">OK</button>
                    </div>
                </div>
            </div>

            <div id="customConfirmModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 99999; justify-content: center; align-items: center; font-family: 'Segoe UI', Arial, sans-serif;">
                <div class="draggable-modal-box" style="background-color: #272a33; border: 1px solid #3c404d; border-radius: 8px; width: 400px; max-width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; position: relative;">
                    <div class="draggable-modal-header" style="background-color: #1d1f26; padding: 15px 20px; border-bottom: 1px solid #3c404d; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; cursor: grab;">
                        <h3 style="margin: 0; color: #ff4a4a; font-size: 16px; font-weight: 600; pointer-events: none;" id="ccmTitle">Warning</h3>
                        <button id="ccmCloseIcon" style="background: none; border: none; color: #888; cursor: pointer; font-size: 16px;"><i class="fas fa-times"></i></button>
                    </div>
                    <div style="padding: 20px; display: flex; gap: 15px; align-items: center;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 32px; color: #ffb142;"></i>
                        <p id="ccmMessage" style="color: #cccccc; font-size: 14px; margin: 0; line-height: 1.5;">Are you sure?</p>
                    </div>
                    <div style="padding: 15px 20px; border-top: 1px solid #3c404d; display: flex; justify-content: flex-end; gap: 10px; background-color: #1d1f26; border-radius: 0 0 8px 8px;">
                        <button id="ccmCancelBtn" style="padding: 8px 16px; background-color: #3c404d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;">Cancel</button>
                        <button id="ccmConfirmBtn" style="padding: 8px 16px; background-color: #ff4a4a; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s; font-weight: 600;">Confirm</button>
                    </div>
                </div>
            </div>

            <div id="customAboutModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: transparent; pointer-events: none; z-index: 99999; font-family: 'Segoe UI', Arial, sans-serif;">
                <div class="draggable-modal-box" style="background-color: #272a33; border: 1px solid #3c404d; border-radius: 8px; width: 420px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); display: flex; flex-direction: column; position: absolute; pointer-events: auto;">
                    <div class="draggable-modal-header" style="background-color: #1d1f26; padding: 15px 20px; border-bottom: 1px solid #3c404d; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; cursor: grab;">
                        <h3 style="margin: 0; color: #dfdfdf; font-size: 16px; font-weight: 600; pointer-events: none;">About OBS WebApp</h3>
                        <button id="camCloseIcon" style="background: none; border: none; color: #888; cursor: pointer; font-size: 16px;"><i class="fas fa-times"></i></button>
                    </div>
                    <div style="padding: 20px; text-align: center;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/d/d3/OBS_Studio_Logo.svg" alt="OBS Logo" style="width: 64px; height: 64px; margin-bottom: 15px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.5));">
                        <h2 style="margin: 0 0 5px 0; color: #fff; font-size: 20px;">OBS WebApp Clone</h2>
                        <p style="color: #4daafc; font-size: 13px; margin-bottom: 15px;">Hosted at <a href="https://obs.ywa.app" target="_blank" style="color: #4daafc; text-decoration: none; font-weight: bold;">obs.ywa.app</a></p>

                        <div style="background: #1d1f26; padding: 15px; border-radius: 6px; border: 1px solid #3c404d; margin-bottom: 15px;">
                            <p style="color: #ccc; font-size: 13px; margin: 0 0 10px 0; line-height: 1.5;">A completely free and ad-free browser-based broadcast, recording, and editing studio.</p>
                            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #3c404d;">
                                <span style="color: #888; font-size: 12px;">Brought to you by</span>
                                <a href="https://ywa.app" target="_blank" style="display: flex; align-items: center; gap: 6px; text-decoration: none; color: #dfdfdf; font-weight: 600; font-size: 13px; transition: color 0.2s;" onmouseover="this.style.color='#4daafc'" onmouseout="this.style.color='#dfdfdf'">
                                    <img src="https://proxy.duckduckgo.com/iu/?u=https://i.imgur.com/KTWctjb.png" alt="YWA App" style="height: 20px; vertical-align: middle;">
                                    ywa.app
                                </a>
                            </div>
                        </div>
                        
                        <p style="color: #888; font-size: 11px; margin: 0; line-height: 1.4;">Disclaimer: This is an independent web adaptation. For the official native desktop client, please visit <a href="https://obsproject.com" target="_blank" style="color: #888; text-decoration: underline;">obsproject.com</a>.</p>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', customModalsHTML);

        // Utility: Make any modal box draggable
        function makeModalDraggable(modalId) {
            const modalWrapper = document.getElementById(modalId);
            if (!modalWrapper) return;
            const modalBox = modalWrapper.querySelector('.draggable-modal-box');
            const header = modalWrapper.querySelector('.draggable-modal-header');
            
            let isDragging = false, offsetX, offsetY;

            header.addEventListener('mousedown', (e) => {
                if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
                isDragging = true;
                header.style.cursor = 'grabbing';
                const rect = modalBox.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                document.body.style.userSelect = 'none';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                modalBox.style.position = 'absolute';
                modalBox.style.margin = '0';
                modalBox.style.left = Math.max(0, Math.min(e.clientX - offsetX, window.innerWidth - modalBox.offsetWidth)) + 'px';
                modalBox.style.top = Math.max(0, Math.min(e.clientY - offsetY, window.innerHeight - modalBox.offsetHeight)) + 'px';
                modalBox.style.bottom = 'auto'; modalBox.style.right = 'auto';
            });

            document.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                    header.style.cursor = 'grab';
                    document.body.style.userSelect = '';
                }
            });
        }

        makeModalDraggable('desktopFeatureModal');
        makeModalDraggable('customInputModal');
        makeModalDraggable('customConfirmModal');
        makeModalDraggable('customAboutModal');

        // Logic: Desktop Warnings Modal
        const desktopModal = document.getElementById('desktopFeatureModal');
        const closeDesktopModal = () => desktopModal.style.display = 'none';
        document.getElementById('dfmCloseIcon').addEventListener('click', closeDesktopModal);
        document.getElementById('dfmCloseBtn').addEventListener('click', closeDesktopModal);
        document.getElementById('dfmGetObsBtn').addEventListener('click', () => { window.open('https://obsproject.com/download', '_blank'); closeDesktopModal(); });

        const desktopDescriptions = {
            "Show Settings Folder": { icon: "fa-folder-open", text: "Opens the system directory containing OBS's core configuration files on your local hard drive." },
            "Show Profile Folder": { icon: "fa-user-cog", text: "Opens the directory containing your user-specific profile data on your computer." },
            "Copy/Paste Filters": { icon: "fa-magic", text: "Allows you to copy effects (like color correction or noise suppression) from one source and apply them directly to another." },
            "Transform": { icon: "fa-crop-alt", text: "Provides options to mathematically resize, rotate, flip, center, or stretch a source within your preview canvas." },
            "Order": { icon: "fa-layer-group", text: "Moves the selected source up or down in your visual layering hierarchy (e.g., move to top, send to back)." },
            "Preview Scaling": { icon: "fa-search-plus", text: "Adjusts how the main preview window shrinks or enlarges to fit your screen resolution." },
            "Lock Preview": { icon: "fa-lock", text: "Prevents you from accidentally clicking, moving, or resizing sources in the preview window." },
            "Advanced Audio Properties": { icon: "fa-sliders-h", text: "Opens a detailed grid to adjust audio sync offsets, panning, volume percentages, and monitoring preferences." },
            "Scene List Mode": { icon: "fa-th-list", text: "Changes how your scenes are displayed in the dock (e.g., as a list or a grid)." },
            "Dock Toolbars": { icon: "fa-toolbox", text: "Toggles the visibility of specific visual elements and toolbars within the interface." },
            "Source Toolbar": { icon: "fa-wrench", text: "Toggles the contextual toolbar above the preview." },
            "Source Icons": { icon: "fa-image", text: "Toggles the visibility of icons next to your sources in the dock." },
            "Status Bar": { icon: "fa-info-circle", text: "Toggles the information bar at the bottom of the OBS window." },
            "Open Multiview": { icon: "fa-th-large", text: "Opens a window displaying multiple scenes simultaneously, which is highly useful for live switching during a broadcast." },
            "Always On Top": { icon: "fa-level-up-alt", text: "Forces the OBS window to stay layered above all other open applications on your computer." },
            "Lock Docks": { icon: "fa-lock", text: "Prevents you from accidentally dragging, moving, or closing your interface panels." },
            "Full-Height Docks": { icon: "fa-arrows-alt-v", text: "Forces dock panels (like Chat or Audio Mixer) to stretch to the full vertical height of the window." },
            "Reset Docks": { icon: "fa-undo-alt", text: "Returns all panels to their original, default positions." },
            "Custom Browser Docks": { icon: "fa-globe", text: "Allows you to embed custom web pages directly into the OBS interface (commonly used for Twitch chat or stream alerts)." },
            "Check for Missing Files": { icon: "fa-file-search", text: "Scans your current layout to ensure all linked media (images, videos, sounds) are still located where OBS expects them to be." },
            "Auto-Configuration Wizard": { icon: "fa-magic", text: "Tests your system hardware and internet speed to automatically recommend the best settings for streaming or recording." },
            "Plugin Manager": { icon: "fa-puzzle-piece", text: "Displays and manages native third-party add-ons installed in OBS." },
            "Captions (Experimental)": { icon: "fa-closed-captioning", text: "A tool for generating and adding closed captions to your broadcast." },
            "Automatic Scene Switcher": { icon: "fa-exchange-alt", text: "An automation tool that changes your active scene based on specific triggers, like which window you currently have open on your PC." },
            "Output Timer": { icon: "fa-stopwatch", text: "Allows you to set a specific countdown for OBS to automatically stop recording or streaming." },
            "Scripts": { icon: "fa-code", text: "Opens a manager for adding custom Lua or Python scripts to introduce new functionalities." },
            "WebSocket Server Settings": { icon: "fa-network-wired", text: "Configures remote control access, allowing tools like Stream Decks or mobile apps to communicate with OBS." },
            "Log Files": { icon: "fa-file-alt", text: "Options to view, analyze, or upload diagnostic files to help figure out why OBS crashed or is lagging." },
            "Crash Reports": { icon: "fa-bug", text: "Allows you to view and submit diagnostic files for crash analysis." },
            "Check File Integrity": { icon: "fa-shield-alt", text: "Scans your OBS software installation to make sure no core files are corrupted or missing." },
            "Check For Updates": { icon: "fa-sync-alt", text: "Pings the server to see if a newer version of the software is available to download." },
            "Restart in Safe Mode": { icon: "fa-hard-hat", text: "Reboots OBS with all third-party plugins and scripts disabled, which is very helpful for troubleshooting crashes." },
            "What's New": { icon: "fa-bullhorn", text: "Displays information about recent updates, features, and bug fixes." },
            "Release Notes": { icon: "fa-clipboard-list", text: "Displays detailed patch notes for the current software version." }
        };

        function showDesktopModal(featureName) {
            const meta = desktopDescriptions[featureName] || { icon: 'fa-desktop', text: `The '${featureName}' tool is a native desktop feature designed to interact directly with your operating system's hardware, file paths, or backend encoding settings.` };
            document.getElementById('dfmTitle').textContent = featureName;
            document.getElementById('dfmBody').innerHTML = `
                <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                    <div style="font-size: 24px; color: #4daafc;"><i class="fas ${meta.icon}"></i></div>
                    <p style="margin: 0; color: #dfdfdf; flex: 1; padding-top: 3px; font-size: 14px;">${meta.text}</p>
                </div>
                <p style="margin-bottom: 0; color: #999; font-size: 13px;">Because this WebApp operates entirely within your browser's local memory, advanced hardware and file management is restricted.</p>
                <p style="margin-top: 15px; margin-bottom: 0; color: #4daafc; font-weight: 500; font-size: 13px;">For the complete broadcasting experience, we highly recommend using the official OBS Studio desktop client.</p>
            `;
            desktopModal.style.display = 'flex';
        }

        // Logic: Floating About Modal
        const aboutModal = document.getElementById('customAboutModal');
        document.getElementById('camCloseIcon').addEventListener('click', () => { aboutModal.style.display = 'none'; });
        
        function showAboutModal() {
            const aboutBox = aboutModal.querySelector('.draggable-modal-box');
            // Center the floating box on screen
            aboutBox.style.left = Math.max(0, (window.innerWidth / 2) - 210) + 'px';
            aboutBox.style.top = Math.max(0, (window.innerHeight / 2) - 180) + 'px';
            aboutModal.style.display = 'block';
        }

        // Logic: Input/Confirm Modals
        const inputModal = document.getElementById('customInputModal');
        const inputField = document.getElementById('cimInput');
        let currentSubmitCallback = null;

        const closeInputModal = () => { inputModal.style.display = 'none'; currentSubmitCallback = null; };
        document.getElementById('cimCloseIcon').addEventListener('click', closeInputModal);
        document.getElementById('cimCancelBtn').addEventListener('click', closeInputModal);
        document.getElementById('cimSubmitBtn').addEventListener('click', () => {
            if (currentSubmitCallback) currentSubmitCallback(inputField.value);
            closeInputModal();
        });

        function showCustomPrompt(title, label, defaultValue, callback) {
            document.getElementById('cimTitle').textContent = title;
            document.getElementById('cimLabel').textContent = label;
            inputField.value = defaultValue;
            currentSubmitCallback = callback;
            inputModal.style.display = 'flex';
            inputField.focus();
            inputField.select();
        }

        const confirmModal = document.getElementById('customConfirmModal');
        let currentConfirmCallback = null;
        
        const closeConfirmModal = () => { confirmModal.style.display = 'none'; currentConfirmCallback = null; };
        document.getElementById('ccmCloseIcon').addEventListener('click', closeConfirmModal);
        document.getElementById('ccmCancelBtn').addEventListener('click', closeConfirmModal);
        document.getElementById('ccmConfirmBtn').addEventListener('click', () => {
            if (currentConfirmCallback) currentConfirmCallback();
            closeConfirmModal();
        });

        function showCustomConfirm(title, message, callback) {
            document.getElementById('ccmTitle').textContent = title;
            document.getElementById('ccmMessage').textContent = message;
            currentConfirmCallback = callback;
            confirmModal.style.display = 'flex';
        }

        // --- 3. CLEAN UP TEXT & BIND MENUS ---
        const oldMenuItems = topNav.querySelectorAll('.menu-item');
        oldMenuItems.forEach(item => {
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
        });

        const allDropdownRows = topNav.querySelectorAll('.dropdown-row');
        allDropdownRows.forEach(row => {
            const textEl = row.querySelector('.menu-text');
            if (textEl) {
                let txt = textEl.textContent.trim();
                if (txt.startsWith('Undo') && !txt.includes('Redo')) textEl.textContent = 'Undo';
                else if (txt.startsWith('Redo')) textEl.textContent = 'Redo';
                else if (txt.includes('Undo/Redo')) textEl.textContent = 'Undo / Redo';
            }
        });

        const menuItems = topNav.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.dropdown-content')) return;
                e.stopPropagation();
                const wasActive = item.classList.contains('active');
                menuItems.forEach(i => i.classList.remove('active'));
                if (!wasActive) item.classList.add('active');
            });
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.obs-menu')) menuItems.forEach(i => i.classList.remove('active'));
        });

        // Keyboard Event Hijacker for Copy/Paste Menu Triggers
        function triggerKeyboardShortcut(key) {
            document.dispatchEvent(new KeyboardEvent('keydown', { key: key, code: 'Key' + key.toUpperCase(), ctrlKey: true, bubbles: true }));
        }

        // --- 4. BIND MENU ITEM ACTIONS ---
        allDropdownRows.forEach(row => {
            row.addEventListener('click', (e) => {
                e.stopPropagation();
                const textEl = row.querySelector('.menu-text');
                if (!textEl) return;
                const actionName = textEl.textContent.trim();

                menuItems.forEach(i => i.classList.remove('active'));

                switch(actionName) {
                    
                    // Native WebApp Core Actions
                    case 'Undo':
                    case 'Undo / Redo': triggerUndo(); break;
                    case 'Redo': triggerRedo(); break;

                    case 'Copy': 
                        triggerKeyboardShortcut('c'); 
                        break;
                    case 'Paste (Duplicate)':
                    case 'Paste (Reference)': 
                        triggerKeyboardShortcut('v'); 
                        break;

                    case 'Settings':
                        const settingsBtn = document.getElementById('settingsBtn') || document.getElementById('menuSettingsBtn') || document.querySelector('[title="Settings"]');
                        const setModal = document.getElementById('settingsModal');
                        if (settingsBtn) { settingsBtn.click(); } 
                        else if (setModal) { setModal.style.display = 'flex'; setModal.classList.add('active'); }
                        break;

                    case 'Exit':
                        showCustomConfirm("Exit WebApp", "Are you sure you want to close the OBS WebApp?", () => {
                            window.close();
                            document.body.innerHTML = `
                                <div style="background-color:#1d1f26; width:100vw; height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; color:#dfdfdf; font-family:sans-serif;">
                                    <i class="fas fa-power-off" style="font-size:48px; color:#3c404d; margin-bottom:20px;"></i>
                                    <h2 style="margin-bottom:10px;">OBS WebApp Closed</h2>
                                    <p style="color:#888;">You may safely close this browser tab.</p>
                                </div>`;
                        });
                        break;

                    case 'About': showAboutModal(); break;

                    case 'Duplicate...':
                        if (typeof activeScene !== 'undefined' && activeScene !== null) {
                            showCustomPrompt("Duplicate Scene", "Enter name for duplicated scene:", activeScene.name + " (Copy)", (dupName) => {
                                if (dupName && dupName.trim() !== "") {
                                    try {
                                        const newScene = new ObsScene(Date.now(), dupName.trim());
                                        newScene.sources = activeScene.sources.map(src => Object.assign({}, src, { id: Date.now() + Math.random() }));
                                        scenes.push(newScene);
                                        if (typeof updateScenesList === 'function') updateScenesList();
                                        if (typeof switchScene === 'function') switchScene(newScene.id);
                                        saveHistoryState(); 
                                    } catch (err) {}
                                }
                            });
                        }
                        break;

                    case 'Reset UI':
                        showCustomConfirm("Reset UI", "Are you sure you want to reset the UI? This will clear your scenes and restore all default panels.", () => {
                            try {
                                scenes = [new ObsScene(Date.now(), 'Scene 1')];
                                activeScene = scenes[0];
                                sources = activeScene.sources;
                                if (typeof updateScenesList === 'function') updateScenesList();
                                if (typeof switchScene === 'function') switchScene(scenes[0].id);
                                
                                ['dock-scenes', 'dock-sources', 'dock-mixer', 'dock-transitions', 'dock-controls'].forEach(id => {
                                    const dock = document.getElementById(id);
                                    if (dock) { dock.style.display = 'flex'; dock.classList.remove('hidden'); }
                                });
                                
                                const statsModal = document.getElementById('statsModal');
                                if (statsModal) statsModal.style.display = 'none';
                                document.body.style.paddingBottom = '0';
                                const dockBtn = document.getElementById('customDockBtn');
                                if (dockBtn && dockBtn.dataset.docked === 'true') dockBtn.click();
                                
                                saveHistoryState(); 
                            } catch(e) {}
                        });
                        break;

                    case 'New...':
                        const addSceneBtn = document.getElementById('addSceneBtn') || document.querySelector('.add-scene-btn');
                        if (addSceneBtn) { addSceneBtn.click(); saveHistoryState(); }
                        break;

                    case 'Rename...':
                        if (typeof activeScene !== 'undefined' && activeScene !== null) {
                            showCustomPrompt("Rename Scene", "Enter new name:", activeScene.name, (newName) => {
                                if (newName && newName.trim() !== "") {
                                    activeScene.name = newName.trim();
                                    if (typeof updateScenesList === 'function') updateScenesList();
                                    saveHistoryState();
                                }
                            });
                        }
                        break;

                    case 'Remove':
                        const removeSceneBtn = document.getElementById('removeSceneBtn') || document.querySelector('.remove-scene-btn');
                        if (removeSceneBtn) { removeSceneBtn.click(); saveHistoryState(); }
                        break;

                    case 'Import...':
                    case 'Export...': showDesktopModal(`${actionName.replace('...', '')} Settings`); break;

                    case 'Reset Base Resolution':
                        const setBtn = document.getElementById('menuSettingsBtn');
                        if (setBtn) setBtn.click();
                        setTimeout(() => {
                            const videoTab = document.querySelector('.settings-tab[data-target="set-video"]');
                            if (videoTab) videoTab.click();
                        }, 100);
                        break;

                    case 'Show Recordings':
                    case 'Remux Recordings':
                        const advModal = document.getElementById('advancedEditorModal');
                        if (advModal) advModal.style.display = 'flex';
                        break;
                    
                    case 'Fullscreen Interface':
                        if (!document.fullscreenElement) { document.documentElement.requestFullscreen().catch(err => {}); } 
                        else { document.exitFullscreen(); }
                        break;

                    case 'Stats':
                        const statsBtn = document.getElementById('statsBtn') || document.getElementById('statsModal');
                        if (statsBtn && statsBtn.tagName === 'BUTTON') statsBtn.click();
                        else if (statsBtn) statsBtn.style.display = 'block'; 
                        break;

                    case 'Scenes': toggleDock('dock-scenes', row); break;
                    case 'Sources': toggleDock('dock-sources', row); break;
                    case 'Audio Mixer': toggleDock('dock-mixer', row); break;
                    case 'Scene Transitions': toggleDock('dock-transitions', row); break;
                    case 'Controls': toggleDock('dock-controls', row); break;

                    case 'Help Portal':
                    case 'Visit Website': window.open('https://obsproject.com/help', '_blank'); break;
                    case 'Join Discord Server': window.open('https://obsproject.com/discord', '_blank'); break;

                    default: showDesktopModal(actionName); break;
                }
            });
        });

        function toggleDock(dockId, rowEl) {
            const dock = document.getElementById(dockId);
            const icon = rowEl.querySelector('.menu-icon');
            if (dock) {
                const isHidden = window.getComputedStyle(dock).display === 'none' || dock.classList.contains('hidden');
                if (isHidden) { dock.style.display = 'flex'; dock.classList.remove('hidden'); if(icon) icon.innerHTML = '<i class="fas fa-check"></i>'; } 
                else { dock.style.display = 'none'; dock.classList.add('hidden'); if(icon) icon.innerHTML = ''; }
            }
        }

        // --- 5. STATS FIXED-SIZE FLOATING & BOTTOM DOCKING LOGIC ---
        const statsModal = document.getElementById('statsModal');
        if (statsModal) {
            statsModal.style.backgroundColor = 'transparent';
            statsModal.style.pointerEvents = 'none'; 

            const statsBox = statsModal.firstElementChild;
            if (statsBox) {
                // Fixed default width prevents squashing (Expanded to 750px)
                const defaultStatsWidth = '750px';
                const defaultStatsHeight = '350px';

                statsBox.style.pointerEvents = 'auto'; 
                statsBox.style.position = 'absolute';
                statsBox.style.top = '60px'; 
                statsBox.style.right = '20px';
                statsBox.style.margin = '0'; 
                statsBox.style.width = defaultStatsWidth;
                statsBox.style.height = defaultStatsHeight;
                statsBox.style.boxShadow = '0 10px 25px rgba(0,0,0,0.6)';
                statsBox.style.zIndex = '99990'; 
                statsBox.style.transition = 'all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1)'; 

                const header = statsBox.querySelector('.modal-header') || statsBox.firstElementChild;
                let isDragging = false, offsetX, offsetY;

                if (header) {
                    header.style.cursor = 'grab';
                    header.addEventListener('mousedown', (e) => {
                        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return; 
                        const dockBtn = document.getElementById('customDockBtn');
                        if (dockBtn && dockBtn.dataset.docked === 'true') return;

                        isDragging = true;
                        header.style.cursor = 'grabbing';
                        statsBox.style.transition = 'none'; 
                        const rect = statsBox.getBoundingClientRect();
                        offsetX = e.clientX - rect.left;
                        offsetY = e.clientY - rect.top;
                        document.body.style.userSelect = 'none';
                    });

                    document.addEventListener('mousemove', (e) => {
                        if (!isDragging) return;
                        let newX = e.clientX - offsetX;
                        let newY = e.clientY - offsetY;
                        const maxX = window.innerWidth - statsBox.offsetWidth;
                        const maxY = window.innerHeight - statsBox.offsetHeight;
                        statsBox.style.left = Math.max(0, Math.min(newX, maxX)) + 'px';
                        statsBox.style.top = Math.max(0, Math.min(newY, maxY)) + 'px';
                        statsBox.style.bottom = 'auto'; statsBox.style.right = 'auto';
                    });

                    document.addEventListener('mouseup', () => {
                        if (isDragging) {
                            isDragging = false;
                            header.style.cursor = 'grab';
                            document.body.style.userSelect = ''; 
                            statsBox.style.transition = 'all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1)'; 
                        }
                    });
                }

                const allCloseButtons = statsBox.querySelectorAll('.close-btn, [class*="close"], button');
                const topCloseBtn = statsBox.querySelector('.close-btn, [class*="close"]');

                if (topCloseBtn && topCloseBtn.parentElement && !document.getElementById('customDockBtn')) {
                    const dockBtn = document.createElement('button');
                    dockBtn.id = 'customDockBtn';
                    dockBtn.dataset.docked = 'false';
                    dockBtn.innerHTML = '<i class="fas fa-arrow-down"></i>'; 
                    dockBtn.title = "Dock to Bottom / Float";
                    dockBtn.style.background = 'none';
                    dockBtn.style.border = 'none';
                    dockBtn.style.color = '#888';
                    dockBtn.style.cursor = 'pointer';
                    dockBtn.style.marginRight = '15px';
                    dockBtn.style.fontSize = '14px';

                    let preDockLeft, preDockTop;
                    const dockHeight = 180; 

                    dockBtn.addEventListener('click', () => {
                        const isDocked = dockBtn.dataset.docked === 'true';
                        if (!isDocked) {
                            dockBtn.dataset.docked = 'true';
                            preDockLeft = statsBox.style.left;
                            preDockTop = statsBox.style.top;
                            dockBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
                            
                            statsBox.style.top = 'auto'; statsBox.style.right = '0';
                            statsBox.style.left = '0'; statsBox.style.bottom = '0';
                            statsBox.style.height = `${dockHeight}px`; 
                            statsBox.style.width = '100%'; statsBox.style.maxWidth = '100%';
                            statsBox.style.borderRadius = '0'; 
                            statsBox.style.boxShadow = '0 -5px 15px rgba(0,0,0,0.3)'; 
                            
                            document.body.style.transition = 'padding-bottom 0.25s';
                            document.body.style.paddingBottom = `${dockHeight}px`;
                        } else {
                            dockBtn.dataset.docked = 'false';
                            dockBtn.innerHTML = '<i class="fas fa-arrow-down"></i>';
                            
                            statsBox.style.left = preDockLeft || 'auto';
                            statsBox.style.top = preDockTop || '60px';
                            statsBox.style.right = preDockLeft ? 'auto' : '20px'; 
                            statsBox.style.bottom = 'auto';
                            
                            statsBox.style.height = defaultStatsHeight;
                            statsBox.style.width = defaultStatsWidth; 
                            statsBox.style.maxWidth = 'none';
                            statsBox.style.borderRadius = '8px'; 
                            statsBox.style.boxShadow = '0 10px 25px rgba(0,0,0,0.6)';
                            
                            document.body.style.paddingBottom = '0';
                        }
                    });
                    
                    dockBtn.onmouseover = () => dockBtn.style.color = '#fff';
                    dockBtn.onmouseout = () => dockBtn.style.color = '#888';
                    topCloseBtn.parentElement.insertBefore(dockBtn, topCloseBtn);
                }

                allCloseButtons.forEach(btn => {
                    if (btn.classList.contains('close-btn') || btn.textContent.toLowerCase().includes('close')) {
                        btn.addEventListener('click', () => {
                            statsModal.style.display = 'none';
                            const dockBtn = document.getElementById('customDockBtn');
                            if (dockBtn && dockBtn.dataset.docked === 'true') {
                                document.body.style.paddingBottom = '0';
                                dockBtn.click(); 
                            }
                        });
                    }
                });
            }
        }

        console.log("✅ OBS Master Addon Loaded: Clean UI, YWA Links, Settings, and Copy/Paste active.");
    } catch (e) {
        console.error("❌ Master Addon Error:", e);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOBSMasterAddon);
} else {
    initOBSMasterAddon();
}
// =========================================================================
// =================== ENHANCED PREMIUM STREAMING ALERT ====================
// =========================================================================
setTimeout(() => {
    const allObsBtns = document.querySelectorAll('.obs-btn');

    allObsBtns.forEach(btn => {
        // Hook up the "Start Streaming" button
        if (btn.textContent.trim() === 'Start Streaming') {
            // Clone to remove the old event listener
            const newStreamBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newStreamBtn, btn);

            newStreamBtn.addEventListener('click', () => {
                const customAlert = document.getElementById('customAlertModal');
                const customMsg = document.getElementById('customAlertMessage');
                const title = document.getElementById('customAlertTitle');

                if (customAlert && customMsg) {
                    // Update the window title
                    if (title) title.innerHTML = '<i class="fas fa-broadcast-tower"></i> Broadcast Limitation';
                    
                    // Inject premium formatted HTML content (No Glow)
                    customMsg.innerHTML = `
                        <div style="padding: 20px 0; margin-bottom: 5px;">
                            <i class="fas fa-satellite-dish" style="font-size: 54px; color: #e74c3c; display: block; margin-bottom: 5px;"></i>
                        </div>
                        
                        <span style="font-size: 20px; font-weight: 800; color: #ffffff; display: block; margin-bottom: 12px; letter-spacing: 0.5px;">
                            Live Streaming is Offline
                        </span>
                        
                        <span style="font-size: 14px; color: #cccccc; display: block; line-height: 1.6; margin-bottom: 22px; padding: 0 10px;">
                            Because <b>OBS WebApp</b> operates entirely within your local browser environment for privacy and performance, it cannot securely broadcast RTMP or HLS streams without a dedicated backend server connected.
                        </span>
                        
                        <div style="background: linear-gradient(90deg, rgba(46, 204, 113, 0.05) 0%, rgba(46, 204, 113, 0.15) 50%, rgba(46, 204, 113, 0.05) 100%); padding: 14px; border-radius: 6px; border: 1px solid rgba(46, 204, 113, 0.3); display: flex; align-items: center; justify-content: center; gap: 10px;">
                            <i class="fas fa-record-vinyl" style="color: #2ecc71; font-size: 20px;"></i>
                            <span style="font-size: 14.5px; color: #2ecc71; font-weight: bold;">
                                Local Recording is Fully Functional!
                            </span>
                        </div>
                    `;
                    
                    customAlert.classList.add('active');
                } else {
                    // Fallback popup
                    alert("Streaming is unavailable in OBS WebApp without a backend. You can still record locally!");
                }
            });
        }
    });
}, 1000);
// =========================================================================
// =================== GUARANTEED SETTINGS BUTTON FIX ======================
// =========================================================================
setTimeout(() => {
    // 1. Make the bottom dock "Settings" button open the menu
    const dockSettingsBtn = document.getElementById('settingsBtn');
    if (dockSettingsBtn) {
        dockSettingsBtn.addEventListener('click', () => {
            if (typeof closeAllMenus === 'function') closeAllMenus();
            const modal = document.getElementById('settingsModal');
            if (modal) {
                modal.classList.add('active');
                // Ensure it pops up in the center of the screen
                const win = modal.querySelector('.obs-window');
                if (win) { 
                    win.style.transform = 'translate(-50%, -50%)'; 
                    win.style.left = '50%'; 
                    win.style.top = '50%'; 
                }
            }
        });
    }

    // 2. Make the new OK, Cancel, and Apply buttons close the menu
    ['settingsOkBtn', 'settingsCancelBtn', 'settingsApplyBtn'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', () => {
                const modal = document.getElementById('settingsModal');
                if (modal) modal.classList.remove('active');
            });
        }
    });
}, 500);
// =========================================================================
// ===================== ULTIMATE SETTINGS TAB FIX =========================
// =========================================================================
setTimeout(() => {
    // 1. Find all duplicated settings menus and target only the LAST one (the active one)
    const allSettingsModals = document.querySelectorAll('#settingsModal');
    const realModal = allSettingsModals[allSettingsModals.length - 1];
    
    if (!realModal) return;

    // 2. Scope the tab logic specifically to this exact menu so duplicates don't steal the clicks
    const tabs = realModal.querySelectorAll('.settings-tab');
    const sections = realModal.querySelectorAll('.settings-section');
    
    tabs.forEach(tab => {
        // Clone the tab to strip away any broken, conflicting click events from previous code
        const newTab = tab.cloneNode(true);
        tab.parentNode.replaceChild(newTab, tab);
        
        newTab.addEventListener('click', () => {
            // Remove 'active' from all tabs and sections inside THIS specific modal
            realModal.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            
            // Add 'active' to the clicked tab
            newTab.classList.add('active');
            
            // Find and show the matching section
            const targetId = newTab.getAttribute('data-target');
            const targetSection = realModal.querySelector('#' + targetId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
        });
    });

    console.log("✅ Settings Tabs locked and secured.");
}, 1000);
// =========================================================================
// ================= FORCE-FIX "RECORDINGS & EDITOR" BUTTON ================
// =========================================================================

setTimeout(() => {
    // Find all buttons on the page
    const allButtons = document.querySelectorAll('.obs-btn');
    let realEditorBtn = null;
    
    // Search specifically for the visible button by its text content
    allButtons.forEach(btn => {
        if (btn.textContent.includes('Recordings & Editor') && btn.closest('.controls-box')) {
            realEditorBtn = btn;
        }
    });

    if (realEditorBtn) {
        // Clone the button to instantly wipe any broken/frozen event listeners attached to it
        const freshEditorBtn = realEditorBtn.cloneNode(true);
        realEditorBtn.parentNode.replaceChild(freshEditorBtn, realEditorBtn);
        
        // Attach the correct function to open the Advanced Editor
        freshEditorBtn.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (typeof closeAllMenus === 'function') closeAllMenus();
            
            const advModal = document.getElementById('advancedEditorModal');
            if (advModal) {
                // Open the new NLE Editor
                advModal.classList.add('active');
                const win = advModal.querySelector('.obs-window');
                if (win) { 
                    win.style.transform = 'translate(-50%, -50%)'; 
                    win.style.left = '50%'; 
                    win.style.top = '50%'; 
                }
            } else {
                // Failsafe: If the new HTML isn't found, try to open the old one
                const oldModal = document.getElementById('editorModal');
                if (oldModal) {
                    oldModal.classList.add('active');
                } else {
                    alert("Editor interface missing! Please ensure the Advanced Editor HTML was pasted into index.html.");
                }
            }
        });
        
        console.log("✅ Editor Button Successfully Hooked!");
    }

    // Force-fix the close button for the editor as well
    const closeBtn = document.getElementById('closeAdvEditorBtn');
    if (closeBtn) {
        const freshClose = closeBtn.cloneNode(true);
        closeBtn.parentNode.replaceChild(freshClose, closeBtn);
        freshClose.addEventListener('click', () => {
            const advModal = document.getElementById('advancedEditorModal');
            if (advModal) advModal.classList.remove('active');
            
            // Pause any playing videos when closed
            if (typeof pausePlayback === 'function') pausePlayback();
            if (typeof pauseNLE === 'function') pauseNLE();
        });
    }
}, 500); // 500ms delay ensures this runs AFTER all other scripts have finished loading
// =========================================================================
// ===================== CROP TOOL UI & BLUE SQUARE FIX ====================
// =========================================================================

setTimeout(() => {
    const cropOverlay = document.getElementById('advCropOverlay');
    const toggleCropBtn = document.getElementById('advToggleCropBtn');
    
    if (cropOverlay) {
        // 1. Instantly hide the rogue blue square
        cropOverlay.style.display = 'none';
        
        // Set a default centralized size for when it is activated
        cropOverlay.style.width = '50%';
        cropOverlay.style.height = '50%';
        cropOverlay.style.left = '25%';
        cropOverlay.style.top = '25%';
    }

    if (toggleCropBtn && cropOverlay) {
        // 2. Hook up the Toggle Crop Button
        let isCropActive = false;
        
        // Clone the button to wipe any frozen event listeners
        const freshToggleBtn = toggleCropBtn.cloneNode(true);
        toggleCropBtn.parentNode.replaceChild(freshToggleBtn, toggleCropBtn);
        
        freshToggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            isCropActive = !isCropActive;
            
            if (isCropActive) {
                // Show the crop tool UI
                cropOverlay.style.display = 'block';
                freshToggleBtn.style.backgroundColor = '#1e50a0'; 
                freshToggleBtn.innerHTML = '<i class="fas fa-check"></i> Apply Crop';
            } else {
                // Hide the crop tool and simulate "applying"
                cropOverlay.style.display = 'none';
                
                // Visual confirmation
                freshToggleBtn.style.backgroundColor = '#4caf50';
                freshToggleBtn.innerHTML = '<i class="fas fa-check-double"></i> Cropped!';
                
                setTimeout(() => {
                    freshToggleBtn.style.backgroundColor = '';
                    freshToggleBtn.innerHTML = '<i class="fas fa-crop"></i> Toggle Crop Tool';
                }, 1500);
            }
        });

        // 3. Make the Crop Overlay draggable and resizable
        let isDragging = false;
        let handle = null;
        let startX, startY, startRect;

        cropOverlay.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startRect = {
                left: cropOverlay.offsetLeft,
                top: cropOverlay.offsetTop,
                width: cropOverlay.offsetWidth,
                height: cropOverlay.offsetHeight
            };

            // Determine what part of the box was clicked
            if (e.target.classList.contains('tl')) handle = 'tl';
            else if (e.target.classList.contains('tr')) handle = 'tr';
            else if (e.target.classList.contains('bl')) handle = 'bl';
            else if (e.target.classList.contains('br')) handle = 'br';
            else handle = 'move';
            
            e.stopPropagation();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            if (handle === 'move') {
                cropOverlay.style.left = (startRect.left + dx) + 'px';
                cropOverlay.style.top = (startRect.top + dy) + 'px';
            } else if (handle === 'br') {
                cropOverlay.style.width = Math.max(20, startRect.width + dx) + 'px';
                cropOverlay.style.height = Math.max(20, startRect.height + dy) + 'px';
            } else if (handle === 'bl') {
                cropOverlay.style.width = Math.max(20, startRect.width - dx) + 'px';
                cropOverlay.style.left = (startRect.left + dx) + 'px';
                cropOverlay.style.height = Math.max(20, startRect.height + dy) + 'px';
            } else if (handle === 'tr') {
                cropOverlay.style.width = Math.max(20, startRect.width + dx) + 'px';
                cropOverlay.style.height = Math.max(20, startRect.height - dy) + 'px';
                cropOverlay.style.top = (startRect.top + dy) + 'px';
            } else if (handle === 'tl') {
                cropOverlay.style.width = Math.max(20, startRect.width - dx) + 'px';
                cropOverlay.style.height = Math.max(20, startRect.height - dy) + 'px';
                cropOverlay.style.left = (startRect.left + dx) + 'px';
                cropOverlay.style.top = (startRect.top + dy) + 'px';
            }
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            handle = null;
        });
    }
}, 1000); // 1000ms delay ensures this runs AFTER the HTML has fully injected into the page