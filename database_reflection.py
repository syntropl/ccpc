from datetime import datetime

from sqlalchemy import create_engine, MetaData, not_
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base


#from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from date_utility import Int_To_Weekday 
from date_utility import DateOfNearestSpecificDayOfWeek
from date_utility import TodayWeekday

#______________________________ DATABASE SETUP (SQLalchemy)


database_path = 'convict_conditioning_1.db'
engine = create_engine(f'sqlite:///{database_path}')


metadata = MetaData()
Base = declarative_base(metadata=metadata)
Base.metadata.reflect(engine)

Session = sessionmaker(bind=engine)
session = Session()

#___ i dont know yet where to put it:
weekdays = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}


#______________________________ CLASSES TO REFLECT DATABASE TABLE ROWS

class Exercise_Group(Base):
    """ORM reflection of db row in table exercise_groups
    in paul wade's convict conditioning he calls them big six: pushups, squats, pullups, leg raises, bridges, and handstand pushups
    class Exercise_Variant objects point to one of those six"""
    
    __table__ = Base.metadata.tables['exercise_groups']

    current_variant_id = __table__.c.current_variant_id
   # current_variant = relationship("Exercise_Variant")
    current_variant = relationship("Exercise_Variant", foreign_keys=[current_variant_id], uselist=False)

    
    def GetRecordsOfThis(self):
        all_executed_work_in_this_group = session.query(Variant_Planned_Or_Executed)\
            .filter(Variant_Planned_Or_Executed.group_id == self.id)\
            .filter(Variant_Planned_Or_Executed.executed_datetime != None)\
            .filter(Variant_Planned_Or_Executed.is_warmup == 0)\
            .filter(Variant_Planned_Or_Executed.is_early_attempt_aka_consolidation == 0)\
            .filter(Variant_Planned_Or_Executed.self_eval_TECHNICAL_CORRECTNESS > 6)\
            .filter(Variant_Planned_Or_Executed.self_eval_WAS_FULLY_EXECUTED == 1)\
            .all()

        return all_executed_work_in_this_group
        

    def GetLastProgressionRecord(self):
        print(f"getting last progression record for {self.name}")
        highest_executed_step = 0
        candidate_record = None       
        for record in self.GetRecordsOfThis():
            # ignore incomplete records
            if\
                record.variant_id is  None \
                or record.exercise_variant_sublevel is None:
                print("considered record has no data in variant_id column or exercise_variant_sublevel column")
            else:
      
                candidate_record = record
                print(record.variant.name)
                print(f"looking at: {record.variant.name} - sublevel {record.exercise_variant_sublevel}")
                if candidate_record.variant.id % 10 >  highest_executed_step:
                    highest_executed_step = candidate_record.id %10
        
        if candidate_record is None:
            print ("no record found")
        return candidate_record

            
                

    # def GetHighestAcceptableWorkRecord(self):
    #     print(f"current variant: \n {self.current_variant.name}")
    #     print(f"current variant name {self.current_variant.name}")
    #     highest_executed_step = 0
    #     candidate_record = None
    #     for record in self.GetRecordsOfThis():
    #         print(f"highest_executed_step {highest_executed_step }")
    #         candidate_record  = record.variant
    #         print(f"candidate_record = {candidate_record.id} {candidate_record.name}")
    #         print(f"step = {candidate_record.id %10}")   
    #         if candidate_record.id % 10   > highest_executed_step:
    #             highest_executed_step = candidate_record.id %10
    #     return candidate_record

     
    def GetSublevelOfCurrentVariant(self):
        print("finding sublevel")
      
        #find records of highest variant
        print("Getting records of {self.name}")
        #get the one with highest date
        print("getting last record")
        record = self.GetLastProgressionRecord()
        print(f"{record.exercise_variant_sublevel} executed {record.executed_datetime}")
        #get its sublevel
        print(f"{self.name}{self.current_variant.name}")

        return -1
    
    def UpdateUserAdvanecmentLevel(self):
        
        lastAdequateSession = self.GetLastProgressionRecord()
        
        if lastAdequateSession is None:
            print(f"{self.name}.GetLastProgressionRecord() returned None")
        else: 
            print(f"updating {self.name} row in table Exercise_Groups")
            self.current_variant_id =  lastAdequateSession.variant_id 
            self.current_variant_sublevel = self.GetSublevelOfCurrentVariant()
            print(f"current_variant_id = {self.current_variant_id}")
            print(f"current_variant_sublevel =  {self.current_variant_sublevel}")  
        
        if self.current_variant is None:
            print(f"{self.name}: current_variant was not set ")
        if self.current_variant_sublevel is None:
            print(f"{self.name}: current_variant_sublevel was not set ")

     
    def PrintCurrentProgressLevel(self):
        v = self.current_variant
        if v == [] or v==None:
            print("user advancement level is not set")
            print("TODO -> calculate user advancement level and store it in excercise group rows in function: Excercise_Group.GetSublevelOfCurrentVariant()")
            self.UpdateUserAdvanecmentLevel()

        else:
            sublevel = self.current_variant_sublevel
            sets = -1
            reps = -1
            unit = 'reps'
            if v.read_reps_as_seconds:
                unit = 'seconds'
            
            print(f"{v.name} sublevel: {sublevel}")

            if sublevel == 1:
                sets = v.sublevel1_sets_amount
                reps = v.sublevel1_reps_in_set     
            elif sublevel == 2:
                sets = v.sublevel2_sets_amount
                reps = v.sublevel2_reps_in_set   
            elif sublevel == 3:
                sets = v.sublevel3_sets_amount
                reps = v.sublevel3_reps_in_set
            else:
                print("exercise_variant_sublevel value must be 1-3")
            print(f"{sets} sets of {reps} {unit}")      

            
