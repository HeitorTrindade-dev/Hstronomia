import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


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
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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
) -> tuple[dict, dict, float]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "commit_message": {
                        "type": "STRING",
                        "description": "Mensagem de commit em uma linha no padrão Conventional Commits (ex: 'refactor(review): validar pin vazio').",
                    },
                    "explanation": {
                        "type": "STRING",
                        "description": "Explicação técnica, concisa e direta em português do que foi alterado.",
                    },
                    "updated_file_content": {
                        "type": "STRING",
                        "description": "Conteúdo integral atualizado do arquivo modificado, sem omissões ou placeholders.",
                    },
                },
                "required": ["commit_message", "explanation", "updated_file_content"],
            },
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


def run_tests(file_path_str: str) -> tuple[bool, str]:
    if file_path_str.startswith("backend/") and Path("backend").exists():
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
    return (True, "Validação de testes não aplicável ao caminho alterado.")


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
    file_path_str: str,
    status_label: str,
    tokens_in: int,
    tokens_out: int,
    elapsed: float,
) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    total = tokens_in + tokens_out
    md = (
        f"### 🤖 Agent PR Review Summary\n\n"
        f"| Campo | Valor |\n"
        f"| :--- | :--- |\n"
        f"| **Status** | {status_label} |\n"
        f"| **Modelo** | `{model_name}` |\n"
        f"| **Arquivo** | `{file_path_str}` |\n"
        f"| **Tokens (Entrada / Saída / Total)** | `{tokens_in:,}` / `{tokens_out:,}` / `{total:,}` |\n"
        f"| **Latência IA** | `{elapsed:.2f}s` |\n"
    )
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(md)


def sanitize_commit_message(raw_msg: str) -> str:
    first_line = raw_msg.strip().splitlines()[0] if raw_msg.strip() else "refactor(review): aplicar ajuste de revisao"
    return first_line[:72]


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
    # Sempre responder no comentário raiz da thread para suportar múltiplos turnos
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

    system_prompt = f"""Você é o engenheiro responsável por atender revisões de PR no repositório Hstronomia.
Siga rigorosamente as diretrizes do projeto extraídas de AGENTS.md:
---
{agents_rules}
---
Regras de execução (Modo Ponytail):
- Faça estritamente a menor alteração cirúrgica completa necessária para atender ao comentário do revisor.
- Não refatore trechos fora do escopo pedido, não adicione dependências novas e evite over-engineering.
- Preserve isolamento multi-tenant (restaurante_id), precisão Decimal em valores monetários e práticas OWASP.
- Retorne o arquivo integral atualizado em 'updated_file_content'.
"""

    user_prompt = f"""Comentário de revisão no arquivo '{file_path_str}':
"{comment_body}"

Trecho do diff (diff_hunk):
```
{diff_hunk}
```

Conteúdo atual completo de '{file_path_str}':
```
{file_content}
```
"""

    log(f"Chamando modelo '{model_name}' para '{file_path_str}'...")
    try:
        ai_response, usage_metadata, elapsed = call_gemini_api(
            api_key, model_name, system_prompt, user_prompt
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

    tokens_in = usage_metadata.get("promptTokenCount", 0)
    tokens_out = usage_metadata.get("candidatesTokenCount", 0)
    updated_content = ai_response.get("updated_file_content", "")
    explanation = ai_response.get("explanation", "Alteração aplicada conforme solicitado.")
    commit_msg = sanitize_commit_message(ai_response.get("commit_message", ""))

    if not updated_content or updated_content.strip() == file_content.strip():
        log("Nenhuma modificação necessária no arquivo.")
        write_step_summary(model_name, file_path_str, "Sem alterações", tokens_in, tokens_out, elapsed)
        reply_to_comment(
            repo_full_name,
            pull_number,
            thread_comment_id,
            f"ℹ️ **Análise concluída** (sem alterações no código):\n\n{explanation}\n\n---\n> 🤖 `{model_name}` • Tokens: `{tokens_in:,}` in / `{tokens_out:,}` out • `{elapsed:.2f}s`",
            github_token,
        )
        sys.exit(0)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    tests_ok, test_logs = run_tests(file_path_str)

    if not tests_ok:
        log("Testes falharam. Revertendo alteração.")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(file_content)

        write_step_summary(model_name, file_path_str, "❌ Testes falharam (revertido)", tokens_in, tokens_out, elapsed)
        erro_msg = (
            f"❌ **Alteração revertida: a suíte de testes (`pytest`) falhou.**\n\n"
            f"```\n{test_logs[-1500:]}\n```\n\n"
            f"---\n"
            f"> 🤖 `{model_name}` • Tokens: `{tokens_in:,}` in / `{tokens_out:,}` out • `{elapsed:.2f}s`"
        )
        reply_to_comment(repo_full_name, pull_number, thread_comment_id, erro_msg, github_token)
        sys.exit(1)

    log(f"Testes aprovados. Commitando: {commit_msg}")
    subprocess.run(["git", "add", str(target_file)], check=True)
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    write_step_summary(model_name, file_path_str, "✅ Aplicado e validado", tokens_in, tokens_out, elapsed)

    resposta_pr = (
        f"✅ **Alteração aplicada e validada!**\n\n"
        f"{explanation}\n\n"
        f"---\n"
        f"> 🤖 **Modelo**: `{model_name}` • **Testes**: aprovados • "
        f"**Tokens**: `{tokens_in:,}` in / `{tokens_out:,}` out • **Tempo IA**: `{elapsed:.2f}s`"
    )
    reply_to_comment(repo_full_name, pull_number, thread_comment_id, resposta_pr, github_token)
    log("Fluxo concluído com sucesso.")


if __name__ == "__main__":
    main()
