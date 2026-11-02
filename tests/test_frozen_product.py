"""Product evidence must demonstrate isolation and release, not just screenshots."""
import copy
import unittest

from tools import check_frozen_product as probe


def evidence():
    sample={'before':{'pid':91,'count':3},'during':{'pid':91,'count':3},
            'after':{'pid':91,'count':5},'layer_events':2,'closed':True}
    return dict(mode='native-product',inventory={'lookup/app.py':'a'*64},
        versions={'kwin':'6.8','qt':'6.12','game':'1.18.8'},
        fixture=dict(pid=41,frame='b'*64,source_ticks=[2,8],hover=True,
            selections=[dict(id=i,session=1,frame='b'*64,word=word,translation='перевод')
                        for i,word in enumerate(('bright','river','vocabulary'),1)],
            input=dict(sample,before={'pid':41,'count':2},during={'pid':41,'count':2},after={'pid':41,'count':4})),
        game=dict(pid=91,exits={name:copy.deepcopy(sample) for name in probe.EXITS}),
        primary={'mode':'primary','scene':False,'key':'public phrase'},
        no_hit_usable=True,internal_focus=True,scales=[1,1.25,2],
        cleanup={name:True for name in probe.CLEANUP})


class EvidenceTests(unittest.TestCase):
    def test_complete_actual_product_evidence(self):
        self.assertTrue(probe.accepted(evidence()))

    def test_rejects_missing_or_contradictory_product_proof(self):
        cases=[]
        value=evidence();value['mode']='research';cases.append(value)
        value=evidence();value['inventory']={};cases.append(value)
        value=evidence();value['fixture']['selections'][1]['frame']='c'*64;cases.append(value)
        value=evidence();value['fixture']['selections'][1]['session']=2;cases.append(value)
        value=evidence();value['fixture']['selections']=value['fixture']['selections'][:2];cases.append(value)
        value=evidence();value['fixture']['source_ticks']=[2,2];cases.append(value)
        value=evidence();value['fixture']['hover']=False;cases.append(value)
        value=evidence();value['game']['exits']['escape']['during']['count']=4;cases.append(value)
        value=evidence();value['game']['exits']['escape']['after']['pid']=92;cases.append(value)
        value=evidence();value['game']['exits']['escape']['after']['count']=3;cases.append(value)
        value=evidence();value['game']['exits'].pop('process_exit');cases.append(value)
        value=evidence();value['cleanup']['profiles_restored']=False;cases.append(value)
        value=evidence();value['primary']['scene']=True;cases.append(value)
        for index,value in enumerate(cases):
            with self.subTest(index=index):self.assertFalse(probe.accepted(value))

    def test_malformed_input_is_not_acceptance(self):
        for value in (None,[],{},dict(mode='native-product')):
            self.assertFalse(probe.accepted(value))
