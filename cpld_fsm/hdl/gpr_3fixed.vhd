-- 3×8 GPR — async R0->q_a, R1->q_b (cpld-system-controller.md §8)
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity gpr_3fixed is
  port (
    clk    : in  std_logic;
    reg_we : in  std_logic;
    w_sel  : in  std_logic_vector(1 downto 0);
    d_in   : in  std_logic_vector(7 downto 0);
    q_a    : out std_logic_vector(7 downto 0);
    q_b    : out std_logic_vector(7 downto 0);
    r0     : out std_logic_vector(7 downto 0);
    r1     : out std_logic_vector(7 downto 0);
    r2     : out std_logic_vector(7 downto 0)
  );
end gpr_3fixed;

architecture rtl of gpr_3fixed is
  type reg_array_t is array (0 to 2) of std_logic_vector(7 downto 0);
  signal regs : reg_array_t := (others => (others => '0'));
begin
  q_a <= regs(0);
  q_b <= regs(1);
  r0  <= regs(0);
  r1  <= regs(1);
  r2  <= regs(2);

  process (clk)
    variable sel : integer range 0 to 3;
  begin
    if rising_edge(clk) then
      if reg_we = '1' then
        sel := to_integer(unsigned(w_sel));
        if sel <= 2 then
          regs(sel) <= d_in;
        end if;
      end if;
    end if;
  end process;
end rtl;
