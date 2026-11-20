import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

MAX_EXTRA_FILES = 8
IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}


def log(msg: str) -> None:
    print(f"[AgentReview] {msg}", flush=True)


def load_event_data() -> dict:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not Path(event_path).exists():
        log("GITHUB_EVENT_PATH não encontrado ou inválido.")
        sys.exit(0)

    with open(event_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file_safely(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def list_repo_files() -> list[str]:
    root = Path(".").resolve()
    files: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        files.append(str(p.relative_to(root)))
    return sorted(files)


def is_safe_repo_path(rel_path: str) -> bool:
    """Impede path traversal e bloqueia alteração de workflows ou arquivos .env."""
    root = Path(".").resolve()
    try:
        resolved = (root / rel_path).resolve()
        resolved.relative_to(root)
    except (ValueError, RuntimeError):
        return False

    normalized = rel_path.replace("\\", "/").lstrip("./")
    if normalized.startswith(".git/") or normalized.startswith(".github/workflows/"):
        return False
    if Path(normalized).name.startswith(".env") and Path(normalized).name != ".env.example":
        return False
    return True


def resolve_model(comment_body: str) -> tuple[str, str]:
    """Resolve o modelo via override [model: ...] no comentário ou variável AI_MODEL."""
    default_model = os.environ.get("AI_MODEL", "").strip() or "gemini-2.5-flash"
    match = re.search(r"\[model:\s*([a-zA-Z0-9._-]+)\]", comment_body, re.IGNORECASE)
    if match:
        chosen = match.group(1).strip()
        cleaned_body = re.sub(r"\[model:\s*[a-zA-Z0-9._-]+\]", "", comment_body, flags=re.IGNORECASE).strip()
        return chosen, cleaned_body
    return default_model, comment_body


def call_gemini_api(
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: dict,
) -> tuple[dict, dict, float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            elapsed = time.monotonic() - start
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage_metadata = data.get("usageMetadata", {})
            return json.loads(candidate_text), usage_metadata, elapsed
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        log(f"Erro HTTP {e.code} na API Gemini (modelo={model_name}): {err_msg}")
        raise
    except Exception as e:
        log(f"Erro inesperado ao chamar Gemini: {e}")
        raise


def run_tests(changed_paths: list[str]) -> tuple[bool, str]:
    touches_backend = any(p.startswith("backend/") for p in changed_paths)
    if touches_backend and Path("backend").exists():
        log("Executando pytest no backend...")
        venv_pytest = Path("backend/.venv/bin/pytest")
        cmd = [str(venv_pytest.resolve()), "-q"] if venv_pytest.exists() else ["pytest", "-q"]
        res = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )
        return (res.returncode == 0, (res.stdout + "\n" + res.stderr).strip())
    return (True, "Validação de testes não aplicável aos arquivos alterados.")


def reply_to_comment(
    repo_full_name: str,
    pull_number: int,
    thread_comment_id: int,
    message: str,
    github_token: str,
) -> None:
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pull_number}/comments/{thread_comment_id}/replies"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "Hstronomia-Agent-Review",
    }
    payload = {"body": message}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log(f"Comentário respondido com sucesso (HTTP {resp.status}).")
    except Exception as e:
        log(f"Erro ao responder comentário de PR: {e}")


def write_step_summary(
    model_name: str,
    changed_paths: list[str],
    status_label: str,
    tokens_in: int,
    tokens_out: int,
    elapsed: float,
) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    total = tokens_in + tokens_out
    files_str = ", ".join(f"`{p}`" for p in changed_paths) if changed_paths else "nenhum"
    md = (
        f"### 🤖 Agent PR Review Summary\n\n"
        f"| Campo | Valor |\n"
        f"| :--- | :--- |\n"
        f"| **Status** | {status_label} |\n"
        f"| **Modelo** | `{model_name}` |\n"
        f"| **Arquivos Alterados** | {files_str} |\n"
        f"| **Tokens (Entrada / Saída / Total)** | `{tokens_in:,}` / `{tokens_out:,}` / `{total:,}` |\n"
        f"| **Latência IA** | `{elapsed:.2f}s` |\n"
    )
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(md)


def sanitize_commit_message(raw_msg: str) -> str:
    first_line = raw_msg.strip().splitlines()[0] if raw_msg.strip() else "refactor(review): aplicar ajuste de revisao"
    return first_line[:72]


