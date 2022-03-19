import numpy as np
from time import time, sleep

from qcodes import (Instrument, MultiParameter, validators as vals)
from qcodes.instrument_drivers.Keysight.M9336A import M9336A
from qcodes.instrument_drivers.Keysight.M9203A import M9203A

BIGINT = int(1e18)

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
        self._instrument.dig.start() # Initiates a waveform acquisition. The digitizer waits for a trigger.
        
        # initiate AWG generation
        self._instrument.awg.initiate_generation('Channel1,Channel2')

        # update nacqs, nrcds and npts values
        self.__nacqs = self._instrument.dig.NumberOfAcquisitions()
        self.__nrcds = self._instrument.dig.NumRecordsPerAcquisition()
        self.__npts = self._instrument.dig.RecordSize()
        
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
            NoErrorCheck = self._instrument.dig.WaitUntilAcqComplete() # Indicates if a (single- or multi-record) waveform can be fetched from the instrument.
            if NoErrorCheck == False: 
                break 
            for j in range(self.__nrcds):
                # This function returns the waveform the digitizer acquired for the specified channel in raw ADC units.
                [__OutArray1, __ActualPoints1, __FirstValidPoint1, __InitialXOffset1, __InitialXTimeSeconds1, __InitialXTimeFraction1, __XIncrement1, __ScaleFactor1, __ScaleOffset1] = self._instrument.dig.AgMD2.Channels('Channel1').Measurement.FetchWaveformInt16()
                [__OutArray2, __ActualPoints2, __FirstValidPoint2, __InitialXOffset2, __InitialXTimeSeconds2, __InitialXTimeFraction2, __XIncrement2, __ScaleFactor2, __ScaleOffset2] = self._instrument.dig.AgMD2.Channels('Channel2').Measurement.FetchWaveformInt16()
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
            self._instrument.dig.continue_acquisition() 

        if NoErrorCheck == True:
            # To optimize the memory size, keep only single array of time data for each channel
            Time1 = np.linspace(__InitialXOffset1,__InitialXOffset1+__ActualPoints1*__XIncrement1,__ActualPoints1)
            Time2 = np.linspace(__InitialXOffset2,__InitialXOffset2+__ActualPoints2*__XIncrement2,__ActualPoints2)
            self._instrument.dig.stop() # stop acquisition
            self._instrument.awg.ch1.abort_generation() # abort generation            
            self._instrument.awg.ch2.abort_generation() # abort generation           
         
        
        print('get() of "IQArray_raw" was executed in {0} s'.format(time()-start_time))
        print('')
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
        self._instrument.dig.start()                  # Initiates a waveform acquisition. The digitizer waits for a trigger.
        
        # initiate AWG generation
        self._instrument.awg.initiate_generation('Channel1,Channel2')
                
        # update nacqs, nrcds and npts values
        self.__nacqs = self._instrument.dig.NumberOfAcquisitions()
        self.__nrcds = self._instrument.dig.NumRecordsPerAcquisition()
        self.__npts = self._instrument.dig.RecordSize()
             
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
            OutVoltageArrays1j = np.zeros((self.__npts,))    # initialize a temporary array for averaging
            OutVoltageArrays2j = np.zeros((self.__npts,))    # initialize a temporary array for averaging
            NoErrorCheck = self._instrument.dig.WaitUntilAcqComplete() # Indicates if a (single- or multi-record) waveform can be fetched from the instrument.
            if NoErrorCheck == False: 
                break
            for j in range(self.__nrcds):
                # This function returns the waveform the digitizer acquired for the specified channel in raw ADC units.
                [__OutArray1, __ActualPoints1, __FirstValidPoint1, __InitialXOffset1, __InitialXTimeSeconds1, __InitialXTimeFraction1, __XIncrement1, __ScaleFactor1, __ScaleOffset1] = self._instrument.dig.AgMD2.Channels('Channel1').Measurement.FetchWaveformInt16()
                [__OutArray2, __ActualPoints2, __FirstValidPoint2, __InitialXOffset2, __InitialXTimeSeconds2, __InitialXTimeFraction2, __XIncrement2, __ScaleFactor2, __ScaleOffset2] = self._instrument.dig.AgMD2.Channels('Channel2').Measurement.FetchWaveformInt16()
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
            self._instrument.dig.continue_acquisition() 
            # averaging over acquisitions
            OutVoltageArrays1i = (OutVoltageArrays1i*i + OutVoltageArrays1j)/(i+1)
            OutVoltageArrays2i = (OutVoltageArrays2i*i + OutVoltageArrays2j)/(i+1)

        if NoErrorCheck == True:
            Time1 = np.linspace(__InitialXOffset1,__InitialXOffset1+__ActualPoints1*__XIncrement1,__ActualPoints1)
            Time2 = np.linspace(__InitialXOffset2,__InitialXOffset2+__ActualPoints2*__XIncrement2,__ActualPoints2)
            self._instrument.dig.stop() # stop acquisition
            self._instrument.awg.ch1.abort_generation() # abort generation            
            self._instrument.awg.ch2.abort_generation() # abort generation   
        
        print('get() of "IQArray_averaged" was executed in {0} s'.format(time()-start_time))
        print('If running QCoDes Measure() or Loop() function: Waiting for QCoDes to write the data to a file.')
        return OutVoltageArrays1i, OutVoltageArrays2i, Time1, Time2    

