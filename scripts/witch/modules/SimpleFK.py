import maya
from maya import cmds as mc
import pymel.core as pm

from witch import utils

from .module_base import ModuleBase, ModuleBaseException

## ----------------------------------------------------------------------
'''

	SIMPLEFK.PY

	A module for building simple FK controls on a joint or chain of joints.

	Note that this module does not override the seaming functions-- the default
	functionality is used.

'''

## ----------------------------------------------------------------------
class SimpleFK(ModuleBase):
	_defaultToken = 'SIMPLEFK'
	_module_type = 'SimpleFK'
		
	def __init__(self, *args):
		super(SimpleFK, self).__init__(*args)

	def build(self, **kwargs):
		self.pushState()

		self.createModule()
		self.conChain = self.createRigChain('CON', 2.0)

		self.connectChains( self.conChain, self.chain )

		## controls
		targetControls = self.conChain[:]
		if self.chainLength > 1:
			if not self['addControlToTip']:
				targetControls.pop(-1)

		for index, item in enumerate( targetControls ):
			name = item.partition("_")[0]
			con = self.createControl('fk', name, item, constrain='parent')
			utils.lock(con, s=True, v=True)
			if self.numControls('fk') > 1:
				pm.parent(self.getZero('fk', index), self.getControl('fk', index-1))

		self.popState()

	def calculateDefaults(self):
		super(SimpleFK, self).calculateDefaults()

	def createParams(self):
		super(SimpleFK, self).createParams()

		params = [
			{ 'name':'addControlToTip', 'type':'bool', 'value':False },
		]

		for param in params:
			name = param.pop('name')
			self.setParam(name, preserveValue=True, **param)

	##!FIXME: 	This isn't working due to some bad combination of reloading
	##			I'll fix this later -- it's not needed for SimpleFK anyway
	# def validate(self):
	# 	result = super(SimpleFK, self).validate()
	# 	return( result )

