"""Prove two independent HTTP clients can prepare a match, without opening the game."""
import argparse,json,threading
from pathlib import Path
try:
    from .rooms import Rooms
    from .server import Server
    from .client import Client
except ImportError:
    from rooms import Rooms
    from server import Server
    from client import Client
def team(catalog,species):
    return [dict(species=species,ability=catalog['species'][species]['abilities'][0],item=None,nature='HARDY',moves=['TACKLE'],evs=[0]*6,ivs=[31]*6,level=50) for _ in range(6)]
def run(catalog):
    rooms=Rooms(catalog);server=Server(('127.0.0.1',0),rooms)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        url='http://127.0.0.1:'+str(server.server_port)
        a=Client(url,rooms.fingerprint);b=Client(url,rooms.fingerprint)
        created=a.enter('Cliente A',team(catalog,'PIKACHU'));b.enter('Cliente B',team(catalog,'MAGIKARP'),created['room'])
        a.select([5,0,2,3]);b.select([1,2,3,4])
        left=a.state();right=b.state()
        assert left['state']==right['state']=='prepared'
        assert left['picks']==[5,0,2,3] and right['picks']==[1,2,3,4]
        assert not left['battleAvailable'] and not right['battleAvailable']
        return {'result':'PASS','roomState':'prepared','clients':2,'picksPerClient':4,'battleAvailable':False}
    finally:server.shutdown();server.server_close();thread.join(5)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--catalog',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(run(json.loads(args.catalog.read_text(encoding='utf8'))),indent=2))
