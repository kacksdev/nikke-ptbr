from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if TOOLS.is_dir():
    sys.path.insert(0, str(TOOLS))

from runtime_installer_core import InstallerError, RuntimeInstallerTransaction  # noqa: E402
from runtime_release_package import verify_runtime_package  # noqa: E402


EventSink = Callable[[dict[str, Any]], None]
ACTIVE_STAGES = {"installing", "repairing", "removing"}


def emit_json(event: dict[str, Any]) -> None:
    # Keep the pipe strictly ASCII. JSON escapes preserve every Portuguese character
    # while avoiding locale-dependent decoding in the .NET Framework host.
    print(json.dumps(event, ensure_ascii=True, separators=(",", ":")), flush=True)


def progress(
    sink: EventSink,
    percent: int,
    phase: str,
    message: str,
    **extra: Any,
) -> None:
    event: dict[str, Any] = {
        "type": "progress",
        "percent": max(0, min(100, int(percent))),
        "phase": phase,
        "message": message,
    }
    event.update(extra)
    sink(event)


def friendly_error(error: BaseException) -> str:
    raw = str(error)
    lowered = raw.lower()
    if "processes must be closed" in lowered:
        return "Feche o jogo e o launcher do NIKKE antes de continuar."
    if "unsupported or updated nikke client fingerprint" in lowered:
        return (
            "A versão instalada do NIKKE ainda não corresponde ao cliente validado "
            "por este pacote. Nenhum arquivo foi alterado."
        )
    if "runtime target fingerprint mismatch" in lowered:
        return (
            "O cliente instalado não corresponde à versão validada pelo mod. "
            "Nenhum arquivo foi alterado."
        )
    if "unknown existing mod targets" in lowered:
        return (
            "Foi encontrado outro componente no mesmo ponto de integração. "
            "O instalador recusou sobrescrevê-lo para proteger o cliente."
        )
    if "runtime output collision" in lowered:
        return (
            "Existe uma pasta de execução que não pertence a esta instalação. "
            "O instalador interrompeu a operação sem substituir nada."
        )
    if "requires repair" in lowered:
        return "A instalação existe, mas precisa ser reparada antes de continuar."
    if "matching installation state is required" in lowered:
        return "Não foi encontrada uma instalação do mod pertencente a este instalador."
    if "refusing to remove changed" in lowered or "changed owned targets" in lowered:
        return (
            "Um componente instalado foi alterado depois da instalação. "
            "A remoção foi interrompida para preservar esses dados. Use Reparar primeiro."
        )
    if "another transaction is pending" in lowered:
        return (
            "Existe uma operação anterior incompleta. Retome a ação indicada antes de "
            "iniciar outra operação."
        )
    if isinstance(error, PermissionError) or "access is denied" in lowered:
        return (
            "O Windows bloqueou a gravação nessa pasta. Reinicie o instalador como "
            "administrador e tente novamente."
        )
    return raw or error.__class__.__name__


def classify_inspection(transaction: RuntimeInstallerTransaction) -> dict[str, Any]:
    official = transaction._verify_client_compatibility()
    artifacts = transaction._artifact_states()
    runtime_output = transaction._scan_runtime_output()
    state = transaction._read_installation_state()
    journal = transaction._load_journal()
    exact = all(record["state"] == "exact" for record in artifacts.values())
    missing = all(record["state"] == "missing" for record in artifacts.values())
    matching = transaction._matching_state(state)
    stage = str(journal.get("stage", "")) if journal else ""
    operation = str(journal.get("operation", "")) if journal else ""

    if stage in ACTIVE_STAGES and operation in {"install", "repair", "remove"}:
        health = "recovery_required"
        recommended_action = operation
        summary = "Uma operação anterior foi interrompida e pode ser retomada com segurança."
    elif matching and state and state.get("status") == "installed" and exact:
        health = "installed_verified"
        recommended_action = "verify"
        summary = "A tradução está instalada e todos os componentes conferem."
    elif matching and state and state.get("status") == "installed":
        health = "repair_required"
        recommended_action = "repair"
        summary = "A instalação foi reconhecida, mas um ou mais componentes precisam de reparo."
    elif matching and state and state.get("status") == "removed" and missing:
        health = "not_installed"
        recommended_action = "install"
        summary = "A tradução não está instalada neste cliente."
    elif state is None and missing and not runtime_output:
        health = "not_installed"
        recommended_action = "install"
        summary = "Cliente compatível encontrado e pronto para receber a tradução."
    else:
        health = "blocked_unknown_state"
        recommended_action = "none"
        summary = (
            "Foram encontrados componentes ou um estado que não pertencem com segurança "
            "a este pacote. Nada será sobrescrito automaticamente."
        )

    return {
        "health": health,
        "recommended_action": recommended_action,
        "summary": summary,
        "artifact_states": artifacts,
        "runtime_output": runtime_output,
        "installation_state_status": state.get("status") if state else None,
        "matching_installation_state": matching,
        "pending_transaction": (
            {
                "operation": operation,
                "stage": stage,
                "next_action": journal.get("next_action"),
            }
            if journal
            else None
        ),
        "official_snapshot": official,
    }


