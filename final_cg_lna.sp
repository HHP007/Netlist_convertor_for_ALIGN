.subckt final_cg_lna 0 Vin Vout vbias1 vbias2 vdd
r0 Vin net7 1K
r1 vdd Vout 1K
m1 net9 vbias1 net7 0 nmos_rvt l=60n w=2u nf=16 m=1
m0 Vout vbias2 net9 0 nmos_rvt l=60n w=2u nf=16 m=1
.ends final_cg_lna
