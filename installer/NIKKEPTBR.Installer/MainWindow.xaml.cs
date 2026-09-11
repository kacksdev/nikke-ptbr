using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using Forms = System.Windows.Forms;

namespace NIKKEPTBR.Installer
{
    public partial class MainWindow : Window
    {
        private const string GitHubUrl = "https://github.com/kacksdev/nikke-ptbr";
        private const string GameBananaUrl = "https://gamebanana.com/members/4201671";
        private readonly CoreBridge _bridge = new CoreBridge();
        private readonly string _requestedPath;
        private bool _busy;
        private CoreResponse _inspection;
        private InstallerAction _recommendedAction = InstallerAction.Install;
        private int _lastLoggedPercent = -100;
        private string _lastLoggedPhase = string.Empty;
        private string _lastLoggedMessage = string.Empty;

        public MainWindow(string requestedPath = null)
        {
            _requestedPath = requestedPath;
            InitializeComponent();
            ConfigureResponsiveWindow();
            Loaded += async (_, __) => await DetectAndInspectAsync(_requestedPath);
        }

        private void ConfigureResponsiveWindow()
        {
            var workArea = SystemParameters.WorkArea;
            var highResolution = workArea.Width >= 2400 && workArea.Height >= 1300;
            var targetWidth = highResolution ? 1920.0 : 1280.0;
            var targetHeight = highResolution ? 1080.0 : 720.0;
            Width = Math.Min(targetWidth, Math.Max(960, workArea.Width - 16));
            Height = Math.Min(targetHeight, Math.Max(600, workArea.Height - 16));
            MaxWidth = workArea.Width;
            MaxHeight = workArea.Height;
        }

        private async Task DetectAndInspectAsync(string requestedPath)
        {
            SetBusy(true);
            SetStatus("LOCALIZANDO O JOGO", "Validando a instalação oficial do NIKKE.", Brushes.White);
            AddLog("Iniciando detecção segura do cliente.");
            try
            {
                var path = string.IsNullOrWhiteSpace(requestedPath)
                    ? await Task.Run(() => GameDetector.Detect())
                    : await Task.Run(() => GameDetector.Normalize(requestedPath));
                if (string.IsNullOrWhiteSpace(path))
                {
                    throw new InvalidOperationException(
                        "A pasta oficial do NIKKE não foi localizada automaticamente. Escolha a pasta que contém nikke.exe.");
                }

                GamePathBox.Text = path;
                var progress = new Progress<InstallerProgress>(UpdateProgress);
                var response = await _bridge.ExecuteAsync(InstallerAction.Inspect, path, progress);
                if (!response.Success)
                {
                    throw new InstallerUiException(response);
                }
                _inspection = response;
                if (!string.IsNullOrWhiteSpace(response.ModVersion))
                {
                    ModVersionText.Text = response.ModVersion;
                }
                if (!string.IsNullOrWhiteSpace(response.ClientVersion))
                {
                    ClientVersionText.Text = response.ClientVersion;
                }
                ApplyInspection(response);
                SetInspectionProgress(response.StringData("health"));
                AddLog("Cliente validado: " + path);
                AddLog(response.StringData("summary"));
            }
            catch (InstallerUiException error)
            {
                _inspection = null;
                PresentFailure(error.Response);
                DisableActionsForUnconfirmedClient();
            }
            catch (Exception error)
            {
                _inspection = null;
                SetStatus("PASTA NÃO CONFIRMADA", error.Message, WarningBrush());
                AddLog("Detecção não concluída: " + error.Message);
                DisableActionsForUnconfirmedClient();
            }
            finally
            {
                SetBusy(false);
            }
        }

