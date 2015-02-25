#!/usr/bin/env python
#
# A class to keep track of class meeting times for scheduling
#
# Author: Joshua A Haas

import datetime as dt
import util

import event

DAYS = ['U','M','T','W','R','F','S']

class Meeting:

  def __init__(self,info,eve):
    """Create a new Meeting with the given info"""
    
    self.FIELDS = ({ 'Start Date' : dt.date,
                     'End Date'   : dt.date,
                     'Day'        : str,
                     'Start Time' : dt.time,
                     'End Time'   : dt.time,
                     'Location'   : str })
    
    self.event = eve
    self.initinfo(info)
    self.checkparams()
    
  def __eq__(self,obj):
    """override the == operator"""
    
    return isinstance(obj,Meeting) and self.info == obj.info
    
  def __ne__(self,obj):
    """override the != operator"""
    
    return not self==obj

  def initinfo(self,info):
    """initialize info dict"""
    
    self.info = util.blankdict(self.FIELDS.keys())
    util.checkdict(info,self.FIELDS.keys())
    self.importinfo(info)

  def checkparams(self):
    """make sure all parameters are valid"""
    
    # Check classes
    for key in self.FIELDS.keys():
      assert isinstance(self.info[key],self.FIELDS[key]), 'Parameter "'+key+'" must be of type '+self.FIELDS[key]
    assert issubclass(self.event.__class__,event.Event), 'Parameter event must be subclass of Event'
    
    # Check values
    assert self.info['Start Date']<self.info['End Date'], 'Parameter "End Date" must be after "Start Date"'
    assert self.info['Day'] in DAYS, 'Parameter "Day" must be any of: M, T, W, R, F, S, U'
    assert self.info['Start Time']<self.info['End Time'] or self.info['End Time'].hour==0, 'Parameter "End Time" must be after "Start Time"'

  def getinfo(self,field=None):
    """return the requested info, or the entire dict if not specified"""
    
    if field is None:
      return self.info
    return self.info[field]
  
  def importinfo(self,info):
    """import info from the dict info into this Meeting"""
    
    self.info = util.updatedict(self.info,info)

  def conflicts(self,other):
    """check if this Meeting overlaps the Meeting other"""
    
    assert isinstance(other,Meeting), 'The argument to Meeting.conflicts() must be of type Meeting'
    
    # If equal, they conflict
    if self==other:
      return True
    
    # If dates do not overlap, no conflict
    if (self.info['End Date']<other.info['Start Date'] or
        self.info['Start Date']>other.info['End Date']):
      return False
    
    # If not on the same day, no conflict
    if self.info['Day']!=other.info['Day']:
      return False
    
    # If times do not overlap, no conflict
    if (self.info['End Time']<other.info['Start Time'] or
        self.info['Start Time']>other.info['End Time']):
      return False
    
    return True
  
  def getduration(self):
    """return the duration of this meeting"""
    
    start = self.info['Start Time']
    if start==0:
      start = 24
    end = self.info['End Time']
    hrs = end.hour-start.hour
    mins = end.minute-start.minute
    return dt.timedelta(0,0,0,0,mins,hrs)
  
  def getnummeets(self):
    """return the number of times this meeting will occur"""
    
    meets = 0
    current = self.info['Start Date']
    end = self.info['End Date']
    daynum = ['M','T','W','R','F','S','U'].index(self.info['Day'])
    while current<=end:
      if current.weekday()==daynum:
        meets += 1
    return meets

class ClassMeeting(Meeting):
  """ClassMeetings also have an instructor"""
  
  def __init__(self,info,eve):
    """create a new ClassMeeting with the given info"""
    
    self.FIELDS = ({ 'Start Date' : dt.date,
                     'End Date'   : dt.date,
                     'Day'        : str,
                     'Start Time' : dt.time,
                     'End Time'   : dt.time,
                     'Location'   : str,
                     'Instructor' : str })
    
    self.event = eve
    self.initinfo(info)
    self.checkparams()
  
  def __eq__(self,obj):
    """override == operator"""
    
    return isinstance(obj,ClassMeeting) and self.info == obj.info
    
  def __ne__(self,obj):
    """override != operator"""
    
    return not self==obj
