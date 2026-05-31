`ifndef PLOVER_DEFINES_VH
`define PLOVER_DEFINES_VH

`define ALU_NOP    4'd0
`define ALU_ADD    4'd1
`define ALU_SUB    4'd2
`define ALU_AND    4'd3
`define ALU_OR     4'd4
`define ALU_XOR    4'd5
`define ALU_NOT    4'd6
`define ALU_PASS_A 4'd7
`define ALU_PASS_B 4'd8
`define ALU_INC    4'd9
`define ALU_DEC    4'd10
`define ALU_CMP    4'd11

`define BUS_IDLE         4'd0
`define BUS_ALU_TO_REG   4'd1
`define BUS_REG_TO_ALU_B 4'd2
`define BUS_MEM_READ     4'd3
`define BUS_MEM_WRITE    4'd4
`define BUS_IMM8_LO      4'd5

`define BR_INC  4'd0
`define BR_HOLD 4'd1
`define BR_JMP  4'd2
`define BR_BEQ  4'd3
`define BR_BNE  4'd4
`define BR_HALT 4'd5
`define BR_INC2 4'd6

`endif