        private void ApplyInspection(CoreResponse response)
        {
            var health = response.StringData("health");
            var summary = response.StringData("summary");
            var recommended = response.StringData("recommended_action");
            switch (health)
            {
                case "installed_verified":
                    SetStatus("INSTALAÇÃO VERIFICADA", summary, SuccessBrush());
                    PrimaryButton.Content = "TRADUÇÃO INSTALADA";
                    PrimaryButton.IsEnabled = false;
                    VerifyButton.IsEnabled = true;
                    RemoveButton.IsEnabled = true;
                    _recommendedAction = InstallerAction.Verify;
                    break;
                case "repair_required":
                    SetStatus("REPARO NECESSÁRIO", summary, WarningBrush());
                    PrimaryButton.Content = "REPARAR AGORA";
                    PrimaryButton.IsEnabled = true;
                    VerifyButton.IsEnabled = true;
                    RemoveButton.IsEnabled = true;
                    _recommendedAction = InstallerAction.Repair;
                    break;
                case "recovery_required":
                    _recommendedAction = ParseAction(recommended);
                    SetStatus("RETOMADA DISPONÍVEL", summary, WarningBrush());
                    PrimaryButton.Content = "RETOMAR " + ActionLabel(_recommendedAction);
                    PrimaryButton.IsEnabled = true;
                    VerifyButton.IsEnabled = false;
                    RemoveButton.IsEnabled = false;
                    break;
                case "not_installed":
                    SetStatus("PRONTO PARA INSTALAR", summary, Brushes.White);
                    PrimaryButton.Content = "INSTALAR TRADUÇÃO";
                    PrimaryButton.IsEnabled = true;
                    VerifyButton.IsEnabled = false;
                    RemoveButton.IsEnabled = false;
                    _recommendedAction = InstallerAction.Install;
                    break;
                default:
                    SetStatus("AÇÃO MANUAL NECESSÁRIA", summary, WarningBrush());
                    PrimaryButton.Content = "INSTALAÇÃO BLOQUEADA";
                    PrimaryButton.IsEnabled = false;
                    VerifyButton.IsEnabled = false;
                    RemoveButton.IsEnabled = false;
                    _recommendedAction = InstallerAction.Inspect;
                    DetailsExpander.IsExpanded = true;
                    break;
            }
        }

        private async void PrimaryAction_OnClick(object sender, RoutedEventArgs e)
        {
            if (_inspection == null)
            {
                Browse_OnClick(sender, e);
                return;
            }
            if (_recommendedAction == InstallerAction.Install ||
                _recommendedAction == InstallerAction.Repair ||
                _recommendedAction == InstallerAction.Remove)
            {
                await RunOperationAsync(_recommendedAction);
            }
        }

        private async void Verify_OnClick(object sender, RoutedEventArgs e)
        {
            await RunOperationAsync(InstallerAction.Verify);
        }

        private async void Remove_OnClick(object sender, RoutedEventArgs e)
        {
            if (_inspection == null)
            {
                return;
            }
            var answer = MessageBox.Show(
                "Remover a tradução PT-BR deste cliente? O instalador removerá somente os três componentes que pertencem exatamente a este pacote e preservará o relatório de execução.",
                "Confirmar remoção",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);
            if (answer == MessageBoxResult.Yes)
            {
                await RunOperationAsync(InstallerAction.Remove);
            }
        }

        private async Task RunOperationAsync(InstallerAction action)
        {
            if (_busy || _inspection == null || string.IsNullOrWhiteSpace(GamePathBox.Text))
            {
                return;
            }

            SetBusy(true);
            DetailsExpander.IsExpanded = true;
            ResetProgress();
            AddLog("Operação iniciada: " + ActionLabel(action) + ".");
            try
            {
                var progress = new Progress<InstallerProgress>(UpdateProgress);
                var response = await _bridge.ExecuteAsync(action, GamePathBox.Text, progress);
                if (!response.Success)
                {
                    PresentFailure(response);
                }
                else
                {
                    SetStatus("OPERAÇÃO CONCLUÍDA", SuccessMessage(action), SuccessBrush());
                    CompletionHint.Text = "Depois de testar, avalie o projeto no GitHub ou no GameBanana. Se encontrar um problema, envie um relato por uma dessas páginas.";
                    AddLog(SuccessMessage(action));
                }
            }
            catch (Exception error)
            {
                PresentFailure(new CoreResponse
                {
                    Success = false,
                    Action = action.ToString().ToLowerInvariant(),
                    Message = error.Message,
                    Technical = error.ToString()
                });
            }
            finally
            {
                SetBusy(false);
            }

            await DetectAndInspectAsync(GamePathBox.Text);
        }

