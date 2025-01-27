import random
import time

import ewcfg
import ewitem
import ewutils

from ew import EwUser

"""
	Smelting Recipe Model Object
"""

class EwSmeltingRecipe:
	# The proper name of the recipe.
	id_recipe = ""

	# The string name of the recipe.
	str_name = ""

	# A list of alternative names.
	alias = []

	# The ingredients for the recipe, by str_name of the object.
	ingredients = []

	# The product(s) created by the recipe, A tuple of the item type (it_food, it_cosmetic, etc) and item_props.
	products = []

	def __init__(
		self,
		id_recipe="",
		str_name="",
		alias = [],
		ingredients = [],
		products = [],
	):
		self.id_recipe = id_recipe
		self.str_name = str_name
		self.alias = alias
		self.ingredients = ingredients
		self.products = products

# Smelting command. It's like other games call "crafting"... but BETTER and for FREE!!
async def smelt(cmd):
	user_data = EwUser(member = cmd.message.author)
	if user_data.life_state == ewcfg.life_state_shambler:
		response = "You lack the higher brain functions required to {}.".format(cmd.tokens[0])
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))



	# Find sought recipe.
	if cmd.tokens_count > 1:
		sought_result = ewutils.flattenTokenListToString(cmd.tokens[1:])
		found_recipe = ewcfg.smelting_recipe_map.get(sought_result)

		if found_recipe != None:
			if 'soul' in found_recipe.products:
				return await smeltsoul(cmd=cmd)

			# Checks what ingredients are needed to smelt the recipe.
			necessary_ingredients = found_recipe.ingredients
			necessary_ingredients_list = []

			owned_ingredients = []

			# Seeks out the necessary ingredients in your inventory.
			missing_ingredients = []


			for matched_item in necessary_ingredients:
				necessary_items = necessary_ingredients.get(matched_item)
				necessary_str = "{} {}".format(necessary_items, matched_item)
				if necessary_items > 1:
					necessary_str += "s"
				necessary_ingredients_list.append(necessary_str)
				
				sought_items = ewitem.find_item_all(item_search = matched_item, id_user = user_data.id_user, id_server = user_data.id_server)
				missing_items = necessary_items - len(sought_items)
				if missing_items > 0:
					missing_str = "{} {}".format(missing_items, matched_item)
					if missing_items > 1:
						missing_str += "s"
					missing_ingredients.append(missing_str)
				else:
					for i in range(necessary_ingredients.get(matched_item)):
						sought_item = sought_items.pop()
						owned_ingredients.append(sought_item.get('id_item'))

			# If you don't have all the necessary ingredients.
			if len(missing_ingredients) > 0:
				response = "You've never done this before, have you? To smelt {}, you’ll need to combine *{}*.".format(found_recipe.str_name, ewutils.formatNiceList(names = necessary_ingredients_list, conjunction = "and"))

				response += " You are missing *{}*.".format(ewutils.formatNiceList(names = missing_ingredients, conjunction = "and"))

			else:
				# If you try to smelt a random cosmetic, use old smelting code to calculate what your result will be.
				if found_recipe.id_recipe == "coolcosmetic" or found_recipe.id_recipe == "toughcosmetic" or found_recipe.id_recipe == "smartcosmetic" or found_recipe.id_recipe == "beautifulcosmetic" or found_recipe.id_recipe == "cutecosmetic":
					
					if not ewitem.check_inv_capacity(id_server = user_data.id_server, id_user = user_data.id_user, item_type = ewcfg.it_cosmetic):
						response = "You can't carry anymore cosmetic items."
						return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
					
					patrician_rarity = 100
					patrician_smelted = random.randint(1, patrician_rarity)
					patrician = False

					if patrician_smelted <= 5:
						patrician = True

					cosmetics_list = []

					if found_recipe.id_recipe == "toughcosmetic":
						style = ewcfg.style_tough
					elif found_recipe.id_recipe == "smartcosmetic":
						style = ewcfg.style_smart
					elif found_recipe.id_recipe == "beautifulcosmetic":
						style = ewcfg.style_beautiful
					elif found_recipe.id_recipe == "cutecosmetic":
						style = ewcfg.style_cute
					else:
						style = ewcfg.style_cool

					for result in ewcfg.cosmetic_items_list:
						if result.style == style and result.acquisition == ewcfg.acquisition_smelting:
							cosmetics_list.append(result)
						else:
							pass

					items = []

					for cosmetic in cosmetics_list:
						if patrician and cosmetic.rarity == ewcfg.rarity_patrician:
							items.append(cosmetic)
						elif not patrician and cosmetic.rarity == ewcfg.rarity_plebeian:
							items.append(cosmetic)

					item = items[random.randint(0, len(items) - 1)]

					item_props = ewitem.gen_item_props(item)

					ewitem.item_create(
						item_type = item.item_type,
						id_user = cmd.message.author.id,
						id_server = cmd.guild.id,
						item_props = item_props
					)

				# If you're trying to smelt a specific item.
				else:
					possible_results = []

					# Matches the recipe's listed products to actual items.
					for result in ewcfg.smelt_results:
						if hasattr(result, 'id_item'):
							if result.id_item not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_food'):
							if result.id_food not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_cosmetic'):
							if result.id_cosmetic not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_weapon'):
							if result.id_weapon not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
						if hasattr(result, 'id_furniture'):
							if result.id_furniture not in found_recipe.products:
								pass
							else:
								possible_results.append(result)
					# If there are multiple possible products, randomly select one.
					item = random.choice(possible_results)

					if not ewitem.check_inv_capacity(id_server = user_data.id_server, id_user = user_data.id_user, item_type = item.item_type):
						response = "You can't carry any more {}s.".format(item.item_type)
						return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

					item_props = ewitem.gen_item_props(item)

					newitem_id = ewitem.item_create(
						item_type = item.item_type,
						id_user = cmd.message.author.id,
						id_server = cmd.guild.id,
						item_props = item_props
					)


				for id_item in owned_ingredients:
					item_check = ewitem.EwItem(id_item=id_item)
					if item_check.item_props.get('id_cosmetic') != 'soul':
						ewitem.item_delete(id_item = id_item)
					else:
						newitem = ewitem.EwItem(id_item=newitem_id)
						newitem.item_props['target'] = id_item
						newitem.persist()
						ewitem.give_item(id_item=id_item, id_user='soulcraft', id_server=cmd.guild.id)

				name = ""
				if hasattr(item, 'str_name'):
					name = item.str_name
				elif hasattr(item, 'id_weapon'):
					name = item.id_weapon

				response = "You sacrifice your {} to smelt a {}!!".format(ewutils.formatNiceList(names = necessary_ingredients_list, conjunction = "and"), name)

				user_data.persist()

		else:
			response = "There is no recipe by the name."

	else:
		response = "Please specify a desired smelt result."

	# Send response
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

