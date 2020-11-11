from synthesizer import *

# f0 = 100
# # formant_amps = map_fq_to_harms({250:50,3500:45},f0)
# # print(formant_amps)
# # formant_amps = {7:40,11:32,23:24,33:0}#this works for /a/ with f0 = 101
# formant_amps = {240:40,2400:40,2400+175*3:0}
# dur = 1
# base_amp = 25
# scale = 750
# generate_flat_complex_wave(formant_amps,f0,dur,base_amp=base_amp,scale=1000,plot=False,ofile="complex.wav",formants_as_harms=False)

# ipa_vowels_to_synth_cf('iu',[0.2,0.3],100,'synth_iu.wav',cf_len=0.01,trans_window=50)

# formant_amps = {5000:(25,2400,7000),8650:(20,7000,15000)}#/s/ or /z/ -- z doesn't seem to be working right though...
# formant_amps = {2600:(37,1000,7000),8300:(2,7000,10000)}#/ʃ/
# formant_amps = {3000:(18,1000,6600),10000:(3,9000,14500)}#/f/
# formant_amps = {2800:(20,1000,5000),11250:(4,8200,15000)}#th
# formant_amps = {3000:(27,1500,6000),7500:(1,6000,10000)}#palatal fric
# formant_amps.update({max(formant_amps.keys())+f0*10:0})
# dur = 2
# scale = 750
# noise_sample_increment = 1
# voicing_amp = 50
# generate_voiceles_fricative(formant_amps, dur, noise_sample_increment=noise_sample_increment, scale=scale, plot=False, ofile="fricative.wav")
# generate_voiced_fricative(100, formant_amps, dur, voicing_amp=voicing_amp, noise_sample_increment=noise_sample_increment, scale=scale, plot=False, ofile="fricative.wav")

# eng_vowel_fmts = {'i':{240:50,2400:45,3500:0},
# 				 'ɪ':{342:50,2278:45,3500:0},#not present in wiki article (based on my own production)
# 				 'ɛ':{610:50,1900:45,3500:0},
# 				 'e':{390:50,2300:45,3500:0},
# 				 'ɑ':{850:50,940:45,2500:0},
# 				 'ɔ':{500:50,700:45,2000:0},
# 				 'ʊ':{454:50,1379:45,2500:0},#not present in wiki article (based on my own production)
# 				 'u':{250:50,595:45,1800:0},
# 				 'ə':{750:50,1220:45,2500:0},#not present in wiki article (based on my own production)
# 				 'ʌ':{600:50,1170:45,2500:0},
# 				 'æ':{725:50,1691:45,3000:0},#not present in wiki article (based on my own production)
# 				 'a':{850:50,1610:45,3000:0},
# 				 'o':{360:50,640:45,2000:0},
# 				}

ipa_to_synth_cf('iɛs',[0.1,0.15,0.15],100,cf_len=0.03)#:D
# ipa_to_synth_cf('ɪ',[1],100,cf_len=0.03)#:D
# ipa_to_synth_cf('ai',[0.15,0.2],100)