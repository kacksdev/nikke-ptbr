using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace NIKKEPTBR.Installer
{
    public sealed class CoreBridge
    {
        private readonly string _cacheOverride;
        private readonly string _stateOverride;
        private readonly object _bootstrapLock = new object();
        private BootstrapContext _context;

        public CoreBridge(string cacheOverride = null, string stateOverride = null)
        {
            _cacheOverride = cacheOverride;
            _stateOverride = stateOverride;
        }

        public Task<CoreResponse> ExecuteAsync(
            InstallerAction action,
            string gameRoot,
            IProgress<InstallerProgress> progress)
        {
            if (string.IsNullOrWhiteSpace(gameRoot))
            {
                throw new ArgumentException("A pasta do jogo não foi informada.", nameof(gameRoot));
            }
            return Task.Run(() => Execute(action, Path.GetFullPath(gameRoot), progress));
        }

        private CoreResponse Execute(
            InstallerAction action,
            string gameRoot,
            IProgress<InstallerProgress> progress)
        {
            var context = EnsureBootstrap(progress);
            var stateRoot = string.IsNullOrWhiteSpace(_stateOverride)
                ? DefaultStateRoot(gameRoot)
                : Path.GetFullPath(_stateOverride);
            var allowedParent = Directory.GetParent(gameRoot)?.FullName;
            if (string.IsNullOrWhiteSpace(allowedParent))
            {
                throw new InvalidOperationException("A pasta do cliente não possui um diretório pai seguro.");
            }

            var arguments = new List<string>
            {
                "--action", ActionName(action),
                "--package-root", context.PackageRoot,
                "--target-root", gameRoot,
                "--state-root", stateRoot,
                "--allowed-target-parent", allowedParent
            };
            var start = new ProcessStartInfo
            {
                FileName = context.CoreExecutable,
                Arguments = JoinArguments(arguments),
                WorkingDirectory = Path.GetDirectoryName(context.CoreExecutable),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = new UTF8Encoding(false),
                StandardErrorEncoding = new UTF8Encoding(false)
            };
            start.EnvironmentVariables["PYTHONUTF8"] = "1";
            start.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";

            CoreResponse final = null;
            var serializer = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
            using (var process = new Process { StartInfo = start })
            {
                if (!process.Start())
                {
                    throw new InvalidOperationException("Não foi possível iniciar o núcleo seguro do instalador.");
                }
                var errorRead = process.StandardError.ReadToEndAsync();
                string line;
                while ((line = process.StandardOutput.ReadLine()) != null)
                {
                    if (string.IsNullOrWhiteSpace(line))
                    {
                        continue;
                    }
                    Dictionary<string, object> payload;
                    try
                    {
                        payload = serializer.Deserialize<Dictionary<string, object>>(line);
                    }
                    catch (Exception parseError)
                    {
                        throw new InvalidDataException("Resposta interna inválida do instalador.", parseError);
                    }

                    object typeValue;
                    var type = payload.TryGetValue("type", out typeValue)
                        ? Convert.ToString(typeValue)
                        : string.Empty;
                    if (string.Equals(type, "progress", StringComparison.OrdinalIgnoreCase))
                    {
                        var corePercent = GetInt(payload, "percent");
                        progress?.Report(new InstallerProgress
                        {
                            Percent = 20 + (int)Math.Round(corePercent * 0.80),
                            Phase = GetString(payload, "phase"),
                            Message = GetString(payload, "message")
                        });
                    }
                    else if (string.Equals(type, "result", StringComparison.OrdinalIgnoreCase))
                    {
                        final = ParseResponse(payload);
                    }
                }
                process.WaitForExit();
                var standardError = errorRead.GetAwaiter().GetResult();
                if (final == null)
                {
                    throw new InvalidOperationException(
                        "O núcleo do instalador terminou sem um relatório válido. " + standardError.Trim());
                }
                if (!final.Success || process.ExitCode != 0)
                {
                    if (string.IsNullOrWhiteSpace(final.Technical))
                    {
                        final.Technical = standardError.Trim();
                    }
                    return final;
                }
            }
            return final;
        }

        private BootstrapContext EnsureBootstrap(IProgress<InstallerProgress> progress)
        {
            lock (_bootstrapLock)
            {
                if (_context == null)
                {
                    _context = new PackageBootstrap(_cacheOverride).EnsureReady(progress);
                }
                return _context;
            }
        }

        private static CoreResponse ParseResponse(Dictionary<string, object> payload)
        {
            object dataValue;
            var data = payload.TryGetValue("data", out dataValue)
                ? dataValue as Dictionary<string, object>
                : null;
            return new CoreResponse
            {
                Success = GetBool(payload, "success"),
                Action = GetString(payload, "action"),
                Message = GetString(payload, "message"),
                Technical = GetString(payload, "technical"),
                PackageId = GetString(payload, "package_id"),
                PackageIdentity = GetString(payload, "package_identity_sha256"),
                ModVersion = GetString(payload, "mod_version"),
                ClientVersion = GetString(payload, "client_version"),
                Data = data ?? new Dictionary<string, object>()
            };
        }

        private static string DefaultStateRoot(string gameRoot)
        {
            var baseRoot = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Kacksdev",
                "NIKKEPTBR",
                "state");
            var normalized = Path.GetFullPath(gameRoot).TrimEnd(Path.DirectorySeparatorChar).ToUpperInvariant();
            string key;
            using (var sha = SHA256.Create())
            {
                key = BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(normalized)))
                    .Replace("-", string.Empty)
                    .Substring(0, 20);
            }
            return Path.Combine(baseRoot, key);
        }

        private static string ActionName(InstallerAction action)
        {
            return action.ToString().ToLowerInvariant();
        }

        private static string GetString(IDictionary<string, object> payload, string key)
        {
            object value;
            return payload.TryGetValue(key, out value) && value != null
                ? Convert.ToString(value, CultureInfo.InvariantCulture)
                : string.Empty;
        }

        private static int GetInt(IDictionary<string, object> payload, string key)
        {
            object value;
            return payload.TryGetValue(key, out value) && value != null
                ? Convert.ToInt32(value, CultureInfo.InvariantCulture)
                : 0;
        }

        private static bool GetBool(IDictionary<string, object> payload, string key)
        {
            object value;
            return payload.TryGetValue(key, out value) && value != null &&
                   Convert.ToBoolean(value, CultureInfo.InvariantCulture);
        }

        private static string JoinArguments(IEnumerable<string> values)
        {
            var result = new StringBuilder();
            foreach (var value in values)
            {
                if (result.Length > 0)
                {
                    result.Append(' ');
                }
                result.Append(QuoteArgument(value ?? string.Empty));
            }
            return result.ToString();
        }

        private static string QuoteArgument(string value)
        {
            if (value.Length > 0 && value.IndexOfAny(new[] { ' ', '\t', '\n', '\v', '"' }) < 0)
            {
                return value;
            }
            var result = new StringBuilder();
            result.Append('"');
            var backslashes = 0;
            foreach (var character in value)
            {
                if (character == '\\')
                {
                    backslashes++;
                    continue;
                }
                if (character == '"')
                {
                    result.Append('\\', backslashes * 2 + 1);
                    result.Append('"');
                    backslashes = 0;
                    continue;
                }
                result.Append('\\', backslashes);
                backslashes = 0;
                result.Append(character);
            }
            result.Append('\\', backslashes * 2);
            result.Append('"');
            return result.ToString();
        }
    }
}
