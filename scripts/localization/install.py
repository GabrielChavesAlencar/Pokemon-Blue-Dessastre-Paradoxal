"""Compile Blue's own locale table to a native Marshal resource, atomically upstream."""
import importlib.util,json,sys
from pathlib import Path
def plan(project,game):
    path=project/'data/pt-br.json'
    if not path.is_file():return {}
    data=json.loads(path.read_text(encoding='utf8'))
    if data.get('version')!=1 or data.get('language')!='pt-BR' or not isinstance(data.get('translations'),dict):raise ValueError('Invalid Portuguese locale.')
    if not all(isinstance(k,str) and isinstance(v,str) and v.strip() for k,v in data['translations'].items()):raise ValueError('Invalid locale entry.')
    spec=importlib.util.spec_from_file_location('blue_translation_controls',Path(__file__).with_name('catalog.py'))
    catalog=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalog)
    for source,target in data['translations'].items():catalog.validate(source,target)
    sys.path.insert(0,str(project))
    from server.ruby_marshal import dumps_simple
    return {game/'Data/blue-pt-br.dat':dumps_simple(sorted([k,v] for k,v in data['translations'].items()))}
