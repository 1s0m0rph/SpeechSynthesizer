import numpy as np
from scipy.io import wavfile as wav
import matplotlib.pyplot as plt
from scipy import interpolate as itp

'''
convert decibel values (e.g. from praat) to the absolute units (lol) that we need here

we make the highest amplitude in these equal to scale and base the others off it
'''
def db_to_absolute(amps,scale=1000):
	m_amp = max(amps)

	absolute_amps = []
	for db_amp in amps:
		if db_amp == 0:
			absolute_amps.append(0)
		else:
			#difference is ratio
			db_diff = db_amp - m_amp
			#20 db is a 10-fold increase in amplitude, so take 10^(x/20)
			amp_rat = 10**(db_diff/20)
			#multiply by that
			absolute_amps.append(scale*amp_rat)

	return absolute_amps


'''
sfp should be in dB and should not include any padding of any kind
'''
def generate_waveform_from_spectrum(syn_fq_pos,sam_len,scale,srate,boundary_exclude,ofile,plot,f0=None,min_extrusion_samples=1000,normalize_sample=False,fade_in=0):
	#convert to absolute amplitude
	syn_fq_pos = db_to_absolute(syn_fq_pos, scale=scale)
	syn_fq_pos += [0]*int(sam_len*(srate//2)-len(syn_fq_pos))

	syn_fq = np.array(syn_fq_pos+list(reversed(syn_fq_pos)))

	if plot:
		fqspace = np.fft.fftfreq(syn_fq.shape[-1])
		fqspace *= srate
		plt.figure(figsize=(20, 10))
		plt.ticklabel_format(useOffset=False)
		plt.xlim(0, 20000)
		plt.yscale('log')
		plt.plot(fqspace, syn_fq)

	sound_dat_single = np.fft.irfft(syn_fq,srate)[boundary_exclude:-boundary_exclude]#1 second sample
	#extrude
	extrusion_samples = min_extrusion_samples if (f0 is None) else int(srate/f0)
	if normalize_sample:
		#look for something equal to the start amplitude near extrusion_samples (this should ensure a smooth transition)
		tol = 1e-5
		sval = sound_dat_single[0]
		while (extrusion_samples < len(sound_dat_single)) and (not np.isclose(sound_dat_single[extrusion_samples],sval,rtol=tol)):
			extrusion_samples += 1
	sound_dat_single = sound_dat_single[:extrusion_samples]


	sound_dat_single = list(sound_dat_single)
	#pretend up until this point that sam_len is 1, then use just one period from this 1-second waveform to generate an arbitrarily long one
	#obviously this works under the assumption that the period is less than or equal to 1, that is, f0 >= 1
	#but a 1Hz f0 is really low (as in: too low to be audible)

	#the length of this (in samples [i.e. 1/srate seconds]) is exactly srate/f0 i.e. one period of the full waveform
	#extrude this exact waveform out to the desired sample length (plus possibly some extra)
	#nreps = (sam_len * srate) / (extrusion_samples)
	nreps_exact = (sam_len*srate)/extrusion_samples
	nreps = int(np.ceil(nreps_exact))
	samples_extra = int(nreps*extrusion_samples) - int(nreps_exact*extrusion_samples)
	sound_dat = sound_dat_single*nreps
	if samples_extra > 0:
		#cut off whatever extra we had
		sound_dat = sound_dat[:-samples_extra]
	sound_dat = np.array(sound_dat)

	#add in fade-in (if there is any). Simple linear will do
	sound_dat[:fade_in] = np.array([sound_dat[i]*(i/fade_in) for i in range(fade_in)])

	if plot:
		plt.figure(figsize=(20, 10))
		plt.xlim(0, extrusion_samples)
		plt.plot(sound_dat)

	if ofile is not None:
		wav.write(ofile, srate, sound_dat)
	else:
		return sound_dat