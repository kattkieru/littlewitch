from copy import deepcopy

import maya
from maya import cmds as mc
from maya import OpenMaya as om
import pymel.core as pm

## ----------------------------------------------------------------------
'''

	UTILS.PY

	General utility functions.

'''

## ----------------------------------------------------------------------
class UtilsException(Exception):
	pass

## ----------------------------------------------------------------------
class colors(object):
	## I'm leaving out colors that never get used
	grey = 0
	black = 1
	darkgrey = 2
	lightgrey = 3
	darkred = 4
	navy = 5
	blue = 6
	darkgreen = 7
	violet = 8  # live through this
	pink = 9
	brown = 10
	darkbrown = 11
	darkorange = 12
	red = 13
	green = 14
	white = 16
	yellow = 17
	ltblue = 18
	ltgreen = 19
	salmon = 20
	tan = 21
	ltyellow = 22
	purple = 30
	darkpink = 31

	_names = {
		"grey":0,
		"black":1,
		"darkgrey":2,
		"lightgrey":3,
		"darkred":4,
		"navy":5,
		"blue":6,
		"darkgreen":7,
		"violet":8,
		"pink":9,
		"brown":10,
		"darkbrown":11,
		"darkorange":12,
		"red":13,
		"green":14,
		"white":16,
		"yellow":17,
		"lightblue":18,
		"lightgreen":19,
		"salmon":20,
		"tan":21,
		"lightyellow":22,
		"purple":30,
		"darkpink":31,
	}

	@staticmethod
	def allNames():
		return(colors._names.keys())

	@staticmethod
	def enumNames():
		## I tried doing this the smart way and failed, so... this:
		result = ("grey=0:black=1:darkgrey=2:lightgrey=3:darkred=4:" + 
			"navy=5:blue=6:darkgreen=7:violet=8:pink=9:brown=10:" + 
			"darkbrown=11:darkorange=12:red=13:green=14:white=16:" + 
			"yellow=17:lightblue=18:lightgreen=19:salmon=20:" +
			"tan=21:lightyellow=22:purple=30:darkpink=31:")

		return( result )

	@staticmethod
	def indexForColor(color):
		if color in colors._names.keys():
			return(colors._names[color])
		else:
			return(0)

	@staticmethod
	def colorForIndex(index):
		for key, value in colors._names.items():
			if value == index:
				return(key)
		raise ValueError('colors::colorForIndex: index not found.')


## ----------------------------------------------------------------------
## Definitions for different rig controller types
## Controllers are created as D-1 nurbs curves only.
controllerCurves = {
	'box' : [[0, -0.5, 0.5], [0, -0.5, -0.5], [0, 0.5, -0.5], [0, 0.5, 0.5], [0, -0.5, 0.5]],
	'circle': [
		[1.874699728327322e-33, 0.5, -3.061616997868383e-17],
		[-1.1716301013315743e-17, 0.46193976625564337, 0.19134171618254486],
		[-2.1648901405887335e-17, 0.35355339059327373, 0.3535533905932738],
		[-2.8285652807192507e-17, 0.19134171618254486, 0.46193976625564337],
		[-3.061616997868383e-17, -2.4894981252573997e-17, 0.5],
		[-2.8285652807192507e-17, -0.19134171618254492, 0.46193976625564337],
		[-2.164890140588733e-17, -0.35355339059327384, 0.35355339059327373],
		[-1.1716301013315742e-17, -0.4619397662556434, 0.19134171618254484],
		[3.223916797098519e-33, -0.5, -5.265055686820291e-17],
		[1.171630101331575e-17, -0.4619397662556433, -0.19134171618254495],
		[2.1648901405887338e-17, -0.3535533905932737, -0.35355339059327384],
		[2.828565280719251e-17, -0.19134171618254478, -0.4619397662556434],
		[3.061616997868383e-17, 1.0816170809946073e-16, -0.5],
		[2.8285652807192507e-17, 0.191341716182545, -0.4619397662556433],
		[2.1648901405887323e-17, 0.35355339059327384, -0.3535533905932736],
		[1.1716301013315736e-17, 0.46193976625564337, -0.19134171618254472],
		[-1.0022072164332974e-32, 0.4999999999999999, 1.6367285933071856e-16]
	],
}


