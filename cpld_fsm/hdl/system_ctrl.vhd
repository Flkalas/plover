-- Plover v1.0 CPLD system controller — GPR + idx5 FSM top
library ieee;
use ieee.std_logic_1164.all;

entity system_ctrl is
  port (
    clk    : in  std_logic;
    opc    : in  std_logic_vector(4 downto 0);
    d_in   : in  std_logic_vector(7 downto 0);
    flg_z  : in  std_logic;
    flg_c  : in  std_logic;
    q_a    : out std_logic_vector(7 downto 0);
    q_b    : out std_logic_vector(7 downto 0);
    reg_we : out std_logic;
    mem_rd : out std_logic;
    mem_wr : out std_logic;
    y_oe   : out std_logic;
    cin    : out std_logic;
    bctrl  : out std_logic_vector(3 downto 0);
    lgc    : out std_logic_vector(3 downto 0);
    s0     : out std_logic;
    s1     : out std_logic;
    pc_load_en : out std_logic
  );
end system_ctrl;

architecture rtl of system_ctrl is
  signal phase          : std_logic_vector(1 downto 0);
  signal idx5           : std_logic_vector(6 downto 0);
  signal macro_end      : std_logic;
  signal w_sel          : std_logic_vector(1 downto 0);
  signal lut_reg_we     : std_logic;
  signal lut_mem_rd     : std_logic;
  signal lut_mem_wr     : std_logic;
  signal lut_y_oe       : std_logic;
  signal lut_cin        : std_logic;
  signal lut_bctrl      : std_logic_vector(3 downto 0);
  signal lut_lgc        : std_logic_vector(3 downto 0);
  signal lut_s0         : std_logic;
  signal lut_s1         : std_logic;
  signal lut_pc_load    : std_logic;
  signal lut_pc_flg_z   : std_logic;
  signal lut_flg_we     : std_logic;
  signal is_xfer        : std_logic;
  signal gpr_d          : std_logic_vector(7 downto 0);
  signal r0, r1, r2     : std_logic_vector(7 downto 0);
begin
  idx5 <= opc & phase;

  u_phase : entity work.phase_sequencer
    port map (
      clk       => clk,
      opc       => opc,
      phase     => phase,
      macro_end => macro_end
    );

  u_lut : entity work.ctrl_lut
    port map (
      idx5          => idx5,
      reg_we        => lut_reg_we,
      mem_rd        => lut_mem_rd,
      mem_wr        => lut_mem_wr,
      y_oe          => lut_y_oe,
      w_sel         => w_sel,
      cin           => lut_cin,
      bctrl         => lut_bctrl,
      lgc           => lut_lgc,
      s0            => lut_s0,
      s1            => lut_s1,
      pc_load_en    => lut_pc_load,
      pc_load_flg_z => lut_pc_flg_z,
      flg_we        => lut_flg_we,
      is_xfer       => is_xfer
    );

  u_xfer : entity work.xfer_mux
    port map (
      opc     => opc,
      is_xfer => is_xfer,
      r0      => r0,
      r1      => r1,
      r2      => r2,
      d_bus   => d_in,
      d_out   => gpr_d
    );

  u_gpr : entity work.gpr_3fixed
    port map (
      clk    => clk,
      reg_we => lut_reg_we,
      w_sel  => w_sel,
      d_in   => gpr_d,
      q_a    => q_a,
      q_b    => q_b,
      r0     => r0,
      r1     => r1,
      r2     => r2
    );

  u_branch : entity work.branch_unit
    port map (
      load_en    => lut_pc_load,
      load_flg_z => lut_pc_flg_z,
      flg_z      => flg_z,
      macro_end  => macro_end,
      pc_load_en => pc_load_en
    );

  reg_we <= lut_reg_we;
  mem_rd <= lut_mem_rd;
  mem_wr <= lut_mem_wr;
  y_oe   <= lut_y_oe;
  cin    <= lut_cin;
  bctrl  <= lut_bctrl;
  lgc    <= lut_lgc;
  s0     <= lut_s0;
  s1     <= lut_s1;
end rtl;
