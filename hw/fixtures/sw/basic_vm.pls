; BASIC token interpreter entry (reserved $1800–$1FFF).
; v0.1: host `plover_basic::BasicVm` executes `.tok` at $2800; CPU stub HALTs.

        .ORG $1800
basic_vm_entry:
        HALT
