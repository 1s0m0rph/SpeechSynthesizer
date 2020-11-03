"""
The main vowel sound synthesizer program
"""


'''
consonants?????
'''
#TODO: this stuff ^^^

from util import *

def harm_formants_to_freq(formant_amps,f0):
	formant_vals = [0]
	formant_xvals = [0]
	prev_formant_num = 0
	for formant_hi in formant_amps:
		fq = formant_hi*f0
		amp = formant_amps[formant_hi]
		#add one harmonic at the midpoint with midpoint amp
		h_amp = (amp+formant_vals[-1])/(8)
		xv = ((formant_hi+prev_formant_num)//2)*f0
		if xv not in formant_xvals:
			formant_vals.append(h_amp)
			formant_xvals.append(xv)
		prev_formant_num = formant_hi
		#add this actual formant
		formant_vals.append(amp)  #amplitude
		formant_xvals.append(fq)  #frequency

	return formant_vals,formant_xvals

def add_midpoints_to_freq_formants(formant_amps,f0):
	formant_xvals = [0]
	formant_vals = [0]
	prev_harm_number = 0
	for fq in formant_amps:
		amp = formant_amps[fq]
		formant_harm_num = int(np.round(fq/f0,0))
		#add a halfway harmonic
		h_amp = (amp+formant_vals[-1])/(8)
		xv = ((formant_harm_num+prev_harm_number)//2)*f0
		if xv not in formant_xvals:
			formant_xvals.append(xv)
			formant_vals.append(h_amp)
		#add the formant
		formant_xvals.append(formant_harm_num*f0)#not exactly fq but as close as we can get
		formant_vals.append(amp)

	return formant_vals,formant_xvals

'''
"flat" referring to the fact that these tones won't change

formant_amps maps frequency (if not formants_as_harms else harmonic numbers) to amplitude (dB)
f0 is fundamental frequency (Hz)
base_amp is amplitude of non-formant (smooth this out instead?)
sam_len in seconds
'''
def generate_flat_complex_wave(formant_amps,f0,sam_len,base_amp=1,scale=1000,srate=44100,ofile=None,plot=False,formants_as_harms=False):
	assert(f0 >= 1)#this is because we generate a 1-second sample to base everything on
	#first build the frequency-space lists
	prev_freq = 0
	if formants_as_harms:
		formant_vals,formant_xvals = harm_formants_to_freq(formant_amps,f0)
	else:
		formant_vals,formant_xvals = add_midpoints_to_freq_formants(formant_amps,f0)
	formant_vals.append(0)#harmonic at high end is zero
	formant_xvals.append((5000//f0)*f0)
	#smooth the harmonics
	harmonic_xvals = np.arange(0,5001,f0)#all harmonics
	harmonic_vals = itp.interp1d(formant_xvals,formant_vals,kind='linear')(harmonic_xvals)
	#now convert to absolute amplitude
	harmonic_vals = db_to_absolute(harmonic_vals,scale=scale)
	#update the frequency array
	syn_fq_pos = ([0]*int((f0-1)) + [base_amp])*(5000//f0)#up to 10k hz
	for i,hi in enumerate(harmonic_vals):
		idx = (i+1)*f0 - 1
		if idx >= len(syn_fq_pos):
			break#smoothing adds some fake stuff way high up
		syn_fq_pos[idx] = hi#literally set the frequency at that harmonic to that amplitude
	#now pad to sample length with zeroes
	syn_fq_pos += [0]*int((srate//2) - len(syn_fq_pos))
	#create the actual synthetic frequencies
	syn_fq = np.array(syn_fq_pos + list(reversed(syn_fq_pos)))

	if plot:
		fqspace = np.fft.fftfreq(syn_fq.shape[-1])
		fqspace *= srate
		plt.figure(figsize=(20,10))
		plt.ticklabel_format(useOffset=False)
		plt.xlim(0,5000)
		plt.yscale('log')
		plt.plot(fqspace,syn_fq)
	
	#transform to get the data
	sound_dat_single = np.fft.irfft(syn_fq,srate)#has to be real valued so we don't get the wave all split
	sound_dat_single = list(sound_dat_single)[:int(srate/f0)]#truncate to just one period
	#pretend up until this point that sam_len is 1, then use just one period from this 1-second waveform to generate an arbitrarily long one
	#obviously this works under the assumption that the period is less than or equal to 1, that is, f0 >= 1
	#but a 1Hz f0 is really low (as in: too low to be audible)

	#the length of this (in samples [i.e. 1/srate seconds]) is exactly srate/f0 i.e. one period of the full waveform
	#extrude this exact waveform out to the desired sample length (plus possibly some extra)
	#nreps = (sam_len * srate) / (srate / f0)
	#nreps = (sam_len * srate) * (f0/srate)
	#nreps = sam_len * f0
	nreps_exact = sam_len*f0
	nreps = int(np.ceil(nreps_exact))
	nreps_extra = int(nreps - nreps_exact)
	sound_dat = sound_dat_single * nreps
	if nreps_extra > 0:
		#cut off whatever extra we had
		sound_dat = sound_dat[:-nreps_extra]
	sound_dat = np.array(sound_dat)
	
	if plot:
		plt.figure(figsize=(20,10))
		plt.xlim(0,int(srate/f0))
		plt.plot(sound_dat)
	
	if ofile is not None:
		wav.write(ofile,srate,sound_dat)
	else:
		return sound_dat


'''
Generate a waveform that can be spliced in between two different sounds by blending them together
that is, move the formants around according to a linear interpolation between the two sets of formants

trans_window is the size of the window we will ifft to for each step in the transition (it has units <srate>)
	for reference the praat spectrogram has an effective equivalent (by default) of 220.5 for this (i.e. 0.005 s)
'''
def generate_crossfade_wave(form1,form2,f0,cf_len=0.05,trans_window=100,srate=44100,base_amp=1):
	assert(len(form1) == len(form2))

	'''
	give me a standard vowel formatted
	
	offset is in units of <srate> (i.e. a time, starting from the beginning of the crossfade)
	'''
	def formant_amps_at(offset):

		formant_amps = {}
		for (fq1,fq2) in zip(form1,form2):
			#fq1 is the value at t=0
			#fq2 is the value at t=cf_len*srate
			#slope of connecting line is (fq2 - fq1) / (cf_len*srate - 0)
			#y - fq1 = ((fq2 - fq1) / (cf_len*srate))*(x - 0)
			#y = x(fq2 - fq1)/(cf_len*srate) + fq1
			fq = int(offset*((fq2 - fq1)/(cf_len*srate)) + fq1)
			#same thing happens for amplitude
			a1 = form1[fq1]
			a2 = form2[fq2]
			amp = offset*((a2 - a1)/(cf_len*srate)) + a1
			formant_amps.update({fq:amp})

		return formant_amps

	wv = np.array([])
	trans_len = trans_window / srate
	cf_samples = int(srate*cf_len)#convert units
	for offset in range(0,cf_samples,trans_window):
		#generate the famps
		formant_amps = formant_amps_at(offset)
		#generate the wave (lazily -- might want to fix the other function at some point)
		wv_add = generate_flat_complex_wave(formant_amps,f0,trans_len,base_amp=base_amp)
		wv = np.concatenate((wv,wv_add))
	return wv

		
#let's use what we have now to generate a few samples
#values from https://en.wikipedia.org/wiki/Formant
eng_vowel_fmts = {'i':{240:50,2400:45,3500:0},
				 'ɪ':{342:50,2278:45,3500:0},#not present in wiki article (based on my own production)
				 'ɛ':{610:50,1900:45,3500:0},
				 'e':{390:50,2300:45,3500:0},
				 'ɑ':{850:50,940:45,2500:0},
				 'ɔ':{500:50,700:45,2000:0},
				 'ʊ':{454:50,1379:45,2500:0},#not present in wiki article (based on my own production)
				 'u':{250:50,595:45,1800:0},
				 'ə':{750:50,1220:45,2500:0},#not present in wiki article (based on my own production)
				 'ʌ':{600:50,1170:45,2500:0},
				 'æ':{725:50,1691:45,3000:0},#not present in wiki article (based on my own production)
				 'a':{850:50,1610:45,3000:0},
				 'o':{360:50,640:45,2000:0},
				}


def ipa_vowels_to_synth(vs,vlens,f0,of=None,**kwargs):
	srate = 44100
	sound_dat = np.array([])
	for v,vlen in zip(vs,vlens):
		formant_amps = eng_vowel_fmts[v]
		this_res = generate_flat_complex_wave(formant_amps,f0,vlen,**kwargs)
		sound_dat = np.concatenate((sound_dat,this_res))#this syntax is dumb numpy

	if of is None:
		return sound_dat
	else:
		wav.write(of,srate,sound_dat)


def ipa_vowels_to_synth_cf(vs,vlens,f0,of=None,cf_len=0.05,trans_window=100,base_amp=1,**kwargs):
	srate = 44100
	sound_dat = np.array([])
	for i,(v, vlen) in enumerate(zip(vs, vlens)):
		formant_amps = eng_vowel_fmts[v]
		this_res = generate_flat_complex_wave(formant_amps, f0, vlen, **kwargs)
		sound_dat = np.concatenate((sound_dat, this_res))  #this syntax is dumb numpy
		if i < len(vs)-1:
			famps_next = eng_vowel_fmts[vs[i+1]]
			#generate a crossfade
			cf = generate_crossfade_wave(formant_amps,famps_next,f0,cf_len=cf_len,trans_window=trans_window,srate=srate,base_amp=base_amp)
			#add it in
			sound_dat = np.concatenate((sound_dat,cf))

	if of is None:
		return sound_dat
	else:
		wav.write(of, srate, sound_dat)