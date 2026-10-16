/* ============================================================
   Program return: true real-time program A/V over WHEP.
   The render plane streams program A/V to MediaMTX (lab profile service
   points at it); this module plays the monitor paths back with a vanilla
   RTCPeerConnection — no libraries, no plugins. Sub-second latency,
   independent of obs-websocket (survives control-channel flaps) and of
   the screenshot pipeline entirely.
   Two paths, tried in order: `monitor-av` (video + Opus audio — a tiny
   ffmpeg repackages the AAC because OBS ships no Opus encoder and Chrome
   won't play AAC over WebRTC), then plain `monitor` video-only. The pane
   starts muted (autoplay-safe); unmuting is a click = a real gesture.
   Signaling goes through the same-origin /whep proxy (overlay forwards
   the SDP to MediaMTX); ICE media flows direct, so this needs LAN/UDP
   between viewer and lab — same requirement as everything else here.
   ============================================================ */

const SESSIONS = new Set();

export function stopAllReturns() {
  for (const s of [...SESSIONS]) { try { s.stop(); } catch {} }
  SESSIONS.clear();
}

export function startReturn(videoEl, { onState } = {}) {
  const session = {
    pc: null, stopped: false, hasAudio: false,
    stop() {
      session.stopped = true;
      try { session.pc?.close(); } catch {}
      SESSIONS.delete(session);
      try {
        videoEl.pause();
        videoEl.removeAttribute('src');
        videoEl.srcObject = null;
      } catch {}
      onState?.(false);
    },
  };
  SESSIONS.add(session);

  (async () => {
    // LOCAL-PATCH (station): monitor-av first (sound included), plain
    // monitor as the video-only fallback. Whatever connects first wins;
    // a failure reports its reason once, not per path.
    const attempts = [
      { path: 'monitor-av', audio: true },
      { path: 'monitor', audio: false },
    ];
    let lastErr = null;
    for (const { path, audio } of attempts) {
      if (session.stopped) return;
      try {
        await connectPath(path, audio);
        return; // onState(true) fired on first frame track
      } catch (err) {
        lastErr = err;
        try { session.pc?.close(); } catch {}
        session.pc = null;
      }
    }
    if (!session.stopped) {
      onState?.(false, lastErr?.message || String(lastErr));
      session.stop();
    }
  })();

  async function connectPath(path, wantAudio) {
    const pc = new RTCPeerConnection();
    session.pc = pc;
    pc.addTransceiver('video', { direction: 'recvonly' });
    if (wantAudio) pc.addTransceiver('audio', { direction: 'recvonly' });
    const up = await new Promise((resolve, reject) => {
      const to = setTimeout(() => reject(new Error(`${path}: no media in 15s`)), 15000);
      pc.ontrack = (e) => {
        if (session.stopped || session.pc !== pc) return;
        try {
          const stream = e.streams[0];
          const hasV = stream.getVideoTracks().length > 0;
          videoEl.srcObject = stream;
          videoEl.play()?.catch?.(() => {});
          if (hasV) {
            session.hasAudio = stream.getAudioTracks().length > 0;
            clearTimeout(to);
            onState?.(true, null, { hasAudio: session.hasAudio, path });
            resolve(true);
          }
        } catch (err) { clearTimeout(to); reject(err); }
      };
      pc.onconnectionstatechange = () => {
        const s = pc.connectionState;
        if ((s === 'failed' || s === 'closed') && !session.stopped && session.pc === pc) {
          clearTimeout(to);
          reject(new Error(`${path}: ${s}`));
        }
      };
      (async () => {
        try {
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          const res = await fetch(`/whep?path=${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/sdp' },
            body: offer.sdp,
          });
          if (!res.ok) throw new Error(`${path}: signaling ${res.status}`);
          const answer = await res.text();
          if (session.stopped || session.pc !== pc) throw new Error('stopped');
          await pc.setRemoteDescription({ type: 'answer', sdp: answer });
        } catch (err) {
          clearTimeout(to);
          reject(err);
        }
      })();
    });
    return up;
  }

  return session;
}
