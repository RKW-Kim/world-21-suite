/* ============================================================
   Program return: true real-time program video over WHEP.
   The render plane streams program A/V to MediaMTX (lab profile service
   points at it); this module plays the monitor path back with a vanilla
   RTCPeerConnection — no libraries, no plugins. Sub-second latency,
   independent of obs-websocket (survives control-channel flaps) and of
   the screenshot pipeline entirely.
   Video-only transceiver: the AAC program audio is not WebRTC-playable
   in Chrome, so we don't subscribe to it. Mixer meters cover audio.
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
    pc: null, stopped: false,
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
    try {
      const pc = new RTCPeerConnection();
      session.pc = pc;
      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.ontrack = (e) => {
        if (session.stopped) return;
        try {
          videoEl.srcObject = e.streams[0];
          videoEl.play()?.catch?.(() => {});
          onState?.(true);
        } catch {}
      };
      pc.onconnectionstatechange = () => {
        const s = pc.connectionState;
        if (s === 'failed' || s === 'disconnected' || s === 'closed') {
          if (session.stopped) return;
          onState?.(false, s);
          session.stop();
        }
      };
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      const res = await fetch('/whep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: offer.sdp,
      });
      if (!res.ok) throw new Error(`signaling ${res.status}`);
      const answer = await res.text();
      if (session.stopped) return;
      await pc.setRemoteDescription({ type: 'answer', sdp: answer });
    } catch (err) {
      if (!session.stopped) {
        onState?.(false, err?.message || String(err));
        session.stop();
      }
    }
  })();

  return session;
}
