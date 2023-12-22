from datetime import datetime
from sqlalchemy import func
from sqlalchemy import create_engine, MetaData, Column, Integer, not_
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


database_path = 'DATA/convict_conditioning_1.db'
engine = create_engine(f'sqlite:///{database_path}')


metadata = MetaData()
metadata.reflect(engine)

Base = declarative_base(metadata=metadata)
Base.metadata.reflect(engine)

Session = sessionmaker(bind=engine)
session = Session()

def WRITE_TO_DATABASE(db_session, ormRowObject):
    print("adding new row to database")
    try:
        db_session.add(row)
        db_session.commit()
        print("new row added to database")
        return row
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        db_session.rollback()
        return None
    


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


        
    def GetRepsInSetForCurrentSublevel(self): 
        v = self.current_variant
        if v == [] or v==None:
            print("user advancement level is not set")
            print("TODO -> calculate user advancement level and store it in excercise group rows in function: Excercise_Group.GetSublevelOfCurrentVariant()")
            self.UpdateUserAdvanecmentLevel()

        else:
            sublevel = self.current_variant_sublevel
            sets = -1   # this code could be used to get sets as well
            reps = -1

            sets = v.SublevelSetsAmount(sublevel)
            reps = v.SublevelRepsInSet(sublevel)

            unit = 'reps'
            if v.read_reps_as_seconds:
                unit = 'seconds'
            
            print(f"{v.name} sublevel: {sublevel}")

            print(f"{sets} sets of {reps} {unit}")
        return reps      

            
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
     
    def SublevelSetsAmount(self, sublevel : int):
         ''' Returns number of sets in a workout for given sublevel 1-3'''
         if sublevel == 1:
            return self.sublevel1_sets_amount
         if sublevel == 2:
            return self.sublevel2_sets_amount
         if sublevel == 3:
            return self.sublevel3_sets_amount
         else:
            raise ValueError("sublevel must be 1-3")
            
    def SublevelRepsInSet(self, sublevel : int):
        ''' Returns numer reps in one set in a workout for given sublevel 1-3'''
        if sublevel == 1:
            return self.sublevel1_reps_in_set
        if sublevel == 2:
            return self.sublevel2_reps_in_set
        if sublevel == 3:
            return self.sublevel3_reps_in_set
        else:
             raise ValueError("sublevel must be 1-3")
         
class Variant_Planned_Or_Executed(Base):
     __table__ = Base.metadata.tables['work_planned_or_executed']
     
     workout_id = __table__.c.workout_id
     workout = relationship("Workout")

     group_id = __table__.c.exercise_group_id
     group = relationship("Exercise_Group")

     variant_id = __table__.c.exercise_variant_id
     variant = relationship("Exercise_Variant") 

class Workout(Base):
    '''reference class to hold elements of represented by Variant_Planned_Or_Executed
    they are linked by foreign key field .workout in Variant_Planned_Or_Executed. 
    It is intended to be used to streamline data gathering for presentation in user's workout session'''
    __table__ = Base.metadata.tables['workouts']

    # elements = relationship("Variant_Planned_Or_Executed", secondary="work_planned_or_executed")

    def AddPlannedWork(
        self,
        exercise_variant_id: int,   
        exercise_variant_sublevel: int,
        is_warmup: int,
        is_early_attempt_aka_consolidation: int,
        planned_reps : int
    ):
        # TYPE CHECKS AND ERROR MESSAGES

        if not isinstance(exercise_variant_id, int) or not (0 <= exercise_variant_id <= 60):
            raise ValueError("exercise_variant must be an integer between 0 and 60") #because this is how many exercises are in convict conditining book by paul wade

        if not isinstance(exercise_variant_sublevel, int) or not (0 <= exercise_variant_sublevel <= 3):
            raise ValueError("exercise_variant_sublevel must be an integer between 1 and 3 or 0 if not actual training")

        if not isinstance(is_warmup, int) or is_warmup not in (0, 1):
            raise ValueError("is_warmup must be an integer 0 or 1")

        if not isinstance(is_early_attempt_aka_consolidation, int) or is_early_attempt_aka_consolidation not in (0, 1):
            raise ValueError("is_early_attempt_aka_consolidation must be an integer 0 or 1")
        



        variant_planned = Variant_Planned_Or_Executed(
            exercise_variant_id =exercise_variant_id,
            exercise_variant_sublevel=exercise_variant_sublevel,
            is_warmup=is_warmup,
            is_early_attempt_aka_consolidation=is_early_attempt_aka_consolidation,
            workout_id = self.id,
            planned_reps = planned_reps
        )
        print(f"writing plan to database: {variant_planned.variant.name} {variant_planned.planned_reps} reps")
        
        WRITE_TO_DATABASE(session, variant_planned)
        
        # make sure this is repeated in the right moment for the right column
        return variant_planned


    def AddWarmup(self, variant_id : int, reps : int):
        work = self.AddPlannedWork(
            variant_id = variant_id, 
            sublevel = 0, 
            is_warmup = 1, 
            is_early_attempt_aka_consolidation = 0, 
            planned_reps = reps
        )

        return work

    def AddConsolidationWork(self, variant_id, reps):
        work = self.AddPlannedWork(
            variant_id,
            sublevel=0,
            is_warmup=0,
            is_early_attempt_aka_consolidation=1,
            planned_reps=reps
        ) 
    def PlanSequence(self, group1:Exercise_Group, group2: Exercise_Group, group3=None):
        groups = []
        groups.append(group1)
        groups.append(group2)
        if group3:
            groups.append(group3)
        
        for group in groups:
            level = group.current_variant % 10
            variant_id = group.current_variant_id
            sublevel = group.current_variant_sublevel
            
            ## PLAN WARMUPS
            if level == 1:
                break
            if level == 2:
                self.AddWarmup(variant_id-1, 15)
            if level == 3:
                self.AddWarmup(variant_id-1, 15)
                self.AddWarmup(variant_id-2, 10)
            if level == 4:
                self.AddWarmup(variant_id-2, 15)
                self.AddWarmup(variant_id-1, 10)
            if level == 5:
                self.AddWarmup(variant_id-3, 15)
                self.AddWarmup(variant_id-2, 10)           
            if level == 6:
                self.AddWarmup(variant_id-4, 15)
                self.AddWarmup(variant_id-2, 10)                   
            if level > 6:
                self.AddWarmup(variant_id-5, 15)
                self.AddWarmup(variant_id-3, 10)   

            ## ADD WORK SESSIONS

            sets =group.current_variant.SublevelSetsAmount()
            reps = group.current_variant.SublevelRepsInSet()
            # number of sets

            for set in range(sets):
                self.AddPlannedWork(
                    variant_id,
                    sublevel,
                    is_warmup = 0,
                    is_early_attempt_aka_consolidation= 0,
                    planned_reps=reps)

    



