
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/LICENSE.md

import requests, argparse, sys, os
# from ptftplib import pxeserver
from collections import Counter, OrderedDict
from time import sleep

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])) + '/..')

from usecase.results import Results

powerstates = ['On','Off','PoweringOn','PoweringOff']
modesenable = ['Disabled','Once','Continuous']
l_getValid = lambda res: res.status_code not in [400, 404] and res.headers.get('content-type') is not None and 'json' in res.headers.get('content-type')
l_prefixSSL = lambda b: ("http://" if b else "https://") 

def getServiceRoot(ipaddr, auth=None, chkCert=True, nossl=False):
    """
    Get service root
    """
    try:
        rs = requests.get(l_prefixSSL(nossl) + ipaddr + '/redfish/v1', auth=auth, verify=chkCert, timeout=20)
        if l_getValid(rs):
            return True, rs.json(object_pairs_hook=OrderedDict)
    except Exception as ex:
        sys.stderr.write("Something went wrong: %s" % str(ex))
    return False, None 


def getSingleSystem(sutURI, auth=None, chkCert=True, nossl=False):
    """
    Get single system
    """
    sysName = sutURI.rsplit('/',1)[-1]
    try:
        rs = requests.get(l_prefixSSL(nossl) + sutURI, auth=auth, verify=chkCert, timeout=20)
        if l_getValid(rs):
            return (True, sysName, sutURI, rs.json())
    except Exception as ex:
        sys.stderr.write("Something went wrong: %s" % str(ex))
    return (False, sysName, sutURI, None)


def getSystems(ipaddr, auth=None, chkCert=True, nossl=False):
    """
    Get systems from a given IP
    """

    sutList = list()
    success = False
    status_code = -1

    try:
        r = requests.get(l_prefixSSL(nossl) + ipaddr + "/redfish/v1/Systems", auth=auth, verify=chkCert, timeout=20)
        status_code = r.status_code
        success = l_getValid(r)
        if success:
            decoded = r.json(object_pairs_hook=OrderedDict)
            members = decoded.get('Members')

            if members is None:
                sys.stderr.write("Members from /Systems does not exist.")
                return False, sutList, r.status_code
            
            for system in members:
                sysURI = system.get('@odata.id') 
                if sysURI is None:
                    sys.stderr.write("No @odata.id for this system")
                    sutList.append((False, '-', '-', None))
                sutList.append(getSingleSystem(ipaddr + sysURI, auth, chkCert, nossl))
        else:
            print(r.text)
    except Exception as ex:
        sys.stderr.write("Something went wrong: %s" % str(ex))
        success = False
    return success, sutList, status_code
        

def postBootAction(SUT, typeBoot, auth=None, chkCert=True, nossl=False):
    """
    Post boot action to given system
    """
    payload = {
                "ResetType": typeBoot
              }
    r = requests.post(l_prefixSSL(nossl) + SUT + "/Actions/ComputerSystem.Reset", auth=auth, verify=chkCert, json=payload,timeout=20)
    return r


def patchBootOverride(SUT, enable, target, auth=None, chkCert=True, nossl=False):
    """
    Patch boot override details to given system

    """
    payload = {
                 "Boot":{
                      "BootSourceOverrideEnabled": enable,\
                      "BootSourceOverrideTarget": target\
                }   
              }
    r = requests.patch(l_prefixSSL(nossl) + SUT, auth=auth, verify=chkCert, json=payload)
    return r


def getBootStatus(SUT, auth=None, chkCert=True, nossl=False):
    """
    Patch boot override details to given system
    """
    try:
        r = requests.get(l_prefixSSL(nossl) + SUT, auth=auth, verify=chkCert)
        if l_getValid(r):
            decoded = r.json(object_pairs_hook=OrderedDict)
            return decoded['Boot']['BootSourceOverrideEnabled'], decoded['Boot']['BootSourceOverrideTarget']
    except Exception as ex:
        sys.stderr.write("Something went wrong: %s" % str(ex))
    return None, None


def checkBootPass(oldOverride, oldType, newOverride, newType):
    """
    return True if input corresponds with results
    """
    return (newOverride == oldOverride == 'Continuous' and newType == oldType) or\
        (newOverride == oldOverride == 'Disabled' and newType == oldType) or\
        (newOverride == oldOverride == 'Once' and newType == 'None')


def checkAllowedValue ( json, value ):
    sutBoot = json.get('Boot')
    sutAllowedValues = sutBoot.get('BootSourceOverrideTarget@Redfish.AllowableValues')
    return value in sutAllowedValues if sutAllowedValues is not None else False


