import boto3
import json
import requests
import sys

import res.utils as utils
import config as config 
import res.compute as compute
import res.awsthread as awsthread

from res.utils import thread_list as thread_list


# SET PYTHON PATH TO INCLUDE export PYTHONPATH=/home/ubuntu/test/lscape/lightscape/agent/src/aws_inventory:$PYTHONPATH
# TO RUN: Try python3 rds.py --services "ec2"

class AgentEnv():

    """
    Get args for ineventory service
    """
    def __init__(self):
        self.profile_name, self.arguments, self.boto3_config, self.selected_regions = utils.check_arguments(sys.argv[1:])
        # --- Displaying execution parameters
        print ('AgentEnv: Number of services   :', len(self.arguments))
        print ('AgentEnv: Services List        :', str(self.arguments))

        # --- AWS basic information
        self.ownerId = utils.get_ownerID(self.profile_name)
        config.logger.info('OWNER ID: ' + self.ownerId)
        config.logger.info('AWS Profile: ' + str(self.profile_name))

        # Resets values set in inventory.py Jag
        config.nb_units_done = 0
        for svc in self.arguments:
            config.nb_units_todo += (config.nb_regions * config.SUPPORTED_INVENTORIES[svc])

        if (len(self.arguments) == 0):
            sys.argv.append("error")
            utils.check_arguments(sys.argv[1:])
            exit(0)


class EC2Instances():
    """
    Class to define methods for extracting RDS info with relevant paramters required.
    """

    def __init__(self, agentEnv):
        self.agentEnv = agentEnv
        self.ec2Inventory = {}    

    def discoverEC2Instances(self):
        self.ec2Thread = (awsthread.AWSThread("ec2", compute.get_ec2_inventory, self.agentEnv.ownerId, 
            self.agentEnv.profile_name, self.agentEnv.boto3_config, self.agentEnv.selected_regions))
        self.ec2Thread.start()
        thread_list.append(self.ec2Thread)
        #self.ec2Inventory["ec2"] = config.global_inventory["ec2"]
        #self.ec2Inventory["ec2-network-interfaces"] = config.global_inventory["ec2-network-interfaces"]
        #self.ec2Inventory["ec2-ebs"] = config.global_inventory["ec2-ebs"]
        #self.ec2Inventory["ec2-vpcs"] = config.global_inventory["ec2-vpcs"]
        #self.ec2Inventory["ec2-security-groups"] = config.global_inventory["ec2-security-groups"]
        #self.ec2Inventory["ec2-internet-gateways"] = config.global_inventory["ec2-internet-gateways"]
        #self.ec2Inventory["ec2-nat-gateways"] = config.global_inventory["ec2-nat-gateways"]
        #self.ec2Inventory["ec2-subnets"] = config.global_inventory["ec2-subnets"]
        #self.ec2Inventory["ec2-eips"] = config.global_inventory["ec2-eips"]
        #self.ec2Inventory["ec2-egpu"] = config.global_inventory["ec2-egpus"]

    def getEC2Instances(self):
        self.ec2Inventory["ec2"] = config.global_inventory["ec2"]
        return self.ec2Inventory

    def printEC2Inventory(self):
        Utils.printInventory("ec2", self.agentEnv, self.getEC2Instances())


class Utils():
    """
    Utils function for common utility processes across the app
    """
    @staticmethod
    def writeToJsonFile(fileName,data):
        with open(fileName, "w") as of:
            of.write(data)

    @staticmethod
    def aPIPostClient(url,payload):
        response = requests.post(url,data=payload)
        return response

    @staticmethod
    def printInventory(service, agentEnv, inventory):
        filename_json = 'AWS_{}_{}_{}.json'.format(service, agentEnv.ownerId, config.timestamp)
        try:
            json_file = open(config.filepath+filename_json,'w+')
        except IOError as e:
            config.logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))

        json_file.write(json.JSONEncoder().encode(inventory))
        json_file.close()


class AgentMain():
    """
    LS Agent entry point process 
    """

    def __init__(self, agentEnv):
        self.agentEnv = agentEnv
        self.apiUrl = "http://127.0.0.1:5000/api/v1alpha1/gw/data-aggregator"
        self.agentId = "tstls123"

    """
    def initRDSInstances(self,id=None):
        self.rdsInstanceInfo = DBInstances()
            self.rdsInstances = self.rdsInstanceInfo.getDBInstances()
    """

    def streamData(self,data,identifier):
        fData = json.dumps({"agentId":self.agentId,"lsDataDump":data}, default=str)
        Utils.writeToJsonFile(identifier+".json",fData)
        Utils.aPIPostClient(self.apiUrl,fData)


    """
    def collectParameters(self):
        for instance in self.rdsInstances['DBInstances']: 
            instanceIden = instance["DBInstanceIdentifier"]
            print("DB Instance info -> ", instance)
            self.streamData(instance,"DB_Instance_"+instanceIden)
            dbParameterG = instance['DBParameterGroups'][0]['DBParameterGroupName'] # Use loop here
            dbParameter = self.rdsInstanceInfo.getDBParameters(dbParameterG)
            self.streamData(dbParameter,"DB_Instance_Parameter"+instanceIden)
            self.streamData(self.rdsInstanceInfo.getDBLogInfo(instanceIden),"DB_Instance_Loginfo_"+instanceIden)
    """

    def initEC2Instances(self):
        ec2Obj = EC2Instances(self.agentEnv)
        ec2Obj.discoverEC2Instances()
        return ec2Obj
        #self.streamData(ec2s,"EC2_Instances")
        

def main():
    agentEnv = AgentEnv()
    agent = AgentMain(agentEnv)
    if ('rds' in agentEnv.arguments):
        #agent.initRDSInstances()
        config.logger.debug("Done processing RDS - IGNORE")
    # agent.collectParameters()
    if ('ec2' in agentEnv.arguments):
        ec2Obj = agent.initEC2Instances()
        config.logger.debug("Done processing EC2")

    config.logger.debug("Waiting on threads execution")
    for th in thread_list:
      th.join()
    config.logger.debug("All threads done executing")

    ec2Obj.printEC2Inventory()
    config.logger.debug("Done processing in main - reached end of main")


main()