class SingleIQPair_averaged(MultiParameter):
    """
    MultiParameter class for IQ data
    """
    def __init__(self, name, instrument, nacqs, nrcds, npts):
        super().__init__(name,
                         names=('I_data_av','Q_data_av'),
                         shapes=((), ()),
                         labels=('I_out_av', 'Q_out_av'),
                         units=('V', 'V'))                        
        
        # Read instrument parameters
        self._instrument = instrument
        
    
    def get_raw(self):
        self._instrument.dig.start()                  # Initiates a waveform acquisition. The digitizer waits for a trigger.

        # initiate AWG generation
        self._instrument.awg.initiate_generation('Channel1,Channel2')

        # update nacqs, nrcds and npts values
        self.__nacqs = self._instrument.dig.NumberOfAcquisitions()
        self.__nrcds = self._instrument.dig.NumRecordsPerAcquisition()
        self.__npts = self._instrument.dig.RecordSize()
             
        OutVoltage1 = 0
        OutVoltage2 = 0
        
        # fetch data
        #print('Fetching data...')
        #print('Number of Acquisitions: ', self.__nacqs)
        #print('Number of Records Per Acquisition: ', self.__nrcds)
        #print('**Number of Averages (= NumberOfAcquisitions x NumberOfRecordsPerAcquisition): ', self.__nacqs*self.__nrcds,'**')
        start_time = time() # get time stamp
        for i in range(self.__nacqs):
            NoErrorCheck = self._instrument.dig.WaitUntilAcqComplete() # Indicates if a (single- or multi-record) waveform can be fetched from the instrument.
            if NoErrorCheck == False: 
                break
            for j in range(self.__nrcds):
                #print('data taken {0} s'.format(time()-start_time))
                # This function returns the waveform the digitizer acquired for the specified channel in raw ADC units.
                [__OutArray1, __ActualPoints1, __FirstValidPoint1, __InitialXOffset1, __InitialXTimeSeconds1, __InitialXTimeFraction1, __XIncrement1, __ScaleFactor1, __ScaleOffset1] = self._instrument.dig.AgMD2.Channels('Channel1').Measurement.FetchWaveformInt16()
                [__OutArray2, __ActualPoints2, __FirstValidPoint2, __InitialXOffset2, __InitialXTimeSeconds2, __InitialXTimeFraction2, __XIncrement2, __ScaleFactor2, __ScaleOffset2] = self._instrument.dig.AgMD2.Channels('Channel2').Measurement.FetchWaveformInt16()
                #print('data fetched {0} s'.format(time()-start_time))
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
                Voltage1 = __ScaleOffset1 + __ScaleFactor1*np.mean(__OutArray1[__FirstValidPoint1:__FirstValidPoint1+__ActualPoints1])
                Voltage2 = __ScaleOffset2 + __ScaleFactor2*np.mean(__OutArray2[__FirstValidPoint2:__FirstValidPoint2+__ActualPoints2])
                
                #print('data scaled {0} s'.format(time()-start_time))
                
                # averaging
                OutVoltage1 = (OutVoltage1*j + Voltage1)/(j+1)
                OutVoltage2 = (OutVoltage2*j + Voltage2)/(j+1)
                #print('data averaged {0} s'.format(time()-start_time))
            self._instrument.dig.continue_acquisition() 

        if NoErrorCheck == True:
            self._instrument.dig.stop() # stop acquisition
            self._instrument.awg.ch1.abort_generation() # abort generation            
            self._instrument.awg.ch2.abort_generation() # abort generation   
        
        #print('get() of "SingleIQPair_averaged" was executed in {0} s'.format(time()-start_time))
        #print('If running QCoDes Measure() or Loop() function: Waiting for QCoDes to write the data to a file.')
        return OutVoltage1, OutVoltage2   

