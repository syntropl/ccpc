from datetime import datetime

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError

from date_utility import Int_To_Weekday 
from date_utility import DateOfNearestSpecificDayOfWeek

#______________________________ DATABASE SETUP (SQLalchemy)


database_path = 'convict_conditioning_1.db'
engine = create_engine(f'sqlite:///{database_path}')

Base = declarative_base()
metadata = MetaData(bind=engine)
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

    def GetRecordsOfThis(self):
        ex = session.query(Variant_Planned_Or_Executed).filter_by(executed_date is not None)

#               get sessions with this group
#     #         find variant with highest id where both eval are acceptable
                    # pushups:incline:3
                    # squats:shoulderstand:2
                    # etc

class Exercise_Variant(Base):
     __table__ = Base.metadata.tables['exercise_variants']

class Variant_Planned_Or_Executed(Base):
     __table__ = Base.metadata.tables['work_planned_or_executed']

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
        return session.query(Exercise_Work_Session_For_Day).filter_by(program_id=self.id)
    
    def GetWorkForWeekday(self, weekday:int):
        return session.query(Exercise_Work_Session_For_Day).filter_by(program_id=self.id,  session_weekday=weekday)
    
    
    def GetNextSessionWeekday(self):  ## GetNextSessionDate

              
        today = datetime.today().weekday()

       # establish which weekdays are in program 
        schedule = self.GetSchedule()
        workingWeekdays = []
        for elem in schedule:
            workingWeekdays.append(elem.session_weekday)
       
       #starting today, loop and check for exectuted todays sessions
        considered_weekday = today
        for i in range(0,6):
            if considered_weekday in workingWeekdays:
                return considered_weekday
            considered_weekday = (today + i)%6
    
    def nearestWorkWeekday(self):
         
        nearestWorkWeekday=  Int_To_Weekday(current_program.GetNextSessionWeekday())
        nearestWorkDate = DateOfNearestSpecificDayOfWeek(nearestWorkWeekday)
        print(f"nearest work weekday: {nearestWorkDate}\n\n")
        return nearestWorkDate



class Exercise_Work_Session_For_Day(Base): 
    __table__=Base.metadata.tables['exercise_work_sessions_for_program_days']
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



#________________________________ CONTROLLERS

# plan next  session 
# get user program
# get next training day number in program
# get sessions pattern for next training day


#____________________________________ START GETTING DATA AS OBJECTS

print(f"user.id : {user.id}")
print(f"program : {current_program.name} \n")
for elem in program_schedule:
    min_worksets = elem.minimum_sessions_in_a_day
    max_worksets = elem.maximum_sessions_in_a_day
    worksets_repr = ""
    if min_worksets == max_worksets:
        worksets_repr = min_worksets
    else:
        worksets_repr = f"{min_worksets} - {max_worksets}"
    print(f"{Int_To_Weekday(elem.session_weekday)} :  {elem.GetGroup().name} / {worksets_repr} sessions\n ")


print("checking sessions recorded or planned:")

int_next_work_weekday = current_program.GetNextSessionWeekday()
nearestWorkWeekday = Int_To_Weekday(int_next_work_weekday)
nearestWorkDate = DateOfNearestSpecificDayOfWeek(int_next_work_weekday)
print(f"today as int: {datetime.today().weekday()}")
print(f"nearest work weekday int: {nearestWorkDate.weekday()}\n\n")

AllRecords = session.query(Variant_Planned_Or_Executed).all()

# if session.query(Variant_Planned_Or_Executed).first() is None:
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
    



# for s in session.query(Variant_Planned_Or_Executed).all().count:
#     print(f"session : {s}")

# print(session.query(Exercise_Variant).first().variant_name)
    # print(f"session : {xv.name}")
    # print(f"session : {xv.instruction}")

    
print("\n")
print(f"next session in {current_program.name} program is on  : {Int_To_Weekday(current_program.GetNextSessionWeekday())}      //// TODO: check for todays records ")

for work_session in current_program.GetWorkForWeekday(1):
    group_name = work_session.group.name
    print(group_name)
    # print(session.query(Exercise_Group).filter_by(id=).one().name)
    


print("\n")






    # create session objects and for each
    #       for each exercise group establish level and sublevel:
#               get sessions with this group
#     #         find variant with highest id where both eval are acceptable
                    # pushups:incline:3
                    # squats:shoulderstand:2
                    # etc
#   return info on current variant and sublevel for each group
#               for each session
    #               add row to plan element (this will be reflected in view)



    #exercise_variants = session.query(Exercise_Variant).all()
# variant_planned_or_executed

def Get_Progress_Status(exercise_group_id):
    for group in exercise_groups:
        print()

print("____________________________________________________END")
print("\n")