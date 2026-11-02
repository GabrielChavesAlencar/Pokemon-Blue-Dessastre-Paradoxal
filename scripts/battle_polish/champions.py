"""Bounded engine patch: only Champions' full-paralysis roll; no copied engine."""
import sys,zlib
OLD='@status == :PARALYSIS && @battle.pbRandom(100) < 25'
NEW='@status == :PARALYSIS && @battle.pbRandom(8) == 0'
def plan(project,game):
    path=game/'Data/Scripts.rxdata'
    if not path.is_file():return {}
    sys.path.insert(0,str(project/'scripts/official_rules'))
    from prepare_restore import Marshal,RubyString,dump
    rows=Marshal(path.read_bytes()).read()
    matches=[r for r in rows if r[1]==b'Battler_UseMoveSuccessChecks']
    if not matches:return {} # Small installer fixtures may have only Main.
    if len(matches)!=1:raise ValueError('Ambiguous battle status script.')
    row=matches[0];source=zlib.decompress(row[2]).decode('utf-8-sig')
    if source.count(NEW)==1 and OLD not in source:return {}
    if source.count(OLD)!=1 or NEW in source:raise ValueError('Unsupported full-paralysis condition; no files changed.')
    row[2]=RubyString(zlib.compress(source.replace(OLD,NEW).encode('utf8')))
    return {path:b'\x04\x08'+dump(rows)}