rotateOrders = {
	'xyz': 0, 
	'yzx': 1, 
	'zxy': 2, 
	'xzy': 3, 
	'yxz': 4, 
	'zyx': 5
}

## ----------------------------------------------------------------------
def addRigRoot(*args):
	oblist = makeList(args, type='joint')

	results = []
	for item in oblist:
		rigRoot = None
		topParent = None

		parent = item.getParent()
		if parent is not None:
			if parent.endswith('__rigRoot'):
				rigRoot = parent
				topParent = rigRoot.getParent()
				if topParent is not None:
					pm.parent(item, topParent)
				else:
					pm.parent(item, w=True)
			else:
				topParent = parent
		
		if not rigRoot:
			rigRoot = pm.createNode('transform', n=item+'__rigRoot')
		snap(rigRoot, item)
		pm.parent(item, rigRoot)

		if topParent is not None:
			pm.parent(rigRoot, topParent)

		results.append(rigRoot)

	if len(results) == 1:
		return(results[0])
	else:
		return(results)


## ----------------------------------------------------------------------
def addZero(*args, **kwargs):
	oblist = makeList(args)

	results = []

	for item in oblist:
		if item.type() == 'joint':
			zero = pm.createNode('transform', n=item+'Zero')
			zero.rotateOrder.set( item.rotateOrder.get() )
			snap(zero, item)
			pm.parent(item, zero)
			results.append(zero)
		elif item.type() == 'transform':
			zero = pm.duplicate(item, rr=True)[0]
			children = zero.getChildren()
			if len(children):
				pm.delete(children)
			zero.rename(item+'Zero')

			for attr in 'trs':
				for axis in 'xyz':
					pAttr = zero.attr(attr+axis)
					pAttr.set(lock=False)
					pAttr.set(k=True)

			pm.parent(item, zero)
			results.append(zero)

	if len(results) == 0:
		return None
	elif len(results) == 1:
		return(results[0])
	else:
		return(results)


## ----------------------------------------------------------------------
def cleanParams(*args, **kwargs):
	prefix = kwargs.get('prefix', None) or kwargs.get('pre', None)
	verbose = kwargs.get('verbose', None) or kwargs.get('v', False)

	oblist = makeList(args)
	
	for item in oblist:
		if verbose:
			print('>> Removing attributes from %s...' % str(item))

		userAttrs = item.listAttr(ud=True)
		if prefix is not None:
			userAttrs = [ x for x in userAttrs if x.count(prefix+"_") ]

		for attr in userAttrs:
			safeDeleteAttr(attr, v=verbose)


