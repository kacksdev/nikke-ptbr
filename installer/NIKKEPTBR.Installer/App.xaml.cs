using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows;

namespace NIKKEPTBR.Installer
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            if (e.Args.Any(arg => string.Equals(arg, "--headless", StringComparison.OrdinalIgnoreCase)))
            {
                RunHeadless(e.Args);
                return;
            }

            var requested = ReadOption(e.Args, "--game-root");
            var window = new MainWindow(requested);
            MainWindow = window;
            ShutdownMode = ShutdownMode.OnMainWindowClose;
            window.Show();
        }

        private void RunHeadless(string[] args)
        {
            CoreResponse response;
            HeadlessOptions options = null;
            try
            {
                options = HeadlessOptions.Parse(args);
                var bridge = new CoreBridge(options.CacheRoot, options.StateRoot);
                response = bridge.ExecuteAsync(
                    options.Action,
                    options.GameRoot,
                    new InlineProgress<InstallerProgress>(_ => { })).GetAwaiter().GetResult();
            }
            catch (Exception error)
            {
                response = new CoreResponse
                {
                    Success = false,
                    Action = options?.Action.ToString().ToLowerInvariant() ?? "unknown",
                    Message = error.Message,
                    Technical = error.ToString()
                };
            }

            var reportPath = options?.ReportPath ?? ReadOption(args, "--report");
            if (!string.IsNullOrWhiteSpace(reportPath))
            {
                WriteJsonAtomic(Path.GetFullPath(reportPath), response);
            }
            Environment.ExitCode = response.Success ? 0 : 1;
            Shutdown(Environment.ExitCode);
        }

        private static string ReadOption(string[] args, string name)
        {
            for (var i = 0; i + 1 < args.Length; i++)
            {
                if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase))
                {
                    return args[i + 1];
                }
            }
            return null;
        }

        private static void WriteJsonAtomic(string path, CoreResponse response)
        {
            var parent = Path.GetDirectoryName(path);
            if (string.IsNullOrWhiteSpace(parent))
            {
                throw new InvalidOperationException("Caminho de relatório inválido.");
            }
            Directory.CreateDirectory(parent);
            var temporary = path + ".tmp-" + Guid.NewGuid().ToString("N");
            var serializer = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
            File.WriteAllText(temporary, serializer.Serialize(response), new UTF8Encoding(false));
            if (File.Exists(path))
            {
                File.Replace(temporary, path, null);
            }
            else
            {
                File.Move(temporary, path);
            }
        }
    }

    internal sealed class InlineProgress<T> : IProgress<T>
    {
        private readonly Action<T> _callback;

        public InlineProgress(Action<T> callback)
        {
            _callback = callback ?? throw new ArgumentNullException(nameof(callback));
        }

        public void Report(T value)
        {
            _callback(value);
        }
    }
}
