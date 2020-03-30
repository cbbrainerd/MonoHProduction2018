from Configuration.StandardSequences.Eras import eras

def customize_year(year):
    try:
        #Get the correct era. Using lambdas in case there are side effects to importing an era: only the correct era is imported
        era= { 
            2016 : lambda: eras.Run2_2016, 
            2017 : lambda: eras.Run2_2017, 
            2018 : lambda: eras.Run2_2018 
        }[year]()
        global_tag= { 
            2016 : '102X_mcRun2_asymptotic_v7',
            2017 : '102X_mc2017_realistic_v7', 
            2018 : '102X_upgrade2018_realistic_v20'
        }[year]
    except KeyError:
        print 'Unsupported year "%s"' % options.year
        raise
    return type('obj',(object,), {'year' : year, 'era' : era, 'global_tag' : global_tag})()
