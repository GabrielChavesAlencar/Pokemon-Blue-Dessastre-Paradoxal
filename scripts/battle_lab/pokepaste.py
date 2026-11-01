"""Bounded HTTPS download worker. Native engine HTTP APIs must not run on Ruby threads."""
from pathlib import Path
import os,re,sys,urllib.error,urllib.request
LIMIT=65536
def normalize(raw):
    match=re.fullmatch(r'https://(?:pokepast\.es|pokepast-es\.translate\.goog)/([a-f0-9]{16})(?:/raw)?/?(?:\?[^\s#]*)?',raw.strip(),re.I)
    if not match:raise ValueError('Use um link HTTPS valido do Pokepaste.')
    return 'https://pokepast.es/'+match[1].lower()+'/raw'
class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # The service needs no cross-origin redirects or arbitrary URL fetches.
        return super().redirect_request(req,fp,code,msg,headers,normalize(newurl))
def download(raw):
    request=urllib.request.Request(normalize(raw),headers={'User-Agent':'BlueBattleHub/1.1','Accept':'text/plain'})
    with urllib.request.build_opener(SafeRedirect).open(request,timeout=20) as response:
        if response.status!=200:raise ValueError('O Pokepaste respondeu com erro HTTP.')
        content=response.read(LIMIT+1)
    if not 0<len(content)<=LIMIT:raise ValueError('Pokepaste vazio ou maior que 64 KB.')
    text=content.decode('utf-8-sig')
    if '<html' in text[:512].lower() or '<!doctype' in text[:512].lower():raise ValueError('O servidor retornou uma pagina em vez do texto do time.')
    return text
def run(raw,destination):
    try:result='OK\n'+download(raw)
    except (OSError,ValueError,urllib.error.URLError) as error:result='ERROR\nNao foi possivel baixar o Pokepaste: '+str(error)+'. Copie o texto do time ou tente novamente.'
    temporary=destination.with_name(destination.name+'.tmp')
    temporary.write_text(result,encoding='utf8');os.replace(temporary,destination)
if __name__=='__main__':run(sys.argv[1],Path(sys.argv[2]))
