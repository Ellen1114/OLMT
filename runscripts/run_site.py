from model_ELM import ELMcase
import os
import numpy as np

#Define directories
caseroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_cases'
runroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run'
inputdata='/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata'
modelroot=os.environ['HOME']+'/models/E3SM'
#Use an existing executable, or set exeroot='' to do build 
exeroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240611_US-UMB_ICB1850CNRDCTCBC_ad_spinup/bld/'
#exeroot=''
#exeroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240614_US-MOz_I1850CNRDCTCBC_ad_spinup/bld' #DATM

site     = 'US-MOz'          #site name
mettype  = 'site'            #met data type
machine  = 'cades-baseline'  #machine name

runtype = 'BGC'          #BGC or SP
if (runtype == 'BGC'):
  #BGC simulation in 3 phases: ad_spinup, final spinup and transient.
  compsets = ['ICB1850CNRDCTCBC','ICB1850CNPRDCTCBC','ICB20TRCNPRDCTCBC']
  suffix   = ['_ad_spinup','','']      #Identifer suffix
  nyears   = [50,50,170]               #number of years to run each case
  depends  = [-1,0,1]                  #Case dependency (-1 = no dependency)
elif (runtype == 'SP'):
  #Satellite phenology simulation
  compsets = ['ICBELMBC']
  suffix = ['']
  nyears = [30]
  depends = [-1]
  startyear = 1985

#User namelist options (leave as blank list if none)
namelist_options = []
namelist_options.append("startdate_add_co2 = '00100101'")
namelist_options.append("add_co2 = 150")

#------------------------------------------------------------------------------------------------
cases = {}
ncases = len(compsets)  #how many cases we are running
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

if (ncases > 1):
    startyear=-1  #Ignore start year if doing full spinup+transient
for c in range(0,ncases):
  cases[c] = ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine=machine,exeroot=exeroot, suffix=suffix[c], nyears=nyears[c], np=1, \
        res='hcru_hcru', startyear=startyear, namelist_options=namelist_options)

  #Create the case
  cases[c].create_case()
  #Get forcing information
  cases[c].get_forcing(mettype=mettype)
  #Set the initial data file (if depends on previous case)
  if (depends[c] >= 0):
      #Set the initial data file from the last year of the prev case
      finidat_year = cases[depends[c]].run_n+1
      if ('20TR' in cases[depends[c]].compset or 'trans' in cases[depends[c]].compset):
          finidat_year = 1850+cases[depends[c]].run_n
      cases[c].set_finidat_file(finidat_case=cases[depends[c]].casename, \
              finidat_year=finidat_year)
  #Set up the case
  cases[c].setup_case()
  #If first case, extract the surface and domain files for the region of interest
  if (c == 0):
    cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
  #If transient case, make the pftdyn file
  if (c == 2):
    cases[c].setup_domain_surfdata(makepftdyn=True)
  #Build the case
  cases[c].build_case()
  #Submit the case
  if (depends[c] < 0):  #no dependency
    jobnum[c] = cases[c].submit_case()
    #Set exeroot for subsequent cases so we don't have to rebuild
    exeroot = cases[c].exeroot
  else:
    jobnum[c] = cases[c].submit_case(depend=jobnum[depends[c]])