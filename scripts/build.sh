#!/bin/bash
# Build the Chinese .dictionary bundles from sources/*.mdx|mdd.
# Needs: python3 with pyglossary, lxml, opencc; Apple's Dictionary Development Kit (DDK).
# Usage: DDK=/path/to/dictionary-development-kit scripts/build.sh [ids...]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DDK="${DDK:-$ROOT/ddk}"
[ -x "$DDK/bin/build_dict.sh" ] || { echo "Set DDK to Apple's Dictionary Development Kit (bin/build_dict.sh)"; exit 1; }

# id | title | source mdx names
DICTS=(
  "xinhua|新华字典|xinhua"
  "zdic|汉典|zdic"
  "kangxi|康熙字典|kangxi"
  "moe|重编国语辞典|moe"
  "idiom|成语典|idiom idiomapp"
  "bujian|汉字部件典|bujian"
)

W="$ROOT/build"; mkdir -p "$W"; cd "$W"
ln -sfn "$ROOT/sources" in
cp "$ROOT/styles/base.css" base.css
for spec in "${DICTS[@]}"; do
  IFS='|' read -r id title names <<<"$spec"
  if [ $# -gt 0 ] && [[ " $* " != *" $id "* ]]; then continue; fi
  echo "== $id ($title)"
  # shellcheck disable=SC2086
  PYTHONPATH="$ROOT/scripts" python3 "$ROOT/scripts/conv.py" "$id" "$title" $names
  # Use the final restyled CSS and plist as installed.
  cp "$ROOT/styles/$id.css" "out/$id/dict.css"
  cp "$ROOT/dicts/$id/dict.plist" "out/$id/dict.plist"
  (cd "out/$id" && "$DDK/bin/build_dict.sh" "$title" dict.xml dict.css dict.plist)
  echo "built $W/out/$id/objects/$title.dictionary"
done
echo "Install: cp -R build/out/<id>/objects/<name>.dictionary ~/Library/Dictionaries/"
