#!/bin/sh -f

MYROOT=/gpfs/wolf2/cades/cli185/
MYMACH=cades-baseline

python ./site_fullrun.py \
      --site US-GC3 --sitegroup Wetland --caseidprefix C2 \
      --nyears_ad_spinup 200 --nyears_final_spinup 600 --tstep 1 \
      --cpl_bypass --machine $MYMACH --compiler gnu --mpilib openmpi --gswp3 \
      --model_root /ccsopen/home/ji8/E3SM_baseline \
      --caseroot /ccsopen/home/ji8/cases \
      --ccsm_input $MYROOT/world-shared/e3sm/inputdata \
      --runroot $MYROOT/scratch/$USER \
      --spinup_vars \
      --np 1 \
      --nopointdata \
      --domainfile $MYROOT/proj-shared/pt-e3sm-inputdata/share/domains/domain.clm/domain.lnd.2x1pt_US-GC3_navy_vji.nc \
      --surffile $MYROOT/proj-shared/pt-e3sm-inputdata/lnd/clm2/surfdata_map/surfdata_2x1pt_US-GC3_simyr1850.nc \
      --landusefile $MYROOT/proj-shared/pt-e3sm-inputdata/lnd/clm2/surfdata_map/surfdata.pftdyn_2x1pt_US-GC3_simyr1850-2015.nc

