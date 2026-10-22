# mac-dictionaries

Dictionaries for macOS Dictionary.app (and [Vocab](https://github.com/vangie/vocab)).

Ready-to-install bundles are on the [Releases](../../releases) page. Unzip and move the `.dictionary`
folder to `~/Library/Dictionaries/`, then enable it in Dictionary.app › Settings.

## Chinese (built here)

| Bundle | ID | Source MDX |
|---|---|---|
| 新华字典 | `com.vangie.cndict.xinhua` | `xinhua` |
| 汉典 | `com.vangie.cndict.zdic` | `zdic` |
| 康熙字典 | `com.vangie.cndict.kangxi` | `kangxi` (+ images from `kangxi.mdd`) |
| 重编国语辞典 | `com.vangie.cndict.moe` | `moe` |
| 成语典 | `com.vangie.cndict.idiom` | `idiom` + `idiomapp` |
| 汉字部件典 | `com.vangie.cndict.bujian` | `bujian` |

Source data: [lxs602/Chinese-Mandarin-Dictionaries](https://github.com/lxs602/Chinese-Mandarin-Dictionaries) @ `9364952`.

Traditional-script dictionaries (重编国语辞典, 成语典, 康熙字典) also index Simplified forms (OpenCC t2s).
Styles follow the system appearance (light/dark).

### Layout

```
sources/   raw .mdx/.mdd (Git LFS)
scripts/   conv.py (MDX -> DDK XML), pre.py (per-dictionary cleanup), peek*.py (inspection), build.sh
styles/    base.css and the final per-dictionary CSS (as installed)
dicts/     per-dictionary Info plist
```

### Build

Requires Python 3 with `pyglossary`, `lxml` and `opencc`, plus Apple's Dictionary Development Kit
(from *Additional Tools for Xcode*).

```sh
git lfs pull
pip install pyglossary lxml opencc
DDK=/path/to/Dictionary\ Development\ Kit scripts/build.sh          # all
DDK=... scripts/build.sh xinhua kangxi                                # some
```

Output: `build/out/<id>/objects/<名称>.dictionary`.

## English (release assets only)

LDOCE5, Longman5_Extras and Macmillan2: prebuilt bundles, attached to the release as-is.
