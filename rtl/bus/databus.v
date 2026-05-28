`default_nettype none

// Tri-state databus arbiter with drive conflict detection
module databus #(
    parameter [7:0] IDLE_VALUE = 8'h00
) (
    input  wire [7:0] alu_out,
    input  wire [7:0] reg_out,
    input  wire [7:0] mem_out,
    input  wire       drv_alu,
    input  wire       drv_reg,
    input  wire       drv_mem,
    output wire [7:0] bus
);

    wire [2:0] drivers = {drv_mem, drv_reg, drv_alu};
    reg  [7:0] bus_r;

    always @(*) begin
        bus_r = IDLE_VALUE;
        if (drv_alu)
            bus_r = alu_out;
        else if (drv_reg)
            bus_r = reg_out;
        else if (drv_mem)
            bus_r = mem_out;
    end

    assign bus = bus_r;

endmodule

`default_nettype wire
