using System;
using System.Collections.Generic;

namespace NIKKEPTBR.Installer
{
    public enum InstallerAction
    {
        Inspect,
        Install,
        Verify,
        Repair,
        Remove,
        Rollback
    }

    public sealed class InstallerProgress
    {
        public int Percent { get; set; }
        public string Phase { get; set; }
        public string Message { get; set; }
    }

    public sealed class CoreResponse
    {
        public bool Success { get; set; }
        public string Action { get; set; }
        public string Message { get; set; }
        public string Technical { get; set; }
        public string PackageId { get; set; }
        public string PackageIdentity { get; set; }
        public string ModVersion { get; set; }
        public string ClientVersion { get; set; }
        public Dictionary<string, object> Data { get; set; } = new Dictionary<string, object>();

        public string StringData(string key)
        {
            object value;
            return Data != null && Data.TryGetValue(key, out value) && value != null
                ? Convert.ToString(value)
                : string.Empty;
        }
    }

    internal sealed class BootstrapManifest
    {
        public int schema_version { get; set; }
        public string build_id { get; set; }
        public string package_identity_sha256 { get; set; }
        public List<BootstrapFile> files { get; set; } = new List<BootstrapFile>();
    }

    internal sealed class BootstrapFile
    {
        public string path { get; set; }
        public long size { get; set; }
        public string sha256 { get; set; }
    }

    internal sealed class BootstrapContext
    {
        public string Root { get; set; }
        public string CoreExecutable { get; set; }
        public string PackageRoot { get; set; }
    }

    internal sealed class HeadlessOptions
    {
        public InstallerAction Action { get; private set; } = InstallerAction.Inspect;
        public string GameRoot { get; private set; }
        public string ReportPath { get; private set; }
        public string StateRoot { get; private set; }
        public string CacheRoot { get; private set; }

        public static HeadlessOptions Parse(string[] args)
        {
            var result = new HeadlessOptions();
            for (var i = 0; i < args.Length; i++)
            {
                var value = args[i];
                if (EqualsOption(value, "--action") && i + 1 < args.Length)
                {
                    InstallerAction action;
                    if (!Enum.TryParse(args[++i], true, out action))
                    {
                        throw new ArgumentException("Ação headless inválida.");
                    }
                    result.Action = action;
                }
                else if (EqualsOption(value, "--game-root") && i + 1 < args.Length)
                {
                    result.GameRoot = System.IO.Path.GetFullPath(args[++i]);
                }
                else if (EqualsOption(value, "--report") && i + 1 < args.Length)
                {
                    result.ReportPath = System.IO.Path.GetFullPath(args[++i]);
                }
                else if (EqualsOption(value, "--state-root") && i + 1 < args.Length)
                {
                    result.StateRoot = System.IO.Path.GetFullPath(args[++i]);
                }
                else if (EqualsOption(value, "--cache-root") && i + 1 < args.Length)
                {
                    result.CacheRoot = System.IO.Path.GetFullPath(args[++i]);
                }
            }

            if (string.IsNullOrWhiteSpace(result.GameRoot))
            {
                result.GameRoot = GameDetector.Detect();
            }
            if (string.IsNullOrWhiteSpace(result.GameRoot))
            {
                throw new InvalidOperationException("Pasta oficial do NIKKE não localizada.");
            }
            if (string.IsNullOrWhiteSpace(result.ReportPath))
            {
                throw new ArgumentException("O modo headless exige --report.");
            }
            return result;
        }

        private static bool EqualsOption(string value, string expected)
        {
            return string.Equals(value, expected, StringComparison.OrdinalIgnoreCase);
        }
    }
}