class User(Base):
    __table__ = Base.metadata.tables['user']
    program_id = __table__.c.current_program
    current_program = relationship("Program")

    def printAllWorkouts(self):
        workouts = session.query(Workout).all()
        print("_________________________________")
        print("\n")
        for workout in workouts:
            print(f"workout date:  {workout.date_planned} ")
            moves = session.query(Variant_Planned_Or_Executed).filter_by(workout_id = workout.id)
            for move in moves:
                print(move.variant.name)
            print("\n\n")


 

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

    def GetTodayWorkouts(self):
        today = datetime.now().date()
        return session.query(Workout).filter(func.date(Workout.date_planned) == today).all()
    
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


        

    def CreateNearestWorkout(self):
        print("todo: add check if there is not already a todays session")
        int_next_work_weekday = current_program.GetNextSessionWeekday()
        self.CreateWorkoutsForNearestWeekday(int_next_work_weekday)
    
    def CreateWorkoutsForNearestWeekday(self, weekday : int):
        day_work_elements = current_program.GetWorkForWeekday(weekday).all()
        if len(day_work_elements)==0:
            print(f"program {self.name} does not contain work for {Int_To_Weekday(weekday)}")
            return
        date = DateOfNearestSpecificDayOfWeek(weekday)
        print(f"creating workouts for nearest: {Int_To_Weekday(weekday)}   {date}\n\n")
     
      # go through groups and get max max_worksets among them
        largest_max_worksets_among_all_days_groups = 0
        for workday_model in day_work_elements:
            if workday_model.max_worksets < largest_max_worksets_among_all_days_groups:
                largest_max_worksets_among_all_days_groups = workday_model.max_worksets
 
        # create as many workouts and hold them in a list
        newWorkouts = []
        for i in range(largest_max_worksets_among_all_days_groups):
            required = 1
            print("todo - when to mark workouts as not required for progression")

            newWorkout = Workout(planned_date = date ,is_required_for_progression = 1)
            WRITE_TO_DATABASE(session, newWorkout)
            newWorkouts.append(newWorkout)
        # for each workout call PlanSequence
        groups = []
        for workday_model in day_work_elements:
            groups.append(workday_model.group)
        group1 = groups[0]
        group2 = groups[1]
        group3 = None
        if len(groups)>2:
            group3 = groups[2]
        
        for workout in newWorkouts:
            workout.PlanSequence(group1, group2, group3)
        


        #CONSIDER PUTTING THIS IN AN AGGREGATING CLASS
        for workday_model in day_work_elements:
            group = workday_model.group
            variant = group.current_variant
            variant_sublevel = group.current_variant_sublevel
            sets_amount = variant.SublevelSetsAmount(variant_sublevel)
            reps_in_set = variant.SublevelRepsInSet(variant_sublevel)
            min_worksets = workday_model.min_worksets
            max_worksets = workday_model.max_worksets
            unit = "reps"
            if variant.read_reps_as_seconds:
                unit = "seconds"

            print(variant.name)
            print(f"{min_worksets} to {max_worksets} workouts of:")
            print(f"        {sets_amount} sets of {reps_in_set} {unit}")

            for i in range(max_worksets):
                required = 1
                if i > (min_worksets-1):
                    print("\n if i > (min_worksets-1):")
                    print(f" i = {i} ")
                    print(f"min worksets  = {min_worksets}")
                    required = 0
            NewWorkout = Workout(date_planned = date)

        


        

    def printSchedule(self, program_schedule : list):
        '''as argument pass a list of workday models'''
        for elem in program_schedule:
            min_worksets = elem.min_worksets
            max_worksets = elem.max_worksets
            worksets_repr = ""
            if min_worksets == max_worksets:
                worksets_repr = min_worksets
            else:
                worksets_repr = f"{min_worksets} - {max_worksets}"
            print(f"{Int_To_Weekday(elem.weekday)} :  {elem.GetGroup().name} / {worksets_repr} sessions\n ")


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
print("\n\n PROGRAM START\n\n")

print(f"user.id : {user.id}")
print(f"program : {current_program.name} \n")
current_program.printSchedule(program_schedule)



#____________________________________ CREATE NEW USER WORKOUT
print("\n\ncalling current_program.CreateNearestWorkout()\n\n\n")
current_program.CreateNearestWorkout()

user.printAllWorkouts()

print("TODO now  instantiate workout and Workout.Add.. functions to populate a workout")

print("____________________________________________________END")
print("\n")