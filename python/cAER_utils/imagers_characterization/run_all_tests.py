# ############################################################
# python class that runs experiments and save data
# author  Federico Corradi - federico.corradi@inilabs.com
# ############################################################
from __future__ import division
import numpy as np
import matplotlib
from pylab import *
import time, os

# import caer communication and control gpib/usb instrumentations
import caer_communication
import gpio_usb
import aedat3_process

# TEST SELECTION
do_ptc_dark = False
do_ptc = False
do_fpn = False
do_latency_pixel = True
current_date = time.strftime("%d_%m_%y-%H_%M_%S")
datadir = 'measurements'

# 0 - INIT control tools
# init control class and open communication
control = caer_communication.caer_communication(host='localhost')
gpio_cnt = gpio_usb.gpio_usb()
print gpio_cnt.query(gpio_cnt.fun_gen,"*IDN?")
try:
    os.stat(datadir)
except:
    os.mkdir(datadir) 

################################################################################
## CONDITION 1 - Homegeneous light source
## Homegeneous light source (integrating sphere, need to measure the luminosity)
## also use the hp33120 to generate sine wave at .1 Hz for FPN measurements
#################################################################################

# 1 - Photon Transfer Curve - data
# setup is in conditions -> Homegeneous light source (integrating sphere, need to measure the luminosity)
if do_ptc_dark:
    print "we are doing dark current, please remove all lights.\n"
    raw_input("Press Enter to continue...")
    control.open_communication_command()
    control.load_biases()    
    folder = datadir + '/ptc_dark_' +  current_date
    control.get_data_ptc( folder = folder, recording_time=3, exposures=np.linspace(500,50000,6))
    control.close_communication_command()    
    print "Data saved in " +  folder

if do_ptc:
    print "\n"
    print "we are doing ptc measurements, please put homogeneous light source (integrating sphere)."
    raw_input("Press Enter to continue...")
    control.open_communication_command()
    control.load_biases()    
    folder = datadir + '/ptc_' +  current_date
    control.get_data_ptc( folder = folder, recording_time=3, exposures=np.linspace(50,65000,20))
    control.close_communication_command()    
    print "Data saved in " +  folder

# 2 - Fixed Pattern Noise - data
# setup is in conditions -> Homegeneous light source (integrating sphere, need to measure the luminosity)
# + we slowly generate a sine wave 
if do_fpn:
    control.open_communication_command()
    control.load_biases()    
    folder = datadir + '/fpn_' +  current_date
    print "we are doing fpn measurements, please put homogeneous light source (integrating sphere)."
    gpio_cnt.set_inst(gpio_cnt.fun_gen,"APPL:SIN 0.3, 10, 0") #10 Vpp sine wave at 0.1 Hz with a 0 volt offset - 48-51lux
    raw_input("Press Enter to continue...")
    control.get_data_fpn(folder = folder, recording_time=20)
    control.close_communication_command()    

if do_latency_pixel:
    print "\n"
    print "we are doing latency measurements, please put homogeneous light source (integrating sphere), and connect led board. Connect the synch cable from the output of the function generator to the synch input on the DVS board."
    raw_input("Press Enter to continue...")
    control.open_communication_command()
    control.load_biases(xml_file="cameras/davis240c.xml")    
    folder = datadir + '/latency_' +  current_date
    num_freqs = 1 
    start_freq = 200 
    stop_freq = 200 
    recording_time = (1.0/start_freq)*8.0 
    #for this_coarse in range(len(sweep_coarse_value)):
    #    for this_fine in range(len(sweep_fine_value)):
    #fit led irradiance
    #A = np.loadtxt("measurements/setup/red_led_irradiance.txt")
    #slope, inter = np.polyfit(A[0],A[1],1)
    #volts = np.array([ 1.5,  2.5,  3. ,  3.5,  4. ,  4.5,  5. ,  5.5]) #led 25 cm away RED with red filter 360 nm
    slope = 0.03664584777
    inter = 2.0118686
    A = np.array([   0. ,    8.7,   21.4,   35.4,   50.4,   66.8,   83.1,  100. ])
    base_level = A

    num_measurements = len(A) 
    base_level_v = 3.1
    #base_level = [base_level_v+step_level*i for i in range(num_measurements)]
    contrast_level = 0.30
    freq_square = 200
    for i in range(num_measurements):
        perc_low = base_level[i]-base_level[i]*contrast_level
        perc_hi = base_level[i]+base_level[i]*contrast_level
        v_hi = perc_hi * slope + inter   
        v_low= perc_low * slope + inter
        print("hi :", str(v_hi))
        print("low :", str(v_low))
        string = "APPL:SQUARE "+str(freq_square)+", "+str(v_hi)+", "+str(v_low)+""
        gpio_cnt.set_inst(gpio_cnt.fun_gen,string) #10 Vpp sine wave at 0.1 Hz with a 0 volt
        control.load_biases(xml_file="cameras/davis240c.xml")  
        time.sleep(3)
        control.get_data_latency( folder = folder, recording_time = recording_time, num_measurement = i)
    control.close_communication_command()    
    print "Data saved in " +  folder
