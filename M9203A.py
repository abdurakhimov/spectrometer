# Import modules
from time import sleep, time
import numpy as np

import comtypes.client # driver for IVI-COM

BIGINT = int(1e18)

from qcodes import (Instrument, MultiParameter, ManualParameter, validators as vals)
from qcodes.instrument.channel import InstrumentChannel

class IQArray_raw(MultiParameter):
    """
    MultiParameter class for IQ data
    Parameters:
        nacqs - number of acquisitions
        nrcds - number of records per one acquisition
        npts - number of points
    """
    def __init__(self, name, instrument, nacqs, nrcds, npts):
        super().__init__(name,
                         names=('I_data','Q_data','I_time','Q_time'),
                         shapes=((), (), (), ()),
                         labels=('I_out', 'Q_out','I_time', 'Q_time'),
                         units=('V', 'V','s','s'))                        
        
        # Read instrument parameters
        self._instrument = instrument
        
        # Set shapes
        self.update_shapes(nacqs, nrcds, npts)
        
        self.setpoint_names = (('I_raw_nrcds','I_raw_npts'), ('Q_raw_nrcds','Q_raw_npts'), ('TimeI_raw_npts',), ('TimeQ_raw_npts',))

    def update_shapes(self,nacqs, nrcds, npts):
        self.shapes = ((nacqs*nrcds,npts), (nacqs*nrcds,npts),(npts,),(npts,))
 

        
    def get_raw(self):
        self._instrument.start()                  # Initiates a waveform acquisition. The digitizer waits for a trigger.
       
        # update nacqs, nrcds and npts values
        self.__nacqs = self._instrument.NumberOfAcquisitions()
        self.__nrcds = self._instrument.NumRecordsPerAcquisition()
        self.__npts = self._instrument.RecordSize()
        
        # define output data arrays
        OutVoltageArrays1 = np.zeros((self.__nacqs*self.__nrcds,self.__npts))
        OutVoltageArrays2 = np.zeros((self.__nacqs*self.__nrcds,self.__npts))
        Time1 = np.zeros((1,self.__npts))
        Time2 = np.zeros((1,self.__npts))
        
        # fetch data
        print('Fetching data...')
        print('Number of Acquisitions: ',self.__nacqs)
        print('Number of Records Per Acquisition: ',self.__nrcds)
        start_time = time() # get time stamp
        for i in range(self.__nacqs):
            NoErrorCheck = self._instrument.WaitUntilAcqComplete() # Indicates if a (single- or multi-record) waveform can be fetched from the instrument.
            if NoErrorCheck == False: 
                break 
            for j in range(self.__nrcds):
                # This function returns the waveform the digitizer acquired for the specified channel in raw ADC units.
                [__OutArray1, __ActualPoints1, __FirstValidPoint1, __InitialXOffset1, __InitialXTimeSeconds1, __InitialXTimeFraction1, __XIncrement1, __ScaleFactor1, __ScaleOffset1] = self._instrument.AgMD2.Channels('Channel1').Measurement.FetchWaveformInt16()
                [__OutArray2, __ActualPoints2, __FirstValidPoint2, __InitialXOffset2, __InitialXTimeSeconds2, __InitialXTimeFraction2, __XIncrement2, __ScaleFactor2, __ScaleOffset2] = self._instrument.AgMD2.Channels('Channel2').Measurement.FetchWaveformInt16()
                ##############################
                # Outputs:
                # OutArray:  Buffer into which the acquired waveform is stored.
                # ActualPoints: Indicates how many data points were actually retrieved from the instrument.
                # FirstValidPoint: Indicates the index of the first valid data point in the output data array.
                # InitialXOffset: The time in relation to the Trigger Event of the first point in the waveform in seconds. Negative values mean that the first point in the waveform array was acquired before the trigger event.
                # InitialXTimeSeconds: Specifies the seconds portion of the absolute time at which the first data point was acquired. Note that the actual time is the sum of InitialXTimeSeconds and InitialXTimeFraction.
                # InitialXTimeFraction: Specifies the fractional portion of the absolute time at which the first data point was acquired. Note that the actual time is the sum of InitialXTimeSeconds and InitialXTimeFraction.
                # XIncrement: The time between points in the acquired waveform in seconds.
                # ScaleFactor: Scaling factor for the waveform data.
                # ScaleOffset: Scaling offset for the waveform data.
                VoltageArray1 = __ScaleOffset1 + np.multiply(__OutArray1[__FirstValidPoint1:__FirstValidPoint1+__ActualPoints1],__ScaleFactor1)
                VoltageArray2 = __ScaleOffset2 + np.multiply(__OutArray2[__FirstValidPoint2:__FirstValidPoint2+__ActualPoints2],__ScaleFactor2)
                OutVoltageArrays1[i*self.__nrcds+j,:] = VoltageArray1
                OutVoltageArrays2[i*self.__nrcds+j,:] = VoltageArray2
            self._instrument.continue_acquisition() 

        if NoErrorCheck == True:
            # To optimize the memory size, keep only single array of time data for each channel
            Time1 = np.linspace(__InitialXOffset1,__InitialXOffset1+__ActualPoints1*__XIncrement1,__ActualPoints1)
            Time2 = np.linspace(__InitialXOffset2,__InitialXOffset2+__ActualPoints2*__XIncrement2,__ActualPoints2)
            self._instrument.stop() # stop acquisition            
         
        
        print('get() of "IQArray_raw" was executed in {0} s'.format(time()-start_time))
        print('If running QCoDes Measure() or Loop() function: Waiting for QCoDes to write the data to a file.')
        return OutVoltageArrays1, OutVoltageArrays2, Time1, Time2

