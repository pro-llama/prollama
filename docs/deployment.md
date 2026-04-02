# Deployment

## Local Development

```bash
pip install prollama[ast]
prollama init
prollama start
```

## Docker

### Single Container

```bash
docker build -t prollama:latest .
docker run -p 8741:8741 prollama:latest
```

### Docker Compose (prollama + Ollama)

```bash
docker compose up -d
```

This starts:
- **prollama** on port 8741 (proxy with anonymization)
- **Ollama** on port 11434 (local LLM server)

Pull a coding model into Ollama:

```bash
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

### GPU Support

Uncomment the GPU section in `docker-compose.yml` for NVIDIA GPU acceleration:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## Self-Hosted (Team/Enterprise)

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Developer   │────▶│   prollama   │────▶│   Ollama    │
│  Workstation │     │   (proxy)    │     │   (GPU)     │
└─────────────┘     │   port 8741  │     │  port 11434 │
                    └──────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL  │  (Team plan: audit logs)
                    └─────────────┘
```

### Systemd Service

```ini
# /etc/systemd/system/prollama.service
[Unit]
Description=prollama LLM Proxy
After=network.target

[Service]
Type=simple
User=prollama
ExecStart=/usr/local/bin/prollama start --host 0.0.0.0
Restart=on-failure
RestartSec=5
Environment=PROLLAMA_CONFIG=/etc/prollama/config.yaml

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable prollama
sudo systemctl start prollama
```

### Reverse Proxy (nginx)

```nginx
upstream prollama {
    server 127.0.0.1:8741;
}

server {
    listen 443 ssl;
    server_name prollama.internal.company.com;

    ssl_certificate     /etc/ssl/prollama.crt;
    ssl_certificate_key /etc/ssl/prollama.key;

    location / {
        proxy_pass http://prollama;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

## Air-Gapped Deployment

For environments with no internet access:

1. Install prollama and Ollama on a machine with GPU
2. Pre-download models: `ollama pull qwen2.5-coder:32b`
3. Configure `routing.strategy: local-only`
4. Set `privacy.level: basic` (AST not required for local models)

```yaml
# config.yaml — air-gapped
providers:
  - name: ollama
    base_url: http://localhost:11434/v1
    models: [qwen2.5-coder:32b]

routing:
  strategy: local-only
  fallback: false

privacy:
  level: basic   # or full if tree-sitter is installed
```

Zero data leaves the network. No cloud API keys required.

## CI/CD Integration

### GitHub Actions

```yaml
- name: prollama auto-fix
  uses: pyqual/prollama-action@v1
  with:
    issue_number: ${{ github.event.issue.number }}
    mode: cloud
    budget: $5.00
    create_pr: true
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    PROLLAMA_API_KEY: ${{ secrets.PROLLAMA_API_KEY }}
```

### GitLab CI

```yaml
prollama-fix:
  stage: fix
  script:
    - pip install prollama
    - prollama solve --ticket gitlab:$CI_PROJECT_PATH#$ISSUE_ID
    - prollama pr --target main
```
