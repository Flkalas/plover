# hwsim

Electrical timing simulator for Plover **74HC comb** blocks. **Stdlib only.**

- **CPLD / clock / microcode** → [`plover_vm`](../plover_vm/) (ideal decode in hwsim is `t_pd=0`)
- **No OSC / 2 MHz recurring** hwsim tests

```bash
python -m hwsim run --all
```

See [docs/hw-sim.md](../docs/hw-sim.md).
