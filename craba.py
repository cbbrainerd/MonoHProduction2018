#!/bin/bash

#Bootstrap CMSSW/crab environments
''':'
set -e
if [ -z "$CMSSW_BASE" ]; then
    . /cvmfs/cms.cern.ch/cmsset_default.sh
    eval `scramv1 runtime -sh 2> /dev/null || { echo exit 1; echo "Must be run with CMSSW environment setup, or from a valid CMSSW release." >&2; }`
    . /cvmfs/cms.cern.ch/crab3/crab.sh
    which crab
#elif ! /usr/bin/which crab &> /dev/null; then 
elif [ -z "$CRAB3_BIN_ROOT" ]; then
    . /cvmfs/cms.cern.ch/crab3/crab.sh
fi
export CRAB_BOOTSTRAPPED=1
export CRAB3_BIN_ROOT
export CRABCLIENT_ROOT
exec python "$0" "$@"
exit 1
'''

import os, sys

try:
    try:
        bin_dir=os.environ['CRAB3_BIN_ROOT']
    except KeyError:
        bin_dir=os.path.join(os.environ['CRABCLIENT_ROOT'],'bin')
except KeyError:
    try:
        os.environ['CRAB_BOOTSTRAPPED']
        print "Failed to bootstrap crab."
        raise SystemExit
    except KeyError:
        os.execl('/bin/bash','bash',*sys.argv)

import imp

#Setup loggers just once. 
import CRABClient.ClientUtilities
class initLoggers():
    def __init__(self,initLoggers):
        self.tblogger,self.logger,self.memhandler=initLoggers()
    def __call__(self):
        return self.tblogger,self.logger,self.memhandler

initLoggers=initLoggers(CRABClient.ClientUtilities.initLoggers)
CRABClient.ClientUtilities.initLoggers=initLoggers

crab=imp.load_source('crab',os.path.join(bin_dir,'crab'))

try:
    dashdash=next(n for n,d in enumerate(sys.argv) if d=='--')
    arguments=sys.argv[1:dashdash]
    directories=[x.rstrip('/') for x in sys.argv[dashdash+1:]]
except StopIteration:
    print "Warning: treating all arguments as flags (not directories) and running over directories crab_*/"
    import glob
    arguments=sys.argv[1:]
    directories=glob.glob('crab_*/')

#Remove trailing slashes to make sure key is the same every time
directories=[d.rstrip('/') for d in directories]
#Dummy subcommand so that CRABClient.__call__() does not actually execute the command. This allows us to capture the output
class SubCommandWrapper(object):
    def __init__(self,cmd):
        self.subcommand=cmd
    def __getattr__(self,attr):
        return getattr(self.subcommand,attr)
    def __call__(self,*args,**kwargs):
        if len(args) > 0: #Initializing command
            self.initialized_command=self.subcommand(*args,**kwargs)
        return self

class MultiClient(crab.CRABClient):
    class status(object):
        def __init__(self,cmd):
            self.cmd=cmd
        def __call__(self,*args,**kwargs):
            val=self.cmd(*args,**kwargs)
            jobList=val.pop('jobList')
            jobs=val.pop('jobs')
            return val
    def __init__(self,arguments,directories):
        super(MultiClient,self).__init__()
        self.arguments=arguments
        self.directories=directories
        self.subCommands=dict((k,SubCommandWrapper(v)) for (k,v) in self.subCommands.items())
        self.retvals={}
    def handle(self,name):
        if name=='status': #debug
            failed=[]
            pubfailed=[]
            done=[]
            running=[]
            for k,v in self.retvals.items():
                jps=v['jobsPerStatus']
                pubEnabled=v['publicationEnabled']
                if pubEnabled:
                    pubSuccess=(
                        (v['publicationFailures']=={}) and
                        ('finished' in jps and v['publication']=={'done':jps['finished']})
                    )
                else:
                    pubSuccess=True
                if 'failed' in jps:
                    failed.append(k)
                elif 'failed' in v['publication']:
                    pubfailed.append(k)
                elif jps.keys()==['finished'] and v['status']=='COMPLETED' and pubSuccess:
                    done.append(k)
                else:
                    running.append(k)
            if done:
                print '%i jobs done:' % len(done)
                print '\n'.join(done)
            if running:
                print '%i jobs still running:' % len(running)
                print '\n'.join(running)
            if failed or pubfailed:
                print '%i jobs failed:' % (len(failed)+len(pubfailed))
                print '\n'.join(failed)
                if pubfailed:
                    print ' (Publication)\n'.join(pubfailed+[''])
                with open('resubmit_crab.sh','w') as f:
                    if failed:
                        f.write('~/bin/craba.py resubmit "$@" -- "%s"' % '" "'.join(failed))
                    if pubfailed:
                        f.write('%s~/bin/craba.py resubmit "$@" --publication -- "%s"' % (('\n' if failed else ''),'" "'.join(pubfailed)))
            if failed or pubfailed or running:
                with open('status_crab.sh','w') as f:
                    f.write('~/bin/craba.py status "$@" -- "%s"' % '" "'.join(running+failed+pubfailed))
    def __call__(self):
        for directory in self.directories:
            sys.argv=[sys.argv[0]]
            sys.argv.extend(self.arguments)
            sys.argv.extend(['-d',directory])
            super(MultiClient,self).__call__()
            name=self.cmd.initialized_command.name
            cmd=self.get_command(self.cmd.initialized_command)
            self.retvals[directory]=cmd()
        self.handle(name)
        return self.retvals
    def get_command(self,cmd): #Specialize commands
        name=cmd.name
        if hasattr(self,name):  
            return getattr(self,name)(cmd)
        else:
            return cmd
        
client=MultiClient(arguments,directories)
retval=client()

import json
#Don't overwrite old statuses
if os.path.exists('crab_log.json'):
    with open('crab_log.json') as f:
        js=json.load(f)
    #Fix for old bug, remove trailing slashes from dict keys
    for key in js.keys():
        if '/' in key:
            js[key.rstrip('/')]=js.pop(key)
    for key,value in retval.items():
        js[key]=value
else:
    js=retval
with open('crab_log.json','w') as f:
    json.dump(js,f)
