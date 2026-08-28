# -*- coding: utf-8 -*-
"""PhysicsControlAsset Profiles(TMap) <-> ImportText 변환"""
import json
def fmt(v):
    if isinstance(v,bool): return 'True' if v else 'False'
    if isinstance(v,(int,float)):
        s=repr(float(v))
        return s
    if isinstance(v,str): return '"%s"'%v
    if isinstance(v,list): return '('+','.join(fmt(x) for x in v)+')'
    if isinstance(v,dict): return '('+','.join('%s=%s'%(k,fmt(x)) for k,x in v.items())+')'
    if v is None: return 'None'
    raise TypeError(str(type(v)))
def tmap(d):
    # UE TMap ImportText:  (("Key",Value),("Key2",Value2))
    return '('+','.join('("%s",%s)'%(k,fmt(v)) for k,v in d.items())+')'