def attach_journal_progress(
    transaction: RuntimeInstallerTransaction,
    sink: EventSink,
) -> None:
    original = transaction._save_journal
    payload_count = max(1, len(transaction.package.payloads))

    def observed(journal: dict[str, Any]) -> None:
        original(journal)
        stage = str(journal.get("stage", ""))
        operation = str(journal.get("operation", ""))
        completed = 0
        if operation == "install":
            completed = len(journal.get("added", []))
        elif operation == "repair":
            completed = len(journal.get("repaired", []))
        elif operation == "remove":
            completed = len(journal.get("removed", []))

        phase_messages = {
            "installing": ("INSTALANDO", "Aplicando componentes verificados."),
            "installed_verified": ("INSTALAÇÃO VERIFICADA", "Instalação concluída e conferida."),
            "install_rolled_back_verified": ("ROLLBACK CONCLUÍDO", "O estado anterior foi restaurado."),
            "repairing": ("REPARANDO", "Restaurando componentes da tradução."),
            "repair_verified": ("REPARO VERIFICADO", "Reparo concluído e conferido."),
            "repair_rolled_back_verified": ("ROLLBACK CONCLUÍDO", "O estado anterior foi restaurado."),
            "removing": ("REMOVENDO", "Removendo somente componentes pertencentes ao mod."),
            "removed_verified": ("REMOÇÃO VERIFICADA", "A tradução foi removida com segurança."),
            "remove_rolled_back_to_installed": ("ROLLBACK CONCLUÍDO", "A instalação anterior foi restaurada."),
        }
        phase, message = phase_messages.get(stage, ("PROCESSANDO", "Atualizando o estado transacional."))
        if stage.endswith("_verified"):
            percent = 96
        elif "rolled_back" in stage:
            percent = 88
        else:
            percent = 24 + int(68 * completed / payload_count)
        progress(
            sink,
            percent,
            phase,
            message,
            stage=stage,
            operation=operation,
            completed_files=completed,
            total_files=payload_count,
        )

    transaction._save_journal = observed  # type: ignore[method-assign]


def execute(
    *,
    action: str,
    package_root: Path,
    target_root: Path,
    state_root: Path,
    allowed_target_parent: Path | None,
    forbidden_roots: Iterable[Path] = (),
    sink: EventSink = emit_json,
) -> dict[str, Any]:
    progress(sink, 2, "PREPARANDO", "Validando o pacote interno do instalador.")
    package = verify_runtime_package(package_root)
    progress(sink, 14, "PACOTE VALIDADO", "Integridade e proveniência do pacote confirmadas.")

    transaction = RuntimeInstallerTransaction(
        package=package,
        target_root=target_root,
        state_root=state_root,
        allowed_target_parent=allowed_target_parent,
        forbidden_roots=forbidden_roots,
    )
    attach_journal_progress(transaction, sink)
    progress(sink, 20, "CLIENTE VALIDADO", "Identidade do cliente e estado local confirmados.")

    if action == "inspect":
        data = classify_inspection(transaction)
    elif action == "install":
        data = transaction.install()
    elif action == "verify":
        data = transaction.verify_installed()
        if not data.get("installed"):
            raise InstallerError("The installed translation did not pass verification.")
    elif action == "repair":
        data = transaction.repair()
    elif action == "remove":
        data = transaction.remove()
    elif action == "rollback":
        data = transaction.rollback_pending()
    else:
        raise InstallerError(f"Unsupported installer action: {action}")

    progress(sink, 100, "CONCLUÍDO", "Operação concluída com verificação integral.")
    return {
        "success": True,
        "action": action,
        "package_id": package.package_id,
        "package_identity_sha256": package.package_identity,
        "mod_version": package.manifest["mod_version"],
        "client_version": package.manifest["client_compatibility"]["version"],
        "data": data,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NIKKE PT-BR transactional installer core")
    parser.add_argument(
        "--action",
        required=True,
        choices=("inspect", "install", "verify", "repair", "remove", "rollback"),
    )
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--allowed-target-parent", type=Path)
    parser.add_argument("--forbidden-root", action="append", default=[], type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = execute(
            action=args.action,
            package_root=args.package_root,
            target_root=args.target_root,
            state_root=args.state_root,
            allowed_target_parent=args.allowed_target_parent,
            forbidden_roots=args.forbidden_root,
        )
    except BaseException as error:
        emit_json(
            {
                "type": "result",
                "success": False,
                "action": args.action,
                "message": friendly_error(error),
                "technical": str(error),
                "error_type": error.__class__.__name__,
            }
        )
        return 1

    event = {"type": "result"}
    event.update(result)
    emit_json(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
