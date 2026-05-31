`timescale 1ns/1ps
`default_nettype none

module tb_alu8;

    reg  [7:0] a, b;
    reg  [3:0] alu_sel;
    wire [7:0] y;
    wire       cout, zero;

    alu8 dut (
        .a      (a),
        .b      (b),
        .alu_sel(alu_sel),
        .y      (y),
        .cout   (cout),
        .zero   (zero)
    );

    integer errors;

    task check;
        input [8*32:1] name;
        input [7:0]    exp_y;
        input          exp_c;
        input          exp_z;
        begin
            if (y !== exp_y || cout !== exp_c || zero !== exp_z) begin
                $display("FAIL %s: sel=%0d a=%02h b=%02h got y=%02h c=%b z=%b",
                         name, alu_sel, a, b, y, cout, zero);
                $display("     expected y=%02h c=%b z=%b", exp_y, exp_c, exp_z);
                errors = errors + 1;
            end else
                $display("PASS %s", name);
        end
    endtask

    initial begin
        errors = 0;
        a = 8'h12;
        b = 8'h34;

        alu_sel = 4'd1; // ADD
        #1;
        check("ADD", 8'h46, 1'b0, 1'b0);

        alu_sel = 4'd2; // SUB
        #1;
        check("SUB", 8'hDE, 1'b1, 1'b0);

        alu_sel = 4'd3; // AND
        #1;
        check("AND", 8'h10, 1'b0, 1'b0);

        alu_sel = 4'd4; // OR
        #1;
        check("OR", 8'h36, 1'b0, 1'b0);

        alu_sel = 4'd5; // XOR
        #1;
        check("XOR", 8'h26, 1'b0, 1'b0);

        a = 8'hFF;
        b = 8'h01;
        alu_sel = 4'd1;
        #1;
        check("ADD_CARRY", 8'h00, 1'b1, 1'b1);

        if (errors == 0) begin
            $display("tb_alu8: all tests passed");
            $finish(0);
        end else begin
            $display("tb_alu8: %0d errors", errors);
            $finish(1);
        end
    end

endmodule

`default_nettype wire
