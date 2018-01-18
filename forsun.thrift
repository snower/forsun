
exception ForsunPlanError{
    1:i16 code,
    2:string message
}

struct ForsunPlan {
    1: required bool is_time_out,
    2: required string key,
    3: required i16 second,
    4: i16 minute = -1,
    5: i16 hour = -1,
    6: i16 day = -1,
    7: i16 month = -1,
    8: i16 week = -1,
    9: required i32 next_time,
    10: i16 status = 0,
    11: i16 count = 0,
    12: i16 current_count = 0,
    13: i32 last_timeout = 0,
    14:string action = "shell",
    15:map<string, string> params = {}
}

service Forsun{
    i16 ping(),
    ForsunPlan create(1:string key, 2:i16 second, 3:i16 minute = -1, 4:i16 hour = -1, 5:i16 day = -1, 6:i16 month = -1, 7:i16 week = -1, 8:string action="shell", 9:map<string, string> params={}) throws (1:ForsunPlanError err),
    ForsunPlan createTimeout(1:string key, 2:i16 second, 3:i16 minute = -1, 4:i16 hour = -1, 5:i16 day = -1, 6:i16 month = -1, 7:i16 week = -1, 8:i16 count=1, 9:string action="shell", 10:map<string, string> params={}) throws (1:ForsunPlanError err),
    ForsunPlan remove(1:string key) throws (1:ForsunPlanError err),
    ForsunPlan get(1:string key) throws (1:ForsunPlanError err),
    list<ForsunPlan> getCurrent(),
    list<ForsunPlan> getTime(1:i32 timestamp),
    list<string> getKeys(1:string prefix),
    void forsun_call(1:string key, 2:i32 ts, 3:map<string, string> params)
}