#!/usr/bin/env python3
"""The stream lane must accept a COMBINED live rendition.

Proved live: a 24/7 music-radio stream publishes ONE HLS rendition with
video and audio together and no separate audio rendition. The station
wanted hls_v AND hls_a, so it resolved to "unplayable" and skipped the
item -- and a music station's most obvious content could never play.

These are the argv shapes, checked offline (the resolve itself needs
YouTube and takes a minute).

Offline, stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import stream          # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL: %s" % msg)
    else:
        print("ok: %s" % msg)


def main():
    # the two-input shape: separate video and audio renditions
    two = {"hls_v": "http://v.m3u8", "hls_a": "http://a.m3u8"}
    check(not stream.spawnable(two) is False,
          "a stream with separate renditions is spawnable")

    # the combined shape: one rendition carrying both
    comb = {"hls_v": "http://v.m3u8", "hls_a": None, "hls_av": "http://av.m3u8"}
    check(stream.spawnable(comb),
          "a stream with only a COMBINED rendition is spawnable")

    # neither: not spawnable
    check(not stream.spawnable({"hls_v": None, "hls_a": None}),
          "a stream with no usable rendition is not spawnable")
    check(not stream.spawnable({}),
          "an empty meta is not spawnable")

    # the argv: the combined stream is ONE input, the split one is TWO
    av_argv = stream.spawn_argv(comb, "slot-stream-a")
    check(av_argv.count("-i") == 1,
          "the combined stream is fed to ffmpeg as ONE input (%d)" %
          av_argv.count("-i"))
    check("http://av.m3u8" in av_argv,
          "the combined stream's url is used")

    two_argv = stream.spawn_argv(two, "slot-stream-a")
    check(two_argv.count("-i") == 2,
          "the split stream is fed as TWO inputs (%d)" % two_argv.count("-i"))
    check("http://v.m3u8" in two_argv and "http://a.m3u8" in two_argv,
          "both rendition urls are used")

    # the timeout must be there: a dead upstream must not hold the frame
    for argv in (av_argv, two_argv):
        check("-rw_timeout" in argv,
              "the ffmpeg read timeout is set")

    print("=== FAILURES: %d ===" % len(fails))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
