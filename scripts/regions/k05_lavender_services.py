"""Source-anchored Lavender citizens and the authored, native Name Rater."""
from __future__ import annotations

import json
from audit import ROOT
from k04_gameplay import sprite
from kanto_overworld import source_npc_dialogue
from pilot import command, new_event

NPCS = {
    (93,10):((10,7),"People come to Lavender to remember their Pokémon.","Muita gente vem a Lavender para lembrar dos seus Pokémon."),
    (93,12):((12,12),"The road north leads back to Rock Tunnel.","O caminho ao norte volta para o Rock Tunnel."),
    (94,8):((9,4),"The Tower is just outside town. Rest here before going in.","A Torre fica logo ali. Descanse aqui antes de entrar."),
    (94,9):((5,6),"The road through Rock Tunnel can wear out a whole team.","A travessia do Rock Tunnel pode cansar a equipe toda."),
    (94,10):((2,2),"The Nurse will heal your party for free.","A enfermeira cura sua equipe de graça."),
    (95,3):((9,5),"Check your supplies before heading up the Tower.","Confira seus suprimentos antes de subir a Torre."),
    (95,6):((9,2),"I always bring something to treat status conditions.","Sempre levo algo para tratar problemas de status."),
    (95,7):((6,2),"Take a look at the clerk's stock before leaving.","Confira o estoque do balcão antes de sair."),
    (96,2):((4,4),"Lavender is usually a quiet town.","Lavender costuma ser uma cidade tranquila."),
    (98,4):((3,5),"Mr. Fuji looks after Pokémon that need a home.","O Sr. Fuji cuida de Pokémon que precisam de um lar."),
    (98,5):((7,2),"Pokémon of all kinds are welcome here.","Pokémon de todo tipo são bem-vindos aqui."),
    (98,7):((9,5),"Please let the Pokémon here rest.","Deixe os Pokémon daqui descansarem, por favor."),
}
RATER = (97,1)
RATER_AT = (4,4)


def verify_name_rater(report):
    rows=[r for r in report["actors"] if (r["source"],r["event"])==RATER]
    if (len(rows)!=1 or tuple(rows[0]["at"])!=RATER_AT or rows[0]["trigger"]!=0
            or not rows[0]["graphic"] or
            not {"pbChoosePokemon","foreign?"}<=set(rows[0]["native_nickname_calls"])):
        raise ValueError("K05 Name Rater source witness was not exact")


def add_services(source,target,donor,native,sid):
    originals, events=donor.attrs["@events"],native.attrs["@events"]
    added=[]
    for (src,eid),(xy,en,pt) in NPCS.items():
        if src!=sid: continue
        event=originals[eid]
        if tuple(event.attrs[k] for k in ("@x","@y"))!=xy or eid in events:
            raise ValueError(f"K05 passive Lavender actor moved: {sid}/{eid}")
        if not source_npc_dialogue(event):
            raise ValueError(f"K05 original Lavender actor is not passive: {sid}/{eid}")
        msg=f"pbMessage(BlueKantoPilot.t({json.dumps(en,ensure_ascii=False)}, {json.dumps(pt,ensure_ascii=False)}))"
        events[eid]=new_event(event,[command(355,msg.encode("utf8"))],0,sprite(source,target,event))
        added.append(eid)
    if sid==RATER[0]:
        eid=RATER[1]
        event=originals[eid]
        if eid in events or tuple(event.attrs[k] for k in ("@x","@y"))!=RATER_AT:
            raise ValueError("K05 original Name Rater moved")
        events[eid]=new_event(event,[command(355,b"BlueKantoLavender.name_rater")],0,sprite(source,target,event))
        added.append(eid)
    return added


def install_runtime(target):
    path=target/"Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
    field=(ROOT/"scripts/regions/KantoK05City.rb").read_bytes()
    path.write_bytes(path.read_bytes()+b"\n"+field.strip()+b"\n")
