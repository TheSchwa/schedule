#!/usr/bin/env python
#
# This python script generates a graphical schedule from the html of
# Rowan's concise student schedule page.  The output can be either
# text, ascii, or html.
#
# Can also parse events added manually in a config file.
#
# Author: Joshua A Haas

import datetime as dt
import ConfigParser as cp
import sys,os.path

import quickfile as qf
import util
from htmlwriter import tab,tag,tags,css,br,space

import schedule,event,meeting

COLUMNS = (['CRN','Course','Title','Campus','Credits','Level',
            'Start Date','End Date','Day','Time','Location','Instructor'])
EVENT_COLS = 6

def convert():
  """parse rowan and config to generate ascii and html"""
  
  try:
    rowanfile = os.path.expanduser('~/rowan.html')
    s = parserowan(rowanfile)
  except IOError:
    print 'Could not find rowan concise schedule file "~/rowan.html"'
    sys.exit(0)
  
  try:
    configfile = os.path.expanduser('~/sched.conf')
    s2 = parseconfig(configfile)
  except IOError:
    print 'Could not find schedule config file "~/sched.conf"'
    sys.exit(0)
  
  s.addevents(s2.getevents())
  (t,b) = getlayout(s)
  
  try:
    asciifile = os.path.expanduser('~/sched-ascii.txt')
    writeascii(t,b,asciifile)
  except IOError:
    print 'Could not write to ascii file "~/sched-ascii.txt"'
    sys.exit(0)
  
  opts = parsehtmlconfig(configfile)
  
  try:
    htmlfile = os.path.expanduser('~/public_html/sched.html')
    writehtml(t,opts,htmlfile)
  except IOError:
    print 'Could not write to html file "~/public_html/sched.html"'
    sys.exit(0)
  
  print 'Success making "~/sched-ascii.txt" and "~/public_html/sched.html"'

def parsehtml(htmlfile):
  """read the data from a schedconv webpage into a Schedule object"""
  
  raise NotImplementedError
  
def parseascii(asciifile):
  """read the data from a schedconv ascii file into a Schedule object"""
  
  raise NotImplementedError

def parseconfig(configfile):
  """read the data from a schedconv config file into a Schedule object"""
  
  sched = schedule.Schedule()
  
  config = cp.RawConfigParser()
  result = config.read(configfile)
  if len(result)==0:
    raise IOError('File not found: "'+configfile+'"')
  sections = config.sections()
  if 'HTML Options' in sections:
    sections.remove('HTML Options')
  
  for section in sections:
    info = {}
    info['Title'] = section
    info['Type'] = 'Config'
    eve = event.Event(info)
    
    # Example meets line shown below
    # meets = MW(8:00-10:00) TR(12P-2P,4P-5:30P) F(9A-noon)
    info = {}
    (info['Start Date'],info['End Date']) = parseconfigdates(config.get(section,'dates'))
    info['Location'] = config.get(section,'location')
    meetinfos = config.get(section,'meets').split(' ')
    for meetinfo in meetinfos:
      days = meetinfo[:meetinfo.find('(')]
      times = meetinfo[meetinfo.find('(')+1:meetinfo.find(')')].split(',')
      for day in days:
        info['Day'] = day
        for time in times:
          (info['Start Time'],info['End Time']) = parseconfigtimes(time)
          eve.addmeet(meeting.Meeting(info,eve))
    sched.addevent(eve)
  
  return sched

def parseconfigdates(s):
  """return two dt.dates based on string s"""
  
  hyphen = s.find('-')
  d1 = s[:hyphen]
  d2 = s[hyphen+1:]
  return (parseconfigdate(d1),parseconfigdate(d2))

def parseconfigdate(s):
  """return a dt.date based on string s"""
  
  slash1 = s.find('/')
  slash2 = s.rfind('/')
  year = int(s[:slash1])
  month = int(s[slash1+1:slash2])
  day = int(s[slash2+1:])
  return dt.date(year,month,day)

def parseconfigtimes(s):
  """return two dt.times based on string s"""
  
  hyphen = s.find('-')
  t1 = s[:hyphen]
  t2 = s[hyphen+1:]
  return (parseconfigtime(t1),parseconfigtime(t2))

