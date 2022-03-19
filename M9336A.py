from qcodes import (validators as vals)
from qcodes.instrument.base import Instrument
import qcodes as qc
from qcodes.instrument.channel import InstrumentChannel

import sys
import clr
import time
import numpy as np

BIGINT = int(1e18)

# load the driver wrapper (instead of the driver directly)
path_to_driver ='C:\\Program Files\\Keysight\\MAwg\\bin'
sys.path.append(path_to_driver)
clr.AddReference("KtMAwgDriverWrapper")

from KtMAwgWrapper import KtMAwgWrapper

class Keysight_M9336A_Channel(InstrumentChannel):
    """
    Class to hold the two Keysight channels, i.e.
    Channel1, Channel2 and Channel3.
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
        
        super().__init__(parent, name)

        self._channel = channel
        
        if channel not in ['Channel1', 'Channel2', 'Channel3']:
            raise ValueError('channel must be either "Channel1" or "Channel2" or "Channel3"')
        
        self.add_parameter('SampleRate',
                           label = 'AWG Sample Rate',
                           unit = 'Hz',
                           get_cmd=self.get_SampleRate,
                           set_cmd=self.set_SampleRate,
                           vals = vals.Numbers(1,1.28e9))
        
        self.add_parameter('ChannelMode',
                           label = 'Channel Mode (Waveform or Marker)',
                           get_cmd=self.get_ChannelMode,
                           set_cmd=self.set_ChannelMode,
                           vals = vals.Enum('waveform', 'marker'))
        
        self.add_parameter('OperationMode',
                           label='Operation Mode',
                           unit='',
                           get_cmd=self.get_OperationMode,
                           set_cmd=self.set_OperationMode,
                           vals = vals.Enum('continuous','burst'))
                
        self.add_parameter('TerminalConfiguration',
                           label='Terminal Configuration',
                           unit='',
                           get_cmd=self.get_TerminalConfiguration,
                           set_cmd=self.set_TerminalConfiguration,
                           vals = vals.Enum('single-ended', 'differential')) 
        
        self.add_parameter('Gain',
                           label='Gain',
                           unit='',
                           get_cmd=self.get_Gain,
                           set_cmd=self.set_Gain,
                           vals = vals.Numbers())
        
        self.add_parameter('Offset',
                           label='Offset',
                           unit='V',
                           get_cmd=self.get_Offset,
                           set_cmd=self.set_Offset,
                           vals = vals.Numbers())  
        
        self.add_parameter('CommonModeOffset',
                           label='Common Mode Offset',
                           unit='V',
                           get_cmd=self.get_CommonModeOffset,
                           set_cmd=self.set_CommonModeOffset,
                           vals = vals.Numbers(-0.5, 0.5))
        
        self.add_parameter('BurstCount',
                           label = 'Burst Count',
                           get_cmd=self.get_BurstCount,
                           set_cmd=self.set_BurstCount,
                           vals = vals.Ints(1,2**31 -1))
        
    
    def get_SampleRate(self):
        return self._parent.driverw.Arbitrary.GetSampleRate(self._channel)
    
    def set_SampleRate(self,value):
        self._parent.driverw.Arbitrary.SetSampleRate(self._channel, value)
    
    def set_ChannelMode(self,value):
        if value == 'waveform':
            self._parent.driverw.Output.SetChannelMode(self._channel, 0)
        elif value == 'marker':
            self._parent.driverw.Output.SetChannelMode(self._channel, 1)
                
    def get_ChannelMode(self):
        value = self._parent.driverw.Output.GetChannelMode(self._channel)
        if value == 0:
            return 'waveform'
        elif value == 1:
            return 'marker'       
        
    def set_OperationMode(self,value):
        if value == 'continuous':
            self._parent.driverw.SetOperationMode(self._channel, 0)   # Sets the mode that determines how the AWG produces output for the specified channel when that channel is in Output Generation State.
        elif value == 'burst':
            self._parent.driverw.SetOperationMode(self._channel, 1)   # Sets the mode that determines how the AWG produces output for the specified channel when that channel is in Output Generation State.
        
    def get_OperationMode(self):
        value = self._parent.driverw.GetOperationMode(self._channel)
        if value == 0:
            return 'continuous'
        elif value == 1:
            return 'burst'
 
    def get_BurstCount(self):
        return self._parent.driverw.Trigger.Start.GetBurstCount(self._channel)
    
    def set_BurstCount(self,value):
        self._parent.driverw.Trigger.Start.SetBurstCount(self._channel, value)
        
    def set_TerminalConfiguration(self,value):
        if value == 'single-ended':
            self._parent.driverw.Output.SetTerminalConfiguration(self._channel, 0)   # Determines whether the AWG will run in Single-ended Mode or Differential Mode. The Terminal Configuration determines how the gain and offset voltages will be processed.
        elif value == 'differential':
            self._parent.driverw.Output.SetTerminalConfiguration(self._channel, 1)   # Determines whether the AWG will run in Single-ended Mode or Differential Mode. The Terminal Configuration determines how the gain and offset voltages will be processed.
        
    def get_TerminalConfiguration(self):
        value = self._parent.driverw.Output.GetTerminalConfiguration(self._channel)
        if value == 0:
            return 'single-ended'
        elif value == 1:
            return 'differential'
            
    def set_Gain(self,value):
        self._parent.driverw.Arbitrary.SetGain(self._channel, value)   # Sets the Composite Gain of the AWG, which the driver uses to set the Digital Gain and the Analog Gain. This value determines the fullscale output voltage.

    def get_Gain(self):
        return self._parent.driverw.Arbitrary.GetGain(self._channel)   # Gets the Composite Gain of the AWG, which the driver uses to set the Digital Gain and the Analog Gain. This value determines the full scale output voltage. 
    
    def set_Offset(self,value):
        self._parent.driverw.Arbitrary.SetOffset(self._channel, value)   # Sets the offset voltage of the waveform the AWG produces. The units are volts.

    def get_Offset(self):
        return self._parent.driverw.Arbitrary.GetOffset(self._channel)   # Gets the offset voltage of the waveform the AWG produces. The units are volts.

    def set_CommonModeOffset(self,value):
        self._parent.driverw.Arbitrary.SetCommonModeOffset(self._channel, value)   #Sets the common mode offset applied when the terminal configuration is set to differential. This is a DC voltage value and the units are volts.

    def get_CommonModeOffset(self):
        return self._parent.driverw.Arbitrary.GetCommonModeOffset(self._channel)     # Gets the common mode offset voltage applied when the terminal configuration is set to differential. This is a DC voltage value, and the units are volts.
    
    def load_waveform(self, WaveformName, WaveformArray, MarkerArray):
        # Creates a channel-specific waveform segment and returns a handle that identifies the waveform segment. The waveform samples are in a double-precision floating point array. An optional array of marker bytes can be provided.
        self._waveform_handle = self._parent.driverw.Arbitrary.Waveform.CreateChannelWaveform(self._channel, WaveformName, WaveformArray, MarkerArray)
    
    def init_channel(self):    
        self._parent.driverw.Arbitrary.Configure(self._channel, self._waveform_handle[0], self.Gain(), self.Offset(), self.CommonModeOffset())  #Configures the attributes of the AWG that affect sequence generation.
    
    def enable(self):
        self._parent.driverw.Output.SetEnabled(self._channel, True)   # If true, causes the waveform produced by the AWG to appear at the output connector for the specified channel.
    
    def initiate_generation(self):
        print('\nTrying to initiate AWG generation ({}).'.format(self._channel))
        print('If the error "The current pending state has 1 conflicts" occures during generation initiating, try to reduce gain and/or offset values.\n')
        self._parent.driverw.InitiateGeneration(self._channel)    # If the AWG is in the Configuration State, this function moves the AWG to the Output Generation State for the specified channel or channels.        
        print('AWG generation ({}) is initiated\n\n'.format(self._channel))
    
    def configure_markers(self):
        self._parent.driverw.Markers.Item('Ext1_Gate').Configure(self._channel, 16, 'External1') # For the specified marker name and the specified channel, sets the marker bit position and the marker destination.
        print('Destination bit of 16 corresponds to External1')
        
        self._parent.driverw.Markers.Item('Ext2_Acq').Configure(self._channel, 17, 'External2') 
        print('Destination bit of 17 corresponds to External2')
        
        self._parent.driverw.Markers.Item('PXI_TRIG0_Acq_Dig').Configure(self._channel, 18, 'PXI_TRIG0') 
        print('Destination bit of 18 corresponds PXI_TRIG0')            

    def abort_generation(self):
        self._parent.driverw.AbortGeneration(self._channel)      # If the AWG is in the Output Generation State, this method moves the AWG to the Configuration State for the specified channel or channels.

class M9336A(Instrument):
    """ 
    Driver for the AWG of the Keysight M9336A card.
    
    """
    def __init__(self, name, address, **kwargs):
        super().__init__(name, **kwargs)
        
        self.driverw = KtMAwgWrapper()


        self.driverw.Initialize(address, '')
        
        print('*********************')
        print('Zoidberg2 AWG Specs:') 
        print('M9336A-B50 Channel Bandwidth, 540 MHz')
        print('M9336A-001 Enable I/Q channels (all 3 channels)')
        print('M9336A-M02 Memory, 2 GB')
        print('*********************')
        
        # Add new Data Markers to the Markers collection with a name specified by the name parameter
        self.driverw.Markers.Add('Ext1_Gate')
        self.driverw.Markers.Add('Ext2_Acq')
        self.driverw.Markers.Add('PXI_TRIG0_Acq_Dig')
        
        #  Add the channel to the instrument
        for ch_num in range(1, 4):
             ch_name = 'ch{}'.format(ch_num) # 'colloquial' name
             ch = 'Channel{}'.format(ch_num) #  the channel name used by Keysight
             channel =  Keysight_M9336A_Channel(self, ch_name, ch)
             self.add_submodule(ch_name, channel)
       
    
    def generate_MarkersArray(self, marker_gate, marker_acq_ext, marker_acq_int):
        # build temporary arrays for the final binary marker mask
        # bit position = destination bit position - 16
        _marker_gate = (2**0)*np.array(marker_gate)
        _marker_acq_ext = (2**1)*np.array(marker_acq_ext)
        _marker_acq_int = (2**2)*np.array(marker_acq_int)
        return np.sum([_marker_gate,_marker_acq_ext,_marker_acq_int], axis=0)
    
    def initiate_generation(self,string):
        self.driverw.InitiateGeneration(string)
        
    def disconnect(self):
        self.driverw.Close()