def verifyBoot(ipaddr, override, typeBoot, single=None, auth=None, delay=120, chkCert=True, nossl=False):
    """
    Verify the service for one-time boot compliance

    param arg1: ipaddress
    param arg2: type of enable [Disable, Once, Continuous]
    param arg3: boot destination [Pxe, Hdd...]
    param auth: auth tuple (user,passwd), default None
    param delay: delay for checking the change, default 120
    param chkCert: boolean of checking certificate
    param nossl: boolean for http/s
    """
    # get pages
    
    auth = auth if not nossl else None
    print('verifyBoot on {}'.format(l_prefixSSL(nossl) + ipaddr))
   
    # corral args into dict for positional params
    argdict = {'auth': auth, 'chkCert':chkCert, 'nossl':nossl}
    
    # depending on parameter, gather single system or all systems
    if single is not None:
        success, sutList, rcode = True, [getSingleSystem(ipaddr + single, **argdict)], '-'
    else:
        success, sutList, rcode = getSystems(ipaddr, **argdict)
    
    # get one time options
    print('{}, collected {} systems, code {}'.format('FAIL' if not success else 'SUCCESS', len(sutList), rcode))
    cntSuccess = 0
    successes = list()
    msgs = list()
    for sut in sutList:
        sutStatus, sutName, sutURI, sutJson = sut
        print( sutStatus, sutName, sutURI )
        # if this system succeeded, start verify
        if sutStatus:
            allowedValue = checkAllowedValue( sutJson, typeBoot )

            # change boot object, then check if behavior succeeded
            r = patchBootOverride(sutURI, override, typeBoot, **argdict)
            print(r.text,r.status_code)
            sleep(10)

            currentOverride, currentType = getBootStatus(sutURI, **argdict)
            if (override, typeBoot) != (currentOverride, currentType):
                if r.status_code == 400 and typeBoot != currentType and not allowedValue: 
                    print('Boot change patch not valid, successful Bad Response')
                else:
                    print('Boot change patch failed')
                    success = False
                continue
            else:
                if typeBoot == currentType and not allowedValue:
                    print('Boot change patch failure, value is not allowed yet is patched')
                    success = False
                    continue
                else:
                    print('Boot change patch success')
            
            # commit restart action, requires GracefulRestart
            r = postBootAction(sutURI, "GracefulRestart", **argdict)
            print(r.text,r.status_code)
            sleeptime = delay
           
            # loop until sleeptime ends, pass if status is correct
            newOverride, newType = getBootStatus(sutURI, **argdict)
            print('Boot status change', newOverride, newType)
            while sleeptime > 0:
                sleep(min(sleeptime,30))
                newOverride, newType = getBootStatus(sutURI, **argdict)
                print('Boot status change', newOverride, newType)
                sleeptime = sleeptime - 30
            successSystem = checkBootPass(currentOverride, currentType, newOverride, newType)
            currentMsg = 'Boot status change {}'.format('FAIL' if not successSystem else 'SUCCESS')
            cntSuccess += 1 if successSystem else 0
            success = success and successSystem
            successes.append(successSystem)
            msgs.append(currentMsg)
        else:
            currentMsg = 'Boot system does not exist {}'.format( sutName )
            print (currentMsg)
            success = successSystem = False
            successes.append(successSystem)
            msgs.append(currentMsg)

    msg = '{} out of {} systems passed'.format(cntSuccess, len(sutList))
    return [sutItem[1] for sutItem in sutList], successes, msgs

def main(argv):
    argget = argparse.ArgumentParser(description='Usecase tool to check compliance to POST Boot action')
    argget.add_argument('ip', type=str, help='ip to test on')
    argget.add_argument('override', type=str, help='type of boot procedure')
    argget.add_argument('type', type=str, help='what to boot into')
    argget.add_argument('-u','--user', type=str, help='user for basic auth')
    argget.add_argument('-p','--passwd', type=str, help='pass for basic auth')
    argget.add_argument('--delay', type=int, default=120, help='optional delay time in seconds')
    argget.add_argument('--nochkcert', action='store_true', help='ignore check for certificate')
    argget.add_argument('--nossl', action='store_true', help='use http instead of https')
    argget.add_argument('--single', type=str, help='uri points to a single system rather than a whole service')
    argget.add_argument('--output', default=None, type=str, help='output directory for results.json')
    
    args = argget.parse_args()
        
    ip = args.ip
    override = args.override
    typeBoot = args.type
    nossl = args.nossl
    auth = (args.user, args.passwd)
    nochkcert = args.nochkcert
    output_dir = args.output
    
    print(ip, override, typeBoot, nochkcert, nossl)
    opts = []
    argsList = []
    for each in str(args).replace('Namespace(','')[:-1].split(', '):
        argsplit = each.split('=',1)
        opts.append(argsplit[0])
        if argsplit[0] == 'passwd':
            argsList.append('**********')
        else:
            argsList.append(argsplit[1])
   
    # create results object
    # how do I report multiple tested systems??
    success, service_root = getServiceRoot(ip, auth=auth, chkCert=(not nochkcert), nossl=nossl)
    results = Results("One Time Boot", service_root if success else dict())
    results.add_cmd_line_args(opts, argsList)
    if output_dir is not None:
        results.set_output_dir(output_dir)

    if not success:
        suts ,rcs, msgs = ['None'], [False], ["ServiceRoot not available"]
        print( "ServiceRoot is not available" )
    else:
        suts, rcs, msgs = verifyBoot(ip, override, typeBoot, single=args.single, auth=auth, delay=120, chkCert=(not nochkcert), nossl=nossl)
    
    for sut, rcbool, msg in zip(suts, rcs, msgs):
        rc = 0 if rcbool else 1
        results.update_test_results(sut, rc, msg)

    # validator = SchemaValidation(rft, service_root, raw_main, results)
    results.write_results()

    return 0 if False not in rcs else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
