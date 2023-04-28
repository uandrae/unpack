#!/usr/bin/env python3

import os
import re
import sys
import argparse
import yaml

class Experiment:

 def __init__(self, name=None, path=None, mbrs=None, is_vfld=True):
        self.name = name
        self.archive = '{}/archive/extract'.format(path) if name in path else '{}/{}/archive/extract'.format(path,name)
        if not os.path.exists(self.archive):
          self.archive = path
          if not os.path.exists(self.archive):
            print("Archive directory does not exist",self.archive)
            sys.exit(1)

        self.mbrs = mbrs
        if ( self.mbrs is None ) :
         self.mbrs = ['']
        elif not isinstance(self.mbrs, list) and not isinstance(self.mbrs, dict) :
         self.mbrs = [self.mbrs]
        elif len(self.mbrs) == 0 and isinstance(self.mbrs,list) :
         self.mbrs = find_mbrs(self.archive,'mbr')
         if len(self.mbrs) == 0 :
          self.mbrs = ['']

        self.is_vfld = is_vfld
        # Testing
        self.dry = True

 def print(self) :
     txt = { 'Experiment name' : self.name, 'Archive' : self.archive, 'Name patterns' : self.mbrs } 
     print()
     [print('{:<20} : {:}'.format(x,y)) for x,y in txt.items()]
     print()

 def unpack_vfld(self,path):

  from glob import glob
  from tarfile import open as taropen

  tpath = path if self.name in path else '{}/{}'.format(path,self.name)

  self.print()

  for mbr in self.mbrs :
   name = self.mbrs[mbr] if isinstance(self.mbrs,dict) else mbr
   t = '{}/{}/'.format(tpath,name)
   print('Target directory:',t)
   sp = self.archive
   print(' Scan',sp,name)
   files = find_files(sp,name)
   if self.is_vfld :
      files = [f for f in files if "vfld" in f]
   else:
      files = [f for f in files if "vobs" in f]
   nf = len(files)
   print('  found {} files'.format(nf))
   if not os.path.exists(t) and nf > 0 :
     if self.dry :
      print(' Create dir:',t)
     else :
      os.makedirs(t)

   for f in files :
    ff = '{}/{}'.format(sp,f)
    if self.is_vfld:
      dtg = re.search(r'(.*)(\d{10}.tar.gz)',f).group(2).split('.')[0]
      yy,mm,dd,hh = re.search(r'(\d{4})(\d{2})(\d{2})(\d{2})',dtg).groups()
      fpath = '{}/{}/{}/{}/'.format(t.rstrip('/'),yy,mm,dd)
      g = glob('{}vfld*{}*'.format(fpath,dtg))
    else:
      dtg = re.search(r'(.*)(\d{8}.tar.gz)',f).group(2).split('.')[0]
      yy,mm,dd = re.search(r'(\d{4})(\d{2})(\d{2})',dtg).groups()
      fpath = '{}/{}/{}/{}/'.format(t.rstrip('/'),yy,mm,dd)
      g = glob('{}vobs*{}*'.format(fpath,dtg))
    if len(g) == 0 :
     print(" Unpack",f,"to",fpath)
     if not self.dry :
      tar = taropen(ff)
      tar.extractall(fpath)
    else:
     print(f" Found {len(g)} files for {dtg}")

def find_mbrs(path,pattern):

  # Scan given path and subdirs and return dirs

  result = []
  it = os.scandir(path)
  for entry in it:
      if not entry.name.startswith('.') and entry.is_dir():
          if re.search('mbr\d{3}',entry.name) :
            result.append(entry.name)

  return result

def find_files(path,pattern):

  # Scan given path and subdirs and return files matching the pattern

  result = []
  try :
   it = os.scandir(path)
  except :
   print(" Could not find",path)
   return result

  for entry in it:
      if not entry.name.startswith('.') and entry.is_file():
          if re.search('(.*)'+pattern+'(\d{10}|\d{8}).tar.gz',entry.name) :
            result.append(entry.name)
      if not entry.name.startswith('.') and entry.is_dir():
          subresult = find_files(os.path.join(path,entry.name),pattern)
          subresult = [entry.name + "/" + e for e in subresult]
          result.extend(subresult)
  return result


def run(config) :

  verdir  = config['verdir']

  exp = [None]*len(config['experiments'])
  for i,e in enumerate(config['experiments']):
    members=config['experiments'][e]['members'] if 'members' in config['experiments'][e] else []
    is_vfld=config['experiments'][e]['is_vfld'] if 'is_vfld' in config['experiments'][e] else True

    exp[i] = Experiment(e,config['experiments'][e]['input_path'],members,is_vfld)
    exp[i].dry = config['dry']
    exp[i].unpack_vfld(verdir)

def main(argv) :

  parser = argparse.ArgumentParser(description='Unpack vfld/vobs files')
  parser.add_argument('-c',dest="config_file",help='Config file',required=True,default=None)
  parser.add_argument("-d", action="store_true", dest="dry", 
                      help="Dry run, check but do not fetch, send or clean anything", default=False)


  if len(argv) == 1 :
     parser.print_help()
     sys.exit(1)

  args = parser.parse_args()

  # Read config file
  if not os.path.isfile(args.config_file) :
     print("Could not find config file:",args.config)
     sys.exit(1)

  config = yaml.safe_load(open(args.config_file))
  config['dry'] = args.dry

  run(config)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

