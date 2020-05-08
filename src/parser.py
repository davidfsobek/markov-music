#!/usr/bin/python
# This class handles the parsing of a midi file and builds a markov
# chain from it.

import hashlib
from music21 import converter, chord, note, instrument, stream
import argparse

from markov_chain import MarkovChain

class Parser:

    def __init__(self, filename, verbose=False, order=1):
        """
        This is the constructor for a Serializer, which will serialize
        a midi given the filename and generate a markov chain of the
        notes in the midi.
        """
        self.filename = filename
        # The tempo is number representing the number of microseconds
        # per beat.
        self.tempo = None
        # The delta time between each midi message is a number that
        # is a number of ticks, which we can convert to beats using
        # ticks_per_beat.
        self.markov_chain = MarkovChain()

        self.order=order
        self.markov_chain.order = order

        self._parse(verbose=verbose)

    def _parse(self, verbose=False):
        """
        This function handles the reading of the midi and chunks the
        notes into sequenced "chords", which are inserted into the
        markov chain.
        """
        previous_notes = []

        midi = converter.parse(self.filename)
        for parts in midi:
            list_of_notes = list(parts.recurse())
            list_of_notes.sort(key=lambda x: float(x.offset))
            previous_offset = 0.0
            for n in list_of_notes:
                if verbose:
                    print(str(n))
                notes = ""
                if isinstance(n, note.Note):
                    notes = str(n.pitch)
                elif isinstance(n, chord.Chord):
                    n_c = str(n).replace('>', '')
                    notes = '|'.join(n_c.split()[1:])
                duration = float(n.duration.quarterLength)
                note_offset = float(n.offset) - previous_offset
                previous_offset = float(n.offset)
                
                # generalized for orders greater than 0.
                next_notes = None
                if len(previous_notes) < self.order:
                    next_notes = previous_notes + [notes]
                else:
                    next_notes = previous_notes[1:] + [notes]
                
                if len(previous_notes) != 0:
                    self.markov_chain.add(','.join(previous_notes), ','.join(next_notes), duration, note_offset)
                
                previous_notes = next_notes

    def get_chain(self):
        return self.markov_chain

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="The midi file input")
    args = parser.parse_args()
    print(Parser(args.input_file, verbose=False).get_chain())
    print('No issues parsing {}'.format(args.input_file))