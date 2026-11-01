"""Small test client for protocol 1. No integration with the offline Hub yet."""
import json,urllib.error,urllib.request
from urllib.parse import urlsplit
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
class Client:
    def __init__(self,url,compatibility):
        parsed=urlsplit(url)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Invalid server URL.')
        self.url=url.rstrip('/');self.compatibility=compatibility;self.token=None;self.room=None
        self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        hello=self.request('GET','/v1/hello')
        if hello['protocol']!=1 or hello['compatibility']!=compatibility:raise ValueError('Server and local engine versions differ.')
    def request(self,method,path,data=None):
        headers={'Content-Type':'application/json'}
        if self.token:headers['Authorization']='Bearer '+self.token
        raw=None if data is None else json.dumps(data).encode()
        request=urllib.request.Request(self.url+path,raw,headers,method=method)
        with self.http.open(request,timeout=5) as response:
            body=response.read(65537)
            if len(body)>65536:raise ValueError('Response too large.')
            return json.loads(body)
    def enter(self,name,team,room=None):
        data={'protocol':1,'compatibility':self.compatibility,'name':name,'team':team}
        value=self.request('POST','/v1/rooms'+('/'+room+'/join' if room else ''),data)
        self.room=value['room'];self.token=value.pop('token');return value
    def state(self):return self.request('GET','/v1/rooms/'+self.room)
    def select(self,indices):return self.request('POST','/v1/rooms/'+self.room+'/select',{'picks':indices})
    def leave(self):return self.request('POST','/v1/rooms/'+self.room+'/leave',{})