## ----------------------------------------------------------------------
def createControl(*args, **kwargs):
	targets = makeList(args)

	if not len(targets):
		## if there are no target objects passed in, put in a blank to
		## force creation of one control
		targets = [ None ]

	## default values
	data = {
		'name':'CONTROL_#s_#d_CON',
		'type':'box',
		'color': colors.green,
		'scale':1.0,
		'aim':'x',
		'up':'y',
		'rotateOrder':'zxy',
		'translation':[0,0,0],
		'rotation':[0,0]
	}

	data.update(**kwargs)

	controls = []
	zeros = []

	for target in targets:
		if not 'side' in data and target is not None:
			data['side'] = determineSide(target)
		else:
			data['side'] = 'cn'

		curve = pm.curve( d=1, p=controllerCurves[data['type']] )
		curve.rename( makeName(data['name'], side=data['side'], upper=True) )
		setColor(curve, data['color'])
		scale = data['scale']
		pm.scale(curve.cv, scale, scale, scale, r=True)

		setAttrSpecial(curve, 'origScale', data['scale'], channelBox=False)

		##!FIXME: Apply aim and up
		setAttrSpecial(curve, 'aim', data['aim'], channelBox=False)
		setAttrSpecial(curve, 'up', data['up'], channelBox=False)

		##!FIXME: apply controller translation and rotation

		## rotate order
		rotateOrder = data['rotateOrder']
		if isinstance(rotateOrder, str) or isinstance(rotateOrder, unicode):
			if not rotateOrder in rotateOrders.keys():
				raise ValueError("rotateOrder must be an integer between 0 and 5 or one of " + ' '.join(rotateOrders.keys()) + '.' )
			rotateOrder = rotateOrders[rotateOrder]
		
		curve.rotateOrder.set( rotateOrder )

		if target is not None:
			snap(curve, target)

		## lockdown
		##!FIXME: only here until the channelBox flag is fixed in setAttrSpecial
		for attr in curve.origScale, curve.aim, curve.up:
			attr.set(k=False, cb=False)
			attr.lock()

		zeros.append( addZero(curve) )
		controls.append( curve )

	return(zip(zeros, controls))


## ----------------------------------------------------------------------
def determineSide(ob):
	centers = [ '_C_','_CN_', '_cn_' ]
	lefts = [ '_L_','_LF_', '_lf_' ]
	rights = [ '_R_','_RT_', '_rt_' ]

	for item in lefts:
		if item in ob:
			return('lf')

	for item in rights:
		if item in ob:
			return('rt')			
	
	return('cn')	


## ----------------------------------------------------------------------
def getAttrSpecial(ob, attr, defaultValue=None, prefix=None):
	if not isinstance(ob, pm.PyNode):
		ob = pm.PyNode(ob)

	attrName = '_'.join([prefix, attr]) if prefix is not None else attr

	if ob.hasAttr(attrName):
		pAttr = ob.attr(attrName)
		if pAttr.type() == 'enum':
			result = pAttr.get(asString=True)
		else:
			result = pAttr.get()
	else:
		result = None

	return(result)

## ----------------------------------------------------------------------
def getParentAttr(ob, pType=None):
	if pType is None:
		raise ValueError('getParentAttr: parent type unspecified.')

	return( getAttrSpecial(ob, pType, None, 'parent') )


## ----------------------------------------------------------------------
def getChain(root, chainList=None):
	'''
	getChain(root, chainList):

	From the specified root, gets the first child hierarchy (the chain). 
	Useful for grabbing entire chains of joints from the root only.

	root: 	The base object to start from; it should be a transform or a subclass
			of a transform.

	chainList:	Used for recursion; do not pass anything in.

	'''

	acceptedTypes = ['transform', 'joint']

	if not isinstance(root, pm.PyNode):
		root = pm.PyNode(root)

	if chainList is None:
		chainList = []

	foundType = 0
	for typ in pm.nodeType(root, inherited=True):
		if typ in acceptedTypes:
			foundType = 1
			break

	if not foundType:
		raise ValueError('getChain: invalid object type (object %s, type %s).' % (root, root.type()) )

	chainList.append(root)

	children = root.getChildren()

	if len(children):
		## we only want the first child
		chainList = getChain(children[0], chainList)

	return(chainList)


## ----------------------------------------------------------------------
def lock(*args, **kwargs):
	oblist = makeList(args)

	lockAll = kwargs.get('all', None) or kwargs.get('a', False)
	t = kwargs.get('translate', None) or kwargs.get('t', False) or lockAll
	r = kwargs.get('rotate', None) or kwargs.get('r', False) or lockAll
	s = kwargs.get('scale', None) or kwargs.get('s', False) or lockAll
	v = kwargs.get('visibility', None) or kwargs.get('v', False) or lockAll

	for item in oblist:
		toLock = []
		if t:
			for axis in 'xyz':
				toLock.append(item.attr('t'+axis))
		if r:
			for axis in 'xyz':
				toLock.append(item.attr('r'+axis))
		if s:
			for axis in 'xyz':
				toLock.append(item.attr('s'+axis))
		if v:
			toLock.append(item.v)

		for attr in toLock:
			attr.set(k=False, cb=False)
			attr.lock()