def parseconfigtime(s):
  """return a dt.time based on string s using following formats:
  24-hr:  8:00  09:00 12  13 0:15   0
  12-hr:  8:00A 9A    12P 1P 12:15A 12A
  string: 'noon' 'midnight' """
  
  if s=='noon':
    hr = 12
    mi = 0
  elif s=='midnight':
    hr = 0
    mi = 0
  else:
    colon = s.find(':')
    if colon>-1:
      hr = int(s[:colon])
      mi = int(s[colon+1:colon+3])
      if ('A' in s.upper()) and (hr==12):
        hr = 0
      elif 'P' in s.upper():
        hr += 12
        if hr==24:
          hr = 12
    else:
      mi = 0
      if 'A' in s.upper():
        hr = int(s[:-1])
        if hr==12:
          hr = 0
      elif 'P' in s.upper():
        hr = int(s[:-1])+12
        if hr==24:
          hr = 12
      else:
        hr = int(s)
  
  return dt.time(hr,mi)


def parserowan(htmlfile):
  """read the data from the rowan webpage into a Schedule object"""
  
  sched = schedule.Schedule()
  
  lines = qf.readlinesbs(htmlfile)
  (tablestart,_) = util.findinlist('Display course details for a student',lines)
  (tablestop,_) = util.findinlist('</table>',lines,tablestart+1)
  starts = util.findallinlist('<tr>',lines,tablestart+1,tablestop)
  stops = util.findallinlist('</tr>',lines,tablestart+1,tablestop)
  
  # Ignore first (table headers) and last (total credits) <tr></tr>
  starts = [x[0] for x in starts[1:-1]]
  stops = [x[0] for x in stops[1:-1]]
  
  for start in starts:
    
    # Build event.Class info
    info = {}
    for i in range(0,EVENT_COLS):
      l = lines[start+1+i]
      if '&nbsp;' in l:
        info = sched.events[-1].getinfo()
        break
      info[COLUMNS[i]] = innerhtml(l).strip()
    eve = parserowanevent(info)
    
    # Build meeting.Meeting info
    info = {}
    for i in range(EVENT_COLS,len(COLUMNS)):
      l = lines[start+1+i]
      info[COLUMNS[i]] = innerhtml(l).strip()
    
    # Check for fake classes (i.e. Honors Participation)
    try:
      meets = parserowanmeet(info,eve)
    except ValueError:
      continue
    
    # If the Class does not exist, add it to sched, else add the meet
    # to the existing Class in sched
    matches = sched.geteventinds(fields={'CRN':eve.getinfo('CRN')})
    if len(matches)==0:
      eve.addmeets(meets)
      sched.addevent(eve)
    else:
      sched.events[matches[0]].addmeet(meets)
      
  return sched

def innerhtml(l):
  """return the innerhtml of the outtermost tag in l"""
  
  openstop = l.find('>')
  closestart = l.find('</',openstop)
  return l[openstop+1:closestart]

def parserowanevent(info):
  """convert strings to correct types"""
  
  info['CRN'] = int(info['CRN'])
  info['Credits'] = float(info['Credits'])
  info['Type'] = 'Class'
  return event.Class(info)

def parserowanmeet(info,eve):
  """convert strings to correct types"""
  
  info['Start Date'] = parserowandate(info['Start Date'])
  info['End Date'] = parserowandate(info['End Date'])
  (info['Start Time'],info['End Time']) = parserowantimes(info['Time'])
  del info['Time']
  
  days = info['Day']
  if len(days)==1:
    return meeting.ClassMeeting(info,eve)
  
  meets = []
  for day in days:
    info['Day'] = day
    meet = meeting.ClassMeeting(info,eve)
    meets.append(meet)
  return meets

def parserowandate(s):
  """convert the string to a dt.date"""
  
  space1 = s.find(' ')
  space2 = s.rfind(' ')
  mon = parserowanmonth(s[:space1])
  day = int(s[space1+1:space2-1])
  yr = int(s[space2+1:])
  return dt.date(yr,mon,day)

