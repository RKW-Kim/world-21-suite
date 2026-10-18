"""Cycle-seam shuffle for the station playlist.

Adopted from obs-media-playlist-source's shuffler.c (and upstream from
VLC's playlist/randomizer.c) — the user-visible rule that module exists
to enforce is: when a shuffled cycle ends and the next one begins, the
first items of the new cycle must not repeat the last items of the
previous one (NOT_SAME_BEFORE >= 1 at the seam). Our daemon plays the
persisted items array sequentially, so the array order IS the play
order and this single rule is the adoptable part; the full darray
history machinery only matters for their in-UI prev/select, which we
do not have.

https://github.com/videolan/vlc/blob/f7bb59d9f51cc10b25ff86d34a3eff744e60c46e/src/playlist/randomizer.c
"""
import random

NOT_SAME_BEFORE = 1


def item_key(item):
    """Stable identity across /library edits: catalog id, else path."""
    return item.get("id") or item.get("file") or item.get("url")


def reshuffle(items, last_keys=()):
    """Fisher-Yates shuffle honoring the VLC seam rule.

    `last_keys`: identity of the final items of the just-ended cycle.
    Returns the same list object, shuffled in place.
    """
    random.shuffle(items)
    if len(items) <= NOT_SAME_BEFORE:
        return items
    avoid = {k for k in last_keys if k is not None}
    if not avoid:
        return items
    band = [
        j for j in range(NOT_SAME_BEFORE, len(items))
        if item_key(items[j]) not in avoid
    ]
    if not band:
        return items  # every unconstrained slot duplicates an avoid key
    for head in range(min(NOT_SAME_BEFORE, len(items))):
        if item_key(items[head]) not in avoid:
            continue
        victim = random.choice(band)
        items[head], items[victim] = items[victim], items[head]
        band.remove(victim)  # that slot now holds an avoid item
    return items


def cycle_last_keys(items, count=NOT_SAME_BEFORE):
    """Identities of the final `count` items of a cycle."""
    out = []
    for item in items[-count:]:
        key = item_key(item)
        if key is not None:
            out.append(key)
    return out