## ----------------------------------------------------------------------
def makeList(*args, **kwargs):
	'''
	makeList(*args, **kwargs):

	From the *args variable, it creates a list of PyNodes for each existing Maya
	object specified.  If you pass in nested lists of objects, they are flattened
	out. String names are converted to PyNodes. Any identifier that is not found
	in the scene is skipped.

	**kwargs

	obType: type of object to filter for (joint, skinCluster)

	Returns:

	A list containing every object found, or an empty list if nothing is 
	discovered.
	'''

	obType = kwargs.get('type', None) or kwargs.get('typ', None)

	def makeListRecursive(passedArgs, realList=None):
		if realList is None:
			realList = []

		for item in passedArgs:
			if isinstance(item, list) or isinstance(item, tuple):
				makeListRecursive(item, realList)
			else:
				realList.append(item)

		return(realList)

	## only attempt PyNodes at this point, after the above list has been filtered
	objects = [ pm.PyNode(x) for x in makeListRecursive(args) if pm.objExists(x) ]

	## filter by type
	if obType is not None:
		objects = pm.ls(objects, type=obType)

	return(objects)

## ----------------------------------------------------------------------
def makeName(name, token='token', side='cn', upper=False):

	def prettyNum(num):
		if num < 10:
			num = '0' + str(num)
		else:
			num = str(num)
		return(num)

	realName = name.replace('#t', token).replace('#s', side)

	## this bit of code is embarrassing
	index = 1
	if realName.count('#d'):
		tempName = realName.replace('#d', prettyNum(index))
		if upper:
			tempName = tempName.upper()
		while mc.objExists(tempName):
			index += 1
			tempName = realName.replace('#d', prettyNum(index))
			if upper:
				tempName = tempName.upper()

		realName = realName.replace('#d', prettyNum(index))
	
	if upper:
		realName = realName.upper()

	return(realName)


## ----------------------------------------------------------------------
def poseMark(*args):
	##!FIXME: add a prefix to save poses for multiple names
	oblist = makeList(args, type='joint')

	for root in oblist:
		chain = getChain(root)
		for item in chain:
			for attr in [ x for x in item.listAttr(ud=True) if x.count('.default_') ]:
				if attr.getParent() is not None:
					## skip children of compound attributes-- they vanish with their parents
					## and cause an error otherwise
					continue
				pm.deleteAttr(attr)

			worldMat = pm.dt.Matrix(pm.xform(item, q=True, ws=True, matrix=True))
			m = om.MTransformationMatrix( worldMat.asMatrix() )

			scale = item.scale.get()
			rot = pm.dt.Quaternion(m.rotation())
			trans = pm.dt.Vector(m.translation(om.MSpace.kWorld))
			
			setAttrSpecial(item, 'default_scale', scale, type='float3', channelBox=False)
			setAttrSpecial(item, 'default_rotationV', [rot.x, rot.y, rot.z], type='float3', channelBox=False)
			setAttrSpecial(item, 'default_rotationW', rot.w, type='float', channelBox=False)
			setAttrSpecial(item, 'default_translation', trans, channelBox=False)

			##!FIXME: temporary fix until I get the channelBox flag working in setAttrSpecial
			for attr in [ 'default_scale', 'default_rotationV', 'default_rotationW', 'default_translation' ]:
				attr = item.attr(attr)
				attr.set(k=False)
				attr.set(cb=False)
				if attr.isCompound() or attr.isMulti():
					for child in attr.getChildren():
						child.set(k=False)
						child.set(cb=False)


