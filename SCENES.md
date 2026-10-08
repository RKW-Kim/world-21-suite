# The SmileTV scenes — production notes

Written to be read aloud or scrolled on a teleprompter. Every section is
self-contained, so you can jump straight to the scene you are about to put on
air.

These notes used to live inside `overlay/deck.html`. They moved here so the
deck could become a small launcher instead of carrying six long documents in
its source.

---

## Before you put anything on air

### Yellow means live

`#FFC107` is not a decoration. It is the channel's signal colour: a live dot,
a hot mic, a bar at full. It appears only when the state it describes is
genuinely active.

This is why the off-air card contains no yellow and no glow. If a dead-air
screen contains one lit yellow pixel, someone glancing at Program can misread
the state. Television never accidentally broadcast a green room because the
standby slate was designed as a genuinely different visual state.

### Scenes and modules are different animals

| | Scenes | Modules |
|---|---|---|
| Examples | starting, tech-diff, q&a, offair, meet, end-credits | ticker, watermark, speaking |
| Count | 9 painted scenes | 4 transparent overlays |
| Background | paints its own, always dark | must be see-through |
| Placed on | its own OBS source | layered on top of a scene |

If a module paints a background it becomes a dark rectangle in OBS and covers
the show. Never layer a scene and a module into one source.

### The frame is fixed

Every scene is exactly 1920 by 1080. That is OBS's canvas, not a resolution
preference.

The bottom 76 pixels are reserved on every scene for the ticker module, which
is precisely 1920 by 76. The top-left corner is reserved for the watermark.
Content may never enter those zones.

There is no responsive design here because there is only one layout.

### Everything is a standalone file

No build step. No framework. No runtime dependency. No install step. Edit the
file, reload in OBS, the change is on air.

That constraint is why no scene can use React, Tailwind, or a carousel library.
It would break the reload-and-it-is-live promise.

---

## The shape of a show

The six scenes in the deck are in presentation order, and that order is the
run of show:

    starting → tech-diff → meet → q&a → tech-diff → end-credits → offair

Before anything, open a segment, carry a video, engage the audience, open
another segment, run the tail, then the real end.

A typical episode: hold on **starting** while people sort out audio and
cameras. Go live to a face. Cut to **tech-diff** to open a segment. If there
is a recorded piece or a meeting, **meet**. Then **q&a** while the audience
talks. More segments. Then **end-credits** for the last few minutes. Then, and
only then, **offair**.

One rule the whole kit enforces: never cut to a holding or off-air state in
the middle of a show. It reads as an error, not as politeness.

---

## 1. Starting

File: `overlay/starting.html`

### What it is

The screen that sits on Program before anyone is talking. Broadcast calls this
a holding screen, a countdown, or a slate.

### What it is for

- Filling dead air. Ten minutes of black reads as broken. This reads as "we
  start at nine".
- Absorbing the awkward minute. The gap between "the show starts now" and
  someone actually talking — camera warm-up, audio check, waiting for the
  third person to join.
- Setting tone. The visual identity of the channel is established here before
  a single word is spoken.
- Being a natural loop. If it runs longer than planned it can sit for hours.

### When to use it

The ten minutes before you go live, and only before you go live.

### What the viewer should get

We arrived at a real place, and it is accounted for. Not: this stream is
broken.

### What is on screen, and why

- **The headline.** The largest type in the entire kit, deliberately. A holding
  screen has one job and must carry exactly one idea. It animates in word by
  word, each word filled with a vertical gradient, pale grey into darker grey,
  with the final word in gold and a soft glow. Grey first, gold last, so the
  eye lands on the word carrying the meaning.
- **Clock and date.** Small, tabular-figured, never competing. They exist to
  be available, not to be read. Tabular figures matter: a clock whose digits
  jitter as numbers swap is genuinely hard to read.
- **The logo, above the headline.** Never beside it. Two focal points on a
  holding screen read as a mistake.
- **Everything centred on one axis.** Same reason.

### Controls

`?title=` replaces the headline words. `?date=` the date line. `?scale=` from
0.4 to 1.6 resizes the mark. One gated interval drives the clock and nothing
else.

### What goes wrong

Cutting to it mid-show. It reads as an error.

---

## 2. Tech diffs