class Zoidberg2(Instrument):
    """ 
    Driver for the Zoidberg2 using the Keysight M9336A and M9203A card.
    
    """
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        print('Initializing AWG ({0}.awg) and digitizer ({1}.dig) ...'.format(name,name))        
        self.awg = M9336A('awg', 'PXI19::0::0::INSTR')
        self.dig = M9203A('dig', 'PXI20::0::0::INSTR')
        
        # For digitizer acquisition config
        self.__NumRecordsPerAcquisition = self.dig.NumRecordsPerAcquisition()      # Specifies the number of records in the acquisition.
        self.__RecordSize = self.dig.RecordSize()            # Specifies the number of samples in each record.
        self.__NumberOfAcquisitions = self.dig.NumberOfAcquisitions()    # number of acquisitions

        self.__Pi = 180
        self.__Delay1 = 30000

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
   
        self.add_parameter(name='NumberOfAcquisitions',
                           label = 'Number of Acquisitions',
                           unit='',
                           set_cmd = self.set_NumberOfAcquisitions,
                           get_cmd = self.get_NumberOfAcquisitions,
                           vals = vals.Ints(0,BIGINT))
        
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
        
        self.add_parameter(name='SingleIQPair_averaged',
                           nacqs=self.NumberOfAcquisitions(),
                           nrcds=self.NumRecordsPerAcquisition(),
                           npts=self.RecordSize(),
                           parameter_class=SingleIQPair_averaged)
        
        self.add_parameter(name='Pi',
                           label= 'Length of Pi pulse',
                           set_cmd = self.set_Pi,
                           get_cmd = self.get_Pi)
        
        self.add_parameter(name='Delay1',
                           label= 'Delay 1',
                           set_cmd = self.set_Delay1,
                           get_cmd = self.get_Delay1)
    
    def set_Pi(self,value):
        self.__Pi = value
        
    def get_Pi(self):
        return self.__Pi
    
    def set_Delay1(self,value):
        self.__Delay1 = value
        
    def get_Delay1(self):
        return self.__Delay1       
    
    def set_NumberOfAcquisitions(self,value):
        self.__NumberOfAcquisitions = value
        self.dig.NumberOfAcquisitions(value)
        self._update_IQArray_shapes()
        
    def get_NumberOfAcquisitions(self):
        return self.__NumberOfAcquisitions

     
    def set_NumRecordsPerAcquisition(self, value):
        self.__NumRecordsPerAcquisition = value
        self.dig.NumRecordsPerAcquisition(value)
        self._update_IQArray_shapes()
    
    def get_NumRecordsPerAcquisition(self):
        return self.__NumRecordsPerAcquisition
    
    def set_RecordSize(self, value):
        self.dig.RecordSize(value)
        self.__RecordSize = int(value)
        self._update_IQArray_shapes()
        
    
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
        
    def disconnect(self):
        self.awg.disconnect()
        self.awg.close()
        self.dig.disconnect()
        self.dig.close()
        
