from WMCore.Configuration import Configuration
config = Configuration()
config.section_('General')
config.General.workArea = 'MonoHProduction_2018_step1'
config.General.transferLogs = True
config.General.requestName = 'gg_sinp_0p35_tanb1_MXd10_MA800_ma150_step1_HZZ'
config.section_('JobType')
config.JobType.numCores = 8
config.JobType.maxMemoryMB = 16000
config.JobType.pyCfgParams = ['outputFile=step1.root']
config.JobType.pluginName = 'Analysis'
config.JobType.allowUndistributedCMSSW = True
config.JobType.psetName = 'step1_2018.py'
config.section_('Data')
config.Data.inputDataset = '/CRAB_PrivateMC/cbrainer-gg_sinp_0p35_tanb1_MXd10_MA800_ma150-175924cc93a1a4432f2f9b18f35a2c14/USER'
config.Data.outputDatasetTag = 'gg_sinp_0p35_tanb1_MXd10_MA800_ma150_step1_HZZ'
config.Data.publication = True
config.Data.unitsPerJob = 1
config.Data.splitting = 'FileBased'
config.Data.inputDBS = 'phys03'
config.section_('Site')
config.Site.storageSite = 'T3_US_FNALLPC'

