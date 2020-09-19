import copy
import json
from pyModbusTCP.client import ModbusClient
import datetime

class modbusTCP_Slave:
    # Working Modes    
    RESULT_MODE__RETURN_ALL_VALUES__RAW = 0
    RESULT_MODE__RETURN_ALL_VALUES__FORMATTED = 1
    RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW = 2
    RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED = 3

    def __init__(self, _jsonFile, _resultMode = 0):

        # JSON object with the information of the Modbus Master device        
        self.deviceHost = _jsonFile["host"]
        self.devicePort = _jsonFile["port"]
        self.deviceData = _jsonFile["data"]

        # Result Mode
        self.resultMode = int(_resultMode)

        # For Polling Process
        self.deviceData_LastValues = ""
        self.deviceData_CurrentValues = ""

    # Connect with Modbus Server
    def SetupPollingProcess(self): 

        # Initialize deviceData values
        for data_point in self.deviceData:
            data_point["value"] = 0

        try:
            # Create Client
            self.client = ModbusClient()
            self.client.host(self.deviceHost)
            self.client.port(self.devicePort)
            self.client.unit_id(1)
        except ValueError as e:
            # Problems accessing Modbus Server
            return -1

        # Initialize copies of data
        self.deviceData_LastValues = copy.deepcopy(self.deviceData)
        self.deviceData_CurrentValues = copy.deepcopy(self.deviceData)

        # Setup process OK
        return 0

    # Poll data from Modbus Master device
    def PollDataFromDevice(self):

        # Open or reconnect TCP to server
        if not self.client.is_open():
            if not self.client.open():
                return -1

        if self.client.is_open():
            # Go through data and act correspondingly
            for data_point in self.deviceData_CurrentValues:
                addr = data_point["address"]
                if data_point["type"] == "coil":
                    read_data = self.client.read_coils(addr, 1)
                    if read_data != None:              
                        data_point["value"] = read_data

                elif data_point["type"] == "register":
                    read_data = self.client.read_holding_registers(addr, 1)
                    if read_data != None:
                        data_point["value"] = read_data        

            ### Process Data and return it depending on Working Mode
            #   RESULT_MODE__RETURN_ALL_VALUES__RAW ==> 0
            #   RESULT_MODE__RETURN_ALL_VALUES__FORMATTED ==> 0
            #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW ==> 0
            #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED ==> 0
            ##################################################################
            if (self.resultMode == self.RESULT_MODE__RETURN_ALL_VALUES__RAW):
                # All data - RAW
                return self.deviceData_CurrentValues
            elif (self.resultMode == self.RESULT_MODE__RETURN_ALL_VALUES__FORMATTED):
                # All data - FORMATTED
                return self.__formatDataValue(self.deviceData_CurrentValues)   
            else:
                # Check for new values
                newValues = self.__checkForNewValues(self.deviceData_LastValues, self.deviceData_CurrentValues)                
                
                # Copy of the latest received data
                self.deviceData_LastValues = copy.deepcopy(self.deviceData_CurrentValues)

                # Process new values, if there is any
                if (newValues != []):
                    # RAW or FORMATTED?
                    if (self.resultMode == self.RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW):
                        return newValues
                    elif (self.resultMode == self.RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED):
                        return self.__formatDataValue(newValues)   
                else:                    
                    return []
                
    # Format RAW data according to this template
    # [ 07/16/20 @ 12:48:06 - 126 ] ---> localhost @ Port: 11503 ==> Value: False from     coil at address: 1520
    def __formatDataValue(self, values):

        # Prepare timestamp
        temp = datetime.datetime.now()
        x = temp.strftime("%x")
        y = temp.strftime("%X")
        z = temp.strftime("%f")
        timestamp = "[ " + x + " @ " + y + " - " + z[:3] + " ]"

        result = []

        for data_point in values:

            # Prepare value
            value = str(data_point["value"][0]).rjust(5)

            # Format information
            formattedValue = (str(timestamp) 
                + " ---> "
                + str(self.deviceHost)
                + " @ Port: "
                + str(self.devicePort)
                + " ==> Value: "
                + value
                + " from "
                + (data_point["type"]).rjust(8)
                + " at address: "
                + str(data_point["address"])
            )

            result.append(formattedValue)

        return result

    # Check if latest polled data is new
    # Only new data will be taken into account
    def __checkForNewValues(self, lastValues, currentValues):
        # Temp array
        newValues = []

        for current_DP in currentValues:
            # Check if the value changed
            for last_DP in lastValues:            
                if (last_DP["type"] == current_DP["type"]) and (last_DP["address"] == current_DP["address"]) and (last_DP["value"] != current_DP["value"]):
                    # --- New value                    
                    newValues.append(current_DP)

        return newValues