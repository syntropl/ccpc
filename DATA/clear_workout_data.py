from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_reflection import Base, Variant_Planned_Or_Executed, Workout  # Replace 'your_model_file' with the actual file name where your models are defined

def ClearWorkoutData():

    # Database configuration
    database_path = 'DATA/convict_conditioning_1.db'
    engine = create_engine(f'sqlite:///{database_path}')

    # Create a Session
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Delete all rows in 'work_planned_or_executed' table
        session.query(Variant_Planned_Or_Executed).delete()

        # Delete all rows in 'workouts' table
        session.query(Workout).delete()

        # Commit the changes
        session.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

    print("Tables cleared successfully.")

if __name__ == "__main__":
    ClearWorkoutData()

