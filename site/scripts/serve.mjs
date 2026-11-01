import http from 'node:http';
import {readFile, stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../dist');
const port=Number(process.env.PORT ?? 4173);
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.wav':'audio/wav'};
http.createServer(async(req,res)=>{
  try {
    const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    let target=path.resolve(root,'.'+name);
    if (target!==root && !target.startsWith(root+path.sep)) {res.writeHead(403).end();return;}
    let exists=false;try{exists=(await stat(target)).isFile();}catch{}
    if (!exists) {
      if (path.extname(name)) {res.writeHead(404).end('Not found');return;}
      target=path.join(root,'index.html');
    }
    res.writeHead(200,{'Content-Type':mime[path.extname(target)]??'application/octet-stream','Cache-Control':'no-store'});
    res.end(await readFile(target));
  }catch{res.writeHead(500).end('Erro ao abrir o portal.');}
}).listen(port,'127.0.0.1',()=>console.log(`Local: http://127.0.0.1:${port}`));