        private void PresentFailure(CoreResponse response)
        {
            var message = string.IsNullOrWhiteSpace(response?.Message)
                ? "A operação não foi concluída. Nenhuma continuação insegura foi executada."
                : response.Message;
            SetStatus("OPERAÇÃO NÃO CONCLUÍDA", message, WarningBrush());
            AddLog("Falha: " + message);
            if (!string.IsNullOrWhiteSpace(response?.Technical) &&
                !string.Equals(response.Technical, message, StringComparison.Ordinal))
            {
                AddLog("Detalhe técnico: " + response.Technical);
            }
            DetailsExpander.IsExpanded = true;
        }

        private void UpdateProgress(InstallerProgress item)
        {
            Dispatcher.Invoke(() =>
            {
                var percent = Math.Max(0, Math.Min(100, item.Percent));
                InstallProgress.Value = percent;
                ProgressPercent.Text = percent + "%";
                ProgressPhase.Text = string.IsNullOrWhiteSpace(item.Phase) ? "PROCESSANDO" : item.Phase;
                var phaseChanged = !string.Equals(_lastLoggedPhase, item.Phase, StringComparison.Ordinal);
                var messageChanged = !string.Equals(_lastLoggedMessage, item.Message, StringComparison.Ordinal);
                if (phaseChanged || messageChanged || percent == 100 || percent - _lastLoggedPercent >= 10)
                {
                    AddLog(item.Message);
                    _lastLoggedPhase = item.Phase ?? string.Empty;
                    _lastLoggedMessage = item.Message ?? string.Empty;
                    _lastLoggedPercent = percent;
                }
            });
        }

        private async void Browse_OnClick(object sender, RoutedEventArgs e)
        {
            if (_busy)
            {
                return;
            }
            using (var picker = new Forms.FolderBrowserDialog())
            {
                picker.Description = "Selecione a pasta que contém nikke.exe";
                picker.ShowNewFolderButton = false;
                if (picker.ShowDialog() == Forms.DialogResult.OK)
                {
                    await DetectAndInspectAsync(picker.SelectedPath);
                }
            }
        }

        private void SetBusy(bool busy)
        {
            _busy = busy;
            BrowseButton.IsEnabled = !busy;
            if (busy)
            {
                PrimaryButton.IsEnabled = false;
                VerifyButton.IsEnabled = false;
                RemoveButton.IsEnabled = false;
            }
            else if (_inspection != null)
            {
                ApplyInspection(_inspection);
            }
        }

        private void DisableActionsForUnconfirmedClient()
        {
            PrimaryButton.Content = "ESCOLHER PASTA";
            PrimaryButton.IsEnabled = true;
            VerifyButton.IsEnabled = false;
            RemoveButton.IsEnabled = false;
        }

        private void ResetProgress()
        {
            InstallProgress.Value = 0;
            ProgressPercent.Text = "0%";
            ProgressPhase.Text = "PREPARANDO";
            _lastLoggedPercent = -100;
            _lastLoggedPhase = string.Empty;
            _lastLoggedMessage = string.Empty;
        }

        private void SetInspectionProgress(string health)
        {
            if (string.Equals(health, "installed_verified", StringComparison.Ordinal))
            {
                InstallProgress.Value = 100;
                ProgressPercent.Text = "100%";
                ProgressPhase.Text = "VERIFICADO";
            }
            else
            {
                InstallProgress.Value = 0;
                ProgressPercent.Text = "0%";
                ProgressPhase.Text = string.Equals(health, "repair_required", StringComparison.Ordinal)
                    ? "REPARO NECESSÁRIO"
                    : "PRONTO";
            }
        }