File: `overlay/tech-diff.html`

### What it is

The title card that opens a recurring segment, with a bar that fills as you
talk through it.

The pattern is borrowed from software. A diff is what changed between one
version and the next. This card names the change and runs a bar to full.

### What it is for

- Naming the thing. When a team ships something every week, "we shipped X"
  needs a consistent home or it gets lost in a chat thread.
- Showing progress without a slide deck. You talk; the card holds the title.
- Marking completion. A segment that fills its bar is finished. A segment still
  filling is in progress. Audiences learn this in one show.
- Being teachable structure. The same frame every week means the regular viewer
  knows what is happening without being told.

### When to use it

Every time you start a named thing. A feature shipped. A fix. A topic. The
moment the subject changes is the moment you cut to this.

### What the viewer should get

We are now in a defined section, and I will know when it is done.

### What is on screen, and why

- **The headline**, same gradient-clip treatment as the opening slate. Grey
  words, one gold word carrying the emphasis, plus the glow. Same grammar,
  same channel.
- **The bar.** Thin, horizontal, reads left to right, and fills once over the
  whole length of the segment rather than per word, so a long discussion does
  not make it strobe.
- **Sentence case throughout.** "Minor technical difficulties", not "Minor
  Technical Difficulties".

The bar is the segment's clock. It is the only element telling the viewer how
much is left.

### Controls

None. It is a fixed card. Repeat a segment by reloading the file.

### What goes wrong

- Putting a bullet list on it. Then it becomes a slide deck and people read
  instead of listening.
- Starting a new card mid-sentence. The bar restarting mid-thought breaks the
  "section finished" contract.
- A different card every week. The repetition is the value.

Keep it on screen for the whole segment. It is the segment's anchor, not an
intro you cut away after two seconds.

---

## 3. Q and A

File: `overlay/q%26a.html`

Note the escaped ampersand in the filename. Browsers serve the file as
`q%26a.html`; that is deliberate, not a typo.

### What it is

A live, working chat overlay. The engagement layer.

Not a picture of a chat. A real one. Messages arrive, move through the field,
and age out.

### What it is for

- Proving the channel is alive at any hour. Movement on screen while nobody is
  talking is the strongest possible "we are on" signal.
- Making the audience part of the programme. The viewer list is the product.
- Handling questions without a producer. Questions arrive sorted by tier rather
  than by who shouted loudest.
- Filling the frame during dead air. Cheaper and better than a holding screen,
  because it looks like content.

### When to use it

Whenever you want the audience talking. After a segment, during a gap, any time
the show benefits from audience energy.

It also runs unattended. It is a scene that fills the frame and looks like
content while doing it.

### What the viewer should get

I am in this room. My message, on screen, with my name.

### The central design claim

Participation is recorded. Every message carries a handle, and the handle is
styled — bronze, silver, gold — so a contribution leaves a visible mark that
does not scroll away with the message. That is the difference between a chat
overlay and a comment section.

### What is on screen, and why

- **Bubbles.** Dark, so they never compete with the face or the headline. Each
  has a thin platform-coloured outline and a matching tail, so messages read as
  belonging to a platform without a logo being needed.
- **Handles.** Metallic vertical gradient, bronze, silver, gold. No medal icon.
  Colour and material carry the tier; an icon would cheapen it.
- **The face.** The calm centre. It breathes slowly, and nothing else on the
  scene moves larger than a bubble. Movement that competes with reading is
  movement that destroys reading.
- **Depth is varied.** Some bubbles behind the face, some in front, some half
  off the edge. A flat grid of identical cards reads as a spreadsheet.
- **Bubbles rise from the bottom on a stagger, hold, and leave**, so the scene
  never sits perfectly still. The travel window is deliberately bounded: the
  headline block owns the top of the picture, so a card is fully transparent
  before it reaches the call to action.

### Controls

`?scale=` from 0.4 to 1.6. Runs silently with no parameters.

### What goes wrong

- Fake chat. Static screenshots of chat are the oldest trick in streaming, and
  audiences now read them as dishonest.
- Showing the chat but never reading it. Visible-and-ignored chat is worse than
  no chat, because it tells people their words do not matter.
- Too much motion. Every message animating hard fights the reading.
- Blocking the face. The face is the anchor; anything crossing it reads as a
  mistake.

