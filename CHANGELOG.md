## 0.0.2 (2023-05-20)

### Feat

- Display request in debug mode
- Send referer to page view event

### Fix

- send engagement_time_msec to enable user tracking

## 0.0.1 (2023-05-14)

### Feat

- Added custom event documentation
- Added crawler detection
- Allow ignore paths using regex
- Sending user-agent to identify this app
- Added debug support
- Implemented collect call
- Implemented response parsing
- Store user id cookie
- Added user_id generator
- Allow override processing (storing cookies etc.)
- Added custom event support
- Implemented middleware to access last request / response

### Fix

- Don't send IP address
- Removed repeated question mark
- Clear request context on finish
- Prevent sending events to other content types

### Refactor

- Process analytics using context
- Allow set other measurement protocol properties
- Udpated types
- Replaced name of current context
