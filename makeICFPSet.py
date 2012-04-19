#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Generates psets
#Uses 'lcg-ls' which requires grid to be sourced and a valid grid proxy (voms-proxy-init)
#Does not add the correct crosssections, this will need to be done by hand.

import commands
#import configuration_SCBooks as conf,
import sys,os,readline,getpass,string,fileinput,socket,datetime,re
import sqlite3

#Connect to database
userDef = getpass.getuser()
user = raw_input("User? ["+userDef+"] :\n")
if user == "" :  user = userDef

paths=[]
shortNames=[]
xsecs=[]

db_location = "/afs/cern.ch/user/d/dburton/www/web/ICF_Database"
db_file = 'sqlite4.db'

db_path = db_location+'/'+db_file

if not os.path.exists(db_path) :
  print 'Cannot find database: ',db_path
  sys.exit()

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

rows = conn.execute('''select
job.rowid,state,path,dataset,rpath,node,susycaf,dset.nonDefault,dset.isData
                     from job join tag on tag.rowid=job.tagid join dset on dset.rowid=job.dsetid
                     where user="'''+user+'''" order by state,path''').fetchall()


for row in rows:
    print ('\t'.join([str(item) for item in row]))[0:90] + "..."
jobnumber = raw_input("\n\n\tWhich job?  ")

#get path and short name from user's selected job
for row in rows:
  if jobnumber == str(row['rowid']):
    datasets = (row['dataset']).split(',')
    if len(datasets) > 1 :
      for dset in datasets :
        path = (row['rpath'])+'/'+string.replace(dset[1:], '/', '.')
        #path = "/store/user/lpcsusyra1/clucas//ICF/automated/2012_04_15_22_40_17"+'/'+string.replace(dset[1:], '/', '.')
        path = path.replace('rjn04','rnandi')
	print "the path is >>>>>>", path
        paths.append(path)
        shortName = (string.split(dset, '/'))[1] + "_" + (string.split(dset, '/'))[2]
        shortName = shortName +"_" + row['susycaf']
        if row['nonDefault'] != None: shortName = shortName + "_" + row['nonDefault']
        shortName = string.replace(shortName,'-','_')
        shortName = string.replace(shortName,',','_')
        shortName = string.replace(shortName,'=','_')
        shortName = string.replace(shortName,' ','_')
        shortNames.append(shortName)
        if row['isData']: xsecs.append('Weight')
        if not row['isData']:xsecs.append(0.0)
        #Would be nice if this information was in the database.
    else :
      dset = datasets[0]
      path = (row['rpath'])
      path = path.replace('rjn04','rnandi')
      path = path.replace('/pnfs/cms/WAX/11/store/','/store/')
      print "the path is >>>>>>", path
      paths.append(path)
      shortName = (string.split(dset, '/'))[1] + "_" + (string.split(dset, '/'))[2]
      shortName = shortName +"_" + row['susycaf']
      if row['nonDefault'] != None: shortName = shortName + "_" + row['nonDefault']
      shortName = string.replace(shortName,'-','_')
      shortName = string.replace(shortName,',','_')
      shortName = string.replace(shortName,'=','_')
      shortName = string.replace(shortName,' ','_')
      shortNames.append(shortName)
      if row['isData']: xsecs.append('Weight')
      if not row['isData']:xsecs.append(0.0)
    break

#disconect from database
#db.disconnect()

#loop over datasets in job
for path, shortName, xsec in zip(paths, shortNames, xsecs) :

  print "Generating " + shortName + '.py'



  prefix = '\n' + '\t' +  "\"dcap://cmsdca.fnal.gov:24137/pnfs/fnal.gov/usr/cms/WAX/11/store/user/"# + path + '/'
  suffix = '\" ,'

  method = raw_input("Use srmls? [n] :\n")

  if method in ["y","yes"] : ### srmls
    offset = 0
    count = 100
    output = []
    # Regular Expression for output path (why didn't I just use [\sA-Za-z0-9_\/\.]+(.root)...)
    PathRE = re.compile('(/store/user/lpcsusyra1/\w+\/+ICF/automated/\S+\/+SusyCAF_Tree_[0-9]+_+[0-9]+_+[a-zA-Z0-9]+\.root)')
    #begin loop
    while True :
      print "Getting list of files %i to %i." % (offset, offset+count)
      #print "srmls -count %i -offset %i srm://gfe02.grid.hep.ph.ic.ac.uk:8443/srm/managerv2?SFN=%s" % (count,offset,path)
      temp = commands.getstatusoutput("srmls -count %i -offset %i srm://gfe02.grid.hep.ph.ic.ac.uk:8443/srm/managerv2?SFN=%s" % (count,offset,path))
      #Succesful?
      print temp
      if temp[0] != 0 and temp[0] != 256 : #256 is a warning
        print "\tError occured:"
        print temp
        break
      #Find lines using regular expression
      lines = PathRE.findall(temp[1])
      print lines
      sys.exit()
      for line in lines :
        output.append(line)
      print "Found %i files." % len(lines)
      if len(lines)<count :
        break
      offset +=count
    ##end loop
  ##end srmls
  else : ###lcg-ls
    temp = commands.getstatusoutput("lcg-ls srm://cmssrm.fnal.gov:8443/11/" + path + "/")
    #Succesful?
    if temp[0] != 0 :
      print "\tError occured:"
      print temp
      break
    #split up chunk of text in to array of filenames
    output = temp[1].split('\n')
    for i,l in enumerate(output):
      output[i] = l[16:]
      print output[i]
 ##end lcg-ls

  output.sort()

  #Remove duplicate files
  toRemove = []
  for i,line1 in enumerate(output[:-1]) :
    if (((line1.split('/'))[-1]).split('_'))[2] == (((output[i+1].split('/'))[-1]).split('_'))[2] :
      toRemove.append(i)
  toRemove.sort()
  toRemove.reverse()
  for i in toRemove :
    del output[i]

  #Write PSet
  outfile = open(shortName+'.py','w')

  #header
  header = '\n'.join([
    'from icf.core import PSet',
    '',
    '%s=PSet(' % shortName,
    '\tName=\"%s\",' % shortName,
    '\tFormat=(\"ICF\",3),',
    '\tFile=['
    ])
  outfile.write(header)

  #body
  filenames = []
  for line in output :
    line = line.rstrip()
    line = prefix + line + suffix
    filenames.append(line)
  for line in filenames :
    outfile.write(line)

  #footer
  if xsec != 'Weight': 
    footer = '\n'.join([
    '',
    '\t],',
    '\tCrossSection=%d,' % xsec,
    ')',
    ])
  if xsec == 'Weight':
    footer = "] \n \tWeight = 1.0, \n )"
  outfile.write(footer)