## ----------------------------------------------------------------------
def poseReset(*args):
	oblist = makeList(args, type='joint')

	for item in oblist:
		if item.hasAttr('default_scale'):
			item.scale.set(item.default_scale.get())
		if item.hasAttr('default_translation'):
			trans = item.default_translation.get()
			pm.xform(item, ws=True, t=trans)
		if item.hasAttr('default_rotationV') and item.hasAttr('default_rotationW'):
			## strangely, you can't pass in dt.Vector to dt.Quaternion
			quat_vec = list( item.default_rotationV.get() )
			quat_vec.append( item.default_rotationW.get() )

			quat = pm.dt.Quaternion( *quat_vec )
			euler = quat.asEulerRotation()
			euler.setDisplayUnit('degrees')
			pm.xform(item, ws=True, rotation=(euler.x, euler.y, euler.z))

		parent = item.getParent()
		if parent is not None and parent.type() == 'transform' and parent.endswith('_rigRoot'):
			## reset the rigRoot on the roots of chains
			addRigRoot(item)

## ----------------------------------------------------------------------
def removeModule(*args):
	oblist = makeList(args)

	for ob in oblist:
		if ob.hasAttr('module'):
			module = ob.module.get()
			if module is not None:
				pm.delete(module)

		## remove extra attributes
		for attr in ['module',]:
			safeDeleteAttr(ob+'.'+attr)

		## remove "input" attributes
		for attr in [ x for x in ob.listAttr(ud=True) if x.endswith('Input') ]:
			safeDeleteAttr(attr)

		## make sure it's removed from the automatedBuild lookups
		safeDeleteAttr(ob+".MODULEROOT")

		chain = getChain(ob)
		poseReset(chain)


## ----------------------------------------------------------------------
def removeParentAttr(*args, **kwargs):
	pType = kwargs.get('type', None)

	oblist = makeList(args)
	if len(oblist) < 1:
		raise UtilsException('removeParent: Need to pass one or more valid objects.')

	if pType is None:
		raise ValueError('removeParent: parent type unspecified.')

	for item in oblist:
		safeDeleteAttr( item+'.parent_'+pType )


## ----------------------------------------------------------------------
def safeDeleteAttr(attr, **kwargs):
	if not isinstance(attr, pm.PyNode):
		try:
			attr = pm.PyNode(attr)
		except:
			# raise ValueError('safeDeleteAttr: Attribute does not exist: %s.' % attr)
			return

	## skip deleting child attributes-- it doesn't work and they 
	## vanish with their parents anyway
	if attr.getParent() is None:
		inputs = attr.inputs(plugs=True)
		attr.set(lock=False)

		if len(inputs):
			for inp in inputs:
				inp // attr

		pm.deleteAttr(attr)


## ----------------------------------------------------------------------
def safeGroup(name):
	if pm.objExists(name):
		return(pm.PyNode(name))
	else:
		group = pm.createNode('transform', name=name)
		return(group)


## ----------------------------------------------------------------------
def safeParent(*args, **kwargs):
	world = kwargs.get('world', False) or kwargs.get('w', False)

	oblist = makeList(args)
	if not len(oblist) >= 2:
		raise ValueError('safeParent: Please pass in at least two objects.')

	if world:
		for item in oblist:
			if item.getParent() is not None:
				pm.parent(item, w=True)

	else:
		target = oblist.pop(-1)
		pm.parent(oblist, target)


