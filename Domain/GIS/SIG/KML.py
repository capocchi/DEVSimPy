# -*- coding: utf-8 -*-

__author__ = "Jon Goodall <jon.goodall@gmail.com> - http://www.duke.edu/~jgl34"
__version__ = "0.0.1"
__license__ = ""
__copyright__ =""

### modified by Laurent Capocchi (capocchi@univ-corse.fr)

try:
	from lxml import etree
	#print("running with lxml.etree")
except ImportError:
	try:
		# Python 2.5
		import xml.etree.cElementTree as etree
		#print("running with cElementTree on Python 2.5+")
	except ImportError:
		try:
			# Python 2.5
			import xml.etree.ElementTree as etree
			#print("running with ElementTree on Python 2.5+")
		except ImportError:
			try:
				# normal cElementTree install
				import cElementTree as etree
				#print("running with cElementTree")
			except ImportError:
				try:
					# normal ElementTree install
					import elementtree.ElementTree as etree
					#print("running with ElementTree")
				except ImportError:
					#print("Failed to import ElementTree from any known place")
					pass
class KML_Tree:
	
	NS = 'http://earth.google.com/kml/2.0'
	
	def __init__(self, filepath):
		"""
		"""
		
		### the xml tree
		self.tree = etree.parse(filepath)
		kml = self.tree.getroot()
		self.doc = kml[0]
			
	def write(self, fn):
		self.tree.write(fn)
		
	def add_folder(self, parent_document=None, point=None):
		new_folder = etree.XML(	"<Folder>\n"\
								" <name>"+point.folder+"</name>\n"\
								"</Folder>\n")
		
		parent_document.append(new_folder)
		
		return new_folder
		
	def add_placemark(self, parent_folder = None, point = None, place = None):
		""" Add new point or replace with place_name
		"""
		new_placemark = etree.XML(	" <Placemark>\n"\
									"  <description>" + point.desc + "</description>\n"\
									"  <name>" + point.name + "</name>\n"\
									"  <styleUrl>#exampleStyleMap</styleUrl>\n"+
									"  <LookAt>\n"\
									"    <longitude>" + str(point.lon) + "</longitude>\n"\
									"    <latitude>" + str(point.lat) + "</latitude>\n"\
									"    <range>" + str(point.ran) + "</range>\n"\
									"    <tilt>" + str(point.tilt) + "</tilt>\n"\
									"    <heading>" + str(point.head) + "</heading>\n"\
									"  </LookAt>\n"\
									"  <visibility>0</visibility>\n"\
									"   <Point>\n"\
									"    <extrude>1</extrude>\n"\
									"    <altitudeMode>relativeToGround</altitudeMode>\n"\
									"    <coordinates>" + str(point.lon) + "," + str(point.lat) +", " +  str(point.alt) + "</coordinates>\n"\
									"   </Point>\n"\
									" </Placemark>\n")
		### if replace
		if place is not None:
			# if the folder and place allready exists, we replace the place
			if 	place.text == point.name:
				parent_folder.replace(place, new_placemark)
		else:
			parent_folder.append(new_placemark)
			
		return new_placemark 
	