def parserowanmonth(s):
  """convert the string to a number 1-12"""
  
  months = ([None,'Jan','Feb','Mar','Apr','May',
      'Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
  return months.index(s)

def parserowantimes(s):
  """convert the string to two dt.time objects"""
  
  hyphen = s.find('-')
  t1 = s[:hyphen-1]
  t2 = s[hyphen+2:]
  return (parserowantime(t1),parserowantime(t2))

def parserowantime(s):
  """convert the string to a dt.time object"""
  
  colon = s.find(':')
  hr = int(s[:colon])
  mins = int(s[colon+1:colon+3])
  if ('pm' in s) and (hr!=12):
    hr += 12
  return dt.time(hr,mins)

def getlayout(s):
  """decide where to put entries in the schedule"""
  
  if len(s.getconflicts())>0:
    raise RuntimeError('Cannot layout a schedule with conflicts')
  
  # Create blank sched matrix
  table = util.matrix(8,7,None)
  
  days = meeting.DAYS
  for d in range(0,7):
    meets = s.getmeets(search={'Day':days[d]})
    
    # If there are more than 8 meets, they won't fit, throw an error
    if len(meets)>8:
      raise RuntimeError('Too many meets on '+days[d]+' to layout')
    
    meets.sort(key=(lambda meet: meet.getinfo('Start Time')))
    for meet in meets:
      
      # Set based on start time or in next available slot if occupied
      # also take into account duration for spanning multiple cells
      # the last cell of the multi is the meeting, previous are 'MULTI'
      pref = getstartind(meet)
      dur = getdurind(meet)
      start = getavailind(table,d,pref)
      
      # Reduce the dur if it doesn't fit
      while (dur>1) and (not isvalid(table,d,start,dur)):
        dur -= 1
      
      # If out of spaces move meets earlier or condense MULTI meets
      if not isvalid(table,d,start,dur):
        table = freespaceup(table,d,8)
        start = getavailind(table,d,pref)
      
      # If there are 8 or fewer meets on this day, layout must work
      assert isvalid(table,d,start,dur), 'Failed to layout a day with 8 or fewer meets'
      
      # Move previous same events later if necessary and possible and
      # move current event later if necessary and possible
      # Based on intuition that same events on different days but
      # at the same times should be in the same row in the schedule
      table = sync(table,meet)
      
      # Set meet and 'MULTI' in table
      for row in range(start,start+dur-1):
        table[row][d] = 'MULTI'
      table[start+dur-1][d] = meet
      
  borders = getborders(table)
  return (table,borders)

def getstartind(meet):
  """return the index in the matrix best matching the start time"""
  
  t = meet.getinfo('Start Time')
  hr = t.hour
  mi = t.minute
  return int(((hr+1.0*mi/60)-8)/2)

def getdurind(meet):
  """return the length of this meet in matrix indices"""
  
  dur = meet.getduration()
  sec = dur.seconds
  hr = int(sec/60/60)
  mi = int((sec-60*60*hr)/60)
  dur = int(((hr+1.0*(mi-0.5)/60)+1)/2)
  if dur<1:
    return 1
  if dur>8:
    return 8
  return dur

def getavailind(matrix,col,pref):
  """return the first open spot in col at or after pref or 8 if none"""
  
  while (pref<8) and (matrix[pref][col] is not None):
    pref += 1
  return pref

def isvalid(matrix,col,start,dur):
  """return True if given layout is valid, False otherwise"""
  
  # Start and duration must be within table
  if (start>7) or (start+dur-1>7) or (start<0) or (dur<1) or (dur>8):
    return False
  
  # Conflicts are invalid
  for r in range(start,start+dur):
    if matrix[r][col] is not None:
      return False
      
  return True

def freespaceup(matrix,col,row):
  """move events sooner, or if doesn't work condense then move sooner,
  if neither work and nothing can be changed return None"""
  
  new = moveup(matrix,col,row)
  if new is not None:
    return new
  
  new = condenseup(matrix,col,row)
  if new is not None:
    return new
  
  return None

def freespacedown(matrix,col,row):
  """move events later, or if doesn't work condense then move later,
  if neither work and nothing can be changed return None"""
  
  new = movedown(matrix,col,row)
  if new is not None:
    return new
  
  new = condensedown(matrix,col,row)
  if new is not None:
    return new
  
  return None

def sync(matrix,meet):
  """try to keep all meets in the same row if they are for the same
  event at the same time (but on different days)"""

  cells = []

  for c in range(0,7):
    for r in range(0,8):
      cell = matrix[r][c]
      if issubclass(cell.__class__,meeting.Meeting) and (cell.event is meet.event):
        cells.append((r,c))
  
  # Attempt to move corresponding meets later to sync
  for (r1,c1) in cells:
    for (r2,c2) in cells:
      t1 = matrix[r1][c1].getinfo('Start Time')
      t2 = matrix[r2][c2].getinfo('Start Time')
      if (r1!=r2) and (c1!=c2) and (t1==t2):
        new = 'Some'
        
        # Try to move m2 later
        while (r1>r2) and (new is not None):
          new = freespacedown(matrix,c2,r2)
          if new is not None:
            matrix[r2+1][c2] = matrix(r2,c2)
            matrix[r2][c2] = None
        
        # Try to move m1 later
        while (r1<r2) and (new is not None):
          new = freespacedown(matrix,c1,r1)
          if new is not None:
            matrix[r1+1][c1] = matrix(r1,c1)
            matrix[r1][c1] = None
  
  # Attempt to move corresponding meets earlier to sync
  for (r1,c1) in cells:
    for (r2,c2) in cells:
      t1 = matrix[r1][c1].getinfo('Start Time')
      t2 = matrix[r2][c2].getinfo('Start Time')
      if (r1!=r2) and (c1!=c2) and (t1==t2):
        new = 'Some'
        
        # Try to move m1 earlier
        while (r1>r2) and (new is not None):
          new = freespaceup(matrix,c1,r1)
          if new is not None:
            matrix[r1-1][c1] = matrix(r1,c1)
            matrix[r1][c1] = None
        
        # Try to move m2 earlier
        while (r1<r2) and (new is not None):
          new = freespaceup(matrix,c2,r2)
          if new is not None:
            matrix[r2-1][c2] = matrix(r2,c2)
            matrix[r2][c2] = None
  
  return matrix

def moveup(matrix,col,row):
  """move events before row sooner in column col if possible, otherwise
  return None if no changes have been made"""
  
  free = row-1
  while (free>=0) and (matrix[free][col] is not None):
    free -= 1
  if free>=0:
    for r in range(free,row-1):
      if r==7:
        matrix[r][col] = None
      else:
        matrix[r][col] = matrix[r+1][col]
    return matrix
  return None

def movedown(matrix,col,row):
  """move events after row later in column col if possible, otherwise
  return None if no changes have been made"""
  
  free = row+1
  while (free<=7) and (matrix[free][col] is not None):
    free += 1
  if free<=7:
    for r in range(free,row+1,-1):
      if r==0:
        matrix[r][col] = None
      else:
        matrix[r][col] = matrix[r-1][col]
    return matrix
  return None

def condenseup(matrix,col,row):
  """condense one event spanning multiple cells if possible then moveup
  otherwise return None if no changes have been made"""
  
  free = row-1
  while (free>=0) and (matrix[free][col]!='MULTI'):
    free -= 1
  if free>=0:
    matrix[free][col] = matrix[free+1][col]
    matrix[free+1][col] = None
    matrix = moveup(matrix,col,row)
    return matrix
  return None

def condensedown(matrix,col,row):
  """condense one event spanning multiple cells if possible then movedown
  otherwise return None if no changes have been made"""
  
  free = row+1
  while (free<=7) and (matrix[free][col]!='MULTI'):
    free += 1
  if free>=0:
    matrix[free][col] = None
    matrix = movedown(matrix,col,row)
    return matrix
  return None

def getborders(table):
  """turn off borders within MULTI events"""
  
  borders = util.matrix(7,7,True)
  for c in range(0,7):
    for r in range(0,7):
      if table[r][c]=='MULTI':
        borders[r][c] = False
  return borders

def writetxt(sched,outfile,):
  """write the schedule to a text file"""
  
  qf.write(sched.strf(),outfile)
  
def writeascii(table,borders,fname):
  """write the schedule to a text file as an ascii table"""
  
  infos = [gettitlestr,getlocstr,gettimestr]
  s = '     '
  days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
  times = [' 8A','10A','12P',' 2P',' 4P',' 6P',' 8P','10P','12A']
  multifill = ['|  |  |','|  |  |','V  V  V']
  for day in days:
    s += (center(day,13)+' ')
  s += '\n'
  s += (' 8A +'+('-------------+'*7)+'\n')
  for row in range(0,8):
    for i in range(0,3):
      s += '    |'
      for col in range(0,7):
        meet = table[row][col]
        if meet is None:
          s += (' '*13+'|')
        else:
          if meet=='MULTI':
            if (row==0) or (table[row-1][col]!='MULTI'):
              s += (' '+infos[i](getmultimeet(table,row,col))+' |')
            else:
              s += (center(multifill[i],13)+'|')
          else:
            if (row==0) or (table[row-1][col]!='MULTI'):
              s += (' '+infos[i](meet)+' |')
            else:
              s += (center(multifill[i],13)+'|')
      s += '\n'
    s += (times[row+1]+' +')
    if row==7:
      s += ('-------------+'*7+'\n')
    else:
      for col in range(0,7):
        if borders[row][col]:
          s += '-------------+'
        else:
          s += '             +'
    s += '\n'
    
  qf.write(s,fname)

def getmultimeetind(matrix,row,col):
  """return the row index at the end of this sequence of 'MULTI'"""
  
  while matrix[row][col]=='MULTI':
    row += 1
  return row

def getmultimeet(matrix,row,col):
  """return the meeting at the end of this sequence of 'MULTI'"""
  
  row = getmultimeetind(matrix,row,col)
  return matrix[row][col]

def center(s,length,fill=' '):
  """return the string s centered in spaces"""
  
  empty = length-len(s)
  left = int(empty/2)
  right = empty-left
  return fill*left+s+fill*right

def gettitlestr(meet):
  """return the formatted title string of meet"""
  
  title = meet.event.getinfo('Title').upper()
  
  delete = ['SOC SCI:','LITERATURE:','SEMINAR: ']
  for d in delete:
    title = title.replace(d,'')
  
  replace = ([['INTRODUCTION','I'],
              ['INTRO','I'],
              ['I TO','I'],
              ['HONORS','H'],
              ['HONOR','H'],
              ['HONR','H'],
              ['ELECTRICAL','ELEC'],
              ['ENGINEERING','ENG'],
              ['COMPUTER SCIENCE','CS'],
              ['COMPUTERS','COMP'],
              ['COMPUTER','COMP'],
              [' AND ',' & '],
              ['- ',''],
              ['HISTORY','HIST'],
              ['MATHEMATICAL','MATH'],
              ['TECHNOLOGIES','TECH'],
              ['TECHNOLOGY','TECH'],
              ['STATISTICS','STAT'],
              ['DIGITAL','DIG']])
  for pair in replace:
    title = title.replace(pair[0],pair[1])
  
  return center(title[:11].title(),11)

def getlocstr(meet):
  """return the formatted location string of meet"""
  
  loc = meet.getinfo('Location').upper()
  
  delete = [' HALL',' CENTER',' BUILDING',' BLDG','CL-']
  for d in delete:
    loc = loc.replace(d,'')
  
  replace = ([['ROBINSON','ROBIN'],
              ['WHITNEY','WHIT'],
              ['ENTERPRISE','ENTERP'],
              ['HAWTHORNE','HAWTH']])
  for pair in replace:
    loc = loc.replace(pair[0],pair[1])
  
  return center(loc.title()[:11],11)

def gettimestr(meet):
  """return the formatted time string of meet"""
  
  start = meet.getinfo('Start Time')
  end = meet.getinfo('End Time')
  shr = twelvehr(start.hour)
  smi = start.minute
  ehr = twelvehr(end.hour)
  emi = end.minute
  return center(str(shr)+':'+str(smi).zfill(2)+'-'
      +str(ehr)+':'+str(emi).zfill(2),11)

def twelvehr(hr):
  """convert hr from 24 hour to 12 hour format"""
  
  if hr>12:
    return hr-12
  if hr==0:
    return 12
  return hr

def parsehtmlconfig(configfile):
  """read the config options for the html from the config file"""
  
  config = cp.RawConfigParser()
  result = config.read(configfile)
  if len(result)==0:
    raise IOError('File not found: "'+configfile+'"')
  if 'HTML Options' not in config.sections():
    return {}
  optlist = config.items('HTML Options')
  opts = {}
  for pair in optlist:
    opts[pair[0]] = pair[1]
  return opts

def writehtml(table,opts,fname):
  """write the schedule to an html file using CSS opts"""
  
  default = ({'title':'Schedule',
              'page-bg-color':'#FFFFFF',
              'font-family':'Verdana',
              'empty-cell-bg-color':'#808080',
              'border-color':'#000000',
              'event-cell-font-color':'#000000',
              'event-cell-bg-color':'#FFFFFF',
              'header-font-color':'#000000'})
  
  opts = util.fillargs(opts,default)
  lines = tag('html',tab(html_gethtml(table,opts)))
  qf.writelines(lines,fname)

def html_gethtml(table,opts):
  """return the content of the <html></html> tags"""
  
  lines = tag('head',tab(html_gethead(table,opts)))
  lines += tag('body',tab(html_getbody(table,opts)))
  return lines

def html_gethead(table,opts):
  """return the content of the <head></head> tags"""
  
  lines = [tags('title',opts['title'])]
  lines += tag('style',tab(html_getstyle(table,opts)))
  return lines

def html_getstyle(table,opts):
  """return the content of the CSS <style></style> tags"""
  
  lines = css('body',{
      'background':opts['page-bg-color'],
      'font-family':opts['font-family']})
  lines += css('table',{
      'border-collapse':'collapse'})
  lines += css('td',{
      'background':opts['empty-cell-bg-color'],
      'border':'solid 3px '+opts['border-color'],
      'text-align':'center',
      'width':'120px',
      'height':'75px'})
  lines += css('td.full',{
      'color':opts['event-cell-font-color'],
      'background':opts['event-cell-bg-color']})
  lines += css('th',{
      'color':opts['header-font-color'],
      'width':'32px',
      'height':'32px'})
  lines += css(['th.time','th.corner'],{
      'position':'relative',
      'display':'block',
      'text-align':'right',
      'right':'8px'})
  lines += css('th.time',{
      'top':'63px'})
  lines += css('th.corner',{
      'top':'24px'})
  return lines

def html_getbody(table,opts):
  """return the content of the <body></body> tags"""
  
  return tag('table',tab(html_gettable(table)))

def html_gettable(table):
  """return the content of the <table></table> tags"""
  
  lines = tag('tr',tab(html_gettableheader()))
  lines += html_getrows(table)
  return lines
  
def html_gettableheader():
  """return the table header row"""
  
  lines = [tags('th','8A',{'class':'corner'})]
  days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
  for day in days:
    lines += [tags('th',day)]
  return lines
  
def html_getrows(table):
  """return the table rows"""
  
  lines = []
  for row in range(0,8):
    lines += tag('tr',tab(html_getrow(table,row)))
  return lines

def html_getrow(table,row):
  """return the specified row"""
  
  times = ['10A','12P','2P','4P','6P','8P','10P','12A']
  lines = [tags('th',times[row],{'class':'time'})]
  for col in range(0,7):
    meet = table[row][col]
    if meet is None:
      lines += [tags('td',space(1))]
    else:
      if meet=='MULTI':
        if (row==0) or (table[row-1][col]!='MULTI'):
          r = getmultimeetind(table,row,col)
          lines += [tags('td',html_getcell(table[r][col]),
              {'class':'full','rowspan':str(r-row+1)})]
      else:
        if (row==0) or (table[row-1][col]!='MULTI'):
          lines += [tags('td',html_getcell(meet),{'class':'full'})]
  return lines

def html_getcell(meet):
  """return the cell info for this meet"""
  
  title = gettitlestr(meet).strip()
  loc = getlocstr(meet).strip()
  time = gettimestr(meet).strip()
  return (title+br(1)+loc+br(1)+time)

def writeoverlap(title,users):
  """write an overlap view schedule to an html file where users is
  a dict with keys of 'username' and values of {'name':'','color':''}"""
  
  raise NotImplementedError

if __name__ == '__main__':
  convert()
