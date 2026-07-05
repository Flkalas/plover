-- BEQ: PC_LOAD_EN gated by FLG_Z at macro_end phase
library ieee;
use ieee.std_logic_1164.all;

entity branch_unit is
  port (
    load_en    : in  std_logic;
    load_flg_z : in  std_logic;
    flg_z      : in  std_logic;
    macro_end  : in  std_logic;
    pc_load_en : out std_logic
  );
end branch_unit;

architecture rtl of branch_unit is
begin
  pc_load_en <= '1'
    when macro_end = '1' and load_en = '1' and (load_flg_z = '0' or flg_z = '1')
    else '0';
end rtl;
