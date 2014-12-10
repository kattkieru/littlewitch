import os

import maya
from maya import cmds as mc
import pymel.core as pm

from . import utils
reload(utils)

from .modules import module_base
reload(module_base)

from . import moduleFactory as mf
reload(mf)

## ----------------------------------------------------------------------
'''

	AUTOMATEDBUILD.PY

	Functions for doing automatic builds of modules.

	This module should be the main entry point for any addition of
	new modules to a rig-- it runs through the build stages in the 
	proper order.

'''

## ----------------------------------------------------------------------
class AutomatedBuildException(Exception):
	pass

## ----------------------------------------------------------------------
def automatedBuild(*args, **kwargs):
	rebuild = kwargs.get('rebuild', False)

	oblist = [ x for x in utils.makeList(args, type='joint') ]

	factory = mf.ModuleFactory()
	print(factory.modules)

	instances = []

	print( ">> AutomatedBuild: Collecting chains..." )
	for item in oblist:
		cType = utils.getAttrSpecial( item, 'type', prefix=module_base.PARAM_PREFIX )
		if not cType in factory.modules:
			## something funky has happened
			print( "\t--Invalid module type %s for root %s-- skipping..." % (cType, item) )
			continue

		if item.hasAttr('module') and item.module.get() is not None:
			## assume it's already built and skip unless rebuild is specified
			if not rebuild:
				print( "\t-- AutomatedBuild: Skipping built root %s." % item )
				continue
			else:
				print( "\t++ AutomatedBuild: Rebuild -- removing module from %s..." % item )
				utils.removeModule( item )

		moduleClass = factory.getClass(cType)
		instance = moduleClass(item)

		instances.append(instance)

	## build stages

	print( ">> AutomatedBuild: Validating..." )
	for instance in instances:
		if not instance.validate():
			raise AutomatedBuildException( 'Instance invalid: %s (root %s).' % (instance['root'], instance._message) )

	print( ">> AutomatedBuild: Build starting..." )
	for instance in instances:
		print( "\t++ %s (%s) -- root (%s)" % (instance['token'], instance['type'], item) )
		instance.build()

	print( ">> AutomatedBuild: Postbuild..." )
	for instance in instances:
		instance.postbuild()

	print( ">> AutomatedBuild: Seaming..." )
	for instance in instances:
		instance.seamRoot()
		instance.seamGoal()

	print( "++ AutomatedBuild: Build complete (%d modules)" % len(instances) )