class KML_File:
	"""
		For creating KML files used for Google Earth
	"""
	def __init__(self, filepath):
		""" Constructor
			adds the kml header to a file (includes a default style)
		"""
		### local copy
		self.filepath = filepath
		
		with open(self.filepath,"w") as f:
			f.write(
			"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"\
			"<kml xmlns=\"http://earth.google.com/kml/2.0\">\n"\
			"<Document>\n"\
			#"<NetworkLink>\n"\
			#"<Link>\n"\
			#"<href>http://lcapocchi.free.fr/devsimpy/out.kml</href>\n"\
			#"<refreshMode>onInterval</refreshMode>\n"\
			#"<refreshInterval>10</refreshInterval>\n"\
			#"</Link>\n"\
			#"</NetworkLink>\n"\
			"<Style id='normalPlaceMarker'>\n"\
			"  <IconStyle>\n"\
			"    <Icon>\n"\
			"      <href>root://icons/palette-3.png</href>\n"\
			"      <x>96</x>\n"\
			"      <y>160</y>\n"\
			"      <w>32</w>\n"\
			"      <h>32</h>\n"\
			"    </Icon>\n"\
			"  </IconStyle>\n"\
			"</Style>\n")
			#f.write(
			#"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"\
			#"<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n"\
			#"<Document>\n"\
				#"<name>Highlighted Icon</name>\n"\
				#"<description>Place your mouse over the icon to see it display the new icon</description>\n"\
				#"<Style id=\"highlightPlacemark\">\n"\
				#"<IconStyle>\n"\
					#"<Icon>\n"\
					#"<href>http://maps.google.com/mapfiles/kml/paddle/red-stars.png</href>\n"\
					#"</Icon>\n"\
				#"</IconStyle>\n"\
				#"</Style>\n"\
				#"<Style id=\"normalPlacemark\">\n"\
				#"<IconStyle>\n"\
					#"<Icon>\n"\
					#"<href>http://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href>\n"\
					#"</Icon>\n"\
				#"</IconStyle>\n"\
				#"</Style>\n"\
				#"<StyleMap id=\"exampleStyleMap\">\n"\
				#"<Pair>\n"\
					#"<key>normal</key>\n"\
					#"<styleUrl>#normalPlacemark</styleUrl>\n"\
				#"</Pair>\n"\
				#"<Pair>\n"\
					#"<key>highlight</key>\n"\
					#"<styleUrl>#highlightPlacemark</styleUrl>\n"\
				#"</Pair>\n"\
				#"</StyleMap>\n")
    
	def close(self):
		with open(self.filepath,"a") as f:
			f.write(
			"</Document>\n"\
			"</kml>")
		
	def open_folder(self, name):
		with open(self.filepath,"a") as f:
			f.write(
			"<Folder>\n"\
			" <name>" + name + "</name>\n")
		
	def close_folder(self):
		with open(self.filepath,"a") as f:
			f.write("</Folder>\n")
		
	def add_placemarker(self, latitude, longitude, altitude = 0.0, description = " ", name = " ", range = 6000, tilt = 45, heading = 0):
		"""adds the point to a kml file"""
		
		with open(self.filepath,"a") as f:
			f.write(
			" <Placemark>\n"\
			"  <description>" + description + "</description>\n"\
			"  <name>" + name + "</name>\n"\
			"  <styleUrl>#exampleStyleMap</styleUrl>"+
			#"  <styleUrl>#normalPlaceMarker</styleUrl>" + 
			"  <LookAt>\n"\
			"    <longitude>" + str(longitude) + "</longitude>\n"\
			"    <latitude>" + str(latitude) + "</latitude>\n"\
			"    <range>" + str(range) + "</range>\n"\
			"    <tilt>" + str(tilt) + "</tilt>\n"\
			"    <heading>" + str(heading) + "</heading>\n"\
			"  </LookAt>\n"\
			"  <visibility>0</visibility>\n"\
			"   <Point>\n"\
			"    <extrude>1</extrude>\n"\
			"    <altitudeMode>relativeToGround</altitudeMode>\n"\
			"    <coordinates>" + str(longitude) + "," + str(latitude) +", " +  str(altitude) + "</coordinates>\n"\
			"   </Point>\n"\
			" </Placemark>\n")
			
if __name__ == "__main__":
	kml = KML_File("out.kml")
	kml.open_folder('Ville')
	kml.add_placemarker(latitude=42.304, longitude=9.151, altitude = 400.0, description = "Centru di a corsica", name = "Corte", range = 6000, tilt = 45, heading = 0)
	kml.add_placemarker(latitude=42.694, longitude=9.447, altitude = 20.0, description = "Cità mio", name = "Bastia", range = 6000, tilt = 45, heading = 0)
	kml.add_placemarker(latitude=41.921, longitude=8.735, altitude = 20.0, description = "Cità di Napoleone", name = "Ajaccio", range = 6000, tilt = 45, heading = 0)
	kml.close_folder()
	kml.close()