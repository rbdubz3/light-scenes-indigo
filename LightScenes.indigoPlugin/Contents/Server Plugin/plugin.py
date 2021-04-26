#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com
#

################################################################################
# Imports
################################################################################
import indigo
import urllib2
from xml.dom.minidom import parseString
import time
import datetime
import threading
import Queue
import sys
import enum

################################################################################
# Globals
################################################################################

########################################
def updateVar(name, value, folder=0):
    if name not in indigo.variables:
        indigo.variable.create(name, value=value, folder=folder)
    else:
        indigo.variable.updateValue(name, value)


################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    # Class properties
    ########################################

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("showDebugInfo", False)
        self.deviceList = []
        self.deviceThreads = []
        self.threadLock = threading.Lock()
        self.sceneQueue = Queue.Queue(100)
        self.lastRefreshTime = datetime.datetime.now()

    ########################################
    def deviceStartComm(self, device):
        if device.id not in self.deviceList:
            props = device.pluginProps
            self.debugLog(
                "Device: id=" + str(device.id) + ",name: " + device.name)
            # Set SupportsColor property so Indigo knows device accepts color actions and should use color UI.
            if props["SupportsRGB"] == True:
                # this is a color bulb
                props["SupportsColor"] = True
            else:
                # this is a tunable white bulb
                props["SupportsColor"] = True
                props["SupportsWhiteTemperature"] = True

            self.debugLog("Updating device id1: " + str(device.id) + ", name: " + device.name)
            device.replacePluginPropsOnServer(props)
            device.updateStateImageOnServer(indigo.kStateImageSel.Auto)

            try:
                #self.debugLog("Updating device id2: " + str(device.id) + ", name: " + device.name)
                self.update(device)
                #self.debugLog("Updating device id3: " + str(device.id) + ", name: " + device.name)
                self.deviceList.append(device.id)
                #self.debugLog("Updating device id4: " + str(device.id) + ", name: " + device.name)
            except Exception as ex:
                self.logger.debug("Exception hit in deviceStartComm - " + str(ex))



    ########################################
    def deviceStopComm(self, device):
        for gThread in self.deviceThreads:
            if gThread.theDevice.name == device.name:
                gThread.stopDevConcurrentThread()
                self.deviceThreads.remove(gThread)
                indigo.server.log("Stopping device thread: " + device.name)

        if device.id in self.deviceList:
            self.deviceList.remove(device.id)
            indigo.server.log("Stopping device: " + device.name)


    # Startup
    ########################################
    def startup(self):
        indigo.server.log(u"Startup called.")
        # Perform an initial version check.
        indigo.server.log(u"Running plugin version check (if enabled).")
        #self.updater.checkVersionPoll()

        if 'scenes' in self.pluginPrefs:
            scenes = self.pluginPrefs['scenes']
        else:
            scenes = list()

        if not self.pluginPrefs.get('scenes', False) and not self.pluginPrefs.get('scenesList', False):
            indigo.server.log(u"pluginPrefs lacks scenes.  Adding.")
            # Add the empty scenes list to the prefs.
            for aNumber in range(1,21):
                # Create a blank sub-list for storing scene name and scene states.
                scene = list()
                # Add the sub-list to the empty scenes list.
                scenes.append(scene)

                if aNumber == 1:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding Christmas.")
                    # Add the scene name.
                    scene.append('Christmas')
                    scene.append('match-colors')
                    scene.append('30')
                    sceneData = list()
                    sceneData.append('0,0,255,0,90,50')
                    sceneData.append('255,125,0,0,90,50')
                    sceneData.append('0,255,0,0,90,50')
                    sceneData.append('255,00,0,0,90,50')
                    sceneData.append('255,255,0,0,90,50')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1650,2400,3800,6400,6500,4500,2200')
                    circadianData.append('10,35,90,95,100,80,40')
                    scene.append(circadianData)
                elif aNumber == 2:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding Halloween.")
                    # Add the scene name.
                    scene.append('Halloween')
                    scene.append('match-colors')
                    scene.append('30')
                    sceneData = list()
                    sceneData.append('40,0,80,0,65,100')
                    sceneData.append('40,0,80,0,40,1000')
                    sceneData.append('100,20,0,0,40,100')
                    sceneData.append('100,20,0,0,65,1000')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1650,2400,3800,6400,6500,4500,2200')
                    circadianData.append('10,35,90,95,100,80,40')
                    scene.append(circadianData)
                elif aNumber == 3:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding St. Patricks.")
                    scene.append('St. Patricks')
                    scene.append('match-colors')
                    scene.append('60')
                    sceneData = list()
                    sceneData.append('13,89,1,0,90,500')
                    sceneData.append('0,255,0,0,10,500')
                    sceneData.append('0,179,22,0,80,500')
                    sceneData.append('13,239,33,0,25,500')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1650,2400,3800,6400,6500,4500,2200')
                    circadianData.append('10,35,90,95,100,80,40')
                    scene.append(circadianData)
                elif aNumber == 4:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding IndoorCirc.")
                    scene.append('IndoorCirc')
                    scene.append('circadian')
                    scene.append('600')
                    sceneData = list()
                    sceneData.append('13,89,1,0,90,500')
                    sceneData.append('0,255,0,0,10,500')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1650,2400,3800,6400,6500,4500,2200')
                    circadianData.append('10,35,90,95,100,80,40')
                    scene.append(circadianData)
                elif aNumber == 5:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding OutdoorCirc.")
                    scene.append('OutdoorCirc')
                    scene.append('circadian')
                    scene.append('600')
                    sceneData = list()
                    sceneData.append('13,89,1,0,90,500')
                    sceneData.append('0,255,0,0,10,500')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1850,2600,5500,6400,6500,4000,2400')
                    circadianData.append('20,55,80,95,100,85,60')
                    scene.append(circadianData)
                elif aNumber == 6:
                    self.debugLog(u"pluginPrefs lacks scenes.  Adding MBR Circ.")
                    scene.append('MBR Circ')
                    scene.append('circadian')
                    scene.append('600')
                    sceneData = list()
                    sceneData.append('13,89,1,0,90,500')
                    sceneData.append('0,255,0,0,10,500')
                    scene.append(sceneData)
                    circadianData = list()
                    circadianData.append('1900,2200,5500,6400,6500,4500,2200')
                    circadianData.append('10,35,90,98,100,80,35')
                    scene.append(circadianData)
                else:
                    # Add the scene name.
                    scene.append('Scene ' + unicode(aNumber))
                    scene.append('match-colors')
                    scene.append('60')

            # Add the new list of empty scenes to the prefs.
            self.pluginPrefs['scenes'] = scenes
            self.debugLog(u"pluginPrefs now contains 20 scenes.")

        # If scenes exist, make sure there are 20 of them.
        if not self.pluginPrefs.get('scenesList', False) or len(self.pluginPrefs['scenesList']) == 0:
            indigo.server.log(u"pluginPrefs lacks scenesList.  Adding.")
            # fill in the dictionary instead of the list
            self.pluginPrefs['scenesList'] = list()
            # Start a new list of empty scenes.
            scenesList = list()

            for theScene in scenes:
                sceneDict = dict()
                # Add the sub-list to the empty scenes list.
                scenesList.append(sceneDict)
                sceneDict['sceneName'] = theScene[0]
                sceneDict['sceneType'] = theScene[1]
                sceneDict['sceneInterval'] = theScene[2]
                indigo.server.log(u"pluginPrefs checking scene=" + theScene[0])
                if len(theScene) > 3:
                    colorDict = dict()
                    sceneDict['colorData'] = colorDict
                    settingNum = 1
                    for thesetting in theScene[3]:
                        key = 'setting' + str(settingNum) + 'Value'
                        colorDict[key] = thesetting
                        settingNum = settingNum + 1

                    # add some default data if nothing is there
                    if len(colorDict) == 0:
                        #sceneData.append('13,89,1,0,90,500')
                        #sceneData.append('0,255,0,0,10,500')
                        colorDict['setting1Value'] = '13,89,1,0,90,500'
                        colorDict['setting2Value'] = '0,255,0,0,10,500'

                if len(theScene) > 4:
                    circadianDict = dict()
                    sceneDict['circadianData'] = circadianDict
                    if len(theScene[4]) == 2:
                        circadianDict['CircadianColorTempValues'] = theScene[4][0]
                        circadianDict['CircadianBrightnessValues'] = theScene[4][1]
                    else:
                        # add some default data if there is insufficient data
                        circadianDict['CircadianColorTempValues'] = '1900,2200,5500,6400,6500,4500,2200'
                        circadianDict['CircadianBrightnessValues'] = '10,35,90,98,100,80,35'

                self.debugLog(u"adding to scenesList. Scene name: " + str(sceneDict['sceneName']))

            # Add the new list of empty scenes to the prefs.
            self.pluginPrefs['scenesList'] = scenesList

        # after creating the scenesList, we can remove the old scenes
        if 'scenes' in self.pluginPrefs:
            indigo.server.log(u"removing old 'scenes' from pluginPrefs.")
            del self.pluginPrefs['scenes']



    ########################################
    def runConcurrentThread(self):
        indigo.server.log("Starting concurrent tread")
        try:
            while True:
                # we sleep (30 minutes) first because when the plugin starts, each device
                # is updated as they are started.
                currentTime = datetime.datetime.now()
                # find the number of minutes since Some Date
                timeDelta = currentTime - self.lastRefreshTime
                diffMinutes = int(timeDelta.days * 1440 + timeDelta.seconds/60)
                if diffMinutes > 30:
                    try:
                        have_it = self.threadLock.acquire(0)
                        if have_it is True:
                            indigo.server.log('...Refreshing Device Status')
                            self.lastRefreshTime = datetime.datetime.now()
                            # lets also output all of the threads in action
                            sceneThreadCount = 0
                            for curSceneThread in self.deviceThreads:
                                sceneThreadCount = sceneThreadCount + 1
                                indigo.server.log("...Running scene thread - deviceName=" + curSceneThread.theDevice.name +
                                                  ",thread=" +str(curSceneThread))
                            indigo.server.log("...Total scene threads - " + str(sceneThreadCount))

                    finally:
                        if have_it is True:
                            indigo.server.log('...runConcurrentThread RELEASING threadLock after refreshing Device Status')
                            self.threadLock.release()

                # TODO should sleep the minimum of all sleeps for the scenes
                self.sleep(10)

                try:
                    while self.sceneQueue.empty() == False:
                        workItem = self.sceneQueue.get_nowait()
                        num_tries = 0
                        have_it = False
                        while num_tries < 10 and have_it is False:
                            if num_tries != 0:
                                self.sleep(0.5)
                            self.debugLog('...runConcurrentThread TRYING for threadLock')
                            have_it = self.threadLock.acquire(0)
                            try:
                                num_tries += 1
                                if have_it:
                                    self.debugLog('...runConcurrentThread threadLock ACQUIRED, num_tries=' + str(num_tries))
                                    # simulate a delay as we'd expect from the bulbs
                                    self.debugLog('...runConcurrentThread PROCESSING workItem=[groupName:' + workItem.groupName
                                                  + ',sceneName:' + str(workItem.sceneName)
                                                  + ',isGroup:' + str(workItem.isGroupWork) + ',workItemType:' + str(workItem.workItemType)
                                                  + ',colorTemp:' + str(workItem.colorTemp) + ',brightness=' + str(workItem.brightness)
                                                  + ',rgbValues:' + str(workItem.rgbValues)
                                                  + ']')
                                    # find a matching thread in the list
                                    sceneThreadActive = False
                                    for gThread in self.deviceThreads:
                                        if gThread.theDevice.name == workItem.theDevice.name:
                                            sceneThreadActive = True
                                    if sceneThreadActive is True:
                                        if workItem.isGroupWork is False:
                                            lightObject = workItem.theLight
                                            if workItem.workItemType is WorkItemType.RGB:
                                                lightObject.set_rgb(workItem.rgbValues[0], workItem.rgbValues[1],
                                                                    workItem.rgbValues[2], workItem.transitionMillis)
                                            elif workItem.workItemType is WorkItemType.CTEMP:
                                                lightObject.set_temperature(workItem.colorTemp, workItem.transitionMillis)
                                            elif workItem.workItemType is WorkItemType.BRIGHTNESS:
                                                lightObject.set_luminance(workItem.brightness, workItem.transitionMillis)
                                        else:
                                            if workItem.workItemType is WorkItemType.RGB:
                                                # Convert the RGBs to percentage, which is what Indigo API is based
                                                newRed = round((workItem.rgbValues[0] * 100)/255)
                                                newGreen = round((workItem.rgbValues[1] * 100)/255)
                                                newBlue = round((workItem.rgbValues[2] * 100)/255)
                                                indigo.dimmer.setColorLevels(workItem.theDevice.id, newRed, newGreen, newBlue)
                                            elif workItem.workItemType is WorkItemType.CTEMP:
                                                #indigo.dimmer.setColorLevels(workItem.theDevice.id, 100, 100, 100, 100, 0, workItem.colorTemp)
                                                indigo.server.log(u"\"%s\" %s to %s" % (indigo.devices[workItem.theDevice.id].name, "set color", str(workItem.colorTemp)))
                                                existingBrightness = indigo.devices[workItem.theDevice.id].states['brightnessLevel']
                                                indigo.dimmer.setColorLevels(workItem.theDevice.id, 100, 100, 100, 
                                                    existingBrightness, 0, workItem.colorTemp)
                                            elif workItem.workItemType is WorkItemType.BRIGHTNESS:
                                                indigo.server.log(u"\"%s\" %s to %s" % (indigo.devices[workItem.theDevice.id].name, "set brightness", str(workItem.brightness)))
                                                indigo.dimmer.setBrightness(workItem.theDevice.id, value=workItem.brightness)
                                    else:
                                        self.debugLog('...runConcurrentThread SKIPPING stale workItem=' + str(workItem))
                                else:
                                    self.debugLog('...runConcurrentThread threadLock NOT acquired, num_tries=' + str(num_tries))
                            finally:
                                if have_it:
                                    self.debugLog('...runConcurrentThread RELEASING threadLock')
                                    self.threadLock.release()
                        self.debugLog('...runConcurrentThread Done, num_tries=' + str(num_tries))
                    #self.debugLog('...runConcurrentThread EMPTY QUEUE')
                except Queue.Empty:
                    self.debugLog('...runConcurrentThread EXCEPTION EMPTY QUEUE, EMPTY QUEUE, EMPTY QUEUE, EMPTY QUEUE')

        except self.StopThread:
            pass


    ########################################
    def groupListGenerator(self, filter="", valuesDict=None, typeId="", targetId=0):
        # Used in actions that need a list of Osram Lightify gropus.
        self.debugLog(u"Starting groupListGenerator.\n  filter: "
                      + unicode(filter) + u"\n  valuesDict: " + unicode(valuesDict) + u"\n  typeId: "
                      + unicode(typeId) + u"\n  targetId: " + unicode(targetId))

        returnGroupList = list()

        #groupId = 0
        #for theGroup in self.lightifyConn.groups():
        #    self.debugLog('...theGroup - groupId=' + str(groupId) + ', details=' + str(theGroup))
        #    returnGroupList.append([theGroup, theGroup])
        #    groupId = groupId + 1

        # Iterate over our bulbs, and return the available list in Indigo's format
        #for bulbId, bulbDetails in self.lightsDict.items():
        #    if typeId == "":
        #        # If no typeId exists, list all devices.
        #        returnBulbList.append([bulbId, bulbDetails['name']])
        #    elif typeId == "hueBulb" and bulbDetails['modelid'] in kHueBulbDeviceIDs:
        #        returnBulbList.append([bulbId, bulbDetails['name']])
        #    elif typeId == "hueAmbiance" and bulbDetails['modelid'] in kAmbianceDeviceIDs:
        #        returnBulbList.append([bulbId, bulbDetails['name']])
        #    elif typeId == "hueLightStrips" and bulbDetails['modelid'] in kLightStripsDeviceIDs:
        #        returnBulbList.append([bulbId, bulbDetails['name']])
        #    elif typeId == "hueLivingColorsBloom" and bulbDetails['modelid'] in kLivingColorsDeviceIDs:
        #        returnBulbList.append([bulbId, bulbDetails['name']])
        #    elif typeId == "hueLivingWhites" and bulbDetails['modelid'] in kLivingWhitesDeviceIDs:
        #        returnBulbList.append([bulbId, bulbDetails['name']])

        # Debug
        self.debugLog(u"groupListGenerator: Return bulb list is %s" % returnGroupList)

        return returnGroupList


    # Generate Scene List
    ########################################
    def sceneListGenerator(self, filter="", valuesDict=None, typeId="", deviceId=0):
        # Used by action dialogs to generate a list of Scenes saved in the plugin prefs.
        self.debugLog(u"Starting sceneListGenerator.\n  filter: " + unicode(filter) + u"\n  valuesDict: "
                      + unicode(valuesDict) + u"\n  typeId: " + unicode(typeId) + u"\n  deviceId: "
                      + unicode(deviceId))

        theList = list()	# Menu item list.

        scenesList = self.pluginPrefs.get('scenesList', None)
        self.debugLog(u"sceneListGenerator: Scenes in plugin prefs:\n" + unicode(scenesList))

        if scenesList != None:
            sceneNumber = 0

            for sceneDict in scenesList:
                # Determine whether the Scene has saved data or not.
                hasData = ""
                sceneName = sceneDict['sceneName']
                self.debugLog('scene ' + sceneName)
                if 'colorData' in sceneDict.keys() or 'circadianData' in sceneDict.keys():
                    self.debugLog("sceneListGenerator: scene " + sceneName + ", hasData=True")
                    hasData = "*"

                sceneNumber += 1
                theList.append((sceneNumber, hasData + unicode(sceneNumber) + ": " + sceneName))
        else:
            theList.append((0, "-- no scenes --"))

        return theList

    # Generate List of active scenes
    ########################################
    def activeSceneListGenerator(self, filter="", valuesDict=None, typeId="", deviceId=0):
        # Used by action dialogs to generate a list of Scenes saved in the plugin prefs.
        self.debugLog(u"Starting activeSceneListGenerator.\n  filter: " + unicode(filter) + u"\n  valuesDict: "
                      + unicode(valuesDict) + u"\n  typeId: " + unicode(typeId) + u"\n  deviceId: "
                      + unicode(deviceId))

        theList = list()	# Menu item list.

        scenesList = self.pluginPrefs.get('scenesList', None)
        if scenesList != None:
            sceneNumber = 0

            for sceneDict in scenesList:
                # Determine whether the Scene has saved data or not.
                hasData = False
                sceneName = sceneDict['sceneName']
                if 'colorData' in sceneDict.keys() or 'circadianData' in sceneDict.keys():
                    self.debugLog("activeSceneListGenerator: scene " + sceneName + ", hasData=True")
                    hasData = True

                sceneNumber += 1
                if hasData is True:
                    theList.append((sceneNumber, unicode(sceneNumber) + ": " + sceneName))
        else:
            theList.append((0, "-- no scenes --"))

        return theList


    # Scenes List Item Selected (callback from action UI)
    ########################################
    def scenesListItemSelected(self, valuesDict=None, typeId="", deviceId=0):
        self.debugLog(u"Starting scenesListItemSelected.  valuesDict: " + unicode(valuesDict)
                      + u", typeId: " + unicode(typeId) + u", targetId: " + unicode(deviceId))

        self.sceneListSelection = valuesDict['sceneId']
        sceneId = int(valuesDict['sceneId'])
        self.debugLog(u".. sceneId-" + self.sceneListSelection)

        sceneDict = self.pluginPrefs['scenesList'][sceneId-1]

        valuesDict['sceneName'] = sceneDict['sceneName']
        valuesDict['sceneType'] = sceneDict['sceneType']
        valuesDict['sceneInterval'] = sceneDict['sceneInterval']

        if 'colorData' in sceneDict.keys():
            colorDict = sceneDict['colorData']

            if 'setting1Value' in colorDict.keys():
                valuesDict['setting1Value'] = colorDict['setting1Value']
            else:
                valuesDict['setting1Value'] = "255,128,128,0,50,100"
            if 'setting2Value' in colorDict.keys():
                valuesDict['setting2Value'] = colorDict['setting2Value']
            else:
                valuesDict['setting2Value'] = "128,255,255,0,75,100"
            if 'setting3Value' in colorDict.keys():
                valuesDict['setting3Value'] = colorDict['setting3Value']
            else:
                valuesDict['setting3Value'] = ""
            if 'setting4Value' in colorDict.keys():
                valuesDict['setting4Value'] = colorDict['setting4Value']
            else:
                valuesDict['setting4Value'] = ""
            if 'setting5Value' in colorDict.keys():
                valuesDict['setting5Value'] = colorDict['setting5Value']
            else:
                valuesDict['setting5Value'] = ""

        if 'circadianData' in sceneDict.keys():
            circDict = sceneDict['circadianData']

            if 'CircadianColorTempValues' in circDict.keys():
                valuesDict['CircadianColorTempValues'] = circDict['CircadianColorTempValues']
            else:
                valuesDict['CircadianColorTempValues'] = "1900,2300,4000,6400,6500,4500,2200"
            if 'CircadianBrightnessValues' in circDict.keys():
                valuesDict['CircadianBrightnessValues'] = circDict['CircadianBrightnessValues']
            else:
                valuesDict['CircadianBrightnessValues'] = "15,35,80,95,100,80,40"

        self.debugLog(u"... selected sceneId: " + unicode(sceneId)
                      + u", sceneName: " + unicode(sceneDict['sceneName']) + u", sceneType: " + unicode(sceneDict['sceneType'])
                      + u", sceneInterval: " + unicode(sceneDict['sceneInterval']))
        if 'colorData' in sceneDict.keys():
            self.debugLog(u"... colorData:+ u" + unicode(sceneDict['colorData']))
        if 'circadianData' in sceneDict.keys():
            self.debugLog(u"... circadianData:+ u" + unicode(sceneDict['circadianData']))

        return valuesDict


    # Save Scene Action
    ########################################
    def saveScene(self, valuesDict, typeId):
        self.debugLog(u"Starting saveScene. valuesDict values:\n" + unicode(valuesDict)
                      +  ", typeId:\n" + unicode(typeId))
        errorsDict = indigo.Dict()
        errorsDict['showAlertText'] = u""

        sceneId = valuesDict['sceneId']
        sceneName = valuesDict['sceneName']
        sceneType = valuesDict['sceneType']
        sceneInterval = valuesDict['sceneInterval']

        self.debugLog(u"Starting saveScene. sceneId:" + unicode(sceneId)
                      +  ", name:" + unicode(sceneName)
                      +  ", interval:" + unicode(sceneInterval)
                      +  ", type:" + unicode(sceneType))

        if not sceneId:
            errorText = u"No Scene specified."
            self.errorLog(errorText)
            # Remember the error.
            self.lastErrorMessage = errorText
            return False
        else:
            # Convert to integer.
            sceneId = int(sceneId)
            # Subtract 1 because key values are 0-based.
            sceneId -= 1

        self.debugLog(u"saveScene - starting Validation for Scene " + unicode(sceneId + 1) + u" (" + sceneName + u") .")
        returnVal = True
        if sceneType == 'match-colors' or sceneType == 'rotate-colors':
            # must have at least 1 color setting
            configStr = 'setting1Value'
            if not valuesDict[configStr]:
                errorsDict[configStr] =  u"No " + configStr + u" specified."
                errorsDict['showAlertText'] += errorsDict[configStr]
                errorText = u"No " + configStr + u" specified."
                self.errorLog(errorText)
                returnVal = False
            else:
                returnVal, valuesDict, errorsDict = self.validateRGBWConfig('setting1Value', valuesDict, errorsDict)

        else:
            # must have at least 1 color setting
            configStr = 'CircadianColorTempValues'
            if not valuesDict[configStr]:
                errorsDict[configStr] =  u"No " + configStr + u" specified."
                errorsDict['showAlertText'] += errorsDict[configStr]
                errorText = u"No " + configStr + u" specified."
                self.errorLog(errorText)
                returnVal = False
            configStr = 'CircadianBrightnessValues'
            if not valuesDict[configStr]:
                errorsDict[configStr] =  u"No " + configStr + u" specified."
                errorsDict['showAlertText'] += errorsDict[configStr]
                errorText = u"No " + configStr + u" specified."
                self.errorLog(errorText)
                returnVal = False

            if returnVal == True:
                returnVal, valuesDict, errorsDict = self.validateCircadianConfig('CircadianColorTempValues', valuesDict, errorsDict)
            if returnVal == True:
                returnVal, valuesDict, errorsDict = self.validateCircadianConfig('CircadianBrightnessValues', valuesDict, errorsDict)

        if returnVal is False:
            self.debugLog(u"saveScene - errors in validation Scene " + unicode(sceneId + 1) + u" (" + sceneName + u") ."
                          + unicode(str(errorsDict['showAlertText'])))
            return valuesDict, errorsDict

        self.debugLog(u"saveScene - finished Validation for Scene " + unicode(sceneId + 1) + u" (" + sceneName + u") .")

        colorDict = dict()
        if valuesDict['setting1Value']:
            colorDict['setting1Value'] = valuesDict['setting1Value']
        if valuesDict['setting2Value']:
            colorDict['setting2Value'] = valuesDict['setting2Value']
        if valuesDict['setting3Value']:
            colorDict['setting3Value'] = valuesDict['setting3Value']
        if valuesDict['setting4Value']:
            colorDict['setting4Value'] = valuesDict['setting4Value']
        if valuesDict['setting5Value']:
            colorDict['setting5Value'] = valuesDict['setting5Value']

        circDict = dict()
        if valuesDict['CircadianColorTempValues']:
            circDict['CircadianColorTempValues'] = valuesDict['CircadianColorTempValues']
        if valuesDict['CircadianBrightnessValues']:
            circDict['CircadianBrightnessValues'] = valuesDict['CircadianBrightnessValues']

        newSceneDict = dict()
        newSceneDict['sceneName'] = sceneName
        newSceneDict['sceneType'] = sceneType
        newSceneDict['sceneInterval'] = sceneInterval
        if len(colorDict) > 0:
            newSceneDict['colorData'] = colorDict
        if len(circDict) > 0:
            newSceneDict['circadianData'] = circDict

        self.debugLog(u"saveScene - adding newSceneDict=" + str(newSceneDict))

        scenesList = self.pluginPrefs['scenesList']

        newScenesList = list()
        for aNumber in range(0,20):
            aDict = dict()
            newScenesList.append(aDict)
            aDict['sceneName'] = scenesList[aNumber]['sceneName']
            aDict['sceneType'] = scenesList[aNumber]['sceneType']
            aDict['sceneInterval'] = scenesList[aNumber]['sceneInterval']
            if 'colorData' in scenesList[aNumber].keys():
                aDict['colorData'] = scenesList[aNumber]['colorData']
            if 'circadianData' in scenesList[aNumber].keys():
                aDict['circadianData'] = scenesList[aNumber]['circadianData']

            if aNumber == sceneId:
                aDict['sceneName'] = newSceneDict['sceneName']
                aDict['sceneType'] = newSceneDict['sceneType']
                aDict['sceneInterval'] = newSceneDict['sceneInterval']
                if len(colorDict) > 0:
                    aDict['colorData'] = colorDict
                if len(circDict) > 0:
                    aDict['circadianData'] = circDict

                self.debugLog(u"saveScene - finished adding NEW, sceneDict=" + str(aDict))

        # Save the device's states to the preset.
        self.pluginPrefs['scenesList'] = newScenesList

        indigo.server.log(u"saveScene - states saved to Scene " + unicode(sceneId + 1) + u" (" + sceneName + u")")


    def getMenuActionConfigUiValues(self, menuId):
        valuesDict = indigo.Dict()
        errorMsgDict = indigo.Dict()

        if menuId == "saveScene":
            scenesList = self.pluginPrefs.get('scenesList', None)
            self.debugLog(u"getMenuActionConfigUiValues: get initial value for saveScene dialog.")

            theScene = None

            if scenesList != None:
                sceneNumber = 0

                for sceneDict in scenesList:
                    # Determine whether the Scene has saved data or not.
                    if 'colorData' in sceneDict.keys() or 'circadianData' in sceneDict.keys():
                        if sceneNumber is 0:
                            theScene = sceneDict
                    sceneNumber += 1

            if theScene is not None:
                self.debugLog(u"...getMenuActionConfigUiValues: loading data for scene0:\n" + unicode(theScene))

                valuesDict['sceneName'] = theScene['sceneName']
                valuesDict['sceneType'] = theScene['sceneType']
                valuesDict['sceneInterval'] = theScene['sceneInterval']
                if 'colorData' in theScene.keys():
                    colorData = theScene['colorData']
                    if colorData is not None:
                        if 'setting1Value' in colorData.keys():
                            valuesDict['setting1Value'] = colorData['setting1Value']
                        else:
                            valuesDict['setting1Value'] = ""
                        if 'setting2Value' in colorData.keys():
                            valuesDict['setting2Value'] = colorData['setting2Value']
                        else:
                            valuesDict['setting2Value'] = ""
                        if 'setting3Value' in colorData.keys():
                            valuesDict['setting3Value'] = colorData['setting3Value']
                        else:
                            valuesDict['setting3Value'] = ""
                        if 'setting4Value' in colorData.keys():
                            valuesDict['setting4Value'] = colorData['setting4Value']
                        else:
                            valuesDict['setting4Value'] = ""
                        if 'setting5Value' in colorData.keys():
                            valuesDict['setting5Value'] = colorData['setting5Value']
                        else:
                            valuesDict['setting5Value'] = ""

                if 'circadianData' in theScene.keys():
                    circData = theScene['circadianData']
                    if circData is not None:
                        if 'CircadianColorTempValues' in circData.keys():
                            valuesDict['CircadianColorTempValues'] = circData['CircadianColorTempValues']
                        else:
                            valuesDict['CircadianColorTempValues'] = ""
                        if 'CircadianBrightnessValues' in circData.keys():
                            valuesDict['CircadianBrightnessValues'] = circData['CircadianBrightnessValues']
                        else:
                            valuesDict['CircadianBrightnessValues'] = ""

        return (valuesDict, errorMsgDict)

    ### Start the scene
    def startScene(self, action, device):
        self.debugLog(u"startScene: device.id: " + unicode(device.id) + u", action:\n" + unicode(action))
        theDevice = indigo.devices[action.deviceId]
        #self.debugLog("...startScene - device id: " + str(action.deviceId) + ", info: " + unicode(theDevice))

        sceneId = int(action.props.get('sceneId', -1))
        scenesList = self.pluginPrefs.get('scenesList', None)

        if scenesList is not None and sceneId != -1 and theDevice is not None:
            sceneDict = scenesList[sceneId-1]
            self.debugLog("...startScene - device: " + str(theDevice.name) + ", scene: " + str(sceneDict))
            sceneName = sceneDict['sceneName']
            sceneType = sceneDict['sceneType']
            sceneInterval = int(sceneDict['sceneInterval'])
            if 'colorData' in sceneDict.keys():
                colorData = sceneDict['colorData']
            if 'circadianData' in sceneDict.keys():
                circadianData = sceneDict['circadianData']

            indigo.server.log("startScene device: " + str(theDevice.name) + ", scene: " + str(sceneName) +
                          ", type:" + str(sceneType) + ", interval:" + str(sceneInterval))

            sceneArray = []
            if sceneType != "circadian":
                for settingNum in range(1,6):
                    key = 'setting' + str(settingNum) + 'Value'
                    if key in colorData.keys():
                        thesetting = colorData[key]
                        self.debugLog("...settingNum=" + str(settingNum) + ", data=" + str(thesetting))
                        tempArray = thesetting.split(",")
                        redVal = int(tempArray[0])
                        greenVal = int(tempArray[1])
                        blueVal = int(tempArray[2])
                        colorTemp = int(tempArray[3])
                        brightness = int(tempArray[4])
                        transMilli = int(tempArray[5])
                        sceneArray.append([redVal, greenVal, blueVal, colorTemp, brightness, transMilli])
            else:
                if len(circadianData) == 2:
                    sceneArray.append(circadianData['CircadianColorTempValues'])
                    sceneArray.append(circadianData['CircadianBrightnessValues'])

            if theDevice is not None and len(sceneArray) != 0:

                self.stopSceneThread(theDevice)

                # create a new one with the correct scene
                self.debugLog("Creating a new scene thread: " + theDevice.name)
                deviceSceneThread = None
                if sceneType == "rotate-colors":
                    deviceSceneThread = RgbRotateSceneThread(theDevice, self.logger, sceneName, sceneInterval,
                                                             sceneArray, self.sceneQueue)
                elif sceneType == "match-colors":
                    deviceSceneThread = RgbMatchSceneThread(theDevice, self.logger, sceneName, sceneInterval,
                                                            sceneArray, self.sceneQueue)
                elif sceneType == "circadian":
                    deviceSceneThread = CircadianSceneThread(theDevice, self.logger, sceneName, sceneInterval,
                                                             sceneArray, self.sceneQueue)

                self.deviceThreads.append(deviceSceneThread)

        return

    ### stop the scene
    def stopScene(self, action, device):
        self.debugLog(u"startScene: device.id: " + unicode(device.id) + u", action:\n" + unicode(action))
        theDevice = indigo.devices[action.deviceId]
        self.debugLog("...stopScene - device id: " + str(action.deviceId) + ", name: " + theDevice.name)

        sceneId = int(action.props.get('sceneId', -1))
        scenes = self.pluginPrefs.get('scenes', None)

        resetTemp = bool(action.props.get('resetTemp', False))
        self.debugLog("stopScene device id: " + str(
            theDevice.id) + ", name: " + theDevice.name + ", resetTemp=" + str(resetTemp))

        stoppedThread = self.stopSceneThread(theDevice)
        # check to see if we need to reset color/temp/etc if we found and stopped a thread
        if stoppedThread and resetTemp is True:
            # reset all the lights to be 2700
            indigo.server.log("stopScene - resetting bulbs to 2700 for device: " + theDevice.name)
            indigo.dimmer.setColorLevels(theDevice.id, 100, 100, 100, 100, 0, 2700)                                      
        elif stoppedThread:
            indigo.server.log("stopScene - stopped scene thread for device: " + theDevice.name)
        else:
            indigo.server.log("stopScene - no scene thread found for device: " + theDevice.name)

        return


    def stopSceneThread(self, device):
        theDevice = indigo.devices[device.id]
        deviceSceneThread = None
        stoppedThread = False
        for gThread in self.deviceThreads:
            self.debugLog("...stopSceneThread Found scene thread: " + str(gThread.theDevice.name))
            if gThread.theDevice.name == theDevice.name:
                deviceSceneThread = gThread
                self.debugLog("...stopSceneThread Found matching scene thread: " + theDevice.name)

        if deviceSceneThread is not None:
            self.debugLog("...stopSceneThread Stopping scene thread: " + theDevice.name)
            deviceSceneThread.stopDevConcurrentThread()
            self.deviceThreads.remove(deviceSceneThread)
            deviceSceneThread = None
            stoppedThread = True
            # any remaining scene workItems will be skipped if an activeScene Thread isn't found for the device

        # lets also output all of the threads in action
        sceneThreadCount = 0
        for curSceneThread in self.deviceThreads:
            sceneThreadCount = sceneThreadCount + 1
            self.debugLog("...stopSceneThread Found running scene thread - deviceName=" + curSceneThread.theDevice.name +
                              ",thread=" +str(curSceneThread))
        self.debugLog("...stopSceneThread Total remaining scene threads - " + str(sceneThreadCount))
        return stoppedThread


    ########################################
    def update(self, device):
        self.debugLog("Updating device idzz: " + str(device.id) + ", name: " + device.name)

    ########################################
    # UI Validate, Close, and Actions defined in Actions.xml:
    ########################################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        # hub = valuesDict['ipAddr'].encode('ascii','ignore').upper()
        # valuesDict['address'] = hub
        # can validate this is a valid ip addr:
        self.debugLog("Need to validate devId:" + str(devId))
        return (True, valuesDict)

    ########################################
    # Validate RGBW string
    ########################################
    def validateRGBWConfig(self, configStr, valuesDict, errorsDict):

        if not valuesDict[configStr]:
            errorsDict[configStr] =  u"No " + configStr + u" specified."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = u"No " + configStr + u" specified."
            self.errorLog(errorText)
            #return valuesDict, errorsDict
            return False, valuesDict, errorsDict

        tempArray = valuesDict[configStr].split(",")
        if len(tempArray) != 6:
            errorsDict[configStr] =  configStr + u" must have 6 values. R,G,B,Temp,Brightness,TransMilli"
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" must have 6 values. R,G,B,Temp,Brightness,TransMilli"
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        tempArray = valuesDict[configStr].split(",")
        redVal = int(tempArray[0])
        greenVal = int(tempArray[1])
        blueVal = int(tempArray[2])
        colorTemp = int(tempArray[3])
        brightness = int(tempArray[4])
        transMilli = int(tempArray[5])

        isTemp = False
        if colorTemp > 0:
            isTemp = True

        if isTemp == False and (redVal < 0 or redVal > 255 or greenVal < 0 or greenVal > 255 or blueVal < 0 or blueVal > 255):
            errorsDict[configStr] =  configStr + u" RGB values must be between 0 and 255."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" RGB values must be between 0 and 255."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if isTemp == True and (redVal != 255 or greenVal != 255 or blueVal != 255):
            errorsDict[configStr] =  configStr + u" ColorTemp RGB values must be 255."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" ColorTemp RGB values must be 255."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if isTemp == True and (colorTemp < 1500 or colorTemp > 6500):
            errorsDict[configStr] =  configStr + u" ColorTemp must be between 1500 and 2500."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" ColorTemp must be between 1500 and 2500."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if brightness < 1 or brightness > 100:
            errorsDict[configStr] =  configStr + u" Brightness must be between 1 and 100."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" Brightness must be between 1 and 100."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if transMilli < 10 or transMilli > 100000:
            errorsDict[configStr] =  configStr + u" transMilli must be between 10 and 100000."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" transMilli must be between 10 and 100000."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        return True, valuesDict, errorsDict

    ########################################
    # Validate Circadian Value
    ########################################
    def validateCircadianConfig(self, configStr, valuesDict, errorsDict):
        isTemp = (configStr == 'CircadianColorTempValues')

        # 1650,2400,3800,6400,6500,4500,2200
        # Late Night, Pre-Sunrise, Post-Sunrise, AM Peak, Max Temp, Pre-Sunset, Post-Sunset
        # Late Night&lt;Pre-Sunrise&lt;Post-Sunrise&lt;AM Peak&lt;Max, also Max&gt;Pre-Sunset&gt;Post-Sunset&gt;Late Night

        if not valuesDict[configStr]:
            errorsDict[configStr] =  u"No " + configStr + u" specified."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = u"No " + configStr + u" specified."
            self.errorLog(errorText)
            #return valuesDict, errorsDict
            return False, valuesDict, errorsDict

        tempArray = valuesDict[configStr].split(",")
        if len(tempArray) != 7:
            errorsDict[configStr] =  configStr + u" must have 7 values. Late Night,Pre-Sunrise,Post-Sunrise,AM Peak,Max Temp,Pre-Sunset,Post-Sunset."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" must have 7 values. Late Night,Pre-Sunrise,Post-Sunrise,AM Peak,Max Temp,Pre-Sunset,Post-Sunset."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        tempArray = valuesDict[configStr].split(",")
        lateNight = int(tempArray[0])
        preSunrise = int(tempArray[1])
        postSunrise = int(tempArray[2])
        amPeak = int(tempArray[3])
        maxVal= int(tempArray[4])
        preSunset = int(tempArray[5])
        postSunset = int(tempArray[6])

        if lateNight > preSunrise or preSunrise > postSunrise or postSunrise > amPeak or amPeak > maxVal:
            errorsDict[configStr] =  configStr + u" - invalid values: Ensure Late Night > Pre-Sunrise > Post-Sunrise > AM Peak > Max."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" - invalid values: Ensure Late Night > Pre-Sunrise > Post-Sunrise > AM Peak > Max."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if maxVal < preSunset or preSunset < postSunset or postSunset < lateNight:
            errorsDict[configStr] =  configStr + u" Invalid values: Ensure Max > Pre-Sunset > Post-Sunset > Late Night."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" - invalid values: Ensure Max > Pre-Sunset > Post-Sunset > Late Night."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if isTemp is True and (lateNight < 1500 or lateNight > 6500 or preSunrise < 1500 or preSunrise > 6500 \
                or postSunrise < 1500 or postSunrise > 6500 or amPeak < 1500 or amPeak > 6500 \
                or maxVal < 1500 or maxVal > 6500 or preSunset < 1500 or preSunset > 6500 \
                or postSunset < 1500 or postSunset > 6500):
            errorsDict[configStr] =  configStr + u" values must be between 1500 and 6500."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" values must be between 1500 and 6500."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        if isTemp is False and (lateNight < 1 or lateNight > 100 or preSunrise < 1 or preSunrise > 100 \
               or postSunrise < 1 or postSunrise > 100 or amPeak < 1 or amPeak > 100 \
               or maxVal < 1 or maxVal > 100 or preSunset < 1 or preSunset > 100 \
               or postSunset < 0 or postSunset > 100):
            errorsDict[configStr] =  configStr + u" values must be between 1 and 100."
            errorsDict['showAlertText'] += errorsDict[configStr]
            errorText = configStr + u" values must be between 1 and 100."
            self.errorLog(errorText)
            return False, valuesDict, errorsDict

        return True, valuesDict, errorsDict


    ########################################
    # Menu Methods
    ########################################
    def toggleDebugging(self):
        if self.debug:
            indigo.server.log("Turning off debug logging")
            self.pluginPrefs["showDebugInfo"] = False
        else:
            indigo.server.log("Turning on debug logging")
            self.pluginPrefs["showDebugInfo"] = True
        self.debug = not self.debug