---

## 4. Off air

File: `overlay/offair.html`

### What it is

The screen shown when the channel is not broadcasting. Broadcast engineers call
this a standby slate or a dead air card.

This is the one scene that is a safety state, not an entertainment state. That
distinction drives every choice in it.

### What it is for

- Making the transition safe. If the last thing on Program was a captured
  meeting window — a video call with a join code visible in it — and anyone
  hits start streaming, or OBS is left encoding, that room goes out to the
  internet. Switching to this scene is a one-action fix that removes an entire
  class of accident.
- Telling viewers the channel still exists. A branded dead-air screen is
  infinitely better than black. It is the difference between offline and
  broken.
- Advertising the next session. A clock and a countdown mean the dead screen is
  still doing work.

### When to use it

The moment the programme genuinely ends.

And whenever you are about to do something risky. That is the reason this scene
exists at all.

### What the viewer should get

We are off, not broken. Here is when we are back.

### What is on screen, and why

- **Nothing yellow, nothing glowing.** Rule one, applied absolutely. This is
  the single most important rule on the scene.
- **The same design language as the opening slate, with the lights down.** Same
  dot field, same gradients, same type. It still reads as the same channel,
  just switched off.
- **Hardware, not a headline.** A plug, mated and apart, on a loop. No words do
  that work, because words describing absence are still words competing for
  attention.
- **A clock and countdown** to the next session. A branded dead-air screen is
  better than black, and this is the difference between offline and broken.
- **An explicit message**: not transmitting, safe to leave on Program.

### Controls

`?next=21:00` counts down to the next occurrence, read as local time.
`?next=2026-10-06T21:00` stamps a full local wall clock. `?note=` replaces the
safety line.

Local time on purpose. A UTC stamp here would silently miscount by hours, which
is the worst possible failure in the one scene you must be able to trust.

### What goes wrong

- Any accent colour that means live elsewhere.
- Ambient life. No carousels, no about-to-start animations.
- A countdown that goes negative or wraps. Past the target it should say the
  session should be open, not count down into negatives.
- Leaving it on for hours. It is a safety state, not a filler.

---

## 5. Meet

File: `overlay/meet.html`

### What it is

A full-frame video surface with the channel's furniture floating over it.

Whatever the video is — a meeting, a screen share, a recorded piece — it becomes
part of the channel rather than a window opened on someone's desktop.

### What it is for

- Turning a working meeting into a broadcast. Same room, same people, same
  conversation, but it looks like a channel instead of a video call.
- Carrying every video in the set. Authored sets play through in order, so the
  scene can run unattended for a whole block.
- Filling the schedule between live segments.
- Not looking like a browser tab. The chrome is what separates a stream from
  someone sharing their screen.

### When to use it

Any time the show needs video: a live meeting, a screen share, a recorded
segment, talking-head pieces, anything filling the schedule between live
segments.

### What the viewer should get

This is a production. Not: someone is sharing their screen.

This is the scene that does the heaviest lifting for the least work. The same
file handles every video you will ever show, because the content lives in a
URL, not in the layout.

### What is on screen, and why

- **The player chrome is off.** No progress bar, no suggested-video end cards,
  no platform watermark. Nothing on screen belongs to the video player. That is
  the premium detail. The channel's furniture replaces all of it.
- **The mark, with a scrim behind it.** It sits over live video where contrast
  is not guaranteed. Over flat colour it would not need one; over a white slide
  it would otherwise disappear.
- **The ticker strip**, inset from the left and running full width, so it reads
  as broadcast furniture rather than a web element.
- **Nothing much moves.** Over moving video, animated chrome competes with the
  content and reads as a screensaver.

### Controls

`?pl=` picks the set: hdf, menta, almond, or all. `?yt=` takes a single video
URL or id and overrides the set. `?start=` is an offset in seconds, measured to
break autoplay — leave it at 0. `?vol=` is 0 to 100, default 50. `?mute=1`
starts muted. `?ctl=1` restores the player controls. `?lab=` and `?cap=`
override the label and the subtitle.

Keys: PageUp and PageDown skip the set, Space plays.

### Two defaults that are deliberate

