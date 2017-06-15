from math import sin, cos
import sys
import time
from direct.showbase.ShowBase import ShowBase

from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import Vec3
from panda3d.core import Vec4
from panda3d.core import Point3
from panda3d.core import BitMask32
from panda3d.core import NodePath
from panda3d.core import PandaNode

from panda3d.bullet import BulletWorld
from panda3d.bullet import BulletHelper
from panda3d.bullet import BulletPlaneShape
from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletDebugNode
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletCapsuleShape
from panda3d.bullet import BulletCharacterControllerNode
from panda3d.bullet import BulletHeightfieldShape
from panda3d.bullet import BulletTriangleMesh
from panda3d.bullet import BulletTriangleMeshShape
from panda3d.bullet import BulletSoftBodyNode
from panda3d.bullet import BulletSoftBodyConfig
from panda3d.bullet import ZUp

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import PandaNode, NodePath, Camera, TextNode
from direct.interval.IntervalGlobal import *

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(0.08, -pos - 0.04), align=TextNode.ALeft)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), scale=.07,
                        parent=base.a2dBottomRight, align=TextNode.ARight,
                        pos=(-0.1, 0.09), shadow=(0, 0, 0, 1))


class CharacterController(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.setupLights()
        # Input
        self.accept('escape', self.doExit)
        self.accept('r', self.doReset)
        self.accept('f3', self.toggleDebug)
        self.accept('space', self.doJump)
	self.accept("q", self.setKey, ["cam-left", True])
	self.accept("e", self.setKey, ["cam-right", True])
	self.accept("q-up", self.setKey, ["cam-left", False])
	self.accept("e-up", self.setKey, ["cam-right", False])

        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('turnLeft', 'a')
        inputState.watchWithModifiers('turnRight', 'd')

        # Task
        taskMgr.add(self.update, 'updateWorld')

        self.setup()
        base.setBackgroundColor(0.1, 0.1, 0.8, 1)
        base.setFrameRateMeter(True)
        base.disableMouse()
        base.camera.setPos(self.characterNP.getPos()+4)
        base.camera.setHpr(self.characterNP.getHpr())
        base.camera.lookAt(self.characterNP)
        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
		
		# Game state variables
        self.isMoving = False
	self.tokensCount = 0
	self.lifeCount = 2
	# OnscreenText object to show Start and Finish game
	self.textObject = OnscreenText(text = 'Lets Go!!!', pos = (0, 0), scale = 0.1)
	
	# Post the instructions
	self.title = addTitle("TIME: 00:00")
	self.inst1 = addInstructions(0.06, "LIFE: "+ str(self.lifeCount))
	self.inst2 = addInstructions(0.12, "TOKEN: "+ str(self.tokensCount))
	
	self.startTime = globalClock.getFrameTime()

	# This is used to store which keys are currently pressed.
	self.keyMap = {"cam-left": 0, "cam-right": 0}
	
	# Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value	
	
    def doExit(self):
        self.cleanup()
        sys.exit(1)

    def doReset(self):
        self.cleanup()
        self.setup()

    def toggleDebug(self):
        if self.debugNP.isHidden():
            self.debugNP.show()
        else:
            self.debugNP.hide()

    def doJump(self):
		self.character.setMaxJumpHeight(5.0)
		self.character.setJumpSpeed(8.0)
		self.character.doJump()
		self.actorNP.pose("jump", 2)

    def processInput(self, dt):
        speed = Vec3(0, 0, 0)
        omega = 0.0

        if inputState.isSet('forward'): speed.setY( 3.0)
        if inputState.isSet('reverse'): speed.setY(-3.0)
        if inputState.isSet('left'):    speed.setX(-3.0)
        if inputState.isSet('right'):   speed.setX( 3.0)
        if inputState.isSet('turnLeft'):  omega =  120.0
        if inputState.isSet('turnRight'): omega = -120.0
		
	if (inputState.isSet('forward')!=0) or (inputState.isSet('reverse')!=0) or (inputState.isSet('left')!=0) or (inputState.isSet('right')!=0):
            if self.isMoving is False:
                self.actorNP.loop("walk")
                self.isMoving = True
        else:
            if self.isMoving:
                self.actorNP.stop()
                self.isMoving = False


        self.character.setAngularMovement(omega)
        self.character.setLinearMovement(speed, True)

    def update(self, task):
        dt = globalClock.getDt()
        self.processInput(dt)
        self.world.doPhysics(dt, 4, 1./240.)
		
	if self.keyMap["cam-left"]:
		base.camera.setX(base.camera, -20 * dt)
	if self.keyMap["cam-right"]:
		base.camera.setX(base.camera, +20 * dt)
		
	# Game timer
	nowTime = globalClock.getFrameTime() - self.startTime
	self.gameTimer = int(60-round( nowTime ))
	if int(round( nowTime )) == 2:
		self.textObject.setText("")
	self.title.setText("TIME: "+str (self.gameTimer))
        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.
        camvec = self.characterNP.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 10.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-10))
            camdist = 10.0
        if (camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - camvec*(5-camdist))
            camdist = 5.0

        self.floater.setPos(self.characterNP.getPos())
        self.floater.setZ(self.characterNP.getZ() + 2.0)
        base.camera.lookAt(self.floater)
	
	# Game end conditions
	if self.lifeCount == 0 or self.gameTimer == 0:
		self.textObject.setText("YOU LOSE!!!")
		self.actorNP.pose("die", 2)
	
	# Game Completion
	distanceToGoal =  self.panda.getPos() - self.characterNP.getPos()
	if distanceToGoal.length() < 1:
		self.panda.loop("walk")
		self.textObject.setText("GAMEOVER!")
		
	
	# If Character fell logic
	if self.characterNP.getZ() < 1:
		print str(self.characterNP.getZ())
		self.lifeCount = self.lifeCount - 1
		self.tokensCount = 0
		self.inst2.setText("TOKEN: "+ str(self.tokensCount))
		self.inst1.setText("LIFE: "+ str(self.lifeCount))
		self.actorNP.pose("die", 2)
		self.characterNP.setPos(0, 0, 10)
	
	# Collecting tokens logic
	for token in render.findAllMatches("**/=token"):
		distance =  token.getPos() - self.characterNP.getPos()
		if (distance.length() < 1.0):
				self.tokensCount = self.tokensCount + 1
				self.inst2.setText("TOKEN: "+ str(self.tokensCount))
				if self.tokensCount == 3:
					self.lifeCount = self.lifeCount + 1
					self.tokensCount = 0
					self.inst2.setText("TOKEN: "+ str(self.tokensCount))
					self.inst1.setText("LIFE: "+ str(self.lifeCount))
				print "Reached Token with distance: " + str(distance) + " COUNT: " + str(self.tokensCount) + " LIFE: " + str(self.lifeCount)
				token.removeNode()
				

        return task.cont

    def cleanup(self):
        self.world = None
        self.render.removeNode()

    def setupLights(self):
        # Light
        alight = AmbientLight('ambientLight')
        alight.setColor(Vec4(0.5, 0.5, 0.5, 1))
        alightNP = render.attachNewNode(alight)

        dlight = DirectionalLight('directionalLight')
        dlight.setDirection(Vec3(1, 1, -1))
        dlight.setColor(Vec4(0.7, 0.7, 0.7, 1))
        dlightNP = render.attachNewNode(dlight)

        self.render.clearLight()
        self.render.setLight(alightNP)
        self.render.setLight(dlightNP)

    def setup(self):

        # World
        self.debugNP = self.render.attachNewNode(BulletDebugNode('Debug'))
        self.debugNP.hide()

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.world.setDebugNode(self.debugNP.node())

        # Floor
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        floorNP = self.render.attachNewNode(BulletRigidBodyNode('Floor'))
        floorNP.node().addShape(shape)
        floorNP.setPos(0, 0, 0)
        floorNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(floorNP.node())
	self.environ = loader.loadModel('models/environment')
	self.environ.reparentTo(floorNP)

	# Stair
	origin = Point3(2, 0, 0)
	size = Vec3(4, 4.75, 0.5)
	shape = BulletBoxShape(size * 0.55)
	for i in range(15):
		
		pos = origin*i + size * i
		pos.setY(0)
		pos.setZ(4)
		stairNP = self.render.attachNewNode(BulletRigidBodyNode('Stair%i' % i))
		stairNP.node().addShape(shape)
		stairNP.setPos(pos)
		stairNP.setCollideMask(BitMask32.allOn())
			
		if i > 0 and i != 14:
			if i%2 != 0:
				# Rotating stairs
				StairHprInterval1 = stairNP.hprInterval(2, Point3(0, 0, 0),startHpr=Point3(0, 0, 0))
				StairHprInterval2 = stairNP.hprInterval(2, Point3(0, 0, 0),startHpr=Point3(360, 0, 0))
				self.StairPace1 = Sequence(StairHprInterval1,StairHprInterval2)
				self.StairPace1.loop()
				
			if i%2 == 0 and i%3 != 0:
				# Up-down motion stairs
				StairsPosInterval1 = stairNP.posInterval(3, Point3(pos.getX(),pos.getY(),pos.getZ()-2),startPos=Point3(pos.getX(),pos.getY(),pos.getZ()+2))
				StairsPosInterval2 = stairNP.posInterval(3, Point3(pos.getX(),pos.getY(),pos.getZ()+2),startPos=Point3(pos.getX(),pos.getY(),pos.getZ()-2))
				self.StairPace2 = Sequence(StairsPosInterval1,StairsPosInterval2)
				self.StairPace2.loop()
			
			if i%2 == 0 and i%3 == 0:
				# Side to side motion stairs
				StairsPosInterval1 = stairNP.posInterval(3, Point3(pos.getX(),pos.getY()-4,pos.getZ()),startPos=Point3(pos.getX(),pos.getY()+4,pos.getZ()))
				StairsPosInterval2 = stairNP.posInterval(3, Point3(pos.getX(),pos.getY()+4,pos.getZ()),startPos=Point3(pos.getX(),pos.getY()-4,pos.getZ()))
				self.StairPace2 = Sequence(StairsPosInterval1,StairsPosInterval2)
				self.StairPace2.loop()

		modelNP = loader.loadModel('models/stone-cube/stone.egg')
		modelNP.reparentTo(stairNP)
		modelNP.setPos(0, 0, 0)
		modelNP.setScale(size)
		
		self.world.attachRigidBody(stairNP.node())
		
		# panda character
		if i == 14:
			self.panda = Actor("models/panda-model", {"walk": "models/panda-walk4"})
			self.panda.reparentTo(render)
			self.panda.setScale(0.002, 0.002, 0.002)
			self.panda.setPos(pos.getX(),pos.getY(),pos.getZ()+0.5)
		
		if i%2 != 0:
			TokenModel = self.loader.loadModel('models/smiley')
			TokenModel.reparentTo(self.render)
			
			TokenModel.setPos(pos.getX(),pos.getY(),pos.getZ()+1)
			TokenModel.setScale(0.6)
			TokenModel.setTag("token",str(i))
		
        # Character
        h = 1.75
        w = 0.4
        shape = BulletCapsuleShape(w, h - 2 * w, ZUp)

        self.character = BulletCharacterControllerNode(shape, 0.4, 'Player')
        #self.character.setMass(1.0)
        self.characterNP = self.render.attachNewNode(self.character)
        self.characterNP.setPos(0, 0, 14)
        self.characterNP.setH(45)
        self.characterNP.setCollideMask(BitMask32.allOn())
        self.world.attachCharacter(self.character)
		# Special thanks to the creator of LEGO Characters "Lewis Chen"
        self.actorNP = Actor('models/Voltage/Voltage.egg', {
						 'die'	: 'models/Voltage/Voltage-FallbackGetup.egg',
                         'walk' : 'models/Voltage/Voltage-walk.egg',
                         'jump' : 'models/Voltage/Voltage-jump.egg'})

        self.actorNP.reparentTo(self.characterNP)
        self.actorNP.setScale(0.3048)
        self.actorNP.setH(180)
        self.actorNP.setPos(0, 0, 0.35)

game = CharacterController()
game.run()
