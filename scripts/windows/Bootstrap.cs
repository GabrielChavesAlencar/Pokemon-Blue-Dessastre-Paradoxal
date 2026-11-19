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
                using(var form=new Form { Text=Hub?"Pokemon Blue - Hub de Batalha":"Pokemon Blue - Historia",ClientSize=new Size(660,285),StartPosition=FormStartPosition.CenterScreen }) {
                    var title=new Label { Text="Preparando sua instalacao...",Left=24,Top=20,Width=612,Height=38,Font=new Font("Segoe UI",15) };
                    var info=new Label { Text="Conferindo a versao atual da main.",Left=24,Top=68,Width=612,Height=112,Font=new Font("Segoe UI",10) };
                    var bar=new ProgressBar { Left=24,Top=188,Width=612,Height=19,Style=ProgressBarStyle.Marquee };
                    // Visible AFTER preparation. The original campaign remains
                    // the default; Sinnoh requires an explicit user click.
                    var campaign=new Button { Text="Jogar campanha",Left=24,Top=225,Width=177,Height=35,Visible=false };
                    var sinnoh=new Button { Text="Testar piloto Sinnoh",Left=211,Top=225,Width=251,Height=35,Visible=false };
                    var close=new Button { Text="Fechar",Left=472,Top=225,Width=164,Height=35,Visible=false };
                    var selection=new TaskCompletionSource<string>();
                    campaign.Click+=delegate { selection.TrySetResult("campaign"); };
                    sinnoh.Click+=delegate { selection.TrySetResult("sinnoh"); };
                    close.Click+=delegate { selection.TrySetResult("cancel"); };
                    form.FormClosed+=delegate { selection.TrySetResult("cancel"); };
                    form.Controls.AddRange(new Control[]{title,info,bar,campaign,sinnoh,close});
                    Status=delegate(string s) { if(!form.IsDisposed)form.BeginInvoke((Action)delegate { info.Text=s; }); };
                    form.Shown+=async delegate {
                        bool experimentalSelected=false;
                        try {
                            // The Sinnoh QA choice MUST be available before the
                            // Kanto/Hoenn/Johto main-game installer runs. A partially
                            // installed Kanto (e.g. 142/145 maps) must not hide the
                            // isolated Sinnoh test option or cause map overwrites.
                            if(Hub)await Task.Run((Action)Prepare);
                            else await Task.Run((Action)PrepareSourceOnly);
                            if(!Hub) {
                                title.Text="Escolha como deseja jogar";
                                info.Text="Campanha principal: Decades/Kanto/Hoenn/Johto.\n"+
                                    "Testar piloto Sinnoh: gera e abre uma COPIA EXPERIMENTAL separada, sem importar saves.\n"+
                                    "Sinnoh ainda nao passou nos testes nativos (R07/R08/R09 pendentes).";
                                bar.Visible=false;
                                campaign.Visible=true;sinnoh.Visible=true;close.Visible=true;
                                string chosen=await selection.Task;
                                campaign.Visible=false;sinnoh.Visible=false;close.Visible=false;
                                if(chosen=="cancel") { form.Close();return; }
                                bar.Visible=true;bar.Style=ProgressBarStyle.Marquee;
                                if(chosen=="sinnoh") {
                                    experimentalSelected=true;
                                    title.Text="Preparando piloto experimental Sinnoh...";
                                    string qa=await Task.Run((Func<string>)PrepareSinnohTestCopy);
                                    title.Text="Abrindo Sinnoh na copia isolada...";
                                    info.Text="Ambiente: "+qa+"\n"+
                                        "Nunca confunda a copia QA com a campanha principal. A compilacao nativa ainda precisa ser verificada.";
                                    // Supervisiona o MESMO QA: compilacao inicial, recuperacao
                                    // verificada e no maximo um reinicio. Nunca abre outro piloto.
                                    string python=Runtime("python","python.exe");
                                    form.WindowState=FormWindowState.Minimized;
                                    await Task.Run(delegate {
                                        Run(python,new[]{"scripts/windows/sinnoh_qa_supervisor.py",
                                            "--project-root",Root,"--qa-dir",qa},Path.GetDirectoryName(python));
                                    });
                                    form.Close();return;
                                }
                                // Only the main campaign runs full installation and
                                // regional Kanto checks. Sinnoh above uses a read-only
                                // baseline and its own isolated QA directory.
                                title.Text="Verificando a instalacao da campanha...";
                                info.Text="Conferindo Kanto, Hoenn e Johto na instalacao principal.\n"+
                                    "Em caso de mapa incompleto, a campanha sera bloqueada sem sobrescrever arquivos.";
                                await Task.Run((Action)Prepare);
                            }
                            if(!Hub && !JohtoReady() && JohtoFilesPresent()) {
                                title.Text="Johto encontrada, mas precisa de reparo";
                                bar.Style=ProgressBarStyle.Continuous;
                                var message=
                                    "Os mapas de Johto existem nesta instalacao, mas a integridade "+
                                    "nao corresponde ao manifesto. Johto NAO sera declarada pronta.\n\n"+
                                    JohtoReason()+"\n\n"+
                                    "Nao substitua mapas nem reinstale o ZIP sobre esta copia.\n"+
                                    "Execute VERIFICAR_QUARTO_JOHTO.bat na pasta do Blue-Story "+
                                    "para gerar o diagnostico privado de Map600, Map674 e Map675.\n\n"+
                                    "OK: continuar com as demais regioes sem modificar Johto.\n\n"+
                                    "Relatorio: .blue-work/johto-main-install-status.json";
                                MessageBox.Show(form,message,"Blue-Story - Johto precisa de verificacao",
                                                MessageBoxButtons.OK,MessageBoxIcon.Warning);
                            }
                            else if(!Hub && !JohtoReady()) {
                                title.Text="Johto ainda não foi instalada";
                                bar.Style=ProgressBarStyle.Continuous;
                                var choice=MessageBox.Show(form,
                                    "Johto ainda não está disponível neste Game.exe.\n\n"+
                                    JohtoReason()+"\n\n"+
                                    "SIM: selecionar o ZIP privado de Johto e instalar agora.\n"+
                                    "NÃO: jogar Decades/Kanto/Hoenn sem Johto.\n"+
                                    "CANCELAR: fechar o inicializador.\n\n"+
                                    "Relatório: .blue-work/johto-main-install-status.json",
                                    "Blue-Story - instalar Johto",MessageBoxButtons.YesNoCancel,
                                    MessageBoxIcon.Warning);
                                if(choice==DialogResult.Cancel) {form.Close();return;}
                                if(choice==DialogResult.Yes) {
                                    string selected=null;
                                    using(var picker=new OpenFileDialog {
                                        Title="Selecione o ZIP privado original de Johto (sem extrair)",
                                        Filter="Pacote Johto (*.zip)|*.zip",
                                        CheckFileExists=true,
                                        Multiselect=false
                                    }) {
                                        if(picker.ShowDialog(form)!=DialogResult.OK) {form.Close();return;}
                                        selected=picker.FileName;
                                    }
                                    title.Text="Instalando Johto no jogo principal...";
                                    bar.Style=ProgressBarStyle.Marquee;
                                    await Task.Run(delegate {InstallSelectedJohto(selected);});
                                    if(!JohtoReady())throw new Exception("Johto não instalada: "+JohtoReason());
                                }
                            }
                            title.Text="Tudo pronto. Abrindo o jogo...";
                            string game=Path.Combine(Root,"game");var process=Process.Start(new ProcessStartInfo(Path.Combine(game,"Game.exe")){WorkingDirectory=game,UseShellExecute=true});
                            form.WindowState=FormWindowState.Minimized;
                            await Task.Run(delegate { process.WaitForExit(); });form.Close();
                        } catch(Exception error) {
                            // Supervised QA may have minimized the window while Game.exe ran.
                            // Restore it so a fail-closed diagnostic is actually visible.
                            if(experimentalSelected)form.WindowState=FormWindowState.Normal;
                            bar.Style=ProgressBarStyle.Continuous;
                            title.Text=Hub?"A instalacao precisa de atencao":"A instalacao nao terminou";
                            info.Text=error.Message+"\nLog: "+LogPath;
                            // Never claim "ready" when optional Kanto did not import:
                            // inspect the status emitted by the downloaded Python.
                            if(!Hub && !experimentalSelected) {
                                string regional=Path.Combine(Root,".blue-work","kanto-install-status.json");
                                try {
                                    if(File.Exists(regional)) {
                                        var proof=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(regional,Encoding.UTF8));
                                        if(proof.ContainsKey("ready") && proof["ready"] is bool && !(bool)proof["ready"]) {
                                            string reason=proof.ContainsKey("reason")?Convert.ToString(proof["reason"]):"Veja o log.";
                                            info.Text="Kanto NAO instalado: "+reason+"\nRelatorio: "+regional+
                                                "\nAbra Blue-Story.exe novamente para tentar instalar automaticamente.";
                                        }
                                    }
                                } catch(Exception) { /* Show the original error on invalid diagnostic. */ }
                            }
                            MessageBox.Show(form,info.Text,experimentalSelected?"Blue-Story - piloto Sinnoh bloqueado":"Pokemon Blue - instalacao incompleta",
                                            MessageBoxButtons.OK,MessageBoxIcon.Warning);
                        }
                    };
                    Application.Run(form);
                }
            }
            return 0;
        } catch(Exception error) { if(LogPath!=null)File.AppendAllText(LogPath,error+Environment.NewLine);if(Array.IndexOf(args,"--prepare-only")<0 && Array.IndexOf(args,"--runtime-test")<0)MessageBox.Show(error.Message,"Pokemon Blue");return 1; }
    }
    // The Blue-Story menu prepares Sinnoh without requiring the user to run
    // a separate BAT/PowerShell command. A new QA copy is always created, never
    // a silent install into the main game or a reused foreign-region save.
    static string PrepareSinnohTestCopy() {
        if(Hub)throw new Exception("Sinnoh experimental so pode ser iniciada pelo Blue-Story.");
        string game=Path.Combine(Root,"game");
        if(!File.Exists(Path.Combine(game,"Game.exe")))
            throw new Exception("Game.exe principal nao encontrado; prepare a base primeiro.");
        string python=Runtime("python","python.exe");
        string git=Runtime("git",Path.Combine("cmd","git.exe"));
        string receipt=Path.Combine(Root,".blue-work","blue-story-sinnoh-launch.json");
        if(File.Exists(receipt))File.Delete(receipt); // Only our own stale receipt.
        Say("[SINNOH QA] Criando nova copia experimental. Original e saves intactos.");
        Run(python,new[]{"scripts/windows/launch_sinnoh_pilot.py",
            "--project-root",Root,"--game-dir",game,"--receipt",receipt},
            Path.GetDirectoryName(git));
        if(!File.Exists(receipt))
            throw new Exception("Sinnoh: instalador nao entregou recibo da copia experimental.");
        var result=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(receipt,Encoding.UTF8));
        object mode,dir,unmodified,qa;
        if(!result.TryGetValue("mode",out mode) ||
           Convert.ToString(mode)!="SINNOH_PRIVATE_EXPERIMENTAL_COPY_NOT_APPROVED" ||
           !result.TryGetValue("qa_directory",out dir) ||
           !result.TryGetValue("main_game_modified",out unmodified) ||
           !(unmodified is bool) || (bool)unmodified ||
           !result.TryGetValue("native_qa_cases_approved",out qa) ||
           Convert.ToInt32(qa)!=0)
            throw new Exception("Sinnoh: recibo invalido ou tentativa de alterar o jogo principal.");
        string work=Path.GetFullPath(Path.Combine(Root,".blue-work")).TrimEnd(Path.DirectorySeparatorChar);
        string folder=Path.GetFullPath(Convert.ToString(dir));
        if(!folder.StartsWith(work+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase) ||
           !Path.GetFileName(folder).StartsWith("game-sinnoh-experimental-",StringComparison.OrdinalIgnoreCase) ||
           !Directory.Exists(folder) ||
           (File.GetAttributes(folder)&FileAttributes.ReparsePoint)!=0 ||
           !File.Exists(Path.Combine(folder,"INICIAR_SINNOH_EXPERIMENTAL.bat")) ||
           !File.Exists(Path.Combine(folder,"sinnoh-experimental-qa.json")))
            throw new Exception("Sinnoh: caminho ou pacote da copia experimental invalido.");
        Say("[SINNOH QA] Piloto pronto para TENTATIVA de inicio em copia isolada: "+folder);
        return folder;
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
            // Keep a short, local tail so Python fail-closed diagnostics are
            // visible in the dialog instead of only an opaque exit code 2.
            var tail=new Queue<string>();
            object tailLock=new object();
            Action<string> capture=delegate(string line) {
                if(String.IsNullOrWhiteSpace(line))return;
                Say(line);
                lock(tailLock) {
                    tail.Enqueue(line.Length>400?line.Substring(0,400):line);
                    while(tail.Count>5)tail.Dequeue();
                }
            };
            process.OutputDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)capture(e.Data);};
            process.ErrorDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)capture(e.Data);};
            process.Start();process.BeginOutputReadLine();process.BeginErrorReadLine();process.WaitForExit();
            if(process.ExitCode!=0) {
                string detail;
                lock(tailLock)detail=String.Join("\n",tail.ToArray());
                throw new Exception("A preparacao parou (codigo "+process.ExitCode+")."+
                    (detail.Length>0?"\nMotivo: "+detail:"")+
                    "\nLog: "+LogPath);
            }
        }
    }
    static string RegionalStatus(string filename,string name) {
        string path=Path.Combine(Root,".blue-work",filename);
        if(!File.Exists(path))return name+": ainda nao verificado";
        try {
            var info=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(path,Encoding.UTF8));
            object ready;
            if(info.TryGetValue("ready",out ready) && ready is bool && (bool)ready) {
                object qa;
                if(name=="Johto" && info.TryGetValue("native_qa",out qa) && qa is bool && !(bool)qa)
                    return "Johto: previa experimental (sem teste no jogo)";
                return name+": integrado";
            }
            return name+": pendente (ver relatorio)";
        } catch(Exception) { return name+": relatorio invalido"; }
    }
    const string JohtoZipName="Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip";
    const string JohtoBundleHash="74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49";
    static Dictionary<string,object> JohtoStatus() {
        string path=Path.Combine(Root,".blue-work","johto-main-install-status.json");
        try {
            if(!File.Exists(path))return new Dictionary<string,object>();
            return Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(path,Encoding.UTF8));
        } catch(Exception) { return new Dictionary<string,object>(); }
    }
    static bool JohtoReady() {
        var s=JohtoStatus();object result;
        return s.TryGetValue("ready",out result) && result is bool && (bool)result;
    }
    static bool JohtoFilesPresent() {
        return File.Exists(Path.Combine(Root,"game","Data","blue-johto-main-preview.json"))
            || File.Exists(Path.Combine(Root,"game","Data","blue-johto-preview-ready.txt"));
    }
    static string JohtoReason() {
        var s=JohtoStatus();object reason;
        if(s.TryGetValue("reason",out reason) && reason!=null)return Convert.ToString(reason);
        return "Johto ainda não foi instalada. Consulte .blue-work/johto-main-install-status.json";
    }
    static void InstallSelectedJohto(string selected) {
        if(!File.Exists(selected))throw new Exception("O ZIP selecionado não existe.");
        if(!String.Equals(Hash(selected),JohtoBundleHash,StringComparison.OrdinalIgnoreCase))
            throw new Exception("Esse ZIP não corresponde ao pacote Johto OFFLINE 12 original verificado. Nenhum arquivo do jogo foi alterado.");
        string destination=Path.Combine(Root,".blue-work",JohtoZipName);
        if(!String.Equals(Path.GetFullPath(selected),Path.GetFullPath(destination),StringComparison.OrdinalIgnoreCase))
            File.Copy(selected,destination,true);
        Say("Preparando Johto no Decades principal com backup, mapas, PBS e scripts.");
        string python=Runtime("python","python.exe");
        string extra=Path.GetDirectoryName(python);
        Run(python,new[]{"scripts/regions/auto_integrate_johto.py"},extra);
        if(!JohtoReady())throw new Exception("A integração Johto falhou: "+JohtoReason());
        Run(python,new[]{"scripts/launch_game.py","--prepare-only"},extra);
        Say("Johto instalada como prévia experimental. É necessário testar a jogabilidade.");
    }
    static string RegionalSummary() {
        return "Decades: instalado | "+
          RegionalStatus("kanto-install-status.json","Kanto")+" | "+
          RegionalStatus("hoenn-main-install-status.json","Hoenn")+" | "+
          RegionalStatus("johto-main-install-status.json","Johto");
    }
    // Optional PERSONAL build: append the exact original private Johto ZIP and
    // a 16-byte footer ["BLUEJH12", ZIP byte length as little-endian Int64] to
    // the PE executable. Windows/.NET ignores this overlay and runs normally.
    // The public GitHub release remains code-only. Personal one-file builds can
    // stage the user's existing private package without publishing its contents.
    const string EmbeddedJohtoMagic="BLUEJH12";
    const long EmbeddedJohtoMaxBytes=32000000L;
    static bool StageEmbeddedJohto() {
        if(Hub)return false;
        string executable=typeof(Bootstrap).Assembly.Location;
        if(!File.Exists(executable))return false;
        long size, length;
        using(var file=new FileStream(executable,FileMode.Open,FileAccess.Read,FileShare.Read)) {
            if(file.Length<16)return false;
            file.Seek(-16,SeekOrigin.End);
            using(var reader=new BinaryReader(file,Encoding.ASCII,true)) {
                if(Encoding.ASCII.GetString(reader.ReadBytes(8))!=EmbeddedJohtoMagic)return false;
                length=reader.ReadInt64();
            }
            size=file.Length;
        }
        if(length<=0 || length>EmbeddedJohtoMaxBytes || length>size-16)
            throw new Exception("Payload Johto embutido no executavel possui dimensoes invalidas.");
        string target=Path.Combine(Root,".blue-work",JohtoZipName);
        if(File.Exists(target) && String.Equals(Hash(target),JohtoBundleHash,StringComparison.OrdinalIgnoreCase)) {
            Say("[JOHTO] Pacote OFFLINE12 original ja esta preparado; sem download adicional.");
            return true;
        }
        // Copy only the appended archive bytes. Verify the entire SHA256
        // against the pinned source BEFORE replacing anything on disk.
        string temp=target+".embedded-tmp";
        if(File.Exists(temp))throw new Exception("Temporario antigo Johto encontrado. Revise "+temp);
        try {
            using(var input=new FileStream(executable,FileMode.Open,FileAccess.Read,FileShare.Read))
            using(var output=new FileStream(temp,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
                input.Position=size-16-length;
                byte[] block=new byte[65536];
                long remaining=length;
                while(remaining>0) {
                    int read=input.Read(block,0,(int)Math.Min((long)block.Length,remaining));
                    if(read<=0)throw new Exception("Payload embutido Johto incompleto.");
                    output.Write(block,0,read);
                    remaining-=read;
                }
            }
            if(!String.Equals(Hash(temp),JohtoBundleHash,StringComparison.OrdinalIgnoreCase))
                throw new Exception("Johto embutida nao passou SHA-256; instalacao nao alterada.");
            if(File.Exists(target)) {
                string backup=Path.Combine(Root,".blue-backups","johto-zip-before-embed-"+DateTime.UtcNow.ToString("yyyyMMddTHHmmssfff")+".zip");
                Directory.CreateDirectory(Path.GetDirectoryName(backup));
                File.Copy(target,backup,false);
                File.Replace(temp,target,null);
            } else File.Move(temp,target);
        } finally {if(File.Exists(temp))File.Delete(temp);}
        Say("[JOHTO] Pacote privado OFFLINE12 extraido do proprio Blue-Story.exe; SHA-256 verificado. Instalacao automatica habilitada.");
        return true;
    }

    // A user-owned private Johto pack can accompany Blue-Story.exe in one
    // downloadable ZIP. Stage it in the SAME already-managed installation
    // before Python checks regions; never publish or modify its raw contents.
    static void StageAdjacentJohto() {
        if(Hub)return;
        string local=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,JohtoZipName);
        string target=Path.Combine(Root,".blue-work",JohtoZipName);
        if(!File.Exists(local) || String.Equals(Path.GetFullPath(local),Path.GetFullPath(target),
                                                StringComparison.OrdinalIgnoreCase))return;
        if(!String.Equals(Hash(local),JohtoBundleHash,StringComparison.OrdinalIgnoreCase)) {
            Say("[JOHTO] Pacote ao lado do Blue-Story.exe nao tem SHA-256 autorizado; nao foi usado.");
            return;
        }
        if(File.Exists(target) && Hash(target)==JohtoBundleHash) {
            Say("[JOHTO] Pacote privado correto ja esta na instalacao principal.");
            return;
        }
        string temp=target+".stage";
        if(File.Exists(temp))File.Delete(temp);
        try {
            File.Copy(local,temp);
            if(Hash(temp)!=JohtoBundleHash)throw new Exception("Falha ao verificar ZIP Johto copiado.");
            if(File.Exists(target))File.Delete(target);
            File.Move(temp,target);
        } finally {if(File.Exists(temp))File.Delete(temp);}
        Say("[JOHTO] ZIP privado encontrado ao lado do Blue-Story.exe; preparado automaticamente antes do Game.exe.");
    }

    static void PrepareSourceOnly() { Prepare(true); }
    static void Prepare() { Prepare(false); }
    static void Prepare(bool sourceOnly) {
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
        if(sourceOnly) {
            // Download public source only. Running install_game.py here would
            // check/repair Kanto before the user can select the Sinnoh pilot.
            // Do NOT touch game/Data, plugins, Game.exe or saves.
            Say("[MENU] Codigo pronto; escolha campanha ou piloto Sinnoh isolado.");
            return;
        }
        StageEmbeddedJohto();
        StageAdjacentJohto();
        Say("[GAME EXE GERENCIADO] "+Path.Combine(Root,"game","Game.exe")+
            " - verifique se esta e a MESMA copia que voce esta jogando.");
        string python=Runtime("python","python.exe");string git=Runtime("git",Path.Combine("cmd","git.exe"));string pathExtra=Path.GetDirectoryName(git);
        if(!Hub) {
            // The source ZIP above includes the editor. Mirror its public
            // components into Johto-Map-Studio both beside Blue-Story.exe and
            // inside the managed project; never distribute private maps.
            string exeDir=AppDomain.CurrentDomain.BaseDirectory;
            Environment.SetEnvironmentVariable("BLUE_STORY_LAUNCHER_DIR",exeDir);
            try {
                Say("[JOHTO EDITOR] Baixando e atualizando Johto Map Studio da main...");
                Run(python,new[]{"scripts/windows/install_johto_editor.py",
                    "--project-root",Root,"--launcher-dir",exeDir},pathExtra);
                Say("[JOHTO EDITOR] Editor disponivel em Johto-Map-Studio ao lado do Blue-Story.exe.");
            } catch(Exception err) {
                // Editor is optional for starting the game; do not prevent
                // Kanto/Hoenn/Johto from running if the EXE folder is read-only.
                Say("[JOHTO EDITOR] Nao foi possivel preparar atalhos: "+err.Message);
            }
        }
        Say("Preparando a base e as atualizacoes. A primeira instalacao pode demorar.");
        var install=new List<string>{"scripts/install_game.py","--apply"};if(Hub)install.Add("--hub-only");Run(python,install.ToArray(),pathExtra);
        Run(python,Hub?new[]{"scripts/battle_lab/launch.py","--prepare-only"}:new[]{"scripts/launch_game.py","--prepare-only"},pathExtra);
        if(!Hub)Say("REGIOES - "+RegionalSummary());
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
