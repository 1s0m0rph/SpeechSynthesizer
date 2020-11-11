"""
Unifies all the other synthesizer files
"""
from fricative_synthesizer import *
from vowel_synthesizer import *
from stop_consonant_synthesizer import *


#TODO CV and VC transitions (VOT etc.)
def ipa_to_synth_cf(sounds,slens,f0,of=None,cf_len=0.05,trans_window=100,base_amp=1,**kwargs):
	assert(len(sounds) <= len(slens))
	srate = 44100
	no_blend_sounds = {' '}#don't blend vowels into these sounds
	sound_dat = np.array([])
	i = 0
	while i < len(sounds):
		if sounds[i] == ' ':#we'll use this to mean word break/silence
			sound_dat = np.concatenate((sound_dat,np.zeros(int(slens[i]*srate))))
			i += 1
			continue
		#collect a string of vowels if there is one
		vstart = i
		while (i < len(sounds)) and (sounds[i] in eng_vowel_fmts):
			i += 1
		if i > vstart:
			vstr,vlens = sounds[vstart:i],slens[vstart:i]
			this_res = ipa_vowels_to_synth_cf(vstr,vlens,f0,of=None,cf_len=cf_len,trans_window=trans_window,base_amp=base_amp,**kwargs)
			if (vstart > 0) and (sounds[vstart-1] not in no_blend_sounds):#this means we're preceeded by a consonant
				#so we should overlay the beginning of the vowel with that consonant and decrease the consonant amplitude
				#decrease the consonant amplitude
				twv = trans_window*10
				sound_dat[-twv:] = np.array([sound_dat[-j]*((twv-j)/twv) for j in range(0,twv)])
				sound_dat[-twv:] += np.array([this_res[j]*((j)/twv) for j in range(0,twv)])
				this_res = this_res[twv:]
			sound_dat = np.concatenate((sound_dat,this_res))
		else:#consonant
			s = sounds[i]
			slen = slens[i]
			if s in eng_fricatives:
				if s in eng_voiced_fric_amps:#voiced fricative
					formant_amps = eng_voiceless_fric_formants[eng_voiced_fric_equivalents[s]]
					voicing_amp = eng_voiced_fric_amps[s]
					this_res = generate_voiced_fricative(f0,formant_amps, slen, srate=srate,voicing_amp=voicing_amp)
					sound_dat = np.concatenate((sound_dat, this_res))
				else:#voiceless fricative
					formant_amps = eng_voiceless_fric_formants[s]
					this_res = generate_voiceles_fricative(formant_amps,slen,srate=srate,ret_syn_fq_pos=False)
					sound_dat = np.concatenate((sound_dat,this_res))
			else:
				raise NotImplementedError("Sound not known (yet!): {}".format(s))
			i += 1

	if of is None:
		of = 'synth_{}.wav'.format(sounds)
	wav.write(of, srate, sound_dat)