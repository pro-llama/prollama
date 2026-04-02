# Anonymization

prollama's anonymization pipeline ensures your code stays private when sent to any LLM.
It works in three layers, each catching different types of sensitive data.

## The Three Layers

### Layer 1: Regex (always active, <1ms)

Scans code with 70+ regex patterns detecting:

- **API keys**: AWS (`AKIA...`), Stripe (`sk_live_...`), GitHub (`ghp_...`), GitLab (`glpat-...`), GCP (`AIza...`)
- **Tokens**: JWT, Bearer tokens, generic API key patterns
- **Connection strings**: PostgreSQL, MySQL, MongoDB, Redis, AMQP, SMTP URLs
- **PII**: Email addresses, IPv4 addresses, international phone numbers
- **Internal URLs**: localhost, private IP ranges (10.x, 192.168.x, 172.16-31.x)

Each match is replaced with a reversible token: `[SECRET_001]`, `[EMAIL_003]`.

### Layer 2: NLP (full mode, 5-10ms)

Detects PII in natural language — comments, docstrings, string literals:

- **Person names**: `# Author: Jan Kowalski` → `# Author: [PERSON_001]`
- **Names in patterns**: `Created by`, `Fixed by`, `Reviewed by`, `@author`, `Copyright`
- **Addresses**: Street addresses, postal patterns
- **Identity numbers**: SSN, credit card numbers
- **Dates of birth**: When preceded by `DOB`, `birthday`, `date of birth`

If `presidio` is installed (`pip install prollama[nlp]`), uses Microsoft Presidio for
ML-based detection. Otherwise, uses a built-in heuristic detector.

### Layer 3: AST (full mode, 10-50ms)

Parses code into an Abstract Syntax Tree using tree-sitter and renames identifiers:

```python
# BEFORE
class StripePaymentProcessor:
    def charge_customer(self, customer_id: str, amount: Decimal):
        response = self.stripe_client.charges.create(
            customer=customer_id,
            amount=int(amount * 100),
            currency="pln"
        )
        return PaymentResult(transaction_id=response.id)

# AFTER (what the LLM sees)
class Class_001:
    def var_001(self, var_002: str, var_003: Decimal):
        response = self.var_004.var_005.create(
            var_006=var_002,
            var_003=int(var_003 * 100),
            var_007="pln"
        )
        return Class_002(var_008=response.var_009)
```

The LLM sees code structure and logic but cannot identify:
- What company this code belongs to
- What payment provider is used
- What business entities are involved

**Preserved** (not anonymized):
- Python/JS builtins: `self`, `print`, `len`, `int`, `str`, `range`, `Exception`, etc.
- Dunder methods: `__init__`, `__str__`, `__name__`
- Import paths: `import stripe`, `from payment.gateway import ...`
- Decorator names: `@property`, `@staticmethod`
- Short identifiers: single-character variables (`x`, `i`, `e`)

**Naming conventions in replacements**:
- PascalCase → `Class_NNN` (class names)
- snake_case → `var_NNN` (functions, variables)
- UPPER_CASE → `CONST_NNN` (constants)

## Rehydration

After the LLM responds, prollama reverses all mappings:

```python
from prollama.anonymizer import AnonymizationPipeline
from prollama.models import PrivacyLevel

pipeline = AnonymizationPipeline(PrivacyLevel.FULL)

# Anonymize
result = pipeline.run(source_code, language="python")
print(result.anonymized_code)  # send this to LLM
print(result.stats)            # {"SECRET": 3, "EMAIL": 1, "AST_IDENT": 15}

# After LLM responds, restore original names
original = pipeline.rehydrate(llm_response, result.mappings)
```

## Supported Languages

| Language | Regex | NLP | AST |
|----------|-------|-----|-----|
| Python | ✅ | ✅ | ✅ |
| JavaScript | ✅ | ✅ | ✅ |
| TypeScript | ✅ | ✅ | Planned |
| Java | ✅ | ✅ | Planned |
| Go | ✅ | ✅ | Planned |
| Rust | ✅ | ✅ | Planned |

Regex and NLP layers are language-agnostic. AST requires a tree-sitter grammar.

## Privacy Level Comparison

```
Level: none     →  Code sent as-is (no privacy)
Level: basic    →  [SECRET_001] replaces sk_live_xxx
                   [EMAIL_001]  replaces jan@acme.com
Level: full     →  [SECRET_001] replaces sk_live_xxx
                   [EMAIL_001]  replaces jan@acme.com
                   [PERSON_001] replaces "Jan Kowalski"
                   Class_001    replaces StripePaymentProcessor
                   var_001      replaces charge_customer
                   CONST_001    replaces STRIPE_SECRET
```
