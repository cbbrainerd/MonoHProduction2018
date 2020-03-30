from WMCore.Configuration import Configuration
import os,sys

test=False
year=2018
#Setup basic config
def get_config(dataset,inputFile):
    config = Configuration()
    
    config.section_("General")
    config.General.transferLogs = True
    config.General.requestName  = '%s_step0_HZZ' % dataset
    if test:
        config.General.requestName+='_test'
    config.General.workArea = 'crab_step0_HZZ_2'
    
    config.section_("JobType")
    config.JobType.pluginName  = 'PrivateMC'
    config.JobType.psetName    = 'step0.py'
    config.JobType.pyCfgParams = ['inputFiles=%s' % inputFile, 'year=%i' % year]
    config.JobType.allowUndistributedCMSSW = True # Complains about slc7 otherwise
    #config.JobType.numCores = 1
    
    config.section_("Data")
    config.Data.splitting       = 'EventBased'
    config.Data.unitsPerJob     = (1 if test else 200)
    config.Data.totalUnits 	    = (1 if test else 20000)
    #Leave out following for test
    config.Data.outputDatasetTag = '%s' % dataset
    config.Data.publication     = (not test)
    config.Data.outputPrimaryDataset = 'CRAB_PrivateMC'
    

    config.section_("Site")
    config.Site.storageSite = 'T2_US_Wisconsin'
    config.Site.whitelist=['T2_US_*']
    return config

with open('LHE_FILES') as f:
    dns={ x.strip().rsplit('/',1)[1].split('LHE_')[1].rsplit('.lhe',1)[0] : x.strip() for x in f.readlines()}
   
xrootd_redirector='root://xrootd.ba.infn.it/'
from CRABAPI.RawCommand import crabCommand as crab
for dn in dns:
    #Fork to avoid crab bugs with involving importing the same pset multiple times
    print 'Submitting for dataset %s' % dn
    newpid=os.fork()
    if newpid!=0:
        exit_code=os.wait()
        print "Child %s exited with status %s" % exit_code
        if(exit_code[1]!=0):
            sys.exit(exit_code)
        if test:
            sys.exit(0)
        continue
    else:
        config=get_config(dn,'%s%s' % (xrootd_redirector,dns[dn]))
        crab('submit',config=config)
        os._exit(0)
