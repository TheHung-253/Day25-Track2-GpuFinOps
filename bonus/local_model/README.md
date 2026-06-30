# Bonus — real local model ($/token from real tok/s)

Run a tiny model on CPU, measure **real tokens/sec**, and compare the resulting
`$/1M-token` to the simulation. Optional — needs `torch` + `transformers`.

```bash
pip install torch transformers
cd bonus/local_model
python run_local.py                 # uses a tiny CPU model
LAB_MODEL=Qwen/Qwen2.5-0.5B python run_local.py   # try a bigger one
```

If deps or the model download are unavailable, the script prints instructions and
exits cleanly (it never breaks the lab).