class IQArray_averaged(MultiParameter):
    """
    MultiParameter class for IQ data
    """
    def __init__(self, name, instrument, nacqs, nrcds, npts):
        super().__init__(name,
                         names=('I_data_av','Q_data_av','I_time','Q_time'),
                         shapes=((), (), (), ()),
                         labels=('I_out_av', 'Q_out_av','I_time', 'Q_time'),
                         units=('V', 'V','s','s'))                        
        
        # Read instrument parameters
        self._instrument = instrument
        
        self.setpoint_labels = (('npts',), ('npts',), ('npts',), ('npts',))
        self.setpoint_names = (('I_npts',), ('Q_npts',), ('TimeI_npts',), ('TimeQ_npts',))
        
        # Set shapes
        self.update_shapes(nacqs,nrcds,npts)

    def update_shapes(self,nacqs,nrcds,npts):
        self.shapes = ((npts,), (npts,),(npts,),(npts,))
 

        
    def get_raw(self):
        self._instrument.start()                  # Initiates a waveform acquisition. The digitizer waits for a trigger.
        
        # update nacqs, nrcds and npts values
        self.__nacqs = self._instrument.NumberOfAcquisitions()
        self.__nrcds = self._instrument.NumRecordsPerAcquisition()
        self.__npts = self._instrument.RecordSize()
        
        # fetch data
        print('Fetching data...')
        print('Number of Acquisitions: ', self.__nacqs)
        print('Number of Records Per Acquisition: ', self.__nrcds)
        print('**Number of Averages (= NumberOfAcquisitions x NumberOfRecordsPerAcquisition): ', self.__nacqs*self.__nrcds,'**')
        
        start_time = time() # get time stamp
        
        # define output data arrays
        OutVoltageArrays1i = np.zeros((self.__npts,))
        OutVoltageArrays2i = np.zeros((self.__npts,))
        Time1 = np.zeros((self.__npts,))
        Time2 = np.zeros((self.__npts,))
        
        for i in range(self.__nacqs):
            NoErrorCheck = self._instrument.WaitUntilAcqComplete() # Indicates if a (single- or multi-record) waveform can be fetched from the instrument.
            if NoErrorCheck == False: 
                break
            for j in range(self.__nrcds):
                OutVoltageArrays1j = np.zeros((self.__npts,))    # initialize a temporary array for averaging
                OutVoltageArrays2j = np.zeros((self.__npts,))    # initialize a temporary array for averaging
                # This function returns the waveform the digitizer acquired for the specified channel in raw ADC units.
                [__OutArray1, __ActualPoints1, __FirstValidPoint1, __InitialXOffset1, __InitialXTimeSeconds1, __InitialXTimeFraction1, __XIncrement1, __ScaleFactor1, __ScaleOffset1] = self._instrument.AgMD2.Channels('Channel1').Measurement.FetchWaveformInt16()
                [__OutArray2, __ActualPoints2, __FirstValidPoint2, __InitialXOffset2, __InitialXTimeSeconds2, __InitialXTimeFraction2, __XIncrement2, __ScaleFactor2, __ScaleOffset2] = self._instrument.AgMD2.Channels('Channel2').Measurement.FetchWaveformInt16()
                ##############################
                # Outputs:
                # OutArray:  Buffer into which the acquired waveform is stored.
                # ActualPoints: Indicates how many data points were actually retrieved from the instrument.
                # FirstValidPoint: Indicates the index of the first valid data point in the output data array.
                # InitialXOffset: The time in relation to the Trigger Event of the first point in the waveform in seconds. Negative values mean that the first point in the waveform array was acquired before the trigger event.
                # InitialXTimeSeconds: Specifies the seconds portion of the absolute time at which the first data point was acquired. Note that the actual time is the sum of InitialXTimeSeconds and InitialXTimeFraction.
                # InitialXTimeFraction: Specifies the fractional portion of the absolute time at which the first data point was acquired. Note that the actual time is the sum of InitialXTimeSeconds and InitialXTimeFraction.
                # XIncrement: The time between points in the acquired waveform in seconds.
                # ScaleFactor: Scaling factor for the waveform data.
                # ScaleOffset: Scaling offset for the waveform data.
                VoltageArray1 = __ScaleOffset1 + np.multiply(__OutArray1[__FirstValidPoint1:__FirstValidPoint1+__ActualPoints1],__ScaleFactor1)
                VoltageArray2 = __ScaleOffset2 + np.multiply(__OutArray2[__FirstValidPoint2:__FirstValidPoint2+__ActualPoints2],__ScaleFactor2)
                
                # averaging over records
                OutVoltageArrays1j = (OutVoltageArrays1j*j + VoltageArray1)/(j+1)
                OutVoltageArrays2j = (OutVoltageArrays2j*j + VoltageArray2)/(j+1)
            self._instrument.continue_acquisition() 
            # averaging over acquisitions
            OutVoltageArrays1i = (OutVoltageArrays1i*i + OutVoltageArrays1j)/(i+1)
            OutVoltageArrays2i = (OutVoltageArrays2i*i + OutVoltageArrays2j)/(i+1)
            
        if NoErrorCheck == True:
            Time1 = np.linspace(__InitialXOffset1,__InitialXOffset1+__ActualPoints1*__XIncrement1,__ActualPoints1)
            Time2 = np.linspace(__InitialXOffset2,__InitialXOffset2+__ActualPoints2*__XIncrement2,__ActualPoints2)
            self._instrument.stop() # stop acquisition
        
        print('get() of "IQArray_averaged" was executed in {0} s'.format(time()-start_time))
        print('If running QCoDes Measure() or Loop() function: Waiting for QCoDes to write the data to a file.')
        return OutVoltageArrays1i, OutVoltageArrays2i, Time1, Time2    
    
