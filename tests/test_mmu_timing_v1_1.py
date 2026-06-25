"""v1.1 dual-async MMU pipeline timing budget."""

from hw.logic.mmu_v1_1 import (
    T_ACC_MAIN_IS62_NS,
    T_ACC_MMU_71024_NS,
    T_FAULT_COMB_NS,
    T_MMU_PIPELINE_NS,
)

CLK_2MHZ_HALF_NS = 250
CLK_2MHZ_FULL_NS = 500


def test_pipeline_constants():
    assert T_ACC_MMU_71024_NS == 15
    assert T_ACC_MAIN_IS62_NS == 45
    assert T_FAULT_COMB_NS == 5
    assert T_MMU_PIPELINE_NS == 65


def test_fits_2mhz_execute_half_period():
    assert T_MMU_PIPELINE_NS < CLK_2MHZ_HALF_NS


def test_fits_2mhz_full_cycle_with_margin():
    assert T_MMU_PIPELINE_NS < CLK_2MHZ_FULL_NS