async def smeltsoul(cmd):
	item = ewitem.find_item(item_search="reanimatedcorpse", id_user=cmd.message.author.id, id_server=cmd.guild.id)
	if not item:
		response = "You can't rip a soul out of a nonexistent object."
	else:
		item_obj = ewitem.EwItem(id_item=item.get('id_item'))
		if item_obj.item_props.get('target') != None and item_obj.item_props.get('target') != "":
			targetid = item_obj.item_props.get('target')
			if ewitem.give_item(id_user=cmd.message.author.id, id_item=targetid, id_server=cmd.guild.id):
				response = "You ripped the soul out of the reanimated corpse. It's in mangled bits now."
				ewitem.item_delete(id_item=item.get('id_item'))
			else:
				response = "You reach for the soul in the reanimated corpse, but your hands are full of cosmetics! Get rid of a few, freak."
		else:
			response = "That's not a reanimated corpse. It only looks like one. Get rid of the fake shit and we'll get started."
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

# "wcim", "whatcanimake", "whatmake", "usedfor" command - finds the item the player is asking for and tells them all smelting recipes that use that item 
# added by huck on 9/3/2020
async def find_recipes_by_item(cmd):
	user_data = EwUser(member = cmd.message.author)
	if user_data.life_state == ewcfg.life_state_shambler:
		response = "You lack the higher brain functions required to {}.".format(cmd.tokens[0])
		return await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))
	
	used_recipe = None
	
	# if the player specifies an item name
	if cmd.tokens_count > 1:
		sought_item = ewutils.flattenTokenListToString(cmd.tokens[1:])
		
		# Allow for the use of recipe aliases
		found_recipe = ewcfg.smelting_recipe_map.get(sought_item)
		if found_recipe != None:
			used_recipe = found_recipe.id_recipe

		# item_sought_in_inventory = ewitem.find_item(item_search=sought_item, id_user=cmd.message.author.id, id_server=cmd.guild.id if cmd.guild is not None else None)
		makes_sought_item = []
		uses_sought_item = []
		
		# if the item name is an item in the player's inventory, we're assuming that the player is looking up information about this item specifically.
		# if item_sought_in_inventory is not None:
			# sought_item = item_sought_in_inventory.id_item
			# print(item_sought_in_inventory['item_def'])
		# man i could NOT get this to work . maybe another day
		
		
		# finds the recipes in questions that applys
		for name in ewcfg.recipe_names:
			# find recipes that this item is used as an ingredient in
			if ewcfg.smelting_recipe_map[name].ingredients.get(sought_item) is not None:
				uses_sought_item.append(name)
				
			# find recipes used to create this item
			elif sought_item in ewcfg.smelting_recipe_map[name].products:
				makes_sought_item.append(ewcfg.smelting_recipe_map[name])
			
			# finds recipes based on possible recipe aliases
			elif used_recipe in ewcfg.smelting_recipe_map[name].products:
				makes_sought_item.append(ewcfg.smelting_recipe_map[name])
		
		# zero matches in either of the above:
		if len(makes_sought_item) < 1 and len(uses_sought_item) < 1:
			response = "No recipes found for *{}*.".format(sought_item)

		#adds the recipe list to a response
		else:
			response = "\n"
			number_recipe = 1
			list_length = len(makes_sought_item)
			for item in makes_sought_item:
				if (item.id_recipe == "toughcosmetic" and ewcfg.cosmetic_map[sought_item].style != ewcfg.style_tough
				or item.id_recipe == "smartcosmetic" and ewcfg.cosmetic_map[sought_item].style != ewcfg.style_smart
				or item.id_recipe == "beautifulcosmetic" and ewcfg.cosmetic_map[sought_item].style != ewcfg.style_beautiful
				or item.id_recipe == "cutecosmetic" and ewcfg.cosmetic_map[sought_item].style != ewcfg.style_cute
				or item.id_recipe == "coolcosmetic" and ewcfg.cosmetic_map[sought_item].style != ewcfg.style_cool):
					list_length -= 1
					continue
				else:
					# formats items in form "# item" (like "1 poudrin" or whatever)
					ingredients_list = []
					ingredient_strings = []
					for ingredient in item.ingredients:
						ingredient_strings.append("{} {}".format(item.ingredients.get(ingredient), ingredient))
				
					if number_recipe == 1:
						response += "To smelt this item, you'll need *{}*. ({})\n".format(ewutils.formatNiceList(names = ingredient_strings, conjunction = "and"), item.id_recipe)
					else:
						response += "Alternatively, to smelt this item, you'll need *{}*. ({})\n".format(ewutils.formatNiceList(names = ingredient_strings, conjunction = "and"), item.id_recipe)
					number_recipe += 1
					
			if len(uses_sought_item) > 0:
				response += "This item can be used to smelt *{}*.".format(ewutils.formatNiceList(names = uses_sought_item, conjunction = "and"))
	
	
	
	# if the player doesnt specify a 2nd argument
	else:
		response = "Please specify an item you would like to look up usage for."
	
	
	
	# send response to player
	await ewutils.send_message(cmd.client, cmd.message.channel, ewutils.formatMessage(cmd.message.author, response))

