#!/usr/bin/env python
#
# A class for events in a schedule
#
# Author: Joshua A Haas

import util

import meeting

class Event:
  
  def __init__(self,info,meets=None):
    """create a new Elass with the given info"""
    
    self.FIELDS = ({ 'Title' : str,
                     'Type'  : str })
    
    self.initinfo(info)
    self.initmeets(meets)
  
  def __eq__(self,obj):
    """override == operator"""
    
    return isinstance(obj,Event) and self.info == obj.info
    
  def __ne__(self,obj):
    """override != operator"""
    
    return not self==obj

  def initinfo(self,info):
    """initialize info dict"""
    
    self.info = util.blankdict(self.FIELDS.keys())
    util.checkdict(info,self.FIELDS.keys())
    self.importinfo(info)

  def initmeets(self,meets):
    """initialize meets list"""
    
    self.meets = []
    if meets is not None:
      self.meets = self.addmeets(meets)
  
  def getinfo(self,field=None):
    """return the requested info, or the entire dict if not specified"""
    
    if field is None:
      return self.info
    return self.info[field]
  
  def importinfo(self,info):
    """import info from the dict info into this class"""
    
    self.info = util.updatedict(self.info,info)

  def getmeetinds(self,search=None):
    """return the meeting that matches the search criteria, or
    return a list of all meetings if no criteria specified"""
    
    if search is None:
      return range(0,len(self.meets))
    matches = []
    for (i,meet) in enumerate(self.meets):
      match = True
      info = meet.getinfo()
      for key in search.keys():
        if (key not in info) or (info[key]!=search[key]):
          match = False
          break
      if match:
        matches.append(i)
    return matches

  def getmeets(self,search=None):
    """return meeting.Meetings instead of indices"""
    
    matches = self.getmeetinds(search)
    return [self.meets[i] for i in matches]

  def addmeet(self,meet):
    """Add a meeting time for this Event"""
    
    if not issubclass(meet.__class__,meeting.Meeting):
      raise TypeError('Input must be subclass of Meeting')
    self.meets.append(meet)
  
  def addmeets(self,meets):
    """add several meeting times for this Event"""
    
    if issubclass(meets.__class__,meeting.Meeting):
      self.addmeet(meets)
    else:
      if not isinstance(meets,list):
        raise TypeError('Input must be subclass of Meeting or List of such')
      for meet in meets:
        self.addmeet(meet)
  
  def removemeets(self,search=None):
    """remove meets that match the search criteria or all if no search"""
    
    if search is None:
      self.meets = []
    else:
      matches = self.getmeetinds(search)
      matches.sort(reverse=True)
      for ind in matches:
        del self.meets[ind]

  def conflicts(self,other):
    """return whether this event has any conflicts with other"""
    
    meets = self.meets
    others = other.meets
    for meet in meets:
      for other in others:
        if meet.conflicts(other):
          return True
    return False

# The Class class (becuase I can) to keep track of classes in a schedule
# subclass of Event
#
# Author: Joshua A Haas

class Class(Event):
  
  def __init__(self,info,meets=None):
    """create a new Class with the given info"""
    
    self.FIELDS = ({ 'CRN'        : int,
                     'Course'     : str,
                     'Title'      : str,
                     'Campus'     : str,
                     'Credits'    : float,
                     'Level'      : str,
                     'Type'       : str })
    
    self.initinfo(info)
    self.initmeets(meets)
  
  def __eq__(self,obj):
    """override == operator"""
    
    return isinstance(obj,Class) and self.info == obj.info
    
  def __ne__(self,obj):
    """override != operator"""
    
    return not self==obj
