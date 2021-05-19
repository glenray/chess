from bs4 import BeautifulSoup
import io
import os
import re
import requests
import zipfile

'''
Base class providing tools to scrape web content
A sub-class must provide specific code for the desired data.
Glen Pritchard - 9/28/2020
9/30/2020: converted to base class
'''
class pgnPillager:
	def __init__(self):
		self.re = re

	def getSoup(self, url, headers=None):
		'''
		return html page at url as Beautiful Soup object
		for further parsing in sub-class
		'''
		html = requests.get(url, headers=headers)
		return BeautifulSoup(html.content, "html.parser")

	def dlFile(self, url, headers=None):
		'''
		return a file downloaded from url
		returns a binary object which can be later:
			transfomed to a string: obj.decode('utf-8')
			used like a file: io.BytesIO(obj) or io.StringIO(obj)
		'''
		print(f"Downloading {url}")
		req = requests.get(url, headers=headers)
		return req.content

	def unzipFile(self, file : bytes):
		'''
		Generator unzips a zip file and yields each file one at a time
		file: byte like object. This is not a string
		'''
		fileBytes = io.BytesIO(file)	# store content of zip file in memory
		myzipFile = zipfile.ZipFile(fileBytes)	# zipfile object of download file
		for name in myzipFile.namelist():	# iterate over the files in the zip
			print(f"Uncompressing {name}")
			yield myzipFile.read(name)	# unzip the file

	def saveFile(self, file, filename, folder):
		'''
		save a file to disk
		'''
		folder = self.verifyPath(folder)
		output = open(f"{folder}/{filename}", 'wb')	
		output.write(file)
		output.close
		print(f"{folder}/{filename} Saved!\n")

	def verifyPath(self, path):
		'''
		Creates the path if it does not exist and returns
		the path with no trailing backslash
		'''
		path=path.rstrip('/ ')
		os.makedirs(path, exist_ok=True)
		return path
