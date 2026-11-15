"""Compile Blue locale and merge the verified, optional Kanto overlay.

No FRLG localization is copied into Decades unless Kanto is installed in the
same game directory. Base Decades translations always win on duplicate keys.
"""
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
    from server.ruby_marshal import dumps_simple,loads,text

    translations=dict(data['translations'])
    overlay=game/'Data/blue-kanto-locale.dat'
    proof=game/'Data/blue-kanto-install.json'
    if overlay.is_file() and proof.is_file():
        manifest=json.loads(proof.read_text(encoding='utf8'))
        if manifest.get('schema')!=1 or manifest.get('source')!='Essentials FRLG 21.1':
            raise ValueError('Unrecognized Kanto installation locale proof.')
        entries=loads(overlay.read_bytes())
        if not isinstance(entries,list):
            raise ValueError('Kanto locale must contain a Marshal array.')
        for pair in entries:
            if not isinstance(pair,list) or len(pair)!=2:
                raise ValueError('Malformed Kanto locale entry.')
            source,target=text(pair[0]),text(pair[1])
            if not source or not target:
                raise ValueError('Empty Kanto locale entry.')
            catalog.validate(source,target)
            translations.setdefault(source,target)

    return {game/'Data/blue-pt-br.dat':dumps_simple(sorted([k,v] for k,v in translations.items()))}
