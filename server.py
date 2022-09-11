import cherrypy
from cherrypy.process import servers
from cherrypy.lib.static import serve_file
import os
import hashlib
import binascii
import json
import sys

# The set of user files and passwords are encrypted with this application and 
# stored in a special file in the data directory; userpass is the passphrase/key
# to be used for this file and is loaded from a text document or supplied on
# launch.
userpass=''

# Open a file and return its contents.
def getFile(filename,mode="r"):
  f = open(filename,mode)
  contents = f.read()
  f.close()
  return contents

# Symmetric-key algorithm for encryption and decryption, based on md5.
def crypt(text, passphrase):
  m = hashlib.md5()
  pad = ""
  last = ""
  text = binascii.hexlify(text)
  while(len(pad) < len(text)):
    encoded = last+passphrase
    m.update(encoded.encode('utf-8'))
    last = m.hexdigest()
    pad = pad + last
  pad = pad[0:len(text)]
  result = ""
  while(len(text) > 0):
    tc = text[0]
    text = text[1:len(text)]
    pc = pad[0]
    pad = pad[1:len(pad)]
    newint = int(str(tc),16) ^ int(str(pc),16)
    newchar = str(hex(newint))[2]
    result = result + newchar
  return binascii.unhexlify(result)

# Backend web interface.
class Server(object):
  # Constructor; only needs to load the passphrase
  def __init__(self):
    global userpass
    userpass = getFile('passphrase.txt')
    return

  # Program entry point for a client application; loads a web interface
  # providing access to the remaining functions.
  def index(self):
    return getFile('index.html')
  index.exposed = True

  # Attempts to load an encrypted file, decrypt it with the provided key, and
  # return the plaintext result. Returns garbage for an incorrect passphrase.
  def read(self, username, password, filename, passphrase):
    global userpass
    userdict = json.loads(crypt(getFile('data/users','rb+'),userpass))
    if username not in userdict.keys() or password not in userdict[username]:
        return "Access attempt failed"
    try:
        f = open('data/'+filename+'.sec','rb+')
        text = crypt(f.read(),passphrase)
        f.close()
        return text
    except:
        return ""
  read.exposed = True

  # Writes or appends data to a file, encrypted with the given passphrase.
  def write(self, username, password, filename, passphrase, text):
    global userpass
    file = crypt(getFile('data/users','rb+'),userpass)
    userdict = json.loads(file.decode())
    if username not in userdict.keys() or password not in userdict[username]:
        return "Access attempt failed"
    try:
        f = open('data/'+filename+'.sec','rb')
        old_text = crypt(f.read(),passphrase)
        text = binascii.unhexlify(binascii.hexlify(old_text) + binascii.hexlify(text))
        f.close()
    except:
        print("No existing file/key combo; creating " + filename);
    f = open('data/'+filename+'.sec','wb+')
    f.write(crypt(text,passphrase))
    f.close()
    return getFile('index.html')
  write.exposed = True
 
  # Webservice method not used by the friendly web application; used to encrypt
  # a pre-existing file without pasting it into the web interface
  def encrypt(self, username, password, filename, passphrase):
    global userpass
    userdict = json.loads(crypt(getFile('data/users','rb+'),userpass))
    if username not in userdict.keys() or password not in userdict[username]:
        return "Access attempt failed"
    text = getfile('data/'+filename+'.txt')
    f = open('data/'+filename+'.sec','wb+')
    f.write(crypt(text,passphrase))
    f.close()
    return getfile('data/'+filename+'.sec')
  encrypt.exposed = True
    
  # Webservice method not used by the friendly web application; used to combine
  # two files, taking into account JSON syntax and merging arrays appropriately.
  def merge(self, username, password, file1, file2, passphrase):
    global userpass
    userdict = json.loads(crypt(getFile('data/users','rb+'),userpass))
    if username not in userdict.keys() or password not in userdict[username]:
        return "Access attempt failed"
    f1 = getfile('data/'+file1+'.sec')
    f2 = getfile('data/'+file2+'.sec')
    if f2[0] == '[':
        f2 = f2[1:]
    return f1 + ', ' + f2
  merge.exposed = True

#program entry point; launches a "Server" object instance on port 8766,
#listening for https traffic
if __name__ == '__main__':
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.server.socket_port = 8766
    cherrypy.server.ssl_certificate = "server.crt"
    cherrypy.server.ssl_private_key = "server.key"
    cherrypy.server.ssl_module = "builtin"
    def fake_wait_for_occupied_port(host, port): return
    servers.wait_for_occupied_port = fake_wait_for_occupied_port
    cherrypy.quickstart(Server())