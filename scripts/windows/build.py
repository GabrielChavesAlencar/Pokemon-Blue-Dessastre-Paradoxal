"""Build the two Windows launchers using the compiler included with Windows/.NET."""
from pathlib import Path
import json,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
def build(root=ROOT):
    compiler=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    output=root/'dist';output.mkdir(exist_ok=True)
    source=root/'scripts/windows'
    references=['System.Windows.Forms','System.Drawing','System.Web.Extensions','System.IO.Compression','System.IO.Compression.FileSystem']
    for mode,name in [('STORY','Blue-Story.exe'),('HUB','Blue-Battle-Hub.exe')]:
        exe=output/name
        subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64','/define:'+mode,'/out:'+str(exe),
                        '/resource:'+str(source/'dependencies.json')+',dependencies.json',
                        *['/r:'+r+'.dll' for r in references],str(source/'Bootstrap.cs')],check=True)
        with tempfile.TemporaryDirectory() as tmp:
            report=Path(tmp)/'result.json'
            subprocess.run([str(exe),'--self-test',str(report)],check=True,timeout=30)
            result=json.loads(report.read_text());assert result['ok'] and result['mode']==mode.lower(),result
        print(name,exe.stat().st_size,'bytes; self-test PASS')
if __name__=='__main__':build()
