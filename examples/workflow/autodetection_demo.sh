#!/bin/bash
# Prollama Autodetekcja - Krok po kroku
# User: Tom Softreck (tom@sapletta.dev)
# Repo: pro-llama/prollama

set -e

echo "======================================"
echo "PROLLAMA AUTODETEKCJA - KROK PO KROKU"
echo "======================================"
echo ""
echo "Użytkownik: Tom Sapletta (tom@sapletta.dev)"
echo "Data: $(date)"
echo ""

echo "[KROK 1] Sprawdzenie danych z .git"
echo "--------------------------------------"
git config user.name
git config user.email
git remote get-url origin
echo ""

echo "[KROK 2] Sprawdzenie aktualnego branchu"
echo "--------------------------------------"
git branch --show-current
echo ""

echo "[KROK 3] Autodetekcja repo przez prollama"
echo "--------------------------------------"
python -c "
from prollama.pr import get_current_repo, get_current_branch
owner, repo = get_current_repo()
branch = get_current_branch()
print(f'Wykryte: {owner}/{repo}')
print(f'Branch: {branch}')
"
echo ""

echo "[KROK 4] Symulacja prollama login"
echo "--------------------------------------"
python -c "
from prollama.auth import save_github_token, load_github_token, get_credentials_path
save_github_token('ghp_demo_token_xxx', '')
token = load_github_token()
path = get_credentials_path()
print(f'Token zapisany: {path}')
print(f'Username: ')
print(f'Logged in: True')
"
echo ""

echo "[KROK 5] Sprawdzenie uprawnień pliku"
echo "--------------------------------------"
ls -la ~/.prollama/credentials.json
echo ""

echo "[KROK 6] Wylogowanie"
echo "--------------------------------------"
python -m prollama.cli logout
echo ""

echo "[KROK 7] Weryfikacja usunięcia"
echo "--------------------------------------"
python -c "
from prollama.auth import load_github_token
print(f'Token usunięty: {load_github_token() is None}')
"
echo ""

echo "======================================"
echo "AUTODETEKCJA DZIAŁA!"
echo "======================================"
