#!/bin/sh -f

python ./site_fullrun.py \
      --site US-Atq --site3rd US-Ha1 --sitegroup AmeriFlux --caseidprefix STP32 \
      --nyears_ad_spinup 200 --nyears_final_spinup 600 --nyears_transient 169 --tstep 1 \
      --cpl_bypass --machine cades-baseline --compiler gnu --mpilib openmpi \
      --hist_nhtfrq_trans -1 \
      --hist_mfilt_trans 8760 \
      --gswp3 --daymet \
      --model_root /ccsopen/home/ji8/E3SM_japg/ \
      --caseroot /ccsopen/home/ji8/cases \
      --ccsm_input /gpfs/wolf2/cades/cli185/world-shared/e3sm/inputdata \
      --metdir /gpfs/wolf2/cades/cli185/world-shared/e3sm/inputdata \
      --spinup_vars \
      --nopftdyn \
      --col3rd \
      --np 1 \
      --tide_forcing_file /ccsopen/home/ji8/OLMT_japg/Annapolis_elev_sal_35yrs_tides.nc \
      --parm_file /ccsopen/home/ji8/OLMT_japg/parm_GC4_9 \
      --parm_file_2nd /ccsopen/home/ji8/OLMT_japg/parm_short_GC3_12 \
