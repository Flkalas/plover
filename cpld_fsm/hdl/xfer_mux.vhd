-- TFR internal read mux — opcode 0x10..0x15 (microcode-spec.md §5)
library ieee;
use ieee.std_logic_1164.all;

entity xfer_mux is
  port (
    opc    : in  std_logic_vector(4 downto 0);
    is_xfer: in  std_logic;
    r0     : in  std_logic_vector(7 downto 0);
    r1     : in  std_logic_vector(7 downto 0);
    r2     : in  std_logic_vector(7 downto 0);
    d_bus  : in  std_logic_vector(7 downto 0);
    d_out  : out std_logic_vector(7 downto 0)
  );
end xfer_mux;

architecture rtl of xfer_mux is
  signal src : std_logic_vector(7 downto 0);
begin
  process (opc, r0, r1, r2)
  begin
    case opc is
      when "10000" => src <= r1; -- 0x10 R1->R0
      when "10001" => src <= r2; -- 0x11 R2->R0
      when "10010" => src <= r0; -- 0x12 R0->R1
      when "10011" => src <= r2; -- 0x13 R2->R1
      when "10100" => src <= r0; -- 0x14 R0->R2
      when "10101" => src <= r1; -- 0x15 R1->R2
      when others  => src <= (others => '0');
    end case;
  end process;

  d_out <= src when is_xfer = '1' else d_bus;
end rtl;