## ----------------------------------------------------------------------
def setAttrSpecial(ob, attr, value, prefix=None, channelBox=True, 
				preserveValue=False, multi=False, 
				append=False, **kwargs):

	attributeType = kwargs.pop('type', None)

	oldValue = None

	if not isinstance(ob, pm.PyNode):
		ob = pm.PyNode(ob)

	attrName = '_'.join([prefix, attr]) if prefix is not None else attr

	# print("Setting attr: %s (value %s)" % (attrName, str(value)))

	if attributeType is None:
		## try to intelligently guess the type from what's been passed in
		if isinstance(value, list) or isinstance(value, tuple):
			if isinstance(value[0], pm.PyNode):
				attributeType = 'message'
				multi = True
			elif len(value) == 3 and unicode(value[0]).isnumeric():
				attributeType = 'float3'
		elif isinstance(value, pm.dt.Point) or isinstance(value, pm.dt.Vector):
			attributeType = 'float3'
		elif isinstance(value, pm.PyNode) or pm.objExists(value):
			attributeType = 'message'
		elif isinstance(value, unicode) or isinstance(value, str):
			attributeType = 'string'
		elif 'enumName' in kwargs:
			attributeType='enum'
			if value.type() == 'string':
				value = kwargs.get('enumName').split(':').index(value)
		elif value is True or value is False:
			attributeType = 'bool'
		elif unicode(15).isnumeric():
			attributeType = 'float'

	## we have the info-- create the attribute
	attrData = {
		'multi':multi
	}

	if attributeType == 'string':
		attrData['dt'] = 'string'
	else:
		attrData['at'] = attributeType

	attrData.update(kwargs)

	if preserveValue:
		try:
			oldValue = ob.attr(attrName).get()
		except:
			##!FIXME: need that logging function
			pass

	safeDeleteAttr(ob+'.'+attrName)
	ob.addAttr(attrName, **attrData)

	if attributeType == 'float3':
		childData = deepcopy(attrData)
		childData.pop('at')
		for axis in 'XYZ':
			if not ob.hasAttr(attrName+axis):
				ob.addAttr(attrName+axis, p=attrName, at='float', **childData)

		## have to do a second loop because the attribute isn't "finished"
		## and available for edit until all three are created
		for axis in 'XYZ':
			ob.attr(attrName+axis).set(k=False)
			ob.attr(attrName+axis).set(cb=channelBox)

	pAttr = ob.attr(attrName)
	pAttr.set(cb=channelBox)

	if oldValue is not None:
		value = oldValue

	## doing the set down here is better because string attrs seem
	## to have trouble with default values. Also, this lets you
	## set the float3's in one go
	if value is not None:
		if attributeType == 'message':
			if multi:
				objects = []
				if append:
					objects += pAttr.get()
				objects += value

				incoming = pAttr.inputs(plugs=True)
				for plug in incoming:
					pAttr // plug

				pAttr.disconnect()

				for index, item in enumerate(objects):
					item.message >> pAttr[index]
			else:
				incoming = pAttr.inputs(plugs=True)
				for plug in incoming:
					pAttr // plug
				pm.PyNode(value).message >> pAttr
		elif attributeType == 'string':
			## have to convert to string for non-string values
			## or PyMEL kicks up an error
			pAttr.set(str(value))
		else:
			pAttr.set(value)
	
	return(pAttr)


## ----------------------------------------------------------------------
def setColor(*args):
	args = list(args)
	color = args.pop(-1)

	if isinstance(color, str) or isinstance(color, unicode):
		color = colors.indexForColor(color)

	oblist = makeList(args)
	for item in oblist:
		item.overrideEnabled.set(True)
		item.overrideColor.set(color)


## ----------------------------------------------------------------------
def setParentAttr(*args, **kwargs):
	pType = kwargs.get('type', None)

	oblist = makeList(args)
	if len(oblist) < 2:
		raise UtilsException('setParentAttr: Need to pass one or more children and one target object.')

	if pType is None:
		raise ValueError('setParentAttr: parent type unspecified.')

	target = oblist.pop(-1)

	##!FIXME: 	Should this sort through the current list of recognized parents,
	##			or is that left up to the caller?

	##!FIXME:	Should this protect against setting parent attrs on non-root
	##			joints in chains?

	for item in oblist:
		setAttrSpecial( item, pType, target, prefix='parent' )


## ----------------------------------------------------------------------
def snap(*args):
	def snapHelper(item, goal):
		pm.delete(pm.parentConstraint(goal, item))

	oblist = makeList(args)
	target = oblist.pop(-1)

	for item in oblist:
		snapHelper(item, target)




