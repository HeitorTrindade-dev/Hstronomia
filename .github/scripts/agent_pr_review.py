import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def log(msg: str) -> None:
    print(f"[AgentReview] {msg}")


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


def call_gemini_api(api_key: str, system_prompt: str, user_prompt: str) -> tuple[dict, dict]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "OBJECT",
                "properties": {
                    "explanation": {
                        "type": "STRING",
                        "description": "Explicação concisa e profissional em português do que foi alterado para atender o comentário do sênior."
                    },
                    "updated_file_content": {
                        "type": "STRING",
                        "description": "Conteúdo integral atualizado do arquivo modificado, sem cortes ou placeholders."
                    }
                },
                "required": ["explanation", "updated_file_content"]
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage_metadata = data.get("usageMetadata", {})
            return json.loads(candidate_text), usage_metadata
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        log(f"Erro na chamada da API Gemini ({e.code}): {err_msg}")
        raise
    except Exception as e:
        log(f"Erro inesperado ao chamar Gemini: {e}")
        raise


def run_tests() -> tuple[bool, str]:
    if Path("backend").exists():
        log("Executando testes no backend via pytest...")
        res = subprocess.run(
            ["pytest", "-v"],
            cwd="backend",
            capture_output=True,
            text=True
        )
        return (res.returncode == 0, res.stdout + "\n" + res.stderr)
    return (True, "Nenhum diretório de testes para rodar.")


def reply_to_comment(repo_full_name: str, pull_number: int, comment_id: int, message: str, github_token: str) -> None:
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pull_number}/comments/{comment_id}/replies"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "Hstronomia-Agent-Review"
    }
    payload = {"body": message}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log(f"Comentário respondido com sucesso (HTTP {resp.status}).")
    except Exception as e:
        log(f"Erro ao responder comentário de PR: {e}")


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")

    if not api_key:
        log("GEMINI_API_KEY não configurada. Abortando.")
        sys.exit(0)

    if not github_token:
        log("GITHUB_TOKEN não configurado. Abortando.")
        sys.exit(0)

    event_data = load_event_data()
    comment = event_data.get("comment", {})
    pull_request = event_data.get("pull_request", {})
    repository = event_data.get("repository", {})

    comment_author = comment.get("user", {}).get("login")
    repo_owner = repository.get("owner", {}).get("login")

    # Trava de autor: só atende se quem comentou for o dono do repositório
    if comment_author != repo_owner:
        log(f"Comentário ignorado. Autor ({comment_author}) não é o proprietário do repositório ({repo_owner}).")
        sys.exit(0)

    # Ignora respostas do próprio bot para evitar loops
    if comment.get("user", {}).get("type") == "Bot" or "github-actions" in comment_author:
        log("Comentário feito por bot. Ignorando.")
        sys.exit(0)

    comment_body = comment.get("body", "").strip()
    file_path_str = comment.get("path")
    diff_hunk = comment.get("diff_hunk", "")
    comment_id = comment.get("id")
    pull_number = pull_request.get("number")
    repo_full_name = repository.get("full_name")
    branch_name = pull_request.get("head", {}).get("ref")

    if not file_path_str or not comment_id or not pull_number:
        log("Dados insuficientes no evento do comentário. Abortando.")
        sys.exit(0)

    target_file = Path(file_path_str)
    if not target_file.exists():
        log(f"Arquivo alvo {target_file} não existe no workspace.")
        sys.exit(0)

    file_content = read_file_safely(target_file)
    agents_rules = read_file_safely(Path("AGENTS.md"))

    system_prompt = f"""Você é o Engenheiro Pleno do projeto Hstronomia, atuando sob as diretrizes do Sênior.
Suas instruções fundamentais de arquitetura e governança são extraídas diretamente do AGENTS.md:
---
{agents_rules}
---
Princípio Ponytail:
- Realize estritamente a menor alteração cirúrgica completa necessária para atender ao comentário do sênior.
- Não refatore trechos não solicitados. Não introduza dependências novas sem necessidade.
- Mantenha segurança OWASP, tipos Decimal para valores monetários e isolamento multi-tenant por restaurante_id.
- O resultado deve ser o código integral do arquivo em 'updated_file_content'.
"""

    user_prompt = f"""O Sênior deixou um comentário de revisão no arquivo '{file_path_str}'.

Comentário do Sênior:
"{comment_body}"

Contexto do Diff (Diff Hunk):
```
{diff_hunk}
```

Conteúdo atual completo do arquivo '{file_path_str}':
```
{file_content}
```

Por favor, forneça:
1. Uma explicação técnica, concisa e direta em português do que foi alterado.
2. O conteúdo integral atualizado do arquivo '{file_path_str}' com a correção aplicada.
"""

    log(f"Chamando Gemini 2.5 Flash para processar revisão no arquivo {file_path_str}...")
    ai_response, usage_metadata = call_gemini_api(api_key, system_prompt, user_prompt)

    updated_content = ai_response.get("updated_file_content")
    explanation = ai_response.get("explanation", "Alteração aplicada conforme solicitado.")

    if not updated_content or updated_content.strip() == file_content.strip():
        log("Nenhuma alteração de código necessária ou detectada.")
        reply_to_comment(
            repo_full_name, pull_number, comment_id,
            "Analisado: nenhuma alteração de código foi necessária para este comentário.",
            github_token
        )
        sys.exit(0)

    # Escreve a alteração no arquivo
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    log(f"Arquivo {target_file} atualizado com sucesso. Rodando validação de testes...")
    tests_ok, test_logs = run_tests()

    tokens_in = usage_metadata.get("promptTokenCount", 0)
    tokens_out = usage_metadata.get("candidatesTokenCount", 0)
    # Gemini 2.5 Flash: $0.075 / 1M input (~$0.000000075/token), $0.30 / 1M output (~$0.00000030/token)
    custo_usd = (tokens_in * 0.000000075) + (tokens_out * 0.00000030)

    if not tests_ok:
        log("Testes falharam após a alteração. Revertendo arquivo e avisando no PR.")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(file_content)

        erro_msg = f"""❌ **A alteração sugerida quebrou a suíte de testes (`pytest`).**

A alteração foi revertida para manter o branch estável.

**Log do erro:**
```
{test_logs[-1500:]}
```

---
> 🤖 **Métricas da Execução**:
> - **Tokens Entrada / Saída**: `{tokens_in:,}` / `{tokens_out:,}`
> - **Custo Estimado**: `${custo_usd:.6f} USD`
"""
        reply_to_comment(repo_full_name, pull_number, comment_id, erro_msg, github_token)
        sys.exit(1)

    log("Testes passaram com sucesso! Fazendo commit e push...")
    subprocess.run(["git", "add", str(target_file)], check=True)
    subprocess.run(["git", "commit", "-m", f"refactor(review): {comment_body[:50]}"], check=True)
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    resposta_pr = f"""✅ **Alteração aplicada e validada com sucesso!**

{explanation}

---
> 🤖 **Métricas da Execução**:
> - **Modelo**: `gemini-2.5-flash`
> - **Validação**: `pytest` 100% aprovado
> - **Tokens Entrada / Saída**: `{tokens_in:,}` / `{tokens_out:,}`
> - **Custo Estimado**: `${custo_usd:.6f} USD` (~R$ {custo_usd * 5.8:.4f})
"""
    reply_to_comment(repo_full_name, pull_number, comment_id, resposta_pr, github_token)
    log("Processo de revisão concluído com sucesso!")


if __name__ == "__main__":
    main()
