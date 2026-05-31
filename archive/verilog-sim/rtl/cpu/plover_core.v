`default_nettype none
`include "plover_defines.vh"

module plover_core (
    input  wire        clk,
    input  wire        rst_n,
    output reg  [15:0] pc,
    output reg         flag_c,
    output reg         flag_z,
    output reg         halted,
    output wire [7:0]  probe_bus,
    output wire [7:0]  probe_alu_y,
    output wire [15:0] probe_cw,
    output wire [7:0]  probe_r0,
    output wire [7:0]  probe_r1,
    output wire [7:0]  probe_r2,
    output wire [7:0]  probe_r3,
    output wire [7:0]  probe_r4,
    output wire [7:0]  probe_r5,
    output wire [7:0]  probe_r6
);

    reg [15:0] pc_next;
    wire [15:0] cw;

    control_rom #(
        .ADDR_WIDTH(16),
        .DEPTH(2)
    ) u_rom (
        .addr(pc),
        .cw  (cw)
    );

    wire [3:0] alu_sel = cw[15:12];
    wire [3:0] reg_ctl = cw[11:8];
    wire [3:0] bus_ctl = cw[7:4];
    wire [3:0] branch  = cw[3:0];

    wire [2:0] reg_idx = reg_ctl[3:1];
    wire       reg_we  = reg_ctl[0];

    wire [7:0] reg_rd;
    wire [7:0] r0, r1, r2, r3, r4, r5, r6;

    reg [2:0] rd_idx;
    reg [2:0] wr_idx;
    reg       wr_en;
    reg [7:0] wr_data;
    reg [7:0] alu_a, alu_b;

    wire [7:0] alu_y;
    wire       alu_cout, alu_zero;

    alu8 u_alu (
        .a      (alu_a),
        .b      (alu_b),
        .alu_sel(alu_sel),
        .y      (alu_y),
        .cout   (alu_cout),
        .zero   (alu_zero)
    );

    always @(*) begin
        rd_idx  = reg_idx;
        wr_idx  = reg_idx;
        wr_en   = 1'b0;
        wr_data = 8'd0;
        alu_a   = 8'd0;
        alu_b   = 8'd0;

        if (!rst_n) begin
            alu_a = 8'd0;
            alu_b = 8'd0;
        end else begin
        // Read port always driven by reg_idx (read-modify-write same cycle)
        alu_a = reg_rd;

        if (bus_ctl == `BUS_REG_TO_ALU_B)
            alu_b = reg_rd;

        if (reg_we) begin
            wr_en = 1'b1;
            case (bus_ctl)
                `BUS_ALU_TO_REG: wr_data = alu_y;
                `BUS_MEM_READ:   wr_data = mem_dout;
                default:         wr_data = 8'd0;
            endcase
        end
        end
    end

    regfile #(.REG_COUNT(7)) u_regs (
        .clk     (clk),
        .rd_idx  (rd_idx),
        .wr_idx  (wr_idx),
        .wr_en   (wr_en),
        .wr_data (wr_data),
        .rd_data (reg_rd),
        .q0(r0), .q1(r1), .q2(r2), .q3(r3), .q4(r4), .q5(r5), .q6(r6)
    );

    wire [15:0] mem_addr = {r1, r0};
    wire        mem_we   = (bus_ctl == `BUS_MEM_WRITE);
    reg  [7:0]  mem_din;
    wire [7:0]  mem_dout;

    sram256 u_sram (
        .clk (clk),
        .we  (mem_we),
        .addr(mem_addr[14:0]),
        .din (mem_din),
        .dout(mem_dout)
    );

    wire drv_alu = (bus_ctl == `BUS_ALU_TO_REG);
    wire drv_mem = (bus_ctl == `BUS_MEM_READ);

    wire [7:0] databus;
    databus u_bus (
        .alu_out (alu_y),
        .reg_out (reg_rd),
        .mem_out (mem_dout),
        .drv_alu (drv_alu),
        .drv_reg (1'b0),
        .drv_mem (drv_mem),
        .bus     (databus)
    );

    always @(*) mem_din = databus;

    assign probe_bus   = databus;
    assign probe_alu_y = alu_y;
    assign probe_cw    = cw;
    assign probe_r0 = r0;
    assign probe_r1 = r1;
    assign probe_r2 = r2;
    assign probe_r3 = r3;
    assign probe_r4 = r4;
    assign probe_r5 = r5;
    assign probe_r6 = r6;

    wire [15:0] jump_addr = {r1, r0};

    always @(*) begin
        pc_next = pc + 16'd1;
        case (branch)
            `BR_HOLD: pc_next = pc;
            `BR_JMP:  pc_next = jump_addr;
            `BR_BEQ:  pc_next = flag_z ? jump_addr : (pc + 16'd1);
            `BR_BNE:  pc_next = !flag_z ? jump_addr : (pc + 16'd1);
            `BR_HALT: pc_next = pc;
            `BR_INC2: pc_next = pc + 16'd2;
            default:  pc_next = pc + 16'd1;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc     <= 16'd0;
            flag_c <= 1'b0;
            flag_z <= 1'b0;
            halted <= 1'b0;
        end else if (!halted) begin
            pc <= pc_next;
            if (alu_sel != `ALU_NOP) begin
                flag_c <= alu_cout;
                flag_z <= alu_zero;
            end
            if (branch == `BR_HALT)
                halted <= 1'b1;
        end
    end

endmodule

`default_nettype wire
