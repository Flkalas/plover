# P12 IPC model

## Run

```text
python p12_ipc_model.py
python mailbox_copy_bps.py
python -m pytest test_p12_ipc_model.py test_mailbox_copy_bps.py -q
```

Modes: `gi1`, `fe2`, `pe1`, `p12`, `p12_stretch`, `fallback_fe2`.

Imports PE1 / FE2 helpers from sibling `research/pe1/model` and `research/primitive-one-clock/model` when present.
