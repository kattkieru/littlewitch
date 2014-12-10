import maya
from maya import cmds as mc
import pymel.core as pm

from .. import utils

## ----------------------------------------------------------------------
'''

	MODULE_BASE.PY

	Base class for all rig modules.  If you know C++, consider this a 
	virtual class with functions that need to be overridden in order to 
	instantiate and build rig parts.

	The following are the main functions you might want to override:

	build():	The least you need to do is to override the build() method.  This
				is where you'll do the bulk of the module's setup.

	calculateDefaults():	When setting params for the first time, this allows you
							to specify the default values of the params based on the
							chain being tagged.

	createParams():	Used to specify rig parameters, settings that change how the
					rig is built.

	postbuild(): 	This is run by automatedBuild after all modules are complete,
					making it easier to connect modules together that need to rely
					on each other.  This function can assume that build() ran 
					successfully.

	seamGoal():		Used to perform connections between modules when you've specified
					a parent for the IK Goal of the current module in another.

	seamRoot():		Used to perform connections between modules when you've specified
					a parent for the root of the current module in another.

	validate():		If your module requires certain pre-conditions be extant before
					build can run, you can check for those conditions here.

'''

## ----------------------------------------------------------------------

class ModuleBaseException(Exception):
	pass

## constants
PARAM_PREFIX = 'WT'

## ----------------------------------------------------------------------

