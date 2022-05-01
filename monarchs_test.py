from monarchs import *
import pytest
from collections import Counter
from io import StringIO

class TestHexUtils:
    def test_hex_name_coord(self):
        assert hex_name((0,0),0) == 'A1'
        assert hex_name((0,0),4) == 'I5'

        for r in range(7):
            for i in range(-2*r,2*r+1):
                for j in range(-r,r):
                    assert hex_coord(hex_name((i,j),r),r) == (i,j)

        with pytest.raises(ValueError, match="I can't handle radius 7"):
            x = hex_name(radius=7)

        with pytest.raises(ValueError, match="Invalid hexname: AB"):
            x = hex_coord('AB', radius=4)

    def test_hex_distance(self):
        for i in range(3):
            for j in range(3):
                if (i + j)%2 == 0:
                    assert hex_distance((0,0),(i,j)) == j + max(i/2-j/2,0)

    def test_allegiance(self):
        assert allegiance(-2,0) == {'nation':'r','regiments':Counter({'r': 3, 'g': 0, 'b': 0})}
        assert allegiance(0,-2) == {'nation':'b','regiments':Counter({'r': 0, 'g': 0, 'b': 0})}
        assert allegiance(4,0) == {'nation':'g','regiments':Counter({'r': 0, 'g': 2, 'b': 0})}

class TestInput:
    def test_input_moves(self, monkeypatch):
        monkeypatch.setattr('sys.stdin', StringIO('NO\nEND\n'))
        assert input_moves('r') == {}

        monkeypatch.setattr('sys.stdin', StringIO('foo\nhex1\nhex2\n2\nYES\nEND\n'))
        assert input_moves('r') == {'boost':'foo',('hex1','hex2'):2}

        monkeypatch.setattr('sys.stdin', StringIO('foo\nhex1\nhex2\nq\nhex1\nhex2\n2\nYES\nEND\n'))
        assert input_moves('r') == {'boost':'foo',('hex1','hex2'):2}

        monkeypatch.setattr('sys.stdin', StringIO('foo\nhex1\nhex2\n2\nNO\nhex3\nhex4\n3\nYES\nEND\n'))
        assert input_moves('r') == {'boost':'foo',('hex3','hex4'):3}

    def test_input_allegiances(self, monkeypatch):
        pass

    def test_input_guesses(self, monkeypatch):
        pass

class TestScoring:
    def test_nation_scores(self):
        pass

    def test_final_scores(self):
        pass

class TestGrid:
    def test_grid_counts(self):
        for n in range(7):
            game = Monarchs(radius=n)
            assert len(game.hexes.keys()) == 3*n**2 + 3*n + 1

            regs = Counter()
            for h in game.hexes.values():
                for nation in h.regiments:
                    regs[nation] += h.regiments[nation]
            for nation in ['r', 'g', 'b']:
                assert regs[nation] == 5 + 4*n + min(2,2*n)


