# add_imm smoke program @ `$0800`

Frozen ROM/SRAM image for breadboard burn. One byte per line (Intel HEX style without record headers).

**Gi1 semantics:** `ADD #imm` writes result to **R0** (not R2). Sequence loads via LDA, adds immediate, stores.

```hex
01
05
0C
02
01
03
0C
02
0A
```

Interpretation (desk): exercise ADD→R0 writeback path; verify against [M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md) mini-program.