# Base class for Scene Threads
class SceneThread(threading.Thread):
    def __init__(self, theDevice, logger, sceneName, sceneSleep, theQueue):
        super(SceneThread, self).__init__()
        self.theDevice = theDevice
        self.logger = logger
        self.stopThread = False
        self.sceneName = sceneName
        self.sceneSleep = sceneSleep
        self.theQueue = theQueue

    def startScene(self):
        # start the scene
        self.logger.debug(
            "...start Scene " + self.sceneName + " for device - " + str(self.theDevice.name) + ", thread-id=" + str(
                self.name))

    def stopScene(self):
        # stop the scene
        self.logger.debug(
            "...stop Scene " + self.sceneName + " for device - " + str(self.theDevice.name) + ", thread-id=" + str(
                self.name))

    def run(self):
        try:
            self.startScene()
            while not self.stopThread:
                try:
                    # do the scene stuff
                    self.logger.debug("...Scene " + self.sceneName + " device running - " + str(
                        self.theDevice.name) + ", thread-id=" + str(self.name))

                    # take a sleep based on the scene preferences
                    time.sleep(self.sceneSleep)
                except:  # Do my other non-socket reading stuff here
                    self.logger.debug(
                        "...Scene device exception - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
                    self.logger.debug(
                        "...Unexpected loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        except:
            self.logger.debug(
                "...Scene exception hit, process exiting - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
            self.logger.debug("...Unexpected non-loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        finally:  # Make sure you don't leave any open network connections
            self.stopScene()

    def stopDevConcurrentThread(self):
        self.logger.debug(
            "...stopping concurrent thread for device - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
        self.stopThread = True

# rotates each bulbs in the device thru the different RGBs in the scene - each bulb will take on a different color
class RgbRotateSceneThread(SceneThread):
    def __init__(self, theDevice, logger, sceneName, sceneSleep, sceneArray, theQueue):
        super(RgbRotateSceneThread, self).__init__(theDevice, logger, sceneName, sceneSleep, theQueue)
        self.sceneArray = sceneArray
        self.lightArray = []
        self.start()

    def startScene(self):
        # start the scene
        self.logger.debug(
            "...start Scene " + self.sceneName + " for device - " + str(self.theDevice.name) + ", thread-id=" + str(
                self.name))

    def run(self):
        try:
            self.startScene()
            startIdx = 0
            maxNum = 0
            while not self.stopThread:
                try:
                    # do the scene stuff
                    self.logger.debug("...Scene " + self.sceneName + " device running - " + str(
                        self.theDevice.name) + ", thread-id=" + str(self.name))
                    theIdx = startIdx
                    for curLight in self.lightArray:
                        tArr = self.sceneArray[theIdx]
                        rgbArray = [tArr[0], tArr[1], tArr[2]]
                        cTemp = tArr[3]
                        brightness = tArr[4]
                        transMilli = tArr[5]
                        if cTemp != 0:
                            workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                    curLight,
                                                    False, WorkItemType.CTEMP,
                                                    [255,255,255], cTemp, 0, transMilli)
                        else:
                            workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                    curLight,
                                                    False, WorkItemType.RGB,
                                                    rgbArray, 0, 0, transMilli)

                        self.theQueue.put(workItem)

                        brightDelta = self.theDevice.brightness - float(brightness)
                        if abs(brightDelta) > 1:
                            # next set the brightness
                            workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                        curLight,
                                                        True, WorkItemType.BRIGHTNESS,
                                                        None, 0, int(brightness), transMilli)
                            self.theQueue.put(workItem)
                        else:
                            self.logger.debug("...RGBROTATE SCENE SKIPPING brightness set for Scene " + self.sceneName + " device running - " + str(
                                self.theDevice.name) + ", brightnessDelta=" + str(brightDelta) )

                        theIdx = theIdx + 1
                        if theIdx == len(self.sceneArray):
                            theIdx = 0
                    startIdx = startIdx + 1
                    if startIdx == len(self.sceneArray):
                        startIdx = 0
                    maxNum = maxNum + 1

                    # take a sleep based on the scene preferences
                    time.sleep(self.sceneSleep)
                except:  # Do my other non-socket reading stuff here
                    self.logger.debug(
                        "...Scene device exception - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
                    self.logger.debug(
                        "...Unexpected loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        except:
            self.logger.debug(
                "...Scene exception hit, process exiting - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
            self.logger.debug("...Unexpected non-loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        finally:  # Make sure you don't leave any open network connections
            self.stopScene()

# rotates each bulbs in the group thru the different RGBs in the scene - each bulb will will take on the same color
class RgbMatchSceneThread(SceneThread):
    def __init__(self, theDevice, logger, sceneName, sceneSleep, sceneArray, theQueue):
        super(RgbMatchSceneThread, self).__init__(theDevice, logger, sceneName, sceneSleep, theQueue)
        self.sceneArray = sceneArray
        self.start()

    def startScene(self):
        # start the scene
        self.logger.debug(
            "...start Scene " + self.sceneName + " for device - " + str(self.theDevice.name) + ", thread-id=" + str(
                self.name))

    def run(self):
        try:
            self.startScene()
            startIdx = 0
            while not self.stopThread:
                try:
                    # do the scene stuff
                    theIdx = startIdx
                    tArr = self.sceneArray[theIdx]
                    rgbArray = [tArr[0], tArr[1], tArr[2]]
                    cTemp = tArr[3]
                    brightness = tArr[4]
                    transMilli = tArr[5]
                    self.logger.debug("...Scene " + self.sceneName + " device running - " + str(
                        self.theDevice.name) + ", thread-id=" + str(self.name))
                    if cTemp != 0 and self.theDevice.supportsWhiteTemperature:
                        workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                    None,
                                                    True, WorkItemType.CTEMP,
                                                    [255,255,255], cTemp, 0, transMilli)
                        self.theQueue.put(workItem)
                    elif self.theDevice.supportsRGB:
                        workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                None,
                                                True, WorkItemType.RGB,
                                                rgbArray, 0, 0, transMilli)
                        self.theQueue.put(workItem)


                    brightDelta = self.theDevice.brightness - float(brightness)
                    if abs(brightDelta) > 1:
                        # next set the brightness
                        workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                    None,
                                                    True, WorkItemType.BRIGHTNESS,
                                                    None, 0, int(brightness), transMilli)
                        self.theQueue.put(workItem)
                    else:
                        self.logger.debug("...RGBMATCH SCENE SKIPPING brightness set for Scene " + self.sceneName + " device running - " + str(
                            self.theDevice.name) + ", brightnessDelta=" + str(brightDelta) )



                    startIdx = startIdx + 1
                    if startIdx == len(self.sceneArray):
                        startIdx = 0

                    # take a sleep based on the scene preferences
                    time.sleep(self.sceneSleep)
                except:  # Do my other non-socket reading stuff here
                    self.logger.debug(
                        "...Scene device exception - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
                    self.logger.debug(
                        "...Unexpected loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        except:
            self.logger.debug(
                "...Scene exception hit, process exiting - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
            self.logger.debug("...Unexpected non-loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        finally:  # Make sure you don't leave any open network connections
            self.stopScene()


class CircadianSceneThread(SceneThread):
    def __init__(self, theDevice, logger, sceneName, sceneSleep, sceneArray, theQueue):
        super(CircadianSceneThread, self).__init__(theDevice, logger, sceneName, sceneSleep, theQueue)
        self.sceneArray = sceneArray
        self.start()

    def run(self):
        try:
            self.startScene()
            while not self.stopThread:
                try:
                    # do the scene stuff
                    circadianVals = self.getCircadian()
                    # get an updated copy of the theDevice
                    newIndigoDevice = indigo.devices[self.theDevice.id]
                    if newIndigoDevice is not None:
                        self.theDevice = newIndigoDevice
                    self.logger.debug("...CIRCAUTO Scene " + self.sceneName + " device running - " + str(
                                    self.theDevice.name) + ", thread-id=" + str(self.name) +
                                      " - onState=" + str(self.theDevice.onState) + ", onOffState=" + str(self.theDevice.states['onOffState']) +
                                      " - NEW/CUR brightness=" + str(circadianVals[0]) + "/" + str(self.theDevice.brightness) +
                                      ", ctemp=" + str(circadianVals[1]) + "/" + str(self.theDevice.whiteTemperature))

                    if self.theDevice.onState is False:
                        self.logger.debug("...CIRCAUTO SKIPPING updates for Scene " + self.sceneName + " device running - " + str(
                            self.theDevice.name) + ", onState=False")
                    else:
                        self.logger.debug("...CIRCAUTO GONNA-DO updates for Scene " + self.sceneName + " device running - " + str(
                            self.theDevice.name) + ", onState=True")

                        if self.theDevice.supportsWhiteTemperature:
                            tempDelta = self.theDevice.whiteTemperature - float(circadianVals[1])
                            if abs(tempDelta) > 25:
                                workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                            None,
                                                            True, WorkItemType.CTEMP,
                                                            None, int(circadianVals[1]), 0, 50)
                                self.theQueue.put(workItem)
                            else:
                                self.logger.debug("...CIRCAUTO SKIPPING ctemp set for Scene " + self.sceneName + " device running - " + str(
                                    self.theDevice.name) + ", tempDelta=" + str(tempDelta))

                        brightDelta = self.theDevice.brightness - float(circadianVals[0])
                        if abs(brightDelta) > 2:
                            # next set the brightness
                            workItem = SceneWorkItem(self.sceneName, self.theDevice.name, self.theDevice,
                                                        None,
                                                        True, WorkItemType.BRIGHTNESS,
                                                        None, 0, int(circadianVals[0]), 50)
                            self.theQueue.put(workItem)
                        else:
                            self.logger.debug("...CIRCAUTO SKIPPING brightness set for Scene " + self.sceneName + " device running - " + str(
                                self.theDevice.name) + ", brightnessDelta=" + str(brightDelta) )
                except:  # Do my other non-socket reading stuff here
                    self.logger.debug(
                        "...Scene device exception - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
                    self.logger.debug(
                        "...Unexpected loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

                finally:
                    # take a sleep based on the scene preferences
                    time.sleep(self.sceneSleep)

        except:
            self.logger.debug(
                "...Scene exception hit, process exiting - " + str(self.theDevice.name) + ", thread-id=" + str(self.name))
            self.logger.debug("...Unexpected non-loop error: - " + str(sys.exc_info()) + ", thread-id=" + str(self.name))

        finally:  # Make sure you don't leave any open network connections
            self.stopScene()

    def getCircadian(self):
        self.logger.debug("getCircadian theDevice name: " + self.theDevice.name)
        temperatureVals = self.sceneArray[0]
        brightnessVals = self.sceneArray[1]
        self.logger.debug("getCircadian device tempVals : " + str(temperatureVals))
        self.logger.debug("getCircadian device brightnessVals : " + str(brightnessVals))

        returnVals = [0.0, 0]

        gradientValue = self.getCircadianValue(brightnessVals)
        gradientBrightness = round(gradientValue)
        returnVals[0] = gradientBrightness

        gradientValue = self.getCircadianValue(temperatureVals)
        gradientTemp = round(gradientValue)
        returnVals[1] = gradientTemp

        self.logger.debug("...getCircadian brightness=" + str(gradientBrightness) + ", temperature=" + str(gradientTemp))

        return returnVals

    ########################################
    def getCircadianValue(self, gradientVals=None):
        rightNow = indigo.server.getTime().date()
        sunriseTime = indigo.server.calculateSunrise(rightNow)
        sunsetTime = indigo.server.calculateSunset(rightNow)
        self.logger.debug("getCircadian gradientVals : " + str(gradientVals))
        self.logger.debug("getCircadian sunrise : " + str(sunriseTime) + ", sunset : " + str(sunsetTime))

        sunriseHr = sunriseTime.hour
        if sunriseTime.minute > 30:
            sunriseHr = sunriseHr + 1
        sunsetHr = sunsetTime.hour
        if sunsetTime.minute > 30:
            sunsetHr = sunsetHr + 1
        peakHrs = round(abs(sunsetHr - sunriseHr) * 0.5)
        stopRiseHr = sunriseHr + round(peakHrs * 0.5) + 2
        fastRiseHr = sunriseHr + 1 + round((stopRiseHr - sunriseHr) * 0.75)
        startFallHr = sunsetHr - round(peakHrs * 0.5)
        if round(fastRiseHr) == round(stopRiseHr):
            fastRiseHr = stopRiseHr - 1

        self.logger.debug(
            "getCircadian sunriseHr : " + str(sunriseHr) + ", sunsetHr : " + str(sunsetHr) + ", peakHrs=" + str(
                peakHrs) + ", fastRiseHr=" + str(fastRiseHr) + ", stopRiseHr=" + str(
                stopRiseHr) + ", startFallHr=" + str(startFallHr))

        currentDate = datetime.datetime.now()
        hourOfDay = currentDate.hour
        minOfHour = currentDate.minute
        gradientValue = 0.0
        if gradientVals == None:
            gradientVals = '15,35,80,95,100,80,40'

        self.logger.debug("getCircadian gradientVals : " + str(gradientVals))
        tempArray = gradientVals.split(",")

        lateNightVal = int(tempArray[0])
        sunrisePreVal = int(tempArray[1])
        sunrisePeakVal = int(tempArray[2])
        amFastPeakVal = int(tempArray[3])
        maxVal = int(tempArray[4])
        pmDropVal = int(tempArray[5])
        sunsetFastDropVal = int(tempArray[6])

        if hourOfDay >= 0 and hourOfDay < (sunriseHr - 1):
            gradientValue = lateNightVal
        elif hourOfDay >= (sunriseHr - 1) and hourOfDay < sunriseHr:
            gradientValue = self.getGradientValue((sunriseHr - 1), sunriseHr, lateNightVal, sunrisePreVal, hourOfDay,
                                                  minOfHour)
        elif hourOfDay >= sunriseHr and hourOfDay < (sunriseHr + 1):
            gradientValue = self.getGradientValue(sunriseHr, (sunriseHr + 1), sunrisePreVal, sunrisePeakVal, hourOfDay,
                                                  minOfHour)
        elif hourOfDay >= (sunriseHr + 1) and hourOfDay < fastRiseHr:
            gradientValue = self.getGradientValue((sunriseHr + 1), fastRiseHr, sunrisePeakVal, amFastPeakVal, hourOfDay,
                                                  minOfHour)
        elif hourOfDay >= fastRiseHr and hourOfDay < stopRiseHr:
            gradientValue = self.getGradientValue(fastRiseHr, stopRiseHr, amFastPeakVal, maxVal, hourOfDay, minOfHour)
        elif hourOfDay >= stopRiseHr and hourOfDay < startFallHr:
            gradientValue = maxVal
        elif hourOfDay >= startFallHr and hourOfDay < (sunsetHr - 1):
            gradientValue = self.getGradientValue(startFallHr, (sunsetHr - 1), maxVal, pmDropVal, hourOfDay, minOfHour)
        elif hourOfDay >= (sunsetHr - 1) and hourOfDay < (sunsetHr + 1):
            gradientValue = self.getGradientValue((sunsetHr - 1), (sunsetHr + 1), pmDropVal, sunsetFastDropVal,
                                                  hourOfDay, minOfHour)
        elif hourOfDay >= (sunsetHr + 1) and hourOfDay < 24:
            gradientValue = self.getGradientValue((sunsetHr + 1), 24, sunsetFastDropVal, lateNightVal, hourOfDay,
                                                  minOfHour)

        return gradientValue

    ########################################
    def getGradientValue(self, startHr, stopHr, startVal, stopVal, curHr, curMin):

        gradientVal = startVal;
        self.logger.debug("...getGradientValue startHr=" + str(startHr) + ", stopHr=" + str(stopHr) + ", startVal=" + str(
            startVal) + ", stopVal=" + str(stopVal) + ", curHr=" + str(curHr) + ", curMin=" + str(curMin))

        totalMin = (stopHr - startHr) * 60
        self.logger.debug("...getGradientValue totalMin=" + str(totalMin))

        if curHr >= startHr and curHr < stopHr:
            minFromStart = ((curHr - startHr) * 60) + curMin
            curPercentage = float(minFromStart) / float(totalMin)

            self.logger.debug("...getGradientValue minFromStart=" + str(minFromStart) + ", totalMin=" + str(
                totalMin) + ", percentage of interval=" + str(curPercentage))

            if startVal < stopVal:
                # // gradientVal is rising
                gradientVal = round(startVal + (curPercentage * (stopVal - startVal)))
                self.logger.debug("...getGradientValue rising, new value=" + str(gradientVal))
            else:
                # // gradientVal is falling
                gradientVal = round(startVal - (curPercentage * (startVal - stopVal)))
                self.logger.debug("...getGradientValue falling, new value=" + str(gradientVal))

        return gradientVal


class SceneWorkItem(object):
    def __init__(self, scene_name, group_name, the_device, the_light, is_group_work, work_item_type,
                 rgb_values, color_temp, brightness, transition_millis):
        self.sceneName = scene_name
        self.groupName = group_name
        self.theDevice = the_device
        self.theLight = the_light
        self.isGroupWork = is_group_work
        self.workItemType = work_item_type
        self.rgbValues = rgb_values
        self.colorTemp = color_temp
        self.brightness = brightness
        self.transitionMillis = transition_millis

class WorkItemType(enum.Enum):
    RGB = 1
    CTEMP = 2
    BRIGHTNESS = 3
    ONOFF = 4

class SceneAction(object):
    def __init__(self):
        self.deviceAction = None
        self.actionValue = None
        self.delayAmount = 900
        self.deviceId = None
        self.configured = True
        self.textToSpeak = None

