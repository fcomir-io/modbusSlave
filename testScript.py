from pathlib import Path
import sys
import os
import json
from modbusTCP_Slave import modbusTCP_Slave

'''
Simple script to test the functionality of the modbusTCP_Slave.py class
'''

def CheckModbusDeviceListFile(jsonFile):
    print(jsonFile)
    # Check if argument is a file or a directory
    if (jsonFile.startswith('/')):
        # --> User introduced a path
        fileToCheck = Path(jsonFile)
    else:
        # --> User introduced a name of a file located in the same path
        fileToCheck = Path(os.getcwd() + "/" + jsonFile)
    
    # Check if file exists    
    if fileToCheck.is_file():        

        # Check if file is JSON ok
        try:
            # Since we are working with python v3.5, open needs a string as argument
            json_object = json.loads(open(str(fileToCheck)).read())
        except Exception as e:
            print(fileToCheck, e)
            return [2, ""]
        return [0, json_object]
    else:
        return [1, ""]


if __name__ == "__main__":

    # Check file content and extract json Object
    result = CheckModbusDeviceListFile(sys.argv[1])        
    ### modbusDevicesList is an array of two values:
    #   - Positon 0 ==> Error code.
    #     * '0' ==> No error
    #     * '1' ==> File not found
    #     * '2' ==> Not JSON format
    #   - Positon 1 ==> JSON data with Modbus Devices List or empty string if there was an error
    #############################################################################################

    # Check if JSON file is correct
    if result[0] == 0:
        # Instantiate a Modbus Slave object
        jsonFile = result[1]
        resultMode = int(sys.argv[2])
        slave = modbusTCP_Slave(jsonFile, resultMode)

        # Setup Polling Process
        status = slave.SetupPollingProcess()

        # Check if Polling Process was initiated correctly
        if status == 0:
            # --> Slave can poll data from Master

            startMessage = "\n   Polling Data from Device   \n"
            startMessage = startMessage + " ---------------------------- \n"    
            print(startMessage)

            # Start Polling Loop        
            main_loop_flag = True
            while main_loop_flag:            
                
                # Get latest data from master
                result = slave.PollDataFromDevice()

                # Check if there is an error
                if result == -1:
                    # -->  There is no Server on the other side or the connection is not possible 
                    print("[ERROR] TCP Server could not be opened - ", result, " [", type(result), "]")
                else:

                    ### Process Result depending on Result Mode set by execution
                    #   RESULT_MODE__RETURN_ALL_VALUES__RAW ==> 0
                    #   RESULT_MODE__RETURN_ALL_VALUES__FORMATTED ==> 0
                    #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW ==> 0
                    #   RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED ==> 0
                    ##################################################################

                    if (resultMode == slave.RESULT_MODE__RETURN_ALL_VALUES__RAW):                    
                        # All data - RAW
                        if result != "":
                            print("All RAW Data: ", result)
                    elif (resultMode == slave.RESULT_MODE__RETURN_ALL_VALUES__FORMATTED):
                        # All data - FORMATTED
                        if result != []:                        
                            for item in result:
                                print("All FORMATTED Data: ", item)
                    elif (resultMode == slave.RESULT_MODE__RETURN_ONLY_NEW_VALUES__RAW):
                        # Only NEW data - RAW
                        if result != []:
                            print("Only NEW Data - RAW: ", result)
                    elif (resultMode == slave.RESULT_MODE__RETURN_ONLY_NEW_VALUES__FORMATTED):
                        # Only NEW data - FORMATTED
                        if result != []:
                            for item in result:
                                print("Only NEW Data - FORMATTED: ", item)
                    else:
                        if result != "" and result != []:
                            print("Unknown Result Mode: ", result)            
            
            # Out of the while
            client.close()
        else:
            # --> Polling process was not initiated correctly

            ### Possible errors
            #   - '1' ==> Problems accessing Modbus Server
            ###############################################
            print("SetupPollingProcess - Status: ", status)               
    else:
        # --> JSON File could not be parsed

        ### Possible errors
        #   - '1' ==> File not found
        #   - '2' ==> Not JSON format
        ###############################
        print("JSON Parsing - Error code: ", result[0])

    print("\n --- END OF CLIENT --- \n")
