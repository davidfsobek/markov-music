import sys
import glob

from parser import Parser
from markov_chain import MarkovChain
import generator as gen

CHOPIN_FILES = '../midi/chopin_piano/*.mid'
ORDER = 3

def main():
    if len(sys.argv) in [2, 3]:
        chain = MarkovChain()
        for fname in glob.glob(CHOPIN_FILES):
            chain.merge(Parser(fname, order=ORDER).get_chain())
        
        g = gen.Generator.load(chain)
        g.generate_instrument_score('i1', duration=120)

        orc = gen.create_orchestra(gen.ORC_SETTINGS, gen.INSTRUMENTS)

        print(g.score)

        if len(sys.argv)==3:
            gen.perform(orc, g.score, create_wav=True, wav_file=sys.argv[2])
        else:
            gen.perform(orc, g.score)
    else:
        print('Invalid number of arguments:')
        print('Example usage: python chopin_generator.py <duration> [<out.wav>]')



if __name__ == "__main__":
    main()