**Volume is half and unmuted.** This is the single most common complaint about
streaming scenes: an audience cannot tell muted from broken. Browsers block
audible autoplay, so the frame sits muted until you press a key, then comes up
at half.

**Captions are off by default.** Captions on an already-quiet room is a fight
nobody needs. Turn them on deliberately for silent footage.

### What goes wrong

- Player controls over channel furniture. Two competing transport bars read as
  a cheap screen share.
- Autoplay blocked. If you see a dead play button, nothing is wrong with the
  video. Press any key.
- Bright chrome over bright content. The scrim exists for exactly this.
- Stretching a 4 by 3 source into a 16 by 9 frame. Let the player letterbox
  inside the frame. It looks like broadcast video; the stretch does not.

---

## 6. End credits

File: `overlay/end-credits.html`

### What it is

The card the channel rests on, with a credits roll.

Two halves: a farewell with a call to action, and a panel that names everyone
involved.

### Why it exists at all

The credits roll is borrowed from film and television, where the names are the
point — a hundred people made the thing and the audience is being told their
names.

Online that habit has mostly been lost. Putting it back does two things. It
credits people who are rarely credited, and it makes the channel feel like a
production rather than a webcam.

### What it is for

- Closing on the call to action. The last thing on screen should be the one
  thing you want remembered, not the credits.
- Naming the people who did the work. This is the motivation engine. Being
  named on the end card is a real, visible, permanent acknowledgement.
- Signalling that this was a complete show. Without an end card a stream just
  stops. With one, it finished.
- Filling the tail. The minutes after the last person says goodbye.
- Driving the follow. Notifications, next session, where to go next.

### When to use it

The last few minutes of the programme, after the real content has ended.

### What the viewer should get

That was a real show made by real people, and here is where to go next.

### What is on screen, and why

- **Headline**, same gradient treatment as every other scene: grey words, one
  gold word carrying the meaning, soft glow. One visual language across the
  whole kit.
- **Names, set large.** This panel is read, not glanced at.
- **Roles small, uppercase, wide-tracked, grey.** Names dominate, titles
  support. Getting this backwards makes the card look like a directory.
- **A completion bar**, deliberately repeating the segment idiom from
  tech-diff, so the whole kit has one visual language for finished.
- **The call to action** under the headline, brighter than anything else, and
  the last thing the eye lands on.
- **The channel signature** small and low, the way a station ident does.

### Controls

None. It is a fixed card and should never need updating.

### What goes wrong

- Generic credits. "Production team", "editing", "special thanks" with no names
  is worse than no credits, because it looks like a template nobody filled in.
- The same six people every time. Rotate the board.
- A roll too fast to read. If it cannot be read, it is decoration.
- Credits over the call to action. The call to action is what converts.
- Leaving it running all night. Cut to offair when the programme genuinely
  ends. The end card is for the tail.

---

## What every scene shares

**One easing curve.** A hard exponential ease-out: fast commit, long settle. If
a scene eases in a different shape, there must be a reason.

**Two families of shadow, strictly separated.** Black ambient shadow is depth,
lifting a surface off the canvas. Yellow glow is a live state. A glow is a
sentence with a subject. If you cannot name the live state it describes, it is
decoration and it comes out.

**No canvas and no requestAnimationFrame.** Every animation is compositor CSS:
transform and opacity only. Rasterise once, then move it on the GPU.

**Reduced motion is a real state on every page**, not a half-finished
animation.

**Legibility under video compression is an accessibility requirement.** The
viewer may be on a five-inch phone or a hundred-inch television and nobody
knows which. So: nothing below about 9 pixels, 11 pixels is the practical
floor for anything carrying meaning, weight 600 minimum on labels that must be
read, and tabular figures on every number that changes in place.

**Flat vector, no 3D**, with one deliberate exception: the credits deck now
uses perspective.

---

## Quick reference

| Scene | Reach for it when |
|---|---|
| starting | Before you go live. Never mid-show. |
| tech-diff | The subject changes. Holds for the whole segment. |
| q&a | You want the audience talking, or you need the frame alive. |
| offair | The programme ended, or you are about to do something risky. |
| meet | Any video at all: meeting, screen share, recorded piece. |
| end-credits | The tail, after the real content has ended. |

Then: cut to offair. Do not leave the end card running all night.