class Keysight_M9203A_Channel(InstrumentChannel):
    """
    Class to hold the two Keysight channels, i.e.
    Channel1 and Channel2.
    """

    def __init__(self, parent: Instrument, name: str, channel: str) -> None:
        """
        Args:
            parent: The Instrument instance to which the channel is
                to be attached.
            name: The 'colloquial' name of the channel
            channel: The name used by the Keysight, i.e. either
                'Channel1' or 'Channel2'
        """

        if channel not in ['Channel1', 'Channel2']:
            raise ValueError('channel must be either "Channel1" or "Channel2"')

        super().__init__(parent, name)


        self.add_parameter('offset',
                           get_cmd=self.get_offset,
                           set_cmd=self.set_offset,
                           label='Offset Voltage',
                           unit='V')
    
        self.add_parameter('range',
                           get_cmd=self.get_range,
                           set_cmd=self.set_range,                                                              
                           label='Range',
                           unit='V')
        
        self._channel = channel
        
    def get_offset(self):
        return self._parent.AgMD2.Channels(self._channel).Offset
    
    def set_offset(self,value):
        self._parent.AgMD2.Channels(self._channel).Offset = value
    
    def get_range(self):
        return self._parent.AgMD2.Channels(self._channel).Range
    
    def set_range(self,value):
        self._parent.AgMD2.Channels(self._channel).Range = value
        

        
