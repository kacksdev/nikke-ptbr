using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;

namespace NIKKEPTBR.Installer
{
    public static class GameDetector
    {
        private static readonly string[] RequiredFiles =
        {
            "nikke.exe",
            "UnityPlayer.dll",
            "GameAssembly.dll"
        };

        public static string Detect()
        {
            foreach (var candidate in CandidateRoots())
            {
                var normalized = Normalize(candidate);
                if (!string.IsNullOrWhiteSpace(normalized))
                {
                    return normalized;
                }
            }
            return null;
        }

        public static string Normalize(string requested)
        {
            if (string.IsNullOrWhiteSpace(requested))
            {
                return null;
            }
            try
            {
                var basePath = File.Exists(requested)
                    ? Path.GetDirectoryName(Path.GetFullPath(requested))
                    : Path.GetFullPath(requested);
                var variants = new[]
                {
                    basePath,
                    Path.Combine(basePath, "game"),
                    Path.Combine(basePath, "NIKKE", "game"),
                    Path.Combine(basePath, "NIKKE", "NIKKE", "game")
                };
                return variants.FirstOrDefault(IsClientRoot);
            }
            catch
            {
                return null;
            }
        }

        public static bool IsClientRoot(string path)
        {
            return !string.IsNullOrWhiteSpace(path) &&
                   Directory.Exists(path) &&
                   RequiredFiles.All(name => File.Exists(Path.Combine(path, name)));
        }

        private static IEnumerable<string> CandidateRoots()
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var candidate in RawCandidates())
            {
                if (string.IsNullOrWhiteSpace(candidate))
                {
                    continue;
                }
                string full;
                try
                {
                    full = Path.GetFullPath(candidate);
                }
                catch
                {
                    continue;
                }
                if (seen.Add(full))
                {
                    yield return full;
                }
            }
        }

        private static IEnumerable<string> RawCandidates()
        {
            var environment = Environment.GetEnvironmentVariable("NIKKE_GAME_ROOT");
            if (!string.IsNullOrWhiteSpace(environment))
            {
                yield return environment;
            }
            yield return AppDomain.CurrentDomain.BaseDirectory;
            yield return Environment.CurrentDirectory;

            foreach (var processName in new[] { "nikke", "nikke_launcher" })
            {
                foreach (var process in Process.GetProcessesByName(processName))
                {
                    using (process)
                    {
                        string executable = null;
                        try
                        {
                            executable = process.MainModule?.FileName;
                        }
                        catch
                        {
                        }
                        if (!string.IsNullOrWhiteSpace(executable))
                        {
                            yield return Path.GetDirectoryName(executable);
                        }
                    }
                }
            }

            foreach (var location in RegistryLocations())
            {
                yield return location;
            }

            foreach (var drive in DriveInfo.GetDrives().Where(item => item.IsReady && item.DriveType == DriveType.Fixed))
            {
                var root = drive.RootDirectory.FullName;
                yield return Path.Combine(root, "Games", "NIKKE", "NIKKE", "game");
                yield return Path.Combine(root, "Games", "NIKKE");
                yield return Path.Combine(root, "NIKKE", "NIKKE", "game");
                yield return Path.Combine(root, "NIKKE");
                yield return Path.Combine(root, "Level Infinite", "NIKKE");
                yield return Path.Combine(root, "Program Files", "NIKKE");
                yield return Path.Combine(root, "Program Files (x86)", "NIKKE");
            }
        }

        private static IEnumerable<string> RegistryLocations()
        {
            var locations = new List<string>();
            foreach (var hive in new[] { RegistryHive.CurrentUser, RegistryHive.LocalMachine })
            {
                foreach (var view in new[] { RegistryView.Registry64, RegistryView.Registry32 })
                {
                    try
                    {
                        using (var root = RegistryKey.OpenBaseKey(hive, view))
                        using (var uninstall = root.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"))
                        {
                            if (uninstall == null)
                            {
                                continue;
                            }
                            foreach (var name in uninstall.GetSubKeyNames())
                            {
                                using (var key = uninstall.OpenSubKey(name))
                                {
                                    var display = Convert.ToString(key?.GetValue("DisplayName"));
                                    if (display?.IndexOf("NIKKE", StringComparison.OrdinalIgnoreCase) < 0 &&
                                        display?.IndexOf("GODDESS OF VICTORY", StringComparison.OrdinalIgnoreCase) < 0)
                                    {
                                        continue;
                                    }
                                    var install = Convert.ToString(key?.GetValue("InstallLocation"));
                                    if (!string.IsNullOrWhiteSpace(install))
                                    {
                                        locations.Add(install.Trim('"'));
                                    }
                                }
                            }
                        }
                    }
                    catch
                    {
                    }
                }
            }
            return locations;
        }
    }
}
