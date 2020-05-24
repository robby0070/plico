from appJar import gui
from datetime import datetime, date
from os import path
import json

measurements = {"peso": 0, "bicipite": 0, "tricipite": 0, "pettorale": 0, \
	"scapola": 0, "addome": 0, "ileo": 0, "coscia": 0, "ginocchio": 0, }

results = { "p6" : 0, "pu" : 0, "pollock" : 0, "BM" : 0, "BM%" : 0, \
	"BF" : 0, "BF%" : 0, }

currentfile = ""

def findValue (filename, value, age) :
	with open(filename, 'r') as file :
		file.readline()
		for line in file:
			if abs(float(line[:line.find(';')]) - value) < 0.1 :
				values = line.split(';')
				return float(values[age - 5])
	return 0

def calcValues() :
	## getting entries ##	
	for measure in measurements:
		value = app.getEntry("num-" + measure)
		measurements[measure] = value if value != None else 0
	sex = app.getRadioButton("radio-sex")
	filename = "tables/"
	filename += "maschi_" if sex == "Maschio" else "femmine_"

	## calculating age ##
	birth = app.getDatePicker("date-birth")
	today = date.today()
	age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

	## calculationg pu and p6 values ##
	pu = measurements["ileo"]
	media_icg = (measurements["ileo"] + measurements["coscia"] + measurements["ginocchio"]) / 3.
	p6 = measurements["bicipite"] + measurements["tricipite"] + measurements["scapola"] + media_icg
	results["pu"]= findValue(filename + "pu.csv", pu, age)
	results["p6"] = findValue(filename + "p6.csv", p6, age)

	## calculating pollock ##
	if sex == "Maschio" :
		pollock_sum = measurements["pettorale"] + measurements["addome"] + measurements["coscia"]
		results["pollock"] = 495 / (1.1093800 - 0.0008267 * pollock_sum + \
			0.0000016 * pollock_sum * pollock_sum - 0.0002574 * age) - 450
	else :
		pollock_sum = measurements["addome"] + measurements["ileo"] + measurements["tricipite"]
		results["pollock"] = 495 / (1.0902369 - 0.0009379 * pollock_sum + \
			0.0000026 * pollock_sum * pollock_sum - 0.00000979 * age) - 450
	
	## caclulating BF and BM ##	
	results["BF%"] = (results["pu"] + results["p6"] + results["pollock"]) / 3.
	results["BM%"] = 100 - results["BF%"]
	results["BF"] = measurements["peso"] / 100 * results["BF%"]
	results["BM"] = measurements["peso"] / 100 * results["BM%"]

	## setting value ##
	for result in results :
		app.setLabel("label-" + result + "-value", "{:5.2f}".format(results[result]))

def submit (button) :
	if button == "Cancella":
		app.stop()
	else :
		calcValues()
	

def load () :
	with open(currentfile, "r") as file:
		data = json.load(file)
		app.setEntry("entry-name", data["nome"])
		app.setDatePicker("date-birth", datetime.strptime(data["nascita"], "%d-%m-%Y"))
		app.setRadioButton("radio-sex", data["sesso"])

def save () :
	calcValues()
	to_dump = {} 
	if path.isfile(currentfile) :
		with open(currentfile, "r") as file:
			to_dump = json.load(file)
	to_dump["nome"]  = app.getEntry("entry-name")
	to_dump["nascita"] = app.getDatePicker("date-birth").strftime("%d-%m-%Y")
	to_dump["sesso"] = app.getRadioButton("radio-sex")

	with open(currentfile, "w") as file :
		to_dump[str(date.today())] = { "misure" : measurements, "risultati" : results } 
		json.dump(to_dump, file, indent=4)

def toolbar(tool) :
	global currentfile
	if "SAVE" in tool :
		if (not currentfile) or (tool == "SAVE AS") :
			currentfile = app.saveBox(fileTypes=[("json", "*.json")], fileExt=".json", asFile=False)
		if currentfile :
			save()

	elif tool == "OPEN" :
		currentfile = app.openBox(fileTypes=[("json", "*.json")], multiple=False, mode='r')
		if currentfile :
			load()

def changesex(radio) :
	if app.getRadioButton("radio-sex") == "Maschio":
		app.enableEntry("num-pettorale")
	else :
		app.disableEntry("num-pettorale")

with gui("developing") as app : 
	app.setBg("white" )
	with app.labelFrame("Anagrafe", colspan=2) :
		app.setFont(20)

		tools = ["SAVE", "SAVE AS", "OPEN"]
		app.addToolbar(tools, toolbar, findIcon=True)
		app.setToolbarImage("SAVE", "img/save.png")
		app.setToolbarImage("SAVE AS", "img/saveas.png")
		app.setToolbarImage("OPEN", "img/open.png")

		app.addLabel("label-name", "Nome")
		app.addEntry("entry-name", 0, 1)
		app.addDatePicker("date-birth", 0, 2, rowspan=3)
		app.setDatePickerRange("date-birth", 1950)

		with app.labelFrame("Sesso", colspan=2) :
			app.addRadioButton("radio-sex", "Maschio", 0, 0)
			app.addRadioButton("radio-sex", "Femmina", 0, 1)
			app.setRadioButtonChangeFunction("radio-sex", changesex)

	with app.labelFrame("Misure") :
		i = 0
		for measure in measurements :
			app.addLabel("label-" + measure, measure.capitalize(), i, 0)
			app.addNumericEntry("num-" + measure, i, 1)
			i += 1

	with app.labelFrame("Risultati", app.gr() - 1, 1) :
		for result in results :
			app.addLabel("label-" + result, result.capitalize(), i, 0)
			app.addLabel("label-" + result + "-value", "	", i, 1)
			app.setLabelBg("label-" + result + "-value", "white")
			app.setLabelRelief("label-" + result + "-value", "sunken")
			i += 1
	app.addButtons(["Conferma", "Cancella"], submit, colspan=2)