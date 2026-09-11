using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

namespace NIKKEPTBR.Installer
{
    internal sealed class PackageBootstrap
    {
        private const string ManifestName = "bootstrap-manifest.json";
        private const string ReadyMarker = ".ready";
        private readonly string _cacheBase;

        public PackageBootstrap(string cacheOverride = null)
        {
            _cacheBase = Path.GetFullPath(string.IsNullOrWhiteSpace(cacheOverride)
                ? Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "Kacksdev",
                    "NIKKEPTBR",
                    "cache")
                : cacheOverride);
        }

        public BootstrapContext EnsureReady(IProgress<InstallerProgress> progress)
        {
            if (BootstrapMetadata.ExpectedSize <= 0 ||
                string.Equals(BootstrapMetadata.ExpectedSha256, "PENDING_BUILD", StringComparison.Ordinal))
            {
                throw new InvalidOperationException("O pacote interno do instalador ainda não foi materializado.");
            }

            Directory.CreateDirectory(_cacheBase);
            var cacheRoot = Path.Combine(_cacheBase, BootstrapMetadata.BuildId);
            if (Directory.Exists(cacheRoot))
            {
                Report(progress, 4, "VALIDANDO CACHE", "Conferindo o pacote interno já preparado.");
                try
                {
                    ValidateExtracted(cacheRoot);
                    return CreateContext(cacheRoot);
                }
                catch
                {
                    SafeDeleteDirectory(cacheRoot, _cacheBase);
                }
            }

            var staging = Path.Combine(_cacheBase, ".staging-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(staging);
            try
            {
                Report(progress, 5, "PREPARANDO", "Abrindo os componentes internos verificados.");
                ExtractEmbedded(staging, progress);
                Report(progress, 17, "VALIDANDO", "Conferindo cada componente por SHA-256.");
                ValidateExtracted(staging);
                File.WriteAllText(
                    Path.Combine(staging, ReadyMarker),
                    BootstrapMetadata.ExpectedSha256 + Environment.NewLine,
                    new UTF8Encoding(false));

                if (Directory.Exists(cacheRoot))
                {
                    SafeDeleteDirectory(cacheRoot, _cacheBase);
                }
                Directory.Move(staging, cacheRoot);
                Report(progress, 20, "PACOTE PRONTO", "Componentes internos preparados com integridade confirmada.");
                return CreateContext(cacheRoot);
            }
            catch
            {
                if (Directory.Exists(staging))
                {
                    SafeDeleteDirectory(staging, _cacheBase);
                }
                throw;
            }
        }

        private static BootstrapContext CreateContext(string root)
        {
            var context = new BootstrapContext
            {
                Root = root,
                CoreExecutable = ResolveInside(root, BootstrapMetadata.CoreRelativePath),
                PackageRoot = ResolveInside(root, BootstrapMetadata.PackageRelativePath)
            };
            if (!File.Exists(context.CoreExecutable))
            {
                throw new InvalidDataException("Executável interno do instalador ausente.");
            }
            if (!Directory.Exists(context.PackageRoot))
            {
                throw new InvalidDataException("Pacote da tradução ausente.");
            }
            return context;
        }

        private static void ExtractEmbedded(string destinationRoot, IProgress<InstallerProgress> progress)
        {
            var assembly = Assembly.GetExecutingAssembly();
            using (var resource = assembly.GetManifestResourceStream(BootstrapMetadata.ResourceName))
            {
                if (resource == null)
                {
                    throw new InvalidDataException("Recurso interno do instalador não encontrado.");
                }
                if (resource.Length != BootstrapMetadata.ExpectedSize)
                {
                    throw new InvalidDataException("Tamanho do pacote interno divergente.");
                }
                var actualHash = ComputeHash(resource);
                if (!string.Equals(actualHash, BootstrapMetadata.ExpectedSha256, StringComparison.OrdinalIgnoreCase))
                {
                    throw new InvalidDataException("Integridade do pacote interno inválida.");
                }
                resource.Position = 0;

                using (var archive = new ZipArchive(resource, ZipArchiveMode.Read, leaveOpen: false))
                {
                    var total = archive.Entries.Where(entry => !IsDirectory(entry)).Sum(entry => entry.Length);
                    long completed = 0;
                    foreach (var entry in archive.Entries.OrderBy(entry => entry.FullName, StringComparer.Ordinal))
                    {
                        if (IsDirectory(entry))
                        {
                            continue;
                        }
                        var destination = ResolveInside(destinationRoot, entry.FullName);
                        Directory.CreateDirectory(Path.GetDirectoryName(destination));
                        using (var input = entry.Open())
                        using (var output = new FileStream(
                            destination,
                            FileMode.CreateNew,
                            FileAccess.Write,
                            FileShare.None,
                            1024 * 1024,
                            FileOptions.SequentialScan))
                        {
                            var buffer = new byte[1024 * 1024];
                            int read;
                            while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                            {
                                output.Write(buffer, 0, read);
                                completed += read;
                                var percent = 5 + (total == 0 ? 0 : (int)(10L * completed / total));
                                Report(progress, percent, "PREPARANDO", "Extraindo os componentes da tradução.");
                            }
                            output.Flush(true);
                        }
                    }
                }
            }
        }

        private static void ValidateExtracted(string root)
        {
            var manifestPath = ResolveInside(root, ManifestName);
            if (!File.Exists(manifestPath))
            {
                throw new InvalidDataException("Manifesto interno ausente.");
            }
            var serializer = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
            var manifest = serializer.Deserialize<BootstrapManifest>(File.ReadAllText(manifestPath, Encoding.UTF8));
            if (manifest == null || manifest.schema_version != 1 || manifest.files == null)
            {
                throw new InvalidDataException("Manifesto interno inválido.");
            }
            if (!string.Equals(manifest.build_id, BootstrapMetadata.BuildId, StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidDataException("Identidade do pacote interno divergente.");
            }

            var expected = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var record in manifest.files)
            {
                var normalized = NormalizeRelative(record.path);
                if (!expected.Add(normalized))
                {
                    throw new InvalidDataException("Entrada duplicada no pacote interno: " + normalized);
                }
                var path = ResolveInside(root, normalized);
                if (!File.Exists(path))
                {
                    throw new InvalidDataException("Componente interno ausente: " + normalized);
                }
                var info = new FileInfo(path);
                if (info.Length != record.size ||
                    !string.Equals(ComputeHash(path), record.sha256, StringComparison.OrdinalIgnoreCase))
                {
                    throw new InvalidDataException("Componente interno adulterado: " + normalized);
                }
            }

            var observed = new HashSet<string>(
                Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
                    .Select(path => NormalizeRelative(RelativePath(root, path)))
                    .Where(path => !string.Equals(path, ManifestName, StringComparison.OrdinalIgnoreCase) &&
                                   !string.Equals(path, ReadyMarker, StringComparison.OrdinalIgnoreCase)),
                StringComparer.OrdinalIgnoreCase);
            if (!expected.SetEquals(observed))
            {
                throw new InvalidDataException("Conjunto de arquivos do pacote interno divergente.");
            }
        }

        private static string RelativePath(string root, string path)
        {
            var rootUri = new Uri(AppendSeparator(Path.GetFullPath(root)));
            var pathUri = new Uri(Path.GetFullPath(path));
            return Uri.UnescapeDataString(rootUri.MakeRelativeUri(pathUri).ToString())
                .Replace('/', Path.DirectorySeparatorChar);
        }

        private static string AppendSeparator(string path)
        {
            return path.EndsWith(Path.DirectorySeparatorChar.ToString(), StringComparison.Ordinal)
                ? path
                : path + Path.DirectorySeparatorChar;
        }

        private static string NormalizeRelative(string path)
        {
            return (path ?? string.Empty).Replace('\\', '/').TrimStart('/');
        }

        private static string ResolveInside(string root, string relative)
        {
            if (string.IsNullOrWhiteSpace(relative) || Path.IsPathRooted(relative) || relative.Contains(":"))
            {
                throw new InvalidDataException("Caminho interno inválido.");
            }
            var normalized = relative.Replace('/', Path.DirectorySeparatorChar);
            var fullRoot = Path.GetFullPath(root);
            var candidate = Path.GetFullPath(Path.Combine(fullRoot, normalized));
            var prefix = AppendSeparator(fullRoot);
            if (!candidate.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidDataException("Caminho interno escapou do pacote.");
            }
            return candidate;
        }

        private static bool IsDirectory(ZipArchiveEntry entry)
        {
            return string.IsNullOrEmpty(entry.Name) &&
                   (entry.FullName.EndsWith("/", StringComparison.Ordinal) ||
                    entry.FullName.EndsWith("\\", StringComparison.Ordinal));
        }

        private static string ComputeHash(string path)
        {
            using (var stream = new FileStream(
                path,
                FileMode.Open,
                FileAccess.Read,
                FileShare.Read,
                1024 * 1024,
                FileOptions.SequentialScan))
            {
                return ComputeHash(stream);
            }
        }

        private static string ComputeHash(Stream stream)
        {
            using (var sha = SHA256.Create())
            {
                return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty);
            }
        }

        private static void SafeDeleteDirectory(string target, string allowedParent)
        {
            var parent = Path.GetFullPath(allowedParent);
            var candidate = Path.GetFullPath(target);
            if (!candidate.StartsWith(AppendSeparator(parent), StringComparison.OrdinalIgnoreCase) ||
                string.Equals(candidate, parent, StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException("Recusa de remoção fora do cache autorizado.");
            }
            Directory.Delete(candidate, recursive: true);
        }

        private static void Report(IProgress<InstallerProgress> progress, int percent, string phase, string message)
        {
            progress?.Report(new InstallerProgress
            {
                Percent = percent,
                Phase = phase,
                Message = message
            });
        }
    }
}
