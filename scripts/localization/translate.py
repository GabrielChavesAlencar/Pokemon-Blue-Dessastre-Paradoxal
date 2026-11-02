"""Author-time offline translation. Players do not install/download any model."""
import argparse,json,re,time,collections
from pathlib import Path
from catalog import CONTROL,validate
def name_regex(values):
    trie={}
    for value in values:
        node=trie
        for char in value:node=node.setdefault(char,{})
        node['']=True
    def pattern(node):
        pieces=[re.escape(char)+pattern(child) for char,child in node.items() if char]
        tail='(?:'+'|'.join(pieces)+')' if len(pieces)>1 else ''.join(pieces)
        return '(?:'+tail+')?' if '' in node and tail else tail
    return r'(?<!\w)(?-i:'+pattern(trie)+r')(?!\w)'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True);parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--language-token',default='>>pob<<');parser.add_argument('--source-model',default='Helsinki-NLP/opus-mt-tc-big-en-pt')
    args=parser.parse_args()
    print('Loading offline runtime',flush=True)
    import ctranslate2,sentencepiece
    print('Loading catalog and tokenizers',flush=True)
    catalog=json.loads(args.catalog.read_text(encoding='utf8'))
    source=sentencepiece.SentencePieceProcessor(model_file=str(args.model/'source.spm'))
    target=sentencepiece.SentencePieceProcessor(model_file=str(args.model/'target.spm'))
    print('Loading translation weights',flush=True)
    translator=ctranslate2.Translator(str(args.model),device='cpu',compute_type='int8',inter_threads=1,intra_threads=4)
    print('Preparing protected names',flush=True)
    names=re.compile(name_regex(catalog['protected']))
    cache=json.loads(args.cache.read_text(encoding='utf8')) if args.cache.is_file() else {}
    for key,value in list(cache.items()):
        try:validate(key,value)
        except ValueError:del cache[key];continue
        if '\u2047' in value or '\ufffd' in value:del cache[key]
    protected=[];prepared={};fallbacks=[]
    # Controls stay outside the model. Names and substitution arguments use
    # validated markers; a conservative fragment fallback preserves every name.
    mask_pattern=re.compile(CONTROL.pattern+'|'+names.pattern,CONTROL.flags)
    def mask(value):
        tokens=[]
        def sub(m):tokens.append(m[0]);return 'X'+str(len(tokens)-1)+'X'
        return mask_pattern.sub(sub,value),tokens
    print('Preparing text batches',flush=True)
    for s in catalog['strings']:
        if s in cache:continue
        masked,tokens=mask(s)
        if not re.search('[A-Za-z]{2}',re.sub(r'X\d+X','',masked)):
            cache[s]=s;continue
        prepared[s]=(masked,tokens)
    encoded={s:[args.language_token]+source.encode(masked,out_type=str)+['</s>'] for s,(masked,_) in prepared.items()}
    keys=sorted(prepared,key=lambda s:len(encoded[s]));started=time.monotonic()
    print('Translating '+str(len(keys))+' strings',flush=True)
    for start in range(0,len(keys),24):
        batch=keys[start:start+24]
        inputs=[encoded[s] for s in batch]
        results=translator.translate_batch(inputs,beam_size=1,max_decoding_length=min(768,max(map(len,inputs))*2+24),max_input_length=1024,repetition_penalty=1.05)
        for s,result in zip(batch,results):
            value=target.decode(result.hypotheses[0]);masked,tokens=prepared[s]
            # Normalize harmless whitespace introduced inside copy markers.
            value=re.sub(r'X\s*(\d+)\s*X',lambda m:'X'+m[1]+'X',value,flags=re.I)
            markers=re.findall(r'X\d+X',value)
            expected=['X'+str(i)+'X' for i in range(len(tokens))]
            if collections.Counter(markers)!=collections.Counter(expected) or '\u2047' in value or '\ufffd' in value:fallbacks.append(s);continue
            for i,token in enumerate(tokens):value=value.replace(expected[i],token)
            try:validate(s,value)
            except ValueError:fallbacks.append(s);continue
            cache[s]=value
        if start%96==0:
            args.cache.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf8')
            print(f'TRANSLATED {start+len(batch)}/{len(keys)} elapsed={int(time.monotonic()-started)}s fallback={len(fallbacks)}',flush=True)
    # Translate unprotected fragments when a sentence's markers were not copied.
    # This guarantees that commands, variables, item/move/species names survive.
    split=re.compile('('+CONTROL.pattern+'|'+names.pattern+')',CONTROL.flags)
    fragments={}
    broken={}
    for s in fallbacks:
        parts=split.split(s);broken[s]=parts
        for i in range(0,len(parts),2):
            raw=parts[i];trim=raw.strip()
            if re.search('[A-Za-z]{2}',trim):fragments.setdefault(trim,None)
    fragments_keys=list(fragments)
    print('Translating protected fallback fragments: '+str(len(fragments_keys)),flush=True)
    for start in range(0,len(fragments_keys),24):
        batch=fragments_keys[start:start+24]
        results=translator.translate_batch([[args.language_token]+source.encode(s,out_type=str)+['</s>'] for s in batch],beam_size=1,max_decoding_length=512,max_input_length=1024)
        for s,r in zip(batch,results):fragments[s]=target.decode(r.hypotheses[0])
        if start%240==0:print(f'FRAGMENTS {start+len(batch)}/{len(fragments_keys)}',flush=True)
    for s,parts in broken.items():
        for i in range(0,len(parts),2):
            raw=parts[i];trim=raw.strip()
            if trim in fragments:parts[i]=raw[:len(raw)-len(raw.lstrip())]+fragments[trim]+raw[len(raw.rstrip()):]
        value=''.join(parts);validate(s,value);cache[s]=value
    args.cache.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf8')
    missing=set(catalog['strings'])-cache.keys()
    if missing:raise ValueError('Missing translations: '+str(len(missing)))
    for s in catalog['strings']:validate(s,cache[s])
    # Terminology fixes are conditional on the English source and do not touch names.
    for s in catalog['strings']:
        v=cache[s]
        if re.search(r'\bgym leader',s,re.I):v=re.sub('líder de ginástica','líder de ginásio',v,flags=re.I)
        if re.search(r'\bturns?\b',s,re.I) and not re.search(r'\b(left|right|around|into)\b',s,re.I):
            for old,new in [('na próxima volta','no próximo turno'),('a próxima volta','o próximo turno'),('nesta volta','neste turno'),('voltas','turnos')]:v=v.replace(old,new)
        validate(s,v);cache[s]=v
    data={'version':1,'language':'pt-BR','sourceModels':['Helsinki-NLP/opus-mt-tc-big-en-pt',args.source_model],'licenses':['CC-BY-4.0','Apache-2.0'],
          'engine':'CTranslate2 / int8 / Brazilian Portuguese','coverage':{'strings':len(catalog['strings']),'mapStrings':len(catalog['mapStrings']),'missing':0,'fragmentFallbacks':len(fallbacks)},
          'translations':{s:cache[s] for s in catalog['strings']}}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('DONE '+json.dumps(data['coverage']),flush=True)
if __name__=='__main__':main()