def rollback_changes(snapshots: dict[str, str | None]) -> None:
    for rel_path, original_content in snapshots.items():
        p = Path(rel_path)
        if original_content is None:
            if p.exists():
                p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(original_content)


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")

    if not api_key or not github_token:
        log("GEMINI_API_KEY ou GITHUB_TOKEN não configurados. Abortando.")
        sys.exit(0)

    event_data = load_event_data()
    comment = event_data.get("comment", {})
    pull_request = event_data.get("pull_request", {})
    repository = event_data.get("repository", {})

    comment_author = comment.get("user", {}).get("login", "")
    repo_owner = repository.get("owner", {}).get("login", "")

    if comment_author != repo_owner:
        log(f"Ignorado: autor '{comment_author}' != dono '{repo_owner}'.")
        sys.exit(0)

    if comment.get("user", {}).get("type") == "Bot" or "github-actions" in comment_author:
        log("Ignorado: comentário de bot.")
        sys.exit(0)

    raw_comment_body = comment.get("body", "").strip()
    file_path_str = comment.get("path")
    diff_hunk = comment.get("diff_hunk", "")
    thread_comment_id = comment.get("in_reply_to_id") or comment.get("id")
    pull_number = pull_request.get("number")
    repo_full_name = repository.get("full_name")
    branch_name = pull_request.get("head", {}).get("ref")

    if not file_path_str or not thread_comment_id or not pull_number or not branch_name:
        log("Payload incompleto no evento. Abortando.")
        sys.exit(0)

    target_file = Path(file_path_str)
    if not target_file.exists():
        log(f"Arquivo alvo '{target_file}' não encontrado.")
        sys.exit(0)

    model_name, comment_body = resolve_model(raw_comment_body)
    file_content = read_file_safely(target_file)
    agents_rules = read_file_safely(Path("AGENTS.md"))
    repo_files = list_repo_files()

    total_tokens_in = 0
    total_tokens_out = 0
    total_elapsed = 0.0

    # --- PASSO 1: Seleção cirúrgica de arquivos extras necessários ---
    select_schema = {
        "type": "OBJECT",
        "properties": {
            "files_to_read": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": f"Lista de até {MAX_EXTRA_FILES} caminhos relativos extras do repositório necessários para entender/implementar a mudança (ex: schemas, services, deps, tests). Retorne vazio se apenas o arquivo comentado bastar.",
            }
        },
        "required": ["files_to_read"],
    }

    select_prompt = f"""Comentário de revisão no arquivo '{file_path_str}':
"{comment_body}"

Trecho do diff (diff_hunk):
```
{diff_hunk}
```

Arquivos disponíveis no repositório:
{chr(10).join(repo_files)}

Selecione apenas os arquivos adicionais estritamente necessários para implementar e testar esta mudança (máximo {MAX_EXTRA_FILES}). Não inclua '{file_path_str}' pois ele já será fornecido."""

    log(f"[Passo 1/2] Identificando arquivos relacionados com '{model_name}'...")
    try:
        sel_resp, sel_usage, sel_elapsed = call_gemini_api(
            api_key,
            model_name,
            "Você seleciona o menor conjunto de arquivos necessários para uma revisão de código.",
            select_prompt,
            select_schema,
        )
    except Exception as e:
        reply_to_comment(
            repo_full_name,
            pull_number,
            thread_comment_id,
            f"❌ **Erro ao consultar o modelo `{model_name}`**: `{e}`\n\nVerifique se o nome do modelo em `AI_MODEL` está disponível na sua chave `GEMINI_API_KEY`.",
            github_token,
        )
        sys.exit(1)

    total_tokens_in += sel_usage.get("promptTokenCount", 0)
    total_tokens_out += sel_usage.get("candidatesTokenCount", 0)
    total_elapsed += sel_elapsed

    extra_files: list[str] = []
    for p in sel_resp.get("files_to_read", [])[:MAX_EXTRA_FILES]:
        if p != file_path_str and p in repo_files and is_safe_repo_path(p):
            extra_files.append(p)

    log(f"Arquivos extras selecionados: {extra_files or 'nenhum'}")

    # --- PASSO 2: Edição multi-arquivo ---
    context_blocks = [f"### Arquivo comentado: {file_path_str}\n```\n{file_content}\n```"]
    for extra in extra_files:
        content = read_file_safely(Path(extra))
        context_blocks.append(f"### Arquivo relacionado: {extra}\n```\n{content}\n```")

    edit_schema = {
        "type": "OBJECT",
        "properties": {
            "commit_message": {
                "type": "STRING",
                "description": "Mensagem de commit em uma linha no padrão Conventional Commits.",
            },
            "explanation": {
                "type": "STRING",
                "description": "Explicação técnica, concisa e direta em português do que foi alterado.",
            },
            "changes": {
                "type": "ARRAY",
                "description": "Lista de arquivos modificados ou criados. Inclua apenas os arquivos que realmente mudaram.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {"type": "STRING", "description": "Caminho relativo no repositório."},
                        "content": {"type": "STRING", "description": "Conteúdo integral atualizado do arquivo."},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        "required": ["commit_message", "explanation", "changes"],
    }

    system_prompt = f"""Você é o engenheiro responsável por atender revisões de PR no repositório Hstronomia.
Siga rigorosamente as diretrizes do projeto extraídas de AGENTS.md:
---
{agents_rules}
---
Regras de execução (Modo Ponytail):
- Faça estritamente a menor alteração cirúrgica completa necessária para atender ao comentário do revisor.
- Você pode alterar múltiplos arquivos simultaneamente (ex: schema, service, deps, controller e testes) quando a mudança exigir.
- Não refatore trechos fora do escopo pedido, não adicione dependências novas e evite over-engineering.
- Preserve isolamento multi-tenant (restaurante_id), precisão Decimal em valores monetários e práticas OWASP.
- Em 'changes', inclua apenas arquivos modificados/criados, sempre com o conteúdo integral atualizado.
"""

    edit_prompt = f"""Comentário de revisão no arquivo '{file_path_str}':
"{comment_body}"

Trecho do diff (diff_hunk):
```
{diff_hunk}
```

Contexto dos arquivos:
{chr(10).join(context_blocks)}
"""

    log(f"[Passo 2/2] Gerando alterações multi-arquivo com '{model_name}'...")
    try:
        ai_response, edit_usage, edit_elapsed = call_gemini_api(
            api_key, model_name, system_prompt, edit_prompt, edit_schema
        )
    except Exception as e:
        reply_to_comment(
            repo_full_name,
            pull_number,
            thread_comment_id,
            f"❌ **Erro ao gerar alterações com `{model_name}`**: `{e}`",
            github_token,
        )
        sys.exit(1)

    total_tokens_in += edit_usage.get("promptTokenCount", 0)
    total_tokens_out += edit_usage.get("candidatesTokenCount", 0)
    total_elapsed += edit_elapsed

    changes = ai_response.get("changes", [])
    explanation = ai_response.get("explanation", "Alterações aplicadas conforme solicitado.")
    commit_msg = sanitize_commit_message(ai_response.get("commit_message", ""))

    # Filtra apenas mudanças reais e seguras
    snapshots: dict[str, str | None] = {}
    applied_paths: list[str] = []

    for change in changes:
        rel_path = change.get("path", "").strip()
        new_content = change.get("content", "")
        if not rel_path or not is_safe_repo_path(rel_path):
            log(f"Caminho ignorado por segurança: '{rel_path}'")
            continue

        p = Path(rel_path)
        original = read_file_safely(p) if p.exists() else None
        if original is not None and original.strip() == new_content.strip():
            continue

        snapshots[rel_path] = original
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(new_content)
        applied_paths.append(rel_path)

    if not applied_paths:
        log("Nenhuma modificação efetiva detectada.")
        write_step_summary(model_name, [], "Sem alterações", total_tokens_in, total_tokens_out, total_elapsed)
        reply_to_comment(
            repo_full_name,
            pull_number,
            thread_comment_id,
            f"ℹ️ **Análise concluída** (sem alterações no código):\n\n{explanation}\n\n---\n> 🤖 `{model_name}` • Tokens: `{total_tokens_in:,}` in / `{total_tokens_out:,}` out • `{total_elapsed:.2f}s`",
            github_token,
        )
        sys.exit(0)

    log(f"Arquivos alterados ({len(applied_paths)}): {applied_paths}")
    tests_ok, test_logs = run_tests(applied_paths)

    if not tests_ok:
        log("Testes falharam. Executando rollback atômico.")
        rollback_changes(snapshots)
        write_step_summary(
            model_name, applied_paths, "❌ Testes falharam (revertido)", total_tokens_in, total_tokens_out, total_elapsed
        )
        erro_msg = (
            f"❌ **Alterações revertidas: a suíte de testes (`pytest`) falhou.**\n\n"
            f"```\n{test_logs[-1500:]}\n```\n\n"
            f"---\n"
            f"> 🤖 `{model_name}` • Tokens: `{total_tokens_in:,}` in / `{total_tokens_out:,}` out • `{total_elapsed:.2f}s`"
        )
        reply_to_comment(repo_full_name, pull_number, thread_comment_id, erro_msg, github_token)
        sys.exit(1)

    log(f"Testes aprovados. Commitando: {commit_msg}")
    subprocess.run(["git", "add", "--", *applied_paths], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    write_step_summary(
        model_name, applied_paths, "✅ Aplicado e validado", total_tokens_in, total_tokens_out, total_elapsed
    )

    files_list = "\n".join(f"- `{p}`" for p in applied_paths)
    resposta_pr = (
        f"✅ **Alterações aplicadas e validadas!**\n\n"
        f"{explanation}\n\n"
        f"**Arquivos modificados:**\n{files_list}\n\n"
        f"---\n"
        f"> 🤖 **Modelo**: `{model_name}` • **Testes**: aprovados • "
        f"**Tokens**: `{total_tokens_in:,}` in / `{total_tokens_out:,}` out • **Tempo IA**: `{total_elapsed:.2f}s`"
    )
    reply_to_comment(repo_full_name, pull_number, thread_comment_id, resposta_pr, github_token)
    log("Fluxo concluído com sucesso.")


if __name__ == "__main__":
    main()