#               get sessions with this group
#     #         find variant with highest id where both eval are acceptable
                    # pushups:incline:3
                    # squats:shoulderstand:2
                    # etc


    

class Exercise_Variant(Base):
     __table__ = Base.metadata.tables['exercise_variants']
     group_id = __table__.c.group_id
    #  exercise_group = relationship("Exercise_Group")
     exercise_group = relationship("Exercise_Group", 
                                  foreign_keys=[group_id])

class Variant_Planned_Or_Executed(Base):
     __table__ = Base.metadata.tables['work_planned_or_executed']
     group_id = __table__.c.exercise_group_id
     group = relationship("Exercise_Group")
     variant_id = __table__.c.exercise_variant_id
    #  variant = relationship("Exercise_Variant") 


class User(Base):
    __table__ = Base.metadata.tables['user']
    program_id = __table__.c.current_program
    current_program = relationship("Program")


    def AddPlannedSession(
        self,
        planned_datetime: datetime,
        executed_datetime: datetime,
        exercise_variant_id: int,
        exercise_variant_sublevel: int,
        is_warmup: int,
        is_early_attempt_aka_consolidation: int
    ):
        # TYPE CHECKS AND ERROR MESSAGES
        if not isinstance(planned_datetime, datetime):
            raise TypeError("planned_datetime must be a datetime object")
        # if not isinstance(executed_datetime, datetime):
        #     raise TypeError("executed_datetime must be a datetime object")

        if not isinstance(exercise_variant_id, int) or not (0 <= exercise_variant_id <= 60):
            raise ValueError("exercise_variant must be an integer between 0 and 60") #because this is how many exercises are in convict conditining book by paul wade

        if not isinstance(exercise_variant_sublevel, int) or not (1 <= exercise_variant_sublevel <= 3):
            raise ValueError("exercise_variant_sublevel must be an integer between 1 and 3")

        if not isinstance(is_warmup, int) or is_warmup not in (0, 1):
            raise ValueError("is_warmup must be an integer 0 or 1")

        if not isinstance(is_early_attempt_aka_consolidation, int) or is_early_attempt_aka_consolidation not in (0, 1):
            raise ValueError("is_early_attempt_aka_consolidation must be an integer 0 or 1")
        
