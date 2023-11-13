import pyvisa as visa
import numpy as np
import time
import matplotlib.pyplot as plt

# Standard visa stuff. Instruments will "probably" not appear on rm.list_resources()
# Port numbers (51234, for example) are defined in the setup script. Anything above 1000 is safe.
rm = visa.ResourceManager()
osc_str = "TCPIP0::127.0.0.1::51234::SOCKET"
sg_str = "TCPIP0::127.0.0.1::51235::SOCKET"
rc_str = "TCPIP0::127.0.0.1::51236::SOCKET"

# Define devices and open communications. All terminations should be \n
osc = rm.open_resource(osc_str)
osc.read_termination = "\n"
print(osc.query("*IDN?"))

sg = rm.open_resource(sg_str)
sg.read_termination = "\n"
print(sg.query("*IDN?"))

rc = rm.open_resource(rc_str)
rc.read_termination = "\n"
print(rc.query("*IDN?"))

# We'll set the rc output to the capacitor, change the capacitance to a certain value, and get the value of the resistance
rc_out0 = rc.query("out?")
if rc_out0 == "r" or rc_out0 == "R":
    rc.write("out C")

cap = 2.5
rc.write(f"c {cap}")
res = float(rc.query("r?"))

# Calculate exact time constant and cutoff frequency
tau = cap*1e-6*res
fc = 1/(2*np.pi*tau)
print(f"Exact RC: {1000*tau:.3f} ms.")
print(f"Exact cutoff freq.: {fc:.3f} Hz")

# Set signal generator properties
freq0 = 700.0
sg.write(f"freq:freq {freq0}")
time.sleep(0.1)
sg.write("amp:amp 10.0")
time.sleep(0.1)
sg.write("out 1")
time.sleep(0.1)
sg.write("amp:offs 0.0")
time.sleep(0.1)
sg.write("wave:wave sine")
time.sleep(0.1)
sg.write("wave:dc 0")
time.sleep(0.1)
sg.write("wave:phas 0.0")


# Adjust oscilloscope and start getting data
osc.write("run")  # This causes error, use graphical interface for now
osc.write("trig:auto")
time.sleep(0.1)
osc.write("horiz:scale 0.0005")
time.sleep(0.1)
osc.write("c1:scale 2")
time.sleep(0.1)
osc.write("c2:enable on")
time.sleep(0.1)
osc.write("c2:scale 2")
time.sleep(1.0)


# Get data
data_x_str = osc.query("horiz:data?")
data_c1_str = osc.query("c1:data?")
data_c2_str = osc.query("c2:data?")

data_x_split = data_x_str.split(",")
data_c1_split = data_c1_str.split(",")
data_c2_split = data_c2_str.split(",")

data_x = []
data_c1 = []
data_c2 = []

for i in range(len(data_x_split)):
    data_x.append(float(data_x_split[i]))
    data_c1.append(float(data_c1_split[i]))
    data_c2.append(float(data_c2_split[i]))

# Plot captured data. Script will pause here, until plot window is closed
plt.plot(data_x, data_c1)
plt.plot(data_x, data_c2)
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.show()


# Sweep frequency
freqs = np.logspace(1, 4, 100)  # 10 Hz to 10 KHz

# Go to initial condition (not always necessary, but can help)
sg.write(f"freq:freq {freqs[0]}")
time.sleep(0.1)
osc.write(f"horiz:scale {0.05}")
time.sleep(0.5)

amps = []
n_periods = 4  # Periods to be displayed
n_divs = 10  # Fixed, usually 8 or 10 in real oscs
for freq in freqs:
    sg.write(f"freq:freq {freq}")
    time.sleep(0.1)
    
    period = 1/freq
    total_time = period*n_periods
    osc_scale = total_time/n_divs
    
    osc.write(f"horiz:scale {osc_scale}")
    time.sleep(0.5)  # Wait a little more to get data
    
    data_c2_str = osc.query("c2:data?")
    data_c2_split = data_c2_str.split(",")
    data_c2 = []
    for i in range(len(data_x_split)):
        data_c2.append(float(data_c2_split[i]))
    amps.append(np.ptp(data_c2[int(len(data_c2)/2):]))  # Only last half to avoid deformation at start

# DB scale, max is 0
dbv = 20*np.log10(np.array(amps))
dbv = dbv - dbv.max()

plt.semilogx(freqs, dbv)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Peak-Peak (dB)")
plt.show()

# Calculate cut-off frequency finding the closest measurement point
cutoff_idx = np.abs(dbv - (-3)).argmin()  # Closest to -3
cutoff_freq = freqs[cutoff_idx]
print(f"Experimental cutoff freq.: {cutoff_freq:.3f} Hz")

# Calculate cut-off frequency by interpolating around previous value
if dbv[cutoff_idx] < -3:
    dbv_vals = [dbv[cutoff_idx - 1], dbv[cutoff_idx]]
    freq_vals = [freqs[cutoff_idx - 1], freqs[cutoff_idx]]
else:
    dbv_vals = [dbv[cutoff_idx], dbv[cutoff_idx + 1]]
    freq_vals = [freqs[cutoff_idx], freqs[cutoff_idx + 1]]
cutoff_freq_interp = freq_vals[0] + (-3 - dbv_vals[0])/((dbv_vals[1] - dbv_vals[0])/(freq_vals[1] - freq_vals[0]))

# Calculate time constant
calc_rc = 1/(2*np.pi*cutoff_freq)
print(f"Experimental RC (Bode): {1000*calc_rc:.3f} ms.")
calc_rc_interp = 1/(2*np.pi*cutoff_freq_interp)

print(f"Interpolated experimental cutoff freq.: {cutoff_freq_interp:.3f} Hz")
print(f"Interpolated experimental RC (Bode): {1000*calc_rc_interp:.3f} ms.")


# Turn everything off
sg.write("amp:offs 0")
sg.write("out 0")
osc.write("stop")

sg.close()
osc.close()
rc.close()