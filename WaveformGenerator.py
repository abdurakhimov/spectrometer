# Import numpy
import numpy as np  

class WaveformGenerator:
    """
    Class containing all functions required to create pulsed and sine waveforms
    """
    def sine(amplitude, frequency, number_of_points, dc_offset, sample_rate):
        data = np.zeros(number_of_points) # define data array
        time = np.linspace(0,(number_of_points-1)/sample_rate,number_of_points) # time array
        data = dc_offset + amplitude*np.sin(2*np.pi*frequency*time)
        return data
    
    def pulse(amplitude, duration, sample_rate):    
        data = amplitude * np.ones(int(round(duration*sample_rate))) 
        return data

    def delay(duration, sample_rate): 
        data = np.zeros(int(round(duration*sample_rate))) 
        return data

    def combine(*args):
        data = [] # define data array
        for arg in args:
            data = np.append(data, arg)
        return data
    
    def time(data, SR):
        return np.linspace(0, (len(data)-1)/SR, len(data))
        
    def save_waveform(filename, data):
        np.savetxt(filename, data)
        print('Saved waveform data to file ',filename)
    
    def load_waveform(filename):
        data = [] # define data array
        data = np.loadtxt(filename)
        return data
    
    def length_correction(waveform, marker1, marker2):
        data1 = np.append(waveform,np.zeros(max(len(waveform),len(marker1),len(marker2))-len(waveform)))
        data2 = np.append(marker1,np.zeros(max(len(waveform),len(marker1),len(marker2))-len(marker1)))
        data3 = np.append(marker2,np.zeros(max(len(waveform),len(marker1),len(marker2))-len(marker2)))
        return data1, data2, data3

    
    
        
        
        