#_______________________________________________________________________________
#
#                             WRITING USER WORK TO DATABASE
#_______________________________________________________________________________
        variant_planned_or_executed = Variant_Planned_Or_Executed(
            planned_datetime=planned_datetime,
            executed_datetime=executed_datetime,
            exercise_variant_id =exercise_variant_id,
            exercise_variant_sublevel=exercise_variant_sublevel,
            is_warmup=is_warmup,
            is_early_attempt_aka_consolidation=is_early_attempt_aka_consolidation
        )

        try:
            session.add(variant_planned_or_executed)
            session.commit()
            print("new row added to database")
            print(variant_planned_or_executed.planned_datetime)
            return variant_planned_or_executed
        
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            session.rollback()
            return None
#_______________________________________________________________________________
        

        


    # def GetCurrentProgram(self):
    #     return session.query(Program).filter_by(id=user.current_program).first()

class Program(Base):
    __table__ = Base.metadata.tables['programs']
        
    def GetSchedule(self):
        return session.query(Exercise_Workday_Model_For_Day).filter_by(program_id=self.id)
    
    def GetWorkForWeekday(self, weekday:int):
        return session.query(Exercise_Workday_Model_For_Day).filter_by(program_id=self.id,  weekday=weekday)
    
    def GetWorkForNearestWorkday(self):
        return self.GetWorkForWeekday(TodayWeekday())

    def GetNextSessionWeekday(self):  ## GetNextSessionDate

              
        # today = datetime.today().weekday()
        today = TodayWeekday()
       # establish which weekdays are in program 
        schedule = self.GetSchedule()
        workingWeekdays = []
        for elem in schedule:
            workingWeekdays.append(elem.weekday)
       
       #starting today, loop and check for exectuted todays sessions
        considered_weekday = today
        for i in range(0,6):
            if considered_weekday in workingWeekdays:
                return considered_weekday
            considered_weekday = (today + i)%6
    
    # def NearestWorkWeekday(self):
         
    #     nearestWorkWeekday=  Int_To_Weekday(current_program.GetNextSessionWeekday())
    #     nearestWorkDate = DateOfNearestSpecificDayOfWeek(nearestWorkWeekday)
    #     print(f"nearest work weekday: {nearestWorkDate}\n\n")
    #     return nearestWorkDate
    
    def UpdateProgressLevels():
        
        
        print("TODO -> fetch executed sessions evaulated good or better and in each group update variant and sublevel")
        # for group in session.query(Exercise_Group).all():
        #     group.UpdateUserAdvanecmentLevel()

        return



class Exercise_Workday_Model_For_Day(Base): 
    __table__=Base.metadata.tables['exercise_workday_models_for_program_days']
    program_id = __table__.c.program_id
    program = relationship("Program")
    exercise_group_id = __table__.c.exercise_group_id 
    group = relationship("Exercise_Group")
    # def GetGroupName(self):
    #     return session.query(Exercise_Group).filter_by(id=self.exercise_group_id).one().name
    


    def GetGroup(self): ## this should be done using sqlalchemy relationhsip syntax 
        return session.query(Exercise_Group).filter_by(id=self.exercise_group_id).one()
    



#______________________________ INSTANTIATE NEEDED INSTANCES

print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
user = session.query(User).one()
current_program = user.current_program
program_schedule = current_program.GetSchedule()





#____________________________________ START GETTING DATA AS OBJECTS

print(f"user.id : {user.id}")
print(f"program : {current_program.name} \n")
for elem in program_schedule:
    min_worksets = elem.min_worksets
    max_worksets = elem.max_worksets
    worksets_repr = ""
    if min_worksets == max_worksets:
        worksets_repr = min_worksets
    else:
        worksets_repr = f"{min_worksets} - {max_worksets}"
    print(f"{Int_To_Weekday(elem.weekday)} :  {elem.GetGroup().name} / {worksets_repr} sessions\n ")



