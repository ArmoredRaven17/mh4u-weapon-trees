# MH4U Weapon Trees

An interactive, in-browser map of every weapon upgrade tree in **Monster Hunter 4 Ultimate**: all
14 weapon classes (2,308 weapons), Charge Blade and Insect Glaive included, drawn as a tilted 2.5D map,
a flat 2D diagram, or a free-orbit 3D view. It's a port of the author's
[MHGU Weapon Trees](https://github.com/ArmoredRaven17/mhgu-weapon-trees), by way of its
[MH3U port](https://github.com/ArmoredRaven17/mh3u-weapon-trees).

Pick a class and a tree from the bottom bar, then click any weapon to see its full stats: attack,
affinity, slots, element (bracketed when it needs Awaken), sharpness (base and Sharpness +1), Hunting
Horn notes and songs, Gunlance shelling, Switch Axe and Charge Blade phials, the Insect Glaive's
Kinsect, bow charges, arc shot or Power Shot and coatings, and bowgun reload/recoil/deviation, ammo,
Rapid Fire (Light) and Crouching Fire (Heavy). It also shows the upgrade recipe, plus the forge recipe
where the smithy has one. You can tick weapons as **Made**, highlight made or unmade ones, and snip
branches out of the view. Snips and Made ticks are saved in your browser.

## How it differs from the MH3U app

The layout is the MH3U app's: no weapon levels, every node is one weapon keyed by the game's own id,
and each run of upgrades is one straight lane (the first upgrade the game lists carries the lane on;
any others branch off to the side). What's new for 4U:

- **Charge Blade and Insect Glaive**, with the CB's phial and the Kinsect a new glaive comes with.
- **Rapid Fire** (shots, wait, damage per shot) on Light Bowguns and **Crouching Fire** ammo on Heavy
  Bowguns, Blast ammo and coatings, and 4U's recoil and deviation wording.
- **Power Shot**: a bow carries either an arc shot or Power Shot in its place.
- **One weapon with two ways in.** Dios Katana upgrades from Wyvern Blade "Fall" and from Tigrine Edge.
  It's drawn under the first (the tracker's parent); both are listed in its panels, and Tigrine Edge
  lists it among its upgrades.
- The theme picker uses the MH4U apps' monster names and icons (same 31 colours).

## Where the data comes from

`docs/index.html` is a single self-contained page with no runtime fetches. Its data block is written by
[scripts/build.py](scripts/build.py) from sibling repos:

- **[mh4u-collection-tracker](https://github.com/ArmoredRaven17/mh4u-collection-tracker)** provides
  the weapon stats, recipes and upgrade links (`docs/data/`, which that repo reads from the game
  itself), the rarity-coloured weapon icons, note icons, monster theme icons, textures and font.
- **[mhgu-weapon-trees](https://github.com/ArmoredRaven17/mhgu-weapon-trees)** provides only the
  coating bottles, matched by colour, since 4U's own aren't decoded yet. Paint has no MHGU bottle, so
  it stays text.

```
python scripts/build.py
```

The build needs Python 3.10+ and Pillow. Both repos default to siblings of this one; pass paths to
override. Only the region between the `DATA:BEGIN` / `DATA:END` markers is rewritten. Edit the app
code in place. Rebuild whenever the tracker's data changes.

## Local development

```
python -m http.server 8136 --directory docs
```

You can also open `docs/index.html` directly, since nothing is fetched.

## Licensing

Code is MIT (see [LICENSE](LICENSE)). Game data and icons are Capcom's. See [NOTICE.md](NOTICE.md).
Monster Hunter 4 Ultimate is © Capcom Co., Ltd. This is an unofficial fan project.

Most of this project's code was written with [Claude Code](https://claude.com/claude-code), working
from the author's direction.
