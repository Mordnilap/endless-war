import asyncio
import random

import ewcfg
import ewutils
import ewrolemgr

from ew import EwUser

class EwDungeonScene:

	# The text sent when a scene starts
	text = ""

	# Whether or not the dungeon is active
	dungeon_state = True

	# Where the scene is taking place
	poi = None

	# life state to assign for this scene
	life_state = None

	# Commands that can be used in a scene, and what scene ID that leads to
	options = {}

	def __init__(
			self,
			text="",
			dungeon_state=True,
			options={},
			poi=None,
			life_state=None,
	):
		self.text = text
		self.dungeon_state = dungeon_state
		self.options = options
		self.poi = poi
		self.life_state = life_state


# maps users to where they are in the tutorial
user_to_tutorial_state = {}

class EwGamestate():
	#server id, duh
	id_server = -1

	#name of the state
	id_state = ""

	#setting of the state, on or off
	bit = True

	#additional value for unique states
	value = ""

	def __init__(
			self,
			 id_state = None,
			 id_server = None
			):

		if id_server is not None and id_state is not None:
			self.id_server = id_server
			self.id_state = id_state
			try:
				data = ewutils.execute_sql_query("SELECT {col_bit}, {col_value} FROM gamestates WHERE {id_server} = %s AND {id_state} = %s".format(

						id_state = ewcfg.col_id_state,
						id_server = ewcfg.col_id_server,
						col_bit = ewcfg.col_bit,
						col_value = ewcfg.col_value
					),(
						self.id_server,
						self.id_state
					))
				# Retrieve data if the object was found
				if len(data) > 0:
					self.id_state = id_state
					self.bit = data[0][0]
					self.value = data[0][1]
				else:
					self.bit = None

			except:
				ewutils.logMsg("Failed to retrieve gamestate {} from database.".format(self.id_state))
	def persist(self):
		ewutils.execute_sql_query(
			"REPLACE INTO gamestates ({id_server}, {id_state},  {col_bit}, {col_value}) VALUES (%s, %s, %s, %s)".format(
				id_server=ewcfg.col_id_server,
				id_state = ewcfg.col_id_state,
				col_bit=ewcfg.col_bit,
				col_value=ewcfg.col_value
			), (
				self.id_server,
				self.id_state,
				self.bit,
				self.value
			))


def format_tutorial_response(scene):
	response = scene.text
	if scene.dungeon_state:
		response += "\n\nWhat do you do?\n\n**>options: "
		options = []
		for path in scene.options.keys():
			options.append("{}{}".format(ewcfg.cmd_prefix, path))
		response += ewutils.formatNiceList(names = options, conjunction = "or")
		response += "**"

	return response

async def begin_tutorial(member):
	user_data = EwUser(member = member)
	user_to_tutorial_state[user_data.id_user] = 0
	
	scene = ewcfg.dungeon_tutorial[0]

	if scene.poi != None:
		user_data.poi = scene.poi
	if scene.life_state != None:
		user_data.life_state = scene.life_state

	user_data.persist()

	await ewrolemgr.updateRoles(client = ewutils.get_client(), member = member)

	response = format_tutorial_response(scene)
	poi_def = ewcfg.id_to_poi.get(user_data.poi)
	channels = [poi_def.channel]
	return await ewutils.post_in_channels(member.guild.id, ewutils.formatMessage(member, response), channels)
	


async def tutorial_cmd(cmd):
	user_data = EwUser(member = cmd.message.author)
	client = cmd.client

	if user_data.poi not in ewcfg.tutorial_pois:
		return

	if user_data.id_user not in user_to_tutorial_state:
		return await begin_tutorial(cmd.message.author)
	
	tutorial_state = user_to_tutorial_state.get(user_data.id_user)

	tutorial_scene = ewcfg.dungeon_tutorial[tutorial_state]

	cmd_content = cmd.message.content[1:].lower()
	
	# Administrators can skip the tutorial
	if cmd_content == "skiptutorial" and cmd.message.author.guild_permissions.administrator:
		new_state = 20
		user_to_tutorial_state[user_data.id_user] = new_state

		scene = ewcfg.dungeon_tutorial[new_state]

		if scene.poi != None:
			user_data.poi = scene.poi

		if scene.life_state != None:
			user_data.life_state = scene.life_state

		user_data.persist()

		await ewrolemgr.updateRoles(client=cmd.client, member=cmd.message.author)

		response = format_tutorial_response(scene)

		poi_def = ewcfg.id_to_poi.get(user_data.poi)
		channels = [poi_def.channel]
		return await ewutils.post_in_channels(cmd.guild.id, ewutils.formatMessage(cmd.message.author, response), channels)

	if cmd_content in tutorial_scene.options:
		new_state = tutorial_scene.options.get(cmd_content)
		user_to_tutorial_state[user_data.id_user] = new_state
			
		scene = ewcfg.dungeon_tutorial[new_state]

		if scene.poi != None:
			user_data.poi = scene.poi

		if scene.life_state != None:
			user_data.life_state = scene.life_state

		user_data.persist()

		await ewrolemgr.updateRoles(client = cmd.client, member = cmd.message.author)

		response = format_tutorial_response(scene)

		poi_def = ewcfg.id_to_poi.get(user_data.poi)
		channels = [poi_def.channel]
		return await ewutils.post_in_channels(cmd.guild.id, ewutils.formatMessage(cmd.message.author, response), channels)


	else:
		""" couldn't process the command. bail out!! """
		""" bot rule 0: be cute """
		randint = random.randint(1,3)
		msg_mistake = "ENDLESS WAR is growing frustrated."
		if randint == 2:
			msg_mistake = "ENDLESS WAR denies you his favor."
		elif randint == 3:
			msg_mistake = "ENDLESS WAR pays you no mind."

		msg = await ewutils.send_message(client, cmd.message.channel, msg_mistake)
		await asyncio.sleep(2)
		try:
			await msg.delete()
			pass
		except:
			pass

		# response = format_tutorial_response(tutorial_scene)
		# return await ewutils.send_message(client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
		return