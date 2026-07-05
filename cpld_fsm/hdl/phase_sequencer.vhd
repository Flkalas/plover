-- 2-bit phase counter + per-opcode phase_count (isa.py PHASE_COUNT)
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity phase_sequencer is
  port (
    clk       : in  std_logic;
    opc       : in  std_logic_vector(4 downto 0);
    phase     : out std_logic_vector(1 downto 0);
    macro_end : out std_logic
  );
end phase_sequencer;

architecture rtl of phase_sequencer is
  signal ph       : unsigned(1 downto 0) := (others => '0');
  signal ph_limit : unsigned(1 downto 0);

  function phase_count(op : std_logic_vector(4 downto 0)) return unsigned is
    variable o : integer;
  begin
    o := to_integer(unsigned(op));
    case o is
      when 1 | 13       => return to_unsigned(2, 2); -- ADD, CMP: phases 0..2
      when 2 | 3 | 8 | 9 | 15 => return to_unsigned(1, 2); -- 2-phase macros
      when 4            => return to_unsigned(1, 2); -- BEQ
      when 5 | 10       => return to_unsigned(0, 2); -- JMP, HALT: 1 phase
      when 16#10# to 16#15# => return to_unsigned(0, 2); -- TFR
      when others       => return to_unsigned(0, 2);
    end case;
  end function;
begin
  ph_limit <= phase_count(opc);
  phase     <= std_logic_vector(ph);
  macro_end <= '1' when ph = ph_limit else '0';

  process (clk)
  begin
    if rising_edge(clk) then
      if ph = ph_limit then
        ph <= (others => '0');
      else
        ph <= ph + 1;
      end if;
    end if;
  end process;
end rtl;
