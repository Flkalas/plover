`default_nettype none

module control_rom #(
    parameter ADDR_WIDTH = 16,
    parameter DEPTH      = 2,
    parameter ROM_LO_FILE = "sim/rom_low.hex",
    parameter ROM_HI_FILE = "sim/rom_high.hex"
) (
    input  wire [ADDR_WIDTH-1:0] addr,
    output wire [15:0]           cw
);

    reg [7:0] rom_lo [0:DEPTH-1];
    reg [7:0] rom_hi [0:DEPTH-1];

    initial begin
        $readmemh(ROM_LO_FILE, rom_lo);
        $readmemh(ROM_HI_FILE, rom_hi);
    end

    assign cw = {rom_hi[addr], rom_lo[addr]};

endmodule

`default_nettype wire
