using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

// Two small launchers share one installation. Dependencies are private and portable.
internal static class Bootstrap {
    const string Repo="GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal";
#if HUB
    const bool Hub=true;
#else
    const bool Hub=false;
#endif
    static string Root,LogPath; static Action<string> Status=delegate {};
    static readonly object LogLock=new object();
    static readonly JavaScriptSerializer Json=new JavaScriptSerializer { MaxJsonLength=4000000 };
    static Dictionary<string,object> Manifest;
    static int Main(string[] args) {
        ServicePointManager.SecurityProtocol=SecurityProtocolType.Tls12;
        try {
            if(args.Length==2 && args[0]=="--self-test") { SelfTest(args[1]);return 0; }
            if(!Environment.Is64BitOperatingSystem)throw new Exception("Este download requer Windows de 64 bits.");
            Root=FindRoot();
            for(int i=0;i+1<args.Length;i++)if(args[i]=="--root")Root=Path.GetFullPath(args[i+1]);
            Directory.CreateDirectory(Path.Combine(Root,".blue-work"));LogPath=Path.Combine(Root,".blue-work","launcher.log");
            using(var stream=typeof(Bootstrap).Assembly.GetManifestResourceStream("dependencies.json"))
            using(var reader=new StreamReader(stream))Manifest=Json.Deserialize<Dictionary<string,object>>(reader.ReadToEnd());
            int runtimeTest=Array.IndexOf(args,"--runtime-test");
            if(runtimeTest>=0 && runtimeTest+1<args.Length) {
                string py=Runtime("python","python.exe"),git=Runtime("git",Path.Combine("cmd","git.exe"));
                Run(py,new[]{"--version"},Path.GetDirectoryName(git));Run(git,new[]{"ls-remote","https://github.com/"+Repo+".git","refs/heads/main"},Path.GetDirectoryName(git));
                if(File.Exists(Path.Combine(Root,"scripts","official_rules","restore.py")))Run(py,new[]{"scripts/official_rules/restore.py","--help"},Path.GetDirectoryName(git));
                if(File.Exists(Path.Combine(Root,"server","ruby_marshal.py")))Run(py,new[]{"-c","import server.ruby_marshal"},Path.GetDirectoryName(git));
                File.WriteAllText(args[runtimeTest+1],Json.Serialize(new { ok=true,python=py,git=git }));return 0;
            }
            bool held;using(var mutex=new Mutex(true,"Local\\PokemonBlueDessastreParadoxalLauncher",out held)) {
                if(!held)throw new Exception("Outro inicializador esta aberto. Feche-o antes de atualizar.");
                if(Array.IndexOf(args,"--prepare-only")>=0) { Prepare();return 0; }
                Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
                using(var form=new Form { Text=Hub?"Pokemon Blue - Hub de Batalha":"Pokemon Blue - Historia",ClientSize=new Size(620,230),StartPosition=FormStartPosition.CenterScreen }) {
                    var title=new Label { Text="Preparando sua instalacao...",Left=24,Top=24,Width=570,Height=36,Font=new Font("Segoe UI",15) };
                    var info=new Label { Text="Conferindo a versao atual da main.",Left=24,Top=76,Width=570,Height=90,Font=new Font("Segoe UI",10) };
                    var bar=new ProgressBar { Left=24,Top=180,Width=570,Height=20,Style=ProgressBarStyle.Marquee };
                    form.Controls.AddRange(new Control[]{title,info,bar});
                    Status=delegate(string s) { if(!form.IsDisposed)form.BeginInvoke((Action)delegate { info.Text=s; }); };
                    form.Shown+=async delegate {
                        try { await Task.Run((Action)Prepare);title.Text="Tudo pronto. Abrindo o jogo...";
                            string game=Path.Combine(Root,"game");var process=Process.Start(new ProcessStartInfo(Path.Combine(game,"Game.exe")){WorkingDirectory=game,UseShellExecute=true});
                            form.WindowState=FormWindowState.Minimized;
                            await Task.Run(delegate { process.WaitForExit(); });form.Close();
                        } catch(Exception error) { bar.Style=ProgressBarStyle.Continuous;title.Text="A instalacao precisa de atencao";info.Text=error.Message+"\nLog: "+LogPath;MessageBox.Show(form,info.Text,"Pokemon Blue"); }
                    };
                    Application.Run(form);
                }
            }
            return 0;
        } catch(Exception error) { if(LogPath!=null)File.AppendAllText(LogPath,error+Environment.NewLine);if(Array.IndexOf(args,"--prepare-only")<0 && Array.IndexOf(args,"--runtime-test")<0)MessageBox.Show(error.Message,"Pokemon Blue");return 1; }
    }
    static string FindRoot() {
        string folder=AppDomain.CurrentDomain.BaseDirectory;
        for(int i=0;i<3 && folder!=null;i++,folder=Path.GetDirectoryName(folder.TrimEnd(Path.DirectorySeparatorChar)))
            if(File.Exists(Path.Combine(folder,"scripts","install_game.py")) && Directory.Exists(Path.Combine(folder,"game")))return folder;
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"PokemonBlueDessastreParadoxal");
    }
    static void Say(string text) { lock(LogLock)File.AppendAllText(LogPath,DateTime.Now.ToString("s")+" | "+text+Environment.NewLine);Status(text); }
    static WebClient Client() { var client=new WebClient();client.Headers[HttpRequestHeader.UserAgent]="PokemonBlueLauncher/1.0";return client; }
    static string Hash(string path) { using(var sha=SHA256.Create())using(var s=File.OpenRead(path))return BitConverter.ToString(sha.ComputeHash(s)).Replace("-","").ToLowerInvariant(); }
    static void Download(string url,string target,string expected) {
        if(File.Exists(target) && expected!=null && Hash(target)==expected)return;
        string tmp=target+".part";using(var client=Client())client.DownloadFile(url,tmp);
        if(expected!=null && Hash(tmp)!=expected)throw new Exception("O arquivo baixado nao passou pela verificacao SHA-256: "+Path.GetFileName(target));
        if(File.Exists(target))File.Delete(target);File.Move(tmp,target);
    }
    internal static string SafePath(string folder,string relative) {
        if(Path.IsPathRooted(relative) || relative.IndexOf(':')>=0)throw new Exception("Caminho invalido no pacote.");
        string root=Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar;
        string target=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!target.StartsWith(root,StringComparison.OrdinalIgnoreCase))throw new Exception("Caminho fora da pasta do pacote.");return target;
    }
    static bool Protected(string relative) {
        string top=relative.Replace('\\','/').Split('/')[0].ToLowerInvariant();
        return top=="game" || top=="saves" || top=="bluehub" || top==".git" || top==".blue-work" || top==".blue-backups" || top=="tools";
    }
    internal static void Extract(string archive,string folder,bool source) {
        using(var zip=ZipFile.OpenRead(archive))foreach(var entry in zip.Entries) {
            string name=entry.FullName.Replace('\\','/');
            if(source) { int slash=name.IndexOf('/');if(slash<0)continue;name=name.Substring(slash+1); }
            if(name.Length==0)continue;
            string target=SafePath(folder,name);if(source && Protected(name))continue;
            if(name.EndsWith("/")){Directory.CreateDirectory(target);continue;}
            Directory.CreateDirectory(Path.GetDirectoryName(target));entry.ExtractToFile(target,true);
        }
    }
    static string Runtime(string key,string executable) {
        var data=(Dictionary<string,object>)Manifest[key];string version=(string)data["version"];
        string folder=Path.Combine(Root,"tools",key+"-"+version);string exe=Path.Combine(folder,executable);
        if(!File.Exists(exe)) {
            Say("Baixando "+key+" portatil. Nao e necessario instalar programas no Windows.");
            string archive=Path.Combine(Root,".blue-work",key+"-"+version+".zip");Download((string)data["url"],archive,(string)data["sha256"]);
            Extract(archive,folder,false);if(!File.Exists(exe))throw new Exception("Pacote de "+key+" incompleto.");
        }
        if(key=="python")foreach(var pth in Directory.GetFiles(folder,"python*._pth")) {
            string text=Path.GetFileNameWithoutExtension(pth)+".zip\n.\n"+Root+"\n"+Path.Combine(Root,"server")+"\n"+Path.Combine(Root,"scripts")+"\n";
            if(Directory.Exists(Path.Combine(Root,"scripts")))foreach(string scriptDir in Directory.GetDirectories(Path.Combine(Root,"scripts")))text+=scriptDir+"\n";
            text+="import site\n";
            File.WriteAllText(pth,text,new UTF8Encoding(false));
        }
        return exe;
    }
    internal static string Quote(string value) {
        return "\""+System.Text.RegularExpressions.Regex.Replace(System.Text.RegularExpressions.Regex.Replace(value,@"(\\*)""",@"$1$1\"""),@"(\\+)$",@"$1$1")+"\"";
    }
    static void Run(string exe,string[] args,string extraPath) {
        string arguments=String.Join(" ",Array.ConvertAll(args,Quote));
        var start=new ProcessStartInfo(exe,arguments) { WorkingDirectory=Root,UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true };
        start.EnvironmentVariables["PATH"]=extraPath+Path.PathSeparator+start.EnvironmentVariables["PATH"];
        start.EnvironmentVariables["PYTHONUTF8"]="1";
        start.EnvironmentVariables["GIT_CONFIG_COUNT"]="1";
        start.EnvironmentVariables["GIT_CONFIG_KEY_0"]="http.sslBackend";
        start.EnvironmentVariables["GIT_CONFIG_VALUE_0"]="openssl";
        using(var process=new Process { StartInfo=start }) {
            process.OutputDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)Say(e.Data);};
            process.ErrorDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)Say(e.Data);};
            process.Start();process.BeginOutputReadLine();process.BeginErrorReadLine();process.WaitForExit();
            if(process.ExitCode!=0)throw new Exception("A preparacao parou (codigo "+process.ExitCode+"). Veja "+LogPath+" e abra novamente para retomar.");
        }
    }
    static void Prepare() {
        foreach(var p in Process.GetProcessesByName("Game"))try { if(String.Equals(p.MainModule.FileName,Path.Combine(Root,"game","Game.exe"),StringComparison.OrdinalIgnoreCase))throw new Exception("Feche o jogo antes de atualizar a instalacao."); }catch(System.ComponentModel.Win32Exception){}
        string marker=Path.Combine(Root,".blue-work","launcher-revision.txt");
        Say("Conferindo a ultima versao da main...");string revision;
        try { string json;using(var c=Client())json=c.DownloadString("https://api.github.com/repos/"+Repo+"/commits/main");revision=(string)Json.Deserialize<Dictionary<string,object>>(json)["sha"]; }
        catch(WebException) { if(!File.Exists(marker) || !File.Exists(Path.Combine(Root,"game","Game.exe")))throw;revision=File.ReadAllText(marker);Say("Sem conexao com o GitHub. Usando a ultima versao instalada."); }
        if(!System.Text.RegularExpressions.Regex.IsMatch(revision,"^[a-f0-9]{40}$"))throw new Exception("Resposta invalida do GitHub.");
        if(!File.Exists(marker) || File.ReadAllText(marker)!=revision || !File.Exists(Path.Combine(Root,"scripts","install_game.py"))) {
            Say("Baixando os arquivos atualizados do projeto...");string zip=Path.Combine(Root,".blue-work","source-"+revision+".zip");
            Download("https://codeload.github.com/"+Repo+"/zip/"+revision,zip,null);
            string stage=Path.Combine(Root,".blue-work","source-"+revision);Extract(zip,stage,true);
            if(!File.Exists(Path.Combine(stage,"scripts","install_game.py")))throw new Exception("O pacote do projeto esta incompleto.");
            string backup=Path.Combine(Root,".blue-backups","launcher-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfff"));
            foreach(string path in Directory.GetFiles(stage,"*",SearchOption.AllDirectories)) {
                string rel=path.Substring(stage.Length+1);string dest=SafePath(Root,rel);Directory.CreateDirectory(Path.GetDirectoryName(dest));
                if(File.Exists(dest)) { if(Hash(dest)==Hash(path))continue;string old=SafePath(backup,rel);Directory.CreateDirectory(Path.GetDirectoryName(old));File.Copy(dest,old,true); }
                File.Copy(path,dest,true);
            }
            File.WriteAllText(marker,revision);Say("Codigo atualizado: "+revision.Substring(0,7));
            string cache=Path.GetFullPath(Path.Combine(Root,".blue-work"))+Path.DirectorySeparatorChar;
            if(Path.GetFullPath(stage).StartsWith(cache,StringComparison.OrdinalIgnoreCase) && Path.GetFileName(stage)=="source-"+revision)Directory.Delete(stage,true);
            if(Path.GetFullPath(zip).StartsWith(cache,StringComparison.OrdinalIgnoreCase) && Path.GetFileName(zip)=="source-"+revision+".zip")File.Delete(zip);
        }
        string python=Runtime("python","python.exe");string git=Runtime("git",Path.Combine("cmd","git.exe"));string pathExtra=Path.GetDirectoryName(git);
        Say("Preparando a base e as atualizacoes. A primeira instalacao pode demorar.");
        var install=new List<string>{"scripts/install_game.py","--apply"};if(Hub)install.Add("--hub-only");Run(python,install.ToArray(),pathExtra);
        Run(python,Hub?new[]{"scripts/battle_lab/launch.py","--prepare-only"}:new[]{"scripts/launch_game.py","--prepare-only"},pathExtra);
        Say("Pronto. Versao "+revision.Substring(0,7)+".");
    }
    static void SelfTest(string report) {
        string folder=Path.Combine(Path.GetTempPath(),"blue-bootstrap-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(folder);
        string zip=Path.Combine(folder,"fixture.zip");using(var archive=ZipFile.Open(zip,ZipArchiveMode.Create)) {
            using(var writer=new StreamWriter(archive.CreateEntry("project/scripts/demo.py").Open()))writer.Write("new source");
            using(var writer=new StreamWriter(archive.CreateEntry("project/game/save.rxdata").Open()))writer.Write("must not install");
        }
        string stage=Path.Combine(folder,"output");Extract(zip,stage,true);
        if(!File.Exists(Path.Combine(stage,"scripts","demo.py")) || Directory.Exists(Path.Combine(stage,"game")))throw new Exception("Protected-file test failed.");
        bool rejected=false;try { SafePath(stage,"../escape"); }catch { rejected=true; }if(!rejected)throw new Exception("Traversal test failed.");
        if(Quote("a b")!="\"a b\"")throw new Exception("Argument quoting test failed.");
        File.WriteAllText(report,Json.Serialize(new { ok=true,mode=Hub?"hub":"story",protectedGame=true,traversalRejected=true }));
    }
}
