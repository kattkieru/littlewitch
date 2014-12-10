import os

import maya
from maya import cmds as mc
import pymel.core as pm

from . import utils
from modules import module_base

## ----------------------------------------------------------------------
'''

	MODULEFACTORY.PY

	Functions for (re)loading module class types.
'''
## ----------------------------------------------------------------------
class ModuleFactoryException(Exception):
	pass


## ----------------------------------------------------------------------
class ModuleFactory(object):
	def __init__(self):
		self.modulePath = os.sep.join( [__file__.rpartition( os.sep )[0], 'modules'] )
		self.modules = [ x.partition('.')[0] for x in os.listdir(self.modulePath) if x.endswith('.py') 
					and not x.count('__init') 
					and not x.count('module_base') ]

	## ----------------------------------------------------------------------

	def __getitem__(self, key):
		return(self.getClass(key))

	def __setitem__(self, key, value):
		raise ValueError("ModuleFactory does not allow the setting of values through brackets.")

	## ----------------------------------------------------------------------
	def getClass(self, name):

		for item in self.modules:
			modName = item.split('.')[0]
			if modName == name:
				impmod = __import__('witch.modules.'+modName, {}, {}, [modName])
				reload(impmod)
				theClass = impmod.__getattribute__( modName )
				return(theClass)

		## class not found!
		raise ModuleFactoryException('Class not found or unloadable: %s.' % name)