        private void SetStatus(string title, string message, Brush color)
        {
            StatusTitle.Text = title;
            StatusMessage.Text = message;
            StatusDot.Fill = color;
        }

        private void AddLog(string message)
        {
            if (string.IsNullOrWhiteSpace(message))
            {
                return;
            }
            LogText.Text += "[" + DateTime.Now.ToString("HH:mm:ss") + "] " + message + Environment.NewLine;
            LogScroller.ScrollToEnd();
        }

        private static InstallerAction ParseAction(string action)
        {
            InstallerAction parsed;
            return Enum.TryParse(action, true, out parsed) ? parsed : InstallerAction.Inspect;
        }

        private static string ActionLabel(InstallerAction action)
        {
            switch (action)
            {
                case InstallerAction.Install: return "INSTALAÇÃO";
                case InstallerAction.Verify: return "VERIFICAÇÃO";
                case InstallerAction.Repair: return "REPARO";
                case InstallerAction.Remove: return "REMOÇÃO";
                case InstallerAction.Rollback: return "RECUPERAÇÃO";
                default: return "INSPEÇÃO";
            }
        }

        private static string SuccessMessage(InstallerAction action)
        {
            switch (action)
            {
                case InstallerAction.Install: return "A tradução PT-BR foi instalada e verificada com sucesso.";
                case InstallerAction.Verify: return "Todos os componentes da tradução foram verificados com sucesso.";
                case InstallerAction.Repair: return "A tradução foi reparada e verificada com sucesso.";
                case InstallerAction.Remove: return "A tradução foi removida com segurança.";
                case InstallerAction.Rollback: return "O estado anterior foi restaurado e verificado.";
                default: return "Operação concluída com sucesso.";
            }
        }

        private static Brush SuccessBrush() => new SolidColorBrush(Color.FromRgb(215, 230, 219));
        private static Brush WarningBrush() => new SolidColorBrush(Color.FromRgb(229, 181, 84));

        private static void OpenUrl(string url)
        {
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
        }

        private void GitHub_OnClick(object sender, MouseButtonEventArgs e) => OpenUrl(GitHubUrl);
        private void GameBanana_OnClick(object sender, MouseButtonEventArgs e) => OpenUrl(GameBananaUrl);

        private void Licenses_OnClick(object sender, MouseButtonEventArgs e)
        {
            try
            {
                using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("NIKKEPTBR.ThirdPartyNotices.txt"))
                using (var reader = new StreamReader(stream ?? throw new InvalidOperationException("Licenças não encontradas."), Encoding.UTF8))
                {
                    MessageBox.Show(reader.ReadToEnd(), "Licenças e avisos", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception error)
            {
                MessageBox.Show(error.Message, "Licenças e avisos", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void Minimize_OnClick(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
        private void Close_OnClick(object sender, RoutedEventArgs e)
        {
            if (!_busy)
            {
                Close();
            }
        }

        private void Header_OnMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
            }
            else
            {
                DragMove();
            }
        }

        private void Window_OnClosing(object sender, CancelEventArgs e)
        {
            if (!_busy)
            {
                return;
            }
            e.Cancel = true;
            MessageBox.Show(
                "Aguarde a operação atual terminar. Se o computador for desligado, o instalador retomará pelo journal persistente na próxima execução.",
                "Operação em andamento",
                MessageBoxButton.OK,
                MessageBoxImage.Information);
        }
    }

    internal sealed class InstallerUiException : Exception
    {
        public CoreResponse Response { get; }

        public InstallerUiException(CoreResponse response)
            : base(response?.Message)
        {
            Response = response;
        }
    }
}
