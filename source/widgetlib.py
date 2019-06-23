#common widgets, so as to easily populate the parts of the GUI that are delegated to other classes

import weakref    #because memory leaks are stupid
import tkinter as tk
import json
import os
from source import common

def center_align_grid_in_frame(frame):
	frame.grid_columnconfigure(0, weight=1)       #the 0th column will be the margin
	frame.grid_columnconfigure(1000, weight=1)    #so I guess technically this just needs to be larger than the number of columns


def right_align_grid_in_frame(frame):
	frame.grid_columnconfigure(0, weight=1)       #the 0th column will be the margin
	frame.grid_columnconfigure(1000, weight=0)    #so I guess technically this just needs to be larger than the number of columns


def leakless_dropdown_trace(object, var_to_trace, fun_to_call):
	#this function will add a "trace" to a particular variable, that is, to allow that variable when changed to call a particular function
	#normally this is not needed except for when things like sprite or game have widgets that they place into the main GUI
	#if this process is not done delicately, then there will be a memory leak
	#so this function handles all the weak references and whatnot in order to make sure that the destructor is correctly applied
	#
	#example: widgetlib.leakless_dropdown_trace(self, "background_selection", "set_background")
	#
	def dropdown_wrapper(this_object):
		def call_desired_function(*args):
			getattr(this_object(),fun_to_call)(getattr(this_object(),var_to_trace).get())
		return call_desired_function
	getattr(object,var_to_trace).trace('w', dropdown_wrapper(weakref.ref(object)))  #when the dropdown is changed, run this function
	dropdown_wrapper(weakref.ref(object))()      #trigger this now to initialize


#this tooltip class modified from
#www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
class ToolTip(object):
	def __init__(self, widget, text='widget info'):
		self.waittime = 500     #miliseconds
		self.wraplength = 180   #pixels
		self.widget = widget
		self.text = text
		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.widget.bind("<ButtonPress>", self.leave)
		self.id = None
		self.tw = None

	def enter(self, event=None):
		self.schedule()

	def leave(self, event=None):
		self.unschedule()
		self.hidetip()

	def schedule(self):
		self.unschedule()
		self.id = self.widget.after(self.waittime, self.showtip)

	def unschedule(self):
		id = self.id
		self.id = None
		if id:
			self.widget.after_cancel(id)

	def showtip(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20
		# creates a toplevel window
		self.tw = tk.Toplevel(self.widget)
		# Leaves only the label and removes the app window
		self.tw.wm_overrideredirect(True)
		self.tw.wm_geometry("+%d+%d" % (x, y))
		label = tk.Label(self.tw, text=self.text, justify='left',
					   background="#ffffff", relief='solid', borderwidth=1,
					   wraplength = self.wraplength)
		label.pack(ipadx=1)

	def hidetip(self):
		tw = self.tw
		self.tw= None
		if tw:
			tw.destroy()

class SpiffyButtons():
	#They are like buttons, except spiffy
	def __init__(self, sprite_object, parent_frame):
		self.DIMENSIONS = {
			"button": {
				"width": 20,
				"height": 20,
				"color.active": "#78C0F8",
				"color.selected": "#C0E0C0"
			},
			"panel": {
				"height_per_button": 30
			}
		}
		self.sprite_object = sprite_object
		self.spiffy_buttons_section = tk.Frame(parent_frame, name="spiffy_buttons")
		right_align_grid_in_frame(self.spiffy_buttons_section)
		self.max_row = 0

	def make_new_group(self, label):
		#TODO: Make new variable (perhaps StringVar?), and hook it in to the sprite object using code placed here or in the next line
		new_group = SpiffyGroup(self, self.max_row, label)
		self.max_row += 1
		return new_group

	def get_panel(self):
		section_height = self.max_row*self.DIMENSIONS["panel"]["height_per_button"]
		return self.spiffy_buttons_section, section_height

class SpiffyGroup():
	#not meant to be used on its own, instead use class SpiffyButtons()
	def __init__(self, parent, row, label):
		self.label = label
		self.default_exists = False
		self.parent = parent
		self.col = 0
		self.row = row

		section_label = tk.Label(self.parent.spiffy_buttons_section, text=label + ':')
		section_label.grid(row=self.row, column=self.col, sticky='E')

		self.col += 1


	def add(self, internal_value_name, image_filename="blank.png"):
		langs = common.get_resource("en.json",os.path.join(self.parent.sprite_object.resource_subpath,"lang"))
		with open(langs) as f:
			langs = json.load(f)

		icon_path = common.get_resource(image_filename, os.path.join(self.parent.sprite_object.resource_subpath,"icons"))
		if icon_path is None:
			icon_path = common.get_resource(image_filename, os.path.join("meta","icons"))
		if icon_path is None:
			raise AssertionError(f"No image resource found with name {image_filename}")

		img = tk.PhotoImage(file=icon_path)

		key = self.label + '.' + internal_value_name
		display_text = internal_value_name.title() + ' ' + self.label
		subkey = key.split('.')[1]
		key = key.split('.')[0]
		if key in langs.keys():
			if subkey in langs[key].keys():
				display_text = langs[key][subkey]

		button = tk.Radiobutton(
				self.parent.spiffy_buttons_section,
				image=img,
				name="_".join([self.label.lower(), internal_value_name, "button"]),
				text=display_text,
				variable="_".join([self.label.lower(), "var"]),
				value=internal_value_name,
				activebackground=self.parent.DIMENSIONS["button"]["color.active"],
				selectcolor=self.parent.DIMENSIONS["button"]["color.selected"],
				width=self.parent.DIMENSIONS["button"]["width"],
				height=self.parent.DIMENSIONS["button"]["height"],
				indicatoron=False,
				command=self.press_spiffy_button()
		)

		ToolTip(button, display_text)
		button.image = img
		button.grid(row=self.row, column=self.col)

		if not self.default_exists:
			button.select()
			self.press_spiffy_button()
			self.default_exists = True

		self.col += 1

	def add_blank_space(self, amount_of_space=1):
		self.col += amount_of_space

	def press_spiffy_button(self):
		self.parent.sprite_object.update_animation()
