#!/usr/bin/env python
#
# A schedule class to keep track of classes
#
# Author: Joshua A Haas

import event

class Schedule:
  
  def __init__(self,events=None):
    """create a new schedule to keep track of events with meetings"""
    
    self.events = []
    if events is not None:
      self.events = self.addevents(events)
  
  def __eq__(self,obj):
    """override == operator"""
    
    return isinstance(obj,Schedule) and self.events == obj.events
    
  def __ne__(self,obj):
    """override != operator"""
    
    return not self==obj

  def getevents(self,types=None,fields=None,meet=None):
    """return all events that match search criteria"""
    
    matches = self.geteventinds(types,fields,meet)
    return [self.events[i] for i in matches]

  def geteventinds(self,types=None,fields=None,meet=None):
    """return all event indices that match search criteria"""
    
    if (types is None) and (fields is None) and (meet is None):
      return range(0,len(self.events))
    
    matches = []
    for (i,eve) in enumerate(self.events):
      if (types is not None) and (not issubclass(eve.__class__,types)):
        continue
      if fields is not None:
        match = True
        info = eve.getinfo()
        for key in fields.keys():
          if (key not in info) or (info[key]!=fields[key]):
            match = False
            break
        if not match:
          continue
      if (meet is not None) and (len(eve.getmeetinds(meet))==0):
        continue
      matches.append(i)
    return matches
  
  def getmeets(self,search=None):
    """return all meets that match search"""
    
    matches = self.getmeetinds(search)
    return [self.events[i].meets[j] for (i,j) in matches]
    
  def getmeetinds(self,search=None):
    """return all (event,meet) index tuples that match search"""
    
    if search is None:
      x = []
      for i in range(0,len(self.events)):
        for j in range(0,len(self.events[i].meets)):
          x.append((i,j))
      return x
      
    matches = []
    for (i,eve) in enumerate(self.events):
      eventmatches = eve.getmeetinds(search)
      for j in eventmatches:
        matches.append((i,j))
    return matches

  def addevent(self,eve):
    """add the event to this Schedule"""
  
    if not issubclass(eve.__class__,event.Event):
      raise TypeError('Input must be subclass of Event')
    self.events.append(eve)
  
  def addevents(self,events):
    """add the events to this Schedule"""
  
    if issubclass(events.__class__,event.Event):
      self.addevent(events)
    else:
      if not isinstance(events,list):
        raise TypeError('Input must be subclass of Event or list of such')
      for eve in events:
        self.addevent(eve)
  
  def removeevents(self,types=None,fields=None,meet=None):
    """remove events that match the search criteria or all if no search"""
    
    if search is None:
      self.events = []
    else:
      matches = self.geteventinds(types,fields,meet)
      matches.sort(reverse=True)
      for ind in matches:
        del self.events[ind]

  def getconflicts(self):
    """return a list of tuples of conflicting meetings"""
    
    conflicts = []
    meets = self.getallmeets()
    for i in range(0,len(meets)):
      meet1 = meets[i]
      for j in range(i+1,len(meets)):
        meet2 = meets[j]
        if meet1.conflicts(meet2):
          conflicts.append((meet1,meet2))
    return conflicts
    
  def getallmeets(self):
    """return a list of all the meets in all my events"""
    
    meets = []
    for eve in self.events:
      for meet in eve.meets:
        meets.append(meet)
    return meets

  def strf(self,eventfields=None,meetfields=None,sep=' - ',tab='  '):
    """print all events and meets according to params"""
    
    if eventfields is None:
      eventfields = ['Title']
    if meetfields is None:
      meetfields = ['Day','Start Time','End Time']
    
    s = ''
    for e in self.events:
      es = ''
      for ef in eventfields:
        if ef in e.info.keys():
          es += (str(e.getinfo(ef))+sep)
      s += (es[:-len(sep)]+'\n')
      for m in e.meets:
        ms = tab
        for mf in meetfields:
          if mf in m.info.keys():
            ms += (str(m.getinfo(mf))+sep)
        s += (ms[:-len(sep)]+'\n')
    return s[:-2]

  def tohtml(self):
    """write the schedule as a pretty and to-scale html table"""
    
    raise NotImplementedError