class M9203A(Instrument):
    """
    QCoDeS driver for Keysight M9203A 2-channel digitizer.
    This driver was written for use with the custom-made spectrometer in the Quantum Spin Dynamics group at UCL
    """
    def __init__(self, name, address, **kwargs):
        # supplying the terminator means you don't need to remove it from every response
        super().__init__(name, **kwargs)
      
        # Create instance of Keysight AgMD2 class
        self.AgMD2 = comtypes.client.CreateObject("AgMD2.AgMD2")
        
        initOptions = "Simulate=False"
        IdQuery = False        # If this is enabled, the driver will query the instrument model and compare it with a list of instrument models that is supported by the driver.
        Reset = False          # If this is enabled, the driver will perform a reset of the instrument.
        self.AgMD2.Initialize(address,IdQuery,Reset,initOptions)
        
        print('*********************')
        print('Zoidberg2 Digitizer Specs:') 
        print('M9203A-LX2 Digital Processing Unit FPGA LX195T')
        print('M9203A-F05 Bandwidth, 650 MHz maximum')
        print('M9203A-DGT Digitizer Firmware')
        print('M9203A-M02 Memory, 256MB, 64M Samples / ch')
        print('M9203A-SR2 Maximum Sampling Rate, 1.6 GS/s per channel')
        print('M9203A-CH2 Two Channels')
        print('*********************')

        #  Add the channel to the instrument
        for ch_num in range(1, 3):
             ch_name = 'ch{}'.format(ch_num) # 'colloquial' name
             ch = 'Channel{}'.format(ch_num) #  the channel name used by Keysight
             channel =  Keysight_M9203A_Channel(self, ch_name, ch)
             self.add_submodule(ch_name, channel)
        
        # For acquisition config
        self.__NumRecordsPerAcquisition = 1      # Specifies the number of records in the acquisition.
        self.__RecordSize = 1024            # Specifies the number of samples in each record.
        self.__SampleRate = 1.6e9/16        # Specifies the sample rate in samples per second. Should be 1.6e9/(2**n) (where n is arbitrary integer?)
        self.__timeout = 1.0                # digitizer timeout in seconds
        
        self.__NumberOfAcquisitions = 1     # number of acquisitions
        self.__NumberOfAverages = self.__NumberOfAcquisitions*self.__NumRecordsPerAcquisition # number of averages

        self.__AcquisitionMode = 'standard' # choose acquisition mode: standard or TSR
        
        self.add_parameter(name='AcquisitionMode',
                           label= 'Standard or TSR',
                           set_cmd = self.set_AcquisitionMode,
                           get_cmd = self.get_AcquisitionMode,
                           vals = vals.Enum('standard','TSR'))
        
        self.add_parameter(name='NumberOfAcquisitions',
                           label = 'Number of Acquisitions',
                           unit='',
                           set_cmd = self.set_NumberOfAcquisitions,
                           get_cmd = self.get_NumberOfAcquisitions,
                           vals = vals.Ints(0,BIGINT))

        self.add_parameter(name='NumberOfAverages',
                           label = 'Number of Averages',
                           unit ='',
                           set_cmd='',
                           get_cmd=self.get_NumberOfAverages,
                           vals = vals.Ints(0,BIGINT))
        
        self.add_parameter(name='TimeOut',
                           label='Digitizer TimeOut',
                           unit='s',
                           set_cmd=self.set_timeout,
                           get_cmd=self.get_timeout,
                           vals = vals.Numbers(0,float('inf')))

        self.add_parameter(name = 'TriggerLevel', 
                           label = 'Digitizer Trigger Level',
                           unit = 'V',
                           set_cmd = self.set_trigger_level,
                           get_cmd = self.get_trigger_level,
                           vals=vals.Numbers(-5.0,+5.0))
        
        self.add_parameter(name = 'TriggerType', 
                           label = 'Digitizer Trigger Type',
                           unit = '',
                           set_cmd = self.set_trigger_type,
                           get_cmd = self.get_trigger_type,
                           vals = vals.Strings())
        
        self.add_parameter(name = 'NumRecordsPerAcquisition',   # Specifies the number of records in the acquisition.
                          label = 'Number of Records',
                          unit = '',
                          set_cmd = self.set_NumRecordsPerAcquisition,
                          get_cmd = self.get_NumRecordsPerAcquisition,
                          vals = vals.Ints())
        
        self.add_parameter(name = 'RecordSize',           # Specifies the number of samples in each record.
                          label = 'Number of Samples',
                          unit = 'pts',
                          set_cmd = self.set_RecordSize,
                          get_cmd = self.get_RecordSize)
        
        # Specifies the sample rate in samples per second. Should be 1.6e9/(2**n) (where n is 0,..,5 for multi-record TSR acquisition)
        self.add_parameter(name = 'SampleRate',
                          label = 'Digitizer Sample Rate',
                          unit = 'Hz',
                          set_cmd = self.set_SampleRate,
                          get_cmd = self.get_SampleRate,
                          vals = vals.Enum(*np.sort(np.divide(1.6e9,np.power(2,range(6))))))   
        
        self.add_parameter(name='IQ_data_raw',
                           nacqs=self.NumberOfAcquisitions(),
                           nrcds=self.NumRecordsPerAcquisition(),
                           npts=self.RecordSize(),
                           parameter_class=IQArray_raw)
        
        self.add_parameter(name='IQ_data_averaged',
                           nacqs=self.NumberOfAcquisitions(),
                           nrcds=self.NumRecordsPerAcquisition(),
                           npts=self.RecordSize(),
                           parameter_class=IQArray_averaged)

    def set_AcquisitionMode(self,value):
        self.__AcquisitionMode = value
    
    def get_AcquisitionMode(self):
        return self.__AcquisitionMode

    def set_NumberOfAcquisitions(self,value):
        self.__NumberOfAcquisitions = value
        self.__NumberOfAverages = self.__NumberOfAcquisitions*self.__NumRecordsPerAcquisition
        self._update_IQArray_shapes()
        
    def get_NumberOfAcquisitions(self):
        return self.__NumberOfAcquisitions

    def get_NumberOfAverages(self):
        return self.__NumberOfAverages
    
    def set_timeout(self,value):
        self.__timeout = value
    
    def get_timeout(self):
        return self.__timeout
        
    def set_trigger_type(self,value):
        self.AgMD2.Trigger.ActiveSource = value # Specifies the source the digitizer monitors for the trigger event.        
        
    def get_trigger_type(self):
        return self.AgMD2.Trigger.ActiveSource # Specifies the source the digitizer monitors for the trigger event.
       
    def set_trigger_level(self,value):
        TriggerType = self.TriggerType()
        self.AgMD2.Trigger.Sources[TriggerType].Level = value # Specifies the voltage threshold for the trigger sub-system
        
    def get_trigger_level(self):
        TriggerType = self.TriggerType()
        return self.AgMD2.Trigger.Sources[TriggerType].Level # Specifies the voltage threshold for the trigger sub-system

    def set_NumRecordsPerAcquisition(self, value):
        self.AgMD2.Acquisition3.ConfigureAcquisition(value, self.__RecordSize, self.__SampleRate) # This function configures the most commonly configured attributes of the digitizer acquisition sub-system
        self.__NumRecordsPerAcquisition = value
        self.__NumberOfAverages = self.__NumberOfAcquisitions*self.__NumRecordsPerAcquisition
        self._update_IQArray_shapes()
    
    def get_NumRecordsPerAcquisition(self):
        return self.__NumRecordsPerAcquisition
    
    def set_RecordSize(self, value):
       self.AgMD2.Acquisition3.ConfigureAcquisition(self.__NumRecordsPerAcquisition, int(value), self.__SampleRate) # This function configures the most commonly configured attributes of the digitizer acquisition sub-system
       self.__RecordSize = int(value)
       self._update_IQArray_shapes()
       print('Record Size is set to ', self.__RecordSize)
    
    def _update_IQArray_shapes(self):
        """ updates nrcds and npts of the IQArray_raw parameter"""
        nacqs = self.NumberOfAcquisitions()
        nrcds = self.NumRecordsPerAcquisition()
        npts = self.RecordSize()
        for _, parameter in self.parameters.items():
            if isinstance(parameter, (IQArray_raw,IQArray_averaged)):
                try:
                    parameter.update_shapes(nacqs,nrcds,npts)
                except AttributeError:
                    pass
                
    def get_RecordSize(self):
        return self.__RecordSize
    
    def set_SampleRate(self, value):
        self.AgMD2.Acquisition3.ConfigureAcquisition(self.__NumRecordsPerAcquisition, self.__RecordSize, value) # This function configures the most commonly configured attributes of the digitizer acquisition sub-system
        self.__SampleRate = value 
        print('Sample Rate is set to {0:e} Hz'.format(self.__SampleRate))
    
    def get_SampleRate(self):
        return self.__SampleRate
    
    def SelfCalibrate(self):
        self.AgMD2.Calibration.SelfCalibrate()   # Executes all internal calibrations.
    
    def start(self):
        if self.AcquisitionMode() == 'TSR':           
            self.AgMD2.Acquisition3.TSR.Enabled = 1    # Specifies whether TSR operation is enabled on the instrument.
            if self.__NumRecordsPerAcquisition > (2**20/self.__RecordSize):
                print('WARNING: NumRecordsPerAcquisition is not optimal. For optimal performance, use NumRecordsPerAcquisition <= 1 MB/RecordSize')
                  
        self.AgMD2.Acquisition3.Initiate()         # Initiates a waveform acquisition. The digitizer waits for a trigger.    
        
                
            
    def WaitUntilAcqComplete(self):
        result = True
        if self.AcquisitionMode() == 'TSR':  
            start_time = time()
            while True:
                if self.AgMD2.Acquisition3.TSR.IsAcquisitionComplete == 1: # Read Only - Indicates if a (single- or multi-record) waveform can be fetched from the instrument. Applicable only when TSR operation is enabled.
                    result=True
                    break
                if (time()-start_time) > self.__timeout:
                    print('ERROR: Digitizer timeout occured. Acquisition stopped.')
                    print('SOLUTION: Check the digitizer is triggered')
                    self.stop()
                    result=False
                    break
                if self.AgMD2.Acquisition3.TSR.MemoryOverflowOccurred == 1: # Indicates that no memory segment was available to acquire new data. The instrument could therefore not accept any new triggers, and some may have been missed.
                    print('ERROR: Memory overflow occured. Acquisition stopped.')
                    print('SOLUTION: Reduce RecordSize and/or NumberOfRecordsPerAcquisition')
                    self.stop()
                    result=False
                    break
        else:
            self.AgMD2.Acquisition.WaitForAcquisitionComplete(1000*self.__timeout)  # timeout is in ms 
        return result
        
    def continue_acquisition(self):
        if self.AcquisitionMode() == 'TSR': 
            self.AgMD2.Acquisition3.TSR.Continue() # Marks the acquired (single- or multi-record) waveform currently available for fetching as no longer needed (e.g. once it has been read). This allows the corresponding memory segment(s) to be released and made available for new acquisitions.
    
    def stop(self):
        if self.AcquisitionMode() == 'TSR': 
            self.AgMD2.Acquisition3.abort()    # Aborts an acquisition and returns the digitizer to the Idle state.
        
    def disconnect(self):
        self.AgMD2.close()
        self.close()
