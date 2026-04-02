# Examples

## Sample Code

Source files designed to demonstrate prollama's anonymization capabilities:

- **fintech_app.py** — Payment processing with Stripe keys, database URLs, person names, business logic
- **healthcare_app.py** — HIPAA-sensitive EHR system with patient data handling

## Scripts

### anonymize_code.py

Anonymize a source file and display a full comparison:

```bash
python examples/anonymize_code.py examples/sample_code/fintech_app.py --level full
```

### routing_demo.py

Demonstrate model routing, escalation chains, and cost estimation:

```bash
python examples/routing_demo.py
```

### batch_scan.py

Scan an entire project directory for sensitive data:

```bash
python examples/batch_scan.py ./my-project --level basic
python examples/batch_scan.py . --level full
```

## Quick Demo

```bash
# Install with AST support
pip install prollama[ast]

# Compare basic vs full anonymization
prollama anonymize examples/sample_code/fintech_app.py --level basic
prollama anonymize examples/sample_code/fintech_app.py --level full

# Or use the Makefile
make demo
```
