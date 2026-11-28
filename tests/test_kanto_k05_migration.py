from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit import json_file
from k05_contract import MAPS, SLOTS, predecessor_sets, scoped_connection
from k05_migration import predecessor_edits
from k04_corridor import published_destinations as rock
from k05_promotion import verify_plan


class KantoK05MigrationTests(unittest.TestCase):
    def prepare(self):
        base={sid for sid in json_file(ROOT/"data/regions/kanto-source.json")["maps"] if int(sid) not in MAPS}
        new={sid:300+i for i,sid in enumerate(sorted(base))}
        new.update(rock())
        new.update({str(i):v for i,v in SLOTS.items()})
        return new

    def test_exact_skip_paths(self):
        new=self.prepare()
        eligible=predecessor_sets(new)
        expected={156:{18,21},160:{21},165:set()}
        for size,sids in eligible.items():
            mapping={i:new[i] for i in sids}
            self.assertEqual(predecessor_edits(mapping,new),expected[size])
            for key in sorted(mapping):
                with self.subTest(size=size,drift=key):
                    drift={**mapping,key:999}
                    with self.assertRaises(ValueError):
                        predecessor_edits(drift,new)
        self.assertEqual(set(eligible),set(expected))

    def test_reject_any_lavender_shortcut(self):
        self.assertTrue(scoped_connection(86,"South",0,87,"North",0))
        self.assertTrue(scoped_connection(93,"North",0,87,"South",0))
        for out in (79,86,107,83):
            self.assertFalse(scoped_connection(93,"West",0,out,"East",0))
        self.assertFalse(scoped_connection(87,"South",0,93,"North",0))
        native={int(k):v for k,v in self.prepare().items()}
        verify_plan(native,{"connections":[[609,"North",0,605,"South",0]]})
        with self.assertRaises(ValueError):
            verify_plan(native,{"connections":[[609,"West",0,604,"East",0]]})
