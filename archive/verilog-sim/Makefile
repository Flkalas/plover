# Plover Verilog simulator
IVL ?= iverilog
VVP ?= vvp
PYTHON ?= python3

RTL_ALU = rtl/alu/hc283_cascade.v rtl/alu/hc153_mux4.v rtl/alu/alu8.v
RTL_CORE = $(RTL_ALU) rtl/reg/hc574.v rtl/reg/regfile.v rtl/bus/databus.v \
	rtl/mem/control_rom.v rtl/mem/sram256.v rtl/cpu/plover_core.v
IVL_INC = -I rtl/cpu

.PHONY: all test sim-alu sim-core rom web-dev sim-server clean

all: test

test: sim-alu sim-core

build/alu8.out: $(RTL_ALU) sim/tb_alu8.v
	@mkdir -p build
	$(IVL) -o $@ $(RTL_ALU) sim/tb_alu8.v

sim-alu: build/alu8.out
	$(VVP) $<

build/core.out: $(RTL_CORE) sim/tb_plover_core.v
	@mkdir -p build
	$(IVL) $(IVL_INC) -o $@ $(RTL_CORE) sim/tb_plover_core.v

sim-core: rom
	$(MAKE) build/core.out
	$(VVP) build/core.out

rom:
	$(PYTHON) tools/microasm.py lib/inc_r1.micro -o sim

clean:
	rm -rf build sim/wave.vcd

web-dev:
	cd web && npm install && npm run dev

sim-server:
	cd sim-runner && pip install -r requirements.txt && uvicorn main:app --reload --host 127.0.0.1 --port 8000
