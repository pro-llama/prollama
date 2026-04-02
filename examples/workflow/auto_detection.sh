#!/bin/bash
# Prollama Autodetekca - Automatyczne rozpoznawanie użytkownika
# User: Tom Softreck (tom@sapletta.dev)
# Repo: pro-llama/prollama

set -e

echo "======================================"
echo "AUTODETEKCJA - BEZ RĘCZNEGO WPISYWANIA"
echo "======================================"
echo ""

echo "[AUTO] Wykrywanie użytkownika z .git"
echo "--------------------------------------"
.venv/bin/python -c "
from prollama.auth import get_git_user_info, get_local_username
from prollama.pr import get_current_repo, get_current_branch

# Automatyczna detekcja - żadnych ręcznych inputów!
name, email = get_git_user_info()
username = get_local_username()
owner, repo = get_current_repo()
branch = get_current_branch()

print(f'git user.name: {name}')
print(f'git user.email: {email}')
print(f'Wykryty username: {username}')
print(f'Repo: {owner}/{repo}')
print(f'Branch: {branch}')
"
echo ""

echo "[AUTO] Symulacja: prollama solve --pr"
echo "--------------------------------------"
echo "Branch name: prollama/fix-typo-in-readme"
echo "Commit author: tom.softreck (auto-detected)"
echo "PR author: tom.softreck (auto-detected)"
echo ""

echo "======================================"
echo "AUTODETEKCJA DZIAŁA BEZ RĘCZNEGO INPUTU!"
echo "======================================"
echo ""
echo "Użycie:"
echo "  prollama solve 'Fix typo' --file README.md --pr"
echo ""
echo "Efekt:"
echo "  - Branch: prollama/fix-typo-in-readmemd"
echo "  - Commit author: tom.softreck (z .git)"
echo "  - PR body zawiera: Author: tom.softreck"
echo ""
