# PromptSentry eval

## Tensor Trust dry run (recommended)

Matches PromptSentry's threat model: **prompt hijacking / injection** + **prompt extraction**.

```bash
cd promptsentry
docker compose up -d

python3 -m venv .venv-eval
source .venv-eval/bin/activate
pip install -r eval/requirements.txt

set -a && source .env && set +a

# inspect the exact 25+25 samples first
python eval/dry_run_tensor_trust.py --limit 25 --preview-only

# then send them through the proxy (~3-6 min)
python eval/dry_run_tensor_trust.py --limit 25
```

- Attacks: filtered rows from Tensor Trust hijack + extraction JSONLs
- Safe: Tensor Trust `access_code` phrases (legitimate password attempts)
- Hit = HTTP 400 from PromptSentry
- Writes `eval/tensor_trust_samples.json` + `eval/tensor_trust_results.jsonl`

## Older JailbreakBench script

`eval/dry_run_jbb.py` remains for comparison, but JBB PAIR prompts are mostly **harmful-content** roleplay - not your primary threat model.
