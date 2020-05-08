#!/usr/bin/python
# This class handles the generation of a new song given a markov chain
# containing the note transitions and their frequencies.
from markov_chain import MarkovChain, Note

import random
import ctcsound

REVERB = False

# Info on ctcsound: https://github.com/csound/ctcsound

ORC_SETTINGS = """
sr=44100
kr=32
nchnls=2
0dbfs=1

gaverb init 0
"""

# basic tone
INSTR1 = """
; p4 is freq
; p5 is amplitude
instr 1
ifreq = p4
iamp = p5
kenv linseg 0, p3/8, 0.8, p3/4, 0.4, 5*p3/8, 0
asig1 oscil 0.2, ifreq
asig2 oscil 0.2, ifreq*2
asig3 oscil 0.2, ifreq*3
aout = (asig1 + asig2 + asig3)*kenv*iamp*0.5
gaverb	 =	gaverb+aout*0.1
outs aout, aout
endin
"""

# drum
INSTR2 = """
	instr	102	; SIMPLE FM
a1	foscil	10000, 440, 1, 2, 3, 1
 	out	a1
 	endin
"""

REVERB_INST = """
instr	99			
averb	reverb	gaverb,2
outs	averb, averb
gaverb	=  0		; reinitialize global reverb variable
endin
"""

INSTRUMENTS = [INSTR1, INSTR2]
SCORE_FUNCTIONS = "" # used for functions called in instruments

def create_orchestra(settings, instruments, reverb=REVERB):
    """
    Inputs:
        * settings: Csound settings, including sr, kr, nchnls, 
            and 0dbfs in a string format
        * instruments: list of instruments, each defined in a string
    Outputs: full orchestra in a string
    """
    output = settings + '\n'
    for instr in instruments:
        output += instr + '\n'
    if (reverb):
        output += REVERB_INST
    return output

def create_score(score_functions, score, duration=60, reverb=REVERB):
    """Inputs: 
        * core_functions: csound functions for any instruments in a string
        * score: a csound score in a string, of form "i1 0 5"
        * duration: for the reverb instrument, should be 
            duration of the entire composition in seconds
        * reverb: boolean used if reverb is wanted in the composition
    Returns the final score in a string"""
    reverb_score = ""
    if (reverb):
        reverb_score = "i99 0 " + str(duration) + '\n'
    return score_functions+reverb_score+score

def perform(orc, score, create_wav=False, wav_file='output.wav'):
    """
    Inputs: 
        * orc: csound orchestra in a string
        * score: csound score in a string
        * create_wav: boolean setting for if running this 
            function will create an output wav file. 
            Default False.
        * wav_file: file name for output wav file. 
            Default 'output.wav'.

    Function reads input orc and score and plays
        the corresponding csound composition. It generates
        the corresponding wav file if create_wav is True.
    """
    c = ctcsound.Csound()
    c.setOption("-odac")

    print(score)

    if (create_wav):
        output_file_flag = '-o ' + wav_file
        c.setOption(output_file_flag)

    # prepare the inputs
    c.compileOrc(orc)
    c.readScore(score)

    # performance
    c.start()
    c.perform()
    c.cleanup()
    c.reset()
    del c


def getFrequency(note, A4=440):
    # Stolen from https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
    notes = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

    octave = int(note[2]) if len(note) == 3 else int(note[1])

    # Convert flats to sharp and remove ocatve
    if '-' in note:
        note_val = ord(note[0]) - 1
        note = (chr(note_val) if note_val!=64 else 'G') + '#'
    else:
        note = note[:2]
        
    keyNumber = notes.index(note[0:1]);
    
    if (keyNumber < 3) :
        keyNumber = keyNumber + 12 + ((octave - 1) * 12) + 1; 
    else:
        keyNumber = keyNumber + ((octave - 1) * 12) + 1; 

    return A4 * 2** ((keyNumber- 49) / 12)

class Generator:

    def __init__(self, markov_chain):
        self.markov_chain = markov_chain
        self.score = ""
        self.total_duration = 0.0

    @staticmethod
    def load(markov_chain):
        assert isinstance(markov_chain, MarkovChain)
        return Generator(markov_chain)

    def _notes_to_score_line(self, notes, second, instr):
        lines = ""
        n_notes = len(notes.notes.split('|'))
        for n in notes.notes.split('|'):
            amp = 1.0 / n_notes
            freq = getFrequency(n)
            lines += f"{instr} {(second + notes.offset):.2f} {notes.duration:.2f} {freq:.2f} {amp:.2f}\n"
        return lines

    def generate_instrument_score(self, instr, duration=60, start_note = None):
        last_note = start_note
        current_duration = 0.0
        instr_score = ""
        # Generate a sequence of notes for the requested duration
        while current_duration < duration:
            new_note_entry = self.markov_chain.get_next(last_note)
            # take the last note in the list
            new_notes =  Note(new_note_entry.notes.split(',')[-1],
                                    new_note_entry.duration, new_note_entry.offset)
            if new_notes.notes != '' and new_notes.duration > 0:
                instr_score += self._notes_to_score_line(new_notes, current_duration, instr)
                current_duration += new_notes.duration + new_notes.offset
            last_note = new_note_entry
        
        self.score += instr_score
        self.total_duration = max(self.total_duration, current_duration)


if __name__ == "__main__":
    import sys
    if len(sys.argv) in [2, 3]:
        # Example usage:
        # python generator.py <in.mid> [<out.wav>]
        from parser import Parser
        chain = Parser(sys.argv[1]).get_chain()
        g = Generator.load(chain)
        g.generate_instrument_score('i1')

        orc = create_orchestra(ORC_SETTINGS, INSTRUMENTS)

        print(g.score)

        if len(sys.argv)==3:
            perform(orc, g.score, create_wav=True, wav_file=sys.argv[2])
        else:
            perform(orc, g.score)

        print('Generated markov chain')
    else:
        print('Invalid number of arguments:')
        print('Example usage: python generator.py <in.mid> [<out.wav>]')
