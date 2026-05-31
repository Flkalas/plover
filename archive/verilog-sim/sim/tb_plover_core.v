`timescale 1ns/1ps
`default_nettype none

module tb_plover_core;

    reg clk = 0;
    reg rst_n = 0;
    always #5 clk = ~clk;

    wire [15:0] pc;
    wire halted;
    wire [7:0] r0, r1;

    plover_core dut (
        .clk(clk),
        .rst_n(rst_n),
        .pc(pc),
        .flag_c(),
        .flag_z(),
        .halted(halted),
        .probe_bus(),
        .probe_alu_y(),
        .probe_cw(),
        .probe_r0(r0),
        .probe_r1(r1),
        .probe_r2(),
        .probe_r3(),
        .probe_r4(),
        .probe_r5(),
        .probe_r6()
    );

    initial begin
        if ($test$plusargs("vcd")) begin
            $dumpfile("sim/wave.vcd");
            $dumpvars(0, tb_plover_core);
        end
    end

    initial begin
        rst_n = 0;
        #20;
        rst_n = 1;
        // Icarus: avoid @(posedge clk) when large comb paths exist; use clock period delays
        #25; // cycle 0: INC R1
        #10;
        #25; // cycle 1: HALT

        if (r1 !== 8'd1) begin
            $display("FAIL: r1=%02h expected 01", r1);
            $finish(1);
        end
        if (halted !== 1'b1) begin
            $display("FAIL: not halted");
            $finish(1);
        end

        $display("PASS tb_plover_core r1=%02h pc=%04h", r1, pc);
        $finish(0);
    end

endmodule

`default_nettype wire
