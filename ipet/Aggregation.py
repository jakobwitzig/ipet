'''
Created on 30.12.2013

@author: bzfhende
'''
import numpy
import Misc, Editable
from xml.etree import ElementTree
from _functools import partial
from ipet.quick_Pandas import getWilcoxonQuotientSignificance as qWilcox
from ipet.IpetNode import IpetNode

class Aggregation(Editable.Editable, IpetNode):
    '''
    aggregates a list of values into a single value, as, e.g., a mean. Allows functions from numpy and
    from Misc-module
    '''
    nodetag = "Aggregation"
    possibleaggregations = ['shmean', 'gemean', 'min', 'max', 'mean', 'size', 'std', 'sum', 'median']
    agg2Stat = {'shmean':qWilcox}
    
    agg2keywords = {'shmean':[("shiftby", 10.0)]}

    def __init__(self, name=None, aggregation=None, **kw):
        '''
        constructs an Aggregation
        
        Parameters
        ----------
        name : The name for this aggregation
        
        aggregation : the name of the aggregation function in use
        
        kw : eventually, other options that will be passed to the call of the aggregation function
        '''
        self.name = name
        self.editableattributes = ['name', 'aggregation']
        if aggregation:
            self.set_aggregation(aggregation)
        elif name:
            self.set_aggregation(name)
            
        for key, val in kw.iteritems():
            setattr(self, key, float(val))

    def set_name(self, newname):
        self.name = newname

    def getName(self):
        if self.name is not None:
            name = self.name
        else:
            name = self.aggregation
            
        if( len(self.getEditableAttributes()) > 2 ):
            name += '(%s)'% ','.join((str(self.__dict__[key]) for key in self.editableattributes[2:]))
        return name

    @staticmethod
    def getPossibleAggregations():
        return Aggregation.possibleaggregations
    
    def getEditableAttributes(self):
        return self.editableattributes

    def set_aggregation(self, aggregation):
        if aggregation not in self.possibleaggregations:
            raise ValueError("%s aggregation not supported" % (aggregation))
        
        self.aggregation = aggregation
        try:
            self.aggrfunc = getattr(numpy, aggregation)
        except AttributeError:
            self.aggrfunc = getattr(Misc, aggregation)
            
        self.editableattributes = self.editableattributes[:2]
            
        attrlist = self.agg2keywords.get(aggregation)
        if attrlist:
            for key, val in attrlist:
                self.__dict__[key] = val
                self.editableattributes.append(key)

    def aggregate(self, valuelist):
        if len(self.getEditableAttributes()) > 2:
            return self.aggrfunc(valuelist, **{key:self.__dict__[key] for key in self.editableattributes[2:]})
        else:
            return self.aggrfunc(valuelist)

    @staticmethod
    def getNodeTag():
        return Aggregation.nodetag
    
    @staticmethod
    def processXMLElem(elem):
        if elem.tag == Aggregation.getNodeTag():
            additional = elem.attrib
            for child in elem:
                additional.update({child.tag:float(child.attrib.get('val'))})
            return Aggregation(**additional)

    def toXMLElem(self):
        attributes = {att:str(self.__dict__[att]) for att in self.editableattributes}
        me = ElementTree.Element(Aggregation.getNodeTag(), attributes)
            
        return me

    def getStatsTest(self):
        method = self.agg2Stat.get(self.name)
        if len(self.getEditableAttributes()) > 1 and method is not None:
            method = partial(method, **{key:self.__dict__[key] for key in self.editableattributes[2:]})
            method.__name__ = self.getName()
        return method

if __name__ == '__main__':
    arr = range(10)
    agg = Aggregation('min')
    agg2 = Aggregation('max')
    print agg.aggregate(arr), agg2.aggregate(arr)
    agg.set_aggregation('mean')
    agg2 = Aggregation('listGetShiftedGeometricMean',  shiftby=30.0)
    agg3 = Aggregation('listGetShiftedGeometricMean',  shiftby=300.0)
    print agg3.aggregate(arr), agg2.aggregate(arr)
