import boto3
import json
import requests

# client = boto3.client('rds')

# print(client.describe_pending_maintenance_actions())

class BotoClientSetup():
	"""
	RDS CLient Setup with BOTO client
	"""
	def setUp(self,isRemote,service):
		if isRemote:
			self.getAWSCreds()
			return boto3.client(service,aws_access_key_id=self.awsCreds["aws_access_key_id"],aws_secret_access_key=self.awsCreds["aws_secret_access_key"],aws_session_token=self.awsCreds["aws_session_token"])
		else:
			return boto3.client(service)

	def getAWSCreds(self):
		x = requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/LSROUser")
		self.awsCreds = x.json()


class DBInstances():
	"""
	Class to define methods for extracting RDS info with relevant paramters required.
	"""

	def __init__(self):
		self.remote = False
		# self.remote = True
		self.rdsClient = BotoClientSetup().setUp(self.remote,"rds")

	def getDBInstances(self):
		return self.rdsClient.describe_db_instances()

	def getDBParameters(self,iden):
		return self.rdsClient.describe_db_parameters(DBParameterGroupName=iden)

	def getDBLogInfo(self,iden):
		return self.rdsClient.describe_db_log_files(DBInstanceIdentifier=iden)	


class EC2Instances():
	"""
	Class to define methods for extracting RDS info with relevant paramters required.
	"""

	def __init__(self):
		self.remote = False
		# self.remote = True
		self.ec2Client = BotoClientSetup().setUp(self.remote,"ec2")

	def getEC2Instances(self):
		return self.ec2Client.describe_instances()


class InventoryService():

	def setUp(self):
		self.client = boto3.client('ec2')


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




class AgentMain():
	"""
	LS Agent entry point process 
	"""

	def __init__(self):
		self.apiUrl = "http://127.0.0.1:5000/api/v1alpha1/gw/data-aggregator"
		self.agentId = "tstls123"

	def initRDSInstances(self,id=None):

		self.rdsInstanceInfo = DBInstances()
		self.rdsInstances = self.rdsInstanceInfo.getDBInstances()

	def streamData(self,data,identifier):
		fData = json.dumps({"agentId":self.agentId,"lsDataDump":data}, default=str)
		Utils.writeToJsonFile(identifier+".json",fData)
		Utils.aPIPostClient(self.apiUrl,fData)


	def collectParameters(self):

		for instance in self.rdsInstances['DBInstances']:
			instanceIden = instance["DBInstanceIdentifier"]
			# print("DB Instance info -> ", instance)
			self.streamData(instance,"DB_Instance_"+instanceIden)
			dbParameterG = instance['DBParameterGroups'][0]['DBParameterGroupName'] # Use loop here
			dbParameter = self.rdsInstanceInfo.getDBParameters(dbParameterG)
			self.streamData(dbParameter,"DB_Instance_Parameter"+instanceIden)
			self.streamData(self.rdsInstanceInfo.getDBLogInfo(instanceIden),"DB_Instance_Loginfo_"+instanceIden)

	def initEC2Instances(self):
		ec2Obj = EC2Instances()
		ec2s = ec2Obj.getEC2Instances()
		self.streamData(ec2s,"EC2_Instances")
		




def main():
	agent = AgentMain()
	# agent.initRDSInstances()
	# agent.collectParameters()
	agent.initEC2Instances()



main()
`