def unwrap(id_user = None, id_server = None, item = None):
	response = "You eagerly rip open a pack of Secreatures™ trading cards!!"
	ewitem.item_delete(item.id_item)
	slimexodia = False

	slimexodia_chance = 1 / 1000

	if random.random() < slimexodia_chance:
		slimexodia = True

	if slimexodia == True:
		# If there are multiple possible products, randomly select one.
		slimexodia_item = random.choice(ewcfg.slimexodia_parts)

		response += " There’s a single holographic card poking out of the swathes of repeats and late edition cards..."
		response += " ***...What’s this?! It’s the legendary card {}!! If you’re able to collect the remaining pieces of Slimexodia, you might be able to smelt something incomprehensibly powerful!!***".format(slimexodia_item.str_name)

		item_props = ewitem.gen_item_props(slimexodia_item)

		ewitem.item_create(
			item_type = slimexodia_item.item_type,
			id_user = id_user.id,
			id_server = id_server.id,
			item_props = item_props
		)

	else:
		response += " But… it’s mostly just repeats and late edition cards. You toss them away."

	return response

def popcapsule(id_user = None, id_server = None, item = None):
	rarity_roll = random.randrange(10)
	ewitem.item_delete(item.id_item)

	if rarity_roll > 3:
		prank_item = random.choice(ewcfg.prank_items_heinous)
	elif rarity_roll > 0:
		prank_item = random.choice(ewcfg.prank_items_scandalous)
	else:
		prank_item = random.choice(ewcfg.prank_items_forbidden)

	item_props = ewitem.gen_item_props(prank_item)

	prank_item_id = ewitem.item_create(
		item_type=prank_item.item_type,
		id_user=id_user.id,
		id_server=id_server.id,
		item_props=item_props
	)
	
	response = "You pop open the Prank Capsule to reveal a {}! Whoa, sick!!".format(prank_item.str_name)
	
	return response