int_next_work_weekday = current_program.GetNextSessionWeekday()
nearestWorkWeekday = Int_To_Weekday(int_next_work_weekday)
nearestWorkDate = DateOfNearestSpecificDayOfWeek(int_next_work_weekday)
print(f"today is {Int_To_Weekday(datetime.today().weekday())}")
print(f"nearest work weekday: {Int_To_Weekday(nearestWorkDate.weekday())}\n\n")



AllRecords = session.query(Variant_Planned_Or_Executed).all() #this should be used in smaller scope and discarded after needed

if  len(AllRecords) == 0:
    print ("there are no records.     -> TODO for each exercise group assume sublevel1 of first step")
     
    user.AddPlannedSession(datetime.now(),0, 23, 1,0,0)
    print( "TODO: get next session weekday and find return its date")

    nearestWorkWeekday = Int_To_Weekday(current_program.GetNextSessionWeekday())
    nearestWorkDate = DateOfNearestSpecificDayOfWeek(nearestWorkWeekday)
    print(f"nearest work weekday: {nearestWorkDate}\n\n")
    
else:
    print("db table work_planned_or_executed contains the following records:")
    for record in AllRecords:

        print(record.planned_datetime)

        # TODO populate with data from function arguments
            # executed_datetime =  None,
            # exercise_variant_id = 23,
            # exercise_variant_sublevel = 1
            # is_warmup = 0
            # is_early_attempt_aka_consolidation = 0
    

    
print("\n")
print(f"next session in {current_program.name} program is on  : {Int_To_Weekday(current_program.GetNextSessionWeekday())}      //// TODO: check for todays records ")

program_for_today = current_program.GetWorkForNearestWorkday()
for work_session in program_for_today:
    min_worksets = work_session.min_worksets
    max_worksets = work_session.max_worksets

    if max_worksets==min_worksets:
        print(f"{min_worksets} worksets:")
    else: 
        print(f"{work_session.min_worksets} to {work_session.max_worksets} worksets:")
    work_session.group.PrintCurrentProgressLevel()
    


# plan next  session 
# user.current_program
# get next training day number in program
# get sessions pattern for next training day
#   after group variant and sublevel updated:
#               for each program day session
    #               add row to plan element (this will be reflected in view)


# for group in session.query(Exercise_Group).all():
#     if group.id < 6: # focusing only on big 6
#         group.PrintCurrentProgressLevel()


# for group in session.query(Exercise_Group).all():
#     if group.id > 6: # focusing only on big 6
#         break

#     print("\n...")
#     print(group.name)
#     v = group.current_variant
#     if v == [] or v == None:
#         print("user advancement level is not set")
#         print("TODO -> calculate user advancement level and store it in excercise group rows in function: Excercise_Group.GetSublevelOfCurrentVariant()")
#         group.UpdateUserAdvanecmentLevel()
#     else:
#         v_name = v.name
#         v_sublevel = group.current_variant_sublevel
#         sets_amount = -1
#         reps_in_set = -1
#         unit = "reps"
#         if v.read_reps_as_seconds:
#             unit = "seconds"

#         print(f"{v_name} sublevel {v_sublevel}")
        
#         if v_sublevel == 1:
#             sets_amount = v.sublevel1_sets_amount
#             reps_in_set = v.sublevel1_reps_in_set     
#         elif v_sublevel == 2:
#             sets_amount = v.sublevel2_sets_amount
#             reps_in_set = v.sublevel2_reps_in_set   
#         elif v_sublevel == 3:
#             sets_amount = v.sublevel3_sets_amount
#             reps_in_set = v.sublevel3_reps_in_set
#         else:
#             print("exercise_variant_sublevel value must be 1-3")
#         print(f"{sets_amount} sets of {reps_in_set} {unit}")      

    print(":::::")
    print("\n")

print("____________________________________________________END")
print("\n")