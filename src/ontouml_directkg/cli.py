"""DirectKG's file-based CLI, using the public Python converter and delivery API."""

import argparse
from errno import ELOOP, ENAMETOOLONG, ENOENT, ENOTDIR
from pathlib import Path
import sys

from .conversion import ConversionResult, convert
from .diagnostics import Diagnostic, DiagnosticsExportError
from .dkgm import DKGM_MODES
from .identity import ConfigurationError
from .provenance import SOFTWARE_VERSION


def _write_stream(text: str, stream) -> None:
    if stream is None:
        return
    try:
        stream.write(text)
    except UnicodeEncodeError:
        try:
            encoding = getattr(stream, "encoding", None) or "utf-8"
            safe = text.encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")
            stream.write(safe)
        except Exception:
            return
    except Exception:
        return
    try:
        stream.flush()
    except Exception:
        pass


class _SafeArgumentParser(argparse.ArgumentParser):
    def _print_message(self, message: str, file=None) -> None:
        if message:
            _write_stream(message, sys.stderr if file is None else file)


def build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(prog="ontouml-directkg", allow_abbrev=False,
                                 description="Convert VP-plugin 0.5.3 OntoUML JSON to Turtle.")
    parser.add_argument("input", type=Path, help="OntoUML JSON input file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Complete ontology output file path")
    parser.add_argument("--version", action="version", version=SOFTWARE_VERSION)
    parser.add_argument("--base-iri")
    parser.add_argument("--ontology-version-iri", metavar="IRI")
    parser.add_argument("--iri-strategy", choices=("name", "id"), default="name")
    parser.add_argument("--input-policy", choices=("strict", "tolerant", "best-effort"), default="tolerant")
    parser.add_argument("--stereotype-policy", choices=("require-known", "allow-missing", "allow-custom"), default="allow-custom")
    parser.add_argument("--inverse-properties", choices=("all", "informed", "named", "none"), default="all")
    parser.add_argument("--no-stereotype-relation-naming", action="store_true")
    parser.add_argument("--relation-labels", choices=("source-only", "generated"), default="source-only")
    parser.add_argument("--material-property-chains", choices=("none", "omit-conflicting-constraints", "preserve-conflicting-constraints"), default="none")
    parser.add_argument("--dkgm-vocabulary", choices=DKGM_MODES, default="import",
                        help="Supply the DKGM vocabulary by stable import, local core, or bridge-target declarations")
    parser.add_argument("--language")
    parser.add_argument("--omit-identifiers", action="store_true")
    parser.add_argument("--metadata-file", type=Path)
    parser.add_argument("--provenance", choices=("none", "embedded", "sidecar"), default="embedded")
    parser.add_argument("--diagnostics-file", type=Path)
    parser.add_argument("--console-level", choices=("info", "warning", "error"), default="info")
    return parser


def _console(event: Diagnostic) -> None:
    context = "; ".join(f"{source.element_type or 'source'} {source.identifier or ''} at {source.path}"
                        for source in event.sources)
    line = (f"[{event.severity}] {event.code}: {event.message} {event.effect}"
            + (" Sources: " + context if context else "")
            + (" Generated IRI: " + event.generated_iri if event.generated_iri else ""))
    _write_stream(line + "\n", sys.stderr)


def _finish(result: ConversionResult, threshold: str, report: Path | None, output: Path) -> bool:
    allowed = {"info": {"INFO", "WARNING", "ERROR"}, "warning": {"WARNING", "ERROR"}, "error": {"ERROR"}}
    for event in result.diagnostics:
        if event.severity in allowed[threshold]:
            _console(event)
    if report is not None:
        artifacts: tuple[Path, ...] = (output,)
        if result.provenance_mode == "sidecar":
            artifacts = (output, output.parent / (output.stem + ".provenance.ttl"))
        try:
            # Artifact replacement may have broken an alias since argument parsing.
            for artifact in artifacts:
                try:
                    aliases_artifact = report.samefile(artifact)
                except OSError as exc:
                    # Unresolvable paths have no file identity to compare.
                    if exc.errno not in {ENOENT, ENOTDIR, ELOOP, ENAMETOOLONG}:
                        raise
                    aliases_artifact = False
                if aliases_artifact:
                    raise OSError(f"destination refers to the same file as {artifact}")
                # A protected pathname can still alias the report when neither
                # destination exists, for example through a dangling symlink.
                try:
                    aliases_path = report.resolve(strict=False) == artifact.resolve(strict=False)
                except (OSError, ValueError, RuntimeError):
                    # Resolution failure alone does not establish an alias.
                    continue
                if aliases_path:
                    raise OSError(f"destination resolves to the same path as {artifact}")
            result.export_diagnostics(report)
        except Exception as exc:
            error = exc if isinstance(exc, DiagnosticsExportError) else DiagnosticsExportError(report, exc)
            _write_stream(f"[ERROR] DIAGNOSTICS_DELIVERY: {error}\n", sys.stderr)
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    report_written = True
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.diagnostics_file is not None:
            try:
                output = args.output.parent.resolve() / args.output.name
                artifacts = {output}
                if args.provenance == "sidecar":
                    artifacts.add(output.with_name(output.stem + ".provenance.ttl"))
                report = args.diagnostics_file
                seen = set()
                while True:
                    # Atomic Turtle delivery replaces the final directory entry,
                    # so check every report alias before following its next link.
                    report = report.parent.resolve() / report.name
                    if report in artifacts:
                        parser.error("The diagnostics file must have a different path from the ontology and provenance files")
                    if report in seen or not report.is_symlink():
                        break
                    seen.add(report)
                    target = report.readlink()
                    report = target if target.is_absolute() else report.parent / target
            except (OSError, ValueError, RuntimeError):
                # Unavailable destinations are reported by the actual delivery
                # operation, rather than changing its defined failure classification.
                pass
        options = vars(args).copy()
        for name in ("input", "output", "diagnostics_file", "console_level"):
            options.pop(name)
        try:
            result = convert(args.input, **options)
        except ConfigurationError as exc:
            parser.error(str(exc))
        delivered = None
        unexpected_error: Exception | None = None
        try:
            delivered = result.deliver(args.output)
        except Exception as exc:
            unexpected_error = exc
        finally:
            report_written = _finish(result, args.console_level, args.diagnostics_file, args.output)
        _write_stream(f"Transformation outcome: {result.outcome}\n", sys.stdout)
        if not report_written:
            return 4
        if unexpected_error is not None:
            _write_stream(
                f"[ERROR] RUNTIME_FAILURE: {type(unexpected_error).__name__}: {unexpected_error}\n",
                sys.stderr,
            )
            return 7
        if result.outcome == "aborted":
            return 3
        if any(failure.kind == "ontology" for failure in delivered.failures):
            return 6
        if delivered.failures:
            return 5
        return 1 if result.outcome == "completed-with-errors" else 0
    except Exception as exc:
        if not report_written:
            return 4
        _write_stream(f"[ERROR] RUNTIME_FAILURE: {type(exc).__name__}: {exc}\n", sys.stderr)
        return 7