class ModuleBase(object):
	_defaultToken = 'MODULEBASE'
	_module_type = 'ModuleBase'
	_minChainLength = 0
	_maxChainLength = 0
	_defaultControllerColor = utils.colors.indexForColor('green')
	_defaultControllerSubColor = utils.colors.indexForColor('yellow')
	_defaultControllerType = 'box'
	_defaultRotationOrder = 'zxy'
	_isIkFk = False
	_usesRoot = True		## this is turned off for special modules, like GOD
	_usesGoal = False

	## ----------------------------------------------------------------------
	## python-y methods
	def __init__(self, *args):
		self._message = None
		
		## different types of controls with their own Param collections
		self._controllerCategories = []

		## these are targets for constraints
		self._inputs = {}
		
		## these are automatically populated if the module author uses
		## the createControl function in the module and not in utils
		## these are sorted into list bins by category, IE, self._controlers['fk']
		self._controllers = {}
		self._controllerZeros = {}

		self.module = self.rig = self.controls = self.extras = None

		## grab the chain
		oblist = utils.makeList(args, type='joint')
		if not len(oblist):
			raise ModuleBaseException('Tried to create module instance without a chain of joints.')
		self.chain = utils.getChain(oblist[0])

		self.segmentScaleCompensateDisable( self.chain )

		self.rigRoot = utils.addRigRoot( self.chain[0] )

		## this has to happen before defaults and params creation
		self.calculateSide()

		self.calculateDefaults()
		self.createParams()

		##!FIXME: If the module already exists, pull info from the extant nodes
		## If it doesn't exist, create the base parts

	def __str__(self):
		joints = 's' if self.chainLength > 1 else ''
		return("<< Witch Rig Module Instance: %s (%d joint%s)." % (self.__class__, self.chainLength, joints) )

	def __repr__(self):
		return( self.__str__() )

	def __getitem__(self, key):
		## This returns None if the lookup fails
		## Is that the right decision?
		result = self.getParam(key)
		return(result)

	def __setitem__(self, key, value):
		## if the parameter was already created in createParams, then you can set it
		## otherwise, kick up an error
		if self.hasAttr(PARAM_PREFIX+"_"+key):
			self.setParam(key, value)
		else:
			raise ValueError("ModuleBase: param '%s' does not exist -- cannot set." % key)

	def getControl(self, category, index):
		return(self._controllers[category][index])

	def getZero(self, category, index):
		return(self._controllerZeros[category][index])

	def numControls(self, category):
		if category in self._controllers.keys():
			return(len(self._controllers[category]))
		else:
			return(0)

	## ----------------------------------------------------------------------
	## "virtual" methods
	def build(self, **kwargs):
		raise ModuleBaseException('Invalid subclass-- build() virtual function not implemented.')

	def calculateDefaults(self):
		## Calculate default colors here if necessary.
		## This is an example; they're set above in the class variables.
		#self._defaultControllerColor = 6
		#self._defaultControllerSubColor = 9

		## default controller types
		self.registerControllerCategory('fk')
		if self._isIkFk:
			self.registerControllerCategory('ik')

	def createParams(self):
		defaultParams = [
			{ 'name':'type', 'type':'string', 'value':self._module_type },
			{ 'name':'token', 'type':'string', 'value':self._defaultToken },
			{ 'name':'hideModule', 'type':'bool', 'value':False },
		]

		## This is the simplest way to identify rig module chain roots in the scene
		## without doing something like adding a custom locator shape: add a special
		## attribute to it, and sort by that attribute
		if not self.root.hasAttr('MODULEROOT'):
			self.root.addAttr('MODULEROOT', at='bool', dv=True, k=True)
			self.root.MODULEROOT.lock()

		for param in defaultParams:
			name = param.pop('name')
			self.setParam(name, preserveValue=True, **param)

		self.createControllerParams()

	def postbuild(self):
		## default: no postbuild
		pass

	def seamGoal(self):
		goalParent = utils.getParentAttr(self.root, 'goal')
		if goalParent is not None and self['goalInput'] is not None:
			##!FIXME: 	offer other types of constraining apart from parent / scale?
			##			This could mean that the constraint listing below wouldn't 
			##			work if the constraint were more exotic

			## clean out prior constraints
			oldCnsts = self['goalInput'].getChildren(type='constraint')
			for item in oldCnsts:
				pm.delete(item)

			self.constrain(goalParent, self['goalInput'], mo=True, type='parent')
			self.constrain(goalParent, self['goalInput'], mo=True, type='scale')

	def seamRoot(self):
		rootParent = utils.getParentAttr(self.root, 'root')
		if rootParent is not None and self['rootInput'] is not None:
			##!FIXME: 	Offer other types of constraining apart from parent / scale?
			##			This could mean that the constraint listing below wouldn't 
			##			work if the constraint were more exotic, and I'll have to
			##			keep track of constraint nodes

			## clean out prior constraints
			oldCnsts = self['rootInput'].getChildren(type='constraint')
			for item in oldCnsts:
				pm.delete(item)

			self.constrain(rootParent, self['rootInput'], mo=True, type='parent')
			self.constrain(rootParent, self['rootInput'], mo=True, type='scale')

	def validate(self):
		if not self._minChainLength == 0 and self.chainLength < self._minChainLength:
			self._message = 'Chain is shorter than min chain length (found %d; requires %d).' % (self.chainLength, self._minChainLength)
			return(False)

		if not self._maxChainLength == 0 and self.chainLength > self._maxChainLength:
			self._message = 'Chain is longer than max chain length (found %d; requires %d).' % (self.chainLength, self._maxChainLength)
			return(False)

		return( True )

	## ----------------------------------------------------------------------
	## properties
	@property ## readonly
	def debug(self):
		## Blake Stone, anyone? God I'm old.
		result = True if mc.optionVar(q='DEBUGLEVEL1') else False
		return(result)

	@property ## readonly
	def chainLength(self):
		return len(self.chain)

	@property ## readonly
	def root(self):
		if self.chainLength:
			return(self.chain[0])
		else:
			return(None)


	## ----------------------------------------------------------------------
	## utility functions
	def addModuleAttr(self, *args):
		if self.module is None:
			raise ModuleBaseException('Module is not created.')

		oblist = utils.makeList(args)
		for ob in oblist:
			if not ob.hasAttr('module'):
				ob.addAttr('module', at='message')
			self.module.message >> ob.module

	def calculateSide(self):
		if self.root is None:
			raise ModuleBaseException('calculateSide: no root joint.')

		side = self.getParam('side', None) or utils.determineSide(self.root)
		data = { 'type':'enum', 'enumName':'cn:lf:rt','value':side }
		self.setParam('side', **data)

	def connectChains(self, *args, **kwargs):
		## pass in the roots to connect
		## arguments to args are expected to be lists or tuples

		chains = []
		for arg in args:
			if isinstance(arg, list) or isinstance(arg, tuple):
				chains.append(utils.makeList(arg))
				root = chains[-1][0].getParent()
				if not root.type() == 'transform' or not root.endswith('_rigRoot'):
					raise ModuleBaseException('connectChains: Passed in chain has no rig root.')
			else:
				raise ModuleBaseException('connectChains: Only lists of joints may be passed in.')

		if len(chains) < 2:
			raise ModuleBaseException('connectChains: need at least two chain roots.')

		targetChain = chains.pop(-1)

		if len(chains) == 1:
			## direct connection
			for source, target in zip(chains[0], targetChain ):
				for attr in 'translate','rotate','scale':
					for axis in 'XYZ':
						source.attr(attr+axis) >> target.attr(attr+axis)

			## because we checked earlier the rigRoots should be present at this point
			sourceRoot = chains[0][0].getParent()
			targetRoot = targetChain[0].getParent()

			pm.parentConstraint(sourceRoot, targetRoot, mo=True)
			pm.scaleConstraint(sourceRoot, targetRoot, mo=True)

		else:
			raise NotImplementedError("Multiple chains aren't finished yet, sorry.")

	def constrain(self, *args, **kwargs):
		cType = kwargs.pop('type', None)

		## I want to be able to provide more than the standard Maya constraints in the
		## at some point, while also offering the module creator the ease of use of specifying 
		## names through these strings if the system is ported to another DCC in the future.
		validConstraints = ['point','orient','pointorient','parent','normal','axis','scale']

		if not cType in validConstraints:
			raise ValueError('constraint type invalid -- must be one of ' ', '.join(validConstraints) + '.')

		oblist = utils.makeList(args)

		results = []
		if cType == 'point' or cType == 'pointorient':
			results.append( pm.pointConstraint(*oblist, **kwargs) )
		elif  cType == 'orient' or cType == 'pointorient':
			results.append( pm.orientConstraint(*oblist, **kwargs) )
		elif cType == 'parent':
			results.append( pm.parentConstraint(*oblist, **kwargs) )
		elif cType == 'scale':
			results.append( pm.scaleConstraint(*oblist, **kwargs) )
		else:
			raise NotImplementedError('Constraint type not yet implemented.')

		if len(results) == 1:
			return(results[0])
		else:
			return(results)

	def createControl(self, category, name, target=None, constrain=None, **kwargs):
		data = self.loadControllerParams(category)

		data['name'] = self['token']+"__"+name+"_#s_#d_CON"

		zero, con = utils.createControl(target, **data)[0]
		pm.parent(zero, self.controls)

		if constrain is not None and target is not None:
			if not (isinstance(constrain, tuple) or isinstance(constrain, list)):
				constrain = [constrain]
			for cType in constrain:
				self.constrain(con, target, type=cType, mo=True)

		self._controllers[category].append(con)
		self._controllerZeros[category].append(zero)

		## this is for introspection
		utils.setAttrSpecial(con, 'con_index', len(self._controllers[category])-1 , channelBox=False)
		
		##!FIXME: setAttrSpecial's channelBox flag
		con.con_index.set(k=False, cb=False)
		con.con_index.lock()

		return(con)

	def createControllerParams(self):
		for controlType in self._controllerCategories:
			params = [
				{ 'name':'%sControllerType' % controlType, 'type':'string', 'value':self._defaultControllerType, },
				{ 'name':'%sControllerColor' % controlType, 'type':'enum', 'enumName':utils.colors.enumNames(), 'value':self._defaultControllerColor, },
				{ 'name':'%sControllerAddSub' % controlType, 'type':'bool', 'value':False, },
				{ 'name':'%sControllerSubColor' % controlType, 'type':'enum', 'enumName':utils.colors.enumNames(), 'value':self._defaultControllerSubColor, },
				{ 'name':'%sControllerScale' % controlType, 'type':'float', 'value':1.0, 'min':0.1 },
				{ 'name':'%sControllerSubScale' % controlType, 'type':'float', 'value':0.9, 'min':0.1 },
				{ 'name':'%sControllerTranslation' % controlType, 'type':'float3', 'value':(0,0,0) },
				{ 'name':'%sControllerRotation' % controlType, 'type':'float3', 'value':(0,0,0) },
				{ 'name':'%sControllerRotateOrder' % controlType, 'type':'enum', 'enumName':'xyz:yzx:zxy:xzy:yxz:zyx', 'value':self._defaultRotationOrder },
				{ 'name':'%sControllerAim' % controlType, 'type':'enum', 'enumName':'x:y:z:-x:-y:-z', 'value':'x' },
				{ 'name':'%sControllerUp' % controlType, 'type':'enum', 'enumName':'x:y:z:-x:-y:-z', 'value':'y' },
			]

			for param in params:
				name = param.pop('name')
				self.setParam(name, preserveValue=True, **param)

	def createModule(self):
		moduleName = self.makeName('#t_#s_MODULE', upper=True)
		if pm.objExists(moduleName):
			raise ModuleBaseException('Cannot create module %s: already exists.' % moduleName)

		self.module = pm.createNode('transform', name=moduleName)
		utils.snap(self.module, self.root)
		self.module.addAttr('nodes', at='float', multi=True)

		for groupName in 'controls','rig','extras':
			group = pm.createNode( 'transform', name='_'.join([moduleName, groupName]) )
			utils.snap(group, self.module)
			pm.parent(group, self.module)

		controls, rig, extras = self.module.getChildren()
		self.controls = controls
		self.rig = rig
		self.extras = extras

		self.extras.inheritsTransform.set(0)

		## addModuleAttr adds a message connection to each node in the module
		## this way, you can find the module from any node which belongs to it
		self.addModuleAttr(self.chain)
		self.addModuleAttr(self.controls, self.rig, self.extras)

		## moduleConnect goes the opposite direction: all nodes have a 
		## connection to the module's nodes attribute so that all
		## required nodes can be found for removal and rebuilds

		self.moduleConnect(self.controls, self.rig, self.extras)

		## for all other introspection, setAttrSpecial does message
		## connections.  Here we're not using a prefix.
		utils.setAttrSpecial(self.module, 'controls', self.controls)
		utils.setAttrSpecial(self.module, 'rig', self.rig)
		utils.setAttrSpecial(self.module, 'extras', self.extras)
		utils.setAttrSpecial(self.module, 'chain', self.chain, multi=True)

		for item in self.rig, self.extras:
			item.v.set(0)

		## create default inputs
		## in mose cases you won't need more than this, but
		## the machinery is there for adding extras as needed
		if self._usesRoot:
			self.registerInput('root')
		if self._usesGoal:
			self.registerInput('goal')

	def createJoint(self, name, target=None):
		name = utils.makeName(name)
		joint = pm.createNode('joint', name=name)
		if target is not None:
			utils.snap(joint, target)
		return( joint )

	def createRigChain(self, prefix='RIG', radius=1.0):
		if self.chain is None or len(self.chain) == 0:
			## probably don't need this error check at this point, but ...
			raise ModuleBaseException('createRigChain: no source chain.')

		radius = 0.01 if radius < 0.01 else radius

		rigChain = []
		for item in self.chain:
			name = '_'.join([prefix, str(item)])
			joint = self.createJoint(name, item)
			if len(rigChain):
				pm.parent(joint, rigChain[-1])
			joint.radius.set(radius)
			rigChain.append(joint)

		rigChainRoot = utils.addRigRoot(rigChain[0])
		pm.parent(rigChainRoot, self.rig)

		pm.makeIdentity(rigChain, a=True, r=True, s=True)

		self.segmentScaleCompensateDisable( rigChain )

		return(rigChain)

	def getParam(self, param, defaultValue=None):
		result = utils.getAttrSpecial(self.root, param, defaultValue, prefix=PARAM_PREFIX)
		return(result)

	def loadControllerParams(self, category):
		data = {
			'type': 		self.getParam('%sControllerType' % category),
			'color': 		self.getParam('%sControllerColor' % category),
			'subColor': 	self.getParam('%sControllerSubColor' % category),
			'scale': 		self.getParam('%sControllerScale' % category),
			'subScale': 	self.getParam('%sControllerSubScale' % category),
			'aim': 			self.getParam('%sControllerAim' % category),
			'up': 			self.getParam('%sControllerUp' % category),
			'rotateOrder': 	self.getParam('%sControllerRotateOrder' % category),
			'translation': 	self.getParam('%sControllerTranslation' % category),
			'rotation': 	self.getParam('%sControllerRotation' % category),
		}

		return(data)

	def makeName(self, name, **kwargs):
		result = utils.makeName(name, token=self['token'], side=self['side'], **kwargs)
		return(result)

	def moduleConnect(self, *args):
		utils.setAttrSpecial( self.module, 'nodes', args, multi=True, append=True )

	def popState(self):
		pass

	def pushState(self):
		pass

	def registerControllerCategory(self, key):
		self._controllerCategories.append(key)
		self._controllers[key] = []
		self._controllerZeros[key] = []

	def registerInput(self, key):
		key = key.lower()
		group = pm.createNode('transform', name=self.makeName("#t_"+key+"_#s_#d_INPUT", upper=True))
		utils.snap(group, self.module)
		pm.parent(group, self.module)
		utils.addZero(group)
		self._inputs[key] = group

		## allow the input to be picked up in the same 
		## manner as the other module params

		self.setParam(key+"Input", group)

		## root is a special input
		## when registered, set it up to move the controls group
		if key == 'root':
			self.constrain(group, self.controls, type='parent', mo=True)
			self.constrain(group, self.controls, type='scale', mo=True)

	def segmentScaleCompensateDisable(self, *args):
		oblist = utils.makeList(args, type='joint')
		for item in oblist:
			item.segmentScaleCompensate.set(False)

	def segmentScaleCompensateEnable(self, *args):
		oblist = utils.makeList(args, type='joint')
		for item in oblist:
			item.segmentScaleCompensate.set(True)

	def setParam(self, param, value, **kwargs):
		if self.debug:
			print(">> Setting Param: %s (value %s)" % (param, str(value)))

		utils.setAttrSpecial(self.root, param, value, prefix=PARAM_PREFIX, **kwargs)











