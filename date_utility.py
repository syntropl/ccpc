from datetime import datetime, timedelta

def Int_To_Weekday(integer: int):
    weekdayNamesByInt = {
        0: 'Sunday',
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday'
    }
    return weekdayNamesByInt.get(integer, 'Invalid wekday int. should be in range(0,6)')

def DateOfNearestSpecificDayOfWeek(workingWeekday: int):
    """argument: int weekday /// sunday-saturday as 0-6/// returns a datetime"""
    if workingWeekday not in range(0,6):
        raise ValueError("workingWeekday must be an integer between 0 and 6")

    todayDate = datetime.now().date()
    todayWeekday = datetime.now().weekday()
    dayDelta = 0
    if todayWeekday < workingWeekday:
        dayDelta = workingWeekday - todayWeekday
        return todayDate + timedelta(dayDelta)
    if todayWeekday == workingWeekday:
        return todayDate
    if todayWeekday > workingWeekday:
        dayDelta = 7 - (todayWeekday - workingWeekday)
        return todayDate + timedelta(dayDelta)





