"""
Contains code for synthesizing (english) fricative consonants:
	s
	z
	ʃ
	ʒ
	h
	f
	v
	θ
	ð

General strategy will be to generate the voiceless pattern and (if voiced) add on voicing afterward
"""

#TODO fix the following: (all voiced),h

from util import *
from scipy.stats import betabinom

eng_voiceless_fric_formants = {'s':{5000:(25,2400,7000),8650:(20,7000,15000)},
							   'ʃ':{60:(15,0,950),2600:(35,1000,7000),8300:(2,7000,10000)},
							   'f':{60:(20,0,580),3000:(21,1000,6600),10000:(3,9000,14500)},
							   'θ':{40:(10,0,450),2800:(17,1000,5000),11250:(3,8200,15000)},#this works okayish but it's not great
							   'h':{40:(28,0,1000),3000:(16,1000,6700)},#POP... nice
							   }

eng_voiced_fric_equivalents = {'z':'s',
							   'ʒ':'ʃ',
							   'v':'f',
							   'ð':'θ'}

eng_voiced_fric_amps = {'z': 44,
						'ʒ': 50,
						'v': 45,
						'ð': 50}

eng_fricatives = set(eng_voiced_fric_amps.keys()).union(eng_voiceless_fric_formants.keys())

'''
generally, voiceless looks like formants, but with random noise in between the (technically nonexistent) harmonics. respectively (mapping peak fq to (amp dB,window bound left, window bound right)):
	s: {5000:(25,2400,7000),8650:(20,7000,15000)}
	sh:{2600:(37,1000,7000),8300:(2,7000,10000)}
	f: {3000:(18,1000,6600),10000:(3,9000,14500)}
	θ: {2800:(20,1000,5000),11250:(4,8200,15000)}
		note: θ and f are practically identical, even to listen to
	h: {3000:(27,1500,6000),7500:(1,6000,10000)}

what should work is to have a default relative amplitude for each sound, then pull the frequencies from a (series of) normal distribution(s)
'''
#TODO fix relative scaling between consonants and vowels
def generate_voiceles_fricative(formant_amps,sam_len,noise_sample_increment=1,srate=44100,scale=1000,ofile=None,plot=False,ret_syn_fq_pos=False):
	boundary_exclude = 1000#exclude the first and last <number> of samples since the edge conditioning of fourier transforms is apparently really weird
	sam_len += 2*(boundary_exclude/srate)
	max_noise_samples = srate
	syn_fq_pos = [0.]*20000#up to 20k hz
	#generate the amplitudes as samples from normal distributions
	#that is, add <noise_sample_increment> dB to a frequency distributed normally according to the formants
	for peak_fq in formant_amps:
		peak_amp,window_low,window_high = formant_amps[peak_fq]
		# window_width *= 10
		# a,b = (min_freq - peak_fq)/(window_width/2),(20000 - peak_fq)/(window_width/2)
		fqs_add = np.round(np.random.triangular(window_low,peak_fq,window_high,size=max_noise_samples))
		# n = int(4*(window_width**2))
		# fqs_add = np.random.binomial(n,0.5,size=max_noise_samples)
		# print(peak_fq)
		# print(fqs_add[:1000] + peak_fq -  (n//2))
		# print(fqs_add[:1000])
		for fq_add in fqs_add:
			if (fq_add < 20000) and (fq_add >= 0):
				syn_fq_pos[int(fq_add)] += noise_sample_increment
				if syn_fq_pos[peak_fq] >= peak_amp:#then we're done with this one
					break


	if ret_syn_fq_pos:#for making voiced fricatives
		return syn_fq_pos
	#convert to absolute amplitude
	return generate_waveform_from_spectrum(syn_fq_pos, sam_len, scale, srate, boundary_exclude, ofile, plot,normalize_sample=True,fade_in=boundary_exclude)


'''
relative voicing amplitudes to highest frication amplitudes by sound, for voicelesses described above:
	z: 44
	ʒ: 50
	v: 45
	ð: 50
'''
def generate_voiced_fricative(f0, formant_amps, sam_len, voicing_amp=50, noise_sample_increment=1, srate=44100, scale=1000, ofile=None, plot=False):
	boundary_exclude = 1000#exclude the first and last <number> of samples since the edge conditioning of fourier transforms is apparently really weird
	sam_len += 2*(boundary_exclude/srate)
	#first generate a voiceless fricative with these amplitudes
	shift_scale = 0.45
	formant_amps = {int(fq*shift_scale):(formant_amps[fq][0],formant_amps[fq][1]*shift_scale,formant_amps[fq][2]*shift_scale) for fq in formant_amps}#pitch-shift the formants
	syn_fq_pos = generate_voiceles_fricative(formant_amps,sam_len,noise_sample_increment=noise_sample_increment,srate=srate,scale=scale,plot=plot,ret_syn_fq_pos=True)
	#now add voicing at H1
	# syn_fq_pos[int(f0)] = voicing_amp*max([amp for amp, _, _ in formant_amps.values()])#louder than the loudest fricative formant
	syn_fq_pos[int(f0)] = voicing_amp
	return generate_waveform_from_spectrum(syn_fq_pos,sam_len,scale,srate,boundary_exclude,ofile,plot,f0=f0,normalize_sample=True,fade_in=boundary_exclude)
