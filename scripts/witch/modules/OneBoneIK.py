import maya
from maya import cmds as mc
import pymel.core as pm

from five import utils

from .module_base import ModuleBase, ModuleBaseException

## ----------------------------------------------------------------------
'''

	ONEBONEIK.PY

	A module for building a simple IK control on a single bone chain.

'''

class OneBoneIK(ModuleBase):
	_defaultToken = 'ONEBONEIK'
	_module_type = 'OneBoneIK'
	_minChainLength = 2
	_maxChainLength = 2
	_defaultControllerType = 'cube'
	_defaultRotationOrder = 'zxy'	 
	_worldHookable = False
	_usesAutoParent = True

	def __init__(self, *args):
		super(OneBoneIK, self).__init__(*args)

	def build(self, **kwargs):
		pass

	def validate(self):
		result = super(OneBoneIK, self).validate()
		return( result )

	def postbuild(self):
		pass

	def calculateDefaults(self):
		pass





